"""One independent-bolt HL33 backing topology; nominal occupancy only."""

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
    bore,
    bounds,
    box,
    cylinder,
)
from scripts.hardware_first_center_hybrid_toe import _principal
from scripts.hardware_first_center_tongue import pair_clashes
from scripts.hardware_first_hl33_common_core import (
    CATALOG,
    CORE_DEPTH,
    CORE_HALF,
    HOLE_INSET,
    MIN_BOLTED_WOOD,
    RAIL_END,
    _overlaps,
    _stack,
)

OUTPUT = (
    ROOT / "docs/bolted-candidate-prototypes/hardware_first_hl33_backing_revision.json"
)
REAR_EXTENSION = 65.0
BACKING_Z = {"left": 80.0, "right": 150.0}
RETAIL_URL = (
    "https://www.lowes.com/pd/Douglas-Fir-Lumber-Common-4-in-x-12-in-x-12-ft-"
    "Actual-3-562-in-x-11-5-in-x-12-ft/1000028845"
)
RETAIL_ENVELOPE_MM = [90.4748, 292.1, 3657.6]


def screen_backing_revision():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    protected = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(protected) != 66 or len({r["name"] for r in protected}) != 66:
        raise ValueError("expected 66 unique fixed screw axes")
    if len(frame_rows) != 12 or len({r["name"] for r in frame_rows}) != 12:
        raise ValueError("expected 12 unique frame axes")
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    hb = raw["base_header"].BoundingBox()
    rear, front, underside = hb.ymin - REAR_EXTENSION, hb.ymax, hb.zmin
    junction = rear + CORE_DEPTH
    core = box(-CORE_HALF, rear, 0, 2 * CORE_HALF, CORE_DEPTH, underside)
    backing = box(-CORE_HALF, junction, 0, 2 * CORE_HALF, front - junction, underside)
    # Local bracket slots preserve one solid backing; the flange is modeled
    # separately and cannot be credited by butt contact alone.
    for side, sign in (("left", -1), ("right", 1)):
        x0 = -CORE_HALF if sign < 0 else CORE_HALF - REACH
        backing = backing.cut(box(x0, junction, BACKING_Z[side], REACH, PLATE, LENGTH))
    backing = backing.clean()
    wood = {
        "core": core,
        "backing": backing,
        "header": raw["base_header"]
        .fuse(
            box(
                -230,
                rear - REACH,
                underside,
                460,
                front - rear + REACH,
                TOP - underside,
            )
        )
        .clean(),
    }
    for side in ("left", "right"):
        wood[f"base_principal_center_{side}"] = _principal(side)
    rail_names = tuple(
        f"base_rail_{level}_{side}"
        for side in ("left", "right")
        for level in ("bottom", "service_lower", "service_upper")
    )
    for name in rail_names:
        b = raw[name].BoundingBox()
        x0, x1 = (
            (b.xmin - 1, -RAIL_END) if name.endswith("left") else (RAIL_END, b.xmax + 1)
        )
        wood[name] = (
            raw[name]
            .intersect(box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2))
            .clean()
        )
    replaced = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
        *rail_names,
    }
    adjacent = {n: s for n, s in raw.items() if n not in panels and n not in replaced}

    plates, bores, paths, own, stacks, receiver = {}, {}, {}, {}, {}, {}

    def axis(name, member, point, direction, wood_length, start, path_length, plate):
        bores[name] = bore(point, direction, wood_length)
        paths[name] = bore(start, direction, path_length)
        own[name] = plate
        receiver[name] = member
        stacks[name] = _stack(start, direction, path_length)

    plates["lower_vertical"] = box(
        -LENGTH / 2, rear - PLATE, underside - REACH, LENGTH, PLATE, REACH
    )
    plates["lower_seat"] = box(
        -LENGTH / 2, rear - REACH, underside - PLATE, LENGTH, REACH, PLATE
    )
    axis(
        "lower_core",
        "core",
        (0, rear, underside - LEG_HOLE),
        (0, 1, 0),
        CORE_DEPTH,
        (0, rear - PLATE, underside - LEG_HOLE),
        CORE_DEPTH + PLATE,
        "lower_vertical",
    )
    axis(
        "lower_header",
        "header",
        (0, rear - HOLE_INSET, underside),
        (0, 0, 1),
        TOP - underside,
        (0, rear - HOLE_INSET, underside - PLATE),
        TOP - underside + PLATE,
        "lower_seat",
    )

    for side, sign in (("left", -1), ("right", 1)):
        center = sign * 70.0
        outer = center + sign * 44.45
        plate_x = outer - PLATE if sign < 0 else outer
        plates[f"upper_{side}_vertical"] = box(plate_x, -100, TOP, PLATE, LENGTH, REACH)
        plates[f"upper_{side}_seat"] = box(
            outer - REACH if sign < 0 else outer, -100, TOP, REACH, LENGTH, PLATE
        )
        axis(
            f"upper_{side}_principal",
            f"base_principal_center_{side}",
            (center - 44.45, -100 + ALONG_BEND, TOP + LEG_HOLE),
            (1, 0, 0),
            88.9,
            (min(center - 44.45, plate_x), -100 + ALONG_BEND, TOP + LEG_HOLE),
            88.9 + PLATE,
            f"upper_{side}_vertical",
        )
        hx = outer + sign * HOLE_INSET
        axis(
            f"upper_{side}_header",
            "header",
            (hx, -100 + ALONG_BEND, underside),
            (0, 0, 1),
            TOP - underside,
            (hx, -100 + ALONG_BEND, underside),
            TOP - underside + PLATE,
            f"upper_{side}_seat",
        )

    # Two staggered factory angles. Each transverse bolt passes through the
    # single backing timber only; no bolt connects both angles or three woods.
    for side, sign in (("left", -1), ("right", 1)):
        z0 = BACKING_Z[side]
        outer = sign * CORE_HALF
        plates[f"backing_{side}_core_leg"] = box(
            -CORE_HALF if sign < 0 else CORE_HALF - REACH,
            junction,
            z0,
            REACH,
            PLATE,
            LENGTH,
        )
        plates[f"backing_{side}_side_leg"] = box(
            outer - PLATE if sign < 0 else outer, junction, z0, PLATE, REACH, LENGTH
        )
        xhole = sign * (CORE_HALF - HOLE_INSET)
        axis(
            f"backing_{side}_core",
            "core",
            (xhole, rear, z0 + ALONG_BEND),
            (0, 1, 0),
            CORE_DEPTH,
            (xhole, rear, z0 + ALONG_BEND),
            CORE_DEPTH + PLATE,
            f"backing_{side}_core_leg",
        )
        bolt_y = junction + HOLE_INSET
        if sign < 0:
            start, direction = (-CORE_HALF - PLATE, bolt_y, z0 + ALONG_BEND), (1, 0, 0)
            wood_start = (-CORE_HALF, bolt_y, z0 + ALONG_BEND)
        else:
            start, direction = (CORE_HALF + PLATE, bolt_y, z0 + ALONG_BEND), (-1, 0, 0)
            wood_start = (CORE_HALF, bolt_y, z0 + ALONG_BEND)
        axis(
            f"backing_{side}_member",
            "backing",
            wood_start,
            direction,
            2 * CORE_HALF,
            start,
            2 * CORE_HALF + PLATE,
            f"backing_{side}_side_leg",
        )

    screws = {r["name"]: cylinder(r) for r in protected}
    long_screws = {r["name"]: cylinder(r, 63.5) for r in protected}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    receivers = dict(raw)
    receivers.update(wood)
    receivers.update(
        {
            "base_header": wood["header"],
            "base_post_center_left": backing,
            "base_post_center_right": backing,
        }
    )
    receiver_loss = {}
    for row in protected:
        name, member = row["name"], row["second_member"]
        old = screws[name].intersect(raw[member]).Volume()
        new = screws[name].intersect(receivers[member]).Volume()
        if old - new > TOL or new <= TOL:
            receiver_loss[name] = round(old - new, 3)
    kicker = {
        n: round(s.intersect(backing).Volume(), 3)
        for n, s in screws.items()
        if n.startswith("round_kicker_") and "_center_" in n
    }
    bore_missing = {
        n: round(
            max(0, solid.Volume() - solid.intersect(wood[receiver[n]]).Volume()), 3
        )
        for n, solid in bores.items()
    }
    backing_axes = [
        f"backing_{side}_{part}"
        for side in ("left", "right")
        for part in ("core", "member")
    ]
    backing_receivers = {
        n: [
            member
            for member, solid in wood.items()
            if bores[n].intersect(solid).Volume() > TOL
        ]
        for n in backing_axes
    }
    intended = {
        n: round(s.intersect(plates[own[n]]).Volume(), 3) for n, s in paths.items()
    }
    other_wood = {
        n: hit
        for n, s in paths.items()
        if (
            hit := _overlaps(
                {n: s},
                {**adjacent, **{k: v for k, v in wood.items() if k != receiver[n]}},
            )
        )
    }
    stack_shapes = {
        f"{n}_{part}": s for n, pieces in stacks.items() for part, s in pieces.items()
    }
    checks = {
        "wood_pairs": pair_clashes(wood),
        "wood_panel": _overlaps(wood, panels),
        "wood_adjacent": _overlaps(wood, adjacent),
        "plate_pairs": pair_clashes(plates, skip_same_angle=True),
        "plate_wood": _overlaps(plates, wood),
        "plate_panel": _overlaps(plates, panels),
        "plate_adjacent": _overlaps(plates, adjacent),
        "bore_pairs": pair_clashes(bores),
        "bolt_path_panel": _overlaps(paths, panels),
        "bolt_path_other_wood": other_wood,
        "bolt_path_other_plate": {
            n: hit
            for n, s in paths.items()
            if (
                hit := _overlaps(
                    {n: s}, {k: v for k, v in plates.items() if k != own[n]}
                )
            )
        },
        "fixed_screw_hardware": _overlaps(screws, {**plates, **bores}),
        "long_screw_hardware": _overlaps(long_screws, {**plates, **bores}),
        "frame_axis_hardware": _overlaps(frame, {**plates, **bores}),
        "stack_panel": _overlaps(stack_shapes, panels),
        "stack_other_wood": _overlaps(stack_shapes, wood),
        "stack_adjacent": _overlaps(stack_shapes, adjacent),
        "stack_plate": _overlaps(stack_shapes, plates),
        "stack_fixed_screw": _overlaps(stack_shapes, screws),
    }
    access = {
        k: checks[k]
        for k in (
            "stack_panel",
            "stack_other_wood",
            "stack_adjacent",
            "stack_plate",
            "stack_fixed_screw",
        )
        if checks[k]
    }
    receiver_thickness = {
        n: (
            CORE_DEPTH
            if n in ("lower_core", "backing_left_core", "backing_right_core")
            else 2 * CORE_HALF
            if n.endswith("_member")
            else 88.9
        )
        for n in bores
    }
    below = {
        n: round(MIN_BOLTED_WOOD - t, 4)
        for n, t in receiver_thickness.items()
        if t < MIN_BOLTED_WOOD - TOL
    }
    ordinary_blank = {
        n: [
            round(v, 4)
            for v in (s.BoundingBox().xlen, s.BoundingBox().ylen, s.BoundingBox().zlen)
        ]
        for n, s in wood.items()
        if n in ("core", "backing")
    }
    stock_fit = {
        n: all(
            a <= b + TOL for a, b in zip(sorted(envelope), sorted(RETAIL_ENVELOPE_MM))
        )
        for n, envelope in ordinary_blank.items()
    }
    failures = [k for k, value in checks.items() if value]
    if receiver_loss:
        failures.append("fixed_screw_receiver_loss")
    if any(v > TOL for v in bore_missing.values()):
        failures.append("bore_exits_receiving_wood")
    if any(v <= TOL for v in intended.values()):
        failures.append("missing_factory_plate_hole_path")
    if below:
        failures.append("hl33_receiver_below_catalog_minimum")
    if any(
        len(members) != 1 or members[0] != receiver[n]
        for n, members in backing_receivers.items()
    ):
        failures.append("backing_bolt_not_one_wood_receiver")
    if not all(len(s.Solids()) == 1 for s in wood.values()):
        failures.append("one_piece_wood")
    seam_backed = (
        backing.BoundingBox().xmin < -1.5875 < backing.BoundingBox().xmax
        and backing.BoundingBox().ymax == front
        and backing.BoundingBox().zmin <= 0
        and backing.BoundingBox().zmax >= underside
        and wood["header"].BoundingBox().zmax
        >= max(panels[n].BoundingBox().zmax for n in ("kicker_left", "kicker_right"))
    )
    if not seam_backed or len(kicker) != 4 or any(v <= TOL for v in kicker.values()):
        failures.append("kicker_inner_edge_or_screw_receiver")
    if not all(stock_fit.values()):
        failures.append("ordinary_4x12_blank_comparator_failure")
    return {
        "status": "rejected_nominal_pose" if failures else "geometry_only_unqualified",
        "scope": "one distinct full-width front backing with two staggered independent HL33 bolt pairs",
        "catalog_source": CATALOG,
        "catalog_page": "C-C-2026 PDF p.315, HL33 row",
        "source_axes": str(AXES.relative_to(ROOT)),
        "assumed_horizontal_hole_inset_mm": HOLE_INSET,
        "assumed_plate_thickness_mm": PLATE,
        "assumed_wood_bore_diameter_mm": 14.2875,
        "rear_extension_mm": REAR_EXTENSION,
        "backing_bracket_base_z_mm": BACKING_Z,
        "backing_member_count": 1,
        "backing_bracket_count": 2,
        "backing_bolt_axes": backing_axes,
        "backing_bolt_receiving_members": backing_receivers,
        "backing_bolt_receiver_count": {
            n: len(members) for n, members in backing_receivers.items()
        },
        "receiver_thickness_mm": receiver_thickness,
        "minimum_hl33_receiver_thickness_mm": min(receiver_thickness.values()),
        "below_minimum_receivers_mm": below,
        "fixed_panel_count": len(panels),
        "fixed_screw_axis_count": len(protected),
        "fixed_frame_axis_count": len(frame_rows),
        "fixed_screw_receiver_loss_mm3": receiver_loss,
        "kicker_center_receiver_mm3": kicker,
        "kicker_inner_seam_backed": seam_backed,
        "wood_bounds_mm": {n: bounds(s) for n, s in wood.items()},
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "bore_missing_wood_mm3": bore_missing,
        "intended_plate_path_mm3": intended,
        "checks_mm3": checks,
        "access_failures_mm3": access,
        "stack_envelope_count": len(stack_shapes),
        "stack_assumptions_mm": {
            "washer_od": 25.4,
            "washer_thickness": 3,
            "head_length": 8,
            "nut_length": 12,
            "tool_od": 40,
            "tool_sweep_length": 25,
        },
        "blank_comparator": {
            "ordinary_nominal": "4x12x12-ft",
            "source": RETAIL_URL,
            "listed_actual_mm": RETAIL_ENVELOPE_MM,
            "axis_aligned_member_envelope_mm": ordinary_blank,
            "one_piece_fit": stock_fit,
            "limit": "Dimensional comparison only; no trim, tolerance, drying, grade, local availability, or machining allowance.",
        },
        "ordinary_stock_gate": "open: the Lowe's/Home Depot 4x12 dimensional lead fails the one-piece backing envelope and leaves no practical core machining allowance",
        "rail_connection_established": False,
        "duty_limit": "No catalog rating transfers to this pose. Independent bolts remove the three-wood stack but do not establish HL33 F1/F2, backing force path, or rail joints.",
        "rating_or_drilling_released": False,
        "failures": failures,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_backing_revision(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
