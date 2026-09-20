"""Nominal BR904 raised-seat screen; source dimensions are not drill coordinates."""

import argparse
import csv
import json
from math import hypot
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.bolted_candidate_ab205_center_fit import (
    _grain_edge_lines,
    _grain_ray_to_face_boundary,
    _line_y,
    _principal_broad_face,
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

OUTPUT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_br904_raised_seat.json"
DRAWING = "https://mobileimages.lowes.com/productimages/d634d853-f9cd-473c-9904-e170613fa268/66922570.jpeg"
PRODUCT = "https://www.homedepot.com/p/325186317"
INCH = 25.4
WIDTH = 1.57 * INCH
PLATE = 0.24 * INCH  # retailer nominal drawing, no minimum thickness claim
HOLE = 9 / 16 * INCH  # Newhouse advertised; drawing rounds to 0.55 in
PITCH = 1.875 * INCH  # Newhouse advertised; drawing rounds to 1.87 in
VERTICAL_NEAR = (4.13 - 0.81 - 1.87) * INCH
SEAT_NEAR = (3.48 - 0.81 - 1.87) * INCH
VERTICAL_LENGTH = 4.13 * INCH
SEAT_LENGTH = 3.48 * INCH
BOLT = 12.7
PLAY = (HOLE - BOLT) / 2
RAIL_END = 121.0
Y_CENTERS = (-100.0, -70.0, -56.0)


def _overlaps(shapes, targets):
    return {name: found for name, solid in shapes.items() if (found := hits(solid, targets))}


def _face_margins(principal, y, z):
    """Measure principal rays on its actual sloped broad-face boundary."""
    face = _principal_broad_face(principal, principal.BoundingBox().xmin)
    lines = _grain_edge_lines(face)
    if len(lines) != 2 or abs(lines[0][2] - lines[1][2]) > 1e-6:
        raise ValueError("expected two parallel principal grain edges")
    slope = lines[0][2]
    unit_z = 1 / hypot(1, slope)
    lower, upper = sorted(_line_y(line, z) for line in lines)
    # Follow the actual shaped broad-face polygon to the oblique end.
    toe, _, _ = _grain_ray_to_face_boundary(face, y, z, slope)
    return {
        "oblique_toe_ray_mm": round(toe, 3),
        "oblique_toe_3_5d_play_margin_mm": round(toe - 3.5 * BOLT - PLAY, 3),
        "transverse_edges_mm": [round((y - lower) * unit_z, 3), round((upper - y) * unit_z, 3)],
        "transverse_4d_play_margins_mm": [
            round((y - lower) * unit_z - 4 * BOLT - PLAY, 3),
            round((upper - y) * unit_z - 4 * BOLT - PLAY, 3),
        ],
    }


def _pose(y_center, raw, panels, panel_rows, frame_rows):
    hb = raw["base_header"].BoundingBox()
    rear, front = hb.ymin, hb.ymax
    lower_rear = rear - SEAT_LENGTH
    # CAD union denotes one shaped timber. Seat and pedestal stay behind Y=-36.
    header = raw["base_header"].fuse(
        box(-230, lower_rear, hb.zmin, 460, front - lower_rear, TOP - hb.zmin)
    ).clean()
    post = box(-POST_HALF, rear, 0, 2 * POST_HALF, front - rear, hb.zmin)
    principals = {
        f"base_principal_center_{side}": _principal(side) for side in ("left", "right")
    }
    rails = {}
    for side in ("left", "right"):
        for level in ("bottom", "service_lower", "service_upper"):
            name = f"base_rail_{level}_{side}"
            original = raw[name]
            b = original.BoundingBox()
            x0, x1 = (b.xmin - 1, -RAIL_END) if side == "left" else (RAIL_END, b.xmax + 1)
            rails[name] = original.intersect(
                box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2)
            ).clean()
    wood = {"base_header": header, "base_post_center": post, **principals, **rails}
    replaced = {
        "base_header", "base_post_center_left", "base_post_center_right", *principals, *rails
    }
    adjacent = {n: s for n, s in raw.items() if n not in replaced and n not in panels}

    plates = {}
    bores = {}
    margins = {}
    upper_header_filters = {}
    # Rear-facing post leg; the horizontal leg points rearward beneath header.
    plates["lower_vertical"] = box(-WIDTH / 2, rear - PLATE, hb.zmin - VERTICAL_LENGTH,
                                     WIDTH, PLATE, VERTICAL_LENGTH)
    plates["lower_seat"] = box(-WIDTH / 2, lower_rear, hb.zmin - PLATE,
                                 WIDTH, SEAT_LENGTH, PLATE)
    for i, z in enumerate((hb.zmin - VERTICAL_NEAR, hb.zmin - VERTICAL_NEAR - PITCH), 1):
        bores[f"lower_post_{i}"] = ("base_post_center", bore((0, rear, z),
                                                      (0, 1, 0), front - rear))
    for i, y in enumerate((rear - SEAT_NEAR, rear - SEAT_NEAR - PITCH), 1):
        bores[f"lower_header_{i}"] = ("base_header", bore((0, y, hb.zmin),
                                                       (0, 0, 1), TOP - hb.zmin))
    for side, center in (("left", -PRINCIPAL_CENTER), ("right", PRINCIPAL_CENTER)):
        sign = -1 if side == "left" else 1
        outer = center + sign * PRINCIPAL_WIDTH / 2
        name = f"base_principal_center_{side}"
        y0 = y_center - WIDTH / 2
        plates[f"upper_{side}_vertical"] = box(
            outer - PLATE if sign < 0 else outer, y0, TOP,
            PLATE, WIDTH, VERTICAL_LENGTH,
        )
        # Both seat legs point toward the center, with a clear central gap.
        plates[f"upper_{side}_seat"] = box(
            outer if sign < 0 else outer - SEAT_LENGTH, y0, TOP,
            SEAT_LENGTH, WIDTH, PLATE,
        )
        for i, z in enumerate((TOP + VERTICAL_NEAR, TOP + VERTICAL_NEAR + PITCH), 1):
            key = f"upper_{side}_principal_{i}"
            bores[key] = (name, bore((center - PRINCIPAL_WIDTH / 2, y_center, z),
                                     (1, 0, 0), PRINCIPAL_WIDTH))
            margins[key] = _face_margins(principals[name], y_center, z)
        for i, x in enumerate((outer - sign * SEAT_NEAR,
                                outer - sign * (SEAT_NEAR + PITCH)), 1):
            bores[f"upper_{side}_header_{i}"] = (
                "base_header", bore((x, y_center, hb.zmin), (0, 0, 1), TOP - hb.zmin)
            )
            upper_header_filters[f"upper_{side}_header_{i}"] = {
                "rear_4d_play_margin_mm": round(y_center - lower_rear - 4 * BOLT - PLAY, 3),
                "front_4d_play_margin_mm": round(front - y_center - 4 * BOLT - PLAY, 3),
                "raised_shoulder_3_5d_play_margin_mm": round(
                    230 - abs(x) - 3.5 * BOLT - PLAY, 3
                ),
            }

    bore_solids = {n: solid for n, (_, solid) in bores.items()}
    missing = {
        n: round(max(0, solid.Volume() - solid.intersect(wood[member]).Volume()), 3)
        for n, (member, solid) in bores.items()
    }
    screws = {r["name"]: cylinder(r) for r in panel_rows}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    receivers = dict(raw)
    receivers.update(wood)
    receivers["base_post_center_left"] = post
    receivers["base_post_center_right"] = post
    receiver_loss = {}
    for row in panel_rows:
        n, member = row["name"], row["second_member"]
        old = screws[n].intersect(raw[member]).Volume()
        new = screws[n].intersect(receivers[member]).Volume()
        if old - new > TOL or new <= TOL:
            receiver_loss[n] = round(old - new, 3)
    kicker = {
        n: round(s.intersect(post).Volume(), 3) for n, s in screws.items()
        if n.startswith("round_kicker_") and "_center_" in n
    }
    hardware = {**plates, **bore_solids}
    plate_wood = _overlaps(plates, wood)
    plate_pairs = {}
    for i, (name, solid) in enumerate(plates.items()):
        for other_name, other in list(plates.items())[i + 1:]:
            if name.rsplit("_", 1)[0] == other_name.rsplit("_", 1)[0]:
                continue  # two legs of one ideal angle share a bend
            volume = solid.intersect(other).Volume()
            if volume > TOL:
                plate_pairs[f"{name} / {other_name}"] = round(volume, 3)
    bore_pairs = {}
    for i, (name, solid) in enumerate(bore_solids.items()):
        for other_name, other in list(bore_solids.items())[i + 1:]:
            volume = solid.intersect(other).Volume()
            if volume > TOL:
                bore_pairs[f"{name} / {other_name}"] = round(volume, 3)
    failures = []
    checks = {
        "plate_panel": _overlaps(plates, panels),
        "plate_adjacent": _overlaps(plates, adjacent),
        "plate_wood": plate_wood,
        "wood_panel": _overlaps(wood, panels),
        "wood_adjacent": _overlaps(wood, adjacent),
        "screw_hardware": _overlaps(screws, hardware),
        "frame_hardware": _overlaps(frame, hardware),
        "bore_panel": _overlaps(bore_solids, panels),
        "bore_adjacent": _overlaps(bore_solids, adjacent),
        "independent_plate_pairs": plate_pairs,
        "independent_bore_pairs": bore_pairs,
    }
    for label, result in checks.items():
        if result:
            failures.append(label)
    if any(v > TOL for v in missing.values()):
        failures.append("bore_exits_wood")
    if receiver_loss:
        failures.append("fixed_screw_receiver_loss")
    if len(kicker) != 4 or any(v <= TOL for v in kicker.values()):
        failures.append("kicker_seam_receiver")
    if not all(len(s.Solids()) == 1 for s in wood.values()):
        failures.append("one_piece_wood")
    if any(v["oblique_toe_3_5d_play_margin_mm"] < 0 or
           min(v["transverse_4d_play_margins_mm"]) < 0 for v in margins.values()):
        failures.append("principal_wood_search_filter")
    if any(min(v.values()) < 0 for v in upper_header_filters.values()):
        failures.append("upper_header_wood_search_filter")
    # These are centerline search filters only; actual NDS categories remain open.
    post_edge = min(VERTICAL_NEAR, hb.zmin - VERTICAL_NEAR - PITCH)
    header_y_edge = rear - SEAT_NEAR - PITCH - lower_rear
    lower_filters = {
        "post_vertical_end_3_5d_play_margin_mm": round(post_edge - 3.5 * BOLT - PLAY, 3),
        "header_rear_edge_4d_play_margin_mm": round(header_y_edge - 4 * BOLT - PLAY, 3),
        "post_x_edge_4d_play_margin_mm": round(POST_HALF - 4 * BOLT - PLAY, 3),
        "header_x_edge_4d_play_margin_mm": round(230 - 4 * BOLT - PLAY, 3),
    }
    if min(lower_filters.values()) < 0:
        failures.append("lower_wood_search_filter")
    return {
        "upper_y_center_mm": y_center,
        "status": "rejected_nominal_geometry" if failures else "geometry_only_unqualified",
        "failures": failures,
        "checks_mm3": checks,
        "bore_missing_receiver_wood_mm3": missing,
        "principal_wood_filters": margins,
        "upper_header_wood_filters": upper_header_filters,
        "lower_wood_filters": lower_filters,
        "fixed_screw_receiver_loss_mm3": receiver_loss,
        "kicker_center_receivers_mm3": kicker,
        "kicker_seam_x_mm": -1.5875,
        "one_piece_cad_solid": {n: len(s.Solids()) == 1 for n, s in wood.items()},
        "changed_wood_bounds_mm": {n: bounds(s) for n, s in wood.items()},
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "bore_count": len(bores),
    }


