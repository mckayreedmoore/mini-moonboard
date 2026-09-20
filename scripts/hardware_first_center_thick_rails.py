"""Six cut-rail 4x6 CAD feasibility screen; no bracket or drilling design."""

import argparse
import csv
import json
import math
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
from scripts.hardware_first_center_hybrid_toe import _principal
from scripts.hardware_first_center_tongue import (
    HOLE_INSET,
    POST_DEPTH,
    POST_HALF,
    RAIL_END_X,
    TONGUE_HALF,
    UPPER_Y0,
)

RAIL_THICKNESS = 90.4748  # listed 3.562-in actual 4x6 thickness; nominal only
ORIGINAL_THICKNESS = 38.1
MIN_RECEIVER = 88.9


def rail_normal(shape):
    """Original front normal in the YZ section; rear is its negative."""
    yz = sorted({(round(v.Y, 7), round(v.Z, 7)) for v in shape.Vertices()})
    dy, dz = yz[1][0] - yz[0][0], yz[1][1] - yz[0][1]
    length = math.hypot(dy, dz)
    if abs(length - ORIGINAL_THICKNESS) > TOL or dy <= 0 or dz <= 0:
        raise ValueError("unexpected rail thickness direction")
    return dy / length, dz / length


def collisions(shapes, targets):
    return {n: found for n, shape in shapes.items() if (found := hits(shape, targets))}


