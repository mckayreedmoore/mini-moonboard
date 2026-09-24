"""Diagnostic WJ-05 center trial with the posts at X=±190 mm.

This separately named trial moves only the center posts, lower cleats and
eight lower fastener axes. It rebuilds their bores and installed stacks from
the transformed geometry. It assigns no resistance and releases no work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_panel_machining import candidate_panel_replacements
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_tool_access as shared_tool_access
from scripts import wood_joint_wj05_center_node_probe as center_probe
from scripts import wood_joint_wj05_center_offset_adapter as offset_adapter
from scripts import wood_joint_wj05_center_tools as center_tools
from scripts import wood_joints_wj05_center_backer_transfer_probe as backer_trial
from scripts.owner_layout_protected import inventory as protected_inventory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/wood-joints-mvp/hypotheses/wj05-center-post-x190.json"
SCHEMA = "wood_joint_wj05_center_post_x190_probe/v1"
GEOMETRY_TOLERANCE_MM3 = center_probe.GEOMETRY_TOL_MM3
TOOL_STROKE_DEGREES = center_tools.STROKE_DEGREES
STATION_IDS = center_tools.STATION_IDS
PREFERRED_STROKE_DEGREES = {"left": -5.0, "right": 5.0}
COUNTERHOLD_HEADING_X = {"left": -1.0, "right": 1.0}


@dataclass(frozen=True)
class MaterializedCenterPostX190:
    """All source-bound shapes for one isolated post-offset trial."""

    trial_id: str
    source_fingerprints_sha256: dict[str, str]
    tool_source_fingerprints_sha256: dict[str, str]
    axes: list[dict[str, Any]]
    movement_records: dict[str, list[dict[str, Any]]]
    parts: dict[str, cq.Shape]
    finished_parts: dict[str, cq.Shape]
    candidates: dict[str, cq.Shape]
    fastener_shapes: dict[str, dict[str, cq.Shape]]
    fixed_axes: dict[str, cq.Shape]
    frame_records: list[dict[str, Any]]
    frame_shapes: dict[str, cq.Shape]
    backer_installed_shapes: dict[str, cq.Shape]
    backer_tool_shapes: dict[str, cq.Shape]
    protected_shapes: dict[str, cq.Shape]
    protected_wires: dict[str, cq.Shape]
    retained_legacy_connectors: dict[str, cq.Shape]
    retained_legacy_sds: dict[str, cq.Shape]
    retained_legacy_inventory: dict[str, Any]
    fixed_axis_identity: dict[str, Any]


def _source_fingerprints() -> dict[str, str]:
    paths = {
        **center_probe._source_bindings(),
        "scripts/wood_joint_wj05_center_offset_adapter.py": hashlib.sha256(
            (ROOT / "scripts/wood_joint_wj05_center_offset_adapter.py").read_bytes()
        ).hexdigest(),
        "scripts/wood_joint_wj05_center_post_x190_probe.py": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
    }
    return dict(sorted(paths.items()))


def _tool_source_fingerprints() -> dict[str, str]:
    paths = {
        **center_tools._tool_source_fingerprints(),
        "scripts/wood_joint_wj05_center_offset_adapter.py": hashlib.sha256(
            (ROOT / "scripts/wood_joint_wj05_center_offset_adapter.py").read_bytes()
        ).hexdigest(),
        "scripts/wood_joint_wj05_center_post_x190_probe.py": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
    }
    return dict(sorted(paths.items()))


def _fixed_identity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    identity = [
        {
            "axis_id": row["axis_id"],
            "origin_global_xyz_mm": row["origin_global_xyz_mm"],
            "axis_global_xyz": row["axis_global_xyz"],
            "shop_purchased_length_mm": row["shop_purchased_length_mm"],
            "candidate_finished_receiver_member": row[
                "candidate_finished_receiver_member"
            ],
        }
        for row in rows
    ]
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    counts = center_probe._fixed_axis_member_counts(rows)
    return {
        "count": len(rows),
        "unique_count": len({row["axis_id"] for row in rows}),
        **counts,
        "axes_moved": 0,
        "identity_sha256": digest,
        "all_source_axis_ids_retained": len(identity) == 66,
    }


def materialize_geometry() -> MaterializedCenterPostX190:
    """Materialize the candidate only; call only in a granted CAD slot."""
    inventory = json.loads(center_probe.SOURCE_INVENTORY.read_text())
    (
        model,
        _source_wood,
        source_parts,
        _backers,
        backer_bolts,
        _backer_bores,
        backer_stacks,
        backer_tools,
        _counterbores,
    ) = backer_trial._source_and_candidate()

    panel_replacements = candidate_panel_replacements(
        model,
        current_parts=model.parts(),
        uncut_parts=model.uncut_wood_parts(),
    )
    for name, part in panel_replacements.items():
        source_parts[name] = part.shape

    source_candidate_parts = center_probe._candidate_parts(source_parts)
    base_axes = [
        axis
        for side in center_probe.SIDES
        for axis in (
            center_probe._upper_fastener_axes(side)
            + center_probe._lower_fastener_axes(side)
        )
    ]
    axes, moved_axis_records = offset_adapter.shift_lower_axes_outward(base_axes)
    parts, moved_member_records = offset_adapter.shift_lower_members_outward(
        source_candidate_parts
    )

    post_center_records = {}
    for side in ("left", "right"):
        name = f"base_post_center_{side}"
        source_box = source_candidate_parts[name].BoundingBox()
        trial_box = parts[name].BoundingBox()
        source_center_x = (source_box.xmin + source_box.xmax) / 2
        trial_center_x = (trial_box.xmin + trial_box.xmax) / 2
        expected_source = offset_adapter.SOURCE_POST_CENTERS_MM[side]
        expected_trial = offset_adapter.TRIAL_POST_CENTERS_MM[side]
        if abs(source_center_x - expected_source) > 1e-6:
            raise ValueError(f"source {name} center is no longer at {expected_source} mm")
        if abs(trial_center_x - expected_trial) > 1e-6:
            raise ValueError(f"trial {name} center is not at {expected_trial} mm")
        post_center_records[side] = {
            "side": side,
            "source_center_x_mm": round(source_center_x, 6),
            "trial_center_x_mm": round(trial_center_x, 6),
        }

    finished_parts = center_probe._finished_trial_parts(axes, parts)
    fixed_rows = inventory["fixed_panel_kicker_screws"]
    fixed_identity = _fixed_identity(fixed_rows)
    fixed_axes = {
        row["axis_id"]: center_probe._inventory_axis_shape(row, fixed_screw=True)
        for row in fixed_rows
    }
    frame_records, frame_shapes = center_probe._source_frame_bolt_records(
        model, inventory["starting_frame_bolts"]
    )
    backer_installed, backer_tool_shapes = center_probe._active_backer_components(
        backer_bolts,
        backer_stacks,
        backer_tools,
    )
    protected = protected_inventory()
    protected_shapes = {
        f"{family}/{name}": shape
        for family, shapes in protected["solids"].items()
        for name, shape in shapes.items()
    }
    protected_wires = protected["solids"].get("wires", {})
    retained_connectors, retained_sds, retained_legacy_inventory = (
        center_tools._retained_legacy_hardware(model, inventory)
    )
    fastener_shapes = {
        axis["axis_id"]: center_probe._fastener_shapes(axis) for axis in axes
    }
    candidates = {
        name: shape
        for name, shape in parts.items()
        if name.startswith(("center_post_cleat_", "center_principal_cleat_"))
    }
    if len(candidates) != 4:
        raise ValueError("expected exactly four candidate center cleats")
    if len(fixed_axes) != 66 or len(frame_records) != 12:
        raise ValueError("fixed panel/kicker or retained frame-bolt inventory changed")
    if len(retained_connectors) != 20 or len(retained_sds) != 120:
        raise ValueError("retained legacy connector inventory changed")

    movement_records = {
        "members": moved_member_records,
        "axes": moved_axis_records,
        "post_centers": post_center_records,
    }
    return MaterializedCenterPostX190(
        trial_id=offset_adapter.TRIAL_ID,
        source_fingerprints_sha256=_source_fingerprints(),
        tool_source_fingerprints_sha256=_tool_source_fingerprints(),
        axes=axes,
        movement_records=movement_records,
        parts=parts,
        finished_parts=finished_parts,
        candidates=candidates,
        fastener_shapes=fastener_shapes,
        fixed_axes=fixed_axes,
        frame_records=frame_records,
        frame_shapes=frame_shapes,
        backer_installed_shapes=backer_installed,
        backer_tool_shapes=backer_tool_shapes,
        protected_shapes=protected_shapes,
        protected_wires=protected_wires,
        retained_legacy_connectors=retained_connectors,
        retained_legacy_sds=retained_sds,
        retained_legacy_inventory=retained_legacy_inventory,
        fixed_axis_identity=fixed_identity,
    )


def _axis_records(geometry: MaterializedCenterPostX190) -> tuple[list[dict], dict]:
    records, pair_checks = center_probe._axis_checks(geometry.axes, geometry.parts)
    for row in records:
        if row["axis_id"].startswith("center_post_header_"):
            point = row["origin_global_xyz_mm"]
            cleat = geometry.parts[row["intended_receivers"][0]].BoundingBox()
            row["distance_screen"] = {
                "cleat_x_edge_distances_mm": [
                    round(point[0] - cleat.xmin, 6),
                    round(cleat.xmax - point[0], 6),
                ],
                "cleat_y_edge_distances_mm": [
                    round(point[1] - cleat.ymin, 6),
                    round(cleat.ymax - point[1], 6),
                ],
                "header_y_edge_distances_mm": [
                    round(point[1] + 175.7, 6),
                    round(-36.0 - point[1], 6),
                ],
                "conditional_screens_mm": {
                    "4D_edge": center_probe.FOUR_D_MM,
                    "5D_pair_spacing": center_probe.FIVE_D_MM,
                },
                "note": (
                    "Geometry only. Distances use the shifted lower-cleat bounds; "
                    "loaded side and governing NDS category need signed actions."
                ),
            }
    return records, pair_checks


def counterhold_heading(side: str) -> cq.Vector:
    """Return the outward, away-from-center wrench heading for one side."""
    if side not in COUNTERHOLD_HEADING_X:
        raise ValueError(f"unknown center side: {side!r}")
    return cq.Vector(COUNTERHOLD_HEADING_X[side], 0, 0)


def preferred_stroke_degrees(side: str) -> float:
    """Return the signed 5-degree sector that avoids the local backer."""
    if side not in PREFERRED_STROKE_DEGREES:
        raise ValueError(f"unknown center side: {side!r}")
    return PREFERRED_STROKE_DEGREES[side]


def preferred_route_operation_ids(side: str) -> tuple[str, ...]:
    preferred = preferred_stroke_degrees(side)
    return (
        "seated_socket_extension_and_inline_ratchet",
        "outward_nut_counterhold",
        f"ratchet_bounded_stroke_{preferred:+g}_degrees",
        "counterhold_vs_static_head_side_tools",
        f"counterhold_vs_ratchet_stroke_{preferred:+g}_degrees",
    )


def preferred_route_status(
    operations: dict[str, Any], side: str
) -> dict[str, Any]:
    checked = preferred_route_operation_ids(side)
    missing = set(checked) - set(operations)
    if missing:
        raise ValueError(f"preferred route operations missing: {sorted(missing)}")
    return {
        "checked_operations": list(checked),
        "clear": all(_operation_clear(operations[name]) for name in checked),
        "alternate_stroke_gates_preferred_route": False,
    }


def _outward_counterhold(
    axis: dict[str, Any], nut: cq.Shape
) -> tuple[cq.Shape, cq.Vector]:
    bolt_direction = cq.Vector(*axis["direction_global_xyz"]).normalized()
    if abs(abs(bolt_direction.z) - 1.0) > 1e-8:
        raise ValueError("center header counterhold requires a vertical bolt axis")
    heading = counterhold_heading(axis.get("side"))
    nut_center = shared_tool_access._seated_tool_center(
        cq.Vector(*axis["origin_global_xyz_mm"]),
        bolt_direction,
        nut,
        WJ04_TRIAL.fasteners.tools[0].head_thickness_mm,
    )
    envelope = shared_tool_access.build_catalog_wrench_envelope(
        nut_center,
        bolt_direction.toTuple(),
        heading.toTuple(),
        WJ04_TRIAL.fasteners.tools[0],
        offset_degrees=0.0,
    )
    return envelope, heading


def _member_contact_projection(
    first: cq.Shape,
    second: cq.Shape,
    *,
    normal_axis: str,
    first_face: str,
    second_face: str,
) -> dict[str, Any]:
    a, b = first.BoundingBox(), second.BoundingBox()
    coordinate = {"x": 0, "y": 1, "z": 2}[normal_axis]
    a_bounds = ((a.xmin, a.xmax), (a.ymin, a.ymax), (a.zmin, a.zmax))
    b_bounds = ((b.xmin, b.xmax), (b.ymin, b.ymax), (b.zmin, b.zmax))
    face_a = a_bounds[coordinate][1 if first_face == "max" else 0]
    face_b = b_bounds[coordinate][1 if second_face == "max" else 0]
    overlap_axes = [index for index in range(3) if index != coordinate]
    lengths = []
    for index in overlap_axes:
        low = max(a_bounds[index][0], b_bounds[index][0])
        high = min(a_bounds[index][1], b_bounds[index][1])
        lengths.append(max(0.0, high - low))
    return {
        "normal_axis": normal_axis,
        "source_face_coordinate_mm": round(face_a, 6),
        "mate_face_coordinate_mm": round(face_b, 6),
        "faces_coincident": abs(face_a - face_b) <= 1e-6,
        "projected_overlap_lengths_mm": [round(value, 6) for value in lengths],
        "gross_projected_contact_area_mm2": round(lengths[0] * lengths[1], 6),
        "net_of_bores": False,
    }


def _contact_geometry(geometry: MaterializedCenterPostX190) -> dict[str, Any]:
    contacts = {}
    for side in ("left", "right"):
        post = geometry.parts[f"base_post_center_{side}"]
        lower = geometry.parts[f"center_post_cleat_{side}"]
        upper = geometry.parts[f"center_principal_cleat_{side}"]
        principal = geometry.parts[f"base_principal_center_{side}"]
        header = geometry.parts["base_header"]
        contacts[side] = {
            "post_to_lower_cleat": _member_contact_projection(
                post,
                lower,
                normal_axis="x",
                first_face="min" if side == "left" else "max",
                second_face="max" if side == "left" else "min",
            ),
            "lower_cleat_to_header": _member_contact_projection(
                lower,
                header,
                normal_axis="z",
                first_face="max",
                second_face="min",
            ),
            "principal_to_upper_cleat": _member_contact_projection(
                principal,
                upper,
                normal_axis="x",
                first_face="min" if side == "left" else "max",
                second_face="max" if side == "left" else "min",
            ),
            "upper_cleat_to_header": _member_contact_projection(
                upper,
                header,
                normal_axis="z",
                first_face="min",
                second_face="max",
            ),
        }
    return contacts


def _fastener_component_maps(
    geometry: MaterializedCenterPostX190,
) -> tuple[dict[str, cq.Shape], dict[str, cq.Shape], dict[str, cq.Shape]]:
    all_shapes = {
        f"{axis_id}/{role}": shape
        for axis_id, roles in geometry.fastener_shapes.items()
        for role, shape in roles.items()
    }
    bores = {key: shape for key, shape in all_shapes.items() if key.endswith("/bore")}
    physical = {
        key: shape
        for key, shape in all_shapes.items()
        if not key.endswith(("/bore", "/head_tool", "/nut_tool"))
    }
    tools = {
        key: shape
        for key, shape in all_shapes.items()
        if key.endswith(("/head_tool", "/nut_tool"))
    }
    return bores, physical, tools


def _obstacle_groups(
    geometry: MaterializedCenterPostX190,
) -> dict[str, dict[str, cq.Shape]]:
    return {
        "center_trial_timber_conservative": geometry.finished_parts,
        "protected": geometry.protected_shapes,
        "fixed_66_panel_kicker_axes": geometry.fixed_axes,
        "retained_frame_bolt_components_and_axes": geometry.frame_shapes,
        "active_wj05_backer_installed_hardware": geometry.backer_installed_shapes,
        "retained_legacy_connector_bodies": geometry.retained_legacy_connectors,
        "retained_legacy_sds_axes": geometry.retained_legacy_sds,
        "candidate_installed_hardware": {
            f"{axis_id}/{role}": shape
            for axis_id, roles in geometry.fastener_shapes.items()
            for role, shape in roles.items()
            if role not in ("bore", "head_tool", "nut_tool")
        },
    }


def _operation_clear(operation: dict[str, Any]) -> bool:
    return bool(operation.get("external_envelope_clear"))


def _build_catalog_tool_route(
    geometry: MaterializedCenterPostX190,
) -> dict[str, Any]:
    obstacle_groups = _obstacle_groups(geometry)
    obstacles = center_tools._qualified_obstacles(obstacle_groups)
    station_axes = {axis["axis_id"]: axis for axis in geometry.axes if axis["axis_id"] in STATION_IDS}
    result = {}
    for station_id in STATION_IDS:
        axis = station_axes[station_id]
        installed = geometry.fastener_shapes[station_id]
        shapes, pose = center_tools._station_tool_shapes(
            axis,
            installed["head"],
            installed["nut"],
        )
        side = axis["side"]
        shapes["nut_side_counterhold"], away_heading = _outward_counterhold(
            axis, installed["nut"]
        )
        ratchet_heading = pose.pop("inward_handle_heading_xyz")
        pose["ratchet_handle_heading_xyz"] = ratchet_heading
        bolt_direction = cq.Vector(*axis["direction_global_xyz"]).normalized()

        head_id = f"candidate_installed_hardware/{station_id}/head"
        shaft_id = f"candidate_installed_hardware/{station_id}/shaft"
        nut_id = f"candidate_installed_hardware/{station_id}/nut"
        excluded_head = (head_id, shaft_id)
        excluded_nut = (nut_id, shaft_id)
        operations = {
            "seated_socket_extension_and_inline_ratchet": center_tools._screen_operation(
                {
                    name: shapes[name]
                    for name in (
                        "socket_bearing_face_seated_occupancy",
                        "extension_body",
                        "ratchet_inline_body",
                    )
                },
                obstacles,
                floor_z_mm=0.0,
                excluded_target_ids=excluded_head,
                exclusion_scope=(
                    "Only this station's head and shaft are excluded. Other installed "
                    "hardware, wood, fixed axes, and protected shapes remain obstacles."
                ),
            ),
            "outward_nut_counterhold": center_tools._screen_operation(
                {"nut_side_counterhold": shapes["nut_side_counterhold"]},
                obstacles,
                floor_z_mm=0.0,
                excluded_target_ids=excluded_nut,
                exclusion_scope=(
                    "Only this station's nut and shaft are excluded. The wrench heads "
                    "outward, away from center/row 1; jaw engagement is not modeled."
                ),
            ),
        }
        stroke_shapes = {}
        for angle in (-TOOL_STROKE_DEGREES, TOOL_STROKE_DEGREES):
            swept = shared_tool_access.rotational_sweep(
                shapes["ratchet_inline_body"],
                cq.Vector(*axis["origin_global_xyz_mm"]),
                bolt_direction,
                angle,
            )
            stroke_shapes[angle] = swept
            operations[f"ratchet_bounded_stroke_{angle:+g}_degrees"] = (
                center_tools._screen_operation(
                    {
                        "socket_bearing_face_seated_occupancy": shapes[
                            "socket_bearing_face_seated_occupancy"
                        ],
                        "extension_body": shapes["extension_body"],
                        "ratchet_continuous_stroke_envelope": swept,
                    },
                    obstacles,
                    floor_z_mm=0.0,
                    excluded_target_ids=excluded_head,
                    exclusion_scope=(
                        "Only this station's head and shaft are excluded. Stroke is a "
                        "conservative analytic envelope, not a complete wrench motion."
                    ),
                )
            )
        operations["counterhold_vs_static_head_side_tools"] = (
            center_tools._screen_operation(
                {"outward_counterhold": shapes["nut_side_counterhold"]},
                {
                    "head_side_tool/socket": shapes[
                        "socket_bearing_face_seated_occupancy"
                    ],
                    "head_side_tool/extension": shapes["extension_body"],
                    "head_side_tool/ratchet": shapes["ratchet_inline_body"],
                },
                floor_z_mm=0.0,
                exclusion_scope=(
                    "No tools are excluded. This checks the simultaneous outward "
                    "nut counterhold against the seated head-side tool chain."
                ),
            )
        )
        for angle, swept in stroke_shapes.items():
            operations[f"counterhold_vs_ratchet_stroke_{angle:+g}_degrees"] = (
                center_tools._screen_operation(
                    {"outward_counterhold": shapes["nut_side_counterhold"]},
                    {"ratchet_stroke": swept},
                    floor_z_mm=0.0,
                    exclusion_scope=(
                        "No tools are excluded. This checks simultaneous counterhold "
                        "and ratchet stroke envelope overlap."
                    ),
                )
            )
        preferred = preferred_stroke_degrees(side)
        operations["selected_backer_avoiding_stroke"] = {
            "degrees": preferred,
            "source_operation": f"ratchet_bounded_stroke_{preferred:+g}_degrees",
            "backer_avoiding_sector_is_geometry_only": True,
            "alternate_sector_is_diagnostic_only": True,
        }
        selected_route = preferred_route_status(operations, side)
        result[station_id] = {
            "axis": axis,
            "tool_pose_and_seating": {
                **pose,
                "counterhold_heading_xyz": list(away_heading.toTuple()),
                "counterhold_direction": "outward, away from row 1 and center",
                "ratchet_preferred_sector_degrees": preferred,
            },
            "operations": operations,
            "preferred_route_status": selected_route,
        }
    return result


def build_report(geometry: MaterializedCenterPostX190) -> dict[str, Any]:
    """Build nominal body, bore, installed-stack, and tool-route checks."""
    if geometry.trial_id != offset_adapter.TRIAL_ID:
        raise ValueError("geometry trial ID does not match the ±190 mm variant")
    axis_records, pair_checks = _axis_records(geometry)
    bores, physical_hardware, simple_tools = _fastener_component_maps(geometry)
    frame_axis_shapes = {
        name: shape
        for name, shape in geometry.frame_shapes.items()
        if name.endswith("/source_occupied_axis")
    }
    frame_components = {
        name: shape
        for name, shape in geometry.frame_shapes.items()
        if not name.endswith("/source_occupied_axis")
    }
    existing_wood = {
        name: shape
        for name, shape in geometry.parts.items()
        if name not in geometry.candidates
    }
    candidates = geometry.candidates
    moved_posts = {
        name: geometry.parts[name]
        for name in ("base_post_center_left", "base_post_center_right")
    }
    body_members = candidates | moved_posts
    body_other_wood = {
        name: shape
        for name, shape in geometry.parts.items()
        if name not in body_members
    }
    body_member_pair_hits = {}
    body_member_names = list(body_members)
    for index, name in enumerate(body_member_names):
        for other in body_member_names[index + 1 :]:
            volume = center_probe._volume(body_members[name], body_members[other])
            if volume > GEOMETRY_TOLERANCE_MM3:
                body_member_pair_hits[f"{name}/{other}"] = round(volume, 6)
    candidate_candidate_hits = {}
    candidate_names = list(candidates)
    for index, name in enumerate(candidate_names):
        for other in candidate_names[index + 1 :]:
            volume = center_probe._volume(candidates[name], candidates[other])
            if volume > GEOMETRY_TOLERANCE_MM3:
                candidate_candidate_hits[f"{name}/{other}"] = round(volume, 6)

    clearance_maps = {
        "body_members_vs_existing_wood_mm3": center_probe._collision_map(
            body_members, body_other_wood
        ),
        "body_members_vs_fixed_66_axes_mm3": center_probe._collision_map(
            body_members, geometry.fixed_axes
        ),
        "body_members_vs_retained_12_axes_mm3": center_probe._collision_map(
            body_members, frame_axis_shapes
        ),
        "body_members_vs_retained_12_components_mm3": center_probe._collision_map(
            body_members, frame_components
        ),
        "body_members_vs_active_backer_hardware_mm3": center_probe._collision_map(
            body_members, geometry.backer_installed_shapes
        ),
        "body_members_vs_protected_services_mm3": center_probe._collision_map(
            body_members, geometry.protected_shapes
        ),
        "body_members_vs_retained_legacy_connectors_mm3": center_probe._collision_map(
            body_members, geometry.retained_legacy_connectors
        ),
        "body_members_vs_retained_legacy_sds_mm3": center_probe._collision_map(
            body_members, geometry.retained_legacy_sds
        ),
        "body_member_pair_intersections_mm3": body_member_pair_hits,
        "member_solids_vs_backer_tool_envelopes_mm3": center_probe._collision_map(
            body_members, geometry.backer_tool_shapes
        ),
        "cleats_vs_existing_wood_mm3": center_probe._collision_map(
            candidates, existing_wood
        ),
        "cleats_vs_fixed_66_axes_mm3": center_probe._collision_map(
            candidates, geometry.fixed_axes
        ),
        "cleats_vs_retained_12_axes_mm3": center_probe._collision_map(
            candidates, frame_axis_shapes
        ),
        "cleats_vs_retained_12_components_mm3": center_probe._collision_map(
            candidates, frame_components
        ),
        "cleats_vs_active_backer_hardware_mm3": center_probe._collision_map(
            candidates, geometry.backer_installed_shapes
        ),
        "cleats_vs_backer_tool_envelopes_mm3": center_probe._collision_map(
            candidates, geometry.backer_tool_shapes
        ),
        "cleats_vs_protected_services_mm3": center_probe._collision_map(
            candidates, geometry.protected_shapes
        ),
        "cleats_vs_retained_legacy_connectors_mm3": center_probe._collision_map(
            candidates, geometry.retained_legacy_connectors
        ),
        "cleats_vs_retained_legacy_sds_mm3": center_probe._collision_map(
            candidates, geometry.retained_legacy_sds
        ),
        "candidate_cleat_pair_intersections_mm3": candidate_candidate_hits,
        "bores_vs_fixed_66_axes_mm3": center_probe._collision_map(
            bores, geometry.fixed_axes
        ),
        "bores_vs_retained_12_axes_mm3": center_probe._collision_map(
            bores, frame_axis_shapes
        ),
        "bores_vs_retained_12_components_mm3": center_probe._collision_map(
            bores, frame_components
        ),
        "bores_vs_active_backer_hardware_mm3": center_probe._collision_map(
            bores, geometry.backer_installed_shapes
        ),
        "bores_vs_backer_tool_envelopes_mm3": center_probe._collision_map(
            bores, geometry.backer_tool_shapes
        ),
        "bores_vs_protected_services_mm3": center_probe._collision_map(
            bores, geometry.protected_shapes
        ),
        "bores_vs_retained_legacy_sds_mm3": center_probe._collision_map(
            bores, geometry.retained_legacy_sds
        ),
        "bores_vs_retained_legacy_connectors_mm3": center_probe._collision_map(
            bores, geometry.retained_legacy_connectors
        ),
        "installed_hardware_vs_fixed_66_axes_mm3": center_probe._collision_map(
            physical_hardware, geometry.fixed_axes
        ),
        "installed_hardware_vs_retained_12_axes_mm3": center_probe._collision_map(
            physical_hardware, frame_axis_shapes
        ),
        "installed_hardware_vs_retained_12_components_mm3": center_probe._collision_map(
            physical_hardware, frame_components
        ),
        "installed_hardware_vs_backer_hardware_mm3": center_probe._collision_map(
            physical_hardware, geometry.backer_installed_shapes
        ),
        "installed_hardware_vs_backer_tool_envelopes_mm3": center_probe._collision_map(
            physical_hardware, geometry.backer_tool_shapes
        ),
        "installed_hardware_vs_protected_services_mm3": center_probe._collision_map(
            physical_hardware, geometry.protected_shapes
        ),
        "installed_hardware_vs_retained_legacy_connectors_mm3": center_probe._collision_map(
            physical_hardware, geometry.retained_legacy_connectors
        ),
        "installed_hardware_vs_retained_legacy_sds_mm3": center_probe._collision_map(
            physical_hardware, geometry.retained_legacy_sds
        ),
        "installed_hardware_vs_finished_wood_mm3": center_probe._collision_map(
            physical_hardware, geometry.finished_parts
        ),
        "simple_tool_proxies_vs_fixed_66_axes_mm3": center_probe._collision_map(
            simple_tools, geometry.fixed_axes
        ),
        "simple_tool_proxies_vs_retained_12_components_mm3": center_probe._collision_map(
            simple_tools, frame_components
        ),
        "simple_tool_proxies_vs_retained_12_axes_mm3": center_probe._collision_map(
            simple_tools, frame_axis_shapes
        ),
        "simple_tool_proxies_vs_backer_hardware_mm3": center_probe._collision_map(
            simple_tools, geometry.backer_installed_shapes
        ),
        "simple_tool_proxies_vs_backer_tool_envelopes_mm3": center_probe._collision_map(
            simple_tools, geometry.backer_tool_shapes
        ),
        "simple_tool_proxies_vs_protected_services_mm3": center_probe._collision_map(
            simple_tools, geometry.protected_shapes
        ),
        "simple_tool_proxies_vs_retained_legacy_connectors_mm3": center_probe._collision_map(
            simple_tools, geometry.retained_legacy_connectors
        ),
        "simple_tool_proxies_vs_retained_legacy_sds_mm3": center_probe._collision_map(
            simple_tools, geometry.retained_legacy_sds
        ),
        "simple_tool_proxies_vs_finished_wood_mm3": center_probe._collision_map(
            simple_tools, geometry.finished_parts
        ),
        **pair_checks,
    }
    wire_clearance = center_probe._source_wire_clearance(
        {
            name: shape
            for name, shape in candidates.items()
            if name.startswith("center_principal_cleat_")
        },
        geometry.protected_wires,
    )
    tool_route = _build_catalog_tool_route(geometry)
    tool_clear = all(
        station["preferred_route_status"]["clear"] for station in tool_route.values()
    )
    alternate_strokes_clear = {
        station_id: {
            name: operation["external_envelope_clear"]
            for name, operation in station["operations"].items()
            if name.startswith("ratchet_bounded_stroke_")
            and name
            != station["operations"]["selected_backer_avoiding_stroke"][
                "source_operation"
            ]
        }
        for station_id, station in tool_route.items()
    }
    contacts = _contact_geometry(geometry)
    contact_planes_coincident = all(
        interface["faces_coincident"]
        and interface["gross_projected_contact_area_mm2"] > 0.0
        for interfaces in contacts.values()
        for interface in interfaces.values()
    )
    geometric_axis_support = all(
        row["intended_receivers_complete"]
        and row["head_washer_support_fraction"] >= 1.0 - 1e-7
        and row["nut_washer_support_fraction"] >= 1.0 - 1e-7
        and not row["unintended_wood_axis_intersections_mm3"]
        for row in axis_records
    )
    clearance_clear = not center_probe._has_hits(clearance_maps)
    wire_clear = bool(wire_clearance) and all(
        row["distance_gate_passed"] for row in wire_clearance.values()
    )
    geometry_clear = (
        clearance_clear
        and wire_clear
        and geometric_axis_support
        and contact_planes_coincident
        and tool_clear
    )

    source_post_centers = {
        side: geometry.movement_records["post_centers"][side]["source_center_x_mm"]
        for side in ("left", "right")
    }
    mechanics_implications = offset_adapter.geometry_implications()
    mechanics_implications["post_center_x_mm"]["source"] = [
        source_post_centers["left"],
        source_post_centers["right"],
    ]
    return {
        "schema": SCHEMA,
        "trial_id": geometry.trial_id,
        "base_trial_id": center_probe.TRIAL_ID,
        "candidate": "compact-floor-flush-wood-joints-development",
        "scope": "source-bound ±190 mm center-post, lower-cleat, and tool-route diagnostic",
        "status": "nominal_geometry_clear_diagnostic"
        if geometry_clear
        else "blocked_nominal_geometry_diagnostic",
        "source_fingerprints_sha256": geometry.source_fingerprints_sha256,
        "tool_source_fingerprints_sha256": geometry.tool_source_fingerprints_sha256,
        "variant_delta": {
            "post_center_x_mm": {
                "source": source_post_centers,
                "trial": {"left": -190.0, "right": 190.0},
            },
            "moved_members": geometry.movement_records["members"],
            "moved_lower_axes": geometry.movement_records["axes"],
            "upper_cleats_and_axes_fixed": True,
            "fixed_66_panel_kicker_axes_moved": 0,
            "active_backers_moved": 0,
            "retained_12_starting_frame_bolts_moved": 0,
        },
        "mechanics_implications": {
            **mechanics_implications,
            "capacity_transfer": False,
        },
        "fixed_panel_kicker_axis_identity": geometry.fixed_axis_identity,
        "retained_starting_frame_bolts": {
            "count": len(geometry.frame_records),
            "axis_ids": [row["axis_id"] for row in geometry.frame_records],
            "candidate_recheck_status": "required_for_every_retained_bolt",
        },
        "retained_legacy_hardware_inventory": geometry.retained_legacy_inventory,
        "candidate_contacts": contacts,
        "fastener_checks": axis_records,
        "clearance_intersections_mm3": clearance_maps,
        "upper_cleat_source_wire_clearance": wire_clearance,
        "tool_routes": tool_route,
        "summary": {
            "body_clear": not center_probe._has_hits(
                {
                    key: value
                    for key, value in clearance_maps.items()
                    if key.startswith(("body_members_", "body_member_"))
                }
            ),
            "all_bores_and_installed_hardware_clear": not center_probe._has_hits(
                {
                    key: value
                    for key, value in clearance_maps.items()
                    if key.startswith(("bores_", "installed_hardware_"))
                }
            ),
            "all_receivers_and_washer_seats_complete": geometric_axis_support,
            "contact_face_planes_coincident_with_positive_projection": contact_planes_coincident,
            "source_wire_clearance_gate_passed": wire_clear,
            "preferred_tool_routes_clear": tool_clear,
            "alternate_stroke_diagnostics_clear": alternate_strokes_clear,
            "nominal_geometry_clear": geometry_clear,
            "tool_physical_access_established": False,
            "strength_assigned": False,
        },
        "materialization_limits": {
            "timber_obstacle_status": (
                "Raw source-derived frame timber has trial bores, but some retained "
                "source openings may be absent; timber intersections are conservative "
                "pending machining integration."
            ),
            "contact_areas_net_of_bores": False,
            "catalog_tool_fit_verified": False,
            "tool_sweep_tolerance_or_manual_clearance": False,
            "complete_joint_load_path_accepted": False,
        },
        "claims": {
            "nominal_geometry_screen_only": True,
            "physical_tool_access_established": False,
            "tool_fit_established": False,
            "structural_resistance_assigned": False,
            "engineering_or_fabrication_release": False,
        },
        "release_flags": dict(center_probe.RELEASE_FLAGS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the JSON report")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    report = build_report(materialize_geometry())
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
