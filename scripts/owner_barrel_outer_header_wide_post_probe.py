"""Detached whole-timber width screen for the two outer-header barrel duties.

This replaces each outer post only in memory. All fixed screw/bolt axes, the
header, side rims, and the published viewer remain unchanged. Nominal CAD fit
does not establish purchased hardware, a structural joint, or drilling sizes.
"""

import json
from functools import lru_cache

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT
from scripts import owner_layout_protected as protected
from scripts.owner_barrel_layout_assembly import build_assembly
from scripts.owner_barrel_outer_header_clearance_probe import (
    STATIONS,
    _hits,
    _other_station_solids,
    _screen_pose,
)
from scripts.owner_barrel_outer_header_post_shift_probe import (
    _front_axes,
    _panel_receiver_axes,
    _support,
)

SCHEMA = "owner_barrel_outer_header_wide_post_probe/v1"
ACCESS_RADIUS_MM = 10.0
NOMINAL_BORE_EDGE_MM = 3.75
ROW_Y_MM = (-135.0, -75.0)
# Actual dressed dimensions. The rotated sections put their wide face in X.
# An ordinary 6x6 is included to test a section with BOTH necessary spans.
SECTIONS_MM = {
    "2x6_rotated": (139.7, 38.1),
    "4x6": (88.9, 139.7),
    "6x6": (139.7, 139.7),
}
SHIFTS_MM = (0.0, 10.0)


def _replacement_post(original, side, width_x, depth_y, inward_shift):
    old = original.BoundingBox()
    outer_x = (old.xmin + inward_shift) if side == "left" else (old.xmax - inward_shift)
    xmin = outer_x if side == "left" else outer_x - width_x
    ymin = (old.ymin + old.ymax - depth_y) / 2
    return cq.Solid.makeBox(width_x, depth_y, old.zlen, cq.Vector(xmin, ymin, old.zmin))


def _x_corridor(side, post, rim, screw_x):
    """Tool-center interval wholly in post and strictly outside side rim."""
    pb, rb = post.BoundingBox(), rim.BoundingBox()
    if side == "left":
        lower = max(pb.xmin + ACCESS_RADIUS_MM, rb.xmax + ACCESS_RADIUS_MM)
        upper = pb.xmax - ACCESS_RADIUS_MM
        axis = lower + 0.1
        screw_margin = screw_x - pb.xmin
        minimum_width = rb.xmax + 2 * ACCESS_RADIUS_MM - screw_x
    else:
        lower = pb.xmin + ACCESS_RADIUS_MM
        upper = min(pb.xmax - ACCESS_RADIUS_MM, rb.xmin - ACCESS_RADIUS_MM)
        axis = upper - 0.1
        screw_margin = pb.xmax - screw_x
        minimum_width = screw_x - (rb.xmin - 2 * ACCESS_RADIUS_MM)
    width = max(0.0, upper - lower)
    return {
        "tool_center_interval_x_mm": [round(lower, 6), round(upper, 6)],
        "tool_center_corridor_width_mm": round(width, 6),
        "chosen_axis_x_mm": round(axis, 6) if width > 0.1 else None,
        "fixed_kicker_screw_x_mm": screw_x,
        "fixed_kicker_screw_outer_margin_mm": round(screw_margin, 6),
        "minimum_x_width_for_tool_and_fixed_screw_mm": round(minimum_width, 6),
    }


def _y_support(post, rows):
    pb = post.BoundingBox()
    margins = [round(min(y - pb.ymin, pb.ymax - y), 6) for y in rows]
    return {
        "row_y_mm": list(rows),
        "row_edge_margins_y_mm": margins,
        "minimum_y_depth_for_two_20mm_rows_mm": round(
            rows[1] - rows[0] + 2 * ACCESS_RADIUS_MM, 6
        ),
        "both_machine_bores_within_post_y": all(
            margin >= NOMINAL_BORE_EDGE_MM for margin in margins
        ),
        "both_20mm_access_rows_within_post_y": all(
            margin >= ACCESS_RADIUS_MM for margin in margins
        ),
        "row_spacing_mm": round(rows[1] - rows[0], 6),
    }


def _new_post_hits(post, post_name, wood, fixed, assembly, station, front, panel):
    fixed_hits = protected.hits({"post": post}, fixed)["post"]
    intended_front = {row.name for row in front}
    intended_panel = {row.name for row in panel}
    unexpected = {}
    for family, hits in fixed_hits.items():
        remaining = {
            name: value
            for name, value in hits.items()
            if (family != "frame_bolts" or name not in intended_front)
            and (family != "panel_screws" or name not in intended_panel)
        }
        if remaining:
            unexpected[family] = remaining
    unrelated = {
        name: shape
        for name, shape in wood.items()
        if name not in {post_name, "base_header"}
    }
    other_physical, other_paths = _other_station_solids(assembly, station)
    return {
        "unexpected_protected_hits_mm3": unexpected,
        "unrelated_wood_hits_mm3": _hits(post, unrelated),
        "other_barrel_physical_hits_mm3": _hits(post, other_physical),
        "other_barrel_path_hits_mm3": _hits(post, other_paths),
    }


