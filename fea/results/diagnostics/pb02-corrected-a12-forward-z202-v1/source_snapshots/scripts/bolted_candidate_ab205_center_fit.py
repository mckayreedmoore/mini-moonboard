"""Nominal AB205 holes on the current center butt; no connector approval."""

import csv
from math import hypot, isfinite, pi
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


def _grain_ray_to_face_boundary(
    face: cq.Face, y_mm: float, z_mm: float, slope_dy_dz: float
) -> tuple[float, float, float]:
    """Return the first actual polygon-edge hit opposite the member's grain axis.

    This is a geometric diagnostic, not the NDS square-cut end distance.
    """
    gy = slope_dy_dz / hypot(slope_dy_dz, 1)
    gz = 1 / hypot(slope_dy_dz, 1)
    hits = []
    for edge in face.Edges():
        vertices = edge.Vertices()
        if len(vertices) != 2:
            continue
        a, b = (vertex.Center() for vertex in vertices)
        ey, ez = b.y - a.y, b.z - a.z
        denominator = gy * ez - gz * ey
        if abs(denominator) < 1e-9:
            continue
        wy, wz = y_mm - a.y, z_mm - a.z
        distance = (wy * ez - wz * ey) / denominator
        fraction = -(wy * gz - wz * gy) / denominator
        if distance > 1e-7 and -1e-7 <= fraction <= 1 + 1e-7:
            hits.append((distance, y_mm - distance * gy, z_mm - distance * gz))
    if not hits:
        raise ValueError("Grain ray did not hit the principal broad-face boundary")
    return min(hits)


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
    grain_ray, hit_y, hit_z = _grain_ray_to_face_boundary(
        face, y, vertical_z_mm[0], lines[0][2]
    )
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
        "nearest_principal_hole_grain_ray_mm": round(grain_ray, 6),
        "nearest_principal_hole_grain_ray_hit_y_mm": round(hit_y, 6),
        "nearest_principal_hole_grain_ray_hit_z_mm": round(hit_z, 6),
        "softwood_loaded_end_minimum_mm": round(end_minimum_mm, 6),
        "principal_end_square_to_grain": abs(ny - 1) < 1e-6,
        "end_distance_classified": False,
        "angle_placement_verified": False,
        "drilling_released": False,
    }


def screen_reversible_row_tolerance(
    vertical_leg: Literal["long", "short"], lateral_allowance_mm: float
) -> dict[str, object]:
    """Shrink the conditional two-edge 4D row band by a supplied axis allowance.

    The allowance must include all relevant row-position error in the local Y
    direction. This does not establish actual product or shop tolerances, an
    oblique-end rule, or a complete connection geometry check.
    """
    if (
        isinstance(lateral_allowance_mm, bool)
        or not isinstance(lateral_allowance_mm, (int, float))
        or not isfinite(lateral_allowance_mm)
        or lateral_allowance_mm < 0
    ):
        raise ValueError("lateral allowance must be finite and nonnegative")
    nominal = screen_center_fit(vertical_leg)
    lower = float(nominal["reversible_4d_y_lower_mm"]) + lateral_allowance_mm
    upper = float(nominal["reversible_4d_y_upper_mm"]) - lateral_allowance_mm
    return {
        "vertical_leg": vertical_leg,
        "lateral_allowance_mm": lateral_allowance_mm,
        "maximum_symmetric_allowance_mm": round(
            float(nominal["reversible_4d_y_band_width_mm"]) / 2, 6
        ),
        "allowance_adjusted_lower_y_mm": round(lower, 6),
        "allowance_adjusted_upper_y_mm": round(upper, 6),
        "allowance_adjusted_window_width_mm": round(upper - lower, 6),
        "nominal_window_exists": lower <= upper,
        "end_distance_classified": False,
        "drilling_released": False,
    }


