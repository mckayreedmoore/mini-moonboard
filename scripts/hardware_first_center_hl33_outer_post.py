"""One lower-only paired outer-post HL33 nominal geometry screen; no drill data."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hl33 import (
    ALONG_BEND,
    LEG_HOLE,
    LENGTH,
    PLATE,
    REACH,
)
from scripts.hardware_first_center_hybrid import (
    AXES,
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

POST_HALF = 95.25
POST_DEPTH = 90.47
MIN_WOOD = 88.9
HOLE_INSET = 50.8  # undimensioned horizontal-flange hole assumption
WASHER_OD = 25.4  # illustrative radial clearance only


def clashes(shapes, targets):
    return {
        name: found for name, shape in shapes.items() if (found := hits(shape, targets))
    }


def screen_hl33_outer_post():
    """Evaluate one front-aligned post, thick shaped header, and paired angles."""
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
    front = hb.ymax
    rear = front - POST_DEPTH
    # The raised center is part of a single shaped blank; the original span
    # remains in the CAD solid. The post stops below the two nominal seats.
    header = (
        raw["base_header"]
        .fuse(box(-230, hb.ymin, hb.zmin, 460, front - hb.ymin, TOP - hb.zmin))
        .clean()
    )
    post = box(-POST_HALF, rear, 0, 2 * POST_HALF, POST_DEPTH, hb.zmin - PLATE)
    wood = {"post": post, "header": header}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    adjacent = {
        n: s
        for n, s in raw.items()
        if n not in panels
        and n not in {"base_header", "base_post_center_left", "base_post_center_right"}
    }

    plates = {}
    header_centers = {}
    for side, sign in (("left", -1), ("right", 1)):
        outer = sign * POST_HALF
        plates[f"{side}_vertical"] = box(
            outer - PLATE if sign < 0 else outer,
            rear,
            hb.zmin - PLATE - REACH,
            PLATE,
            LENGTH,
            REACH,
        )
        plates[f"{side}_seat"] = box(
            min(outer, outer - sign * REACH),
            rear,
            hb.zmin - PLATE,
            REACH,
            LENGTH,
            PLATE,
        )
        header_centers[side] = outer - sign * HOLE_INSET
    hole_y = rear + ALONG_BEND
    hole_z = hb.zmin - PLATE - LEG_HOLE
    bores = {
        "shared_post": (
            "post",
            bore((-POST_HALF, hole_y, hole_z), (1, 0, 0), 2 * POST_HALF),
        ),
        **{
            f"{side}_header": (
                "header",
                bore((x, hole_y, hb.zmin), (0, 0, 1), TOP - hb.zmin),
            )
            for side, x in header_centers.items()
        },
    }
    bore_shapes = {n: s for n, (_, s) in bores.items()}
    hardware = {**plates, **bore_shapes}
    screws = {r["name"]: cylinder(r) for r in protected}
    long_screws = {r["name"]: cylinder(r, 63.5) for r in protected}
    frame = {r["name"]: cylinder(r) for r in frame_rows}

    receiver_loss = {}
    receiver_missing = {}
    for row in protected:
        name, member = row["name"], row["second_member"]
        replacement = (
            post
            if member.startswith("base_post_center_")
            else (header if member == "base_header" else raw[member])
        )
        old = screws[name].intersect(raw[member]).Volume()
        new = screws[name].intersect(replacement).Volume()
        if old - new > TOL:
            receiver_loss[name] = round(old - new, 3)
        if new <= TOL:
            receiver_missing[name] = member
    kicker_receivers = {
        n: round(shape.intersect(post).Volume(), 3)
        for n, shape in screws.items()
        if n.startswith("round_kicker_") and "_center_" in n
    }
    bore_missing = {
        n: round(shape.Volume() - shape.intersect(wood[member]).Volume(), 3)
        for n, (member, shape) in bores.items()
        if shape.Volume() - shape.intersect(wood[member]).Volume() > TOL
    }
    bore_other = {
        n: found
        for n, (member, shape) in bores.items()
        if (found := hits(shape, {k: s for k, s in wood.items() if k != member}))
    }
    pair_hits = {
        f"{a} / {b}": round(plates[a].intersect(plates[b]).Volume(), 3)
        for a in ("left_vertical", "left_seat")
        for b in ("right_vertical", "right_seat")
        if plates[a].intersect(plates[b]).Volume() > TOL
    }
    bore_crossings = {
        f"{a} / {b}": round(bore_shapes[a].intersect(bore_shapes[b]).Volume(), 3)
        for a in bore_shapes
        for b in bore_shapes
        if a < b and bore_shapes[a].intersect(bore_shapes[b]).Volume() > TOL
    }
    blanks = {n: blank_envelope(s) for n, s in wood.items()}
    stock = {"post": [90.47, 190.5, 2438.4], "header": [90.47, 241.3, 3657.6]}
    stock_fit = {
        n: all(a <= b + TOL for a, b in zip(sorted(blanks[n]), sorted(stock[n])))
        for n in wood
    }
    receiver_thickness = {"post": 2 * POST_HALF, "header": TOP - hb.zmin}
    result = {
        "scope": "lower-only; upper joint unmodeled",
        "source": str(AXES.relative_to(ROOT)),
        "catalog_source": "https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog",
        "protected_axis_count": len(protected),
        "retained_frame_axis_count": len(frame_rows),
        "catalog_minimum_wood_thickness_mm": MIN_WOOD,
        "receiver_thickness_mm": receiver_thickness,
        "post_bounds_mm": bounds(post),
        "header_bounds_mm": bounds(header),
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "bore_bounds_mm": {n: bounds(s) for n, s in bore_shapes.items()},
        "post_hole_center_mm": [0, round(hole_y, 4), round(hole_z, 4)],
        "header_hole_centers_mm": {
            n: [round(x, 4), round(hole_y, 4), round(hb.zmin, 4)]
            for n, x in header_centers.items()
        },
        "shared_post_bolt_axis_count": 1,
        "header_bore_axis_count": 2,
        "header_bore_axis_spacing_mm": round(
            abs(header_centers["right"] - header_centers["left"]), 4
        ),
        "seat_inner_gap_mm": round(2 * (POST_HALF - REACH), 4),
        "plate_pair_clashes_mm3": pair_hits,
        "plate_wood_clashes_mm3": clashes(plates, wood),
        "plate_panel_clashes_mm3": clashes(plates, panels),
        "plate_adjacent_wood_clashes_mm3": clashes(plates, adjacent),
        "new_wood_panel_clashes_mm3": clashes(wood, panels),
        "new_wood_adjacent_clashes_mm3": clashes(wood, adjacent),
        "bore_missing_receiver_wood_mm3": bore_missing,
        "independent_bore_crossings_mm3": bore_crossings,
        "bore_other_wood_clashes_mm3": bore_other,
        "bore_panel_clashes_mm3": clashes(bore_shapes, panels),
        "bore_adjacent_wood_clashes_mm3": clashes(bore_shapes, adjacent),
        "protected_screw_hardware_clashes_mm3": clashes(screws, hardware),
        "conditional_63_5_overall_screw_hardware_clashes_mm3": clashes(
            long_screws, hardware
        ),
        "existing_frame_axis_hardware_clashes_mm3": clashes(frame, hardware),
        "existing_frame_axis_new_wood_clashes_mm3": clashes(frame, wood),
        "protected_screw_receiver_loss_mm3": receiver_loss,
        "protected_screw_receiver_missing": receiver_missing,
        "kicker_center_receivers_mm3": kicker_receivers,
        "kicker_seam_vertical_support_gap_mm": round(
            max(0.0, hb.zmin - post.BoundingBox().zmax), 4
        ),
        "kicker_seam_supported": -POST_HALF <= -1.5875 <= POST_HALF
        and abs(post.BoundingBox().ymax - front) <= TOL
        and abs(header.BoundingBox().ymax - front) <= TOL
        and post.BoundingBox().zmax + TOL >= hb.zmin,
        "ideal_1in_washer_clear_edge_gaps_mm": {
            "header_same_row": round(
                abs(header_centers["right"] - header_centers["left"]) - WASHER_OD, 4
            ),
            "post_to_y_edges": [
                round(hole_y - rear - WASHER_OD / 2, 4),
                round(front - hole_y - WASHER_OD / 2, 4),
            ],
        },
        "one_piece_cad_solid": {n: len(s.Solids()) == 1 for n, s in wood.items()},
        "minimum_axis_aligned_blank_envelope_mm": blanks,
        "stock_example_actual_envelope_mm": stock,
        "stock_example_dimension_fit": stock_fit,
        "stock_leads": {
            "post_primary": {
                "retailer_model": "Lowe's model 110341",
                "listed_section_mm": [190.5, 90.47],
                "url": "https://www.lowes.com/pd/4-in-x-8-in-x-8-ft-Douglas-Fir-Lumber/1000028833",
            },
            "post_optional_dry": {
                "retailer_item_model": "Lowe's item 100565 / model 151980",
                "listed_section_mm": [190.5, 90.47],
                "condition": "#2 Better Douglas fir, kiln-dried; local stock unknown",
                "url": "https://www.lowes.com/pd/Georgia-Pacific-4-in-x-8-in-x-10-ft-Douglas-Fir-Lumber-Common-3-562-in-x-7-5-in-x-10-ft-Actual/1000464221",
            },
            "header": {
                "description": "Lowe's 4x10x12-ft #2 Better Douglas fir, green",
                "listed_section_mm": [90.47, 241.3],
                "local_stock_and_dry_size": "unknown; delivered section must be measured",
                "url": "https://www.lowes.com/pd/4-in-x-10-in-x-12-ft-Douglas-Fir-Lumber-Common-3-562-in-x-9-5-in-x-12-ft-Actual/1000028861",
            },
        },
    }
    failures = []
    for label, bad in (
        (
            "HL33 catalog minimum wood thickness",
            any(v + TOL < MIN_WOOD for v in receiver_thickness.values()),
        ),
        (
            "plate collision",
            bool(
                pair_hits
                or result["plate_wood_clashes_mm3"]
                or result["plate_panel_clashes_mm3"]
                or result["plate_adjacent_wood_clashes_mm3"]
            ),
        ),
        (
            "new wood collision",
            bool(
                result["new_wood_panel_clashes_mm3"]
                or result["new_wood_adjacent_clashes_mm3"]
            ),
        ),
        (
            "bore collision",
            bool(
                bore_missing
                or bore_crossings
                or bore_other
                or result["bore_panel_clashes_mm3"]
                or result["bore_adjacent_wood_clashes_mm3"]
            ),
        ),
        (
            "protected screw collision",
            bool(result["protected_screw_hardware_clashes_mm3"]),
        ),
        (
            "conditional overall screw envelope collision",
            bool(result["conditional_63_5_overall_screw_hardware_clashes_mm3"]),
        ),
        ("protected receiver loss", bool(receiver_loss or receiver_missing)),
        (
            "existing frame axis collision",
            bool(
                result["existing_frame_axis_hardware_clashes_mm3"]
                or result["existing_frame_axis_new_wood_clashes_mm3"]
            ),
        ),
        (
            "kicker seam or center receiver failure",
            not result["kicker_seam_supported"]
            or len(kicker_receivers) != 4
            or any(v <= TOL for v in kicker_receivers.values()),
        ),
        ("one-piece solid failure", not all(result["one_piece_cad_solid"].values())),
        ("stock dimension failure", not all(stock_fit.values())),
    ):
        if bad:
            failures.append(label)
    result["failures"] = failures
    result["status"] = (
        "rejected_installed_geometry_trial" if failures else "geometry_only_unqualified"
    )
    result["qualification"] = (
        "Ideal 4.55-mm full rectangular plates and 14.2875-mm full nominal bores; "
        "horizontal hole inset assumed 50.8 mm. Shared post bolt action, delivered "
        "hole/bend dimensions, head/nut/washer thickness, tool access, tolerances, "
        "wood edge/end distances, resistance and load path are unverified. No drilling data."
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_hl33_outer_post(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
