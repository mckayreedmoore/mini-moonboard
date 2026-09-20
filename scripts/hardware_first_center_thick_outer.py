"""One nominal thick-header, outer-post center trial; never drilling data."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hl33 import (
    ALONG_BEND,
    LEG_HOLE,
    PLATE,
    PRINCIPAL_WIDTH,
    UPPER_Y0,
)
from scripts.hardware_first_center_hl33 import (
    LENGTH as UPPER_LENGTH,
)
from scripts.hardware_first_center_hl33 import (
    REACH as UPPER_REACH,
)
from scripts.hardware_first_center_hybrid import (
    AXES,
    POST_HALF,
    ROOT,
    TOL,
    TOP,
    blank_envelope,
    bore,
    bounds,
    box,
    cylinder,
    hits,
)
from scripts.hardware_first_center_outer_post import (
    HL35_MIN_RECEIVER_THICKNESS,
    HOLE_INSET,
)
from scripts.hardware_first_center_outer_post import (
    LENGTH as LOWER_LENGTH,
)
from scripts.hardware_first_center_outer_post import (
    REACH as LOWER_REACH,
)

RAIL_END_X = 120.0


def clashes(shapes, targets):
    return {
        name: found for name, shape in shapes.items() if (found := hits(shape, targets))
    }


def screen_thick_outer():
    """Screen this one complete nominal pose and its frozen occupied axes."""
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    protected = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(protected) != 66 or len({r["name"] for r in protected}) != 66:
        raise ValueError("expected 66 unique protected panel/kicker axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 frozen frame axes")

    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    hb = raw["base_header"].BoundingBox()
    rear, front = hb.ymin, hb.ymax
    header = (
        raw["base_header"]
        .fuse(
            box(
                -230,
                rear - LOWER_REACH,
                hb.zmin,
                460,
                front - rear + LOWER_REACH,
                TOP - hb.zmin,
            )
        )
        .clean()
    )
    post = box(-POST_HALF, rear, 0, 2 * POST_HALF, front - rear, hb.zmin - PLATE)
    wood = {"header": header, "post": post}
    for side, center in (("left", -70.0), ("right", 70.0)):
        name = f"base_principal_center_{side}"
        original = raw[name]
        spread = (PRINCIPAL_WIDTH - original.BoundingBox().xlen) / 2
        widened = original.fuse(
            original.translate((-spread, 0, 0)), original.translate((spread, 0, 0))
        ).clean()
        b = widened.BoundingBox()
        wood[name] = widened.intersect(
            box(b.xmin - 1, b.ymin - 1, TOP, b.xlen + 2, b.ylen + 2, b.zmax - TOP + 2)
        ).clean()
    rail_names = tuple(
        f"base_rail_{level}_{side}"
        for side in ("left", "right")
        for level in ("bottom", "service_lower", "service_upper")
    )
    original_rails = {name: raw[name] for name in rail_names}
    for name in rail_names:
        b = raw[name].BoundingBox()
        x0, x1 = (
            (b.xmin - 1, -RAIL_END_X)
            if name.endswith("left")
            else (RAIL_END_X, b.xmax + 1)
        )
        wood[name] = (
            raw[name]
            .intersect(box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2))
            .clean()
        )

    plates = {}
    bores = {}
    lower_header_x = {}
    post_centers = {}
    for side, sign in (("left", -1), ("right", 1)):
        outer = sign * POST_HALF
        plates[f"lower_{side}_vertical"] = box(
            outer - PLATE if sign < 0 else outer,
            rear,
            hb.zmin - PLATE - LOWER_REACH,
            PLATE,
            LOWER_LENGTH,
            LOWER_REACH,
        )
        plates[f"lower_{side}_seat"] = box(
            min(outer, outer - sign * LOWER_REACH),
            rear,
            hb.zmin - PLATE,
            LOWER_REACH,
            LOWER_LENGTH,
            PLATE,
        )
        hx = outer - sign * HOLE_INSET
        lower_header_x[side] = hx
        for i, y in enumerate((rear + 31.75, rear + 95.25), 1):
            bores[f"lower_{side}_header_{i}"] = (
                "header",
                bore((hx, y, hb.zmin), (0, 0, 1), TOP - hb.zmin),
            )
            post_centers[f"{side}_{i}"] = [outer, y, hb.zmin - PLATE - 50.8]
    for i, y in enumerate((rear + 31.75, rear + 95.25), 1):
        bores[f"shared_post_{i}"] = (
            "post",
            bore((-POST_HALF, y, hb.zmin - PLATE - 50.8), (1, 0, 0), 2 * POST_HALF),
        )
    upper_header_x = {}
    for side, center in (("left", -70.0), ("right", 70.0)):
        outer = center + (
            -PRINCIPAL_WIDTH / 2 if side == "left" else PRINCIPAL_WIDTH / 2
        )
        plates[f"upper_{side}_vertical"] = box(
            outer - PLATE if side == "left" else outer,
            UPPER_Y0,
            TOP,
            PLATE,
            UPPER_LENGTH,
            UPPER_REACH,
        )
        plates[f"upper_{side}_seat"] = box(
            outer - UPPER_REACH if side == "left" else outer,
            UPPER_Y0,
            TOP,
            UPPER_REACH,
            UPPER_LENGTH,
            PLATE,
        )
        member = f"base_principal_center_{side}"
        bores[f"upper_{side}_principal"] = (
            member,
            bore(
                (center - PRINCIPAL_WIDTH / 2, UPPER_Y0 + ALONG_BEND, TOP + LEG_HOLE),
                (1, 0, 0),
                PRINCIPAL_WIDTH,
            ),
        )
        hx = outer + (-LEG_HOLE if side == "left" else LEG_HOLE)
        upper_header_x[side] = hx
        bores[f"upper_{side}_header"] = (
            "header",
            bore((hx, UPPER_Y0 + ALONG_BEND, hb.zmin), (0, 0, 1), TOP - hb.zmin),
        )

    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    replaced = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        *wood.keys(),
    }
    adjacent = {n: s for n, s in raw.items() if n not in panels and n not in replaced}
    bore_shapes = {n: shape for n, (_, shape) in bores.items()}
    screws = {r["name"]: cylinder(r) for r in protected}
    long_screws = {r["name"]: cylinder(r, 63.5) for r in protected}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    hardware = {**plates, **bore_shapes}
    receiver = dict(raw)
    receiver.update(wood)
    receiver["base_header"] = header
    receiver["base_post_center_left"] = post
    receiver["base_post_center_right"] = post
    receiver_loss = {}
    receiver_missing = {}
    for row in protected:
        name, member = row["name"], row["second_member"]
        old = screws[name].intersect(raw[member]).Volume()
        new = screws[name].intersect(receiver[member]).Volume()
        if old - new > TOL:
            receiver_loss[name] = round(old - new, 3)
        if new <= TOL:
            receiver_missing[name] = member
    bore_missing = {
        n: round(max(0, shape.Volume() - shape.intersect(wood[member]).Volume()), 3)
        for n, (member, shape) in bores.items()
    }
    bore_other = {
        n: found
        for n, (member, shape) in bores.items()
        if (found := hits(shape, {k: v for k, v in wood.items() if k != member}))
    }
    plate_pairs = {}
    for i, (name, shape) in enumerate(plates.items()):
        for other_name, other in list(plates.items())[i + 1 :]:
            if name.rsplit("_", 1)[0] == other_name.rsplit("_", 1)[0]:
                continue
            volume = shape.intersect(other).Volume()
            if volume > TOL:
                plate_pairs[f"{name} / {other_name}"] = round(volume, 3)
    bore_crossings = {}
    for i, (name, shape) in enumerate(bore_shapes.items()):
        for other_name, other in list(bore_shapes.items())[i + 1 :]:
            volume = shape.intersect(other).Volume()
            if volume > TOL:
                bore_crossings[f"{name} / {other_name}"] = round(volume, 3)
    wood_pairs = {}
    for i, (name, shape) in enumerate(wood.items()):
        for other_name, other in list(wood.items())[i + 1 :]:
            volume = shape.intersect(other).Volume()
            if volume > TOL:
                wood_pairs[f"{name} / {other_name}"] = round(volume, 3)
    bracketed_header_thickness = {
        n: round(TOP - hb.zmin, 4)
        for n, (member, _) in bores.items()
        if member == "header"
    }
    undersize = {
        n: t
        for n, t in bracketed_header_thickness.items()
        if t + TOL < HL35_MIN_RECEIVER_THICKNESS
    }
    shared_post_rows = [
        i
        for i in (1, 2)
        if post_centers[f"left_{i}"][1:] == post_centers[f"right_{i}"][1:]
    ]
    blanks = {
        n: blank_envelope(s, n.startswith("base_principal_") or n in rail_names)
        for n, s in wood.items()
    }
    stock = {
        "post": [184.15, 139.7, 3048],
        "header": [90.4748, 241.3, 3657.6],
        **{n: [139.7, 139.7, 3048] for n in wood if n.startswith("base_principal_")},
        **{n: [38.1, 139.7, 3048] for n in rail_names},
    }
    stock_fit = {
        n: all(a <= b + TOL for a, b in zip(sorted(blanks[n]), sorted(stock[n])))
        for n in wood
    }
    results = {
        "width_option": KERF_RIGHT,
        "source": str(AXES.relative_to(ROOT)),
        "protected_axis_count": len(protected),
        "retained_frame_axis_count": len(frame_rows),
        "changed_rail_count": len(rail_names),
        "rail_resection": "Six original rail inner ends cut at X = ±120 mm; one planar cut each.",
        "wood_bounds_mm": {n: bounds(s) for n, s in wood.items()},
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "bore_bounds_mm": {n: bounds(s) for n, s in bore_shapes.items()},
        "bracketed_header_receiver_thickness_mm": bracketed_header_thickness,
        "hl35_minimum_receiver_thickness_mm": HL35_MIN_RECEIVER_THICKNESS,
        "lower_post_receiver_thickness_mm": round(2 * POST_HALF, 4),
        "undersize_header_receivers_mm": undersize,
        "lower_header_hole_x_mm": lower_header_x,
        "upper_header_hole_x_mm": upper_header_x,
        "minimum_upper_lower_header_bore_axis_spacing_x_mm": round(
            min(
                abs(a - b)
                for a in lower_header_x.values()
                for b in upper_header_x.values()
            ),
            4,
        ),
        "post_vertical_hole_centers_mm": post_centers,
        "shared_post_through_bolt_axes": len(shared_post_rows),
        "post_bores_shared_between_lower_plates": len(shared_post_rows) == 2,
        "bore_missing_receiver_wood_mm3": bore_missing,
        "independent_bore_crossings_mm3": bore_crossings,
        "bore_other_wood_clashes_mm3": bore_other,
        "bore_panel_clashes_mm3": clashes(bore_shapes, panels),
        "bore_adjacent_wood_clashes_mm3": clashes(bore_shapes, adjacent),
        "plate_pair_clashes_mm3": plate_pairs,
        "plate_wood_clashes_mm3": clashes(plates, wood),
        "plate_panel_clashes_mm3": clashes(plates, panels),
        "plate_adjacent_wood_clashes_mm3": clashes(plates, adjacent),
        "wood_panel_clashes_mm3": clashes(wood, panels),
        "changed_wood_pair_clashes_mm3": wood_pairs,
        "wood_adjacent_clashes_mm3": clashes(wood, adjacent),
        "protected_screw_hardware_clashes_mm3": clashes(screws, hardware),
        "conditional_63_5_overall_screw_hardware_clashes_mm3": clashes(
            long_screws, hardware
        ),
        "protected_screw_receiver_loss_mm3": receiver_loss,
        "protected_screw_receiver_missing": receiver_missing,
        "existing_frame_axis_hardware_clashes_mm3": clashes(frame, hardware),
        "existing_frame_axis_changed_wood_clashes_mm3": clashes(frame, wood),
        "original_rail_plate_clashes_mm3": clashes(original_rails, plates),
        "original_rail_principal_clashes_mm3": clashes(
            original_rails,
            {n: s for n, s in wood.items() if n.startswith("base_principal_")},
        ),
        "original_rail_bore_clashes_mm3": clashes(original_rails, bore_shapes),
        "one_piece_cad_solid": {n: len(s.Solids()) == 1 for n, s in wood.items()},
        "minimum_sampled_blank_envelope_mm": blanks,
        "ordinary_stock_example_actual_envelope_mm": stock,
        "header_stock_lead": "Lowe's 4x10x12-ft #2 Better Douglas-fir green; local stock and dry size unknown",
        "ordinary_stock_example_dimension_fit": stock_fit,
        "kicker_center_receivers_mm3": {
            n: round(s.intersect(post).Volume(), 3)
            for n, s in screws.items()
            if n.startswith("round_kicker_") and "_center_" in n
        },
        "kicker_seam_supported": (
            -POST_HALF <= -1.5875 <= POST_HALF
            and post.BoundingBox().zmin <= 0
            and post.BoundingBox().zmax >= header.BoundingBox().zmin - TOL
            and header.BoundingBox().zmax >= 277
            and post.BoundingBox().ymax == front
            and header.BoundingBox().ymax == front
        ),
        "kicker_seam_vertical_support_gap_mm": round(
            header.BoundingBox().zmin - post.BoundingBox().zmax, 4
        ),
        "lower_seat_center_x_gap_mm": round(2 * (POST_HALF - LOWER_REACH), 4),
        "reversible_F1_coverage": "unestablished: one outward-X upper HL33 per principal",
        "rail_to_center_attachment": "absent: six cut rail ends have no specified prefabricated connection",
        "shared_post_bolt_action": "unresolved: two through-bolts engage both lower HL35 vertical legs",
    }
    failures = []
    for label, bad in (
        ("catalog header thickness", bool(undersize)),
        ("post through-bolt rows do not coincide", len(shared_post_rows) != 2),
        (
            "plate collision",
            bool(
                plate_pairs
                or results["plate_wood_clashes_mm3"]
                or results["plate_panel_clashes_mm3"]
                or results["plate_adjacent_wood_clashes_mm3"]
            ),
        ),
        (
            "wood collision",
            bool(
                wood_pairs
                or results["wood_panel_clashes_mm3"]
                or results["wood_adjacent_clashes_mm3"]
            ),
        ),
        (
            "protected screw collision",
            bool(results["protected_screw_hardware_clashes_mm3"]),
        ),
        ("bore crossing", bool(bore_crossings)),
        (
            "bore collision",
            bool(
                bore_other
                or results["bore_panel_clashes_mm3"]
                or results["bore_adjacent_wood_clashes_mm3"]
            ),
        ),
        ("bore exits receiver", any(v > TOL for v in bore_missing.values())),
        ("protected receiver loss", bool(receiver_loss or receiver_missing)),
        ("missing kicker seam support", not results["kicker_seam_supported"]),
        (
            "existing frame axis collision",
            bool(
                results["existing_frame_axis_hardware_clashes_mm3"]
                or results["existing_frame_axis_changed_wood_clashes_mm3"]
            ),
        ),
        ("one-piece wood failure", not all(results["one_piece_cad_solid"].values())),
        ("blank dimension failure", not all(stock_fit.values())),
    ):
        if bad:
            failures.append(label)
    results["failures"] = failures
    results["status"] = (
        "rejected_installed_geometry_trial" if failures else "geometry_only_unqualified"
    )
    results["qualification"] = (
        "Ideal nominal plates and 14.2875-mm occupied bores; assumed undimensioned hole insets and "
        "4.55-mm plate thickness. No delivered hardware, structural capacity, reversible-F1 force path, "
        "rail-to-center connection, machining margin, or fabrication release."
    )
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_thick_outer(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
