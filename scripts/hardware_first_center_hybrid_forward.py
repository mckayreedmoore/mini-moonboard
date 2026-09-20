"""One nominal 15-mm-forward HL35 center trial; never drilling data."""

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
    PRINCIPAL_CENTER,
    PRINCIPAL_WIDTH,
    REACH,
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

SHIFT = 15.0
RAIL_END_X = 120.0


def _nonempty_hits(shapes, others):
    return {
        name: found for name, solid in shapes.items() if (found := hits(solid, others))
    }


def screen_forward():
    """Screen only this nominal pose against fixed panels, wood and axes."""
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len({r["name"] for r in panel_rows}) != 66:
        raise ValueError("expected 66 distinct protected panel/kicker axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 existing frame axes")
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    hb = raw["base_header"].BoundingBox()
    rear, front = hb.ymin, hb.ymax
    upper_y0 = rear + SHIFT
    extension_mm = max(0.0, upper_y0 + LENGTH - front)
    if abs(extension_mm - 2.3) > TOL:
        raise ValueError("unexpected header seat extension")

    # The extension is confined to the existing central raised header region.
    extension = box(-230, front, hb.zmin, 460, extension_mm, TOP - hb.zmin)
    header = (
        raw["base_header"]
        .fuse(
            box(-230, rear - REACH, hb.zmin, 460, front - rear + REACH, TOP - hb.zmin),
            extension,
        )
        .clean()
    )
    post = box(-POST_HALF, rear, 0, 2 * POST_HALF, front - rear, hb.zmin)
    principals = {
        f"base_principal_center_{side}": _principal(side) for side in ("left", "right")
    }
    center = {"base_header": header, "base_post_center": post, **principals}
    rails = {}
    for side in ("left", "right"):
        for level in ("bottom", "service_lower", "service_upper"):
            name = f"base_rail_{level}_{side}"
            original = raw[name]
            b = original.BoundingBox()
            x0, x1 = (
                (b.xmin - 1, -RAIL_END_X)
                if side == "left"
                else (RAIL_END_X, b.xmax + 1)
            )
            rails[name] = original.intersect(
                box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2)
            ).clean()
    changed_wood = {**center, **rails}
    replaced = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        *principals,
        *rails,
    }
    adjacent = {n: s for n, s in raw.items() if n not in panels and n not in replaced}

    plates = {
        "lower_vertical": box(
            -LENGTH / 2, rear - PLATE, hb.zmin - REACH, LENGTH, PLATE, REACH
        ),
        "lower_seat": box(
            -LENGTH / 2, rear - REACH, hb.zmin - PLATE, LENGTH, REACH, PLATE
        ),
    }
    bores = {}
    for i, x in enumerate((-31.75, 31.75), 1):
        bores[f"lower_post_{i}"] = (
            "base_post_center",
            bore((x, rear, hb.zmin - 50.8), (0, 1, 0), front - rear),
        )
        bores[f"lower_header_{i}"] = (
            "base_header",
            bore((x, rear - 50.8, hb.zmin), (0, 0, 1), TOP - hb.zmin),
        )
    for side, xcenter in (("left", -PRINCIPAL_CENTER), ("right", PRINCIPAL_CENTER)):
        outer = xcenter + (
            -PRINCIPAL_WIDTH / 2 if side == "left" else PRINCIPAL_WIDTH / 2
        )
        x0 = outer - PLATE if side == "left" else outer
        seat_x = outer - REACH if side == "left" else outer
        plates[f"upper_{side}_vertical"] = box(x0, upper_y0, TOP, PLATE, LENGTH, REACH)
        plates[f"upper_{side}_seat"] = box(seat_x, upper_y0, TOP, REACH, LENGTH, PLATE)
        hx = outer + (-50.8 if side == "left" else 50.8)
        for i, y in enumerate((upper_y0 + 31.75, upper_y0 + 95.25), 1):
            bores[f"upper_{side}_principal_{i}"] = (
                f"base_principal_center_{side}",
                bore(
                    (xcenter - PRINCIPAL_WIDTH / 2, y, TOP + 50.8),
                    (1, 0, 0),
                    PRINCIPAL_WIDTH,
                ),
            )
            bores[f"upper_{side}_header_{i}"] = (
                "base_header",
                bore((hx, y, hb.zmin), (0, 0, 1), TOP - hb.zmin),
            )
    bore_solids = {n: solid for n, (_, solid) in bores.items()}
    missing = {
        n: round(
            max(0, solid.Volume() - solid.intersect(changed_wood[member]).Volume()), 3
        )
        for n, (member, solid) in bores.items()
    }
    screws = {r["name"]: cylinder(r) for r in panel_rows}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    receivers = dict(raw)
    receivers["base_header"] = header
    receivers["base_post_center_left"] = post
    receivers["base_post_center_right"] = post
    receivers.update(principals)
    receivers.update(rails)
    receiver_loss = {}
    receiver_missing = {}
    for row in panel_rows:
        name, member = row["name"], row["second_member"]
        if member not in receivers:
            raise ValueError(f"unknown protected receiver: {member}")
        old = screws[name].intersect(raw[member]).Volume()
        new = screws[name].intersect(receivers[member]).Volume()
        if old - new > TOL:
            receiver_loss[name] = round(old - new, 3)
        if new <= TOL:
            receiver_missing[name] = member

    wood_panel = _nonempty_hits(changed_wood, panels)
    wood_adjacent = _nonempty_hits(changed_wood, adjacent)
    plate_panel = _nonempty_hits(plates, panels)
    plate_adjacent = _nonempty_hits(plates, adjacent)
    plate_wood = _nonempty_hits(plates, changed_wood)
    screw_hardware = _nonempty_hits(screws, {**plates, **bore_solids})
    frame_hardware = _nonempty_hits(frame, {**plates, **bore_solids})
    # Existing frame axes through changed timber are retained as observations,
    # since their complete installed bolt stacks are outside this screen.
    frame_wood = _nonempty_hits(frame, changed_wood)
    failures = []
    for name, failed in (
        ("header extension intersects fixed panels", bool(hits(extension, panels))),
        ("changed wood intersects panels", bool(wood_panel)),
        ("changed wood intersects adjacent wood", bool(wood_adjacent)),
        (
            "ideal plate intersects panel or unintended wood",
            bool(plate_panel or plate_adjacent or plate_wood),
        ),
        ("protected screw intersects plate or bore", bool(screw_hardware)),
        ("protected screw receiver lost", bool(receiver_loss or receiver_missing)),
        ("existing frame axis intersects new hardware", bool(frame_hardware)),
        ("nominal bore exits receiving wood", any(v > TOL for v in missing.values())),
        (
            "changed timber is disconnected",
            not all(len(s.Solids()) == 1 for s in changed_wood.values()),
        ),
    ):
        if failed:
            failures.append(name)
    return {
        "status": "rejected_nominal_geometry_trial"
        if failures
        else "geometry_only_unqualified",
        "source": str(AXES.relative_to(ROOT)),
        "width_option": KERF_RIGHT,
        "upper_shift_mm": SHIFT,
        "header_forward_extension_mm": round(extension_mm, 4),
        "protected_axis_count": len(panel_rows),
        "existing_frame_axis_count": len(frame_rows),
        "changed_rail_count": len(rails),
        "changed_wood_bounds_mm": {n: bounds(s) for n, s in changed_wood.items()},
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "header_extension_panel_clashes_mm3": hits(extension, panels),
        "changed_wood_panel_clashes_mm3": wood_panel,
        "changed_wood_adjacent_clashes_mm3": wood_adjacent,
        "plate_panel_clashes_mm3": plate_panel,
        "plate_adjacent_clashes_mm3": plate_adjacent,
        "plate_changed_wood_clashes_mm3": plate_wood,
        "protected_screw_hardware_clashes_mm3": screw_hardware,
        "protected_receiver_loss_mm3": receiver_loss,
        "protected_receiver_missing": receiver_missing,
        "existing_frame_axis_hardware_clashes_mm3": frame_hardware,
        "existing_frame_axis_changed_wood_intersections_mm3": frame_wood,
        "bore_missing_receiver_wood_mm3": missing,
        "one_piece_cad_solid": {
            n: len(s.Solids()) == 1 for n, s in changed_wood.items()
        },
        "failures": failures,
        "unresolved": [
            "Prefabricated rail-to-center connection and load path across the nominal 5.55-mm rail gap.",
            "Other frame bolts and complete installed bolt stacks, heads, washers, nuts, tool and withdrawal clearance.",
            "Delivered HL35 hole/bend geometry, wood edge/end distances, blank procurement and machinability.",
            "Connector and bolt capacities; no cutting, drilling or procurement approval.",
        ],
        "qualification": "Ideal 4.55-mm plate rectangles and 14.2875-mm bore envelopes; occupied screw axes are analysis geometry, never drilling coordinates.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_forward(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
