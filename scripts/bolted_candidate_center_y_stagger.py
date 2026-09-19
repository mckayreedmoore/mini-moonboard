"""Non-selected AB205 center-header underside row-Y geometry screen.

The top short-vertical trial and every wood member stay at their raw CAD pose.
Nominal cylinders and ideal square-corner steel envelopes are diagnostics only.
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
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
CENTER_RECORD = ROOT / "docs/bolted-candidate-prototypes/ab205-center-fit.json"
BOLT_D_MM = 12.7
BORE_D_MM = 14.2875
WOOD_BEARING_MM = 38.1
LONG_OFFSETS_MM = (1.4375 * 25.4, 3.3125 * 25.4)
SHORT_OFFSETS_MM = (0.8125 * 25.4, 2.6875 * 25.4)
PLATE_WIDTH_MM = 1.625 * 25.4
PLATE_THICKNESS_MM = 6.35


def _bore(
    start: tuple[float, float, float], direction: tuple[int, int, int]
) -> cq.Solid:
    return cq.Solid.makeCylinder(
        BORE_D_MM / 2, WOOD_BEARING_MM, cq.Vector(*start), cq.Vector(*direction)
    )


def _fraction(wood: cq.Shape, bore: cq.Solid) -> float:
    return round(wood.intersect(bore).Volume() / bore.Volume(), 6)


def _retained_axes() -> tuple[dict[str, int], list[tuple[str, cq.Solid]]]:
    counts = {"hillman_panel": 0, "bolt_clearance": 0}
    occupied = []
    with AXES.open(newline="") as handle:
        for row in csv.DictReader(handle):
            kind = row["shop_opening_kind"]
            if kind not in counts:
                continue
            counts[kind] += 1
            start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
            direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
            solid = cq.Solid.makeCylinder(
                float(row["occupied_diameter_mm"]) / 2,
                float(row["occupied_length_mm"]),
                start,
                direction,
            )
            occupied.append((row["name"], solid))
    if counts != {"hillman_panel": 66, "bolt_clearance": 12}:
        raise ValueError("Frozen retained-axis inventory changed")
    return counts, occupied


def _category(distance: float, minimum: float) -> str:
    if distance < 1e-6:
        return "coincident_axes"
    if distance + 1e-6 >= minimum:
        return "at_or_above_conditional_minimum"
    return "below_conditional_minimum"


def _angle_blocks(
    x: float, y: float, z: float, sign: int, *, above: bool
) -> tuple[cq.Solid, ...]:
    y0 = y - PLATE_WIDTH_MM / 2
    horizontal_z = z if above else z - PLATE_THICKNESS_MM
    vertical_z = z if above else z - 3.5 * 25.4
    return (
        cq.Solid.makeBox(
            4.125 * 25.4,
            PLATE_WIDTH_MM,
            PLATE_THICKNESS_MM,
            cq.Vector(min(x, x + sign * 4.125 * 25.4), y0, horizontal_z),
        ),
        cq.Solid.makeBox(
            PLATE_THICKNESS_MM,
            PLATE_WIDTH_MM,
            3.5 * 25.4,
            cq.Vector(min(x, x + sign * PLATE_THICKNESS_MM), y0, vertical_z),
        ),
    )


def screen_center_y_stagger(
    underside_rows_mm: tuple[float, ...] | None = None,
) -> dict[str, object]:
    """Sample underside Y in the raw post's conditional reversible 4D band."""
    record = json.loads(CENTER_RECORD.read_text())
    top_y = float(record["short_vertical_midband_trial"]["row_y_mm"])
    top_trial = screen_center_fit("short", top_y)
    if not (
        top_trial["reversible_4d_y_lower_mm"]
        <= top_y
        <= top_trial["reversible_4d_y_upper_mm"]
    ):
        raise ValueError("Recorded top row left its conditional 4D band")
    raw = {part.name: part.shape for part in frame.uncut_wood_parts()}
    header = raw["base_header"]
    post = raw["base_post_center_left"]
    header_bounds = header.BoundingBox()
    post_bounds = post.BoundingBox()
    lower = max(header_bounds.ymin, post_bounds.ymin) + 4 * BOLT_D_MM
    upper = min(header_bounds.ymax, post_bounds.ymax) - 4 * BOLT_D_MM
    if lower > upper:
        raise ValueError("Raw post has no conditional 4D row band")
    if underside_rows_mm is None:
        rows = (lower, (lower + top_y) / 2, top_y, (top_y + upper) / 2, upper)
    else:
        rows = underside_rows_mm
    if not rows or any(
        not isfinite(y) or y < lower - 1e-6 or y > upper + 1e-6 for y in rows
    ):
        raise ValueError("Underside row must stay within the raw-post 4D band")
    counts, retained = _retained_axes()
    # The lesser wood bearing length in Table 12.5.1D is conditional here.
    parallel_min = 1.5 * BOLT_D_MM
    perpendicular_min = (5 * WOOD_BEARING_MM + 10 * BOLT_D_MM) / 8
    samples = []
    for row_y in rows:
        sides = []
        for side, sign in (("left", -1), ("right", 1)):
            principal = raw[f"base_principal_center_{side}"]
            post = raw[f"base_post_center_{side}"]
            x = (
                principal.BoundingBox().xmin
                if sign < 0
                else principal.BoundingBox().xmax
            )
            post_x = post.BoundingBox().xmin if sign < 0 else post.BoundingBox().xmax
            top_xs = [x + sign * offset for offset in LONG_OFFSETS_MM]
            underside_xs = [post_x + sign * offset for offset in LONG_OFFSETS_MM]
            top_bores = [
                _bore((hole_x, top_y, header_bounds.zmax), (0, 0, -1))
                for hole_x in top_xs
            ]
            underside_bores = [
                _bore((hole_x, row_y, header_bounds.zmin), (0, 0, 1))
                for hole_x in underside_xs
            ]
            post_bores = [
                _bore((post_x, row_y, header_bounds.zmin - offset), (-sign, 0, 0))
                for offset in SHORT_OFFSETS_MM
            ]
            top_principal_bores = [
                _bore((x, top_y, header_bounds.zmax + offset), (-sign, 0, 0))
                for offset in SHORT_OFFSETS_MM
            ]
            all_bores = top_bores + underside_bores + post_bores + top_principal_bores
            hits = sorted(
                name
                for name, occupied in retained
                if any(bore.intersect(occupied).Volume() > 1e-6 for bore in all_bores)
            )
            overlaps = [
                a.intersect(b).Volume() for a in top_bores for b in underside_bores
            ]
            distance = min(
                ((ax - bx) ** 2 + (top_y - row_y) ** 2) ** 0.5
                for ax in top_xs
                for bx in underside_xs
            )
            top_blocks = _angle_blocks(x, top_y, header_bounds.zmax, sign, above=True)
            underside_blocks = _angle_blocks(
                post_x, row_y, header_bounds.zmin, sign, above=False
            )
            body_overlap = sum(
                a.intersect(b).Volume() for a in top_blocks for b in underside_blocks
            )
            sides.append(
                {
                    "side": side,
                    "top_header_x_mm": [round(value, 6) for value in top_xs],
                    "underside_header_x_mm": [
                        round(value, 6) for value in underside_xs
                    ],
                    "minimum_axis_distance_mm": round(distance, 6),
                    "minimum_bore_web_mm": round(distance - BORE_D_MM, 6),
                    "overlapping_header_bore_pairs": sum(
                        volume > 1e-6 for volume in overlaps
                    ),
                    "maximum_header_bore_overlap_mm3": round(max(overlaps), 6),
                    "top_principal_bore_full_section_fractions": [
                        _fraction(principal, bore) for bore in top_principal_bores
                    ],
                    "top_header_bore_full_section_fractions": [
                        _fraction(header, bore) for bore in top_bores
                    ],
                    "post_bore_full_section_fractions": [
                        _fraction(post, bore) for bore in post_bores
                    ],
                    "header_bore_full_section_fractions": [
                        _fraction(header, bore) for bore in underside_bores
                    ],
                    "retained_axis_hits": hits,
                    "parallel_row_spacing_category": _category(distance, parallel_min),
                    "perpendicular_row_spacing_category": _category(
                        distance, perpendicular_min
                    ),
                    "angle_body_overlap_mm3": round(body_overlap, 6),
                    "angle_bodies_on_opposite_header_faces": (
                        top_blocks[0].BoundingBox().zmin >= header_bounds.zmax - 1e-6
                        and underside_blocks[0].BoundingBox().zmax
                        <= header_bounds.zmin + 1e-6
                    ),
                    "nds_row_accepted": False,
                }
            )
        samples.append({"underside_row_y_mm": round(row_y, 6), "sides": sides})
    return {
        "status": "geometry_screen_only",
        "top_row_y_mm": round(top_y, 6),
        "post_4d_y_band_mm": [round(lower, 6), round(upper, 6)],
        "physical_kicker_width_option": floor_flush_width.KERF_RIGHT,
        "retained_axis_counts": counts,
        "table_12_5_1d_conditional_minimum_mm": {
            "parallel": parallel_min,
            "perpendicular": perpendicular_min,
        },
        "maximum_possible_y_stagger_mm": round(max(top_y - lower, upper - top_y), 6),
        "parallel_minimum_reachable_in_band": (
            max(top_y - lower, upper - top_y) >= parallel_min
        ),
        "perpendicular_minimum_reachable_in_band": (
            max(top_y - lower, upper - top_y) >= perpendicular_min
        ),
        "table_12_5_1d_basis": "2024 NDS Table 12.5.1D; D=12.7 mm; assumed lesser wood bearing length=38.1 mm (l/D=3). Direction and member classification unverified.",
        "selected_row_y_mm": None,
        "samples": samples,
        "limits": "Nominal raw-wood and retained-axis geometry only. Angle blocks omit bend radii, hardware, washers, tolerance and access. No NDS row acceptance, full rating or drilling release.",
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen_center_y_stagger(), indent=2))
