"""One lower-only outer-X-face HL35 center screen; never drilling data."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hybrid import (
    AXES,
    LENGTH,
    PLATE,
    POST_HALF,
    REACH,
    ROOT,
    TOL,
    blank_envelope,
    bore,
    bounds,
    box,
    cylinder,
    hits,
)

WASHER_OD = 25.4  # illustrative 1-in OD only; thickness and product unspecified
HOLE_INSET = 50.8  # undimensioned horizontal HL35 hole offset assumption
HL35_MIN_RECEIVER_THICKNESS = 88.9  # Simpson HL35 3/5 series, both receivers


def nonempty_hits(shapes, others):
    return {
        name: found for name, shape in shapes.items() if (found := hits(shape, others))
    }


def screen_outer_post():
    """Screen full nominal plates, bores and frozen occupied axes for one pose."""
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    protected = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(protected) != 66 or len({r["name"] for r in protected}) != 66:
        raise ValueError("expected 66 unique protected panel/kicker axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 existing frame axes")

    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    hb = raw["base_header"].BoundingBox()
    rear, front = hb.ymin, hb.ymax
    # The seat occupies the former top 4.55 mm of the post. It supports the
    # unmodified one-piece header while leaving the kicker-facing side aligned.
    post = box(-POST_HALF, rear, 0, 2 * POST_HALF, front - rear, hb.zmin - PLATE)
    header = raw["base_header"]
    receiver_thickness = {"post": post.BoundingBox().xlen, "header": hb.zlen}
    undersize_receivers = {
        n: round(thickness, 4)
        for n, thickness in receiver_thickness.items()
        if thickness + TOL < HL35_MIN_RECEIVER_THICKNESS
    }
    wood = {"post": post, "header": header}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    adjacent = {
        n: s
        for n, s in raw.items()
        if n not in panels
        and n not in {"base_header", "base_post_center_left", "base_post_center_right"}
    }
    plates = {}
    bores = {}
    header_centers = {}
    post_centers = {}
    for side, sign in (("left", -1), ("right", 1)):
        outer = sign * POST_HALF
        x0 = outer - PLATE if sign < 0 else outer
        inner_tip = outer - sign * REACH
        plates[f"{side}_vertical"] = box(
            x0, rear, hb.zmin - PLATE - REACH, PLATE, LENGTH, REACH
        )
        plates[f"{side}_seat"] = box(
            min(outer, inner_tip),
            rear,
            hb.zmin - PLATE,
            REACH,
            LENGTH,
            PLATE,
        )
        hx = outer - sign * HOLE_INSET
        header_centers[side] = hx
        for i, y in enumerate((rear + 31.75, rear + 95.25), 1):
            # Opposite vertical legs share each full-width post bore; two
            # independent side bolts would occupy identical wood cylinders.
            bores[f"{side}_header_{i}"] = (
                "header",
                bore((hx, y, hb.zmin), (0, 0, 1), hb.zlen),
            )
            post_centers[f"{side}_{i}"] = [outer, y, hb.zmin - PLATE - 50.8]
    for i, y in enumerate((rear + 31.75, rear + 95.25), 1):
        bores[f"shared_post_{i}"] = (
            "post",
            bore((-POST_HALF, y, hb.zmin - PLATE - 50.8), (1, 0, 0), 2 * POST_HALF),
        )
    shared_post_rows = [
        i
        for i in (1, 2)
        if post_centers[f"left_{i}"][1:] == post_centers[f"right_{i}"][1:]
    ]

    screws = {r["name"]: cylinder(r) for r in protected}
    long_screws = {r["name"]: cylinder(r, 63.5) for r in protected}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    hardware = {**plates, **{n: shape for n, (_, shape) in bores.items()}}
    pair_hits = {}
    for a in ("left_vertical", "left_seat"):
        for b in ("right_vertical", "right_seat"):
            v = plates[a].intersect(plates[b]).Volume()
            if v > TOL:
                pair_hits[f"{a} / {b}"] = round(v, 3)
    bore_crossings = {}
    for i in (1, 2):
        for j in (1, 2):
            a, b = bores[f"left_header_{i}"][1], bores[f"right_header_{j}"][1]
            v = a.intersect(b).Volume()
            if v > TOL:
                bore_crossings[f"left_{i} / right_{j}"] = round(v, 3)
    bore_missing = {
        n: round(max(0, shape.Volume() - shape.intersect(wood[member]).Volume()), 3)
        for n, (member, shape) in bores.items()
    }
    receiver_loss = {}
    receiver_missing = {}
    for row in protected:
        member = row["second_member"]
        new_member = (
            post
            if member.startswith("base_post_center_")
            else wood.get(member, raw.get(member))
        )
        if new_member is None:
            raise ValueError(f"unknown protected screw receiver: {member}")
        old = screws[row["name"]].intersect(raw[member]).Volume()
        new = screws[row["name"]].intersect(new_member).Volume()
        if old - new > TOL:
            receiver_loss[row["name"]] = round(old - new, 3)
        if new <= TOL:
            receiver_missing[row["name"]] = member
    kicker_receivers = {
        n: round(shape.intersect(post).Volume(), 3)
        for n, shape in screws.items()
        if n.startswith("round_kicker_") and "_center_" in n
    }
    blank = {n: blank_envelope(s) for n, s in wood.items()}
    stock = {"post": [184.15, 139.7, 3048.0], "header": [38.1, 139.7, 3048.0]}
    stock_fit = {
        n: all(a <= b + TOL for a, b in zip(sorted(blank[n]), sorted(stock[n])))
        for n in wood
    }
    plate_wood = nonempty_hits(plates, wood)
    plate_adjacent = nonempty_hits(plates, adjacent)
    plate_panels = nonempty_hits(plates, panels)
    wood_panels = nonempty_hits(wood, panels)
    wood_adjacent = nonempty_hits(wood, adjacent)
    bore_shapes = {n: shape for n, (_, shape) in bores.items()}
    bore_panels = nonempty_hits(bore_shapes, panels)
    bore_adjacent = nonempty_hits(bore_shapes, adjacent)
    bore_other_center_wood = {
        n: hits(
            shape, {other: solid for other, solid in wood.items() if other != member}
        )
        for n, (member, shape) in bores.items()
    }
    bore_other_center_wood = {
        n: found for n, found in bore_other_center_wood.items() if found
    }
    screw_hardware = nonempty_hits(screws, hardware)
    long_screw_hardware = nonempty_hits(long_screws, hardware)
    frame_hardware = nonempty_hits(frame, hardware)
    frame_new_post = nonempty_hits(frame, {"post": post})
    # A 1-in OD disc is only a radial clearance comparator; no washer
    # thickness, head/nut, grip or bearing is implied.
    header_washer_edge_gap = (
        abs(header_centers["right"] - header_centers["left"]) - WASHER_OD
    )
    post_washer_y_gap = 63.5 - WASHER_OD
    failures = []
    for label, bad in (
        ("HL35 catalog minimum receiver thickness", bool(undersize_receivers)),
        (
            "plate collision",
            bool(pair_hits or plate_wood or plate_adjacent or plate_panels),
        ),
        ("new wood collision", bool(wood_panels or wood_adjacent)),
        ("protected screw collision", bool(screw_hardware)),
        (
            "conditional purchased-overall screw envelope collision",
            bool(long_screw_hardware),
        ),
        ("independent header bore crossing", bool(bore_crossings)),
        (
            "bore collision with panel or other wood",
            bool(bore_panels or bore_adjacent or bore_other_center_wood),
        ),
        ("bore exits receiver wood", any(v > TOL for v in bore_missing.values())),
        ("protected screw receiver loss", bool(receiver_loss or receiver_missing)),
        ("existing frame axis collision", bool(frame_hardware)),
        ("existing frame axis enters new post", bool(frame_new_post)),
        (
            "missing kicker support",
            len(kicker_receivers) != 4
            or any(v <= TOL for v in kicker_receivers.values()),
        ),
        (
            "one-piece CAD solid failure",
            any(len(s.Solids()) != 1 for s in wood.values()),
        ),
        ("stock dimension failure", not all(stock_fit.values())),
    ):
        if bad:
            failures.append(label)
    return {
        "status": "rejected_installed_geometry_trial"
        if failures
        else "geometry_only_unqualified",
        "scope": "lower-only; upper center joint unresolved",
        "pose": "paired lower HL35 vertical legs on the common post outer X faces, inward seats beneath one-piece original header",
        "source": str(AXES.relative_to(ROOT)),
        "protected_axis_count": len(protected),
        "retained_frame_bolt_axis_count": len(frame_rows),
        "post_bounds_mm": bounds(post),
        "header_bounds_mm": bounds(header),
        "hl35_catalog_minimum_receiver_thickness_mm": HL35_MIN_RECEIVER_THICKNESS,
        "bolt_receiver_thickness_mm": {
            n: round(v, 4) for n, v in receiver_thickness.items()
        },
        "undersize_hl35_bolt_receivers_mm": undersize_receivers,
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "post_vertical_hole_centers_mm": post_centers,
        "header_hole_x_mm": header_centers,
        "coincident_left_right_post_bolt_rows": shared_post_rows,
        "unique_post_through_bolt_axes": 4 - len(shared_post_rows),
        "post_bores_shared_between_side_plates": len(shared_post_rows) == 2,
        "multilateral_fastener_action": "unresolved; the paired HL35 legs share two through-bolts, not four independent bolts per side",
        "independent_header_bore_axis_spacing_mm": round(
            abs(header_centers["right"] - header_centers["left"]), 4
        ),
        "independent_header_bore_crossings_mm3": bore_crossings,
        "upper_lower_header_bore_spacing": "not applicable: upper HL35 pair omitted in this lower-only trial",
        "bore_missing_receiver_wood_mm3": bore_missing,
        "kicker_seam_x_mm": -1.5875,
        "kicker_seam_supported": -POST_HALF <= -1.5875 <= POST_HALF,
        "kicker_center_receivers_mm3": kicker_receivers,
        "protected_screw_receiver_loss_mm3": receiver_loss,
        "protected_screw_receiver_missing": receiver_missing,
        "plate_pair_clashes_mm3": pair_hits,
        "plate_intended_wood_clashes_mm3": plate_wood,
        "plate_adjacent_wood_clashes_mm3": plate_adjacent,
        "plate_panel_clashes_mm3": plate_panels,
        "new_wood_panel_clashes_mm3": wood_panels,
        "new_wood_adjacent_clashes_mm3": wood_adjacent,
        "bore_panel_clashes_mm3": bore_panels,
        "bore_adjacent_wood_clashes_mm3": bore_adjacent,
        "bore_other_center_wood_clashes_mm3": bore_other_center_wood,
        "protected_screw_hardware_clashes_mm3": screw_hardware,
        "conditional_63_5_overall_screw_hardware_clashes_mm3": long_screw_hardware,
        "existing_frame_axis_hardware_clashes_mm3": frame_hardware,
        "existing_frame_axis_new_post_clashes_mm3": frame_new_post,
        "ideal_1in_od_washer_clear_edge_gaps_mm": {
            "header_left_right_same_row": round(header_washer_edge_gap, 4),
            "post_same_side_along_y": round(post_washer_y_gap, 4),
        },
        "one_piece_cad_solid": {n: len(s.Solids()) == 1 for n, s in wood.items()},
        "minimum_axis_aligned_blank_envelope_mm": blank,
        "ordinary_stock_example_actual_envelope_mm": stock,
        "ordinary_stock_example_dimension_fit": stock_fit,
        "eight_foot_header_length_surplus_mm": round(2438.4 - blank["header"][0], 4),
        "failures": failures,
        "unmodeled": [
            "complete upper principal/header connection; this is lower-only",
            "delivered HL35 hole, bend, plate and coating geometry",
            "actual bolt head, nut, washer thickness/bearing, grip and shared-post-bolt details",
            "tool and withdrawal paths, wood edge/end distances and tolerances",
            "delivered solid stock, grade, machining allowance and local availability",
            "connector and wood resistance, full joint force path",
        ],
        "qualification": "Ideal 4.55-mm full rectangular plates, 14.2875-mm full bores, assumed 50.8-mm header hole inset and illustrative 25.4-mm washer OD. Frozen occupied axes are analysis envelopes, never drilling coordinates. No capacity or fabrication claim.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_outer_post(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
