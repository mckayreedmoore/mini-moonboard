"""Nominal parent-neighbor screen for the 660-mm zero-gap HL53 rail trial.

Diagnostic solid envelopes only; never drilling coordinates or a joint rating.
"""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hl53 import (
    ANGLE_LENGTH,
    ANGLE_REACH,
    FIRST_OFFSET,
    GAUGE7_NOMINAL,
    SECOND_OFFSET,
)
from scripts.hardware_first_center_hybrid import (
    AXES,
    ROOT,
    TOL,
    TOP,
    box,
    cylinder,
    hits,
)
from scripts.hardware_first_hl53_spaced_ribs import (
    ACCESS_DEPTH,
    ACCESS_DIAMETER,
    HEADER_FRONT,
    HEADER_REAR,
    POSE_Y,
    POST_HALF,
    RAIL_GAP,
    RIB_WIDTH,
    WASHER_DIAMETER,
    WASHER_THICKNESS,
    _bore,
    _principal,
)
from scripts.hardware_first_hl53_wide_ribs import (
    INTEGRAL_RAIL_DEPTH,
    INTEGRAL_RAIL_LENGTH,
    INTEGRAL_RAIL_Y_MAX,
    INTEGRAL_RAIL_Y_MIN,
    JOINT_Y,
    _rail_joint,
)

OUTPUT = (
    ROOT
    / "docs/bolted-candidate-prototypes/hardware_first_hl53_660_parent_neighbor.json"
)
SPACING = 660
RAIL_NAME = "base_rail_bottom_right"


def _parent(raw):
    """Rebuild the nominal 660-mm parent solids using the spaced-rib poses."""
    hb = raw["base_header"].BoundingBox()
    cap_half = SPACING / 2 + RIB_WIDTH / 2
    wood = {
        "base_header": raw["base_header"]
        .fuse(
            box(
                -cap_half,
                HEADER_REAR,
                hb.zmin,
                2 * cap_half,
                HEADER_FRONT - HEADER_REAR,
                TOP - hb.zmin,
            )
        )
        .clean(),
        "base_post_center": box(
            -POST_HALF,
            HEADER_REAR,
            0,
            2 * POST_HALF,
            HEADER_FRONT - HEADER_REAR,
            hb.zmin,
        ),
    }
    for side, sign in (("left", -1), ("right", 1)):
        wood[f"front_principal_{side}"] = _principal(
            raw[f"base_principal_center_{side}"], sign * 70
        )
        wood[f"rib_principal_{side}"] = _principal(
            raw[f"base_principal_center_{side}"], sign * SPACING / 2
        )
        wood[f"rib_post_{side}"] = box(
            sign * SPACING / 2 - RIB_WIDTH / 2,
            HEADER_REAR,
            0,
            RIB_WIDTH,
            HEADER_FRONT - HEADER_REAR,
            hb.zmin,
        )
    rail_names = [
        f"base_rail_{level}_{side}"
        for side in ("left", "right")
        for level in ("bottom", "service_lower", "service_upper")
    ]
    rail_inner = SPACING / 2 + RIB_WIDTH / 2 + RAIL_GAP
    for name in rail_names:
        b = raw[name].BoundingBox()
        left = name.endswith("left")
        x0, x1 = (b.xmin - 1, -rail_inner) if left else (rail_inner, b.xmax + 1)
        wood[name] = (
            raw[name]
            .intersect(box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2))
            .clean()
        )
    # The candidate zero-gap rail is one continuous solid, not the parent's
    # 15-mm-gap rail. Only this one of six rail ends is replaced.
    original = raw[RAIL_NAME]
    b = original.BoundingBox()
    inner = SPACING / 2 + RIB_WIDTH / 2
    trimmed = original.intersect(
        box(inner, b.ymin - 1, b.zmin - 1, b.xmax + 1 - inner, b.ylen + 2, b.zlen + 2)
    ).clean()
    t = trimmed.BoundingBox()
    integral = box(
        inner,
        INTEGRAL_RAIL_Y_MIN,
        t.zmax - INTEGRAL_RAIL_DEPTH,
        INTEGRAL_RAIL_LENGTH,
        INTEGRAL_RAIL_Y_MAX - INTEGRAL_RAIL_Y_MIN,
        INTEGRAL_RAIL_DEPTH,
    )
    wood[RAIL_NAME] = trimmed.fuse(integral).clean()
    replaced = {
        "base_header",
        *rail_names,
        "base_principal_center_left",
        "base_principal_center_right",
        "base_post_center_left",
        "base_post_center_right",
    }
    adjacent = {
        name: solid
        for name, solid in raw.items()
        if name not in replaced and not name.startswith(("main_", "kicker_"))
    }
    return wood, adjacent, hb.zmin, t.zmax


