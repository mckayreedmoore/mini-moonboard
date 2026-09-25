"""Complete current WJ24 physical wood/panel contact graph.

The collector consumes an already materialized current geometry object and
its frozen revision report. It does not compose geometry or infer force
transfer, stiffness, resistance, support adequacy, anchorage, or acceptance.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from scripts import wood_joint_current_receiver_screen as receiver_screen
from scripts import wood_joint_wj12_diagnostic as wj12_diagnostic

CURRENT_REVISION_ID = receiver_screen.CURRENT_REVISION_ID
SCHEMA = "wood_joint_current_contact_graph/v1"
EXPECTED_CANDIDATE_BOLT_COUNT = 92
EXPECTED_FRAME_BOLT_COUNT = 12
EXPECTED_PANEL_SCREW_COUNT = 66
GEOMETRY_TOLERANCE_MM = 1e-5
AREA_TOLERANCE_MM2 = 1e-6
NORMAL_TOLERANCE = 1e-7


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f"value is not plain JSON data: {type(value).__name__}")


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        _plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _valid_sha256(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")
    return value


def _shape_metrics(shape: Any, *, label: str) -> dict[str, Any]:
    box = shape.BoundingBox()
    values = [
        float(box.xmin),
        float(box.xmax),
        float(box.ymin),
        float(box.ymax),
        float(box.zmin),
        float(box.zmax),
    ]
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{label} has a non-finite bounding box")
    volume = float(shape.Volume())
    if not math.isfinite(volume) or volume <= 0.0:
        raise ValueError(f"{label} must have a positive finite volume")
    return {
        "bounds_xyz_mm": values,
        "volume_mm3": volume,
    }


def _aabb_relation(
    first: Sequence[float], second: Sequence[float], tolerance_mm: float
) -> tuple[bool, float]:
    """Return a broadphase candidate flag and AABB separation lower bound."""
    gaps = (
        max(0.0, first[0] - second[1], second[0] - first[1]),
        max(0.0, first[2] - second[3], second[2] - first[3]),
        max(0.0, first[4] - second[5], second[4] - first[5]),
    )
    distance_lower_bound = math.sqrt(sum(gap * gap for gap in gaps))
    return max(gaps) <= tolerance_mm, distance_lower_bound


def _canonical_pair(first: str, second: str) -> tuple[str, str]:
    if first == second:
        raise ValueError(f"contact pair cannot repeat member {first!r}")
    return tuple(sorted((first, second)))


def _member_ids(row: Mapping[str, Any], *, label: str) -> tuple[str, ...]:
    members = row.get("members")
    if not isinstance(members, Sequence) or isinstance(members, (str, bytes)):
        raise TypeError(f"{label} must provide a member sequence")
    result = tuple(map(str, members))
    if len(result) < 2 or any(not member for member in result):
        raise ValueError(f"{label} must name at least two nonempty members")
    if len(set(result)) != len(result):
        raise ValueError(f"{label} repeats a member")
    return result


def _candidate_bolt_inventory(
    geometry: Any, node_ids: set[str]
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    bores = getattr(geometry, "candidate_bores", None)
    if not isinstance(bores, Mapping) or len(bores) != EXPECTED_CANDIDATE_BOLT_COUNT:
        raise ValueError(
            "current geometry must provide exactly 92 candidate bolt bores"
        )
    hardware = getattr(geometry, "candidate_installed_hardware", None)
    if not isinstance(hardware, Mapping) or set(hardware) != set(bores):
        raise ValueError("current candidate bore and installed-hardware IDs differ")

    inventory: list[dict[str, Any]] = []
    edge_associations: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for axis_id, bore in sorted(bores.items()):
        axis_id = str(axis_id)
        reported_members = getattr(bore, "receiver_ids", None)
        if not isinstance(reported_members, (tuple, list)) or len(reported_members) < 2:
            raise ValueError(
                f"{axis_id}: candidate bore needs at least two receiver IDs"
            )
        members = tuple(map(str, reported_members))
        if len(set(members)) != len(members) or any(not member for member in members):
            raise ValueError(
                f"{axis_id}: candidate receiver IDs must be unique and nonempty"
            )
        absent = set(members) - node_ids
        if absent:
            raise ValueError(
                f"{axis_id}: candidate receiver nodes are absent: {sorted(absent)}"
            )

        pair_records = []
        for first, second in itertools.combinations(members, 2):
            pair = _canonical_pair(first, second)
            pair_record = {
                "member_pair": list(pair),
                "receiver_pair_as_recorded": [first, second],
                "association_basis": "both members occur in this candidate bore receiver membership",
                "physical_head_to_nut_order_established": False,
            }
            pair_records.append(pair_record)
            edge_associations[pair].append(
                {
                    "axis_id": axis_id,
                    **pair_record,
                    "receiver_member_ids_as_recorded": list(members),
                }
            )
        inventory.append(
            {
                "axis_id": axis_id,
                "receiver_member_ids_as_recorded": list(members),
                "receiver_member_order_semantics": (
                    "preserved provider order only; not interpreted as physical head-to-nut order"
                ),
                "member_pair_associations": pair_records,
            }
        )
    return inventory, edge_associations


def _retained_frame_bolt_inventory(
    geometry: Any,
    source_inventory: Mapping[str, Any],
    node_ids: set[str],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    live_rows = getattr(geometry, "frame_bolt_records", None)
    source_rows = source_inventory.get("starting_frame_bolts")
    if not isinstance(live_rows, Sequence) or isinstance(live_rows, (str, bytes)):
        raise TypeError("current geometry lacks retained frame-bolt records")
    if not isinstance(source_rows, Sequence) or isinstance(source_rows, (str, bytes)):
        raise TypeError("source inventory lacks retained frame-bolt membership")
    if (
        len(live_rows) != EXPECTED_FRAME_BOLT_COUNT
        or len(source_rows) != EXPECTED_FRAME_BOLT_COUNT
    ):
        raise ValueError("expected exactly 12 retained frame-bolt records")

    source_by_id = {str(row["axis_id"]): row for row in source_rows}
    live_by_id = {str(row["axis_id"]): row for row in live_rows}
    if (
        len(source_by_id) != EXPECTED_FRAME_BOLT_COUNT
        or len(live_by_id) != EXPECTED_FRAME_BOLT_COUNT
    ):
        raise ValueError("retained frame-bolt IDs must be unique")
    if set(source_by_id) != set(live_by_id):
        raise ValueError(
            "live retained frame-bolt IDs differ from the source inventory"
        )

    inventory: list[dict[str, Any]] = []
    edge_associations: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for axis_id in sorted(source_by_id):
        source_row = source_by_id[axis_id]
        live_row = live_by_id[axis_id]
        source_members = _member_ids(source_row, label=f"source frame bolt {axis_id}")
        live_members = _member_ids(live_row, label=f"live frame bolt {axis_id}")
        if set(source_members) != set(live_members):
            raise ValueError(
                f"{axis_id}: live frame-bolt member set differs from source"
            )
        absent = set(source_members) - node_ids
        if absent:
            raise ValueError(
                f"{axis_id}: retained frame-bolt nodes are absent: {sorted(absent)}"
            )

        pair_records = []
        for first, second in itertools.combinations(source_members, 2):
            pair = _canonical_pair(first, second)
            pair_record = {
                "member_pair": list(pair),
                "source_member_pair_as_recorded": [first, second],
                "association_basis": "co-membership in retained source frame-bolt record",
                "physical_head_to_nut_order_established": False,
            }
            pair_records.append(pair_record)
            edge_associations[pair].append({"axis_id": axis_id, **pair_record})
        inventory.append(
            {
                "axis_id": axis_id,
                "source_member_ids_as_recorded": list(source_members),
                "member_order_semantics": "source membership only; not a physical stack order",
                "member_pair_associations": pair_records,
                "source_occupied_length_mm": source_row.get(
                    "source_occupied_length_mm"
                ),
                "source_occupied_diameter_mm": source_row.get(
                    "source_occupied_diameter_mm"
                ),
                "source_nominal_length_mm": source_row.get("source_nominal_length_mm"),
                "source_grip_mm": source_row.get("source_grip_mm"),
                "axis_global_xyz": _plain(source_row.get("axis_global_xyz")),
                "origin_global_xyz_mm": _plain(source_row.get("origin_global_xyz_mm")),
            }
        )
    return inventory, edge_associations


def _fixed_panel_screw_inventory(
    geometry: Any,
    source_inventory: Mapping[str, Any],
    report: Mapping[str, Any],
    node_ids: set[str],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    fixed_axes = getattr(geometry, "fixed_axes", None)
    if not isinstance(fixed_axes, Mapping):
        raise TypeError("current geometry lacks the 66 fixed panel/kicker axes")
    rows = receiver_screen.build_current_panel_axis_map(
        source_inventory, report, set(fixed_axes)
    )
    if len(rows) != EXPECTED_PANEL_SCREW_COUNT:
        raise ValueError("current screw map must contain exactly 66 axes")

    inventory: list[dict[str, Any]] = []
    edge_associations: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        panel_id = str(row["panel_member"])
        receiver_id = str(row["receiver_member"])
        absent = {panel_id, receiver_id} - node_ids
        if absent:
            raise ValueError(
                f"{row['axis_id']}: current screw member nodes are absent: {sorted(absent)}"
            )
        pair = _canonical_pair(panel_id, receiver_id)
        association = {
            "axis_id": str(row["axis_id"]),
            "panel_member": panel_id,
            "receiver_member": receiver_id,
            "current_location_status": str(row["current_location_status"]),
            "association_basis": "current 66-axis map from the frozen revision report",
        }
        inventory.append(_plain(row))
        edge_associations[pair].append(association)
    return inventory, edge_associations


def _opposed_planar_contact_area(first: Any, second: Any) -> tuple[float, float]:
    """Return exact coplanar contact area with opposed and co-oriented normals."""
    opposed_area = 0.0
    cooriented_area = 0.0
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
        normal_a = face_a.normalAt().normalized()
        center_a = face_a.Center()
        for face_b in second_faces:
            if not receiver_screen._face_bounds_overlap(
                face_a, face_b, GEOMETRY_TOLERANCE_MM
            ):
                continue
            normal_b = face_b.normalAt().normalized()
            dot = float(normal_a.dot(normal_b))
            if abs(abs(dot) - 1.0) > NORMAL_TOLERANCE:
                continue
            if (
                abs(float((face_b.Center() - center_a).dot(normal_a)))
                > GEOMETRY_TOLERANCE_MM
            ):
                continue
            common = face_a.intersect(face_b)
            area = sum(float(face.Area()) for face in common.Faces())
            if area <= AREA_TOLERANCE_MM2:
                continue
            if dot < 0.0:
                opposed_area += area
            else:
                cooriented_area += area
    return opposed_area, cooriented_area


def _contact_state(
    measured: Mapping[str, Any], opposed_area: float, cooriented_area: float
) -> str:
    base_state = str(measured["geometry_state"])
    if base_state == "positive_volume_overlap":
        return "solid_overlap"
    if base_state == "separated":
        return "separated"
    if base_state == "finite_planar_face_contact":
        shared = float(measured["finite_shared_planar_face_area_mm2"])
        if (
            opposed_area + AREA_TOLERANCE_MM2 >= shared
            and opposed_area > AREA_TOLERANCE_MM2
        ):
            return "finite_opposed_planar_touch"
        if (
            cooriented_area + AREA_TOLERANCE_MM2 >= shared
            and cooriented_area > AREA_TOLERANCE_MM2
        ):
            return "finite_cooriented_planar_touch"
        return "finite_mixed_or_unresolved_planar_touch"
    return "zero_area_touch_or_unresolved"


def _validate_source_fingerprints(geometry: Any) -> dict[str, Any]:
    raw_inputs = getattr(geometry, "source_inputs_sha256", None)
    if not isinstance(raw_inputs, Mapping) or not raw_inputs:
        raise ValueError("current geometry lacks source input SHA-256 fingerprints")
    source_inputs = {
        str(path): _valid_sha256(digest, f"source hash for {path}")
        for path, digest in sorted(raw_inputs.items())
    }
    inventory_hash = _valid_sha256(
        getattr(geometry, "source_inventory_sha256", None),
        "source inventory hash",
    )
    return {
        "geometry_source_inputs_sha256": source_inputs,
        "source_inventory_sha256": inventory_hash,
    }


def collect_current_contact_graph(
    geometry: Any, report: Mapping[str, Any]
) -> dict[str, Any]:
    """Build the current complete physical timber/panel contact graph.

    ``geometry`` must be the already materialized current ``g24_outer_2x6``
    geometry. ``report`` is the frozen geometry revision report passed by the
    parent. The collector uses ``_composed_wood`` to include retained source
    members, rebuilt hosts, candidate blocks, and current panel replacements.
    """
    if getattr(geometry, "layout_id", None) != CURRENT_REVISION_ID:
        raise ValueError(
            "geometry object is not the owner-reviewed current WJ24 revision"
        )
    if not isinstance(report, Mapping):
        raise TypeError("current revision report must be a mapping")
    if report.get("revision_id") != CURRENT_REVISION_ID:
        raise ValueError("current revision report does not match the live geometry")

    raw_shapes, finished_shapes = wj12_diagnostic._composed_wood(geometry)
    if (
        not raw_shapes
        or not finished_shapes
        or not set(raw_shapes) <= set(finished_shapes)
    ):
        raise ValueError(
            "composed raw members must be contained in the finished wood/panel inventory"
        )

    # Cache member bounds and volumes once per unique shape object. The cached
    # finished bounds drive the broadphase; raw records remain in the complete
    # node inventory for receiver/contact interpretation.
    shape_metrics_cache: dict[int, dict[str, Any]] = {}

    def metrics(shape: Any, label: str) -> dict[str, Any]:
        key = id(shape)
        if key not in shape_metrics_cache:
            shape_metrics_cache[key] = _shape_metrics(shape, label=label)
        return shape_metrics_cache[key]

    source = getattr(geometry, "source", None)
    raw_source_parts = getattr(source, "uncut_wood_parts", None)
    if not callable(raw_source_parts):
        raise TypeError("current geometry source lacks its raw member inventory")
    source_member_ids = {str(part.name) for part in raw_source_parts()}
    source_inventory = getattr(geometry, "source_inventory", None)
    if not isinstance(source_inventory, Mapping):
        raise TypeError("current geometry lacks its source inventory")
    source_part_rows = source_inventory.get("parts")
    if not isinstance(source_part_rows, Sequence) or isinstance(
        source_part_rows, (str, bytes)
    ):
        raise TypeError("source inventory lacks its canonical part-kind records")
    source_part_kinds = {
        str(row["part_id"]): str(row["kind"]) for row in source_part_rows
    }
    if len(source_part_kinds) != len(source_part_rows):
        raise ValueError("source inventory has duplicate part-kind IDs")
    rebuilt_host_ids = set(getattr(geometry, "finished_hosts", {}))
    candidate_part_ids = set(getattr(geometry, "finished_candidate_parts", {}))
    panel_replacement_ids = set(getattr(geometry, "panel_replacements", {}))
    additional_overlay_ids = set(
        getattr(geometry, "additional_finished_source_parts", {})
    )

    node_rows: list[dict[str, Any]] = []
    for member_id in sorted(finished_shapes):
        raw_shape = raw_shapes.get(member_id)
        finished_shape = finished_shapes[member_id]
        roles = []
        if member_id in source_member_ids:
            roles.append("source_inventory_member")
        if member_id in rebuilt_host_ids:
            roles.append("current_rebuilt_host")
        if member_id in candidate_part_ids:
            roles.append("current_candidate_timber")
        if member_id in panel_replacement_ids:
            roles.append("current_panel_replacement")
        if member_id in additional_overlay_ids:
            roles.append("additional_finished_source_overlay")
        if not roles:
            roles.append("retained_composed_member")
        node_rows.append(
            {
                "member_id": member_id,
                "member_kind": "panel"
                if member_id in panel_replacement_ids
                or source_part_kinds.get(member_id) == "plywood_panel"
                else "timber",
                "composition_roles": roles,
                # Some current panels are source members and retain raw-shape
                # metrics; newly introduced finished-only members may not.
                "raw": metrics(raw_shape, f"raw/{member_id}")
                if raw_shape is not None
                else None,
                "finished": metrics(finished_shape, f"finished/{member_id}"),
            }
        )
    node_ids = {row["member_id"] for row in node_rows}
    finished_metrics = {row["member_id"]: row["finished"] for row in node_rows}

    candidate_inventory, candidate_edges = _candidate_bolt_inventory(geometry, node_ids)
    frame_inventory, frame_edges = _retained_frame_bolt_inventory(
        geometry, geometry.source_inventory, node_ids
    )
    screw_inventory, screw_edges = _fixed_panel_screw_inventory(
        geometry, geometry.source_inventory, report, node_ids
    )

    edges: list[dict[str, Any]] = []
    broadphase_pairs = 0
    exact_pairs = 0
    broadphase_separated_pairs = 0
    for first_id, second_id in itertools.combinations(sorted(node_ids), 2):
        pair = (first_id, second_id)
        first_shape = finished_shapes[first_id]
        second_shape = finished_shapes[second_id]
        first_bounds = finished_metrics[first_id]["bounds_xyz_mm"]
        second_bounds = finished_metrics[second_id]["bounds_xyz_mm"]
        candidate, aabb_distance = _aabb_relation(
            first_bounds, second_bounds, GEOMETRY_TOLERANCE_MM
        )
        if candidate:
            broadphase_pairs += 1
            measured = receiver_screen._interface_geometry(
                first_shape, second_shape, GEOMETRY_TOLERANCE_MM
            )
            exact_pairs += 1
            opposed_area = 0.0
            cooriented_area = 0.0
            if measured["geometry_state"] == "finite_planar_face_contact":
                opposed_area, cooriented_area = _opposed_planar_contact_area(
                    first_shape, second_shape
                )
            edge_geometry = {
                "geometry_state": _contact_state(
                    measured, opposed_area, cooriented_area
                ),
                "interface_geometry_state": measured["geometry_state"],
                "broadphase_candidate": True,
                "aabb_separation_lower_bound_mm": aabb_distance,
                "minimum_separation_mm": float(measured["minimum_separation_mm"]),
                "common_volume_mm3": float(measured["common_volume_mm3"]),
                "finite_shared_planar_face_area_mm2": float(
                    measured["finite_shared_planar_face_area_mm2"]
                ),
                "opposed_planar_face_contact_area_mm2": opposed_area,
                "cooriented_planar_face_contact_area_mm2": cooriented_area,
                "contact_measurement_basis": "exact BRep via current receiver interface helper",
            }
        else:
            broadphase_separated_pairs += 1
            edge_geometry = {
                "geometry_state": "separated",
                "interface_geometry_state": "not_evaluated_aabb_separated",
                "broadphase_candidate": False,
                "aabb_separation_lower_bound_mm": aabb_distance,
                "minimum_separation_mm": None,
                "common_volume_mm3": 0.0,
                "finite_shared_planar_face_area_mm2": 0.0,
                "opposed_planar_face_contact_area_mm2": 0.0,
                "cooriented_planar_face_contact_area_mm2": 0.0,
                "contact_measurement_basis": "disjoint cached AABBs; lower bound only, exact BRep distance not evaluated",
            }

        edges.append(
            {
                "member_ids": [first_id, second_id],
                **edge_geometry,
                "candidate_bolt_associations": sorted(
                    candidate_edges.get(pair, []),
                    key=lambda row: (row["axis_id"], row["receiver_pair_as_recorded"]),
                ),
                "retained_frame_bolt_source_membership": sorted(
                    frame_edges.get(pair, []),
                    key=lambda row: (
                        row["axis_id"],
                        row["source_member_pair_as_recorded"],
                    ),
                ),
                "current_panel_screw_associations": sorted(
                    screw_edges.get(pair, []), key=lambda row: row["axis_id"]
                ),
            }
        )

    source_fingerprints = _validate_source_fingerprints(geometry)
    pair_universe_count = len(node_ids) * (len(node_ids) - 1) // 2
    if len(edges) != pair_universe_count:
        raise AssertionError("contact graph omitted one or more unique member pairs")
    return {
        "schema": SCHEMA,
        "revision_id": CURRENT_REVISION_ID,
        "scope": (
            "physical timber/panel geometric contact graph; no force, stiffness, resistance, load split, "
            "support adequacy, anchorage, installation, or acceptance result"
        ),
        "source_sha256": {
            **source_fingerprints,
            "frozen_revision_report_canonical_json_sha256": _canonical_sha256(report),
        },
        "counts": {
            "physical_member_nodes": len(node_rows),
            "unique_member_pairs": pair_universe_count,
            "aabb_broadphase_candidates": broadphase_pairs,
            "exact_brep_pairs_evaluated": exact_pairs,
            "aabb_separated_pairs_not_exactly_evaluated": broadphase_separated_pairs,
            "candidate_bolt_axes": len(candidate_inventory),
            "retained_frame_bolt_axes": len(frame_inventory),
            "current_panel_screw_axes": len(screw_inventory),
        },
        "inventories": {
            "physical_members": node_rows,
            "candidate_bolt_axes": candidate_inventory,
            "retained_frame_bolts": frame_inventory,
            "current_panel_screw_axes": screw_inventory,
        },
        "edges": edges,
        "assumptions_and_limits": [
            "The node set is the complete raw/finished wood and panel set returned by the current WJ12 composed-wood helper.",
            "AABB-separated pairs are definitively noncontacting within the recorded tolerance; their exact BRep distance is not evaluated and only the AABB lower bound is reported.",
            "A candidate receiver membership associates an axis with every unordered member pair in that membership; it does not infer physical head-to-nut or adjacency order.",
            "Retained frame-bolt rows preserve source membership only; source member order is not interpreted as a physical stack order.",
            "Panel-screw associations use the current 66-axis map and current revision report; screw envelope overlap does not establish embedment or resistance.",
            "Finite face contacts, separations, and solid overlaps are geometry only; they do not establish active contact, load sharing, compatibility, strength, stiffness, or capacity.",
            "No floor, anchor, or household-support surface is included in this graph.",
        ],
    }
