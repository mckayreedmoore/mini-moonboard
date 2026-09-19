"""Nominal AB205 holes on the current center butt; no connector approval."""

import csv
from math import hypot, pi
from pathlib import Path
from typing import Literal

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as frame

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"


def _principal_broad_face(principal: cq.Solid, x_mm: float) -> cq.Face:
    return next(
        face
        for face in principal.Faces()
        if face.Vertices()
        and all(abs(vertex.Center().x - x_mm) < 1e-5 for vertex in face.Vertices())
    )


def _grain_edge_lines(face: cq.Face) -> tuple[tuple[float, float, float], ...]:
    """Return the two long YZ-side edges as (y0, z0, dy/dz)."""
    lines = []
    for edge in sorted(face.Edges(), key=lambda item: item.Length(), reverse=True)[:2]:
        a, b = (vertex.Center() for vertex in edge.Vertices())
        lines.append((a.y, a.z, (b.y - a.y) / (b.z - a.z)))
    return tuple(lines)


def _line_y(line: tuple[float, float, float], z_mm: float) -> float:
    y0, z0, slope = line
    return y0 + slope * (z_mm - z0)


def screen_center_fit(
    vertical_leg: Literal["long", "short"] = "long",
    row_y_mm: float | None = None,
) -> dict[str, object]:
    """Check one flush-bend orientation against raw CAD, before new drilling."""
    if vertical_leg not in ("long", "short"):
        raise ValueError("Vertical AB205 leg must be long or short")
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    station = next(
        item for item in frame.stations() if item[0] == "clip_split_base_center_left"
    )
    header = parts["base_header"]
    principal = parts["base_principal_center_left"]
    x = principal.BoundingBox().xmin
    z = header.BoundingBox().zmax
    y = station[1].y if row_y_mm is None else row_y_mm
    bolt_diameter_mm = 12.7
    wood_hole_radius_mm = 14.2875 / 2
    loaded_edge_mm = 4 * bolt_diameter_mm
    long_offsets_in = (1.4375, 3.3125)
    short_offsets_in = (0.8125, 2.6875)
    vertical_offsets_in = (
        long_offsets_in if vertical_leg == "long" else short_offsets_in
    )
    horizontal_offsets_in = (
        short_offsets_in if vertical_leg == "long" else long_offsets_in
    )
    vertical_z_mm = tuple(z + offset * 25.4 for offset in vertical_offsets_in)
    face = _principal_broad_face(principal, x)
    lines = _grain_edge_lines(face)
    if len(lines) != 2 or abs(lines[0][2] - lines[1][2]) > 1e-5:
        raise ValueError("Expected two parallel principal broad-face grain edges")
    ny = 1 / hypot(1, lines[0][2])

    def edge_bounds(z_mm: float) -> tuple[float, float]:
        lower, upper = sorted(_line_y(line, z_mm) for line in lines)
        return lower + loaded_edge_mm / ny, upper - loaded_edge_mm / ny

    header_bounds = header.BoundingBox()
    lower_y = max(
        header_bounds.ymin + loaded_edge_mm,
        *(edge_bounds(hole_z)[0] for hole_z in vertical_z_mm),
    )
    upper_y = min(
        header_bounds.ymax - loaded_edge_mm,
        *(edge_bounds(hole_z)[1] for hole_z in vertical_z_mm),
    )
    far_lower_line_y = min(_line_y(line, vertical_z_mm[1]) for line in lines)
    far_upper_line_y = max(_line_y(line, vertical_z_mm[1]) for line in lines)
    far_edge_distance = min((y - far_lower_line_y) * ny, (far_upper_line_y - y) * ny)

    bore_fractions = []
    wood_length_mm = 38.1
    for hole_z in vertical_z_mm:
        bore = cq.Solid.makeCylinder(
            wood_hole_radius_mm,
            wood_length_mm,
            cq.Vector(x, y, hole_z),
            cq.Vector(1, 0, 0),
        )
        bore_fractions.append(
            principal.intersect(bore).Volume()
            / (pi * wood_hole_radius_mm**2 * wood_length_mm)
        )
    for offset_in in horizontal_offsets_in:
        bore = cq.Solid.makeCylinder(
            wood_hole_radius_mm,
            wood_length_mm,
            cq.Vector(x - offset_in * 25.4, y, z),
            cq.Vector(0, 0, -1),
        )
        bore_fractions.append(
            header.intersect(bore).Volume()
            / (pi * wood_hole_radius_mm**2 * wood_length_mm)
        )

    end_minimum_mm = 3.5 * bolt_diameter_mm
    vertical_offset_mm = vertical_offsets_in[0] * 25.4
    return {
        "station": station[0],
        "source_cad": "mini_moonboard.compact_floor_flush_frame.uncut_wood_parts() and stations()",
        "placement": f"AB205 bend at header-top/principal-side butt; {vertical_leg} leg vertical, {'short' if vertical_leg == 'long' else 'long'} leg horizontal; trial hole row Y",
        "contact_x_mm": round(x, 6),
        "contact_z_mm": round(z, 6),
        "legacy_station_y_mm": round(station[1].y, 6),
        "trial_row_y_mm": round(y, 6),
        "bolt_diameter_mm": bolt_diameter_mm,
        "nominal_bore_diameter_mm": 2 * wood_hole_radius_mm,
        "vertical_hole_offsets_from_bend_in": list(vertical_offsets_in),
        "horizontal_hole_offsets_from_bend_in": list(horizontal_offsets_in),
        "wood_bore_count": len(bore_fractions),
        "wood_bore_full_section_fractions": [
            round(value, 6) for value in bore_fractions
        ],
        "legacy_y_far_principal_4d_reserve_mm": round(
            far_edge_distance - loaded_edge_mm, 6
        ),
        "reversible_4d_y_lower_mm": round(lower_y, 6),
        "reversible_4d_y_upper_mm": round(upper_y, 6),
        "reversible_4d_y_band_width_mm": round(upper_y - lower_y, 6),
        "nearest_principal_hole_vertical_offset_mm": round(vertical_offset_mm, 6),
        "principal_grain_z_component": round(ny, 6),
        "nearest_principal_hole_grain_ray_mm": round(vertical_offset_mm / ny, 6),
        "softwood_loaded_end_minimum_mm": round(end_minimum_mm, 6),
        "principal_end_square_to_grain": abs(ny - 1) < 1e-6,
        "end_distance_classified": False,
        "angle_placement_verified": False,
        "drilling_released": False,
    }