def _header_hardware(wood, header_bottom):
    """Recreate all eight nominal header brackets and short access envelopes."""
    brackets, bolts, washers, tools = {}, {}, {}, {}

    def add(name, member, seat_member, face, direction, y, bend_z, rise):
        mb = wood[member].BoundingBox()
        plate_x = face if direction == 1 else face - GAUGE7_NOMINAL
        seat_x = face if direction == 1 else face - ANGLE_REACH
        z0 = bend_z if rise == 1 else bend_z - ANGLE_REACH
        seat_z = bend_z if rise == 1 else bend_z - GAUGE7_NOMINAL
        body = (
            box(
                plate_x,
                y - ANGLE_LENGTH / 2,
                z0,
                GAUGE7_NOMINAL,
                ANGLE_LENGTH,
                ANGLE_REACH,
            )
            .fuse(
                box(
                    seat_x,
                    y - ANGLE_LENGTH / 2,
                    seat_z,
                    ANGLE_REACH,
                    ANGLE_LENGTH,
                    GAUGE7_NOMINAL,
                )
            )
            .clean()
        )
        for index, offset in enumerate((FIRST_OFFSET, SECOND_OFFSET), 1):
            for flange in ("vertical", "seat"):
                key = f"{name}_{flange}_{index}"
                if flange == "vertical":
                    z = bend_z + rise * offset
                    hole = _bore((plate_x, y, z), (1, 0, 0), GAUGE7_NOMINAL)
                    start = (min(mb.xmin, plate_x), y, z)
                    bolts[key] = _bore(start, (1, 0, 0), mb.xlen + GAUGE7_NOMINAL, 12.7)
                    outer = face + direction * GAUGE7_NOMINAL
                    opposite = mb.xmin if direction == 1 else mb.xmax
                    ends = [
                        ((outer, y, z), (direction, 0, 0)),
                        ((opposite, y, z), (-direction, 0, 0)),
                    ]
                else:
                    x = face + direction * offset
                    hole = _bore((x, y, seat_z), (0, 0, 1), GAUGE7_NOMINAL)
                    sb = wood[seat_member].BoundingBox()
                    start = (x, y, min(sb.zmin, seat_z))
                    bolts[key] = _bore(start, (0, 0, 1), sb.zlen + GAUGE7_NOMINAL, 12.7)
                    outer = bend_z + rise * GAUGE7_NOMINAL
                    opposite = sb.zmin if rise == 1 else sb.zmax
                    ends = [
                        ((x, y, outer), (0, 0, rise)),
                        ((x, y, opposite), (0, 0, -rise)),
                    ]
                body = body.cut(hole)
                for end_index, (point, normal) in enumerate(ends):
                    washers[f"{key}_{end_index}"] = _bore(
                        point, normal, WASHER_THICKNESS, WASHER_DIAMETER
                    )
                    tools[f"{key}_{end_index}"] = _bore(
                        point, normal, ACCESS_DEPTH, ACCESS_DIAMETER
                    )
        brackets[name] = body.clean()

    for side, sign in (("left", -1), ("right", 1)):
        front = wood[f"front_principal_{side}"].BoundingBox()
        rib = wood[f"rib_principal_{side}"].BoundingBox()
        rib_post = wood[f"rib_post_{side}"].BoundingBox()
        add(
            f"upper_front_{side}",
            f"front_principal_{side}",
            "base_header",
            front.xmin if sign < 0 else front.xmax,
            sign,
            POSE_Y["upper_front"],
            TOP,
            1,
        )
        add(
            f"upper_rib_{side}",
            f"rib_principal_{side}",
            "base_header",
            rib.xmax if sign < 0 else rib.xmin,
            -sign,
            POSE_Y["upper_rib"],
            TOP,
            1,
        )
        add(
            f"lower_front_{side}",
            "base_post_center",
            "base_header",
            -POST_HALF if sign < 0 else POST_HALF,
            sign,
            POSE_Y["lower_front"],
            header_bottom,
            -1,
        )
        add(
            f"lower_rib_{side}",
            f"rib_post_{side}",
            "base_header",
            rib_post.xmax if sign < 0 else rib_post.xmin,
            -sign,
            POSE_Y["lower_rib"],
            header_bottom,
            -1,
        )
    return brackets, bolts, washers, tools


