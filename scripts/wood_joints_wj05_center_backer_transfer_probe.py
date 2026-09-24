"""WJ-05 center kicker backer-to-header transfer trial; diagnostic only.

This source-builds the existing kerf-right kicker backers and moved center
posts, then adds ordinary vertical through-bolts from each backer into the
maintained base header. It does not assign resistance or release machining.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
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
from scripts import owner_layout_protected as protected

AXES_CSV = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
OUTPUT_JSON = ROOT / "docs/wood-joints-mvp/wj05-center-backer-transfer.json"
OUTPUT_MD = ROOT / "docs/wood-joints-mvp/wj05-center-backer-transfer.md"

POST_SHIFT_X_MM = {"left": -110.0, "right": 110.0}
BACKER_X_MM = {
    "left": (-90.4875, -1.5875),
    "right": (-1.5875, 87.3125),
}
BACKER_Y_MM = (-124.9, -36.0)
BACKER_Z_MM = (0.0, 238.9)
BACKER_DIMS_MM = (88.9, 88.9, 238.9)
HEADER_Z_MM = (238.9, 277.0)

# Provisional geometry envelopes only. Bolt pattern is deliberately an
# investigation pose: one 1/4-in-class through-bolt at each y station per side.
BOLT_DIAMETER_MM = 6.35
BORE_DIAMETER_MM = 7.3
WASHER_DIAMETER_MM = 16.256  # 1/4-in Type A narrow washer max OD, .640 in.
WASHER_NOMINAL_THICKNESS_MM = 1.651  # ASME B18.22.1 Type A, .065 in.
WASHER_MIN_THICKNESS_MM = 1.2954  # Type A min, .051 in.
WASHER_MAX_THICKNESS_MM = 2.032  # Type A max, .080 in.
TOP_WASHER_COUNT = 3
NUT_DIAMETER_ENVELOPE_MM = 12.827  # 1/4-in hex nut max across corners, .505 in.
NUT_HEIGHT_MM = 5.7404  # 1/4-in finished hex nut max thickness, .226 in.
HEAD_DIAMETER_ENVELOPE_MM = 12.827  # 1/4-in hex bolt max across corners, .505 in.
HEAD_HEIGHT_MM = 4.7752  # 1/4-in hex bolt max head height, .188 in.
BOTTOM_COUNTERBORE_DIAMETER_MM = 20.0
BOTTOM_COUNTERBORE_DEPTH_MM = 7.0
SOCKET_EXTERNAL_DIAMETER_MM = KOKEN_SOCKET_OUTSIDE_DIAMETER_MM
SOCKET_LENGTH_MM = KOKEN_SOCKET_LENGTH_MM
NOMINAL_BOLT_LENGTH_MM = 304.8  # 12-in diagnostic length, not a selected SKU.
THREAD_PAST_NUT_MM = 3.175
WOOD_GRIP_REQUIRED_MM = 269.94  # Owner-directed effective grip screen.
NOMINAL_THREAD_LENGTH_MM = 25.4  # B18.2.1: LT=2D+0.50 in for bolt >6 in.
THREAD_GAUGE_TOL_MM = 6.35  # Five 1/4-20 UNC pitches.
LENGTH_TOL_MIN_MM = 4.572  # B18.2.1 Table 5: -0.18 in for 1/4-3/8, >6 in.
LENGTH_TOL_MAX_MM = 2.54  # B18.2.1 Table 5: +0.10 in for 1/4-3/8, >6 in.
BOTTOM_WASHER_THICKNESS_MM = WASHER_MAX_THICKNESS_MM
BOLT_UNDERHEAD_Z_MM = BOTTOM_COUNTERBORE_DEPTH_MM - BOTTOM_WASHER_THICKNESS_MM
WOOD_BEARING_START_Z_MM = BOTTOM_COUNTERBORE_DEPTH_MM
WOOD_GRIP_CAD_MM = HEADER_Z_MM[1] - WOOD_BEARING_START_Z_MM
UNDERHEAD_TO_WOOD_END_MM = HEADER_Z_MM[1] - BOLT_UNDERHEAD_Z_MM
HEADER_BEARING_LENGTH_MM = HEADER_Z_MM[1] - HEADER_Z_MM[0]
HEADER_START_FROM_UNDERHEAD_MM = HEADER_Z_MM[0] - BOLT_UNDERHEAD_Z_MM
LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM = HEADER_BEARING_LENGTH_MM / 4
TOP_WASHER_STACK_MIN_MM = TOP_WASHER_COUNT * WASHER_MIN_THICKNESS_MM
TOP_WASHER_STACK_NOMINAL_MM = TOP_WASHER_COUNT * WASHER_NOMINAL_THICKNESS_MM
TOP_WASHER_STACK_MAX_MM = TOP_WASHER_COUNT * WASHER_MAX_THICKNESS_MM
COLLISION_TOL_MM3 = 0.01

# Provisional per-station (x, y) locations. The repaired right pair avoids the
# F1/G1 wire while preserving all fixed panel and kicker screw axes.
BACKER_BOLT_STATIONS = {
    "left": ((-35.0, -97.0), (-35.0, -63.0)),
    "right": ((41.0, -98.0), (25.0, -76.0)),
}

SOURCE_FILES = (
    ROOT / "docs/wood-joints-mvp/source-inventory.json",
    AXES_CSV,
    ROOT / "docs/floor-flush-construction-kerf-right/stock-profiles.json",
    ROOT / "mini_moonboard/compact_floor_flush_frame.py",
    ROOT / "mini_moonboard/floor_flush_width.py",
    ROOT / "mini_moonboard/round_service_wiring.py",
    ROOT / "mini_moonboard/hold_tnut_reinforcement.py",
    ROOT / "scripts/owner_layout_protected.py",
    ROOT / "mini_moonboard/wood_joint_wj05_socket.py",
    Path(__file__),
)


def _box(bounds):
    (x0, x1), (y0, y1), (z0, z1) = bounds
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def _axis(row, length_key="modeled_length_mm", diameter_key="modeled_diameter_mm"):
    start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
    direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
    return cq.Solid.makeCylinder(
        float(row[diameter_key]) / 2,
        float(row[length_key]),
        start,
        direction.normalized(),
    )


def _box_overlap(a, b):
    return not (
        a.xmax < b.xmin
        or b.xmax < a.xmin
        or a.ymax < b.ymin
        or b.ymax < a.ymin
        or a.zmax < b.zmin
        or b.zmax < a.zmin
    )


def _volume(first, second):
    if not _box_overlap(first.BoundingBox(), second.BoundingBox()):
        return 0.0
    return first.intersect(second).Volume()


def _hits(shape, targets, *, tol=COLLISION_TOL_MM3):
    result = {}
    bounds = shape.BoundingBox()
    for name, other in targets.items():
        if _box_overlap(bounds, other.BoundingBox()):
            volume = _volume(shape, other)
            if volume > tol:
                result[name] = round(volume, 6)
    return result


def _read_axes():
    with AXES_CSV.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _fixed_axis_shapes(rows):
    screws, frame_bolts = {}, {}
    for row in rows:
        if row["shop_opening_kind"] == "hillman_panel":
            screws[row["name"]] = _axis(
                row,
                length_key="shop_purchased_length_mm",
                diameter_key="occupied_diameter_mm",
            )
        elif row["kind"] == "bolt":
            frame_bolts[row["name"]] = _axis(row)
    if len(screws) != 66 or len(frame_bolts) != 12:
        raise ValueError(f"Expected 66 panel axes and 12 frame bolts; found {len(screws)}, {len(frame_bolts)}")
    return screws, frame_bolts


def _source_and_candidate():
    model = variant(KERF_RIGHT)
    source_wood = {part.name: part.shape for part in model.uncut_wood_parts()}
    if not {"base_header", "base_post_center_left", "base_post_center_right"} <= set(source_wood):
        raise ValueError("Maintained center header/post source members changed")

    wood = dict(source_wood)
    for side, shift in POST_SHIFT_X_MM.items():
        name = f"base_post_center_{side}"
        wood[name] = wood[name].translate(cq.Vector(shift, 0, 0))

    backers = {
        f"inner_kicker_backer_{side}": _box(
            (
                BACKER_X_MM[side],
                BACKER_Y_MM,
                BACKER_Z_MM,
            )
        )
        for side in ("left", "right")
    }
    bolts, bores, stacks, tools, counterbores = {}, {}, {}, {}, {}
    for side, stations in BACKER_BOLT_STATIONS.items():
        for index, (x, y) in enumerate(stations, start=1):
            name = f"backer_header_{side}_{index}"
            bores[name] = cq.Solid.makeCylinder(
                BORE_DIAMETER_MM / 2,
                HEADER_Z_MM[1],
                cq.Vector(x, y, 0),
                cq.Vector(0, 0, 1),
            )
            bolts[name] = cq.Solid.makeCylinder(
                BOLT_DIAMETER_MM / 2,
                NOMINAL_BOLT_LENGTH_MM,
                cq.Vector(x, y, BOLT_UNDERHEAD_Z_MM),
                cq.Vector(0, 0, 1),
            )
            counterbores[name] = cq.Solid.makeCylinder(
                BOTTOM_COUNTERBORE_DIAMETER_MM / 2,
                BOTTOM_COUNTERBORE_DEPTH_MM,
                cq.Vector(x, y, 0),
                cq.Vector(0, 0, 1),
            )
            bottom_washer = cq.Solid.makeCylinder(
                WASHER_DIAMETER_MM / 2,
                BOTTOM_WASHER_THICKNESS_MM,
                cq.Vector(x, y, BOTTOM_COUNTERBORE_DEPTH_MM - BOTTOM_WASHER_THICKNESS_MM),
                cq.Vector(0, 0, 1),
            )
            bottom_head = cq.Solid.makeCylinder(
                HEAD_DIAMETER_ENVELOPE_MM / 2,
                HEAD_HEIGHT_MM,
                cq.Vector(
                    x,
                    y,
                    BOTTOM_COUNTERBORE_DEPTH_MM
                    - BOTTOM_WASHER_THICKNESS_MM
                    - HEAD_HEIGHT_MM,
                ),
                cq.Vector(0, 0, 1),
            )
            top_washer = cq.Solid.makeCylinder(
                WASHER_DIAMETER_MM / 2,
                TOP_WASHER_STACK_MAX_MM,
                cq.Vector(x, y, HEADER_Z_MM[1]),
                cq.Vector(0, 0, 1),
            )
            top_nut = cq.Solid.makeCylinder(
                NUT_DIAMETER_ENVELOPE_MM / 2,
                NUT_HEIGHT_MM,
                cq.Vector(x, y, HEADER_Z_MM[1] + TOP_WASHER_STACK_MAX_MM),
                cq.Vector(0, 0, 1),
            )
            top_nut_z = HEADER_Z_MM[1] + TOP_WASHER_STACK_MAX_MM
            bottom_head_z = BOLT_UNDERHEAD_Z_MM - HEAD_HEIGHT_MM
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
            stacks[name] = {
                "bottom_washer": bottom_washer,
                "bottom_head": bottom_head,
                "top_washer": top_washer,
                "top_nut": top_nut,
            }
            tools[name] = {
                # Keep the prior endpoint envelopes while adding seated body
                # and the complete axial insertion sweep.
                "top": top_socket.approach_endpoint_envelope,
                "bottom": bottom_socket.approach_endpoint_envelope,
                "top_seated": top_socket.external_envelope,
                "bottom_seated": bottom_socket.external_envelope,
                "top_approach_sweep": top_socket.approach_sweep_envelope,
                "bottom_approach_sweep": bottom_socket.approach_sweep_envelope,
            }

    # Remove only candidate holes and the required flush bottom head/washer seats.
    finished_backers = {}
    finished_header = wood["base_header"]
    for name, solid in backers.items():
        side = name.removeprefix("inner_kicker_backer_")
        finished = solid
        for index, (x, y) in enumerate(BACKER_BOLT_STATIONS[side], start=1):
            bolt_name = f"backer_header_{side}_{index}"
            finished = finished.cut(
                cq.Solid.makeCylinder(
                    BORE_DIAMETER_MM / 2,
                    BACKER_Z_MM[1] - BOTTOM_COUNTERBORE_DEPTH_MM,
                    cq.Vector(x, y, BOTTOM_COUNTERBORE_DEPTH_MM),
                    cq.Vector(0, 0, 1),
                )
            ).cut(counterbores[bolt_name])
        finished_backers[name] = finished
    for name, bore in bores.items():
        finished_header = finished_header.cut(
            cq.Solid.makeCylinder(
                BORE_DIAMETER_MM / 2,
                HEADER_Z_MM[1] - HEADER_Z_MM[0],
                cq.Vector(bore.BoundingBox().xmin + BORE_DIAMETER_MM / 2,
                          bore.BoundingBox().ymin + BORE_DIAMETER_MM / 2,
                          HEADER_Z_MM[0]),
                cq.Vector(0, 0, 1),
            )
        )
    wood["base_header"] = finished_header
    wood.update(finished_backers)
    return model, source_wood, wood, backers, bolts, bores, stacks, tools, counterbores


def _service_screen(candidate_shapes, service_inventory):
    reports = {}
    for candidate_name, shape in candidate_shapes.items():
        family_hits = {}
        cb = shape.BoundingBox()
        for family, members in service_inventory["solids"].items():
            candidates = {
                name: obstacle
                for name, obstacle in members.items()
                if _box_overlap(cb, obstacle.BoundingBox())
            }
            hits = _hits(shape, candidates)
            if hits:
                family_hits[family] = hits
        reports[candidate_name] = family_hits
    return reports


def _axis_reception(rows, backers):
    center_rows = {
        row["name"]: row
        for row in rows
        if row["name"].startswith(("round_kicker_left_center_", "round_kicker_right_center_"))
    }
    if len(center_rows) != 4:
        raise ValueError(f"Expected four fixed center-kicker axes, found {len(center_rows)}")
    reception = {}
    for name, row in center_rows.items():
        side = "left" if "_left_" in name else "right"
        axis = _axis(
            row,
            length_key="shop_purchased_length_mm",
            diameter_key="occupied_diameter_mm",
        )
        receiver = backers[f"inner_kicker_backer_{side}"]
        full_embed = float(row["shop_purchased_length_mm"]) - abs(
            float(row["start_y_mm"]) - BACKER_Y_MM[1]
        )
        embedded_axis = cq.Solid.makeCylinder(
            float(row["occupied_diameter_mm"]) / 2,
            full_embed,
            cq.Vector(
                float(row["start_x_mm"]),
                BACKER_Y_MM[1],
                float(row["start_z_mm"]),
            ),
            cq.Vector(0, -1, 0),
        )
        inside = _volume(embedded_axis, receiver)
        reception[name] = {
            "receiver": f"inner_kicker_backer_{side}",
            "fixed_axis_xyz_mm": [
                float(row["start_x_mm"]),
                float(row["start_y_mm"]),
                float(row["start_z_mm"]),
            ],
            "purchased_length_mm": float(row["shop_purchased_length_mm"]),
            "modeled_occupied_diameter_mm": float(row["occupied_diameter_mm"]),
            "modeled_axis_volume_inside_backer_mm3": round(inside, 6),
            "modeled_embedded_axis_volume_fraction_inside_backer": round(
                inside / embedded_axis.Volume(), 8
            ),
            "nominal_embedded_length_after_panel_back_mm": round(full_embed, 6),
            "source_screw_diameter_limit": "Historical occupied CAD envelope only; it is not a Hillman 42605 measured diameter or pilot size.",
            "full_embedded_axis_volume_received": abs(inside - embedded_axis.Volume()) < 0.01,
            "axis_includes_panel_thickness": True,
            "full_purchased_axis_shape_volume_mm3": round(axis.Volume(), 6),
        }
    return reception


def _source_fingerprints():
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SOURCE_FILES
    }


def _fastener_stack_screen():
    options = []
    for length_in, top_washer_count in ((11.5, 1), (12.0, 1), (12.0, 3)):
        nominal_length = length_in * 25.4
        # B18.2.1 defines nominal LG,max = Lnom - LT, with a minus-only
        # five-coarse-pitch tolerance. Also carry the minimum overall-length
        # tolerance into the worst-case body calculation; this is why a
        # nominal 12-in bolt can have only 268.478 mm of smooth body.
        maximum_smooth_shank = nominal_length - NOMINAL_THREAD_LENGTH_MM
        minimum_smooth_shank = (
            nominal_length
            - LENGTH_TOL_MIN_MM
            - NOMINAL_THREAD_LENGTH_MM
            - THREAD_GAUGE_TOL_MM
        )
        top_washers_min = top_washer_count * WASHER_MIN_THICKNESS_MM
        top_washers_nominal = top_washer_count * WASHER_NOMINAL_THICKNESS_MM
        top_washers_max = top_washer_count * WASHER_MAX_THICKNESS_MM
        # The underhead bearing face is below its 2.032 mm washer at Z=4.968.
        # The wood itself is still 270 mm long (Z=7…277); the bolt-axis
        # distance from underhead to wood top is 272.032 mm.
        nut_bearing_min = UNDERHEAD_TO_WOOD_END_MM + top_washers_min
        nut_bearing_nominal = UNDERHEAD_TO_WOOD_END_MM + top_washers_nominal
        nut_bearing_max = UNDERHEAD_TO_WOOD_END_MM + top_washers_max
        nut_top_max = nut_bearing_max + NUT_HEIGHT_MM
        required_underhead_length = nut_top_max + THREAD_PAST_NUT_MM
        minimum_delivered_length = nominal_length - LENGTH_TOL_MIN_MM
        maximum_delivered_length = nominal_length + LENGTH_TOL_MAX_MM
        wood_smooth_margin = minimum_smooth_shank - UNDERHEAD_TO_WOOD_END_MM
        nut_start_margin_at_max_smooth = nut_bearing_min - maximum_smooth_shank
        nut_start_margin_at_min_smooth = nut_bearing_min - minimum_smooth_shank
        # NDS 12.3.7.2 permits nominal D when thread bearing in the member
        # holding the threads is no more than one-quarter its full bearing
        # length. Here that member is the 38.1 mm header at the bolt tip.
        # A later thread transition is also needed for complete nut engagement.
        allowed_transition_min = (
            UNDERHEAD_TO_WOOD_END_MM - LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM
        )
        smooth_range_needed = (allowed_transition_min, nut_bearing_min)
        standard_smooth_range = (minimum_smooth_shank, maximum_smooth_shank)
        feasible_shank_low = max(smooth_range_needed[0], standard_smooth_range[0])
        feasible_shank_high = min(smooth_range_needed[1], standard_smooth_range[1])
        feasible_with_measurement = feasible_shank_low <= feasible_shank_high
        max_header_thread_exposure = max(
            0.0,
            min(
                HEADER_BEARING_LENGTH_MM,
                UNDERHEAD_TO_WOOD_END_MM
                - max(HEADER_START_FROM_UNDERHEAD_MM, minimum_smooth_shank),
            ),
        )
        min_header_thread_exposure = max(
            0.0,
            min(
                HEADER_BEARING_LENGTH_MM,
                UNDERHEAD_TO_WOOD_END_MM
                - max(HEADER_START_FROM_UNDERHEAD_MM, maximum_smooth_shank),
            ),
        )
        minimum_tip_projection = minimum_delivered_length - nut_top_max
        nominal_tip_projection = nominal_length - (
            UNDERHEAD_TO_WOOD_END_MM + top_washers_nominal + NUT_HEIGHT_MM
        )
        required_total_thread_min = nominal_length - nut_bearing_min
        required_total_thread_max = nominal_length - UNDERHEAD_TO_WOOD_END_MM
        if not feasible_with_measurement:
            status = "blocked_no_standard_thread_transition_meets_NDS_limited_thread_and_full_nut_engagement_bounds"
        elif max_header_thread_exposure > LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM:
            status = "conditional_measure_each_thread_transition;_use_root_diameter_if_header_exposure_exceeds_one_quarter"
        else:
            status = "conditional_NDS_limited_thread_geometry_and_full_nut_engagement;_verify_each_delivered_bolt"
        options.append(
            {
                "nominal_length_in": length_in,
                "top_type_a_washer_count": top_washer_count,
                "nominal_underhead_length_mm": round(nominal_length, 3),
                "minimum_delivered_length_mm_from_asme_length_tolerance": round(
                    minimum_delivered_length, 3
                ),
                "maximum_delivered_length_mm_from_asme_length_tolerance": round(
                    maximum_delivered_length, 3
                ),
                "asme_nominal_total_thread_length_mm": NOMINAL_THREAD_LENGTH_MM,
                "asme_max_total_thread_length_including_five_pitch_tolerance_mm": round(
                    NOMINAL_THREAD_LENGTH_MM + THREAD_GAUGE_TOL_MM, 3
                ),
                "asme_smooth_shank_length_range_mm_from_underhead": [
                    round(minimum_smooth_shank, 3),
                    round(maximum_smooth_shank, 3),
                ],
                "thread_transition_interval_global_z_mm": [
                    round(BOLT_UNDERHEAD_Z_MM + smooth_range_needed[0], 3),
                    round(BOLT_UNDERHEAD_Z_MM + smooth_range_needed[1], 3),
                ],
                "nominal_bolt_tip_global_z_mm": round(
                    BOLT_UNDERHEAD_Z_MM + nominal_length, 3
                ),
                "minimum_delivered_bolt_tip_global_z_mm": round(
                    BOLT_UNDERHEAD_Z_MM + minimum_delivered_length, 3
                ),
                "underhead_to_wood_end_mm": round(
                    UNDERHEAD_TO_WOOD_END_MM, 3
                ),
                "bolt_underhead_z_mm": BOLT_UNDERHEAD_Z_MM,
                "wood_bearing_start_z_mm": WOOD_BEARING_START_Z_MM,
                "wood_bearing_end_z_mm": HEADER_Z_MM[1],
                "owner_effective_grip_criterion_mm": WOOD_GRIP_REQUIRED_MM,
                "actual_CAD_wood_span_coordinates_z_mm": [
                    BOTTOM_COUNTERBORE_DEPTH_MM,
                    HEADER_Z_MM[1],
                ],
                "actual_CAD_wood_span_length_mm": round(WOOD_GRIP_CAD_MM, 3),
                "maximum_smooth_shank_minus_underhead_to_wood_end_mm": round(
                    maximum_smooth_shank - UNDERHEAD_TO_WOOD_END_MM, 3
                ),
                "minimum_smooth_shank_minus_underhead_to_wood_end_mm": round(
                    wood_smooth_margin, 3
                ),
                "thread_exposure_in_header_mm_at_standard_min_max_smooth_shank": [
                    round(max_header_thread_exposure, 3),
                    round(min_header_thread_exposure, 3),
                ],
                "header_bearing_length_mm": round(HEADER_BEARING_LENGTH_MM, 3),
                "nds_12_3_7_2_max_thread_bearing_if_using_nominal_d_mm": round(
                    LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM, 3
                ),
                "nds_nominal_d_limited_thread_rule_passes_over_full_standard_envelope": (
                    max_header_thread_exposure <= LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM
                ),
                "top_washer_stack_thickness_min_nominal_max_mm": [
                    round(top_washers_min, 3),
                    round(top_washers_nominal, 3),
                    round(top_washers_max, 3),
                ],
                "nut_bearing_face_min_nominal_max_mm_from_underhead": [
                    round(nut_bearing_min, 3),
                    round(nut_bearing_nominal, 3),
                    round(nut_bearing_max, 3),
                ],
                "nut_bearing_face_min_nominal_max_global_z_mm": [
                    round(BOLT_UNDERHEAD_Z_MM + nut_bearing_min, 3),
                    round(BOLT_UNDERHEAD_Z_MM + nut_bearing_nominal, 3),
                    round(BOLT_UNDERHEAD_Z_MM + nut_bearing_max, 3),
                ],
                "nut_face_margin_for_standard_shank_range_mm_at_min_washer_thickness": [
                    round(nut_start_margin_at_max_smooth, 3),
                    round(nut_start_margin_at_min_smooth, 3),
                ],
                "thread_transition_interval_for_nds_limited_thread_and_full_nut_engagement_mm_from_underhead": [
                    round(smooth_range_needed[0], 3),
                    round(smooth_range_needed[1], 3),
                ],
                "overlap_with_ASME_shank_envelope_mm": (
                    [round(feasible_shank_low, 3), round(feasible_shank_high, 3)]
                    if feasible_with_measurement
                    else []
                ),
                "thread_length_range_implied_at_nominal_overall_length_mm": [
                    round(required_total_thread_min, 3),
                    round(required_total_thread_max, 3),
                ],
                "required_underhead_length_mm_using_maximum_washer_and_nut_thickness": round(
                    required_underhead_length, 3
                ),
                "minimum_tip_past_nut_mm_from_length_tolerance": round(
                    minimum_tip_projection, 3
                ),
                "nominal_tip_past_nut_mm": round(nominal_tip_projection, 3),
                "wood_bearing_length_mm": round(WOOD_GRIP_CAD_MM, 3),
                "standard_tolerance_envelope_allows_limited_threads_in_header": (
                    max_header_thread_exposure <= LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM
                ),
                "nut_seat_guaranteed_by_standard_envelope": (
                    nut_start_margin_at_max_smooth >= 0.0
                ),
                "possible_with_measured_thread_start_within_standard_envelope": feasible_with_measurement,
                "minimum_tip_projection_exceeds_3p175mm": (
                    minimum_tip_projection >= THREAD_PAST_NUT_MM
                ),
                "geometric_thread_stack_status": status,
            }
        )

    catalog_12_max_shank_from_minimum_thread = 12.0 * 25.4 - NOMINAL_THREAD_LENGTH_MM
    triple_stack = options[2]
    catalog_12_margin = (
        triple_stack["nut_bearing_face_min_nominal_max_mm_from_underhead"][0]
        - catalog_12_max_shank_from_minimum_thread
    )
    return {
        "basis": {
            "bolt_standard": "ASME B18.2.1-2012, hex bolt, 1/4-20 UNC, length over 6 in",
            "nominal_thread_length_rule": "LT = 2D + 0.50 in = 1.00 in",
            "maximum_thread_length_rule": "LG,max = Lnom - LT, with a minus-only tolerance of five coarse pitches. For the minimum total length envelope, smooth shank is (Lnom - 0.18 in) - (LT + 0.25 in); this can put the thread transition into the required wood span.",
            "bolt_length_tolerance_over_6in_1_4_through_3_8in": "+0.10/-0.18 in",
            "washer": "ASME B18.22.1 Type A narrow, 1/4 in; basic OD 5/8 in with 0.640 in max envelope, thickness 0.065 in nominal / 0.051-0.080 in tolerance",
            "nut": "ASME B18.2.2 finished 1/4-20 hex nut; max thickness 0.226 in, max corners 0.505 in",
            "head": "ASME B18.2.1 regular hex bolt; max height 0.188 in, max corners 0.505 in",
            "stack_dimensions_mm": {
                "owner_effective_grip_criterion_mm": WOOD_GRIP_REQUIRED_MM,
                "bolt_underhead_z_mm": BOLT_UNDERHEAD_Z_MM,
                "wood_span_start_z_mm": WOOD_BEARING_START_Z_MM,
                "wood_span_end_z_mm": HEADER_Z_MM[1],
                "actual_CAD_wood_bearing_length_mm": round(
                    WOOD_GRIP_CAD_MM, 3
                ),
                "underhead_to_wood_end_mm_including_head_washer": round(
                    UNDERHEAD_TO_WOOD_END_MM, 3
                ),
                "top_washer_count": TOP_WASHER_COUNT,
                "top_washer_stack_min_nominal_max": [
                    round(TOP_WASHER_STACK_MIN_MM, 3),
                    round(TOP_WASHER_STACK_NOMINAL_MM, 3),
                    round(TOP_WASHER_STACK_MAX_MM, 3),
                ],
                "top_nut_max_thickness": NUT_HEIGHT_MM,
                "minimum_thread_past_nut_used_for_length_check": THREAD_PAST_NUT_MM,
                "minimum_underhead_length_with_max_washer_nut_and_thread_projection": round(
                    UNDERHEAD_TO_WOOD_END_MM
                    + TOP_WASHER_STACK_MAX_MM
                    + NUT_HEIGHT_MM
                    + THREAD_PAST_NUT_MM,
                    3,
                ),
                "bottom_head_plus_washer_depth": round(
                    HEAD_HEIGHT_MM + BOTTOM_WASHER_THICKNESS_MM, 3
                ),
                "bottom_counterbore_depth": BOTTOM_COUNTERBORE_DEPTH_MM,
                "remaining_counterbore_depth_allowance": round(
                    BOTTOM_COUNTERBORE_DEPTH_MM
                    - HEAD_HEIGHT_MM
                    - BOTTOM_WASHER_THICKNESS_MM,
                    3,
                ),
            },
            "option_comparison": options,
        },
        "specific_12in_catalog_example": {
            "source_product": "Bolt Depot product 5238, stainless 18-8 1/4-20 x 12 in hex bolt",
            "published_length_tolerance": "+0.00/-0.18 in",
            "published_minimum_thread_length_in": 1.0,
            "maximum_smooth_body_from_published_1in_minimum_thread_at_max_delivered_length_mm": round(
                catalog_12_max_shank_from_minimum_thread, 3
            ),
            "nut_face_margin_at_minimum_three_washer_thickness_mm_if_only_minimum_thread_is_provided": round(
                catalog_12_margin, 3
            ),
            "required_thread_transition_interval_mm_from_underhead_for_12in_three_washer_stack": [
                round(
                    UNDERHEAD_TO_WOOD_END_MM
                    - LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM,
                    3,
                ),
                round(UNDERHEAD_TO_WOOD_END_MM + TOP_WASHER_STACK_MIN_MM, 3),
            ],
            "nominal_12in_thread_length_range_that_places_start_in_three_washer_band_in": [
                round(
                    (
                        12.0 * 25.4
                        - (UNDERHEAD_TO_WOOD_END_MM + TOP_WASHER_STACK_MIN_MM)
                    )
                    / 25.4,
                    4,
                ),
                round(
                    (
                        12.0 * 25.4
                        - (UNDERHEAD_TO_WOOD_END_MM
                           - LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM)
                    )
                    / 25.4,
                    4,
                ),
            ],
            "thread_stack_status": "not_guaranteed_to_seat; published minimum 1-in thread allows a smooth shank beyond the 3-washer nut face and the total-length tolerance permits thread transition inside wood; measure delivered length, smooth-shank end, and washer/nut stack together",
        },
        "conditional_receiving_spec": {
            "status": "conditional_geometry_only_no_sku_accepted",
            "nominal_fastener": "1/4-20 UNC, 12-in partial-thread hex bolt to ASME B18.2.1, nut and Type A narrow washers",
            "bolt_underhead_z_mm": BOLT_UNDERHEAD_Z_MM,
            "actual_CAD_wood_span_start_z_mm": WOOD_BEARING_START_Z_MM,
            "actual_CAD_wood_span_end_z_mm": HEADER_Z_MM[1],
            "actual_CAD_wood_span_length_mm": round(WOOD_GRIP_CAD_MM, 3),
            "underhead_to_wood_end_mm_including_head_washer": round(
                UNDERHEAD_TO_WOOD_END_MM, 3
            ),
            "owner_effective_grip_criterion_mm": WOOD_GRIP_REQUIRED_MM,
            "measured_thread_transition_interval_from_underhead_mm_with_three_top_washers": [
                round(
                    UNDERHEAD_TO_WOOD_END_MM
                    - LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM,
                    3,
                ),
                round(UNDERHEAD_TO_WOOD_END_MM + TOP_WASHER_STACK_MIN_MM, 3),
            ],
            "measured_thread_transition_global_z_mm_with_three_top_washers": [
                round(
                    BOLT_UNDERHEAD_Z_MM
                    + UNDERHEAD_TO_WOOD_END_MM
                    - LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM,
                    3,
                ),
                round(
                    BOLT_UNDERHEAD_Z_MM
                    + UNDERHEAD_TO_WOOD_END_MM
                    + TOP_WASHER_STACK_MIN_MM,
                    3,
                ),
            ],
            "minimum_combined_top_washer_thickness_mm": round(
                TOP_WASHER_STACK_MIN_MM, 4
            ),
            "delivered_length_range_mm_from_standard_tolerance": [
                round(12.0 * 25.4 - LENGTH_TOL_MIN_MM, 3),
                round(12.0 * 25.4 + LENGTH_TOL_MAX_MM, 3),
            ],
            "coupled_measured_length_thread_condition": "For measured delivered underhead length L and measured smooth-shank/thread transition S (both mm from the underhead datum), require S >= underhead-to-wood-end minus one quarter of the 38.1 mm header bearing length (262.507 mm), so thread bearing in the member holding the threads stays within the NDS 12.3.7.2 nominal-D limit. Also require S <= underhead-to-wood-end plus the actual combined top-washer thickness to engage the full nut. With the three-washer minimum stack the interval is 262.507–275.918 mm. Verify conforming thread through the full nut and at least 3.175 mm of threaded tip beyond it. Measure L, S, and washer stack together; do not infer S from nominal length or a catalog minimum-thread statement. If the actual NDS thread-bearing limit is exceeded, use measured root diameter in the lateral-yield calculation instead of nominal D.",
            "measured_thread_transition_band_with_three_minimum_washers_mm": [
                round(
                    UNDERHEAD_TO_WOOD_END_MM
                    - LIMITED_THREAD_MAX_HEADER_EXPOSURE_MM,
                    3,
                ),
                round(UNDERHEAD_TO_WOOD_END_MM + TOP_WASHER_STACK_MIN_MM, 3),
            ],
            "standard_12in_envelope_smooth_shank_mm_from_underhead": [
                options[2]["asme_smooth_shank_length_range_mm_from_underhead"][0],
                options[2]["asme_smooth_shank_length_range_mm_from_underhead"][1],
            ],
            "worst_case_standard_threads_can_enter_wood_by_mm": round(
                UNDERHEAD_TO_WOOD_END_MM
                - options[2]["asme_smooth_shank_length_range_mm_from_underhead"][0],
                3,
            ),
            "evidence_needed": "A manufacturer-guaranteed shank/thread transition that meets the coupled dimensions, or receipt measurement of every bolt's overall underhead length and actual smooth-shank/thread start, plus measurement of the washer stack and nut fit. No SKU is accepted.",
        },
        "dimension_sources": {
            "asme_b18_2_1_thread_and_bolt_geometry": "https://studylib.net/doc/27174816/asme-b18.2.1-2012",
            "asme_b18_2_2_finished_nut_geometry": "https://studylib.net/doc/27188368/asme-b18.2.2-2022",
            "12in_catalog_bolt_example": "https://boltdepot.com/Product-Details?product=5238",
            "finished_hex_nut_1_4_20": "https://boltdepot.com/Product-Details?product=2563",
            "1_4in_washer_od_and_id": "https://boltdepot.com/Product-Details?product=2947",
            "asme_type_a_washer_thickness": "https://www.panduit.com/content/dam/panduit/en/products/media/6/86/986/6986/101806986.pdf",
            "7_16_deep_socket_dimensions": "https://kokenusa.com/products/deep-socket-3-8sq-dr-12-p-7-16",
        },
        "limitations": [
            "A smooth shank through every millimeter of wood is not required by this screen. The actual thread-bearing length in the 38.1 mm header must be bounded for NDS 12.3.7.2; otherwise use a measured root diameter.",
            "The 11.5-in option is a dimensionally plausible length screen, not a verified stocked SKU or selected material/grade.",
            "A 7.3-mm nominal clearance hole is modeled; hole, bolt, washer, wood, and placement tolerances remain open.",
            "Thread fit and geometric seating are not resistance, preload, bearing, splitting, stiffness, or fatigue checks.",
        ],
    }


def _build_report():
    rows = _read_axes()
    screw_axes, frame_bolts = _fixed_axis_shapes(rows)
    (
        _model,
        source_wood,
        wood,
        backers,
        bolts,
        bores,
        stacks,
        tools,
        counterbores,
    ) = _source_and_candidate()
    service = protected.inventory()

    # Candidate bodies may touch the header at z=238.9; that is the intended
    # bearing face. All other source timber is an unintended-overlap target.
    body_hits = {}
    source_obstacles = {
        name: shape
        for name, shape in source_wood.items()
        if name not in {"base_header", "base_post_center_left", "base_post_center_right"}
    }
    moved_posts = {
        f"base_post_center_{side}": wood[f"base_post_center_{side}"]
        for side in ("left", "right")
    }
    source_obstacles.update(moved_posts)
    for name, shape in backers.items():
        body_hits[name] = _hits(shape, source_obstacles)
    moved_post_hits = {}
    post_obstacles = {
        name: shape
        for name, shape in source_wood.items()
        if name not in {"base_header", "base_post_center_left", "base_post_center_right"}
    }
    for name, shape in moved_posts.items():
        moved_post_hits[name] = _hits(shape, post_obstacles)
    moved_post_panel_axis_hits = {
        name: _hits(shape, screw_axes) for name, shape in moved_posts.items()
    }
    moved_post_frame_axis_hits = {
        name: _hits(shape, frame_bolts) for name, shape in moved_posts.items()
    }

    # All axis-cylinder envelopes are retained. Center screw hits in the
    # backers are intentional; every other fixed screw axis must clear.
    panel_axis_hits = {}
    intended_center = {
        f"round_kicker_{side}_center_{index}"
        for side in ("left", "right")
        for index in (1, 2)
    }
    for name, backer in backers.items():
        all_hits = _hits(backer, screw_axes)
        intended = {axis: volume for axis, volume in all_hits.items() if axis in intended_center}
        unexpected = {axis: volume for axis, volume in all_hits.items() if axis not in intended_center}
        side = name.removeprefix("inner_kicker_backer_")
        expected_for_side = {
            f"round_kicker_{side}_center_1",
            f"round_kicker_{side}_center_2",
        }
        panel_axis_hits[name] = {
            "expected_receiver_axis_hits_mm3": {
                axis: intended[axis] for axis in sorted(intended) if axis in expected_for_side
            },
            "unexpected_fixed_axis_hits_mm3": unexpected
            | {axis: volume for axis, volume in intended.items() if axis not in expected_for_side},
        }

    # The new through-bolt/bore/stack/tool geometry must miss all fixed axes.
    candidate_hardware = {}
    for name in bolts:
        candidate_hardware[f"bolt/{name}"] = bolts[name]
        candidate_hardware[f"bore/{name}"] = bores[name]
        candidate_hardware[f"counterbore/{name}"] = counterbores[name]
        for role, shape in stacks[name].items():
            candidate_hardware[f"stack/{name}/{role}"] = shape
        for role, shape in tools[name].items():
            candidate_hardware[f"tool/{name}/{role}"] = shape
    hardware_panel_hits = {
        name: _hits(shape, screw_axes) for name, shape in candidate_hardware.items()
    }
    hardware_frame_hits = {
        name: _hits(shape, frame_bolts) for name, shape in candidate_hardware.items()
    }
    new_bore_unintended_wood_hits = {
        name: _hits(shape, source_obstacles)
        for name, shape in {**bores, **counterbores}.items()
    }

    # Screen backers and all new machining/hardware against maintained T-nuts,
    # provisional hold paths, LED bodies/wires, and source screw/bolt solids.
    service_candidates = {**backers, **moved_posts}
    service_candidates.update(candidate_hardware)
    service_hits = _service_screen(service_candidates, service)
    allowed_service_hits = {}
    unintended_service_hits = {}
    for candidate_name, families in service_hits.items():
        allowed, unexpected = {}, {}
        for family, witnesses in families.items():
            permitted_names = set()
            if candidate_name.startswith("inner_kicker_backer_") and family == "panel_screws":
                side = candidate_name.removeprefix("inner_kicker_backer_")
                permitted_names = {
                    f"round_kicker_{side}_center_1",
                    f"round_kicker_{side}_center_2",
                }
            expected = {key: value for key, value in witnesses.items() if key in permitted_names}
            other = {key: value for key, value in witnesses.items() if key not in permitted_names}
            if expected:
                allowed.setdefault(family, {}).update(expected)
            if other:
                unexpected.setdefault(family, {}).update(other)
        if allowed:
            allowed_service_hits[candidate_name] = allowed
        if unexpected:
            unintended_service_hits[candidate_name] = unexpected

    # Hardware and tools must clear the drilled source members and candidate
    # bodies. The countersunk bearing surfaces are face contacts, not overlaps.
    hardware_to_machined_wood = {
        name: _hits(shape, wood)
        for name, shape in candidate_hardware.items()
        if not name.startswith(("bore/", "counterbore/"))
    }

    reception = _axis_reception(rows, backers)
    seam_left = -1.5875
    edge_support = {}
    for side in ("left", "right"):
        edge_x = seam_left + (-0.5 if side == "left" else 0.5)
        backer = backers[f"inner_kicker_backer_{side}"]
        edge_support[f"kicker_{side}"] = all(
            backer.isInside(cq.Vector(edge_x, -36.1, z), 1e-4)
            for z in (0.5, 112.5, 238.4)
        )

    header_contact_gross = BACKER_DIMS_MM[0] * BACKER_DIMS_MM[1]
    header_contact_net = header_contact_gross - 2 * cq.Solid.makeCylinder(
        BORE_DIAMETER_MM / 2,
        1.0,
        cq.Vector(0, 0, 0),
        cq.Vector(0, 0, 1),
    ).Volume()
    source_counts = {
        "fixed_panel_kicker_axes": len(screw_axes),
        "retained_frame_bolt_axes": len(frame_bolts),
        "protected_service_families": service["counts"],
    }
    fastener_stack_screen = _fastener_stack_screen()

    bolt_path_reception = {}
    for side, stations in BACKER_BOLT_STATIONS.items():
        for index, (x, y) in enumerate(stations, start=1):
            name = f"backer_header_{side}_{index}"
            bore = bores[name]
            backer_name = f"inner_kicker_backer_{side}"
            backer_fraction = _volume(bore, backers[backer_name]) / bore.Volume()
            header_fraction = _volume(bore, source_wood["base_header"]) / bore.Volume()
            counterbore_fraction = _volume(
                counterbores[name], backers[backer_name]
            ) / counterbores[name].Volume()
            bolt_path_reception[name] = {
                "intended_wood": [backer_name, "base_header"],
                "clearance_bore_diameter_mm": BORE_DIAMETER_MM,
                "bore_volume_fraction_in_backer": round(backer_fraction, 8),
                "bore_volume_fraction_in_header": round(header_fraction, 8),
                "bottom_counterbore_volume_fraction_in_backer": round(
                    counterbore_fraction, 8
                ),
                "complete_bore_received_by_intended_wood": abs(
                    backer_fraction + header_fraction - 1.0
                ) < 1e-6,
            }

    bolt_records = []
    for side, stations in BACKER_BOLT_STATIONS.items():
        for index, (x, y) in enumerate(stations, start=1):
            bolt_records.append(
                {
                    "id": f"backer_header_{side}_{index}",
                    "side": side,
                    "members": ["inner_kicker_backer_" + side, "base_header"],
                    "axis_start_xyz_mm": [x, y, BOLT_UNDERHEAD_Z_MM],
                    "axis_direction_xyz": [0, 0, 1],
                    "wood_bearing_span_mm": [WOOD_BEARING_START_Z_MM, HEADER_Z_MM[1]],
                    "backer_header_interface_z_mm": 238.9,
                    "nominal_backer_envelope_clearance_to_y_edges_mm": [
                        min(y - BACKER_Y_MM[0], BACKER_Y_MM[1] - y)
                    ][0],
                    "nominal_4d_comparator_mm_for_1_4_in_bolt": 4 * BOLT_DIAMETER_MM,
                    "tool_envelope_diameter_mm": SOCKET_EXTERNAL_DIAMETER_MM,
                    "socket_external_occupancy_intent": {
                        "top_nut": wj05_socket_occupancy_intent(
                            seated_koken_3305a_7_16_envelope(
                                (x, y),
                                HEADER_Z_MM[1] + TOP_WASHER_STACK_MAX_MM,
                                outward_z=1,
                                target_bounds_z_mm=(
                                    HEADER_Z_MM[1] + TOP_WASHER_STACK_MAX_MM,
                                    HEADER_Z_MM[1]
                                    + TOP_WASHER_STACK_MAX_MM
                                    + NUT_HEIGHT_MM,
                                ),
                            ),
                            target_component="top_nut",
                            target_bounds_z_mm=(
                                HEADER_Z_MM[1] + TOP_WASHER_STACK_MAX_MM,
                                HEADER_Z_MM[1]
                                + TOP_WASHER_STACK_MAX_MM
                                + NUT_HEIGHT_MM,
                            ),
                            target_max_corner_diameter_mm=NUT_DIAMETER_ENVELOPE_MM,
                        ),
                        "bottom_head": wj05_socket_occupancy_intent(
                            seated_koken_3305a_7_16_envelope(
                                (x, y),
                                BOLT_UNDERHEAD_Z_MM,
                                outward_z=-1,
                                target_bounds_z_mm=(
                                    BOLT_UNDERHEAD_Z_MM - HEAD_HEIGHT_MM,
                                    BOLT_UNDERHEAD_Z_MM,
                                ),
                            ),
                            target_component="bottom_bolt_head",
                            target_bounds_z_mm=(
                                BOLT_UNDERHEAD_Z_MM - HEAD_HEIGHT_MM,
                                BOLT_UNDERHEAD_Z_MM,
                            ),
                            target_max_corner_diameter_mm=HEAD_DIAMETER_ENVELOPE_MM,
                        ),
                    },
                    "nominal_bolt_length_envelope_mm": NOMINAL_BOLT_LENGTH_MM,
                    "nominal_bolt_tip_global_z_mm": round(
                        BOLT_UNDERHEAD_Z_MM + NOMINAL_BOLT_LENGTH_MM, 3
                    ),
                    "required_wood_grip_mm": WOOD_GRIP_REQUIRED_MM,
                    "nominal_CAD_underhead_to_wood_end_mm_including_head_washer": round(
                        UNDERHEAD_TO_WOOD_END_MM, 3
                    ),
                    "nominal_wood_bearing_length_mm": round(WOOD_GRIP_CAD_MM, 3),
                    "top_Type_A_washer_count": TOP_WASHER_COUNT,
                    "top_washer_stack_min_nominal_max_mm": [
                        round(TOP_WASHER_STACK_MIN_MM, 3),
                        round(TOP_WASHER_STACK_NOMINAL_MM, 3),
                        round(TOP_WASHER_STACK_MAX_MM, 3),
                    ],
                    "provisional_underhead_length_requirement_mm": fastener_stack_screen[
                        "basis"
                    ]["stack_dimensions_mm"][
                        "minimum_underhead_length_with_max_washer_nut_and_thread_projection"
                    ],
                    "12in_three_washer_thread_stack_status": fastener_stack_screen["basis"][
                        "option_comparison"
                    ][2]["geometric_thread_stack_status"],
                    "12in_three_washer_minimum_tip_past_nut_mm": fastener_stack_screen[
                        "basis"
                    ]["option_comparison"][2][
                        "minimum_tip_past_nut_mm_from_length_tolerance"
                    ],
                    "fastener_status": "12-in partial-thread geometry remains conditional on measuring delivered thread transition, actual nut engagement, washer stack, and tip; smooth shank through every millimeter of wood is not required; apply NDS 12.3.7.2 nominal-D limit when its thread-bearing condition is met, otherwise use actual root diameter; no SKU or capacity accepted",
                }
            )

    all_backer_service_hits = unintended_service_hits
    candidate_geometry_clear = (
        not any(body_hits.values())
        and not any(moved_post_hits.values())
        and not any(moved_post_panel_axis_hits.values())
        and not any(moved_post_frame_axis_hits.values())
        and all(not row["unexpected_fixed_axis_hits_mm3"] for row in panel_axis_hits.values())
        and all(not hits for hits in hardware_panel_hits.values())
        and all(not hits for hits in hardware_frame_hits.values())
        and not any(new_bore_unintended_wood_hits.values())
        and not all_backer_service_hits
        and all(row["full_embedded_axis_volume_received"] for row in reception.values())
        and all(row["complete_bore_received_by_intended_wood"] for row in bolt_path_reception.values())
        and all(edge_support.values())
        and not any(hardware_to_machined_wood.values())
    )
    result = {
        "schema": "wood_joints_wj05_center_backer_transfer_probe/v3",
        "candidate_id": "wj05-center-backer-header-through-bolt-diagnostic-v2",
        "status": "nominal_geometry_clear_diagnostic" if candidate_geometry_clear else "revise_named_geometry_or_service_collision",
        "source_candidate": "compact-floor-flush-development kerf-right source geometry; separate wood-joints development lane only",
        "source_fingerprints_sha256": _source_fingerprints(),
        "topology": {
            "moved_center_posts_x_shift_mm": POST_SHIFT_X_MM,
            "backer_bounds_mm": {
                side: {
                    "x": list(BACKER_X_MM[side]),
                    "y": list(BACKER_Y_MM),
                    "z": list(BACKER_Z_MM),
                }
                for side in ("left", "right")
            },
            "backer_stock_candidate": "two separate solid sawn 88.9 x 88.9 x 238.9 mm members, grain along Z; stock/source availability not verified",
            "member_transport": {
                "backers": "two discrete pieces; no glue or permanent joining assumed",
                "center_posts": "two existing 38.1 x 139.7 x 238.9 mm pieces, shifted in X only; each remains a discrete piece",
                "increased_member_length_or_section": False,
                "transport_and_frame_sequence_observed": False,
            },
            "fixed_center_kicker_axes": reception,
            "inner_edge_support_sample_check": edge_support,
            "backer_to_header_path": "Each backer has two ordinary vertical through-bolts into the actual base_header. The backer/header face contact is at Z=238.9 mm; the bolts cross 238.9 mm of backer and 38.1 mm of header.",
            "complete_frame_path": "Not established: base_header-to-principal/post duties and relocated center-post joints remain separate WJ-03/WJ-04/WJ-06 obligations.",
            "nominal_backer_header_contact_gross_mm2": round(header_contact_gross, 3),
            "nominal_contact_area_after_two_7p3mm_bores_mm2": round(header_contact_net, 3),
            "through_bolts": bolt_records,
            "fastener_stack_screen": fastener_stack_screen,
            "access_envelopes": {
                "socket_basis": {
                    "product": KOKEN_3305A_7_16_PRODUCT,
                    "product_url": KOKEN_PRODUCT_URL,
                    "drive": "3/8-in square, 12-point, 7/16-in output",
                    "listed_dimensions_mm": {
                        "D1_working_end_od": KOKEN_SOCKET_WORKING_END_DIAMETER_MM,
                        "D2_max_od": KOKEN_SOCKET_OUTSIDE_DIAMETER_MM,
                        "H1_hex_engagement": KOKEN_SOCKET_H1_MM,
                        "H2_stud_clearance_depth": KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
                        "L_overall_length": KOKEN_SOCKET_LENGTH_MM,
                    },
                    "external_model": "D2 max OD applied over full L as conservative exterior occupancy; unlisted axial OD profile not inferred",
                    "internal_fit": "12-point cavity geometry, across-corner clearance, tolerance, and engagement fit are not modeled or assessed",
                },
                "top_tool": "Seated envelope starts at nut bearing face Z=283.096 mm and extends +Z; approach endpoint remains at nut outer face. Full axial approach sweep included.",
                "bottom_tool": "Seated envelope starts at bolt underhead face Z=4.968 mm and extends -Z; approach endpoint remains at head outer face. Full axial approach sweep included.",
                "intended_hex_occupancy": "Named nut/head axial occupancy recorded separately; it is not counted as an obstacle clash. The external envelope still checks against all unrelated wood, fixed axes, and protected services.",
                "bottom_tool_against_floor": "not modeled; no floor friction or anchor claim added",
                "ratchet, extension, drive-end access, swing, floor clearance, and installation/removal order": "unmodeled and unverified; no tool access or assembly-sequence acceptance",
            },
        },
        "inventory": source_counts,
        "screens": {
            "backer_to_unrelated_source_wood_or_shifted_posts_mm3": body_hits,
            "shifted_posts_vs_unrelated_source_wood_mm3": moved_post_hits,
            "shifted_posts_vs_all_66_purchased_axis_envelopes_mm3": moved_post_panel_axis_hits,
            "shifted_posts_vs_12_frame_bolt_axes_mm3": moved_post_frame_axis_hits,
            "backer_vs_all_66_purchased_axis_envelopes_mm3": panel_axis_hits,
            "new_bolt_hole_reception_by_intended_wood": bolt_path_reception,
            "new_fastener_bore_stack_tool_vs_all_66_purchased_axes_mm3": hardware_panel_hits,
            "new_fastener_bore_stack_tool_vs_12_frame_bolt_axes_mm3": hardware_frame_hits,
            "new_bore_and_counterbore_vs_unintended_source_wood_mm3": new_bore_unintended_wood_hits,
            "new_fastener_stack_tool_vs_machined_frame_wood_mm3": hardware_to_machined_wood,
            "new_backer_and_fastener_geometry_vs_protected_services": {
                "unintended_hits": unintended_service_hits,
                "expected_center_kicker_screw_receiver_hits": allowed_service_hits,
            },
        },
        "geometry_clear_for_this_probe": candidate_geometry_clear,
        "mechanics_and_release": {
            "resistance": "unverified; no capacity inferred",
            "bolt group and complete joint behavior": "unverified; axial loading along the vertical backer grain and load transfer into the header need an applicable mechanics method",
            "wood bearing, splitting, net section, washer bearing, stiffness, and slip": "unverified",
            "actual stock and grain quality": "unverified",
            "bolt SKU, delivered length/shank/thread, nut engagement, washers, and torque": "unverified",
            "counterbore machining and remaining foot section": "unverified",
            "permanent floor fit and bottom tool approach": "unverified; bottom counterbores are accessible only while the member is lifted/open during assembly or disassembly",
            "whole-frame header connection and altered center-post duties": "unverified",
            "tolerance stack, tool swing, transport and installation sequence": "unverified",
            "drilling/fabrication/structural/climbing release": False,
        },
        "limits": [
            "Fixed 66 panel/kicker axes and the twelve source frame-bolt axes were screened as geometric envelopes; no hardware capacity or acceptance transfers.",
            "Hillman screw axis diameter is a historical occupied CAD envelope, not a published/observed Hillman diameter, pilot, or instruction.",
            "Hold projection is the maintained provisional 50.8 mm screen and is not delivered hold-bolt length.",
            "Nominal CAD gaps do not include stock, drilling, placement, washer, nut, tool, or floor tolerances.",
            "The Ko-ken geometry is one outside-envelope proxy: internal 12-point profile, tool fit, driver, approach clearance beyond the modeled coaxial insertion sweep, and tolerance are not modeled or assessed.",
            "This trial has not replaced all 24 former angle duties, all 144 SDS axes, or supplied fresh six-case evidence.",
        ],
    }
    return result


def _markdown(result):
    geometry = result["topology"]
    backers = geometry["backer_bounds_mm"]
    stack = geometry["fastener_stack_screen"]
    options = stack["basis"]["option_comparison"]
    short_single, long_single, long_triple = options
    access = geometry["access_envelopes"]
    lines = [
        "# WJ-05 center kicker backer transfer diagnostic",
        "",
        f"Status: **{result['status']}**. Geometry trial only; no joint capacity, drilling, fabrication, or climbing release.",
        "",
        "This source-bound trial retains the kerf-right panels, all four fixed center-kicker screw axes, and the two inner kicker edges. It uses the owner-review ±180 mm center-post placement and adds two ordinary vertical through-bolts from each separate 4×4 backer into the maintained `base_header`. This remains a diagnostic WJ-05 topology; it does not replace the selected candidate or transfer old acceptance.",
        "",
        "## Candidate geometry",
        "",
        "| Piece | X (mm) | Y (mm) | Z (mm) |",
        "|---|---:|---:|---:|",
        f"| Left backer | {backers['left']['x'][0]:.4f}…{backers['left']['x'][1]:.4f} | {backers['left']['y'][0]:.1f}…{backers['left']['y'][1]:.1f} | {backers['left']['z'][0]:.1f}…{backers['left']['z'][1]:.1f} |",
        f"| Right backer | {backers['right']['x'][0]:.4f}…{backers['right']['x'][1]:.4f} | {backers['right']['y'][0]:.1f}…{backers['right']['y'][1]:.1f} | {backers['right']['z'][0]:.1f}…{backers['right']['z'][1]:.1f} |",
        "| Base header | −1219.2…1216.025 | −175.7…−36 | 238.9…277 |",
        "",
        "Each backer receives two provisional 1/4-20 Z-axis through-bolts with a 7.3 mm nominal clearance bore. The left axes are at X/Y=(−35,−97) and (−35,−63) mm; the repaired right axes are at (41,−98) and (25,−76) mm. Each bolt crosses 238.9 mm of backer and 38.1 mm of header. A 20 mm diameter, 7 mm deep open counterbore in the backer bottom contains one standard 1/4-in hex head and one Type A washer at maximum envelope thickness; their combined depth is 6.807 mm, leaving 0.193 mm nominal recess allowance. The illustrative top stack uses three Type A washers. These dimensions are an investigation pose, not a cut or drill schedule.",
        "",
        "The model screens all 66 purchased-length screw-axis envelopes and all twelve retained frame-bolt axes. It also checks the backers, bores, hardware stacks, and tool envelopes against maintained hold/T-nut, LED, wire, panel-screw, and frame-bolt solids, with exact solid intersections after bounding-box pruning. The source report contains every collision witness.",
        "",
        "## Receiver and support results",
        "",
        "The four fixed center-kicker axes are modeled at X=±70 mm, Z=60/192 mm, along −Y. All four have full nominal axis-volume reception in their assigned backer; each 63.5 mm purchased-length axis enters 45.24375 mm of backing beyond the kicker panel back. Both kicker inner-edge support sample sets are contained by the backers. The gross backer/header contact is 7903.21 mm² per side before bolt bores.",
        "",
        "WJ-05 tool geometry uses one Ko-ken 3305A-7/16 outer-envelope proxy. It includes seated and prior approach-endpoint placements plus their continuous coaxial sweep. Top seat datum is the nut bearing face at Z=283.096 mm; bottom seat datum is the bolt underhead face at Z=4.968 mm. The modeled exterior envelope is checked against wood, fixed axes, and protected services. Intended occupancy at the named nut/head is recorded separately and is not an obstacle clash. Internal 12-point profile, fit, clearances, driver, tolerances, and tool access are not assessed. Nominal positive gaps are not tolerance or assembly acceptance. A geometry-clear result does not establish connection resistance or an integrated frame.",
        "",
        "## Bolt thread and tool screen",
        "",
        "The shaft begins at the bolt underhead bearing face, Z=4.968 mm, beneath the 2.032 mm bottom washer. Wood bearing starts at Z=7 mm and ends at Z=277 mm: 270 mm of wood, but 272.032 mm from the underhead datum to the wood top. This screen does not require a smooth shank through all 270 mm of wood. Under NDS 12.3.7.2, nominal D is permitted only when thread bearing in the member holding the threads stays within one-quarter of that member's full bearing length; otherwise use measured root diameter. Here the tip member is the 38.1 mm header, so that limit is 9.525 mm. Complete nut engagement and at least 3.175 mm of threaded tip remain required. The 12-in ASME envelope has 268.478–279.400 mm smooth-shank length, corresponding to at most 3.554 mm of thread bearing in the header, but its long-shank end does not guarantee full nut engagement. Type A washer thickness is 1.295–2.032 mm; the finished hex nut maximum thickness is 5.740 mm.",
        "",
        "| Nominal bolt and top washer stack | Standard smooth/thread transition range from underhead (mm) | Measured transition band for NDS limited-thread use and full nut engagement (mm) | Worst-case header thread bearing |",
        "|---|---:|---:|---|",
        f"| 11.5 in + 1 washer | {short_single['asme_smooth_shank_length_range_mm_from_underhead'][0]:.2f}…{short_single['asme_smooth_shank_length_range_mm_from_underhead'][1]:.2f} | {short_single['thread_transition_interval_for_nds_limited_thread_and_full_nut_engagement_mm_from_underhead'][0]:.2f}…{short_single['thread_transition_interval_for_nds_limited_thread_and_full_nut_engagement_mm_from_underhead'][1]:.2f} | {short_single['thread_exposure_in_header_mm_at_standard_min_max_smooth_shank'][0]:.2f} mm (over the 9.525 mm NDS nominal-D limit) |",
        f"| 12 in + 1 washer | {long_single['asme_smooth_shank_length_range_mm_from_underhead'][0]:.2f}…{long_single['asme_smooth_shank_length_range_mm_from_underhead'][1]:.2f} | {long_single['thread_transition_interval_for_nds_limited_thread_and_full_nut_engagement_mm_from_underhead'][0]:.2f}…{long_single['thread_transition_interval_for_nds_limited_thread_and_full_nut_engagement_mm_from_underhead'][1]:.2f} | {long_single['thread_exposure_in_header_mm_at_standard_min_max_smooth_shank'][0]:.2f} mm (within limit) |",
        f"| 12 in + 3 washers | {long_triple['asme_smooth_shank_length_range_mm_from_underhead'][0]:.2f}…{long_triple['asme_smooth_shank_length_range_mm_from_underhead'][1]:.2f} | {long_triple['thread_transition_interval_for_nds_limited_thread_and_full_nut_engagement_mm_from_underhead'][0]:.2f}…{long_triple['thread_transition_interval_for_nds_limited_thread_and_full_nut_engagement_mm_from_underhead'][1]:.2f} | {long_triple['thread_exposure_in_header_mm_at_standard_min_max_smooth_shank'][0]:.2f} mm (within limit) |",
        "",
        "The corrected three-washer transition band is 262.507–275.918 mm from the underhead. This permits up to 9.525 mm thread bearing in the 38.1 mm header and requires threads to start by the nut bearing face for full engagement. For the 12-in standard envelope, the thread starts 3.554 mm into the header at its shortest smooth-body extreme, which fits the NDS one-quarter limit; a measured transition is still needed to prove full nut engagement. The 11.5-in envelope permits 16.254 mm in the header at its shortest smooth-body extreme, so it needs a measured transition in its allowed interval or a root-diameter calculation. No SKU is accepted.",
        "",
        "### Conditional receiving specification for the modeled three-washer stack",
        "",
        "The wood path is Z=7–277 mm, with a 4.968 mm underhead datum. On receipt, measure each 12-in bolt's delivered underhead length, thread transition, nut, and washer stack together. For the three-washer case, require the transition to fall between 262.507 mm and the underhead-to-wood-top distance plus the actual washer stack; with three minimum washers this is 262.507–275.918 mm. This is an NDS limited-thread and full-nut-engagement receive band, not a full-wood smooth-shank requirement. If thread bearing exceeds the 9.525 mm header limit, carry measured root diameter into the NDS lateral-yield method. Also verify threads through the complete nut and at least 3.175 mm beyond it. No SKU currently meets this evidence requirement; physical receive fields remain blank.",
        "",
        f"Tool screen uses cataloged {access['socket_basis']['product']}: 55 mm overall length, 17.2 mm maximum OD, 16 mm working-end OD, H1=12 mm, H2=41.5 mm. The external model applies maximum OD over full length; it does not model internal profile or claim a fit. At the bottom stations, the seated external envelope reaches {BOLT_UNDERHEAD_Z_MM - SOCKET_LENGTH_MM:.3f} mm ({BOLT_UNDERHEAD_Z_MM - SOCKET_LENGTH_MM:.3f} mm below member bottom), and the full insertion sweep reaches {BOLT_UNDERHEAD_Z_MM - SOCKET_LENGTH_MM - HEAD_HEIGHT_MM:.3f} mm below member bottom. The 1.4 mm value from 20 mm counterbore diameter less 17.2 mm envelope is a nominal radial remainder only. Ratchet/extension, drive-end access, floor clearance, and installation/removal sequence are unmodeled and unverified.",
        "",
        "Dimension references: [ASME B18.2.1-2012](https://studylib.net/doc/27174816/asme-b18.2.1-2012), [ASME B18.2.2-2022](https://studylib.net/doc/27188368/asme-b18.2.2-2022), [12-in bolt example](https://boltdepot.com/Product-Details?product=5238), [finished hex nut](https://boltdepot.com/Product-Details?product=2563), [1/4-in washer](https://boltdepot.com/Product-Details?product=2947), [Type A washer catalog dimensions](https://www.panduit.com/content/dam/panduit/en/products/media/6/86/986/6986/101806986.pdf), [Type A washer tolerance reference](https://www.nvent.com/sites/default/files/acquiadam_assets/2021-09/CB_Technical%20Reference.pdf), and [7/16-in deep socket](https://kokenusa.com/products/deep-socket-3-8sq-dr-12-p-7-16).",
        "",
        "## Required follow-up",
        "",
        "- Establish a mechanics model for two long bolts parallel to backer grain, header bearing, the eccentric backer-to-header transfer, and the bottom counterbores. No capacity is assigned here.",
        "- Obtain a 12-in partial-thread bolt whose coupled delivered length, smooth-shank/thread transition, measured three-washer stack, nut seat, and 3.175 mm minimum thread projection satisfy the conditional receiving specification; otherwise this receiver connection remains blocked.",
        "- Check whether the bottom head/tool pockets and socket/ratchet can be assembled and removed in the declared frame sequence while respecting the floor assumption.",
        "- Integrate and recheck the changed center-post/header/principal duties, all 24 duty owners, the other 62 fixed panel axes, and twelve frame-bolt arrangements in the complete WJ-06 model.",
        "- Add dimensional tolerances, contact/opening, tool swing, member transport, and complete forward/reverse assembly to WJ-07.",
        "",
        "Physical receiving and observation fields stay blank. This file does not authorize purchase, cutting, drilling, fabrication, or use. No resistance or load-capacity result is assigned.",
        "",
        "Reproduce with `uv run python scripts/wood_joints_wj05_center_backer_transfer_probe.py --write`. Source hashes are recorded in [`wj05-center-backer-transfer.json`](wj05-center-backer-transfer.json).",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = _build_report()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT_JSON.write_text(rendered)
        OUTPUT_MD.write_text(_markdown(result))
        print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
        print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