def _retained_axis_intersections(
    bores: tuple[cq.Solid, ...], *, purchased_panel_length: bool = False
) -> tuple[dict[str, int], list[str]]:
    retained = []
    inspected_counts = {"hillman_panel": 0, "bolt_clearance": 0}
    with AXES.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["shop_opening_kind"] not in inspected_counts:
                continue
            inspected_counts[row["shop_opening_kind"]] += 1
            start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
            direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
            occupied = cq.Solid.makeCylinder(
                float(row["occupied_diameter_mm"]) / 2,
                float(row["shop_purchased_length_mm"])
                if purchased_panel_length
                and row["shop_opening_kind"] == "hillman_panel"
                else float(row["occupied_length_mm"]),
                start,
                direction,
            )
            if any(bore.intersect(occupied).Volume() > 1e-6 for bore in bores):
                retained.append(row["name"])
    if inspected_counts != {"hillman_panel": 66, "bolt_clearance": 12}:
        raise ValueError("Frozen retained-axis inventory changed")
    return inspected_counts, retained


def screen_retained_axis_conflicts(
    row_y_mm: float, *, purchased_panel_length: bool = False
) -> dict[str, object]:
    """Intersect nominal bores with retained axes, not installed hardware stacks."""
    trial = screen_center_fit("short", row_y_mm)
    x = float(trial["contact_x_mm"])
    z = float(trial["contact_z_mm"])
    radius = float(trial["nominal_bore_diameter_mm"]) / 2
    bores = tuple(
        cq.Solid.makeCylinder(
            radius, 38.1, cq.Vector(x, row_y_mm, z + offset * 25.4), cq.Vector(1, 0, 0)
        )
        for offset in trial["vertical_hole_offsets_from_bend_in"]
    ) + tuple(
        cq.Solid.makeCylinder(
            radius, 38.1, cq.Vector(x - offset * 25.4, row_y_mm, z), cq.Vector(0, 0, -1)
        )
        for offset in trial["horizontal_hole_offsets_from_bend_in"]
    )
    inspected_counts, retained = _retained_axis_intersections(
        bores, purchased_panel_length=purchased_panel_length
    )
    return {
        "station": trial["station"],
        "orientation": "short_vertical",
        "trial_row_y_mm": round(row_y_mm, 6),
        "source_axes": str(AXES.relative_to(ROOT)),
        "retained_axis_types": ["hillman_panel", "bolt_clearance"],
        "retained_axes_inspected": inspected_counts,
        "trial_bore_count": len(bores),
        "intersecting_retained_axis_ids": retained,
        "nominal_axis_conflicts_found": bool(retained),
        "limitations": "Nominal centerline bore/occupied-axis screen only; not washers, plates, tools, tolerances, adjacent replacement connectors, or bolt capacity.",
    }


