"""Bounded post-only AB205 geometry screen on the raw floor-flush CAD.

The principal and its top angle remain fixed. No offset or drilling is selected.
"""

import csv
import json
from math import isfinite
from pathlib import Path

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as frame
from mini_moonboard import floor_flush_width
from scripts.bolted_candidate_ab205_center_fit import screen_center_fit

ROOT = Path(__file__).resolve().parents[1]
KERF_AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
OFFICIAL_AXES = ROOT / "docs/floor-flush-construction/connection-axes.csv"
BORE_DIAMETER_MM = 14.2875
BORE_RADIUS_MM = BORE_DIAMETER_MM / 2
NOMINAL_BOLT_DIAMETER_MM = 12.7
WOOD_DEPTH_MM = 38.1
SHORT_OFFSETS_MM = (0.8125 * 25.4, 2.6875 * 25.4)
LONG_OFFSETS_MM = (1.4375 * 25.4, 3.3125 * 25.4)
_AXIS_GEOMETRY_FIELDS = (
    "kind",
    "first_member",
    "second_member",
    "start_x_mm",
    "start_y_mm",
    "start_z_mm",
    "direction_x",
    "direction_y",
    "direction_z",
    "modeled_length_mm",
    "modeled_diameter_mm",
    "occupied_length_mm",
    "occupied_diameter_mm",
    "shop_opening_kind",
    "shop_finished_opening_min_mm",
    "shop_finished_opening_max_mm",
)


def _same_axis_geometry(
    left: list[dict[str, str]], right: list[dict[str, str]]
) -> bool:
    """Compare axis identity and geometry, excluding packet-specific prose."""

    def keyed(rows: list[dict[str, str]]) -> dict[str, tuple[str, ...]]:
        return {
            row["name"]: tuple(row[field] for field in _AXIS_GEOMETRY_FIELDS)
            for row in rows
        }

    left_by_name = keyed(left)
    right_by_name = keyed(right)
    return (
        len(left_by_name) == len(left)
        and len(right_by_name) == len(right)
        and left_by_name == right_by_name
    )


def fixed_pattern_header_min_pair_spacing_mm(outward_shift_mm: float) -> float:
    """Minimum distance across all opposed factory axes, ignoring timber fit."""
    return min(
        abs(top - (under + outward_shift_mm))
        for top in LONG_OFFSETS_MM
        for under in LONG_OFFSETS_MM
    )


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _cylinder(row: dict[str, str]) -> cq.Solid:
    start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
    direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
    return cq.Solid.makeCylinder(
        float(row["occupied_diameter_mm"]) / 2,
        float(row["occupied_length_mm"]),
        start,
        direction,
    )


def _fraction(wood: cq.Shape, bore: cq.Solid) -> float:
    return round(wood.intersect(bore).Volume() / bore.Volume(), 6)


