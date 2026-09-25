"""Source-bound geometry screen for the current WJ24 panel screw receivers.

The collector consumes an already materialized current geometry object. It
does not rebuild the candidate, run a solver, or turn geometric contact into a
capacity or load-sharing claim.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

CURRENT_REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
SCHEMA = "wood_joint_current_receiver_screen/v1"
EXPECTED_MOVED_AXIS_IDS = frozenset(
    {
        *(f"round_panel_lower_{side}_edge_{index}" for side in ("left", "right") for index in (1, 2)),
        *(f"round_kicker_{side}_center_{index}" for side in ("left", "right") for index in (1, 2)),
    }
)
EXPECTED_KICKER_CENTER_RECEIVERS = {
    f"round_kicker_{side}_center_{index}": f"base_post_center_{side}"
    for side in ("left", "right")
    for index in (1, 2)
}


def build_current_panel_axis_map(
    source_inventory: Mapping[str, Any],
    report: Mapping[str, Any],
    fixed_axis_ids: Sequence[str] | set[str] | frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    """Join 58 source-station axes to the eight report-recorded current moves."""
    if report.get("revision_id") != CURRENT_REVISION_ID:
        raise ValueError(
            f"expected report for {CURRENT_REVISION_ID}, found {report.get('revision_id')!r}"
        )

    source_rows = source_inventory.get("fixed_panel_kicker_screws")
    if not isinstance(source_rows, Sequence) or isinstance(source_rows, (str, bytes)):
        raise ValueError("source inventory lacks fixed panel/kicker screw rows")
    by_id = {str(row["axis_id"]): row for row in source_rows}
    if len(by_id) != len(source_rows) or len(by_id) != 66:
        raise ValueError(f"expected 66 unique source panel axes, found {len(by_id)}")

    moved_rows = report.get("moved_panel_axes")
    if not isinstance(moved_rows, Sequence) or isinstance(moved_rows, (str, bytes)):
        raise ValueError("current report lacks moved_panel_axes rows")
    moved_by_id = {str(row["axis_id"]): row for row in moved_rows}
    if len(moved_by_id) != len(moved_rows):
        raise ValueError("current report contains duplicate moved panel axis IDs")
    if set(moved_by_id) != EXPECTED_MOVED_AXIS_IDS:
        raise ValueError(
            "current report moved-axis set differs from the eight reviewed axis moves"
        )

    if fixed_axis_ids is not None and set(map(str, fixed_axis_ids)) != set(by_id):
        raise ValueError("materialized fixed axis IDs differ from the 66 source IDs")

    result: list[dict[str, Any]] = []
    for axis_id in sorted(by_id):
        source = by_id[axis_id]
        moved = moved_by_id.get(axis_id)
        if moved is None:
            origin = source["origin_global_xyz_mm"]
            direction = source["axis_global_xyz"]
            receiver = source.get(
                "candidate_finished_receiver_member",
                source["source_finished_receiver_member"],
            )
            previous_receiver = source.get("source_finished_receiver_member")
            movement = [0.0, 0.0, 0.0]
        else:
            origin = moved["new_start_global_xyz_mm"]
            direction = moved["axis_global_xyz_unchanged"]
            receiver = moved["receiver_member"]
            previous_receiver = moved.get(
                "previous_receiver_member", source.get("source_finished_receiver_member")
            )
            movement = moved["translation_global_xyz_mm"]
            if moved["panel_member"] != source["panel_member"]:
                raise ValueError(f"moved panel member changed for {axis_id}")

            source_origin = [float(value) for value in source["origin_global_xyz_mm"]]
            old_origin = [float(value) for value in moved["old_start_global_xyz_mm"]]
            new_origin = [float(value) for value in origin]
            translation = [float(value) for value in movement]
            source_direction = [float(value) for value in source["axis_global_xyz"]]
            moved_direction = [float(value) for value in direction]
            if any(
                len(vector) != 3
                for vector in (
                    source_origin,
                    old_origin,
                    new_origin,
                    translation,
                    source_direction,
                    moved_direction,
                )
            ):
                raise ValueError(f"invalid moved-axis coordinate vector for {axis_id}")
            if not all(
                math.isclose(a, b, rel_tol=0.0, abs_tol=1e-6)
                for a, b in zip(old_origin, source_origin)
            ):
                raise ValueError(f"moved-axis old start differs from source origin for {axis_id}")
            if not all(
                math.isclose(new, old + delta, rel_tol=0.0, abs_tol=1e-6)
                for new, old, delta in zip(new_origin, old_origin, translation)
            ):
                raise ValueError(f"moved-axis start does not equal old start plus translation for {axis_id}")
            if not all(
                math.isclose(current, original, rel_tol=0.0, abs_tol=1e-9)
                for current, original in zip(moved_direction, source_direction)
            ):
                raise ValueError(f"moved-axis direction differs from source direction for {axis_id}")

        if len(origin) != 3 or len(direction) != 3 or len(movement) != 3:
            raise ValueError(f"invalid coordinate vector for {axis_id}")
        norm = math.sqrt(sum(float(v) ** 2 for v in direction))
        if not math.isclose(norm, 1.0, abs_tol=1e-6):
            raise ValueError(f"non-unit current axis direction for {axis_id}")
        if axis_id in EXPECTED_KICKER_CENTER_RECEIVERS and receiver != EXPECTED_KICKER_CENTER_RECEIVERS[axis_id]:
            raise ValueError(f"current kicker center receiver changed for {axis_id}")

        result.append(
            {
                "axis_id": axis_id,
                "panel_member": source["panel_member"],
                "receiver_member": receiver,
                "previous_receiver_member": previous_receiver,
                "origin_global_xyz_mm": [float(v) for v in origin],
                "axis_global_xyz": [float(v) for v in direction],
                "translation_from_source_xyz_mm": [float(v) for v in movement],
                "source_occupied_length_mm": float(source["source_occupied_length_mm"]),
                "source_occupied_diameter_mm": float(source["source_occupied_diameter_mm"]),
                "purchased_length_mm": float(source["shop_purchased_length_mm"]),
                "purchased_product_policy": (
                    moved.get("purchased_product_policy", "Hillman 42605; existing purchased screw and pilot policy retained")
                    if moved is not None
                    else "Hillman 42605; existing purchased screw and pilot policy retained"
                ),
                "current_location_status": "moved" if moved is not None else "source_station_retained",
            }
        )
    return result


def _bbox_values(shape: Any) -> tuple[float, float, float, float, float, float]:
    box = shape.BoundingBox()
    return (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)


def _boxes_overlap(a: Any, b: Any, tolerance: float = 1e-7) -> bool:
    aa, bb = _bbox_values(a), _bbox_values(b)
    return all(
        not (aa[2 * axis + 1] < bb[2 * axis] - tolerance or bb[2 * axis + 1] < aa[2 * axis] - tolerance)
        for axis in range(3)
    )


def _point_tuple(point: Any) -> tuple[float, float, float]:
    return (float(point.x), float(point.y), float(point.z))


def _axis_aligned_shape(shape: Any, origin: Sequence[float], direction: Sequence[float]) -> Any:
    """Rotate an exact BRep so its axis is global +X for exact axial bounds."""
    import cadquery as cq

    start = cq.Vector(*origin)
    source = cq.Vector(*direction).normalized()
    target = cq.Vector(1.0, 0.0, 0.0)
    dot = max(-1.0, min(1.0, source.dot(target)))
    angle = math.acos(dot)
    cross = source.cross(target)
    if angle <= 1e-12:
        return shape
    if cross.Length <= 1e-12:
        rotation_axis = cq.Vector(0.0, 1.0, 0.0)
    else:
        rotation_axis = cross.normalized()
    return shape.rotate(start, start + rotation_axis, math.degrees(angle))


def _aligned_bounds(shape: Any, origin: Sequence[float], direction: Sequence[float]) -> dict[str, Any]:
    aligned = _axis_aligned_shape(shape, origin, direction)
    box = aligned.BoundingBox()
    return {
        "shape": aligned,
        "axial_bounds_from_reported_origin_mm": [
            float(box.xmin) - float(origin[0]),
            float(box.xmax) - float(origin[0]),
        ],
        "axial_length_mm": float(box.xlen),
        "transverse_center_offset_mm": [
            (float(box.ymin) + float(box.ymax)) / 2.0 - float(origin[1]),
            (float(box.zmin) + float(box.zmax)) / 2.0 - float(origin[2]),
        ],
        "transverse_extents_mm": [float(box.ylen), float(box.zlen)],
    }


def _validate_current_axis_shape(axis_shape: Any, row: Mapping[str, Any], tolerance_mm: float = 0.05) -> dict[str, Any]:
    bounds = _aligned_bounds(
        axis_shape, row["origin_global_xyz_mm"], row["axis_global_xyz"]
    )
    axial = bounds["axial_bounds_from_reported_origin_mm"]
    offsets = bounds["transverse_center_offset_mm"]
    if abs(axial[0]) > tolerance_mm or axial[1] <= tolerance_mm:
        raise ValueError(
            f"materialized fixed axis is not at its current reported start: {row['axis_id']}"
        )
    if max(abs(value) for value in offsets) > tolerance_mm:
        raise ValueError(
            f"materialized fixed axis is stale or double-moved: {row['axis_id']}"
        )
    if min(bounds["transverse_extents_mm"]) <= 0:
        raise ValueError(f"materialized fixed axis has invalid cross-section: {row['axis_id']}")
    return {key: value for key, value in bounds.items() if key != "shape"}


def _shape_intersection(
    axis_shape: Any,
    receiver_shape: Any,
    origin: Sequence[float],
    direction: Sequence[float],
) -> dict[str, Any]:
    if not _boxes_overlap(axis_shape, receiver_shape):
        return {
            "bbox_candidate": False,
            "intersection_volume_mm3": 0.0,
            "shape": None,
            "axial_bounds_from_axis_start_mm": None,
        }
    common = axis_shape.intersect(receiver_shape)
    common_bounds = (
        _aligned_bounds(common, origin, direction)["axial_bounds_from_reported_origin_mm"]
        if float(common.Volume()) > 0.0
        else None
    )
    return {
        "bbox_candidate": True,
        "shape": common,
        "intersection_volume_mm3": float(common.Volume()),
        "axial_bounds_from_axis_start_mm": common_bounds,
    }


def _axis_host_result(
    axis_shape: Any,
    raw_receiver: Any,
    finished_receiver: Any | None,
    row: Mapping[str, Any],
    *,
    volume_tolerance_mm3: float,
) -> dict[str, Any]:
    model = _validate_current_axis_shape(axis_shape, row)
    origin = row["origin_global_xyz_mm"]
    direction = row["axis_global_xyz"]
    raw = _shape_intersection(axis_shape, raw_receiver, origin, direction)
    raw_common = raw.pop("shape", None)
    diameter = max(model["transverse_extents_mm"])
    model_area = float(axis_shape.Volume()) / model["axial_length_mm"]
    raw_volume = float(raw["intersection_volume_mm3"])
    result: dict[str, Any] = {
        "raw_receiver_bbox_candidate": bool(raw["bbox_candidate"]),
        "raw_receiver_axis_envelope_intersection_volume_mm3": raw_volume,
        "raw_receiver_intersection_axial_bounds_from_axis_start_mm": raw[
            "axial_bounds_from_axis_start_mm"
        ],
        "raw_receiver_full_section_equivalent_length_mm": raw_volume / model_area if model_area else None,
        "raw_receiver_axis_envelope_intersects": raw_volume > volume_tolerance_mm3,
        "materialized_axis_envelope": {
            **model,
            "diameter_from_aligned_shape_bounds_mm": diameter,
            "cross_section_area_from_shape_volume_mm2": model_area,
            "status": "current CAD occupied geometry; not measured Hillman screw geometry",
        },
        "source_inventory_envelope_fields": {
            "length_mm": float(row["source_occupied_length_mm"]),
            "diameter_mm": float(row["source_occupied_diameter_mm"]),
            "status": "source inventory fields; distinct from current fixed-axis BRep bounds",
        },
    }
    if finished_receiver is not None:
        finished = _shape_intersection(axis_shape, finished_receiver, origin, direction)
        result["finished_receiver_axis_envelope_overlap_volume_mm3"] = float(
            finished["intersection_volume_mm3"]
        )
        result["finished_receiver_axis_envelope_clear"] = (
            float(finished["intersection_volume_mm3"]) <= volume_tolerance_mm3
        )
    else:
        result["finished_receiver_axis_envelope_clear"] = None
    return result


def _transverse_bbox_margins(
    receiver: Any, origin: Sequence[float], direction: Sequence[float]
) -> dict[str, dict[str, float]]:
    """Return centerline margins to axis-aligned receiver extents only."""
    bounds = _bbox_values(receiver)
    coordinates = {"x": (0, 1), "y": (2, 3), "z": (4, 5)}
    dominant = max(range(3), key=lambda i: abs(float(direction[i])))
    result: dict[str, dict[str, float]] = {}
    for name, index in (("x", 0), ("y", 1), ("z", 2)):
        if index == dominant:
            continue
        lo, hi = coordinates[name]
        result[name] = {
            "to_min_bbox_face_mm": float(origin[index]) - bounds[lo],
            "to_max_bbox_face_mm": bounds[hi] - float(origin[index]),
        }
    return result


def _face_bounds_overlap(first: Any, second: Any, tolerance: float = 1e-5) -> bool:
    return _boxes_overlap(first, second, tolerance)


def _finite_shared_planar_face_area(first: Any, second: Any, tolerance: float) -> float:
    """Sum exact common area for coplanar planar boundary-face pairs."""
    total = 0.0
    first_faces = [
        face
        for face in first.Faces()
        if face.geomType() == "PLANE" and float(face.Area()) > 1e-8
    ]
    second_faces = [
        face
        for face in second.Faces()
        if face.geomType() == "PLANE" and float(face.Area()) > 1e-8
    ]
    for face_a in first_faces:
        bounds_a = face_a.BoundingBox()
        normal_a = face_a.normalAt().normalized()
        center_a = face_a.Center()
        for face_b in second_faces:
            if not _face_bounds_overlap(face_a, face_b, tolerance):
                continue
            normal_b = face_b.normalAt().normalized()
            if abs(abs(normal_a.dot(normal_b)) - 1.0) > 1e-7:
                continue
            center_delta = face_b.Center() - center_a
            if abs(center_delta.dot(normal_a)) > tolerance:
                continue
            common = face_a.intersect(face_b)
            total += sum(float(face.Area()) for face in common.Faces())
    return total


def _interface_geometry(first: Any, second: Any, tolerance_mm: float = 1e-5) -> dict[str, Any]:
    overlap = 0.0
    bbox_candidate = _boxes_overlap(first, second, tolerance_mm)
    if bbox_candidate:
        overlap = float(first.intersect(second).Volume())
    distance = float(first.distance(second))
    shared_area = (
        _finite_shared_planar_face_area(first, second, tolerance_mm)
        if distance <= tolerance_mm and overlap <= 1e-6
        else 0.0
    )
    if overlap > 1e-6:
        state = "positive_volume_overlap"
    elif distance > tolerance_mm:
        state = "separated"
    elif shared_area > 1e-6:
        state = "finite_planar_face_contact"
    else:
        state = "zero_area_touch_or_unresolved_contact"
    return {
        "bbox_candidate": bbox_candidate,
        "minimum_separation_mm": distance,
        "common_volume_mm3": overlap,
        "finite_shared_planar_face_area_mm2": shared_area,
        "geometry_state": state,
    }


def _named_source_shapes(geometry: Any) -> dict[str, Any]:
    source = getattr(geometry, "source", None)
    parts = getattr(source, "parts", None)
    if not callable(parts):
        return {}
    return {str(part.name): part.shape for part in parts()}


def _contact_graph_interfaces(geometry: Any, report: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Measure declared bolt pairs, exterior runner seats, and center post/header seats."""
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for axis_id, bore in sorted(getattr(geometry, "candidate_bores", {}).items()):
        receiver_ids = tuple(map(str, getattr(bore, "receiver_ids", ())))
        if len(receiver_ids) < 2:
            continue
        for first_id, second_id in zip(receiver_ids, receiver_ids[1:]):
            pair = tuple(sorted((first_id, second_id)))
            row = grouped.setdefault(
                pair,
                {
                    "members": list(pair),
                    "interface_basis": "adjacent receiver IDs in current candidate-bolt stack",
                    "candidate_bolt_axis_ids": [],
                    "candidate_bolt_axis_count": 0,
                },
            )
            row["candidate_bolt_axis_ids"].append(str(axis_id))
            row["candidate_bolt_axis_count"] += 1

    for block_id, change in report.get("exterior_block_changes", {}).items():
        runner_id = str(change["runner_id"])
        pair = tuple(sorted((str(block_id), runner_id)))
        grouped.setdefault(
            pair,
            {
                "members": list(pair),
                "interface_basis": "reported exterior block seat on floor runner",
                "candidate_bolt_axis_ids": [],
                "candidate_bolt_axis_count": 0,
            },
        )

    for side in ("left", "right"):
        pair = tuple(sorted(("base_header", f"base_post_center_{side}")))
        grouped.setdefault(
            pair,
            {
                "members": list(pair),
                "interface_basis": "current center-post top seat against base header underside",
                "candidate_bolt_axis_ids": [],
                "candidate_bolt_axis_count": 0,
            },
        )

    shape_by_id: dict[str, Any] = {}
    shape_by_id.update(_named_source_shapes(geometry))
    shape_by_id.update(getattr(geometry, "finished_hosts", {}))
    shape_by_id.update(getattr(geometry, "finished_candidate_parts", {}))

    output = []
    for pair, row in sorted(grouped.items()):
        first_id, second_id = pair
        if first_id not in shape_by_id or second_id not in shape_by_id:
            raise ValueError(f"current contact graph shape is absent for {pair}")
        measured = _interface_geometry(shape_by_id[first_id], shape_by_id[second_id])
        output.append({**row, **measured})
    return output


