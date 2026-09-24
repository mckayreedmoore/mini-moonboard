"""WJ-05 audit of all fixed panel/kicker screw receivers and frame paths.

This is geometry and path accounting.  It does not establish screw capacity,
new structural-joint capacity, delivered material, or a fabrication release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import cadquery as cq

from mini_moonboard.connection_geometry import material_intervals
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.wood_joint_frame import build_outer_nodes
from mini_moonboard.wood_joint_wj05_socket import (
    KOKEN_3305A_7_16_PRODUCT,
    KOKEN_PRODUCT_URL,
    KOKEN_SOCKET_H1_MM,
    KOKEN_SOCKET_LENGTH_MM,
    KOKEN_SOCKET_OUTSIDE_DIAMETER_MM,
    KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
    KOKEN_SOCKET_WORKING_END_DIAMETER_MM,
    seated_koken_3305a_7_16_envelope,
    wj05_socket_occupancy_intent,
)
from scripts.owner_layout_protected import inventory as protected_inventory
from scripts.wood_joints_wj05_center_backer_transfer_probe import (
    BACKER_BOLT_STATIONS as ADOPTED_BACKER_BOLT_COORDS,
)
from scripts.wood_joints_wj05_center_backer_transfer_probe import (
    BACKER_X_MM,
    BACKER_Y_MM,
    BACKER_Z_MM,
    BOLT_DIAMETER_MM,
    BOLT_UNDERHEAD_Z_MM,
    BORE_DIAMETER_MM,
    BOTTOM_COUNTERBORE_DEPTH_MM,
    BOTTOM_COUNTERBORE_DIAMETER_MM,
    BOTTOM_WASHER_THICKNESS_MM,
    HEAD_DIAMETER_ENVELOPE_MM,
    HEAD_HEIGHT_MM,
    HEADER_Z_MM,
    NOMINAL_BOLT_LENGTH_MM,
    NUT_DIAMETER_ENVELOPE_MM,
    NUT_HEIGHT_MM,
    TOP_WASHER_STACK_MAX_MM,
    WASHER_DIAMETER_MM,
    _source_and_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
OUTPUT_JSON = ROOT / "docs/wood-joints-mvp/wj05-receiver-audit.json"
OUTPUT_MD = ROOT / "docs/wood-joints-mvp/wj05-receiver-audit.md"
SIDES = ("left", "right")
SUPPORT_PROBE_RADIAL_WIDTH_MM = 1.0
SUPPORT_PROBE_END_INSET_MM = 0.05
CENTER_DUTY_BLOCKERS = (
    "clip_split_header_center_left",
    "clip_split_header_center_right",
    "clip_split_base_center_left",
    "clip_split_base_center_right",
)
FOUR_DIAMETER_MM = 4 * BOLT_DIAMETER_MM
SOURCE_FILES = (
    SOURCE_INVENTORY,
    ROOT / "mini_moonboard/wood_joint_frame.py",
    ROOT / "scripts/wood_joints_wj05_center_backer_transfer_probe.py",
    ROOT / "mini_moonboard/wood_joint_wj05_socket.py",
    Path(__file__),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bounds(shape: cq.Shape) -> list[float]:
    box = shape.BoundingBox()
    return [
        round(value, 6)
        for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def _volume(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    if (
        a.xmax < b.xmin
        or b.xmax < a.xmin
        or a.ymax < b.ymin
        or b.ymax < a.ymin
        or a.zmax < b.zmin
        or b.zmax < a.zmin
    ):
        return 0.0
    return first.intersect(second).Volume()


def _axis_shape(row: dict) -> cq.Shape:
    return cq.Solid.makeCylinder(
        row["source_occupied_diameter_mm"] / 2,
        row["shop_purchased_length_mm"],
        cq.Vector(*row["origin_global_xyz_mm"]),
        cq.Vector(*row["axis_global_xyz"]).normalized(),
    )


def _backer_station_shapes(x: float, y: float) -> dict[str, cq.Shape]:
    axis = cq.Vector(0, 0, 1)
    top_washer_z = HEADER_Z_MM[1]
    top_nut_z = top_washer_z + TOP_WASHER_STACK_MAX_MM
    bottom_head_z = (
        BOTTOM_COUNTERBORE_DEPTH_MM
        - BOTTOM_WASHER_THICKNESS_MM
        - HEAD_HEIGHT_MM
    )
    top_socket = seated_koken_3305a_7_16_envelope(
        (x, y),
        top_nut_z,
        outward_z=1,
        target_bounds_z_mm=(top_nut_z, top_nut_z + NUT_HEIGHT_MM),
    )
    bottom_socket = seated_koken_3305a_7_16_envelope(
        (x, y),
        BOLT_UNDERHEAD_Z_MM,
        outward_z=-1,
        target_bounds_z_mm=(bottom_head_z, BOLT_UNDERHEAD_Z_MM),
    )
    return {
        "bore": cq.Solid.makeCylinder(
            BORE_DIAMETER_MM / 2,
            HEADER_Z_MM[1],
            cq.Vector(x, y, 0),
            axis,
        ),
        "counterbore": cq.Solid.makeCylinder(
            BOTTOM_COUNTERBORE_DIAMETER_MM / 2,
            BOTTOM_COUNTERBORE_DEPTH_MM,
            cq.Vector(x, y, 0),
            axis,
        ),
        "bolt": cq.Solid.makeCylinder(
            BOLT_DIAMETER_MM / 2,
            NOMINAL_BOLT_LENGTH_MM,
            cq.Vector(x, y, BOLT_UNDERHEAD_Z_MM),
            axis,
        ),
        "bottom_washer": cq.Solid.makeCylinder(
            WASHER_DIAMETER_MM / 2,
            BOTTOM_WASHER_THICKNESS_MM,
            cq.Vector(
                x,
                y,
                BOTTOM_COUNTERBORE_DEPTH_MM - BOTTOM_WASHER_THICKNESS_MM,
            ),
            axis,
        ),
        "bottom_head": cq.Solid.makeCylinder(
            HEAD_DIAMETER_ENVELOPE_MM / 2,
            HEAD_HEIGHT_MM,
            cq.Vector(x, y, bottom_head_z),
            axis,
        ),
        "top_washer": cq.Solid.makeCylinder(
            WASHER_DIAMETER_MM / 2,
            TOP_WASHER_STACK_MAX_MM,
            cq.Vector(x, y, top_washer_z),
            axis,
        ),
        "top_nut": cq.Solid.makeCylinder(
            NUT_DIAMETER_ENVELOPE_MM / 2,
            NUT_HEIGHT_MM,
            cq.Vector(x, y, top_nut_z),
            axis,
        ),
        # Preserve approach endpoint and screen seated and swept occupancy.
        "top_tool": top_socket.approach_endpoint_envelope,
        "top_tool_seated": top_socket.external_envelope,
        "top_tool_approach_sweep": top_socket.approach_sweep_envelope,
        "bottom_tool": bottom_socket.approach_endpoint_envelope,
        "bottom_tool_seated": bottom_socket.external_envelope,
        "bottom_tool_approach_sweep": bottom_socket.approach_sweep_envelope,
    }


def _candidate_receiver_shapes(rows: list[dict]):
    model = variant(KERF_RIGHT)
    uncut = {part.name: part.shape for part in model.uncut_wood_parts()}
    finished = {
        part.name: part.shape for part in model.parts() if part.name in uncut
    }

    # WJ-03 source hosts include retained selected-candidate openings plus the
    # candidate's new bores.  Use those net solids rather than uncut proxies.
    nodes = build_outer_nodes()
    for node in nodes.values():
        for name, part in node.source_host_parts.items():
            finished[name] = part.finished_shape

    (
        _model,
        _source_wood,
        center_wood,
        backers,
        _bolts,
        _bores,
        _stacks,
        _tools,
        _counterbores,
    ) = _source_and_candidate()
    station_shapes = {}
    for side, coords in ADOPTED_BACKER_BOLT_COORDS.items():
        for index, (x, y) in enumerate(coords, 1):
            station_id = f"backer_header_{side}_{index}"
            station_shapes[station_id] = _backer_station_shapes(x, y)
            bore = station_shapes[station_id]["bore"]
            finished["base_header"] = finished["base_header"].cut(bore).clean()
    for side in SIDES:
        name = f"inner_kicker_backer_{side}"
        uncut[name] = backers[name]
        body = backers[name]
        for index, _coords in enumerate(ADOPTED_BACKER_BOLT_COORDS[side], 1):
            shapes = station_shapes[f"backer_header_{side}_{index}"]
            body = body.cut(shapes["bore"]).cut(shapes["counterbore"])
        finished[name] = body.clean()

    # Persist the fixed center screw openings in the proposed finished backers.
    for row in rows:
        receiver = row["candidate_finished_receiver_member"]
        if receiver.startswith("inner_kicker_backer_"):
            finished[receiver] = finished[receiver].cut(_axis_shape(row)).clean()
    return uncut, finished, station_shapes, center_wood


def _receiver_record(row: dict, uncut: cq.Shape, finished: cq.Shape) -> dict:
    origin = cq.Vector(*row["origin_global_xyz_mm"])
    direction = cq.Vector(*row["axis_global_xyz"]).normalized()
    length = row["shop_purchased_length_mm"]
    intervals = material_intervals(uncut, origin, direction, 0.0, length)
    if len(intervals) != 1:
        raise ValueError(
            f"Expected one receiver interval for {row['axis_id']}; got {intervals}"
        )
    start, end = intervals[0]
    probe_start = start + SUPPORT_PROBE_END_INSET_MM
    probe_length = end - start - 2 * SUPPORT_PROBE_END_INSET_MM
    if probe_length <= 0:
        raise ValueError(f"Receiver interval too short for {row['axis_id']}")
    radius = row["source_occupied_diameter_mm"] / 2
    probe_origin = origin + direction * probe_start
    inner = cq.Solid.makeCylinder(radius, probe_length, probe_origin, direction)
    outer = cq.Solid.makeCylinder(
        radius + SUPPORT_PROBE_RADIAL_WIDTH_MM,
        probe_length,
        probe_origin,
        direction,
    )
    annulus = outer.cut(inner)
    supported = _volume(annulus, finished)
    support_fraction = supported / annulus.Volume()
    receiver = row["candidate_finished_receiver_member"]
    is_backer = receiver.startswith("inner_kicker_backer_")
    side = "left" if "_left_" in row["axis_id"] else "right"
    path = (
        [
            receiver,
            f"backer_header_{side}_1/backer_header_{side}_2",
            "base_header",
            *CENTER_DUTY_BLOCKERS,
        ]
        if is_backer
        else [receiver, "integrated replacement interfaces pending WJ-06"]
    )
    return {
        "axis_id": row["axis_id"],
        "panel_member": row["panel_member"],
        "candidate_finished_receiver_member": receiver,
        "axis_origin_global_xyz_mm": row["origin_global_xyz_mm"],
        "axis_direction_global_xyz": row["axis_global_xyz"],
        "fixed_shop_purchased_length_mm": length,
        "source_occupied_diameter_mm": row["source_occupied_diameter_mm"],
        "uncut_receiver_material_interval_from_axis_origin_mm": [
            round(start, 6),
            round(end, 6),
        ],
        "nominal_receiver_embedment_mm": round(end - start, 6),
        "finished_receiver_bounds_xyz_mm": _bounds(finished),
        "finished_receiver_annular_probe": {
            "radial_width_outside_occupied_axis_mm": SUPPORT_PROBE_RADIAL_WIDTH_MM,
            "end_inset_mm": SUPPORT_PROBE_END_INSET_MM,
            "support_fraction": round(support_fraction, 9),
            "continuous_nominal_wood": support_fraction >= 1.0 - 1e-7,
            "scope": "local geometry continuity only; no screw resistance or pilot claim",
        },
        "immediate_receiver_path": path,
        "receiver_is_structural_frame_member": not is_backer,
        "separate_receiver_attachment_geometry_present": is_backer,
        "receiver_attachment_path_status": (
            "blocked_diagnostic_backer_attachment"
            if is_backer
            else "direct_frame_member_no_separate_backer_attachment"
        ),
        "whole_frame_replacement_path_complete": False,
        "physical_receiver_observed": None,
    }


def build_report() -> dict:
    source = json.loads(SOURCE_INVENTORY.read_text())
    rows = source["fixed_panel_kicker_screws"]
    if len(rows) != 66 or len({row["axis_id"] for row in rows}) != 66:
        raise ValueError("WJ-05 requires exactly 66 unique fixed screw axes")
    uncut, finished, station_shapes, center_wood = _candidate_receiver_shapes(rows)
    records = [
        _receiver_record(
            row,
            uncut[row["candidate_finished_receiver_member"]],
            finished[row["candidate_finished_receiver_member"]],
        )
        for row in rows
    ]
    if not all(
        record["finished_receiver_annular_probe"]["continuous_nominal_wood"]
        for record in records
    ):
        raise ValueError("At least one fixed screw lacks finished receiver support")

    protected = protected_inventory()
    wire_id = "wire_072_F1_G1"
    wire = protected["solids"]["wires"][wire_id]
    original_tool = _backer_station_shapes(35.0, -63.0)["top_tool"]
    original_collision = original_tool.intersect(wire)
    original_collision_volume = original_collision.Volume()
    if original_collision_volume <= 0:
        raise ValueError("Original WJ-05 top-tool/wire blocker disappeared")

    protected_hits = {}
    unrelated_wood_hits = {}
    protected_solids = {
        f"{family}/{name}": shape
        for family, solids in protected["solids"].items()
        for name, shape in solids.items()
    }
    unrelated_wood = {
        name: shape
        for name, shape in center_wood.items()
        if name
        not in {
            "base_header",
            "inner_kicker_backer_left",
            "inner_kicker_backer_right",
        }
    }
    for station_id, shapes in station_shapes.items():
        for role, shape in shapes.items():
            key = f"{station_id}/{role}"
            protected_hits[key] = {
                name: round(volume, 6)
                for name, obstacle in protected_solids.items()
                if (volume := _volume(shape, obstacle)) > 0.01
            }
            unrelated_wood_hits[key] = {
                name: round(volume, 6)
                for name, obstacle in unrelated_wood.items()
                if (volume := _volume(shape, obstacle)) > 0.01
            }
    if any(protected_hits.values()) or any(unrelated_wood_hits.values()):
        raise ValueError("Repaired WJ-05 backer station has a new nominal collision")

    center_axes = [
        record
        for record in records
        if record["candidate_finished_receiver_member"].startswith(
            "inner_kicker_backer_"
        )
    ]
    receiver_counts = Counter(
        record["candidate_finished_receiver_member"] for record in records
    )
    panel_counts = Counter(
        "kicker" if record["panel_member"].startswith("kicker_") else "main_panel"
        for record in records
    )
    edge_samples = {}
    seam_x = BACKER_X_MM["left"][1]
    for side in SIDES:
        edge_x = seam_x + (-0.5 if side == "left" else 0.5)
        points = [[edge_x, -36.1, z] for z in (0.5, 112.5, 238.4)]
        body = uncut[f"inner_kicker_backer_{side}"]
        edge_samples[side] = {
            "sample_points_global_xyz_mm": points,
            "all_inside_receiver": all(
                body.isInside(cq.Vector(*point), 1e-4) for point in points
            ),
        }

    attachment_bolts = []
    for side, coords in ADOPTED_BACKER_BOLT_COORDS.items():
        backer_box = uncut[f"inner_kicker_backer_{side}"].BoundingBox()
        for index, (x, y) in enumerate(coords, 1):
            bolt_id = f"backer_header_{side}_{index}"
            bore = station_shapes[bolt_id]["bore"]
            backer = uncut[f"inner_kicker_backer_{side}"]
            header = uncut["base_header"]
            edge_distance = min(
                x - backer_box.xmin,
                backer_box.xmax - x,
                y - backer_box.ymin,
                backer_box.ymax - y,
            )
            top_tool = station_shapes[bolt_id]["top_tool"]
            top_seated_tool = station_shapes[bolt_id]["top_tool_seated"]
            top_approach_sweep = station_shapes[bolt_id]["top_tool_approach_sweep"]
            bolt = station_shapes[bolt_id]["bolt"]
            principal_id = f"base_principal_center_{side}"
            principal = unrelated_wood[principal_id]
            top_nut_z = HEADER_Z_MM[1] + TOP_WASHER_STACK_MAX_MM
            bottom_head_z = (
                BOTTOM_COUNTERBORE_DEPTH_MM
                - BOTTOM_WASHER_THICKNESS_MM
                - HEAD_HEIGHT_MM
            )
            top_socket = seated_koken_3305a_7_16_envelope(
                (x, y),
                top_nut_z,
                outward_z=1,
                target_bounds_z_mm=(top_nut_z, top_nut_z + NUT_HEIGHT_MM),
            )
            bottom_socket = seated_koken_3305a_7_16_envelope(
                (x, y),
                BOLT_UNDERHEAD_Z_MM,
                outward_z=-1,
                target_bounds_z_mm=(bottom_head_z, BOLT_UNDERHEAD_Z_MM),
            )
            attachment_bolts.append(
                {
                    "bolt_id": bolt_id,
                    "axis_global_xyz_mm": [x, y, BOLT_UNDERHEAD_Z_MM],
                    "direction_global_xyz": [0.0, 0.0, 1.0],
                    "clearance_bore_diameter_mm": BORE_DIAMETER_MM,
                    "minimum_center_to_backer_xy_edge_mm": round(
                        edge_distance, 6
                    ),
                    "edge_margin_beyond_4d_mm": round(
                        edge_distance - FOUR_DIAMETER_MM, 6
                    ),
                    "bore_fraction_in_backer": round(
                        _volume(bore, backer) / bore.Volume(), 9
                    ),
                    "bore_fraction_in_header": round(
                        _volume(bore, header) / bore.Volume(), 9
                    ),
                    "top_approach_endpoint_to_named_F1_G1_wire_mm": round(
                        top_tool.distance(wire), 6
                    ),
                    "top_seated_tool_to_named_F1_G1_wire_mm": round(
                        top_seated_tool.distance(wire), 6
                    ),
                    "top_approach_sweep_to_named_F1_G1_wire_mm": round(
                        top_approach_sweep.distance(wire), 6
                    ),
                    "minimum_bolt_or_top_approach_endpoint_to_same_side_principal_mm": round(
                        min(top_tool.distance(principal), bolt.distance(principal)),
                        6,
                    ),
                    "minimum_bolt_or_top_approach_sweep_to_same_side_principal_mm": round(
                        min(
                            top_approach_sweep.distance(principal),
                            bolt.distance(principal),
                        ),
                        6,
                    ),
                    "socket_external_occupancy_intent": {
                        "top_nut": wj05_socket_occupancy_intent(
                            top_socket,
                            target_component="top_nut",
                            target_bounds_z_mm=(
                                top_nut_z,
                                top_nut_z + NUT_HEIGHT_MM,
                            ),
                            target_max_corner_diameter_mm=NUT_DIAMETER_ENVELOPE_MM,
                        ),
                        "bottom_head": wj05_socket_occupancy_intent(
                            bottom_socket,
                            target_component="bottom_bolt_head",
                            target_bounds_z_mm=(
                                bottom_head_z,
                                BOLT_UNDERHEAD_Z_MM,
                            ),
                            target_max_corner_diameter_mm=HEAD_DIAMETER_ENVELOPE_MM,
                        ),
                    },
                    "same_side_principal_id": principal_id,
                    "physical_hardware_observed": None,
                }
            )

    pair_spacing = {}
    for side, coords in ADOPTED_BACKER_BOLT_COORDS.items():
        first, second = (cq.Vector(x, y, 0) for x, y in coords)
        distance = (second - first).Length
        pair_spacing[side] = {
            "center_distance_mm": round(distance, 6),
            "diameter_multiple": round(distance / BOLT_DIAMETER_MM, 6),
            "margin_beyond_4d_mm": round(distance - FOUR_DIAMETER_MM, 6),
        }

    return {
        "schema": "wood_joint_wj05_receiver_audit/v2",
        "candidate": "compact-floor-flush-wood-joints-development",
        "status": "blocked_center_receiver_path",
        "source_fingerprints_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in SOURCE_FILES
        },
        "fixed_axis_identity": {
            "count": len(records),
            "unique_count": len({record["axis_id"] for record in records}),
            "main_panel_axes": panel_counts["main_panel"],
            "kicker_axes": panel_counts["kicker"],
            "axes_moved": 0,
        },
        "receiver_summary": {
            "finished_receiver_geometry_pass_count": sum(
                record["finished_receiver_annular_probe"][
                    "continuous_nominal_wood"
                ]
                for record in records
            ),
            "direct_structural_frame_member_axes": len(records) - len(center_axes),
            "separate_center_backer_axes": len(center_axes),
            "accepted_separate_backer_attachment_axes": 0,
            "receiver_axis_counts": dict(sorted(receiver_counts.items())),
        },
        "axes": records,
        "center_receiver_trial": {
            "socket_outer_envelope_basis": {
                "product": KOKEN_3305A_7_16_PRODUCT,
                "product_url": KOKEN_PRODUCT_URL,
                "listed_dimensions_mm": {
                    "D1_working_end_od": KOKEN_SOCKET_WORKING_END_DIAMETER_MM,
                    "D2_max_od": KOKEN_SOCKET_OUTSIDE_DIAMETER_MM,
                    "H1_hex_engagement": KOKEN_SOCKET_H1_MM,
                    "H2_stud_clearance_depth": KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
                    "L_overall_length": KOKEN_SOCKET_LENGTH_MM,
                },
                "exterior_model": (
                    "D2 max OD applied over full L for seated, approach-endpoint, "
                    "and coaxial insertion-sweep occupancy; D1/H1 do not define "
                    "an inferred stepped outside profile."
                ),
                "internal_profile_and_fit": "12-point cavity, across-corner clearance, fit, and tolerance not modeled or assessed",
            },
            "center_axis_ids": [record["axis_id"] for record in center_axes],
            "backer_bounds_xyz_mm": {
                side: [
                    *BACKER_X_MM[side],
                    *BACKER_Y_MM,
                    *BACKER_Z_MM,
                ]
                for side in SIDES
            },
            "inner_kicker_edge_support": edge_samples,
            "provisional_backer_header_attachment_bolts": attachment_bolts,
            "backer_bolt_pair_spacing": pair_spacing,
            "nominal_collision_screens": {
                "adopted_hardware_and_tools_vs_protected_services_mm3": protected_hits,
                "adopted_hardware_and_tools_vs_unrelated_wood_mm3": unrelated_wood_hits,
                "all_clear": True,
            },
            "path_geometry": (
                "Each separate backer has two provisional vertical through-bolt "
                "bores into base_header; this is an owner-scope-permitted diagnostic, "
                "not an accepted structural path."
            ),
            "accepted": False,
        },
        "resolved_findings": [
            {
                "id": "right_backer_upper_tool_hits_F1_G1_wire",
                "disposition": "repaired_nominal_geometry",
                "fixed_panel_kicker_axes_moved": 0,
                "original_station_global_xy_mm": [35.0, -63.0],
                "repaired_station_global_xy_mm": [25.0, -76.0],
                "original_tool_wire_intersection_volume_mm3": round(
                    original_collision_volume, 6
                ),
                "repaired_tool_wire_intersection_volume_mm3": round(
                    _volume(
                        station_shapes["backer_header_right_2"]["top_tool"],
                        wire,
                    ),
                    6,
                ),
                "repaired_seated_tool_wire_intersection_volume_mm3": round(
                    _volume(
                        station_shapes["backer_header_right_2"][
                            "top_tool_seated"
                        ],
                        wire,
                    ),
                    6,
                ),
                "repaired_approach_sweep_wire_intersection_volume_mm3": round(
                    _volume(
                        station_shapes["backer_header_right_2"][
                            "top_tool_approach_sweep"
                        ],
                        wire,
                    ),
                    6,
                ),
                "repaired_tool_to_wire_clearance_mm": round(
                    station_shapes["backer_header_right_2"]["top_tool"].distance(
                        wire
                    ),
                    6,
                ),
                "repaired_approach_endpoint_to_wire_clearance_mm": round(
                    station_shapes["backer_header_right_2"]["top_tool"].distance(
                        wire
                    ),
                    6,
                ),
                "repaired_seated_tool_to_wire_clearance_mm": round(
                    station_shapes["backer_header_right_2"][
                        "top_tool_seated"
                    ].distance(wire),
                    6,
                ),
                "repaired_approach_sweep_to_wire_clearance_mm": round(
                    station_shapes["backer_header_right_2"][
                        "top_tool_approach_sweep"
                    ].distance(wire),
                    6,
                ),
                "original_tool_bounds_xyz_mm": _bounds(original_tool),
                "original_intersection_bounds_xyz_mm": _bounds(
                    original_collision
                ),
                "repaired_tool_bounds_xyz_mm": _bounds(
                    station_shapes["backer_header_right_2"]["top_tool"]
                ),
                "repaired_seated_tool_bounds_xyz_mm": _bounds(
                    station_shapes["backer_header_right_2"]["top_tool_seated"]
                ),
                "repaired_approach_sweep_bounds_xyz_mm": _bounds(
                    station_shapes["backer_header_right_2"][
                        "top_tool_approach_sweep"
                    ]
                ),
                "paired_right_station_global_xy_mm": [41.0, -98.0],
                "right_pair_spacing": pair_spacing["right"],
                "minimum_right_edge_margin_beyond_4d_mm": min(
                    row["edge_margin_beyond_4d_mm"]
                    for row in attachment_bolts
                    if row["bolt_id"].startswith("backer_header_right_")
                ),
            "scope": (
                    "Catalog outer-envelope proxy only. Approach endpoint, seated "
                    "occupancy, and coaxial insertion sweep are nominal exact solids; "
                    "internal socket fit, tolerances, driver access, and mechanics "
                    "remain unmodeled or open."
                ),
            }
        ],
        "blocking_conditions": [
            {
                "id": "center_structural_duties_not_implemented",
                "legacy_duty_ids": list(CENTER_DUTY_BLOCKERS),
                "resolution_required": (
                    "Model the center principal/header and moved-post/base/header "
                    "interfaces before the base_header endpoint can be called a "
                    "complete integrated candidate path."
                ),
            },
            {
                "id": "backer_attachment_hardware_unselected",
                "bolt_ids": [row["bolt_id"] for row in attachment_bolts],
                "resolution_required": (
                    "Select and verify complete bolt stacks, delivered thread "
                    "transition, tools, tolerances, and joint resistance."
                ),
            },
        ],
        "physical_observations": {
            "receiver_stock": None,
            "screw_axes": None,
            "backer_bolts": None,
            "inner_edge_support": None,
            "service_routing": None,
            "complete": False,
        },
        "release_flags": {
            "layout_complete": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "climbing_released": False,
        },
        "limits": [
            "The 1 mm annular probe checks nominal finished-wood continuity around the modeled occupied axis; it is not a pilot, thread, embedment-capacity, edge-distance, or split-resistance criterion.",
            "The retained Hillman policy and all 66 axis coordinates are unchanged.",
            "The repaired right backer bolt pair has positive nominal 4D edge and spacing margins and nominal service/wood clearance across the approach endpoint, seated, and coaxial-sweep envelopes; no tolerance or resistance acceptance is inferred.",
            "The Ko-ken external-envelope proxy does not model the internal 12-point profile, clearance fit, ratchet, extension, drive-end access, or any path beyond the coaxial insertion sweep.",
            "Direct reception by a structural frame member does not qualify that member's pending replacement interfaces or the integrated frame.",
            "No physical stock, hole, fastener, service route, or edge support was observed.",
        ],
    }


def render_markdown(report: dict) -> str:
    blockers = report["blocking_conditions"]
    resolved = report["resolved_findings"][0]
    counts = report["receiver_summary"]
    lines = [
        "# WJ-05 fixed screw receiver audit",
        "",
        "Status: **blocked center receiver path**. Geometry audit only; every release flag remains false.",
        "",
        "## Inventory result",
        "",
        "| Item | Result |",
        "|---|---:|",
        f"| Fixed axes enumerated | {report['fixed_axis_identity']['count']} |",
        f"| Main panel / kicker axes | {report['fixed_axis_identity']['main_panel_axes']} / {report['fixed_axis_identity']['kicker_axes']} |",
        f"| Finished receiver annular checks passed | {counts['finished_receiver_geometry_pass_count']} |",
        f"| Axes received directly by structural frame timber | {counts['direct_structural_frame_member_axes']} |",
        f"| Axes received by separate center backers | {counts['separate_center_backer_axes']} |",
        "| Fixed axes moved | 0 |",
        "",
        "Every axis has one 45.24375 mm nominal uncut receiver interval. The checked-in JSON records every coordinate, receiver, finished-solid bound, local annular support result, and immediate path. This confirms nominal wood continuity around each modeled axis. It does not establish Hillman resistance or a pilot instruction.",
        "",
        "## Center and inner-edge result",
        "",
        "The four center kicker axes are `round_kicker_left_center_1`, `round_kicker_left_center_2`, `round_kicker_right_center_1`, and `round_kicker_right_center_2`. They enter the two 88.9 × 88.9 × 238.9 mm diagnostic backers at X=±70 mm and Z=60/192 mm. Both three-point kerf-right inner-edge samples lie inside their assigned backers.",
        "",
        "Two provisional vertical bores per backer reach `base_header`, but that path is not accepted. It remains a diagnostic topology.",
        "",
        "## Socket outer-envelope path screen",
        "",
        "Both producers now use one Ko-ken 3305A-7/16 outside-envelope proxy. It records the seated socket from each hex fastener's far face, preserves the former approach endpoint, and screens the continuous coaxial sweep between them. Top seat datum is the nut bearing face at Z=283.096 mm; bottom seat datum is the bolt underhead face at Z=4.968 mm. The fastener's intended occupancy is recorded separately; it is excluded only from obstacle clashing. The 12-point internal profile and engagement fit are not modeled.",
        (
            "At the repaired right upper station `(25, −76)`, current nominal "
            f"proxy clearances to `wire_072_F1_G1` are "
            f"{resolved['repaired_seated_tool_to_wire_clearance_mm']:.6f} mm "
            "for seated body and "
            f"{resolved['repaired_approach_sweep_to_wire_clearance_mm']:.6f} mm "
            "for full approach sweep. The preserved approach endpoint alone "
            f"measures {resolved['repaired_tool_to_wire_clearance_mm']:.6f} mm. "
            "The prior approach-only model at station `(35, −63)` recorded "
            f"{resolved['original_tool_wire_intersection_volume_mm3']:.6f} mm³ "
            "wire overlap. These are nominal outside-envelope diagnostics, not "
            "tool-fit, tolerance, or access acceptance."
        ),
        "",
        f"The right pair center spacing is {resolved['right_pair_spacing']['center_distance_mm']:.6f} mm ({resolved['right_pair_spacing']['diameter_multiple']:.6f}D), leaving {resolved['right_pair_spacing']['margin_beyond_4d_mm']:.6f} mm beyond 4D. The minimum right backer center-to-edge margin beyond 4D is {resolved['minimum_right_edge_margin_beyond_4d_mm']:.6f} mm. Tool path, bolt, bore, stack, and backer proxy solids are screened against protected services and unrelated wood. These nominal checks carry no tolerance acceptance.",
        "",
        "## Exact blockers",
        "",
        "- The center structural duties remain unimplemented: " + ", ".join(f"`{name}`" for name in blockers[0]["legacy_duty_ids"]) + ".",
        "- The four provisional backer/header bolt stacks remain unselected and lack complete joint evidence.",
        "",
        "Physical observation fields remain blank. No drilling, fabrication, structural, or climbing release is made.",
        "",
    ]
    return "\n".join(lines)


def write_outputs() -> None:
    report = build_report()
    OUTPUT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    OUTPUT_MD.write_text(render_markdown(report))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_outputs()
    else:
        print(json.dumps(build_report(), indent=2))


if __name__ == "__main__":
    main()
