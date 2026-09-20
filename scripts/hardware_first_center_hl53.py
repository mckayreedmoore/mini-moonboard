"""Conditional HL53 center-assembly geometry screen, not a drilling plan."""

import argparse
import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
BORE = 14.2875  # nominal 9/16-in wood clearance for a 1/2-in bolt
POST_WIDTH = 139.7  # trial 6x solid, 5.5-in actual in X
HEADER_DEPTH = 88.9  # trial 4x solid, 3.5-in actual in Z
ANGLE_LENGTH = 63.5  # HL53 L, along Y in this trial
ANGLE_REACH = 146.05  # HL53 W1 and W2
FIRST_OFFSET = 50.8  # HL53 D3 from bend
SECOND_OFFSET = 114.3  # HL53 D3 + D4; across each flange
GAUGE7_NOMINAL = 4.55  # conceptual envelope only, not delivered gauge


def _cylinder(point, direction, length, diameter):
    return cq.Solid.makeCylinder(diameter / 2, length, cq.Vector(*point), direction)


def _wood():
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    hb = raw["base_header"].BoundingBox()
    rise = HEADER_DEPTH - hb.zlen
    cap = cq.Solid.makeBox(hb.xlen, hb.ylen, rise, cq.Vector(hb.xmin, hb.ymin, hb.zmax))
    raw["base_header"] = raw["base_header"].fuse(cap).clean()
    for side in ("left", "right"):
        for kind in ("principal", "post"):
            name = f"base_{kind}_center_{side}"
            original = raw[name]
            half_growth = (POST_WIDTH - original.BoundingBox().xlen) / 2
            # Overlap the translated extrusions: three copies would leave
            # 12.7-mm internal voids and falsely report missing wood.
            raw[name] = original.fuse(*(original.translate((offset, 0, 0))
                                        for offset in (-half_growth, -half_growth / 2,
                                                       half_growth / 2, half_growth))).clean()
        name = f"base_principal_center_{side}"
        p = raw[name]
        pb = p.BoundingBox()
        keep = cq.Solid.makeBox(pb.xlen + 2, pb.ylen + 2, pb.zmax - hb.zmax - rise + 2,
                                cq.Vector(pb.xmin - 1, pb.ymin - 1, hb.zmax + rise))
        raw[name] = p.intersect(keep).clean()
    return raw


