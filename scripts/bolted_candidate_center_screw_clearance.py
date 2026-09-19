"""RS-2 nominal physical screw-clearance requirements; no drilling release.

Shafts are finite 63.5 mm centerline segments. Head checks use only the start
point; neither an unknown head nor a historical occupied cylinder is modeled.
"""

import csv
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mini_moonboard import floor_flush_width
from scripts.bolted_candidate_center_y_stagger import (
    BORE_D_MM,
    LONG_OFFSETS_MM,
    PLATE_THICKNESS_MM,
    SHORT_OFFSETS_MM,
    _angle_blocks,
)

AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
CENTER = ROOT / "docs/bolted-candidate-prototypes/ab205-center-fit.json"
STAGGER = ROOT / "docs/bolted-candidate-prototypes/center-y-stagger.json"
OUTPUT = ROOT / "docs/bolted-candidate-prototypes/center-screw-clearance-requirements.json"
PROTECTED = (
    "round_panel_lower_left_center_1",
    "round_kicker_left_center_1",
    "round_kicker_left_center_2",
    "kicker_header_left_1",
)
LENGTH_MM = 63.5
ROUND_DIGITS = 6


def _point(point):
    return cq.Vector(*point)


def _distance_segment_to_shape(start, end, shape):
    """Exact finite OCC edge-to-solid distance, including end-cap/tip effects."""
    return cq.Edge.makeLine(_point(start), _point(end)).distance(shape)


def _distance_point_to_shape(point, shape):
    return cq.Vertex.makeVertex(*point).distance(shape)


def _axis(start, direction, length):
    return tuple(start[i] + length * direction[i] for i in range(3))


def _f(value):
    return round(float(value), ROUND_DIGITS)


def _protected_screws():
    counts = {"hillman_panel": 0, "bolt_clearance": 0}
    selected = {}
    with AXES.open(newline="") as handle:
        for row in csv.DictReader(handle):
            kind = row["shop_opening_kind"]
            if kind in counts:
                counts[kind] += 1
            if row["name"] not in PROTECTED:
                continue
            if row["name"] in selected or kind != "hillman_panel":
                raise ValueError("Protected screw inventory changed")
            length = float(row["shop_purchased_length_mm"])
            if abs(length - LENGTH_MM) > 1e-6:
                raise ValueError("Protected purchased screw length changed")
            start = tuple(float(row[f"start_{a}_mm"]) for a in "xyz")
            direction = tuple(float(row[f"direction_{a}"]) for a in "xyz")
            if abs(sum(d * d for d in direction) - 1) > 1e-6:
                raise ValueError("Protected screw direction is not unit length")
            selected[row["name"]] = {
                "name": row["name"],
                "start_mm": [_f(v) for v in start],
                "direction": [_f(v) for v in direction],
                "tip_mm": [_f(v) for v in _axis(start, direction, length)],
                "purchased_centerline_length_mm": length,
            }
    if counts != {"hillman_panel": 66, "bolt_clearance": 12} or set(selected) != set(PROTECTED):
        raise ValueError("Frozen retained-axis inventory changed")
    return counts, [selected[name] for name in PROTECTED]


def _cylinder(start, direction, length):
    return cq.Solid.makeCylinder(BORE_D_MM / 2, length, _point(start), _point(direction))


def _drilled_angle_blocks(x, row_y, bend_z, above):
    """Return ideal angle legs with both nominal factory-pattern holes removed."""
    horizontal, vertical = _angle_blocks(x, row_y, bend_z, -1, above=above)
    for offset in LONG_OFFSETS_MM:
        z0 = bend_z if above else bend_z - PLATE_THICKNESS_MM
        horizontal = horizontal.cut(
            _cylinder((x - offset, row_y, z0), (0, 0, 1), PLATE_THICKNESS_MM)
        )
    for offset in SHORT_OFFSETS_MM:
        hole_z = bend_z + offset if above else bend_z - offset
        vertical = vertical.cut(
            _cylinder((x - PLATE_THICKNESS_MM, row_y, hole_z), (1, 0, 0), PLATE_THICKNESS_MM)
        )
    return horizontal, vertical


