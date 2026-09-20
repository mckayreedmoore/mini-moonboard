"""Bounded common-core HL33 geometry screen; nominal occupancy, never drill data."""

import argparse
import csv
import json
from pathlib import Path

import cadquery as cq

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
    hits,
)
from scripts.hardware_first_center_hybrid_toe import _principal
from scripts.hardware_first_center_tongue import pair_clashes

OUTPUT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_hl33_common_core.json"
CATALOG = "https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog"
CORE_DEPTH = 90.47
CORE_HALF = 120.0
TONGUE_HALF = 25.4
RAIL_END = 130.0
HOLE_INSET = 50.8  # Undimensioned horizontal-leg hole position.
BORE_DIAMETER = 14.2875  # Occupied clearance assumption, not a drill callout.
MIN_BOLTED_WOOD = 88.9
ANGLE_Z = 80.0
TRIAL_REAR_EXTENSION = (45.0, 65.0)


def _overlaps(shapes, targets):
    return {n: found for n, shape in shapes.items() if (found := hits(shape, targets))}


def _stack(start, direction, length):
    """Illustrative outside-face hardware and tool sweep at both bolt ends."""
    p = cq.Vector(*start)
    d = cq.Vector(*direction)
    end = p + d.multiply(length)
    result = {}
    for side, face, outward in (("head", p, d.multiply(-1)), ("nut", end, d)):
        result[f"{side}_washer"] = cq.Solid.makeCylinder(12.7, 3, face, outward)
        body_start = face + outward.multiply(3)
        result[f"{side}_body"] = cq.Solid.makeCylinder(
            12.7, 8 if side == "head" else 12, body_start, outward
        )
        tool_start = body_start + outward.multiply(8 if side == "head" else 12)
        result[f"{side}_tool"] = cq.Solid.makeCylinder(20, 25, tool_start, outward)
    return result


