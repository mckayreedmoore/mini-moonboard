"""One nominal HL33 hybrid center screen; coordinates are never drill data."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hybrid import (
    AXES,
    ROOT,
    blank_envelope,
    bore,
    bounds,
    box,
    cylinder,
    hits,
)

REACH = 82.55  # C-C-2026 HL33 W1/W2 = 3 1/4 in
LENGTH = 63.5  # C-C-2026 HL33 L = 2 1/2 in
ALONG_BEND = 31.75  # C-C-2026 D1 = 1 1/4 in
LEG_HOLE = 50.8  # C-C-2026 D3 = 2 in, vertical leg
PLATE = 4.55  # assumed ideal 7-gauge envelope, not a delivered dimension
BORE = 14.2875  # assumed 9/16-in wood clearance, not a drill instruction
TOP = 327.8
POST_HALF = 92.075
PRINCIPAL_WIDTH = 88.9
UPPER_Y0 = -100.0  # one installed pose; hole at -68.25 mm
TOL = 0.01


def screen_hl33():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len({r["name"] for r in panel_rows}) != 66:
        raise ValueError("expected 66 unique protected kerf-right axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 existing frame axes")

    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    hb = raw["base_header"].BoundingBox()
    rear, front = hb.ymin, hb.ymax
    lower_rear = rear - REACH
    header = (
        raw["base_header"]
        .fuse(box(-230, lower_rear, hb.zmin, 460, front - lower_rear, TOP - hb.zmin))
        .clean()
    )
    post = box(-POST_HALF, rear, 0, POST_HALF * 2, front - rear, hb.zmin)
    principals = {}
    for side, center in (("left", -70.0), ("right", 70.0)):
        name = f"base_principal_center_{side}"
        original = raw[name]
        spread = (PRINCIPAL_WIDTH - original.BoundingBox().xlen) / 2
        widened = original.fuse(
            original.translate((-spread, 0, 0)), original.translate((spread, 0, 0))
        ).clean()
        b = widened.BoundingBox()
        principals[name] = widened.intersect(
            box(b.xmin - 1, b.ymin - 1, TOP, b.xlen + 2, b.ylen + 2, b.zmax - TOP + 2)
        ).clean()
    wood = {"post": post, "header": header, **principals}
    panels = {n: s for n, s in raw.items() if n.startswith(("kicker_", "main_"))}
    replaced = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
    }
    adjacent = {n: s for n, s in raw.items() if n not in panels and n not in replaced}

    plates = {
        "lower_vertical": box(
            -LENGTH / 2, rear - PLATE, hb.zmin - REACH, LENGTH, PLATE, REACH
        ),
        "lower_seat": box(
            -LENGTH / 2, lower_rear, hb.zmin - PLATE, LENGTH, REACH, PLATE
        ),
    }
    bores = {
        "lower_post": (
            "post",
            bore((0, rear, hb.zmin - LEG_HOLE), (0, 1, 0), front - rear),
        ),
        # Horizontal-flange hole offset is undimensioned; symmetric assumption.
        "lower_header": (
            "header",
            bore((0, rear - LEG_HOLE, hb.zmin), (0, 0, 1), TOP - hb.zmin),
        ),
    }
    for side, center in (("left", -70.0), ("right", 70.0)):
        outer = center + (
            -PRINCIPAL_WIDTH / 2 if side == "left" else PRINCIPAL_WIDTH / 2
        )
        outward = -1 if side == "left" else 1
        plates[f"upper_{side}_vertical"] = box(
            outer - PLATE if side == "left" else outer,
            UPPER_Y0,
            TOP,
            PLATE,
            LENGTH,
            REACH,
        )
        plates[f"upper_{side}_seat"] = box(
            outer - REACH if side == "left" else outer,
            UPPER_Y0,
            TOP,
            REACH,
            LENGTH,
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
        bores[f"upper_{side}_header"] = (
            "header",
            bore(
                (outer + outward * LEG_HOLE, UPPER_Y0 + ALONG_BEND, hb.zmin),
                (0, 0, 1),
                TOP - hb.zmin,
            ),
        )

    screws = {r["name"]: cylinder(r) for r in panel_rows}
    long_screws = {r["name"]: cylinder(r, 63.5) for r in panel_rows}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    bore_shapes = {n: solid for n, (_, solid) in bores.items()}
    hardware = {**plates, **bore_shapes}
    plate_pairs = {}
    for i, (a, shape) in enumerate(plates.items()):
        for b, other in list(plates.items())[i + 1 :]:
            if a.rsplit("_", 1)[0] == b.rsplit("_", 1)[0]:
                continue  # two legs of the same ideal angle share a bend
            volume = shape.intersect(other).Volume()
            if volume > TOL:
                plate_pairs[f"{a} / {b}"] = round(volume, 3)
    bore_crossings = {}
    for i, (a, shape) in enumerate(bore_shapes.items()):
        for b, other in list(bore_shapes.items())[i + 1 :]:
            volume = shape.intersect(other).Volume()
            if volume > TOL:
                bore_crossings[f"{a} / {b}"] = round(volume, 3)
    missing = {
        n: round(max(0, solid.Volume() - solid.intersect(wood[member]).Volume()), 3)
        for n, (member, solid) in bores.items()
        if solid.Volume() - solid.intersect(wood[member]).Volume() > TOL
    }
    receiver_loss = {}
    for row in panel_rows:
        name, member = row["name"], row["second_member"]
        receiver = (
            post
            if member.startswith("base_post_center_")
            else header
            if member == "base_header"
            else principals.get(member, raw.get(member))
        )
        if receiver is None:
            raise ValueError(f"unknown protected receiver: {member}")
        loss = (
            screws[name].intersect(raw[member]).Volume()
            - screws[name].intersect(receiver).Volume()
        )
        if loss > TOL:
            receiver_loss[name] = round(loss, 3)
    kicker_receivers = {
        n: round(shape.intersect(post).Volume(), 3)
        for n, shape in screws.items()
        if n.startswith("round_kicker_") and "_center_" in n
    }

    def clashes(items, targets):
        return {n: hit for n, shape in items.items() if (hit := hits(shape, targets))}

    plate_wood = clashes(plates, wood)
    plate_panel = clashes(plates, panels)
    plate_adjacent = clashes(plates, adjacent)
    wood_panel = clashes(wood, panels)
    wood_adjacent = clashes(wood, adjacent)
    bore_panel = clashes(bore_shapes, panels)
    bore_adjacent = clashes(bore_shapes, adjacent)
    bore_other_wood = {
        n: hit
        for n, (member, shape) in bores.items()
        if (hit := hits(shape, {k: v for k, v in wood.items() if k != member}))
    }
    screw_plate = clashes(screws, plates)
    screw_bore = clashes(screws, bore_shapes)
    long_screw_plate = clashes(long_screws, plates)
    long_screw_bore = clashes(long_screws, bore_shapes)
    frame_hardware = clashes(frame, hardware)
    frame_wood = clashes(frame, wood)
    one_piece = {n: len(shape.Solids()) == 1 for n, shape in wood.items()}
    blanks = {
        n: blank_envelope(shape, n.startswith("base_principal_"))
        for n, shape in wood.items()
    }
    stock = {
        "post": [184.15, 139.7, 3048.0],
        "header": [88.9, 241.3, 3048.0],
        "base_principal_center_left": [139.7, 139.7, 3048.0],
        "base_principal_center_right": [139.7, 139.7, 3048.0],
    }
    stock_fit = {
        n: all(a <= b + TOL for a, b in zip(sorted(blank), sorted(stock[n])))
        for n, blank in blanks.items()
    }
    kicker_seam = -1.5875
    # Center seam runs over the common post then the raised header up to the
    # kicker top. This checks continuous nominal rear-edge contact in Z.
    kicker_top = max(raw[n].BoundingBox().zmax for n in ("kicker_left", "kicker_right"))
    seam_supported = (
        -POST_HALF <= kicker_seam <= POST_HALF
        and post.BoundingBox().zmin <= 0
        and post.BoundingBox().zmax >= header.BoundingBox().zmin
        and header.BoundingBox().zmax >= kicker_top
        and post.BoundingBox().ymax == front
        and header.BoundingBox().ymax == front
    )
    failures = [
        label
        for label, failed in (
            (
                "plate collision",
                bool(plate_pairs or plate_wood or plate_panel or plate_adjacent),
            ),
            ("new wood collision", bool(wood_panel or wood_adjacent)),
            ("protected screw collision", bool(screw_plate or screw_bore)),
            ("independent bore crossing", bool(bore_crossings)),
            (
                "bore collision with other material",
                bool(bore_panel or bore_adjacent or bore_other_wood),
            ),
            ("bore exits receiving wood", bool(missing)),
            ("protected screw receiver loss", bool(receiver_loss)),
            ("existing frame axis collision", bool(frame_hardware or frame_wood)),
            (
                "missing kicker edge backing",
                not seam_supported
                or len(kicker_receivers) != 4
                or any(v <= TOL for v in kicker_receivers.values()),
            ),
            ("not one-piece CAD solids", not all(one_piece.values())),
            ("no dimensional retail blank fit", not all(stock_fit.values())),
        )
        if failed
    ]
    return {
        "status": "rejected_installed_geometry_trial"
        if failures
        else "geometry_only_unqualified",
        "pose": "One rear-Y HL33 on one-piece common post, two outward-X HL33 on one-piece thick principals; raised one-piece shaped header; upper Y start -100 mm",
        "source": str(AXES.relative_to(ROOT)),
        "catalog_source": "https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog",
        "catalog_mm": {
            "leg_reach": REACH,
            "bend_length": LENGTH,
            "along_bend_hole_offset": ALONG_BEND,
            "vertical_leg_hole_offset": LEG_HOLE,
            "bolt_diameter": 12.7,
            "bolt_quantity_per_angle": 2,
            "gauge": 7,
        },
        "undimensioned_assumptions": {
            "horizontal_flange_hole_offset_mm": LEG_HOLE,
            "ideal_plate_thickness_mm": PLATE,
            "wood_bore_diameter_mm": BORE,
            "qualification": "Horizontal hole offset and actual plate thickness are not dimensioned in the catalog drawing. Ideal plate rectangles, bend radii and delivered hole tolerances are not verified; bore is a diagnostic clearance envelope, not a drill size.",
        },
        "protected_axis_count": len(panel_rows),
        "existing_frame_axis_count": len(frame_rows),
        "header_bounds_mm": bounds(header),
        "post_bounds_mm": bounds(post),
        "principal_bounds_mm": {n: bounds(s) for n, s in principals.items()},
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "one_piece_cad_solid": one_piece,
        "minimum_sampled_blank_envelope_mm": blanks,
        "ordinary_stock_example_actual_envelope_mm": stock,
        "ordinary_stock_example_dimension_fit": stock_fit,
        "retail_blank_qualification": "Envelope fit is dimensional only; delivered one-piece stock, grade, defects, machining margin, handling and local availability are unverified. CAD fusions define one-piece shapes, not laminated members.",
        "kicker_seam_x_mm": kicker_seam,
        "kicker_seam_supported": seam_supported,
        "kicker_center_receivers_mm3": kicker_receivers,
        "protected_screw_receiver_loss_mm3": receiver_loss,
        "plate_pair_clashes_mm3": plate_pairs,
        "plate_intended_wood_clashes_mm3": plate_wood,
        "plate_panel_clashes_mm3": plate_panel,
        "plate_adjacent_wood_clashes_mm3": plate_adjacent,
        "new_wood_panel_clashes_mm3": wood_panel,
        "new_wood_adjacent_clashes_mm3": wood_adjacent,
        "bore_bounds_mm": {n: bounds(shape) for n, shape in bore_shapes.items()},
        "bore_panel_clashes_mm3": bore_panel,
        "bore_adjacent_wood_clashes_mm3": bore_adjacent,
        "bore_other_new_wood_clashes_mm3": bore_other_wood,
        "protected_screw_plate_clashes_mm3": screw_plate,
        "protected_screw_bore_clashes_mm3": screw_bore,
        "conditional_63_5_overall_screw_plate_clashes_mm3": long_screw_plate,
        "conditional_63_5_overall_screw_bore_clashes_mm3": long_screw_bore,
        "bore_missing_receiver_wood_mm3": missing,
        "independent_bore_crossings_mm3": bore_crossings,
        "existing_frame_axis_hardware_clashes_mm3": frame_hardware,
        "existing_frame_axis_new_wood_clashes_mm3": frame_wood,
        "failures": failures,
        "unmodeled": [
            "heads, washers, nuts and tool/withdrawal access",
            "delivered HL33 bends, holes, coatings and tolerances",
            "wood edge/end distance and joint resistance",
            "bracket load path and frame redesign for any collision",
            "delivered screw shaft occupancy and required embedment",
            "retail stock availability and one-piece machining yield",
        ],
        "qualification": "Nominal geometry only. Existing frame axes are checked as occupied cylinders but their receiving wood and resistance are not requalified. No capacity, procurement, cutting or drilling approval.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_hl33(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
