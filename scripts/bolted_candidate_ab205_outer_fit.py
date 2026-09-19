"""Nominal AB205 outer-base fit against current raw CAD; no joint approval."""

import csv
from math import hypot, isfinite, pi
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


def _grain_ray_to_rim_end(
    rim: cq.Solid, start: cq.Vector, grain: cq.Vector
) -> float | None:
    """Find the first raw end-face hit along a bounded reverse-grain ray."""
    box = rim.BoundingBox()
    limit = hypot(hypot(box.xlen, box.ylen), box.zlen)
    hits = []
    for face in rim.Faces():
        if face.geomType() != "PLANE":
            continue
        normal = face.normalAt()
        approach = grain.dot(normal)
        if approach >= -1e-7:
            continue
        distance = (start - face.Center()).dot(normal) / approach
        if not 1e-7 < distance <= limit:
            continue
        hit = start - grain * distance
        if face.distance(cq.Vertex.makeVertex(*hit.toTuple())) <= 1e-5:
            hits.append(distance)
    return min(hits) if hits else None


def screen_outer_fit(
    side: Side = "left", vertical_leg: Leg = "long", row_y_mm: float | None = None
) -> dict[str, object]:
    """Screen one nominal factory row against raw wood and retained CAD axes."""
    if side not in ("left", "right") or vertical_leg not in ("long", "short"):
        raise ValueError("Expected left/right side and long/short vertical leg")
    if row_y_mm is not None and not isfinite(row_y_mm):
        raise ValueError("Trial row must be finite")
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    station = next(
        item for item in frame.stations() if item[0] == f"clip_angle_base_{side}"
    )
    _, origin, *_ = station
    row_y = origin.y if row_y_mm is None else row_y_mm
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
            cq.Vector(inner_x, row_y, origin.z + offset * 25.4),
            cq.Vector(-sign, 0, 0),
        )
        for offset in vertical
    ] + [
        cq.Solid.makeCylinder(
            bore_radius,
            header_depth,
            cq.Vector(inner_x + sign * offset * 25.4, row_y, origin.z),
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
    grain = cq.Vector(0, lines[0][2], 1).normalized()
    rim_ray_x = (rim.BoundingBox().xmin + rim.BoundingBox().xmax) / 2
    rim_end_rays = [
        _grain_ray_to_rim_end(
            rim, cq.Vector(rim_ray_x, row_y, origin.z + offset * 25.4), grain
        )
        for offset in vertical
    ]
    edge_distances = []
    for offset in vertical:
        z = origin.z + offset * 25.4
        lower, upper = sorted(_line_y(line, z) for line in lines)
        edge_distances.append(min((row_y - lower) * ny, (upper - row_y) * ny))
    header_edge = min(
        row_y - header.BoundingBox().ymin, header.BoundingBox().ymax - row_y
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
        "trial_row_y_mm": _rounded(row_y),
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
        "installed_bores_full_raw_wood": all(value >= 1 - 1e-5 for value in fractions),
        "rim_hole_edge_distances_mm": [_rounded(value) for value in edge_distances],
        "rim_hole_min_4d_reserve_mm": _rounded(min(edge_distances) - 4 * bolt_diameter),
        "header_row_edge_distance_mm": _rounded(header_edge),
        "header_row_4d_reserve_mm": _rounded(header_edge - 4 * bolt_diameter),
        "nearest_rim_hole_grain_ray_mm": _rounded(vertical[0] * 25.4 / ny),
        "rim_hole_grain_rays_to_actual_end_mm": [
            _rounded(value) if value is not None else None for value in rim_end_rays
        ],
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


def search_outer_fit(
    side: Side = "left", max_row_displacement_mm: float = 50.0
) -> dict[str, object]:
    """Find the nominal both-edge 4D Y bands within a limited clip-row move."""
    if (
        side not in ("left", "right")
        or not isfinite(max_row_displacement_mm)
        or max_row_displacement_mm < 0
    ):
        raise ValueError("Expected left/right side and finite nonnegative displacement")
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    station = next(
        item for item in frame.stations() if item[0] == f"clip_angle_base_{side}"
    )
    _, origin, *_ = station
    rim = parts[f"base_side_{side}"]
    header = parts["base_header"]
    inner_x = rim.BoundingBox().xmax if side == "left" else rim.BoundingBox().xmin
    lines = _grain_edge_lines(_broad_face(rim, inner_x))
    if len(lines) != 2 or abs(lines[0][2] - lines[1][2]) > 1e-5:
        raise ValueError("Expected two parallel rim grain edges")
    ny = 1 / hypot(1, lines[0][2])
    four_d = 4 * 12.7
    header_box = header.BoundingBox()
    options = {}
    for leg, offsets in (("long", (1.4375, 3.3125)), ("short", (0.8125, 2.6875))):
        bounds = [
            tuple(sorted(_line_y(line, origin.z + offset * 25.4) for line in lines))
            for offset in offsets
        ]
        lower = max(
            origin.y - max_row_displacement_mm,
            header_box.ymin + four_d,
            *(edge[0] + four_d / ny for edge in bounds),
        )
        upper = min(
            origin.y + max_row_displacement_mm,
            header_box.ymax - four_d,
            *(edge[1] - four_d / ny for edge in bounds),
        )
        option: dict[str, object] = {
            "reversible_4d_y_lower_mm": _rounded(lower),
            "reversible_4d_y_upper_mm": _rounded(upper),
            "reversible_4d_y_band_width_mm": _rounded(max(0.0, upper - lower)),
            "conditional_4d_both_members": False,
            "rim_end_distance_classified": False,
            "drilling_released": False,
        }
        if lower <= upper:
            trial = screen_outer_fit(side, leg, (lower + upper) / 2)
            option.update(
                trial_row_y_mm=trial["trial_row_y_mm"],
                row_displacement_mm=_rounded(float(trial["trial_row_y_mm"]) - origin.y),
                raw_wood_bore_fractions=trial["raw_wood_bore_fractions"],
                installed_bores_full_raw_wood=trial["installed_bores_full_raw_wood"],
                rim_hole_grain_rays_to_actual_end_mm=trial[
                    "rim_hole_grain_rays_to_actual_end_mm"
                ],
                rim_hole_min_4d_reserve_mm=trial["rim_hole_min_4d_reserve_mm"],
                header_row_4d_reserve_mm=trial["header_row_4d_reserve_mm"],
                retained_axes_inspected=trial["retained_axes_inspected"],
                intersecting_retained_axis_ids=trial["intersecting_retained_axis_ids"],
                front_bolt_axis_ids=trial["front_bolt_axis_ids"],
                nearest_new_rim_bore_above_front_bolt_clearance_mm=trial[
                    "nearest_new_rim_bore_above_front_bolt_clearance_mm"
                ],
                conditional_4d_both_members=(
                    float(trial["rim_hole_min_4d_reserve_mm"]) >= -1e-5
                    and float(trial["header_row_4d_reserve_mm"]) >= -1e-5
                    and bool(trial["installed_bores_full_raw_wood"])
                    and not trial["intersecting_retained_axis_ids"]
                ),
            )
        options[f"{leg}_vertical"] = option
    return {
        "station": station[0],
        "legacy_row_y_mm": _rounded(origin.y),
        "maximum_row_displacement_mm": max_row_displacement_mm,
        "conditional_loaded_edge_rule": "reversible 4D from both nominal bolt centers on rim and header",
        "orientations": options,
        "frozen_panel_axes_moved": False,
        "installed_hardware_stack_verified": False,
        "rim_end_distance_classified": False,
        "drilling_released": False,
    }
