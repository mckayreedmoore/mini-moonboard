"""Detached inward-post topology screen for the outer-header barrel duties.

Only candidate solids move in memory. Source wood, fixed connection axes, and
the published viewer are not changed. Positive projection overlap is not a
wood-bearing or connection-capacity qualification.
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

SCHEMA = "owner_barrel_outer_header_post_shift_probe/v1"
SHIFTS_INWARD_MM = (0, 20, 40, 60, 80, 90)
TOOL_RADIUS_MM = 10.0  # Same nominal 20 x 40 mm straight access as the prior search.


def _overlap(first_min, first_max, second_min, second_max):
    return max(0.0, min(first_max, second_max) - max(first_min, second_min))


def _axis_solid(connection):
    return cq.Solid.makeCylinder(
        connection.diameter / 2,
        connection.length,
        connection.start,
        connection.direction.normalized(),
    )


def _front_axes(side, post, connections):
    pb = post.BoundingBox()
    axes = sorted(
        (row for row in connections if row.name.startswith(f"rail_front_bolt_{side}_")),
        key=lambda row: row.name,
    )
    if len(axes) != 2 or any(
        row.members != (f"base_post_outer_{side}", f"base_floor_{side}") for row in axes
    ):
        raise ValueError(f"{side}: two retained rail-front bolt axes required")
    centerline, bore_hits = [], []
    for row in axes:
        end = row.start + row.direction.normalized() * row.length
        centerline.append(
            round(
                _overlap(
                    pb.xmin, pb.xmax, min(row.start.x, end.x), max(row.start.x, end.x)
                ),
                6,
            )
        )
        bore_hits.append(round(protected._volume(_axis_solid(row), post), 6))
    return axes, centerline, bore_hits


def _panel_receiver_axes(side, post, connections):
    """Check unchanged kicker screws whose named receiver is the outer post."""
    name = f"base_post_outer_{side}"
    pb = post.BoundingBox()
    axes = sorted(
        (row for row in connections if name in row.members), key=lambda row: row.name
    )
    if len(axes) != 2 or any(
        not row.name.startswith(f"round_kicker_{side}_rim_") for row in axes
    ):
        raise ValueError(f"{side}: two fixed kicker-to-outer-post screws required")
    x_margin, centerline, bore_hits = [], [], []
    for row in axes:
        end = row.start + row.direction.normalized() * row.length
        margin = min(row.start.x - pb.xmin, pb.xmax - row.start.x)
        x_margin.append(round(margin, 6))
        centerline.append(
            round(
                _overlap(
                    pb.ymin, pb.ymax, min(row.start.y, end.y), max(row.start.y, end.y)
                )
                if margin > 0 and pb.zmin < row.start.z < pb.zmax
                else 0.0,
                6,
            )
        )
        bore_hits.append(round(protected._volume(_axis_solid(row), post), 6))
    return axes, x_margin, centerline, bore_hits


def _support(side, post, header, rim):
    pb, hb, rb = (shape.BoundingBox() for shape in (post, header, rim))
    butt_x = _overlap(pb.xmin, pb.xmax, hb.xmin, hb.xmax)
    butt_y = _overlap(pb.ymin, pb.ymax, hb.ymin, hb.ymax)
    if abs(pb.zmax - hb.zmin) > 1e-6:
        raise ValueError(f"{side}: post/header butt elevation changed")
    return {
        "header_butt_area_mm2": round(butt_x * butt_y, 6),
        "rim_projection_overlap_x_mm": round(
            _overlap(pb.xmin, pb.xmax, rb.xmin, rb.xmax), 6
        ),
        "post_bounds_x_mm": [round(pb.xmin, 6), round(pb.xmax, 6)],
        "rim_bounds_x_mm": [round(rb.xmin, 6), round(rb.xmax, 6)],
    }


def _thresholds(side, post, rim, front_axes, panel_axes):
    """Necessary X thresholds for a centered top-entry tool and old bolt axes."""
    pb, rb = post.BoundingBox(), rim.BoundingBox()
    center = (pb.xmin + pb.xmax) / 2
    if side == "left":
        tool_clear = rb.xmax + TOOL_RADIUS_MM - center
        bolt_lost = min(row.start.x - pb.xmin for row in front_axes)
        panel_lost = min(pb.xmax - row.start.x for row in panel_axes)
        rim_lost = rb.xmax - pb.xmin
    else:
        tool_clear = center - (rb.xmin - TOOL_RADIUS_MM)
        bolt_lost = min(pb.xmax - row.start.x for row in front_axes)
        panel_lost = min(row.start.x - pb.xmin for row in panel_axes)
        rim_lost = pb.xmax - rb.xmin
    return {
        "minimum_shift_for_20mm_tool_rim_clearance_mm": round(tool_clear, 6),
        "shift_at_loss_of_front_bolt_centerline_post_overlap_mm": round(bolt_lost, 6),
        "shift_at_loss_of_kicker_screw_receiver_centerline_mm": round(panel_lost, 6),
        "shift_at_loss_of_all_post_rim_x_projection_mm": round(rim_lost, 6),
    }


@lru_cache(maxsize=1)
def search():
    """Screen six mirrored post shifts, fixed axes, and finite protected paths."""
    assembly = build_assembly()
    fixed = protected.inventory()
    if (
        len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
    ):
        raise ValueError("Exact kerf-right fixed connection inventory changed")
    wood = assembly["wood"]
    candidates, thresholds = [], {}
    for side, station in STATIONS.items():
        post_name, rim_name = f"base_post_outer_{side}", f"base_side_{side}"
        original, rim, header = wood[post_name], wood[rim_name], wood["base_header"]
        sign = 1 if side == "left" else -1
        front_axes, baseline_overlap, _ = _front_axes(
            side, original, assembly["frame_connections"]
        )
        if any(
            value < original.BoundingBox().xlen - 1e-5 for value in baseline_overlap
        ):
            raise ValueError(
                f"{side}: old front bolt axes no longer span original post"
            )
        panel_axes, _, baseline_panel, _ = _panel_receiver_axes(
            side, original, assembly["panel_connections"]
        )
        if any(value <= 0 for value in baseline_panel):
            raise ValueError(f"{side}: fixed kicker screw misses original post")
        thresholds[side] = _thresholds(side, original, rim, front_axes, panel_axes)
        other_physical, other_paths = _other_station_solids(assembly, station)
        for shift in SHIFTS_INWARD_MM:
            post = original.translate(cq.Vector(sign * shift, 0, 0))
            trial_wood = dict(wood)
            trial_wood[post_name] = post
            pb = post.BoundingBox()
            xmid = (pb.xmin + pb.xmax) / 2
            outer_header = _screen_pose(
                side,
                (
                    f"post_shift_{shift}",
                    "vertical_top",
                    xmid,
                    xmid,
                    (-135.0, -75.0),
                    70.0,
                ),
                trial_wood,
                fixed,
                other_physical,
                other_paths,
            )
            support = _support(side, post, header, rim)
            _, front_overlap, front_bore_hits = _front_axes(
                side, post, assembly["frame_connections"]
            )
            _, panel_margin, panel_overlap, panel_bore_hits = _panel_receiver_axes(
                side, post, assembly["panel_connections"]
            )
            post_fixed_hits = {
                family: hits
                for family, hits in protected.hits({"shifted_post": post}, fixed)[
                    "shifted_post"
                ].items()
                if hits
            }
            intended_front = {row.name for row in front_axes}
            intended_panel = {row.name for row in panel_axes}
            unexpected_fixed = {}
            for family, hits in post_fixed_hits.items():
                remaining = {
                    name: volume
                    for name, volume in hits.items()
                    if (family != "frame_bolts" or name not in intended_front)
                    and (family != "panel_screws" or name not in intended_panel)
                }
                if remaining:
                    unexpected_fixed[family] = remaining
            unrelated_wood = {
                name: shape
                for name, shape in wood.items()
                if name not in {post_name, "base_header"}
            }
            post_wood_hits = _hits(post, unrelated_wood)
            post_neighbor_physical_hits = _hits(post, other_physical)
            post_neighbor_path_hits = _hits(post, other_paths)
            gates = {
                "outer_header_geometry": outer_header["geometry_gates_clear"],
                "fixed_front_bolts_enter_post": all(
                    value > 0 for value in front_overlap
                ),
                "fixed_kicker_screws_enter_post": all(
                    value > 0 for value in panel_overlap
                ),
                "rim_projection_overlap": support["rim_projection_overlap_x_mm"] > 0,
                "full_header_butt": abs(
                    support["header_butt_area_mm2"]
                    - original.BoundingBox().xlen * original.BoundingBox().ylen
                )
                < 1e-4,
                "shifted_post_unrelated_wood": not post_wood_hits,
                "shifted_post_protected": not unexpected_fixed,
                "shifted_post_neighbor_physical": not post_neighbor_physical_hits,
                "shifted_post_neighbor_paths": not post_neighbor_path_hits,
            }
            candidates.append(
                {
                    "side": side,
                    "station": station,
                    "shift_inward_mm": shift,
                    **support,
                    "front_bolt_axis_post_centerline_overlap_mm": front_overlap,
                    "front_bolt_bore_post_hits_mm3": front_bore_hits,
                    "kicker_screw_axis_post_x_edge_margin_mm": panel_margin,
                    "kicker_screw_axis_post_centerline_overlap_mm": panel_overlap,
                    "kicker_screw_bore_post_hits_mm3": panel_bore_hits,
                    "shifted_post_unexpected_fixed_hits_mm3": unexpected_fixed,
                    "shifted_post_unrelated_wood_hits_mm3": post_wood_hits,
                    "shifted_post_neighbor_physical_hits_mm3": post_neighbor_physical_hits,
                    "shifted_post_neighbor_path_hits_mm3": post_neighbor_path_hits,
                    "outer_header": outer_header,
                    "failed_gates": [
                        name for name, passed in gates.items() if not passed
                    ],
                    "nominal_fixed_axis_geometry_clear": all(gates.values()),
                }
            )
    return {
        "schema": SCHEMA,
        "width_option": KERF_RIGHT,
        "wood_basis": assembly["diagnostics"]["wood_basis"],
        "fixed_axes": {"panel_screws": 66, "frame_bolts": 12},
        "protected_counts": fixed["counts"],
        "shifts_inward_mm": list(SHIFTS_INWARD_MM),
        "thresholds_by_side_mm": thresholds,
        "candidates": candidates,
        "fully_viable_fixed_axis_poses": [
            f"{row['side']}/{row['shift_inward_mm']}"
            for row in candidates
            if row["nominal_fixed_axis_geometry_clear"]
        ],
        "limits": (
            "Projected rim overlap is only a necessary geometric proxy, not a verified "
            "bearing/support path. Fixed rail-front bolts and kicker screws must "
            "still enter their named post receiver; "
            "hardware dimensions, delivered tools, complete thread, tolerances, "
            "insertion sequence, changed-member strength, and loads remain open."
        ),
        "viewer_changed": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(search(), indent=2, sort_keys=True))
