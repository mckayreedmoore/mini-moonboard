"""One-piece deep principal test for the nominal outward BR904 upper pose."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_br904_outward_seat import (
    OUTPUT as PARENT_REPORT,
)
from scripts.hardware_first_br904_outward_seat import (
    Y_CENTER,
    _hardware,
    _pair_hits,
    _wood,
)
from scripts.hardware_first_br904_raised_seat import (
    BOLT,
    DRAWING,
    HOLE,
    PITCH,
    PLAY,
    PRODUCT,
    _overlaps,
)
from scripts.hardware_first_center_hybrid import (
    AXES,
    ROOT,
    TOL,
    blank_envelope,
    bounds,
    cylinder,
    hits,
)

OUTPUT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_br904_deep_principal.json"
DEEPENING = 60.0
BIG_BOX_LISTING = "https://www.homedepot.com/p/202533687"
BIG_BOX_ACTUAL_MM = [88.9, 241.3, 3657.6]  # HD nominal 4x10x12: actual 3.5x9.5x144 in


def _deep_wood(raw):
    wood, replaced, hb = _wood(raw)
    original_principals = {}
    for side in ("left", "right"):
        name = f"base_principal_center_{side}"
        original = wood[name]
        original_principals[name] = original
        # Union defines a single machinable blank/profile, never assembled plies.
        wood[name] = original.fuse(original.translate((0, -DEEPENING, 0))).clean()
        if len(wood[name].Solids()) != 1:
            raise ValueError(f"rearward profile is not one solid: {name}")
    return wood, replaced, hb, original_principals


def screen_deep_principal():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len({r["name"] for r in panel_rows}) != 66:
        raise ValueError("expected 66 fixed panel/kicker axes")
    if len(frame_rows) != 12 or len({r["name"] for r in frame_rows}) != 12:
        raise ValueError("expected 12 existing frame axes")
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    wood, replaced, hb, original_principals = _deep_wood(raw)
    adjacent = {n: s for n, s in raw.items() if n not in panels and n not in replaced}
    plates, bores, paths, principal_filters, header_filters = _hardware(wood, hb)
    bore_solids = {n: s for n, (_, s) in bores.items()}
    screws = {r["name"]: cylinder(r) for r in panel_rows}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    receivers = dict(raw)
    receivers.update(wood)
    for side in ("left", "right"):
        receivers[f"base_post_center_{side}"] = wood["base_post_center"]
    receiver_loss = {}
    for row in panel_rows:
        name, member = row["name"], row["second_member"]
        original = screws[name].intersect(raw[member]).Volume()
        current = screws[name].intersect(receivers[member]).Volume()
        if original - current > TOL or current <= TOL:
            receiver_loss[name] = round(original - current, 3)
    frame_receiver_changed = sorted({
        row["name"] for row in frame_rows
        if row["first_member"] in replaced or row["second_member"] in replaced
    })
    kicker = {
        n: round(s.intersect(wood["base_post_center"]).Volume(), 3)
        for n, s in screws.items()
        if n.startswith("round_kicker_") and "_center_" in n
    }
    missing = {
        n: round(max(0, solid.Volume() - solid.intersect(wood[member]).Volume()), 3)
        for n, (member, solid) in bores.items()
    }
    intended = {}
    foreign = {}
    for name, path in paths.items():
        side = name.split("_")[1]
        own = f"upper_{side}_{'vertical' if 'principal' in name else 'seat'}"
        intended[name] = round(path.intersect(plates[own]).Volume(), 3)
        clash = hits(path, {n: s for n, s in plates.items() if n != own})
        if clash:
            foreign[name] = clash
    bolt_other_wood = {}
    for name, path in paths.items():
        member = bores[name][0]
        found = hits(path, {**adjacent, **{n: s for n, s in wood.items() if n != member}})
        if found:
            bolt_other_wood[name] = found
    checks = {
        "plate_panel": _overlaps(plates, panels),
        "plate_wood": _overlaps(plates, wood),
        "plate_adjacent": _overlaps(plates, adjacent),
        "bolt_path_panel": _overlaps(paths, panels),
        "bolt_path_other_wood": bolt_other_wood,
        "bolt_path_other_plate": foreign,
        "fixed_screw_hardware": _overlaps(screws, {**plates, **bore_solids}),
        "frame_axis_hardware": _overlaps(frame, {**plates, **bore_solids}),
        "changed_wood_panel": _overlaps(wood, panels),
        "changed_wood_adjacent": _overlaps(wood, adjacent),
        "changed_wood_pairs": _pair_hits(wood),
        "independent_plate_pairs": _pair_hits(plates, skip_same_angle=True),
        "independent_bore_pairs": _pair_hits(bore_solids),
    }
    blanks = {name: blank_envelope(shape, True) for name, shape in wood.items()
              if name in original_principals}
    bounds_fit = {name: all(a <= b + TOL for a, b in zip(sorted(blank),
                  sorted(BIG_BOX_ACTUAL_MM))) for name, blank in blanks.items()}
    failures = [name for name, clash in checks.items() if clash]
    if any(v > TOL for v in missing.values()):
        failures.append("bore_exits_receiving_wood")
    if any(v <= TOL for v in intended.values()):
        failures.append("missing_intended_plate_hole_path")
    if receiver_loss:
        failures.append("fixed_screw_receiver_loss")
    if frame_receiver_changed:
        failures.append("frame_axis_receiver_changed")
    if len(kicker) != 4 or any(v <= TOL for v in kicker.values()):
        failures.append("kicker_seam_receiver")
    if not all(len(shape.Solids()) == 1 for shape in wood.values()):
        failures.append("one_piece_wood")
    if any(v["oblique_toe_3_5d_play_margin_mm"] < 0 or
           min(v["transverse_4d_play_margins_mm"]) < 0
           for v in principal_filters.values()):
        failures.append("principal_wood_search_filter")
    if any(min(v.values()) < 0 for v in header_filters.values()):
        failures.append("header_wood_search_filter")
    return {
        "status": "rejected_nominal_geometry" if failures else "geometry_only_stock_unverified",
        "parent_report": str(PARENT_REPORT.relative_to(ROOT)),
        "product_id": "Newhouse/Adamax BR904; Home Depot 325186317",
        "product_source": PRODUCT,
        "nominal_drawing": DRAWING,
        "width_option": KERF_RIGHT,
        "source_axes": str(AXES.relative_to(ROOT)),
        "parent_upper_y_center_mm": Y_CENTER,
        "rearward_deepening_mm": DEEPENING,
        "factory_hole_diameter_mm": HOLE,
        "factory_pitch_mm": PITCH,
        "trial_bolt_diameter_mm": BOLT,
        "factory_hole_radial_play_mm": round(PLAY, 5),
        "fixed_panel_kicker_axis_count": len(panel_rows),
        "fixed_panel_solid_count": len(panels),
        "existing_frame_axis_count": len(frame_rows),
        "wood_bore_count": len(bores),
        "bolt_path_count": len(paths),
        "original_principal_bounds_mm": {n: bounds(s) for n, s in original_principals.items()},
        "changed_wood_bounds_mm": {n: bounds(s) for n, s in wood.items()},
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "principal_minimum_sampled_blank_mm": blanks,
        "blank_method": "Minimum Y/Z bounding rectangle sampled every 0.1 degree, plus X extent; no trim, defects, straightness, or machining allowance.",
        "ordinary_big_box_example": {
            "listing": BIG_BOX_LISTING,
            "listed_actual_envelope_mm": BIG_BOX_ACTUAL_MM,
            "geometric_envelope_fit_only": bounds_fit,
            "status": "Dimensional lead only. Listing says Fir, not an adopted DF-L grade. Verify species-grade stamp and delivered stock before any DF-L input adoption; local availability, dimensions, defect-free yield, transport, full-length machining, and cutting allowance remain unverified.",
        },
        "ordinary_big_box_blank_verified": False,
        "bore_missing_receiver_wood_mm3": missing,
        "intended_plate_bolt_path_overlap_mm3": intended,
        "principal_wood_filters": principal_filters,
        "header_wood_filters": header_filters,
        "checks_mm3": checks,
        "fixed_screw_receiver_loss_mm3": receiver_loss,
        "frame_receiver_changed": frame_receiver_changed,
        "kicker_center_receivers_mm3": kicker,
        "kicker_seam_x_mm": -1.5875,
        "one_piece_cad_solid": {n: len(s.Solids()) == 1 for n, s in wood.items()},
        "failures": failures,
        "filter_limit": "3.5D oblique-toe and reversible 4D principal-edge plus factory-hole-play markers are nominal search filters, not classified NDS end/edge acceptance. The +2.313-mm principal and +2.361-mm header shoulder minima are not tolerance-qualified.",
        "unresolved": ["delivered BR904 bend and hole tolerances", "actual complete bolt stacks and access", "wood end/edge classification and joint resistance", "verified ordinary one-piece blanks", "lower post/header bracket and full frame load path", "rail-to-center prefabricated connections after trimming"],
        "material_or_rating_adopted": False,
        "drilling_released": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_deep_principal(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