def _panel_receiver_interfaces(
    geometry: Any,
    axes: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Measure exact panel-to-receiver separation/contact for current screw pairs."""
    panels = _named_source_shapes(geometry)
    panels.update(getattr(geometry, "panel_replacements", {}))
    receiver_shapes = dict(getattr(geometry, "finished_hosts", {}))
    grouped: dict[tuple[str, str], list[str]] = {}
    for row in axes:
        pair = (str(row["panel_member"]), str(row["receiver_member"]))
        grouped.setdefault(pair, []).append(str(row["axis_id"]))

    output = []
    for (panel_id, receiver_id), axis_ids in sorted(grouped.items()):
        if panel_id not in panels:
            raise ValueError(f"current panel shape is absent: {panel_id}")
        if receiver_id not in receiver_shapes:
            raise ValueError(f"current finished receiver shape is absent: {receiver_id}")
        output.append(
            {
                "panel_member": panel_id,
                "receiver_member": receiver_id,
                "fixed_hillman_axis_ids": sorted(axis_ids),
                **_interface_geometry(panels[panel_id], receiver_shapes[receiver_id]),
            }
        )
    return output


def _kicker_seam_geometry(geometry: Any, kicker_center: Mapping[str, Any]) -> dict[str, Any]:
    panels = _named_source_shapes(geometry)
    panels.update(getattr(geometry, "panel_replacements", {}))
    for panel_id in ("kicker_left", "kicker_right"):
        if panel_id not in panels:
            raise ValueError(f"current kicker panel shape is absent: {panel_id}")
    left_bounds = _bbox_values(panels["kicker_left"])
    right_bounds = _bbox_values(panels["kicker_right"])
    left_post = _bbox_values(geometry.raw_hosts["base_post_center_left"])
    right_post = _bbox_values(geometry.raw_hosts["base_post_center_right"])
    seam_left = left_bounds[1]
    seam_right = right_bounds[0]
    seam_midpoint = (seam_left + seam_right) / 2.0
    center_axes = [axis for rows in kicker_center["center_posts"].values() for axis in rows["axes"]]
    return {
        "kicker_left_outermost_x_face_mm": left_bounds[1],
        "kicker_right_innermost_x_face_mm": right_bounds[0],
        "panel_edge_to_edge_x_gap_mm": seam_right - seam_left,
        "panel_edge_planes_touch_by_x_extent": abs(seam_right - seam_left) <= 1e-6,
        "left_panel_edge_to_left_center_post_inner_face_x_mm": seam_left - left_post[1],
        "right_center_post_inner_face_to_right_panel_edge_x_mm": right_post[0] - seam_right,
        "nearest_moved_kicker_axis_to_panel_seam_center_x_mm": min(
            abs(float(axis["origin_global_xyz_mm"][0]) - seam_midpoint)
            for axis in center_axes
        ),
        "panel_to_panel_interface": _interface_geometry(panels["kicker_left"], panels["kicker_right"]),
        "limits": [
            "Panel and post edge planes are compared in global X; this does not evaluate panel bending or support capacity.",
            "A screw receiver path through a post does not establish continuous support under the kicker center seam.",
        ],
    }


def collect_current_receiver_screen(geometry: Any, report: Mapping[str, Any]) -> dict[str, Any]:
    """Measure current modeled screw-envelope intersections with declared raw receivers.

    The work is limited to one bbox-filtered receiver solid per screw axis,
    distinct panel/receiver face pairs, declared adjacent bolt-stack pairs,
    two exterior runner seats, and two explicit center-post/header seats. It
    does not evaluate support requirements, fastener resistance, or transfer
    capacity.
    """
    if getattr(geometry, "layout_id", None) != CURRENT_REVISION_ID:
        raise ValueError("geometry object is not the owner-reviewed current revision")
    source_inventory = getattr(geometry, "source_inventory", None)
    fixed_axes = getattr(geometry, "fixed_axes", None)
    if not isinstance(source_inventory, Mapping) or not isinstance(fixed_axes, Mapping):
        raise ValueError("current geometry lacks its source inventory or fixed axis solids")
    axes = build_current_panel_axis_map(source_inventory, report, set(fixed_axes))

    raw_hosts = getattr(geometry, "raw_hosts", {})
    finished_hosts = getattr(geometry, "finished_hosts", {})
    raw_parts = getattr(geometry, "raw_candidate_parts", {})
    axis_results: list[dict[str, Any]] = []
    receiver_counts: Counter[str] = Counter()
    for row in axes:
        receiver_id = str(row["receiver_member"])
        raw_receiver = raw_hosts.get(receiver_id, raw_parts.get(receiver_id))
        finished_receiver = finished_hosts.get(receiver_id)
        if raw_receiver is None:
            raise ValueError(f"current raw receiver is absent: {receiver_id}")
        axis_shape = fixed_axes[row["axis_id"]]
        measured = _axis_host_result(
            axis_shape,
            raw_receiver,
            finished_receiver,
            row,
            volume_tolerance_mm3=1e-6,
        )
        receiver_counts[receiver_id] += 1
        axis_results.append({**row, **measured})

    kicker_axes = [
        row for row in axis_results if row["axis_id"] in EXPECTED_KICKER_CENTER_RECEIVERS
    ]
    kicker_receivers = {row["receiver_member"] for row in kicker_axes}
    if len(kicker_axes) != 4 or kicker_receivers != {
        "base_post_center_left",
        "base_post_center_right",
    }:
        raise ValueError("current kicker-center receiver mapping is incomplete")

    kicker_side_geometry: dict[str, Any] = {}
    for side in ("left", "right"):
        post_id = f"base_post_center_{side}"
        post = raw_hosts.get(post_id)
        if post is None:
            raise ValueError(f"current kicker receiver post is absent: {post_id}")
        matching = [row for row in kicker_axes if row["receiver_member"] == post_id]
        post_bounds = _bbox_values(post)
        kicker_side_geometry[side] = {
            "receiver_member": post_id,
            "raw_receiver_bounds_xyz_mm": [
                [post_bounds[0], post_bounds[1]],
                [post_bounds[2], post_bounds[3]],
                [post_bounds[4], post_bounds[5]],
            ],
            "axis_count": len(matching),
            "axes": [
                {
                    "axis_id": row["axis_id"],
                    "origin_global_xyz_mm": row["origin_global_xyz_mm"],
                    "centerline_to_receiver_bbox_side_margins_mm": _transverse_bbox_margins(
                        post,
                        row["origin_global_xyz_mm"],
                        row["axis_global_xyz"],
                    ),
                    "raw_receiver_axis_envelope_intersects": row[
                        "raw_receiver_axis_envelope_intersects"
                    ],
                    "raw_receiver_axis_envelope_intersection_volume_mm3": row[
                        "raw_receiver_axis_envelope_intersection_volume_mm3"
                    ],
                    "raw_receiver_intersection_axial_bounds_from_axis_start_mm": row[
                        "raw_receiver_intersection_axial_bounds_from_axis_start_mm"
                    ],
                    "raw_receiver_full_section_equivalent_length_mm": row[
                        "raw_receiver_full_section_equivalent_length_mm"
                    ],
                    "finished_receiver_axis_envelope_clear": row[
                        "finished_receiver_axis_envelope_clear"
                    ],
                }
                for row in matching
            ],
        }

    old_backer_ids = {"inner_kicker_backer_left", "inner_kicker_backer_right"}
    old_backers_present = sorted(
        old_backer_ids & (set(raw_hosts) | set(raw_parts) | set(finished_hosts))
    )
    posts = {
        side: raw_hosts[f"base_post_center_{side}"] for side in ("left", "right")
    }
    left_bounds = _bbox_values(posts["left"])
    right_bounds = _bbox_values(posts["right"])
    post_gap = right_bounds[0] - left_bounds[1]

    contact_graph = _contact_graph_interfaces(geometry, report)
    panel_receiver_interfaces = _panel_receiver_interfaces(geometry, axes)
    kicker_seam = _kicker_seam_geometry(geometry, {"center_posts": kicker_side_geometry})
    moved_interface_keys = {
        (row["panel_member"], row["receiver_member"])
        for row in axis_results
        if row["current_location_status"] == "moved"
    }
    moved_panel_interfaces = [
        row
        for row in panel_receiver_interfaces
        if (row["panel_member"], row["receiver_member"]) in moved_interface_keys
    ]

    return {
        "schema": SCHEMA,
        "revision_id": CURRENT_REVISION_ID,
        "scope": "current nominal geometry screen; no force, resistance, capacity, installation, or acceptance result",
        "counts": {
            "panel_kicker_axes_total": len(axis_results),
            "unchanged_source_station_axes": sum(
                row["current_location_status"] == "source_station_retained"
                for row in axis_results
            ),
            "moved_axes": sum(row["current_location_status"] == "moved" for row in axis_results),
            "current_receiver_member_counts": dict(sorted(receiver_counts.items())),
        },
        "limits": [
            "The source inventory's 50.8 mm occupied-length field is a historical SPAX analysis envelope; the current CAD axis is 63.5 mm and the retained purchased policy is Hillman 42605 at 63.5 mm nominal. None is measured installed screw engagement.",
            "Raw receiver overlap and finite interface contact are geometric facts only; neither supplies required support, load sharing, or resistance.",
            "Bounding-box margins below are nominal geometric distances, not adopted fastener edge/end checks.",
        ],
        "axes": axis_results,
        "four_moved_kicker_center_receiver_check": {
            "current_receiver_map": EXPECTED_KICKER_CENTER_RECEIVERS,
            "previous_backer_shapes_present_in_current_composition": bool(old_backers_present),
            "previous_backer_shape_ids_present": old_backers_present,
            "side_to_side_center_post_bbox_gap_x_mm": post_gap,
            "center_posts": kicker_side_geometry,
            "limits": [
                "The measured post gap is the open X interval between the two current post bounding boxes, not a conclusion about panel seam capacity.",
                "A geometric shaft-envelope intersection does not prove screw engagement, installed length, or transfer capacity.",
            ],
        },
        "panel_to_receiver_interfaces": {
            "scope": "one exact panel-to-finished-receiver check per distinct panel/receiver pair in the current 66-axis map",
            "interfaces": panel_receiver_interfaces,
            "moved_axis_interfaces": moved_panel_interfaces,
            "kicker_center_seam": kicker_seam,
        },
        "bolt_declared_and_runner_contact_graph": {
            "scope": "adjacent receiver pairs declared by the current 92 candidate bolt stacks, two current exterior block-to-runner seats, and two explicit current center-post-to-header top seats",
            "interfaces": contact_graph,
            "candidate_bolt_interface_count": sum(
                row["candidate_bolt_axis_count"] > 0 for row in contact_graph
            ),
            "runner_seat_interface_count": sum(
                row["interface_basis"] == "reported exterior block seat on floor runner"
                for row in contact_graph
            ),
            "center_post_header_seat_interface_count": sum(
                row["interface_basis"]
                == "current center-post top seat against base header underside"
                for row in contact_graph
            ),
            "limits": [
                "Bolt-declared adjacency is a layout record, not proof of a force path, compatibility, or load sharing.",
                "Only finite coplanar face intersections are reported as face contact; common solid volume is kept separate as overlap.",
                "Runner contact area is geometric only and does not establish bearing capacity or floor anchorage.",
            ],
        },
        "release": False,
    }