def _rail_hardware(wood, bend_z):
    rib = wood["rib_principal_right"].BoundingBox()
    rail = wood[RAIL_NAME].BoundingBox()
    face = rib.xmax
    y0 = JOINT_Y - ANGLE_LENGTH / 2
    body = box(face, y0, bend_z, GAUGE7_NOMINAL, ANGLE_LENGTH, ANGLE_REACH)
    body = body.fuse(
        box(face, y0, bend_z, ANGLE_REACH, ANGLE_LENGTH, GAUGE7_NOMINAL)
    ).clean()
    bolts, washers, tools = {}, {}, {}
    for index, offset in enumerate((FIRST_OFFSET, SECOND_OFFSET), 1):
        for flange in ("vertical", "seat"):
            key = f"rail_{flange}_{index}"
            if flange == "vertical":
                z = bend_z + offset
                hole = _bore((face, JOINT_Y, z), (1, 0, 0), GAUGE7_NOMINAL)
                bolts[key] = _bore(
                    (rib.xmin, JOINT_Y, z), (1, 0, 0), rib.xlen + GAUGE7_NOMINAL, 12.7
                )
                ends = [
                    ((face + GAUGE7_NOMINAL, JOINT_Y, z), (1, 0, 0)),
                    ((rib.xmin, JOINT_Y, z), (-1, 0, 0)),
                ]
            else:
                x = face + offset
                hole = _bore((x, JOINT_Y, bend_z), (0, 0, 1), GAUGE7_NOMINAL)
                # Use the actual rail section along this bolt's centerline,
                # as in the isolated probe, rather than the whole bbox.
                line = _bore(
                    (x, JOINT_Y, rail.zmin - 1), (0, 0, 1), rail.zlen + 2, 0.2
                ).intersect(wood[RAIL_NAME])
                bottom = line.BoundingBox().zmin
                bolts[key] = _bore(
                    (x, JOINT_Y, bottom),
                    (0, 0, 1),
                    bend_z - bottom + GAUGE7_NOMINAL,
                    12.7,
                )
                ends = [
                    ((x, JOINT_Y, bend_z + GAUGE7_NOMINAL), (0, 0, 1)),
                    ((x, JOINT_Y, bottom), (0, 0, -1)),
                ]
            body = body.cut(hole)
            for end_index, (point, normal) in enumerate(ends):
                washers[f"{key}_{end_index}"] = _bore(
                    point, normal, WASHER_THICKNESS, WASHER_DIAMETER
                )
                tools[f"{key}_{end_index}"] = _bore(
                    point, normal, ACCESS_DEPTH, ACCESS_DIAMETER
                )
    return body.clean(), bolts, washers, tools