def screen_hl53_center():
    """Screen one 6x-center/4x-header X-face pair with opposing Y stagger."""
    with AXES.open(newline="") as handle:
        panel = [r for r in csv.DictReader(handle) if r["shop_opening_kind"] == "hillman_panel"]
    if len(panel) != 66 or len({r["name"] for r in panel}) != 66:
        raise ValueError("expected 66 unique protected kerf-right screw axes")
    baseline = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    wood = _wood()
    hb = wood["base_header"].BoundingBox()
    # At most 76.2 mm apart while each 63.5-mm angle remains on the
    # original 139.7-mm Y face. Lower row is behind the kicker screw path.
    upper_y = hb.ymax - ANGLE_LENGTH / 2
    lower_y = hb.ymin + ANGLE_LENGTH / 2
    bores = []
    bore_solids = {}
    for side in ("left", "right"):
        center_x = -70 if side == "left" else 70
        for face in ("outer", "inner"):
            outward = -1 if side == "left" else 1
            surface_x = center_x + (outward if face == "outer" else -outward) * POST_WIDTH / 2
            into_member = -outward if face == "outer" else outward
            for level, y, bend_z, member, zsign in (
                ("upper", upper_y, hb.zmax, f"base_principal_center_{side}", 1),
                ("lower", lower_y, hb.zmin, f"base_post_center_{side}", -1),
            ):
                for index, offset in enumerate((FIRST_OFFSET, SECOND_OFFSET), 1):
                    key = f"{side}_{face}_{level}_{index}"
                    z = bend_z + zsign * offset
                    # The horizontal seat projects away from its vertical
                    # timber face; its factory hole cannot lie inside it.
                    x = surface_x - into_member * offset
                    v = _cylinder((center_x - POST_WIDTH / 2, y, z),
                                  cq.Vector(1, 0, 0), POST_WIDTH, BORE)
                    h = _cylinder((x, y, hb.zmin), cq.Vector(0, 0, 1), hb.zlen, BORE)
                    bores.append({
                        "id": key, "vertical_center_mm": [center_x, y, z],
                        "header_center_mm": [x, y],
                        "vertical_missing_wood_mm3": round(max(0, v.Volume() - wood[member].intersect(v).Volume()), 3),
                        "header_missing_wood_mm3": round(max(0, h.Volume() - wood["base_header"].intersect(h).Volume()), 3),
                    })
                    bore_solids[key] = (v, h)
    panel_clashes = []
    receivers = 0
    for row in panel:
        start = tuple(float(row[f"start_{a}_mm"]) for a in "xyz")
        direction = cq.Vector(*(float(row[f"direction_{a}"]) for a in "xyz"))
        screw = _cylinder(start, direction, 63.5, float(row["occupied_diameter_mm"]))
        if wood[row["second_member"]].intersect(screw).Volume() > 0.01:
            receivers += 1
        clashes = [key for key, (v, h) in bore_solids.items()
                   if v.intersect(screw).Volume() > 0.01 or h.intersect(screw).Volume() > 0.01]
        if clashes:
            panel_clashes.append({"name": row["name"], "bores": clashes})
    edge = {}
    for side in ("left", "right"):
        kicker = baseline[f"kicker_{side}"].BoundingBox()
        post = wood[f"base_post_center_{side}"].BoundingBox()
        edge[side] = round((kicker.xmax - post.xmax) if side == "left"
                           else (post.xmin - kicker.xmin), 4)
    left_inner = wood["base_post_center_left"].BoundingBox().xmax
    right_inner = wood["base_post_center_right"].BoundingBox().xmin
    gap = right_inner - left_inner
    max_gap_with_full_inner_edge_support = (
        baseline["kicker_right"].BoundingBox().xmin
        - baseline["kicker_left"].BoundingBox().xmax
    )
    return {
        "status": "rejected_installed_geometry_trial",
        "concept": "paired HL53 on both X faces of each solid 6x center principal/post; solid 4x header raised upward; upper bracket toward front, lower bracket toward rear",
        "source": str(AXES.relative_to(ROOT)),
        "all_66_panel_axes_unchanged": True,
        "hl53_nominal_pattern_mm": {"bend_length": ANGLE_LENGTH, "leg_reach": ANGLE_REACH,
                                     "hole_offsets_across_each_flange": [FIRST_OFFSET, SECOND_OFFSET]},
        "header_z_mm": [round(hb.zmin, 4), round(hb.zmax, 4)],
        "upper_lower_y_mm": [upper_y, lower_y],
        "upper_lower_y_separation_mm": round(upper_y - lower_y, 4),
        "nominal_wood_bore_diameter_mm": BORE,
        "bores": bores,
        "panel_receivers_with_nominal_intersection": receivers,
        "panel_bore_clashes": panel_clashes,
        "remaining_kicker_inner_edge_overhang_mm": edge,
        "full_kicker_inner_edge_support": all(v <= 0 for v in edge.values()),
        "between_posts_gap_mm": round(gap, 4),
        "maximum_gap_if_posts_alone_support_inner_kicker_edges_mm": round(max_gap_with_full_inner_edge_support, 4),
        "two_inner_gauge7_plates_nominal_mm": 2 * GAUGE7_NOMINAL,
        "nominal_inner_plate_shortfall_mm": round(2 * GAUGE7_NOMINAL - max_gap_with_full_inner_edge_support, 4),
        "disposition": "Reject this paired X-face installed concept: full inner kicker-edge support by the posts alone limits their gap below even two bare nominal 7-gauge inner HL53 plates, before bolt heads, nuts, washers, or tool access. The trial also reports nominal bore and protected screw intersections independently. Moving posts outward with separate kicker blocking, using Y-face brackets, or sharing a common receiver is a different unqualified concept. No wood-joint, steel, withdrawal, neighbor-frame, load-sharing, or native-solve acceptance; do not drill.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_hl53_center(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
