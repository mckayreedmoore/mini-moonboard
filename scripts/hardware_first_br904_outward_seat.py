"""One nominal outward BR904 upper-center pose; never a drilling plan."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_br904_raised_seat import (
    BOLT,
    DRAWING,
    HOLE,
    PITCH,
    PLATE,
    PLAY,
    PRODUCT,
    SEAT_LENGTH,
    SEAT_NEAR,
    VERTICAL_LENGTH,
    VERTICAL_NEAR,
    WIDTH,
    _face_margins,
    _overlaps,
)
from scripts.hardware_first_center_hybrid import (
    AXES,
    POST_HALF,
    PRINCIPAL_CENTER,
    PRINCIPAL_WIDTH,
    ROOT,
    TOL,
    TOP,
    bore,
    bounds,
    box,
    cylinder,
    hits,
)
from scripts.hardware_first_center_hybrid_toe import _principal

OUTPUT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_br904_outward_seat.json"
Y_CENTER = -100.0
HEADER_HALF_RAISE = 230.0
RAIL_END = 210.0  # 7.16 mm beyond the ideal outward seat end


def _pair_hits(shapes, *, skip_same_angle=False):
    found = {}
    items = list(shapes.items())
    for i, (name, solid) in enumerate(items):
        for other_name, other in items[i + 1:]:
            if skip_same_angle and name.rsplit("_", 1)[0] == other_name.rsplit("_", 1)[0]:
                continue
            volume = solid.intersect(other).Volume()
            if volume > TOL:
                found[f"{name} / {other_name}"] = round(volume, 3)
    return found


def _wood(raw):
    hb = raw["base_header"].BoundingBox()
    header = raw["base_header"].fuse(
        box(-HEADER_HALF_RAISE, hb.ymin, hb.zmin, 2 * HEADER_HALF_RAISE,
            hb.ymax - hb.ymin, TOP - hb.zmin)
    ).clean()
    post = box(-POST_HALF, hb.ymin, 0, 2 * POST_HALF, hb.ymax - hb.ymin, hb.zmin)
    principals = {
        f"base_principal_center_{side}": _principal(side) for side in ("left", "right")
    }
    rails = {}
    for side in ("left", "right"):
        for level in ("bottom", "service_lower", "service_upper"):
            name = f"base_rail_{level}_{side}"
            original = raw[name]
            b = original.BoundingBox()
            x0, x1 = ((b.xmin - 1, -RAIL_END) if side == "left"
                      else (RAIL_END, b.xmax + 1))
            rails[name] = original.intersect(
                box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2)
            ).clean()
    wood = {"base_header": header, "base_post_center": post, **principals, **rails}
    replaced = {
        "base_header", "base_post_center_left", "base_post_center_right", *principals, *rails
    }
    return wood, replaced, hb


def _hardware(wood, hb):
    plates = {}
    bores = {}
    paths = {}
    principal_filters = {}
    header_filters = {}
    y0 = Y_CENTER - WIDTH / 2
    for side, center in (("left", -PRINCIPAL_CENTER), ("right", PRINCIPAL_CENTER)):
        sign = -1 if side == "left" else 1
        outer = center + sign * PRINCIPAL_WIDTH / 2
        member = f"base_principal_center_{side}"
        plate = f"upper_{side}_vertical"
        seat = f"upper_{side}_seat"
        plate_x = outer - PLATE if sign < 0 else outer
        seat_x = outer - SEAT_LENGTH if sign < 0 else outer
        plates[plate] = box(plate_x, y0, TOP, PLATE, WIDTH, VERTICAL_LENGTH)
        plates[seat] = box(seat_x, y0, TOP, SEAT_LENGTH, WIDTH, PLATE)
        for i, z in enumerate((TOP + VERTICAL_NEAR, TOP + VERTICAL_NEAR + PITCH), 1):
            key = f"upper_{side}_principal_{i}"
            # Full wood bore; bolt path continues through its outer plate.
            bores[key] = (member, bore((center - PRINCIPAL_WIDTH / 2, Y_CENTER, z),
                                        (1, 0, 0), PRINCIPAL_WIDTH))
            paths[key] = bore((min(center - PRINCIPAL_WIDTH / 2, plate_x), Y_CENTER, z),
                              (1, 0, 0), PRINCIPAL_WIDTH + PLATE)
            principal_filters[key] = _face_margins(wood[member], Y_CENTER, z)
        for i, x in enumerate((outer + sign * SEAT_NEAR,
                                outer + sign * (SEAT_NEAR + PITCH)), 1):
            key = f"upper_{side}_header_{i}"
            bores[key] = ("base_header", bore((x, Y_CENTER, hb.zmin),
                                               (0, 0, 1), TOP - hb.zmin))
            paths[key] = bore((x, Y_CENTER, hb.zmin), (0, 0, 1), TOP - hb.zmin + PLATE)
            header_filters[key] = {
                "rear_4d_play_margin_mm": round(Y_CENTER - hb.ymin - 4 * BOLT - PLAY, 3),
                "front_4d_play_margin_mm": round(hb.ymax - Y_CENTER - 4 * BOLT - PLAY, 3),
                "raised_shoulder_3_5d_play_margin_mm": round(
                    HEADER_HALF_RAISE - abs(x) - 3.5 * BOLT - PLAY, 3
                ),
            }
    return plates, bores, paths, principal_filters, header_filters


def screen_outward_seat():
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
    wood, replaced, hb = _wood(raw)
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
    # A bolt should pass its own nominal hole, while foreign plates stay clear.
    intended = {}
    foreign = {}
    for name, path in paths.items():
        side = name.split("_")[1]
        own_plate = f"upper_{side}_{'vertical' if 'principal' in name else 'seat'}"
        intended[name] = round(path.intersect(plates[own_plate]).Volume(), 3)
        clash = hits(path, {n: s for n, s in plates.items() if n != own_plate})
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
        "status": "rejected_nominal_geometry" if failures else "geometry_only_unqualified",
        "product_id": "Newhouse/Adamax BR904; Home Depot 325186317",
        "product_source": PRODUCT,
        "nominal_drawing": DRAWING,
        "drawing_limit": "Retailer nominal rounded dimensions; bend datum and delivered tolerances unverified. Newhouse published 9/16-in hole and 1-7/8-in pitch used for occupied axes. No AB205 dimensions.",
        "width_option": KERF_RIGHT,
        "source_axes": str(AXES.relative_to(ROOT)),
        "upper_y_center_mm": Y_CENTER,
        "upper_bracket_count": 2,
        "fixed_panel_kicker_axis_count": len(panel_rows),
        "fixed_panel_solid_count": len(panels),
        "existing_frame_axis_count": len(frame_rows),
        "wood_bore_count": len(bores),
        "bolt_path_count": len(paths),
        "nominal_mm": {
            "plate_width": round(WIDTH, 3), "plate_thickness": round(PLATE, 3),
            "factory_hole_diameter": HOLE, "factory_pitch": PITCH,
            "vertical_near": round(VERTICAL_NEAR, 3),
            "seat_near": round(SEAT_NEAR, 3),
            "vertical_length": round(VERTICAL_LENGTH, 3),
            "horizontal_length_to_outer_bend": round(SEAT_LENGTH, 3),
            "bolt_path_diameter": BOLT, "factory_hole_radial_play": round(PLAY, 5),
        },
        "header_raised_half_width_mm": HEADER_HALF_RAISE,
        "rail_inner_end_abs_x_mm": RAIL_END,
        "changed_wood_bounds_mm": {n: bounds(s) for n, s in wood.items()},
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
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
        "filter_limit": "Principal oblique ray 3.5D and reversible 4D transverse edge markers include nominal hole play; header 4D Y-edge and raised shoulder 3.5D markers are search filters, not classified NDS acceptance.",
        "unresolved": ["delivered BR904 identity and tolerance", "bend geometry and minimum plate thickness", "bolt head, washer, nut, tool and withdrawal clearance", "wood end/edge classification and resistance", "lower post/header bracket and complete joint load path", "prefabricated rail-to-center connection after resection"],
        "material_or_rating_adopted": False,
        "drilling_released": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_outward_seat(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