@lru_cache(maxsize=1)
def search():
    assembly = build_assembly()
    wood, fixed = assembly["wood"], protected.inventory()
    if (
        len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
    ):
        raise ValueError("Exact fixed connection inventory changed")
    candidates = []
    for side, station in STATIONS.items():
        post_name, rim_name = f"base_post_outer_{side}", f"base_side_{side}"
        original, rim, header = wood[post_name], wood[rim_name], wood["base_header"]
        other_physical, other_paths = _other_station_solids(assembly, station)
        for section, (width_x, depth_y) in SECTIONS_MM.items():
            rows = ROW_Y_MM
            for shift in SHIFTS_MM:
                post = _replacement_post(original, side, width_x, depth_y, shift)
                trial_wood = dict(wood)
                trial_wood[post_name] = post
                y = _y_support(post, rows)
                front, front_overlap, front_hits = _front_axes(
                    side, post, assembly["frame_connections"]
                )
                pb = post.BoundingBox()
                front_y_margins = [
                    round(min(row.start.y - pb.ymin, pb.ymax - row.start.y), 6)
                    for row in front
                ]
                panel, panel_margin, panel_overlap, panel_hits = _panel_receiver_axes(
                    side, post, assembly["panel_connections"]
                )
                screw_x = panel[0].start.x
                if any(abs(row.start.x - screw_x) > 1e-6 for row in panel):
                    raise ValueError(f"{side}: kicker receiver X axes diverged")
                x = _x_corridor(side, post, rim, screw_x)
                support = _support(side, post, header, rim)
                post_hits = _new_post_hits(
                    post, post_name, wood, fixed, assembly, station, front, panel
                )
                # Expensive 3-D row check is relevant only when a whole tool
                # envelope can enter the post and both nominal rows fit.
                row_screen = None
                if (
                    x["chosen_axis_x_mm"] is not None
                    and y["both_20mm_access_rows_within_post_y"]
                ):
                    axis_x = x["chosen_axis_x_mm"]
                    row_screen = _screen_pose(
                        side,
                        (
                            f"{section}_shift_{shift:g}",
                            "vertical_top",
                            axis_x,
                            axis_x,
                            rows,
                            70.0,
                        ),
                        trial_wood,
                        fixed,
                        other_physical,
                        other_paths,
                    )
                gates = {
                    "20mm_x_corridor": x["chosen_axis_x_mm"] is not None,
                    "20mm_y_support_both_rows": y[
                        "both_20mm_access_rows_within_post_y"
                    ],
                    "fixed_kicker_centerlines_enter_post": all(
                        v > 0 for v in panel_overlap
                    ),
                    "fixed_front_bolts_enter_post": all(v > 0 for v in front_overlap)
                    and all(v > 0 for v in front_y_margins),
                    "header_butt_both_rows": all(
                        post.BoundingBox().ymin <= row <= post.BoundingBox().ymax
                        and header.BoundingBox().ymin
                        <= row
                        <= header.BoundingBox().ymax
                        for row in rows
                    ),
                    "rim_x_projection": support["rim_projection_overlap_x_mm"] > 0,
                    "new_post_unrelated_wood": not post_hits["unrelated_wood_hits_mm3"],
                    "new_post_protected": not post_hits[
                        "unexpected_protected_hits_mm3"
                    ],
                    "new_post_other_barrel": not post_hits[
                        "other_barrel_physical_hits_mm3"
                    ]
                    and not post_hits["other_barrel_path_hits_mm3"],
                    "outer_header_rows": bool(
                        row_screen and row_screen["geometry_gates_clear"]
                    ),
                }
                candidates.append(
                    {
                        "side": side,
                        "section": section,
                        "nominal_section_mm": [width_x, depth_y],
                        "shift_inward_mm": shift,
                        **x,
                        **y,
                        **support,
                        "post_bounds_y_mm": [
                            round(post.BoundingBox().ymin, 6),
                            round(post.BoundingBox().ymax, 6),
                        ],
                        "fixed_front_axis_post_overlap_mm": front_overlap,
                        "fixed_front_axis_post_y_margin_mm": front_y_margins,
                        "fixed_front_bore_post_hits_mm3": front_hits,
                        "fixed_kicker_axis_post_overlap_mm": panel_overlap,
                        "fixed_kicker_axis_x_margin_mm": panel_margin,
                        "fixed_kicker_bore_post_hits_mm3": panel_hits,
                        **post_hits,
                        "outer_header": row_screen,
                        "failed_gates": [
                            name for name, passed in gates.items() if not passed
                        ],
                        "nominal_geometry_clear": all(gates.values()),
                    }
                )
    return {
        "schema": SCHEMA,
        "width_option": KERF_RIGHT,
        "fixed_axes": {"panel_screws": 66, "frame_bolts": 12},
        "protected_counts": fixed["counts"],
        "sections_mm": SECTIONS_MM,
        "shifts_inward_mm": list(SHIFTS_MM),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "geometry_clear_poses": [
            f"{row['side']}/{row['section']}/{row['shift_inward_mm']:g}"
            for row in candidates
            if row["nominal_geometry_clear"]
        ],
        "limits": "Nominal whole-timber, fixed-axis fit only; no delivered hardware/tool dimensions, wood capacities, loads, assembly sequence, or drilling release",
        "viewer_changed": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(search(), indent=2, sort_keys=True))