def screen_thick_rails():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    protected = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(protected) != 66 or len({r["name"] for r in protected}) != 66:
        raise ValueError("expected 66 unique fixed panel/kicker axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 existing frame axes")

    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    hb = raw["base_header"].BoundingBox()
    front, rear = hb.ymax, hb.ymax - POST_DEPTH
    lower_top = hb.zmin - PLATE
    tongue = box(-TONGUE_HALF, rear, lower_top, 2 * TONGUE_HALF, POST_DEPTH, PLATE)
    post = (
        box(-POST_HALF, rear, 0, 2 * POST_HALF, POST_DEPTH, lower_top)
        .fuse(tongue)
        .clean()
    )
    header = (
        raw["base_header"]
        .fuse(
            box(
                -230,
                hb.ymin - REACH,
                hb.zmin,
                460,
                front - hb.ymin + REACH,
                TOP - hb.zmin,
            )
        )
        .clean()
    )
    center_wood = {
        "post": post,
        "header": header,
        "base_principal_center_left": _principal("left"),
        "base_principal_center_right": _principal("right"),
    }
    names = tuple(
        f"base_rail_{level}_{side}"
        for side in ("left", "right")
        for level in ("bottom", "service_lower", "service_upper")
    )
    cut_rails = {}
    thick_rails = {}
    normals = {}
    for name in names:
        original = raw[name]
        b = original.BoundingBox()
        x0, x1 = (
            (b.xmin - 1, -RAIL_END_X)
            if name.endswith("left")
            else (RAIL_END_X, b.xmax + 1)
        )
        cut = original.intersect(
            box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2)
        ).clean()
        ny, nz = rail_normal(cut)
        added = RAIL_THICKNESS - ORIGINAL_THICKNESS
        # ponytail: two overlapping translated sections make the minimum
        # single-piece prismatic envelope without a second timber/lamination.
        thick = cut.fuse(
            cut.translate((0, -ny * added / 2, -nz * added / 2)),
            cut.translate((0, -ny * added, -nz * added)),
        ).clean()
        cut_rails[name] = cut
        thick_rails[name] = thick
        normals[name] = [round(ny, 6), round(nz, 6)]

    replaced = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
        *names,
    }
    adjacent = {n: s for n, s in raw.items() if n not in panels and n not in replaced}
    plates = {}
    bores = {}
    for side, sign in (("left", -1), ("right", 1)):
        outer = sign * POST_HALF
        plates[f"lower_{side}_vertical"] = box(
            outer - PLATE if sign < 0 else outer,
            rear,
            lower_top - REACH,
            PLATE,
            LENGTH,
            REACH,
        )
        plates[f"lower_{side}_seat"] = box(
            min(outer, outer - sign * REACH), rear, lower_top, REACH, LENGTH, PLATE
        )
        bores[f"lower_{side}_header"] = bore(
            (outer - sign * HOLE_INSET, rear + ALONG_BEND, hb.zmin),
            (0, 0, 1),
            TOP - hb.zmin,
        )
    bores["shared_post"] = bore(
        (-POST_HALF, rear + ALONG_BEND, lower_top - LEG_HOLE),
        (1, 0, 0),
        2 * POST_HALF,
    )
    for side, center in (("left", -70.0), ("right", 70.0)):
        outer = center + (-44.45 if side == "left" else 44.45)
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
        bores[f"upper_{side}_principal"] = bore(
            (center - 44.45, UPPER_Y0 + ALONG_BEND, TOP + LEG_HOLE),
            (1, 0, 0),
            88.9,
        )
        bores[f"upper_{side}_header"] = bore(
            (
                outer + (-LEG_HOLE if side == "left" else LEG_HOLE),
                UPPER_Y0 + ALONG_BEND,
                hb.zmin,
            ),
            (0, 0, 1),
            TOP - hb.zmin,
        )
    hardware = {**plates, **bores}
    screws = {r["name"]: cylinder(r) for r in protected}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    all_wood = {**center_wood, **thick_rails, **adjacent}
    rail_other_wood = {
        n: hits(s, {k: v for k, v in all_wood.items() if k != n})
        for n, s in thick_rails.items()
    }
    rail_other_wood = {n: v for n, v in rail_other_wood.items() if v}
    rail_panel = collisions(thick_rails, panels)
    rail_hardware = collisions(thick_rails, hardware)
    # Existing screw penetration into its rail is intentional. Report only
    # additional occupied volume caused by the thickening.
    rail_screws = {}
    for name, shape in thick_rails.items():
        added_hits = {
            axis: round(new - screw.intersect(cut_rails[name]).Volume(), 3)
            for axis, screw in screws.items()
            if (new := screw.intersect(shape).Volume())
            - screw.intersect(cut_rails[name]).Volume()
            > TOL
        }
        if added_hits:
            rail_screws[name] = added_hits
    rail_frame = collisions(thick_rails, frame)

    original_loss = {
        n: round(cut.Volume() - cut.intersect(thick_rails[n]).Volume(), 3)
        for n, cut in cut_rails.items()
        if cut.Volume() - cut.intersect(thick_rails[n]).Volume() > TOL
    }
    receiver_loss = {}
    receiver_missing = {}
    for row in protected:
        member, name = row["second_member"], row["name"]
        if member not in thick_rails:
            continue
        old = screws[name].intersect(cut_rails[member]).Volume()
        new = screws[name].intersect(thick_rails[member]).Volume()
        if old - new > TOL:
            receiver_loss[name] = round(old - new, 3)
        if old > TOL and new <= TOL:
            receiver_missing[name] = member

    # One millimeter of open space at each actual cut-end footprint establishes
    # an exposed candidate face, not bolt-stack or installation access.
    face_blockers = {}
    for name, shape in thick_rails.items():
        left = name.endswith("left")
        shifted = shape.translate((1 if left else -1, 0, 0))
        b = shape.BoundingBox()
        x0 = -RAIL_END_X if left else RAIL_END_X - 1
        prism = shifted.intersect(
            box(x0, b.ymin - 100, b.zmin - 100, 1, b.ylen + 200, b.zlen + 200)
        )
        blockers = hits(
            prism,
            {
                **{k: v for k, v in all_wood.items() if k != name},
                **panels,
                **hardware,
                **screws,
                **frame,
            },
        )
        if blockers:
            face_blockers[name] = blockers

    blanks = {n: blank_envelope(s, True) for n, s in thick_rails.items()}
    stock = [90.4748, 142.875, 3048.0]  # listed actual 4x6 section, 10-ft comparator
    stock_fit = {
        n: all(a <= b + TOL for a, b in zip(sorted(dim), sorted(stock)))
        for n, dim in blanks.items()
    }
    failures = [
        label
        for label, bad in (
            ("rail collision with wood", bool(rail_other_wood)),
            ("rail collision with panel", bool(rail_panel)),
            ("rail collision with tongue-concept plate or bore", bool(rail_hardware)),
            ("rail collision with protected screw", bool(rail_screws)),
            ("rail collision with existing frame axis", bool(rail_frame)),
            (
                "original rail or screw support lost",
                bool(original_loss or receiver_loss or receiver_missing),
            ),
            ("cut end face blocked", bool(face_blockers)),
            (
                "one-piece CAD solid failure",
                not all(len(s.Solids()) == 1 for s in thick_rails.values()),
            ),
            ("4x6 dimension failure", not all(stock_fit.values())),
            ("receiver thickness failure", RAIL_THICKNESS + TOL < MIN_RECEIVER),
        )
        if bad
    ]
    return {
        "width_option": KERF_RIGHT,
        "source": str(AXES.relative_to(ROOT)),
        "orientation": "Hold each original sloped front panel-bearing face fixed; extend its 38.1-mm section toward rear (-Y,-Z) to 90.4748 mm; retain x=±120 mm inner cuts.",
        "protected_axis_count": len(protected),
        "retained_frame_axis_count": len(frame_rows),
        "fixed_panel_outline_count": len(panels),
        "changed_rail_count": len(names),
        "rail_front_normal_yz": normals,
        "rail_receiver_thickness_mm": {n: RAIL_THICKNESS for n in names},
        "minimum_hl_receiver_thickness_mm": MIN_RECEIVER,
        "rail_bounds_mm": {n: bounds(s) for n, s in thick_rails.items()},
        "minimum_sampled_blank_envelope_mm": blanks,
        "listed_4x6_actual_stock_comparator_mm": stock,
        "listed_4x6_dimension_fit": stock_fit,
        "one_piece_cad_solid": {
            n: len(s.Solids()) == 1 for n, s in thick_rails.items()
        },
        "original_rail_wood_loss_mm3": original_loss,
        "protected_screw_receiver_loss_mm3": receiver_loss,
        "protected_screw_receiver_missing": receiver_missing,
        "rail_other_wood_clashes_mm3": rail_other_wood,
        "rail_panel_clashes_mm3": rail_panel,
        "rail_tongue_hardware_clashes_mm3": rail_hardware,
        "rail_protected_screw_clashes_mm3": rail_screws,
        "rail_existing_frame_axis_clashes_mm3": rail_frame,
        "rail_end_face_1mm_blockers_mm3": face_blockers,
        "failures": failures,
        "status": "rejected_installed_geometry_trial"
        if failures
        else "geometry_only_unqualified",
        "qualification": "Nominal CAD occupancy and sampled blank fit only. No rail bracket, bolt stack, tool access, delivered stock tolerance, bearing, capacity, or drilling claim.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_thick_rails(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
