"""Local rail resection screen for the fixed hybrid HL35 pose; never drill data."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hybrid import (
    AXES,
    PRINCIPAL_CENTER,
    PRINCIPAL_WIDTH,
    REACH,
    ROOT,
    TOL,
    TOP,
    blank_envelope,
    bounds,
    box,
    cylinder,
    hits,
    screen_hybrid,
)

RAIL_END_X = 120.0  # Clears the outermost ideal upper vertical plate by 1 mm.


def screen_rails():
    baseline = screen_hybrid()
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [row for row in rows if row["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [row for row in rows if row["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len({row["name"] for row in panel_rows}) != 66:
        raise ValueError("expected 66 distinct fixed panel/kicker axes")
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    hb = raw["base_header"].BoundingBox()
    rear, front = hb.ymin, hb.ymax
    receivers = dict(raw)
    receivers["base_header"] = (
        raw["base_header"]
        .fuse(
            box(-230, rear - REACH, hb.zmin, 460, front - rear + REACH, TOP - hb.zmin)
        )
        .clean()
    )
    post = box(-92.075, rear, 0, 184.15, front - rear, hb.zmin)
    receivers["base_post_center_left"] = post
    receivers["base_post_center_right"] = post
    principals = {}
    for side, center in (("left", -PRINCIPAL_CENTER), ("right", PRINCIPAL_CENTER)):
        name = f"base_principal_center_{side}"
        original = raw[name]
        spread = (PRINCIPAL_WIDTH - 38.1) / 2
        widened = original.fuse(
            original.translate((-spread, 0, 0)),
            original.translate((spread, 0, 0)),
        ).clean()
        b = widened.BoundingBox()
        principals[name] = widened.intersect(
            box(b.xmin - 1, b.ymin - 1, TOP, b.xlen + 2, b.ylen + 2, b.zmax - TOP + 2)
        ).clean()
        receivers[name] = principals[name]

    plates = {
        n: box(b[0], b[2], b[4], b[1] - b[0], b[3] - b[2], b[5] - b[4])
        for n, b in baseline["plate_bounds_mm"].items()
    }
    rail_names = tuple(
        f"base_rail_{level}_{side}"
        for side in ("left", "right")
        for level in ("bottom", "service_lower", "service_upper")
    )
    rails = {}
    for name in rail_names:
        b = raw[name].BoundingBox()
        x0, x1 = (
            (b.xmin - 1, -RAIL_END_X)
            if name.endswith("left")
            else (RAIL_END_X, b.xmax + 1)
        )
        # A single end-plane cut preserves the original rail section.
        rails[name] = (
            raw[name]
            .intersect(box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2))
            .clean()
        )
        receivers[name] = rails[name]

    screw_receiver_loss = {}
    screw_receiver_missing = {}
    assigned = {name: [] for name in rail_names}
    retained_volume = {}
    for row in panel_rows:
        name, member = row["name"], row["second_member"]
        if member not in receivers:
            raise ValueError(f"unknown fixed screw receiver: {member}")
        screw = cylinder(row)
        old = screw.intersect(raw[member]).Volume()
        new = screw.intersect(receivers[member]).Volume()
        if old - new > TOL:
            screw_receiver_loss[name] = round(old - new, 3)
        if new <= TOL:
            screw_receiver_missing[name] = member
        if member in assigned:
            assigned[member].append(name)
            retained_volume[name] = round(new, 3)

    rail_panel = {n: hits(s, panels) for n, s in rails.items()}
    original_principal = {n: hits(raw[n], principals) for n in rails}
    original_plate = {n: hits(raw[n], plates) for n in rails}
    rail_principal = {n: hits(s, principals) for n, s in rails.items()}
    rail_plate = {n: hits(s, plates) for n, s in rails.items()}
    frame = {row["name"]: cylinder(row) for row in frame_rows}
    frame_rail = {n: hits(s, rails) for n, s in frame.items()}
    one_piece = {n: len(s.Solids()) == 1 for n, s in rails.items()}
    blanks = {n: blank_envelope(s, True) for n, s in rails.items()}
    screw_min = {
        n: min(retained_volume[screw] for screw in names) if names else 0
        for n, names in assigned.items()
    }
    feasible = (
        all(len(names) == 2 for names in assigned.values())
        and not screw_receiver_loss
        and not screw_receiver_missing
        and not any(rail_panel.values())
        and not any(rail_principal.values())
        and not any(rail_plate.values())
        and not any(frame_rail.values())
        and all(one_piece.values())
    )
    return {
        "status": "rail_geometry_feasible_only"
        if feasible
        else "rejected_rail_geometry",
        "source": str(AXES.relative_to(ROOT)),
        "parent_status": baseline["status"],
        "protected_axis_count": len(panel_rows),
        "changed_rail_count": len(rails),
        "resection": "Original rail solids retained outward of X = ±120 mm; one planar inner-end cut each. Axes and raw panels fixed.",
        "rail_bounds_mm": {n: bounds(s) for n, s in rails.items()},
        "original_rail_bounds_mm": {n: bounds(raw[n]) for n in rails},
        "rail_one_piece_cad_solid": one_piece,
        "rail_assigned_screws": assigned,
        "rail_screw_receiver_volume_mm3": retained_volume,
        "rail_screw_receiver_min_mm3": screw_min,
        "protected_receiver_loss_mm3": screw_receiver_loss,
        "protected_receiver_missing": screw_receiver_missing,
        "rail_panel_clashes_mm3": {n: v for n, v in rail_panel.items() if v},
        "original_rail_principal_clashes_mm3": original_principal,
        "original_rail_plate_clashes_mm3": original_plate,
        "rail_principal_clashes_mm3": {n: v for n, v in rail_principal.items() if v},
        "rail_plate_clashes_mm3": {n: v for n, v in rail_plate.items() if v},
        "existing_frame_axis_rail_clashes_mm3": {
            n: v for n, v in frame_rail.items() if v
        },
        "minimum_sampled_rail_blank_envelope_mm": blanks,
        "blank_method": "X length and minimum sampled Y/Z rotation at 0.1 degree; geometric bound, no machining allowance.",
        "outer_plate_to_rail_end_clearance_mm": 1.0,
        "principal_to_rail_end_gap_mm": 5.55,
        "unresolved": [
            "A prefabricated rail-to-center connection and load path across the 5.55-mm end gap are not established.",
            "The parent hybrid still has upper principal toe bore exits and other unresolved installed-hardware checks.",
            "Delivered timber, cuts, edge distances, screw embedment and capacity are unverified.",
        ],
        "qualification": "CAD occupancy only. Fixed axes are not drilling coordinates; no lap, custom steel, or capacity claim.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_rails(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
