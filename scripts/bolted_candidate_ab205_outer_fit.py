"""Nominal AB205 outer-base fit against current raw CAD; no joint approval."""

import csv
from math import hypot, pi
from pathlib import Path
from typing import Literal

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as frame
from scripts.bolted_candidate_ab205_center_fit import _grain_edge_lines, _line_y

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
Side = Literal["left", "right"]
Leg = Literal["long", "short"]


def _rounded(value: float) -> float:
    return round(value, 6)


def _broad_face(shape: cq.Solid, x_mm: float) -> cq.Face:
    return next(
        face
        for face in shape.Faces()
        if face.Vertices()
        and all(abs(vertex.Center().x - x_mm) < 1e-5 for vertex in face.Vertices())
    )


def screen_outer_fit(
    side: Side = "left", vertical_leg: Leg = "long"
) -> dict[str, object]:
    """Screen the factory pattern at the existing clip origin, including retained axes."""
    if side not in ("left", "right") or vertical_leg not in ("long", "short"):
        raise ValueError("Expected left/right side and long/short vertical leg")
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    station = next(
        item for item in frame.stations() if item[0] == f"clip_angle_base_{side}"
    )
    _, origin, *_ = station
    rim = parts[f"base_side_{side}"]
    header = parts["base_header"]
    runner = parts[f"base_floor_{side}"]
    post = parts[f"base_post_outer_{side}"]
    sign = 1 if side == "left" else -1
    inner_x = rim.BoundingBox().xmax if side == "left" else rim.BoundingBox().xmin
    assert abs(inner_x - origin.x) < 1e-5
    width = 1.625 * 25.4
    thickness = 0.25 * 25.4
    bore_radius = 0.5625 * 25.4 / 2
    bolt_diameter = 0.5 * 25.4
    offsets = {"long": (1.4375, 3.3125), "short": (0.8125, 2.6875)}
    vertical = offsets[vertical_leg]
    horizontal = offsets["short" if vertical_leg == "long" else "long"]
    rim_depth = rim.BoundingBox().xlen
    header_depth = header.BoundingBox().zlen
    bores = [
        cq.Solid.makeCylinder(
            bore_radius,
            rim_depth,
            cq.Vector(inner_x, origin.y, origin.z + offset * 25.4),
            cq.Vector(-sign, 0, 0),
        )
        for offset in vertical
    ] + [
        cq.Solid.makeCylinder(
            bore_radius,
            header_depth,
            cq.Vector(inner_x + sign * offset * 25.4, origin.y, origin.z),
            cq.Vector(0, 0, -1),
        )
        for offset in horizontal
    ]
    fractions = [
        bore.intersect(receiver).Volume() / (pi * bore_radius**2 * length)
        for bore, receiver, length in zip(
            bores,
            (rim, rim, header, header),
            (rim_depth, rim_depth, header_depth, header_depth),
            strict=True,
        )
    ]
    face = _broad_face(rim, inner_x)
    lines = _grain_edge_lines(face)
    ny = 1 / hypot(1, lines[0][2])
    edge_distances = []
    for offset in vertical:
        z = origin.z + offset * 25.4
        lower, upper = sorted(_line_y(line, z) for line in lines)
        edge_distances.append(min((origin.y - lower) * ny, (upper - origin.y) * ny))
    header_edge = min(
        origin.y - header.BoundingBox().ymin, header.BoundingBox().ymax - origin.y
    )
    # Nominal rectangular flange extents omit the formed bend radius.
    leg_height = (4.125 if vertical_leg == "long" else 3.5) * 25.4
    leg_reach = (3.5 if vertical_leg == "long" else 4.125) * 25.4
    plate_top = origin.z + leg_height
    runner_top = runner.BoundingBox().zmax
    post_top = post.BoundingBox().zmax
    nominal_pad_height = 127.0
    occupied = []
    counts = {"hillman_panel": 0, "bolt_clearance": 0}
    front_ids = []
    panel_kicker_ids = []
    with AXES.open(newline="") as handle:
        for row in csv.DictReader(handle):
            kind = row["shop_opening_kind"]
            if kind not in counts:
                continue
            counts[kind] += 1
            if (
                kind == "hillman_panel"
                and side in row["name"]
                and ("kicker" in row["name"] or "lower" in row["name"])
            ):
                panel_kicker_ids.append(row["name"])
            start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
            direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
            cylinder = cq.Solid.makeCylinder(
                float(row["occupied_diameter_mm"]) / 2,
                float(row["occupied_length_mm"]),
                start,
                direction,
            )
            if any(bore.intersect(cylinder).Volume() > 1e-6 for bore in bores):
                occupied.append(row["name"])
            if row["name"].startswith(f"rail_front_bolt_{side}_"):
                front_ids.append(row["name"])
    if counts != {"hillman_panel": 66, "bolt_clearance": 12} or len(front_ids) != 2:
        raise ValueError("Retained axis inventory changed")
    # The existing front bolts run through post and runner below the rim's butt.
    front_centers_z = [point.z for point in frame.front_points()]
    front_bolt_upper_z = max(front_centers_z) + 9.525 / 2
    return {
        "station": station[0],
        "orientation": f"{vertical_leg}_vertical",
        "source_cad": "mini_moonboard.compact_floor_flush_frame.uncut_wood_parts() and stations()",
        "contact_x_mm": _rounded(origin.x),
        "contact_y_mm": _rounded(origin.y),
        "contact_z_mm": _rounded(origin.z),
        "factory_vertical_offsets_in": list(vertical),
        "factory_horizontal_offsets_in": list(horizontal),
        "nominal_plate_width_mm": _rounded(width),
        "nominal_plate_thickness_mm": _rounded(thickness),
        "nominal_vertical_extent_mm": _rounded(leg_height),
        "nominal_horizontal_extent_mm": _rounded(leg_reach),
        "wood_bore_count": len(bores),
        "nominal_wood_bore_diameter_mm": _rounded(2 * bore_radius),
        "raw_wood_bore_fractions": [_rounded(value) for value in fractions],
        "rim_hole_edge_distances_mm": [_rounded(value) for value in edge_distances],
        "rim_hole_min_4d_reserve_mm": _rounded(min(edge_distances) - 4 * bolt_diameter),
        "header_row_edge_distance_mm": _rounded(header_edge),
        "header_row_4d_reserve_mm": _rounded(header_edge - 4 * bolt_diameter),
        "nearest_rim_hole_grain_ray_mm": _rounded(vertical[0] * 25.4 / ny),
        "rim_end_square_to_grain": False,
        "rim_end_distance_classified": False,
        "retained_axes_source": str(AXES.relative_to(ROOT)),
        "retained_axes_inspected": counts,
        "intersecting_retained_axis_ids": occupied,
        "front_bolt_axis_ids": front_ids,
        "retained_front_bolt_nominal_diameter_mm": 9.525,
        "retained_front_bolt_nominal_length_mm": 101.6,
        "retained_front_bolt_stack_source": "docs/floor-flush-build-package.md",
        "panel_kicker_axis_context_ids": panel_kicker_ids,
        "front_bolt_upper_occupied_z_mm": _rounded(front_bolt_upper_z),
        "nearest_new_rim_bore_above_front_bolt_clearance_mm": _rounded(
            origin.z + vertical[0] * 25.4 - bore_radius - front_bolt_upper_z
        ),
        "runner_top_z_mm": _rounded(runner_top),
        "post_top_z_mm": _rounded(post_top),
        "plate_bottom_above_runner_mm": _rounded(origin.z - runner_top),
        "plate_bottom_above_floor_mm": _rounded(origin.z),
        "nominal_pad_top_z_mm": nominal_pad_height,
        "plate_bottom_above_nominal_pad_mm": _rounded(origin.z - nominal_pad_height),
        "plate_top_z_mm": _rounded(plate_top),
        "nominal_bore_axis_conflict": bool(occupied),
        "complete_washer_nut_stack_verified": False,
        "tool_and_withdrawal_path_verified": False,
        "pad_clearance_verified": False,
        "floor_pad_geometry_available": False,
        "factory_tolerances_verified": False,
        "capacity_established": False,
        "drilling_released": False,
    }