def screen_oblique_end_ray_filter() -> dict[str, object]:
    """Find a necessary factory-hole offset under a stated grain-ray proxy.

    The 2024 NDS bolt end-distance definition is for a square-cut end. This
    calculation is deliberately not an NDS pass/fail rule for the oblique cut.
    """
    short = screen_center_fit("short")
    long = screen_center_fit("long")
    grain_z = float(short["principal_grain_z_component"])
    required_ray = float(short["softwood_loaded_end_minimum_mm"])
    offset = required_ray * grain_z
    if abs(float(short["nearest_principal_hole_grain_ray_mm"]) * grain_z
           - float(short["nearest_principal_hole_vertical_offset_mm"])) > 0.001:
        raise ValueError("Current oblique end is not the expected horizontal cut")
    return {
        "geometry": "fixed left-center principal; AB205 bend flush with header top",
        "reference": "2024 NDS Table 12.5.1A 3.5D reduced-value softwood tension threshold",
        "reference_applies_directly_to_oblique_cut": False,
        "proxy": "grain-parallel ray to the actual oblique cut, for a conservative factory-pattern search only",
        "minimum_proxy_ray_mm": round(required_ray, 6),
        "minimum_factory_near_hole_vertical_offset_from_bend_mm": round(offset, 6),
        "minimum_factory_near_hole_vertical_offset_from_bend_in": round(offset / 25.4, 6),
        "short_vertical_near_hole_offset_mm": short["nearest_principal_hole_vertical_offset_mm"],
        "short_vertical_required_offset_gain_mm": round(
            offset - float(short["nearest_principal_hole_vertical_offset_mm"]), 6
        ),
        "short_vertical_ray_mm": short["nearest_principal_hole_grain_ray_mm"],
        "long_vertical_ray_mm": long["nearest_principal_hole_grain_ray_mm"],
        "long_vertical_conditional_4d_row_band_mm": long["reversible_4d_y_band_width_mm"],
        "end_distance_classified": False,
        "connector_selected": False,
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
            if row["shop_opening_kind"] == "hillman_panel" and abs(
                float(row["shop_purchased_length_mm"]) - 63.5
            ) > 1e-6:
                raise ValueError("Retained panel screw purchased length changed")
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
        "panel_screw_obstacle_basis": (
            "mixed_purchased_length_legacy_diameter_sensitivity"
            if purchased_panel_length
            else "legacy_analysis_length_and_diameter"
        ),
        "physical_panel_screw_clearance_status": "unresolved_external_envelope",
        "limitations": "Nominal centerline bore/occupied-axis screen only. The purchased-length option mixes 63.5 mm with an unsupported legacy screw diameter; neither option verifies physical screw clearance. Not washers, plates, tools, tolerances, adjacent replacement connectors, or bolt capacity.",
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
        "shared_header_bolt_stack_class": "two steel flanges around one wood header; potentially unequal opposed actions",
        "two_member_single_shear_method_directly_applicable_to_shared_header_bolts": False,
        "unique_wood_bore_axes": 6,
        "post_bore_full_section_fractions": [
            round(value, 6) for value in post_fractions
        ],
        "post_conditional_reversible_4d_edge_reserve_mm": round(post_edge_reserve, 6),
        "retained_axis_conflicts_for_six_unique_bores": sorted(
            set(all_axes["intersecting_retained_axis_ids"]) | set(post_axis_hits)
        ),
        "mixed_purchased_length_legacy_diameter_axis_conflicts_for_six_unique_bores": sorted(
            set(purchased_top_hits) | set(purchased_post_hits)
        ),
        "physical_panel_screw_clearance_status": "unresolved_external_envelope",
        "nominal_angle_outer_envelope_intersecting_raw_wood_parts": plate_intersections,
        "nominal_angle_envelope_source": "ABB AB205 4-1/8 in height, 3-1/2 in base, 1-5/8 in width, 1/4 in thickness; ideal square-corner boxes, no bend radius or tolerances",
        "end_distance_classified": False,
        "shared_fastener_stack_defined": False,
        "installed_angle_and_tool_clearance_verified": False,
        "drilling_released": False,
    }


def screen_opposed_center_washer_envelope(row_y_mm: float) -> dict[str, object]:
    """Screen illustrative retail washer solids on the two shared header bolts.

    This tests only the washer's external cylindrical envelope. It does not
    select a washer grade or establish nut, head, tool, shank, or bearing fit.
    """
    trial = screen_opposed_center_fit(row_y_mm)
    parts = frame.uncut_wood_parts()
    header = next(part.shape for part in parts if part.name == "base_header")
    bounds = header.BoundingBox()
    flange_thickness_mm = 0.25 * 25.4
    flange_width_mm = 1.625 * 25.4
    washer_diameter_mm = 1.375 * 25.4
    washer_thickness_mm = 0.125 * 25.4
    radius = washer_diameter_mm / 2
    x_values = trial["top_header_hole_x_mm"]
    top_z = bounds.zmax + flange_thickness_mm
    bottom_z = bounds.zmin - flange_thickness_mm - washer_thickness_mm
    washers = tuple(
        cq.Solid.makeCylinder(
            radius, washer_thickness_mm, cq.Vector(x, row_y_mm, z), cq.Vector(0, 0, 1)
        )
        for x in x_values
        for z in (top_z, bottom_z)
    )
    wood_hits = sorted({
        part.name for part in parts
        if any(washer.intersect(part.shape).Volume() > 1e-6 for washer in washers)
    })
    _, retained_hits = _retained_axis_intersections(washers)
    _, purchased_hits = _retained_axis_intersections(
        washers, purchased_panel_length=True
    )
    pitch = abs(x_values[1] - x_values[0])
    return {
        "station_pair": trial["station_pair"],
        "trial_row_y_mm": round(row_y_mm, 6),
        "illustrative_retail_washer": "Lowe's Hillman 270067; 1/2-inch nominal, 1-3/8-inch OD, 1/8-inch thick",
        "washer_source": "https://www.lowes.com/pd/Hillman-1-Count-x-1-37-in-Zinc-Plated-Standard-SAE-Flat-Washer/3058563",
        "washer_outer_diameter_mm": round(washer_diameter_mm, 6),
        "washer_thickness_mm": round(washer_thickness_mm, 6),
        "shared_header_wood_plus_two_flange_grip_mm": round(
            bounds.zlen + 2 * flange_thickness_mm, 6
        ),
        "wood_plus_flange_plus_two_washer_stack_mm": round(
            bounds.zlen + 2 * flange_thickness_mm + 2 * washer_thickness_mm, 6
        ),
        "two_washer_axis_pitch_mm": round(pitch, 6),
        "washer_to_washer_nominal_clearance_mm": round(pitch - washer_diameter_mm, 6),
        "washer_to_angle_side_nominal_margin_mm": round(
            (flange_width_mm - washer_diameter_mm) / 2, 6
        ),
        "washer_envelope_intersecting_raw_parts": wood_hits,
        "retained_axis_intersections": retained_hits,
        "purchased_length_mixed_axis_intersections": purchased_hits,
        "washer_strength_verified": False,
        "nut_and_tool_envelope_verified": False,
        "actual_delivered_hardware_verified": False,
        "end_distance_classified": False,
        "drilling_released": False,
    }