def screen_parent_neighbor():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len({r["name"] for r in panel_rows}) != 66:
        raise ValueError("expected 66 distinct fixed panel/kicker axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 original frame axes")
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    wood, adjacent, header_bottom, bend_z = _parent(raw)
    header_brackets, header_bolts, header_washers, header_tools = _header_hardware(
        wood, header_bottom
    )
    rail_bracket, rail_bolts, rail_washers, rail_tools = _rail_hardware(wood, bend_z)
    parent_wood = {
        **{
            n: s for n, s in wood.items() if n not in (RAIL_NAME, "rib_principal_right")
        },
        **adjacent,
    }
    # Existing unchanged panel-axis receivers retain their original names;
    # the rebuilt front/post/header replace the old named receivers.
    receivers = dict(raw)
    receivers.update(wood)
    for side in ("left", "right"):
        receivers[f"base_principal_center_{side}"] = wood[f"front_principal_{side}"]
        receivers[f"base_post_center_{side}"] = wood["base_post_center"]
    receiver_loss = {}
    for row in panel_rows:
        screw = cylinder(row)
        member = row["second_member"]
        old = screw.intersect(raw[member]).Volume()
        new = screw.intersect(receivers[member]).Volume()
        if old - new > TOL or new <= TOL:
            receiver_loss[row["name"]] = round(old - new, 3)
    screws = {r["name"]: cylinder(r) for r in panel_rows}
    frame_axes = {r["name"]: cylinder(r) for r in frame_rows}
    rail_hardware = {
        "rail_bracket": rail_bracket,
        **rail_bolts,
        **rail_washers,
        **rail_tools,
    }
    parent_hardware = {
        **header_brackets,
        **header_bolts,
        **header_washers,
        **header_tools,
    }
    checks = {
        "rail_to_parent_wood": hits(wood[RAIL_NAME], parent_wood),
        "rail_to_parent_brackets": hits(wood[RAIL_NAME], header_brackets),
        "rail_to_parent_bolts": hits(wood[RAIL_NAME], header_bolts),
        "rail_to_parent_washers": hits(wood[RAIL_NAME], header_washers),
        "rail_to_parent_tools": hits(wood[RAIL_NAME], header_tools),
        "rail_bracket_to_parent_wood": hits(rail_bracket, parent_wood),
        "rail_bracket_to_parent_brackets": hits(rail_bracket, header_brackets),
        "rail_bracket_to_parent_bolts": hits(rail_bracket, header_bolts),
        "rail_bracket_to_parent_washers": hits(rail_bracket, header_washers),
        "rail_bracket_to_parent_tools": hits(rail_bracket, header_tools),
        "rail_bolts_to_parent_wood": {
            n: v for n, s in rail_bolts.items() if (v := hits(s, parent_wood))
        },
        "rail_bolts_to_parent_brackets": {
            n: v for n, s in rail_bolts.items() if (v := hits(s, header_brackets))
        },
        "rail_washers_to_parent_wood": {
            n: v for n, s in rail_washers.items() if (v := hits(s, parent_wood))
        },
        "rail_tools_to_parent_wood": {
            n: v for n, s in rail_tools.items() if (v := hits(s, parent_wood))
        },
        "rail_hardware_to_parent_hardware": {
            n: v for n, s in rail_hardware.items() if (v := hits(s, parent_hardware))
        },
        "rail_hardware_to_fixed_screws": {
            n: v for n, s in screws.items() if (v := hits(s, rail_hardware))
        },
        "rail_hardware_to_panels": {
            n: v for n, s in rail_hardware.items() if (v := hits(s, panels))
        },
    }
    old_frame_axis_hits = {
        n: v for n, s in frame_axes.items() if (v := hits(s, rail_hardware))
    }
    isolated = _rail_joint(
        raw,
        panels,
        panel_rows,
        {"fixed_screw_receiver_loss_mm3": {}, "kicker_seam_supported": True},
        0.0,
    )
    return {
        "status": "nominal_parent_neighbor_clash"
        if any(checks.values())
        else "partial_parent_neighbor_geometry_clear",
        "source_axes": str(AXES.relative_to(ROOT)),
        "width_option": KERF_RIGHT,
        "rib_spacing_mm": SPACING,
        "rail_to_rib_gap_mm": 0,
        "station": "bottom right only",
        "header_bracket_count": len(header_brackets),
        "parent_header_bracket_names": sorted(header_brackets),
        "parent_wood_names": sorted(parent_wood),
        "fixed_panel_kicker_axis_count": len(panel_rows),
        "fixed_screw_receiver_loss_mm3": receiver_loss,
        "isolated_zero_gap_status": isolated["status"],
        "checks_mm3": checks,
        "old_frame_axis_hits_mm3_diagnostic_only": old_frame_axis_hits,
        "screened_ideal_hardware": "HL53 nominal bodies, 12.7-mm bolt paths, 25.4-mm washers, and 38.1-mm by 30-mm straight tool cylinders",
        "other_rail_ends_open": 5,
        "existing_frame_bolt_axes_resolved": False,
        "actual_hardware_access_verified": False,
        "catalog_applicability_verified": False,
        "load_rating_adopted": False,
        "connected_architecture_verdict": False,
        "drilling_released": False,
        "scope_limit": "One zero-gap rail station against reconstructed 660-mm parent wood, eight header brackets and their modeled hardware; old frame-axis hits are diagnostic only, and the other five rail joints, full hardware, frame-bolt changes and resistance remain open.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_parent_neighbor(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