def _case(name, underside_y, top_y, raw, screws):
    header = raw["base_header"].BoundingBox()
    principal = raw["base_principal_center_left"].BoundingBox()
    post = raw["base_post_center_left"].BoundingBox()
    x = principal.xmin
    if abs(x - post.xmin) > 1e-6:
        raise ValueError("Left principal/post bend X no longer aligns")
    if abs(header.zmax - principal.zmin) > 1e-6 or abs(header.zmin - post.zmax) > 1e-6:
        raise ValueError("RS-2 raw contact geometry changed")
    shared = abs(top_y - underside_y) < 1e-6
    obstacles = []
    bores = []

    def add_bore(label, member, start, direction, length):
        shape = _cylinder(start, direction, length)
        obstacles.append((label, shape))
        bores.append({"id": label, "member": member, "start_mm": [_f(v) for v in start],
                      "direction": list(direction), "length_mm": _f(length),
                      "nominal_diameter_mm": BORE_D_MM})

    for index, offset in enumerate(LONG_OFFSETS_MM, 1):
        hole_x = x - offset
        add_bore(f"header_{index}_top" if not shared else f"header_{index}_shared",
                 "base_header", (hole_x, top_y, header.zmin), (0, 0, 1), header.zlen)
        if not shared:
            add_bore(f"header_{index}_underside", "base_header",
                     (hole_x, underside_y, header.zmin), (0, 0, 1), header.zlen)
    for face, row_y, bend_z, member in (
        ("top", top_y, header.zmax, "base_principal_center_left"),
        ("underside", underside_y, header.zmin, "base_post_center_left"),
    ):
        for index, offset in enumerate(SHORT_OFFSETS_MM, 1):
            hole_z = bend_z + offset if face == "top" else bend_z - offset
            add_bore(f"{face}_side_{index}", member,
                     (x, row_y, hole_z), (1, 0, 0), 38.1)

    bodies = []
    body_details = []
    for face, row_y, bend_z, above in (
        ("top", top_y, header.zmax, True),
        ("underside", underside_y, header.zmin, False),
    ):
        horizontal, vertical = _drilled_angle_blocks(x, row_y, bend_z, above)
        for leg, shape in (("horizontal", horizontal), ("vertical", vertical)):
            label = f"{face}_{leg}_steel"
            bodies.append((label, shape))
        body_details.extend(
            {"id": f"{face}_{leg}_steel",
             "horizontal_holes_subtracted": 2 if leg == "horizontal" else 0,
             "vertical_holes_subtracted": 2 if leg == "vertical" else 0,
             "nominal_hole_diameter_mm": BORE_D_MM}
            for leg in ("horizontal", "vertical")
        )

    def pairs(shapes, head):
        result = []
        for screw in screws:
            for label, shape in shapes:
                distance = (_distance_point_to_shape(screw["start_mm"], shape) if head
                            else _distance_segment_to_shape(screw["start_mm"], screw["tip_mm"], shape))
                item = {"screw": screw["name"], "obstacle": label,
                        "distance_mm": _f(distance)}
                if not head:
                    item["strict_raw_upper_bound_shaft_radius_mm"] = _f(distance)
                result.append(item)
        return result

    shaft_bore = pairs(obstacles, False)
    shaft_steel = pairs(bodies, False)
    head_bore = pairs(obstacles, True)
    head_steel = pairs(bodies, True)
    groups = {"shaft_to_bore": shaft_bore, "shaft_to_steel": shaft_steel,
              "head_start_to_bore": head_bore, "head_start_to_steel": head_steel}
    return {"case": name, "top_row_y_mm": top_y, "underside_row_y_mm": underside_y,
            "bores": bores, "steel_bodies": body_details,
            **{f"{key}_pairs": value for key, value in groups.items()},
            "closest_pairs": {key: min(value, key=lambda p: p["distance_mm"])
                              for key, value in groups.items()}}


def screen_center_screw_clearance():
    """Screen left RS-2 nominal bores and ideal steel bodies against four screws."""
    center = json.loads(CENTER.read_text())
    stagger = json.loads(STAGGER.read_text())
    top_y = float(center["short_vertical_midband_trial"]["row_y_mm"])
    underside_y = float(stagger["conditional_parallel_interval_midpoint_trial"]["underside_row_y_mm"])
    raw = {p.name: p.shape for p in floor_flush_width.variant(floor_flush_width.KERF_RIGHT).uncut_wood_parts()}
    counts, screws = _protected_screws()
    return {
        "status": "physical_clearance_requirement_screen_only",
        "width_option": floor_flush_width.KERF_RIGHT,
        "source_cad": "mini_moonboard.floor_flush_width.variant(KERF_RIGHT).uncut_wood_parts()",
        "source_axes": str(AXES.relative_to(ROOT)),
        "source_trial_rows": [str(CENTER.relative_to(ROOT)), str(STAGGER.relative_to(ROOT))],
        "retained_axis_counts": counts,
        "protected_screws": screws,
        "nominal_inputs_mm": {"ab205_short_leg": 88.9, "ab205_long_leg": 104.775,
                              "ab205_width": 41.275, "ab205_thickness": PLATE_THICKNESS_MM,
                              "wood_and_steel_hole_diameter": BORE_D_MM,
                              "short_leg_hole_offsets": list(SHORT_OFFSETS_MM),
                              "long_leg_hole_offsets": list(LONG_OFFSETS_MM)},
        "unknowns": {"actual_shaft_diameter_mm": None,
                     "shaft_diameter_tolerance_mm": None,
                     "installed_head_projection_mm": None,
                     "installed_head_radius_mm": None},
        "distance_interpretation": "Finite screw centerline to nominal bore volume or drilled ideal steel body. For a round shaft, its radius must be strictly less than the unrounded raw distance, before all tolerances and allowances; a zero distance has no admissible positive radius. Six-decimal radius fields are display bounds, not acceptance thresholds. Head distances are from the screw start point only; no head body or projection is modeled.",
        "cases": [_case("shared", top_y, top_y, raw, screws),
                  _case("stagger", underside_y, top_y, raw, screws)],
        "joint_selected": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(screen_center_screw_clearance(), indent=2) + "\n")
    print(OUTPUT)