def screen_trial(rear_extension, raw, panel_rows, frame_rows):
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    hb = raw["base_header"].BoundingBox()
    rear, front, underside = hb.ymin - rear_extension, hb.ymax, hb.zmin
    junction = rear + CORE_DEPTH
    angle_z = ANGLE_Z
    # One solid rear core and integral narrow front seam tongue. Backing wings
    # remain separate one-piece members and receive explicit HL33 attachments.
    rear_block = box(-CORE_HALF, rear, 0, 2 * CORE_HALF, CORE_DEPTH, underside)
    front_tongue = box(
        -TONGUE_HALF, junction, 0, 2 * TONGUE_HALF, front - junction, underside
    )
    core = rear_block.fuse(front_tongue).clean()
    wood = {"core": core}
    for side, sign in (("left", -1), ("right", 1)):
        x0 = -CORE_HALF if sign < 0 else TONGUE_HALF
        backing = box(
            x0, junction, 0, CORE_HALF - TONGUE_HALF, front - junction, underside
        )
        # The factory angle occupies this local rear-face pocket; it is not
        # counted as an attachment merely because wood faces touch.
        pocket = box(x0, junction, angle_z, CORE_HALF - TONGUE_HALF, PLATE, LENGTH)
        wood[f"backing_{side}"] = backing.cut(pocket).clean()
    wood["header"] = (
        raw["base_header"]
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
        .clean()
    )
    for side in ("left", "right"):
        wood[f"base_principal_center_{side}"] = _principal(side)
    rail_names = tuple(
        f"base_rail_{level}_{side}"
        for side in ("left", "right")
        for level in ("bottom", "service_lower", "service_upper")
    )
    for name in rail_names:
        original = raw[name]
        b = original.BoundingBox()
        x0, x1 = (
            (b.xmin - 1, -RAIL_END) if name.endswith("left") else (RAIL_END, b.xmax + 1)
        )
        wood[name] = original.intersect(
            box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2)
        ).clean()
    replaced = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
        *rail_names,
    }
    adjacent = {n: s for n, s in raw.items() if n not in panels and n not in replaced}

    plates = {}
    bores = {}
    paths = {}
    own = {}
    stacks = {}

    def add_axis(
        name,
        member,
        point,
        direction,
        wood_length,
        plate_point,
        path_length,
        plate_name,
    ):
        bores[name] = (member, bore(point, direction, wood_length))
        paths[name] = bore(plate_point, direction, path_length)
        own[name] = plate_name
        stacks[name] = _stack(plate_point, direction, path_length)

    # One rear-Y lower HL33 attaches the core to the extended header.
    plates["lower_vertical"] = box(
        -LENGTH / 2, rear - PLATE, underside - REACH, LENGTH, PLATE, REACH
    )
    plates["lower_seat"] = box(
        -LENGTH / 2, rear - REACH, underside - PLATE, LENGTH, REACH, PLATE
    )
    add_axis(
        "lower_core",
        "core",
        (0, rear, underside - LEG_HOLE),
        (0, 1, 0),
        CORE_DEPTH,
        (0, rear - PLATE, underside - LEG_HOLE),
        CORE_DEPTH + PLATE,
        "lower_vertical",
    )
    add_axis(
        "lower_header",
        "header",
        (0, rear - HOLE_INSET, underside),
        (0, 0, 1),
        TOP - underside,
        (0, rear - HOLE_INSET, underside - PLATE),
        TOP - underside + PLATE,
        "lower_seat",
    )

    # Two outward-X upper HL33s at the known short-bend station.
    for side, sign in (("left", -1), ("right", 1)):
        center = sign * 70.0
        outer = center + sign * 44.45
        x0 = outer - PLATE if sign < 0 else outer
        plates[f"upper_{side}_vertical"] = box(x0, -100, TOP, PLATE, LENGTH, REACH)
        plates[f"upper_{side}_seat"] = box(
            outer - REACH if sign < 0 else outer, -100, TOP, REACH, LENGTH, PLATE
        )
        add_axis(
            f"upper_{side}_principal",
            f"base_principal_center_{side}",
            (center - 44.45, -100 + ALONG_BEND, TOP + LEG_HOLE),
            (1, 0, 0),
            88.9,
            (min(center - 44.45, x0), -100 + ALONG_BEND, TOP + LEG_HOLE),
            88.9 + PLATE,
            f"upper_{side}_vertical",
        )
        hx = outer + sign * HOLE_INSET
        add_axis(
            f"upper_{side}_header",
            "header",
            (hx, -100 + ALONG_BEND, underside),
            (0, 0, 1),
            TOP - underside,
            (hx, -100 + ALONG_BEND, underside),
            TOP - underside + PLATE,
            f"upper_{side}_seat",
        )

    # Each backing has one real HL33: front-face core leg and outer-side
    # backing leg. One transverse bolt passes both side legs and all three
    # wood sections; the two core-face legs have separate through-core bolts.
    for side, sign in (("left", -1), ("right", 1)):
        outer = sign * CORE_HALF
        plates[f"backing_{side}_core_leg"] = box(
            -CORE_HALF if sign < 0 else CORE_HALF - REACH,
            junction,
            angle_z,
            REACH,
            PLATE,
            LENGTH,
        )
        plates[f"backing_{side}_side_leg"] = box(
            outer - PLATE if sign < 0 else outer,
            junction,
            angle_z,
            PLATE,
            REACH,
            LENGTH,
        )
        xhole = sign * (CORE_HALF - HOLE_INSET)
        add_axis(
            f"backing_{side}_core",
            "core",
            (xhole, rear, angle_z + ALONG_BEND),
            (0, 1, 0),
            CORE_DEPTH,
            (xhole, rear, angle_z + ALONG_BEND),
            CORE_DEPTH + PLATE,
            f"backing_{side}_core_leg",
        )
    shared_y = junction + HOLE_INSET
    shared_z = angle_z + ALONG_BEND
    add_axis(
        "backing_shared",
        "backing_left",
        (-CORE_HALF, shared_y, shared_z),
        (1, 0, 0),
        2 * CORE_HALF,
        (-CORE_HALF - PLATE, shared_y, shared_z),
        2 * CORE_HALF + 2 * PLATE,
        "backing_left_side_leg",
    )

    bore_shapes = {n: s for n, (_, s) in bores.items()}
    screws = {r["name"]: cylinder(r) for r in panel_rows}
    long_screws = {r["name"]: cylinder(r, 63.5) for r in panel_rows}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    receivers = dict(raw)
    receivers.update(wood)
    receivers.update(
        {
            "base_header": wood["header"],
            "base_post_center_left": wood["backing_left"],
            "base_post_center_right": wood["backing_right"],
        }
    )
    receiver_loss = {}
    for row in panel_rows:
        n, member = row["name"], row["second_member"]
        old = screws[n].intersect(raw[member]).Volume()
        new = screws[n].intersect(receivers[member]).Volume()
        if old - new > TOL or new <= TOL:
            receiver_loss[n] = round(old - new, 3)
    kicker = {
        n: round(
            s.intersect(wood[f"backing_{'left' if 'left' in n else 'right'}"]).Volume(),
            3,
        )
        for n, s in screws.items()
        if n.startswith("round_kicker_") and "_center_" in n
    }
    bore_missing = {
        n: round(max(0, s.Volume() - s.intersect(wood[member]).Volume()), 3)
        for n, (member, s) in bores.items()
        if n != "backing_shared"
    }
    shared = bore_shapes["backing_shared"]
    shared_missing = round(
        max(
            0,
            shared.Volume()
            - shared.intersect(
                wood["backing_left"].fuse(wood["core"], wood["backing_right"])
            ).Volume(),
        ),
        3,
    )
    bore_missing["backing_shared"] = shared_missing
    intended = {
        n: round(path.intersect(plates[own[n]]).Volume(), 3)
        for n, path in paths.items()
    }
    intended["backing_shared_right_leg"] = round(
        paths["backing_shared"].intersect(plates["backing_right_side_leg"]).Volume(), 3
    )
    other_wood = {
        n: found
        for n, path in paths.items()
        if n != "backing_shared"
        and (
            found := hits(
                path,
                {**adjacent, **{k: s for k, s in wood.items() if k != bores[n][0]}},
            )
        )
    }
    other_plate = {
        n: found
        for n, path in paths.items()
        if (
            found := hits(
                path,
                {
                    k: s
                    for k, s in plates.items()
                    if k != own[n]
                    and not (n == "backing_shared" and k == "backing_right_side_leg")
                },
            )
        )
    }
    stack_shapes = {
        f"{n}_{part}": s for n, pieces in stacks.items() for part, s in pieces.items()
    }
    stack_other_wood = _overlaps(stack_shapes, wood)
    stack_plates = _overlaps(stack_shapes, plates)
    tool_shapes = {n: s for n, s in stack_shapes.items() if n.endswith("_tool")}
    tool_pairs = {
        pair: volume
        for pair, volume in pair_clashes(tool_shapes).items()
        if pair.split(" / ")[0].rsplit("_", 2)[0]
        != pair.split(" / ")[1].rsplit("_", 2)[0]
    }
    checks = {
        "plate_panel": _overlaps(plates, panels),
        "plate_wood": _overlaps(plates, wood),
        "plate_adjacent": _overlaps(plates, adjacent),
        "plate_pairs": pair_clashes(plates, skip_same_angle=True),
        "wood_panel": _overlaps(wood, panels),
        "wood_adjacent": _overlaps(wood, adjacent),
        "wood_pairs": pair_clashes(wood),
        "bolt_path_panel": _overlaps(paths, panels),
        "bolt_path_other_wood": other_wood,
        "bolt_path_other_plate": other_plate,
        "independent_bore_pairs": pair_clashes(bore_shapes),
        "fixed_screw_hardware": _overlaps(screws, {**plates, **bore_shapes}),
        "conditional_63_5_screw_hardware": _overlaps(
            long_screws, {**plates, **bore_shapes}
        ),
        "frame_axis_hardware": _overlaps(frame, {**plates, **bore_shapes}),
        "stack_panel": _overlaps(stack_shapes, panels),
        "stack_adjacent": _overlaps(stack_shapes, adjacent),
        "stack_fixed_screw": _overlaps(stack_shapes, screws),
        "stack_changed_wood": stack_other_wood,
        "stack_plate": stack_plates,
        "different_axis_tool_pairs": tool_pairs,
    }
    # Plate-to-wood and stack-to-wood contacts are evaluated separately;
    # their designated receiving faces are intentional.
    fundamental = []
    repairable = []
    for label in (
        "plate_panel",
        "wood_panel",
        "fixed_screw_hardware",
        "conditional_63_5_screw_hardware",
        "stack_panel",
        "stack_fixed_screw",
    ):
        if checks[label]:
            fundamental.append(label)
    for label in (
        "plate_wood",
        "plate_adjacent",
        "plate_pairs",
        "wood_adjacent",
        "wood_pairs",
        "bolt_path_panel",
        "bolt_path_other_wood",
        "bolt_path_other_plate",
        "independent_bore_pairs",
        "frame_axis_hardware",
        "stack_adjacent",
        "stack_changed_wood",
        "stack_plate",
        "different_axis_tool_pairs",
    ):
        if checks[label]:
            repairable.append(label)
    if receiver_loss:
        fundamental.append("protected_receiver_loss")
    if any(v > TOL for v in bore_missing.values()):
        repairable.append("bore_missing_wood")
    if any(v <= TOL for v in intended.values()):
        repairable.append("missing_factory_plate_path")
    if len(kicker) != 4 or any(v <= TOL for v in kicker.values()):
        fundamental.append("kicker_center_backing")
    if not all(len(s.Solids()) == 1 for s in wood.values()):
        repairable.append("one_piece_wood")
    core_backing_intersection = {
        side: round(core.intersect(wood[f"backing_{side}"]).Volume(), 6)
        for side in ("left", "right")
    }
    if any(v > TOL for v in core_backing_intersection.values()):
        fundamental.append("core_backing_solid_overlap")
    receiver_thickness = {
        "lower_core": CORE_DEPTH,
        "lower_header": TOP - underside,
        **{f"upper_{side}_principal": 88.9 for side in ("left", "right")},
        **{f"upper_{side}_header": TOP - underside for side in ("left", "right")},
        **{f"backing_{side}_core": CORE_DEPTH for side in ("left", "right")},
        "backing_shared_left_wing": CORE_HALF - TONGUE_HALF,
        "backing_shared_core_tongue": 2 * TONGUE_HALF,
        "backing_shared_right_wing": CORE_HALF - TONGUE_HALF,
    }
    thickness_violations = {
        n: round(MIN_BOLTED_WOOD - thickness, 4)
        for n, thickness in receiver_thickness.items()
        if thickness < MIN_BOLTED_WOOD - TOL
    }
    # Even a thicker tongue would leave the shared bolt joining three wood
    # sections through two angles, outside the catalog's tabulated joint.
    fundamental.append("catalog_inapplicable_backing_connection")
    if any(n != "backing_shared_core_tongue" for n in thickness_violations):
        fundamental.append("other_receiver_below_catalog_minimum")
    return {
        "parameter_core_rear_extension_mm": rear_extension,
        "core_bounds_mm": bounds(core),
        "core_rear_block_bounds_mm": bounds(rear_block),
        "core_front_tongue_bounds_mm": bounds(front_tongue),
        "core_backing_intersection_mm3": core_backing_intersection,
        "bolted_wood_section_thickness_mm": {
            n: round(v, 4) for n, v in receiver_thickness.items()
        },
        "catalog_minimum_wood_shortfall_mm": thickness_violations,
        "backing_connection_catalog_applicable": False,
        "backing_catalog_inapplicability": [
            "shared bolt crosses a 50.8-mm integral core tongue, below the HL33 88.9-mm minimum bolted wood thickness",
            "shared transverse bolt forms a three-wood/two-angle stack, not the tabulated two-member HL33 installation",
        ],
        "wood_bounds_mm": {n: bounds(s) for n, s in wood.items()},
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "bore_count": len(bores),
        "bolt_path_count": len(paths),
        "intended_plate_path_mm3": intended,
        "bore_missing_wood_mm3": bore_missing,
        "protected_receiver_loss_mm3": receiver_loss,
        "existing_frame_axis_receivers_changed": sorted(
            {
                r["name"]
                for r in frame_rows
                if r["first_member"] in replaced or r["second_member"] in replaced
            }
        ),
        "kicker_center_backing_mm3": kicker,
        "checks_mm3": checks,
        "stack_assumptions_mm": {
            "washer_od": 25.4,
            "washer_thickness": 3,
            "head_envelope_length": 8,
            "nut_envelope_length": 12,
            "tool_od": 40,
            "tool_sweep_length": 25,
        },
        "stack_envelope_count": len(stack_shapes),
        "fundamental_for_this_pose": fundamental,
        "repairable_geometry_or_detail": repairable,
        "status": "rejected_nominal_pose"
        if fundamental or repairable
        else "geometry_only_unqualified",
    }