def screen_opposed_center_fit(row_y_mm: float) -> dict[str, object]:
    """Test shared header holes for opposed short-vertical AB205 trials."""
    trial = screen_center_fit("short", row_y_mm)
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    post = parts["base_post_center_left"]
    x = float(trial["contact_x_mm"])
    z = post.BoundingBox().zmax
    radius = float(trial["nominal_bore_diameter_mm"]) / 2
    vertical_offsets = trial["vertical_hole_offsets_from_bend_in"]
    post_bores = tuple(
        cq.Solid.makeCylinder(
            radius, 38.1, cq.Vector(x, row_y_mm, z - offset * 25.4), cq.Vector(1, 0, 0)
        )
        for offset in vertical_offsets
    )
    post_fractions = [
        post.intersect(bore).Volume() / (pi * radius**2 * 38.1) for bore in post_bores
    ]
    all_axes = screen_retained_axis_conflicts(row_y_mm)
    _, post_axis_hits = _retained_axis_intersections(post_bores)
    purchased_top_hits = screen_retained_axis_conflicts(
        row_y_mm, purchased_panel_length=True
    )["intersecting_retained_axis_ids"]
    _, purchased_post_hits = _retained_axis_intersections(
        post_bores, purchased_panel_length=True
    )
    post_bounds = post.BoundingBox()
    four_d = 4 * float(trial["bolt_diameter_mm"])
    post_edge_reserve = (
        min(row_y_mm - post_bounds.ymin, post_bounds.ymax - row_y_mm) - four_d
    )
    plate_width = 1.625 * 25.4
    plate_thickness = 0.25 * 25.4
    long_leg_length = 4.125 * 25.4
    short_leg_length = 3.5 * 25.4
    y0 = row_y_mm - plate_width / 2
    top_z = float(trial["contact_z_mm"])
    top_blocks = (
        cq.Solid.makeBox(
            long_leg_length,
            plate_width,
            plate_thickness,
            cq.Vector(x - long_leg_length, y0, top_z),
        ),
        cq.Solid.makeBox(
            plate_thickness,
            plate_width,
            short_leg_length,
            cq.Vector(x - plate_thickness, y0, top_z),
        ),
    )
    bottom_blocks = (
        cq.Solid.makeBox(
            long_leg_length,
            plate_width,
            plate_thickness,
            cq.Vector(x - long_leg_length, y0, z - plate_thickness),
        ),
        cq.Solid.makeBox(
            plate_thickness,
            plate_width,
            short_leg_length,
            cq.Vector(x - plate_thickness, y0, z - short_leg_length),
        ),
    )
    plate_intersections = sorted(
        part.name
        for part in frame.uncut_wood_parts()
        if any(
            block.intersect(part.shape).Volume() > 1e-6
            for block in top_blocks + bottom_blocks
        )
    )
    return {
        "station_pair": [
            "clip_split_base_center_left",
            "clip_split_header_center_left",
        ],
        "proposal": "one top and one underside AB205, each short leg vertical; two common through-header axes on matching horizontal long legs",
        "trial_row_y_mm": round(row_y_mm, 6),
        "top_header_hole_x_mm": [
            round(x - offset * 25.4, 6)
            for offset in trial["horizontal_hole_offsets_from_bend_in"]
        ],
        "underside_header_hole_x_mm": [
            round(x - offset * 25.4, 6)
            for offset in trial["horizontal_hole_offsets_from_bend_in"]
        ],
        "shared_header_hole_count": 2,
        "unique_wood_bore_axes": 6,
        "post_bore_full_section_fractions": [
            round(value, 6) for value in post_fractions
        ],
        "post_conditional_reversible_4d_edge_reserve_mm": round(post_edge_reserve, 6),
        "retained_axis_conflicts_for_six_unique_bores": sorted(
            set(all_axes["intersecting_retained_axis_ids"]) | set(post_axis_hits)
        ),
        "purchased_panel_length_axis_conflicts_for_six_unique_bores": sorted(
            set(purchased_top_hits) | set(purchased_post_hits)
        ),
        "nominal_angle_outer_envelope_intersecting_raw_wood_parts": plate_intersections,
        "nominal_angle_envelope_source": "ABB AB205 4-1/8 in height, 3-1/2 in base, 1-5/8 in width, 1/4 in thickness; ideal square-corner boxes, no bend radius or tolerances",
        "end_distance_classified": False,
        "shared_fastener_stack_defined": False,
        "installed_angle_and_tool_clearance_verified": False,
        "drilling_released": False,
    }