def screen_raised_seat():
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
    poses = [_pose(y, raw, panels, panel_rows, frame_rows) for y in Y_CENTERS]
    return {
        "status": "rejected_bounded_raised_seat" if all(p["failures"] for p in poses)
                  else "conditional_nominal_geometry_only",
        "product": "Newhouse/Adamax BR904; Home Depot internet #325186317",
        "product_source": PRODUCT,
        "retailer_nominal_drawing": DRAWING,
        "width_option": KERF_RIGHT,
        "source_axes": str(AXES.relative_to(ROOT)),
        "fixed_panel_kicker_axes": len(panel_rows),
        "existing_frame_axes": len(frame_rows),
        "fixed_panel_solids": len(panels),
        "factory_nominal_mm": {
            "plate_width": round(WIDTH, 3), "plate_thickness": round(PLATE, 3),
            "hole_diameter_advertised": HOLE, "pitch_advertised": PITCH,
            "vertical_near_from_drawing_arithmetic": round(VERTICAL_NEAR, 3),
            "horizontal_near_from_drawing_arithmetic": round(SEAT_NEAR, 3),
            "vertical_overall": round(VERTICAL_LENGTH, 3),
            "horizontal_to_outer_bend": round(SEAT_LENGTH, 3),
        },
        "drawing_interpretation": "Retailer drawing is nominal and rounded. Near-hole distances are arithmetic from overall, free-end inset and 1.87-in drawn pitch; bend datum and finished tolerances are unresolved. Advertised 1-7/8-in pitch and 9/16-in hole govern bore envelopes.",
        "assumed_bolt_diameter_mm": BOLT,
        "hole_radial_play_mm": round(PLAY, 5),
        "poses": poses,
        "identity_and_tolerance_gate": "Lowe's Adamax BR904 and Newhouse BR904 model identity is supported by manufacturer brand relationship, but delivered Home Depot lot and dimensions are unverified; drawing is not controlled manufacturing tolerance.",
        "wood_filter_limit": "3.5D oblique toe and 4D edge margins include nominal factory-hole radial play, but are search filters, not classified NDS acceptance. Lower end filters are simplified centerline proxies; other wood ends and load directions remain unresolved.",
        "unresolved": ["delivered bend datum and hole locations", "plate bend radius and true minimum thickness", "bolt stacks, washer seating and tool access", "complete wood end/edge classification and resistance", "connector/joint resistance and frame load path", "rail-to-center prefabricated connections and handling of one-piece blanks"],
        "material_or_rating_adopted": False,
        "drilling_released": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_raised_seat(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