def screen_common_core():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len({r["name"] for r in panel_rows}) != 66:
        raise ValueError("expected 66 unique protected axes")
    if len(frame_rows) != 12 or len({r["name"] for r in frame_rows}) != 12:
        raise ValueError("expected 12 unique existing frame axes")
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    trials = [
        screen_trial(extension, raw, panel_rows, frame_rows)
        for extension in TRIAL_REAR_EXTENSION
    ]
    return {
        "scope": "one parameterized kerf-right common-core HL33 geometry prototype",
        "source_axes": str(AXES.relative_to(ROOT)),
        "catalog_source": CATALOG,
        "catalog_page": "C-C-2026 PDF p.315, HL33 row",
        "factory_nominal_mm": {
            "leg_reach": REACH,
            "bend_length": LENGTH,
            "hole_along_bend": ALONG_BEND,
            "vertical_leg_hole": LEG_HOLE,
            "minimum_bolted_wood": MIN_BOLTED_WOOD,
        },
        "assumed_mm": {
            "horizontal_leg_hole_inset": HOLE_INSET,
            "ideal_plate_thickness": PLATE,
            "occupied_wood_bore_diameter": BORE_DIAMETER,
            "core_rear_depth": CORE_DEPTH,
            "core_half_width": CORE_HALF,
            "backing_angle_base_z": ANGLE_Z,
            "front_tongue_half_width": TONGUE_HALF,
            "trimmed_inner_rail_end_abs_x": RAIL_END,
        },
        "fixed_panel_solid_count": 6,
        "fixed_panel_screw_axis_count": 66,
        "fixed_frame_axis_count": 12,
        "hold_led_boundary": "Raw kerf-right panel solids and their hold/LED layout are unchanged; hole/LED voids are not individually modeled in this solid screen.",
        "duty_mapping": {
            "lower_HL33": "rear core face to raised header; catalog uplift and local F1 cannot establish reversible F1, F2 or moment for this pose",
            "upper_two_HL33": "outward principal faces to raised header; reversible F1, unlisted F2 and couples unestablished",
            "backing_two_HL33": "core front face to separate left/right backing wings; shared transverse bolt crosses both backing wings and integral tongue",
            "front_backing": "left/right wings receive four center kicker screws; integral core tongue supports both kicker inner edges",
            "six_inner_rails": "trimmed endpoints only; no rated rail-to-center bracket connection established",
        },
        "fundamental_integration_gaps": [
            "backing shared bolt is catalog-inapplicable: 50.8-mm core tongue and unlisted three-wood/two-angle stack",
            "six trimmed inner rails have no modeled factory-bracket load path to the new center",
            "reversible F1/F2 and moment duty are not established for lower, upper or backing HL33s",
        ],
        "shape_only_minimum_revision_mm": {
            "current_core_width": 2 * CORE_HALF,
            "current_tongue_width": 2 * TONGUE_HALF,
            "current_each_wing_width": CORE_HALF - TONGUE_HALF,
            "minimum_tongue_width": MIN_BOLTED_WOOD,
            "minimum_each_wing_width": MIN_BOLTED_WOOD,
            "minimum_total_core_width": round(3 * MIN_BOLTED_WOOD, 4),
            "increase_over_current_core_width": round(
                3 * MIN_BOLTED_WOOD - 2 * CORE_HALF, 4
            ),
            "minimum_rail_end_abs_x_for_side_plate": round(
                1.5 * MIN_BOLTED_WOOD + PLATE, 4
            ),
            "limit": "Thickness arithmetic only; does not cure the unlisted shared stack, access, stock blank, or load path.",
        },
        "minimum_connection_revision": (
            "Replace the common transverse bolt with separate two-member backing-angle "
            "attachments that give each wing its own accessible bolt/nut path; "
            "geometry and catalog applicability of that topology are untested."
        ),
        "direct_independent_bolt_split": {
            "inner_wing_to_tongue_face_gap_mm": 0.0,
            "assumed_washer_thickness_mm": 3.0,
            "assumed_nut_length_mm": 12.0,
            "disposition": "Blocked at both inner wing faces by the continuous tongue; separate bolts need a new accessible bracket/member pose or qualified relief, not just a wider blank.",
            "cad_trial_run": False,
        },
        "trials": trials,
        "rating_or_drilling_released": False,
        "unresolved": [
            "HL33 horizontal hole inset, bend and delivered tolerances",
            "actual bolt length, washer/nut geometry and wrench approach",
            "F1/F2 load direction and reversible resistance at each angle",
            "backing-to-core load path and shared-bolt action",
            "rail-to-center prefabricated brackets, changed frame bolts",
            "wood end/edge distances, stock and all component resistance",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_common_core(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