def screen_center_post_offsets(
    offsets_mm: tuple[float, ...] = (0, 5, 10, 15),
) -> dict[str, object]:
    """Compare specified outward shifts of the two posts only, in millimeters."""
    if any(
        not isfinite(offset) or offset not in (0, 5, 10, 15) for offset in offsets_mm
    ):
        raise ValueError("Only the bounded 0/5/10/15 mm offsets are in scope")
    trial = screen_center_fit("short")
    row_y = (trial["reversible_4d_y_lower_mm"] + trial["reversible_4d_y_upper_mm"]) / 2
    raw = {part.name: part.shape for part in frame.uncut_wood_parts()}
    physical = {
        part.name: part.shape
        for part in floor_flush_width.variant(
            floor_flush_width.KERF_RIGHT
        ).uncut_wood_parts()
    }
    header = raw["base_header"]
    header_z = header.BoundingBox().zmax
    post_z = header.BoundingBox().zmin
    kerf_rows = _rows(KERF_AXES)
    official_rows = _rows(OFFICIAL_AXES)
    retained = [
        row
        for row in kerf_rows
        if row["shop_opening_kind"] in ("hillman_panel", "bolt_clearance")
    ]
    counts = {
        kind: sum(row["shop_opening_kind"] == kind for row in retained)
        for kind in ("hillman_panel", "bolt_clearance")
    }
    if counts != {"hillman_panel": 66, "bolt_clearance": 12}:
        raise ValueError("Frozen retained-axis inventory changed")
    post_names = {f"base_post_center_{side}" for side in ("left", "right")}
    relevant = lambda rows: [
        row
        for row in rows
        if row["shop_opening_kind"] == "hillman_panel"
        and row["second_member"] in post_names
    ]
    post_rows = relevant(kerf_rows)
    if len(post_rows) != 4 or not _same_axis_geometry(
        post_rows, relevant(official_rows)
    ):
        raise ValueError("Kerf-right and official post panel axes diverged")
    frozen_kicker_axis_inner_edge_reserves = []
    modeled_occupied_inner_edge_reserves = []
    for screw in post_rows:
        bounds = raw[screw["second_member"]].BoundingBox()
        center_x = float(screw["start_x_mm"])
        radius = float(screw["occupied_diameter_mm"]) / 2
        axis_reserve = (
            bounds.xmax - center_x
            if screw["second_member"].endswith("_left")
            else center_x - bounds.xmin
        )
        frozen_kicker_axis_inner_edge_reserves.append(axis_reserve)
        modeled_occupied_inner_edge_reserves.append(axis_reserve - radius)
    max_shift_with_axis_center = min(frozen_kicker_axis_inner_edge_reserves)
    max_shift_with_modeled_occupancy = min(modeled_occupied_inner_edge_reserves)
    if max_shift_with_modeled_occupancy <= 0:
        raise ValueError(
            "Modeled kicker screw occupancy is already outside its raw post"
        )
    distinct_bolt_shift = 3 * NOMINAL_BOLT_DIAMETER_MM
    full_pair_shift = LONG_OFFSETS_MM[1] - LONG_OFFSETS_MM[0] + distinct_bolt_shift
    if (
        fixed_pattern_header_min_pair_spacing_mm(full_pair_shift)
        < distinct_bolt_shift - 1e-6
    ):
        raise ValueError("Fixed-pattern full-pair spacing threshold is inconsistent")
    retained_solids = [
        (row["name"], row["shop_opening_kind"], _cylinder(row)) for row in retained
    ]
    samples = []
    for offset in offsets_mm:
        sides = []
        for side, sign in (("left", -1), ("right", 1)):
            name = f"base_post_center_{side}"
            shifted = raw[name].translate((sign * offset, 0, 0))
            principal = raw[f"base_principal_center_{side}"]
            bend_x = (
                principal.BoundingBox().xmin
                if sign < 0
                else principal.BoundingBox().xmax
            )
            post_x = (
                shifted.BoundingBox().xmin if sign < 0 else shifted.BoundingBox().xmax
            )
            top_xs = [bend_x + sign * distance for distance in LONG_OFFSETS_MM]
            underside_xs = [post_x + sign * distance for distance in LONG_OFFSETS_MM]
            post_zs = [post_z - distance for distance in SHORT_OFFSETS_MM]
            post_bores = [
                cq.Solid.makeCylinder(
                    BORE_RADIUS_MM,
                    WOOD_DEPTH_MM,
                    cq.Vector(post_x, row_y, z),
                    cq.Vector(-sign, 0, 0),
                )
                for z in post_zs
            ]
            top_bores = [
                cq.Solid.makeCylinder(
                    BORE_RADIUS_MM,
                    WOOD_DEPTH_MM,
                    cq.Vector(x, row_y, header_z),
                    cq.Vector(0, 0, -1),
                )
                for x in top_xs
            ]
            underside_bores = [
                cq.Solid.makeCylinder(
                    BORE_RADIUS_MM,
                    WOOD_DEPTH_MM,
                    cq.Vector(x, row_y, post_z),
                    cq.Vector(0, 0, 1),
                )
                for x in underside_xs
            ]
            # Opposed header holes occupy the same raw header thickness.
            overlaps = [
                round(a.intersect(b).Volume(), 6)
                for a in top_bores
                for b in underside_bores
            ]
            spacing = min(abs(a - b) for a in top_xs for b in underside_xs)
            candidate_bores = post_bores + underside_bores
            bore_hits = sorted(
                {
                    axis_name
                    for axis_name, _, solid in retained_solids
                    if any(
                        bore.intersect(solid).Volume() > 1e-6
                        for bore in candidate_bores
                    )
                }
            )
            panel_hits = sorted(
                {
                    axis_name
                    for axis_name, kind, solid in retained_solids
                    if kind == "hillman_panel"
                    and any(
                        bore.intersect(solid).Volume() > 1e-6
                        for bore in candidate_bores
                    )
                }
            )
            supported_panel_axes = sorted(
                axis_name
                for axis_name, kind, solid in retained_solids
                if kind == "hillman_panel" and shifted.intersect(solid).Volume() > 1e-6
            )
            kicker = physical[f"kicker_{side}"]
            kicker_edge_x = (
                kicker.BoundingBox().xmax if sign < 0 else kicker.BoundingBox().xmin
            )
            post_inner_x = (
                shifted.BoundingBox().xmax if sign < 0 else shifted.BoundingBox().xmin
            )
            kicker_rows = [
                row
                for row in post_rows
                if row["second_member"] == name
                and row["first_member"] == f"kicker_{side}"
            ]
            if len(kicker_rows) != 2:
                raise ValueError("Frozen kicker screw inventory changed")
            kicker_engagement = []
            for screw in kicker_rows:
                occupied = _cylinder(screw)
                volume = shifted.intersect(occupied).Volume()
                center_x = float(screw["start_x_mm"])
                edge_material = (
                    min(
                        center_x - shifted.BoundingBox().xmin,
                        shifted.BoundingBox().xmax - center_x,
                    )
                    - float(screw["occupied_diameter_mm"]) / 2
                )
                kicker_engagement.append(
                    {
                        "axis_id": screw["name"],
                        "occupied_axis_intersection_mm3": round(volume, 6),
                        "modeled_occupied_axis_edge_reserve_mm": round(
                            edge_material, 6
                        ),
                        "occupied_axis_intersects_shifted_post": volume > 1e-6,
                        "modeled_occupied_axis_inside_post_width": edge_material > 0,
                    }
                )
            # Ideal square-corner AB205 boxes locate the underside angle only.
            y0 = row_y - 1.625 * 25.4 / 2
            angle_boxes = (
                cq.Solid.makeBox(
                    4.125 * 25.4,
                    1.625 * 25.4,
                    6.35,
                    cq.Vector(
                        min(post_x, post_x + sign * 4.125 * 25.4), y0, post_z - 6.35
                    ),
                ),
                cq.Solid.makeBox(
                    6.35,
                    1.625 * 25.4,
                    3.5 * 25.4,
                    cq.Vector(
                        post_x - 6.35 if sign < 0 else post_x, y0, post_z - 3.5 * 25.4
                    ),
                ),
            )
            angle_wood_hits = sorted(
                part_name
                for part_name, shape in raw.items()
                if part_name != name
                and any(box.intersect(shape).Volume() > 1e-6 for box in angle_boxes)
            )
            sides.append(
                {
                    "side": side,
                    "post_shift_x_mm": sign * offset,
                    "principal_x_bounds_mm": [
                        round(principal.BoundingBox().xmin, 6),
                        round(principal.BoundingBox().xmax, 6),
                    ],
                    "shifted_post_x_bounds_mm": [
                        round(shifted.BoundingBox().xmin, 6),
                        round(shifted.BoundingBox().xmax, 6),
                    ],
                    "top_header_x_mm": [round(x, 6) for x in top_xs],
                    "underside_header_x_mm": [round(x, 6) for x in underside_xs],
                    "underside_post_bolt_axes_x_y_z_mm": [
                        [round(post_x, 6), round(row_y, 6), round(z, 6)]
                        for z in post_zs
                    ],
                    "underside_angle_bend_x_y_z_mm": [
                        round(post_x, 6),
                        round(row_y, 6),
                        round(post_z, 6),
                    ],
                    "post_bore_full_section_fractions": [
                        _fraction(shifted, bore) for bore in post_bores
                    ],
                    "header_bore_full_section_fractions": [
                        _fraction(header, bore) for bore in underside_bores
                    ],
                    "minimum_top_underside_axis_spacing_mm": round(spacing, 6),
                    "conditional_separate_header_bolts_minimum_3d_mm": 3
                    * NOMINAL_BOLT_DIAMETER_MM,
                    "separate_header_bolt_spacing_screen": (
                        "shared_axis_not_this_check"
                        if offset == 0
                        else (
                            "meets_3d_minimum"
                            if spacing >= 3 * NOMINAL_BOLT_DIAMETER_MM
                            else "below_3d_minimum"
                        )
                    ),
                    "minimum_top_underside_bore_web_mm": round(
                        spacing - BORE_DIAMETER_MM, 6
                    ),
                    "overlapping_top_underside_bore_pairs": sum(
                        volume > 1e-6 for volume in overlaps
                    ),
                    "maximum_top_underside_bore_overlap_mm3": max(overlaps),
                    "coincident_header_axes": sum(
                        abs(a - b) < 1e-6 for a in top_xs for b in underside_xs
                    ),
                    "nominal_panel_axis_hits": panel_hits,
                    "retained_bore_axis_hits": bore_hits,
                    "panel_axes_intersecting_shifted_post": supported_panel_axes,
                    "kicker_interior_edge_x_mm": round(kicker_edge_x, 6),
                    "shifted_post_inner_edge_x_mm": round(post_inner_x, 6),
                    "kicker_interior_seam_overhang_mm": round(
                        abs(kicker_edge_x - post_inner_x), 6
                    ),
                    "kicker_seam_overhang_increase_from_raw_baseline_mm": offset,
                    "kicker_interior_edge_directly_supported_by_post": False,
                    "kicker_edge_support_verified": False,
                    "kicker_support_degraded_vs_baseline": offset > 0,
                    "kicker_screw_support_engagement": kicker_engagement,
                    "underside_angle_box_raw_wood_hits_except_shifted_post": angle_wood_hits,
                    "drilling_released": False,
                }
            )
        samples.append({"offset_mm": offset, "sides": sides})
    return {
        "status": "geometry_screen_only",
        "source_cad": "mini_moonboard.compact_floor_flush_frame.uncut_wood_parts()",
        "axis_sources": [
            str(KERF_AXES.relative_to(ROOT)),
            str(OFFICIAL_AXES.relative_to(ROOT)),
        ],
        "top_trial_row_y_mm": round(row_y, 6),
        "top_principal_and_angle_unchanged": True,
        "physical_kicker_width_option": floor_flush_width.KERF_RIGHT,
        "retained_axis_counts": counts,
        "kerf_official_relevant_panel_axes_identical": True,
        "fixed_pattern_offset_threshold": {
            "necessary_lower_bound_from_coincident_factory_pair_mm": round(
                distinct_bolt_shift, 6
            ),
            "cross_pair_spacing_at_that_lower_bound_mm": round(
                fixed_pattern_header_min_pair_spacing_mm(distinct_bolt_shift), 6
            ),
            "minimum_shift_for_all_distinct_header_pairs_3d_mm": round(
                full_pair_shift, 6
            ),
            "minimum_extra_factory_pattern_shift_at_axis_center_limit_mm": round(
                full_pair_shift - max_shift_with_axis_center, 6
            ),
            "axis_center_margin_at_assumed_post_shift_mm": 0,
            "different_factory_pattern_verified": False,
            "maximum_shift_before_frozen_kicker_screw_axis_reaches_post_edge_mm": round(
                max_shift_with_axis_center, 6
            ),
            "maximum_shift_before_modeled_screw_occupancy_reaches_post_edge_mm": round(
                max_shift_with_modeled_occupancy, 6
            ),
            "required_shift_exceeds_axis_center_limit_mm": round(
                distinct_bolt_shift - max_shift_with_axis_center, 6
            ),
            "simultaneous_nominal_3d_and_frozen_axis_engagement_possible": (
                distinct_bolt_shift < max_shift_with_axis_center
            ),
            "applies_to_other_factory_hole_patterns": False,
            "kicker_edge_support_verified": False,
        },
        "selected_offset_mm": None,
        "samples": samples,
        "spacing_source": "2024 AWC NDS Table 12.5.1B: 3D minimum for distinct fasteners in a row; x is header grain and both angle rows use the same y. This is a placement screen, not a joint capacity.",
        "missing_checks": [
            "loads",
            "access",
            "ratings",
            "bolt and washer stack",
            "angle tolerance and bend radius",
            "wood edge/end resistance",
            "kicker edge support and shifted support load path",
        ],
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen_center_post_offsets(), indent=2))
