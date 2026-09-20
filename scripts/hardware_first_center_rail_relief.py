"""Profiled one-piece bottom 4x6 relief screen; never drilling data."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hl33 import ALONG_BEND, LEG_HOLE, PLATE, REACH
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
from scripts.hardware_first_center_hybrid_toe import _principal
from scripts.hardware_first_center_thick_rails import (
    MIN_RECEIVER,
    ORIGINAL_THICKNESS,
    RAIL_THICKNESS,
    rail_normal,
)
from scripts.hardware_first_center_tongue import (
    HOLE_INSET,
    POST_DEPTH,
    POST_HALF,
    RAIL_END_X,
    TONGUE_HALF,
    UPPER_Y0,
)

CLEARANCE = 1.0  # nominal CAD envelope, not an installation or tolerance allowance
SEAT_BAND_LENGTH = 63.5  # HL33 listed L; candidate rail-side contact band only


def clearance_box(shape):
    b = shape.BoundingBox()
    return box(
        b.xmin - CLEARANCE,
        b.ymin - CLEARANCE,
        b.zmin - CLEARANCE,
        b.xlen + 2 * CLEARANCE,
        b.ylen + 2 * CLEARANCE,
        b.zlen + 2 * CLEARANCE,
    )


def clashes(shapes, targets):
    return {n: found for n, shape in shapes.items() if (found := hits(shape, targets))}


def screen_rail_relief():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    protected = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(protected) != 66 or len({r["name"] for r in protected}) != 66:
        raise ValueError("expected 66 unique fixed panel/kicker axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 fixed frame axes")

    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    hb = raw["base_header"].BoundingBox()
    rear = hb.ymax - POST_DEPTH
    lower_top = hb.zmin - PLATE
    post = (
        box(-POST_HALF, rear, 0, 2 * POST_HALF, POST_DEPTH, lower_top)
        .fuse(box(-TONGUE_HALF, rear, lower_top, 2 * TONGUE_HALF, POST_DEPTH, PLATE))
        .clean()
    )
    raised_header = box(
        -230,
        hb.ymin - REACH,
        hb.zmin,
        460,
        hb.ymax - hb.ymin + REACH,
        TOP - hb.zmin,
    )
    header = raw["base_header"].fuse(raised_header).clean()
    wood = {
        "post": post,
        "header": header,
        "base_principal_center_left": _principal("left"),
        "base_principal_center_right": _principal("right"),
    }
    seats = {}
    bores = {}
    for side, sign in (("left", -1), ("right", 1)):
        outer = sign * POST_HALF
        bores[f"lower_{side}_header"] = bore(
            (outer - sign * HOLE_INSET, rear + ALONG_BEND, hb.zmin),
            (0, 0, 1),
            TOP - hb.zmin,
        )
        center = sign * 70.0
        upper_outer = center + sign * 44.45
        seats[f"upper_{side}_seat"] = box(
            upper_outer - REACH if sign < 0 else upper_outer,
            UPPER_Y0,
            TOP,
            REACH,
            63.5,
            PLATE,
        )
        bores[f"upper_{side}_header"] = bore(
            (upper_outer + sign * LEG_HOLE, UPPER_Y0 + ALONG_BEND, hb.zmin),
            (0, 0, 1),
            TOP - hb.zmin,
        )

    originals = {}
    thick = {}
    relieved = {}
    service_rails = {}
    relief_removed = {}
    for side in ("left", "right"):
        name = f"base_rail_bottom_{side}"
        original = raw[name]
        b = original.BoundingBox()
        x0, x1 = (
            (b.xmin - 1, -RAIL_END_X) if side == "left" else (RAIL_END_X, b.xmax + 1)
        )
        cut = original.intersect(
            box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2)
        ).clean()
        ny, nz = rail_normal(cut)
        added = RAIL_THICKNESS - ORIGINAL_THICKNESS
        full = cut.fuse(
            cut.translate((0, -ny * added / 2, -nz * added / 2)),
            cut.translate((0, -ny * added, -nz * added)),
        ).clean()
        # Profile only the added rear material; the source rail stays whole.
        extra = full.cut(cut).clean()
        obstacles = (
            raised_header,
            seats[f"upper_{side}_seat"],
            bores[f"upper_{side}_header"],
        )
        for obstacle in obstacles:
            extra = extra.cut(clearance_box(obstacle)).clean()
        profile = cut.fuse(extra).clean()
        originals[name], thick[name], relieved[name] = cut, full, profile
        relief_removed[name] = round(full.Volume() - profile.Volume(), 3)

    # The four unchanged service rails retain the rejected parent's cut/thick profile.
    for side in ("left", "right"):
        for level in ("service_lower", "service_upper"):
            name = f"base_rail_{level}_{side}"
            original = raw[name]
            b = original.BoundingBox()
            x0, x1 = (
                (b.xmin - 1, -RAIL_END_X)
                if side == "left"
                else (RAIL_END_X, b.xmax + 1)
            )
            cut = original.intersect(
                box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2)
            ).clean()
            ny, nz = rail_normal(cut)
            added = RAIL_THICKNESS - ORIGINAL_THICKNESS
            service_rails[name] = cut.fuse(
                cut.translate((0, -ny * added / 2, -nz * added / 2)),
                cut.translate((0, -ny * added, -nz * added)),
            ).clean()

    replaced = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
        "base_rail_bottom_left",
        "base_rail_bottom_right",
        *service_rails,
    }
    adjacent = {n: s for n, s in raw.items() if n not in panels and n not in replaced}
    screws = {r["name"]: cylinder(r) for r in protected}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    all_wood = {**wood, **adjacent, **service_rails, **relieved}
    original_loss = {
        n: round(
            max(0, original.Volume() - original.intersect(relieved[n]).Volume()), 3
        )
        for n, original in originals.items()
        if original.Volume() - original.intersect(relieved[n]).Volume() > TOL
    }
    receiver_loss = {}
    receiver_missing = {}
    for row in protected:
        name, member = row["name"], row["second_member"]
        receiver = (
            post
            if member.startswith("base_post_center_")
            else header
            if member == "base_header"
            else relieved[member]
            if member in relieved
            else service_rails[member]
            if member in service_rails
            else wood[member]
            if member in wood
            else raw.get(member)
        )
        if receiver is None:
            raise ValueError(f"unknown receiver: {member}")
        old = screws[name].intersect(raw[member]).Volume()
        new = screws[name].intersect(receiver).Volume()
        if old - new > TOL:
            receiver_loss[name] = round(old - new, 3)
        if old > TOL and new <= TOL:
            receiver_missing[name] = member
    wood_clashes = {
        n: hits(s, {k: v for k, v in all_wood.items() if k != n})
        for n, s in relieved.items()
    }
    wood_clashes = {n: v for n, v in wood_clashes.items() if v}
    panel_clashes = clashes(relieved, panels)
    seat_clashes = clashes(relieved, seats)
    bore_clashes = clashes(relieved, bores)
    frame_clashes = clashes(relieved, frame)
    screw_added = {}
    for n, shape in relieved.items():
        found = {
            axis: round(new - screws[axis].intersect(originals[n]).Volume(), 3)
            for axis in screws
            if (new := screws[axis].intersect(shape).Volume())
            - screws[axis].intersect(originals[n]).Volume()
            > TOL
        }
        if found:
            screw_added[n] = found
    one_piece = {n: len(s.Solids()) == 1 for n, s in relieved.items()}
    seat_bands = {}
    seat_band_loss = {}
    for n, shape in relieved.items():
        b = thick[n].BoundingBox()
        left = n.endswith("left")
        x0 = -230 - CLEARANCE - SEAT_BAND_LENGTH if left else 230 + CLEARANCE
        band = box(x0, b.ymin - 1, b.zmin - 1, SEAT_BAND_LENGTH, b.ylen + 2, b.zlen + 2)
        seat_bands[n] = [round(x0, 4), round(x0 + SEAT_BAND_LENGTH, 4)]
        seat_band_loss[n] = round(
            max(0, thick[n].intersect(band).Volume() - shape.intersect(band).Volume()),
            3,
        )
    blanks = {n: blank_envelope(s, True) for n, s in relieved.items()}
    stock = [90.4748, 142.875, 3048.0]
    stock_fit = {
        n: all(a <= b + TOL for a, b in zip(sorted(dim), sorted(stock)))
        for n, dim in blanks.items()
    }
    failures = [
        label
        for label, bad in (
            ("wood collision", bool(wood_clashes)),
            ("panel collision", bool(panel_clashes)),
            ("upper seat or bore collision", bool(seat_clashes or bore_clashes)),
            (
                "original wood or screw receiver loss",
                bool(original_loss or receiver_loss or receiver_missing),
            ),
            ("new protected screw occupancy", bool(screw_added)),
            ("existing frame axis collision", bool(frame_clashes)),
            (
                "one-piece or stock comparator failure",
                not all(one_piece.values()) or not all(stock_fit.values()),
            ),
            (
                "candidate rail-side seat band loses full thickness",
                any(v > TOL for v in seat_band_loss.values()),
            ),
        )
        if bad
    ]
    return {
        "status": "rejected_installed_geometry_trial"
        if failures
        else "geometry_only_unqualified",
        "source": str(AXES.relative_to(ROOT)),
        "width_option": KERF_RIGHT,
        "protected_axis_count": len(protected),
        "retained_frame_axis_count": len(frame_rows),
        "fixed_panel_outline_count": len(panels),
        "changed_rail_count": len(relieved),
        "retained_parent_thick_service_rail_count": len(service_rails),
        "profile": "Keep original cut bottom rail whole; add rear-normal material to 90.4748 mm, then remove added material inside 1-mm-expanded raised-center-header, upper-seat and upper-header-bore bounding boxes.",
        "clearance_envelope_mm": CLEARANCE,
        "minimum_hl_receiver_thickness_mm": MIN_RECEIVER,
        "full_blank_thickness_mm": RAIL_THICKNESS,
        "candidate_hl33_rail_side_contact_band_x_mm": seat_bands,
        "candidate_contact_band_full_section_thickness_mm": {
            n: RAIL_THICKNESS for n in seat_bands
        },
        "candidate_contact_band_full_section_loss_mm3": seat_band_loss,
        "rail_bounds_mm": {n: bounds(s) for n, s in relieved.items()},
        "relief_removed_mm3": relief_removed,
        "minimum_sampled_blank_envelope_mm": blanks,
        "listed_4x6_actual_stock_comparator_mm": stock,
        "listed_4x6_dimension_fit": stock_fit,
        "one_piece_cad_solid": one_piece,
        "original_bottom_rail_wood_loss_mm3": original_loss,
        "protected_screw_receiver_loss_mm3": receiver_loss,
        "protected_screw_receiver_missing": receiver_missing,
        "rail_other_wood_clashes_mm3": wood_clashes,
        "rail_panel_clashes_mm3": panel_clashes,
        "rail_upper_seat_clashes_mm3": seat_clashes,
        "rail_upper_header_bore_clashes_mm3": bore_clashes,
        "rail_protected_screw_added_occupancy_mm3": screw_added,
        "rail_existing_frame_axis_clashes_mm3": frame_clashes,
        "failures": failures,
        "qualification": "Nominal occupancy and full-section rail-side contact band only. No installed HL33 pose, mating header seat, bolt stack, access, delivered stock, capacity, or drilling approval.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_rail_relief(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
