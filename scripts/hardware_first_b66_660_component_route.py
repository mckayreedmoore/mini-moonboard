"""Nominal UB66/B66 one-rail fit against the 660-mm parent assembly.

This is a component geometry screen, not an NDS resistance or drilling plan.
"""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_b66_rear_y import HOLE, OFFSETS, REACH, SHEET, WIDTH
from scripts.hardware_first_center_hybrid import AXES, ROOT, TOL, box, cylinder, hits
from scripts.hardware_first_hl53_660_parent_neighbor import (
    RAIL_NAME,
    SPACING,
    _header_hardware,
    _parent,
)
from scripts.hardware_first_hl53_spaced_ribs import (
    ACCESS_DEPTH,
    ACCESS_DIAMETER,
    WASHER_DIAMETER,
    WASHER_THICKNESS,
    _bore,
)
from scripts.hardware_first_hl53_wide_ribs import (
    INTEGRAL_RAIL_DEPTH,
    INTEGRAL_RAIL_Y_MAX,
    INTEGRAL_RAIL_Y_MIN,
    JOINT_Y,
)

OUTPUT = (
    ROOT
    / "docs/bolted-candidate-prototypes/hardware_first_b66_660_component_route.json"
)
MIN_WOOD = 76.2
BOLT_DIAMETER = 9.525


def _rail_with_full_seat(raw, wood):
    """Extend only the existing zero-gap integral rail pad to B66 reach."""
    old = raw[RAIL_NAME]
    b = old.BoundingBox()
    rib = wood["rib_principal_right"].BoundingBox()
    inner = rib.xmax
    trimmed = old.intersect(
        box(inner, b.ymin - 1, b.zmin - 1, b.xmax + 1 - inner, b.ylen + 2, b.zlen + 2)
    ).clean()
    t = trimmed.BoundingBox()
    pad = box(
        inner,
        INTEGRAL_RAIL_Y_MIN,
        t.zmax - INTEGRAL_RAIL_DEPTH,
        REACH + 1,
        INTEGRAL_RAIL_Y_MAX - INTEGRAL_RAIL_Y_MIN,
        INTEGRAL_RAIL_DEPTH,
    )
    return trimmed.fuse(pad).clean(), t.zmax


def _b66_hardware(wood, bend_z):
    """Place official-DXF nominal holes; retain approximate access envelopes."""
    rib = wood["rib_principal_right"]
    rail = wood[RAIL_NAME]
    rb = rib.BoundingBox()
    face = rb.xmax
    y0 = JOINT_Y - WIDTH / 2
    body = (
        box(face, y0, bend_z, SHEET, WIDTH, REACH)
        .fuse(box(face, y0, bend_z, REACH, WIDTH, SHEET))
        .clean()
    )
    holes, bolts, washers, tools = [], {}, {}, {}
    for i, free_end_offset in enumerate(OFFSETS, 1):
        reach_from_bend = REACH - free_end_offset
        for flange in ("vertical", "seat"):
            name = f"rail_{flange}_{i}"
            if flange == "vertical":
                z = bend_z + reach_from_bend
                factory_hole = _bore((face, JOINT_Y, z), (1, 0, 0), SHEET, HOLE)
                line = _bore((rb.xmin - 1, JOINT_Y, z), (1, 0, 0), rb.xlen + 2, 0.2)
                receiver = rib
                axis = "x"
                start = (rb.xmin, JOINT_Y, z)
                length = rb.xlen + SHEET
                wood_length = rb.xlen
                ends = [
                    ((face + SHEET, JOINT_Y, z), (1, 0, 0)),
                    ((rb.xmin, JOINT_Y, z), (-1, 0, 0)),
                ]
            else:
                x = face + reach_from_bend
                factory_hole = _bore((x, JOINT_Y, bend_z), (0, 0, 1), SHEET, HOLE)
                b = rail.BoundingBox()
                line = _bore((x, JOINT_Y, b.zmin - 1), (0, 0, 1), b.zlen + 2, 0.2)
                receiver = rail
                axis = "z"
                section = line.intersect(rail)
                if section.Volume() <= TOL:
                    bottom = bend_z
                else:
                    bottom = section.BoundingBox().zmin
                start = (x, JOINT_Y, bottom)
                length = bend_z - bottom + SHEET
                wood_length = bend_z - bottom
                ends = [
                    ((x, JOINT_Y, bend_z + SHEET), (0, 0, 1)),
                    ((x, JOINT_Y, bottom), (0, 0, -1)),
                ]
            section = line.intersect(receiver)
            thickness = sum(
                getattr(s.BoundingBox(), f"{axis}len") for s in section.Solids()
            )
            body = body.cut(factory_hole)
            direction = (1, 0, 0) if flange == "vertical" else (0, 0, 1)
            bolt = _bore(start, direction, length, BOLT_DIAMETER)
            wood_bore = _bore(start, direction, wood_length, BOLT_DIAMETER)
            bolts[name] = bolt
            for j, (point, normal) in enumerate(ends):
                washers[f"{name}_{j}"] = _bore(
                    point, normal, WASHER_THICKNESS, WASHER_DIAMETER
                )
                tools[f"{name}_{j}"] = _bore(
                    point, normal, ACCESS_DEPTH, ACCESS_DIAMETER
                )
            holes.append(
                {
                    "id": name,
                    "free_end_offset_mm": free_end_offset,
                    "receiver": "rib_principal_right"
                    if flange == "vertical"
                    else RAIL_NAME,
                    "receiver_thickness_mm": round(thickness, 3),
                    "receiver_continuous": len(section.Solids()) == 1,
                    "factory_hole_clear": factory_hole.intersect(body).Volume() <= TOL,
                    "bolt_wood_overlap_mm3": round(
                        bolt.intersect(receiver).Volume(), 3
                    ),
                    "bore_missing_receiver_mm3": round(
                        max(
                            0,
                            wood_bore.Volume() - wood_bore.intersect(receiver).Volume(),
                        ),
                        3,
                    ),
                }
            )
    return body.clean(), holes, bolts, washers, tools


def screen_b66_route():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len({r["name"] for r in panel_rows}) != 66:
        raise ValueError("expected 66 distinct protected panel/kicker axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 old frame axes for diagnostic comparison")
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    wood, adjacent, header_bottom, _ = _parent(raw)
    wood[RAIL_NAME], bend_z = _rail_with_full_seat(raw, wood)
    header_brackets, header_bolts, header_washers, header_tools = _header_hardware(
        wood, header_bottom
    )
    bracket, holes, bolts, washers, tools = _b66_hardware(wood, bend_z)
    parent_wood = {
        **{
            n: s for n, s in wood.items() if n not in (RAIL_NAME, "rib_principal_right")
        },
        **adjacent,
    }
    parent_hardware = {
        **header_brackets,
        **header_bolts,
        **header_washers,
        **header_tools,
    }
    hardware = {"rail_bracket": bracket, **bolts, **washers, **tools}
    receivers = {**raw, **wood}
    for side in ("left", "right"):
        receivers[f"base_principal_center_{side}"] = wood[f"front_principal_{side}"]
        receivers[f"base_post_center_{side}"] = wood["base_post_center"]
    receiver_loss = {}
    for row in panel_rows:
        screw = cylinder(row)
        old = screw.intersect(raw[row["second_member"]]).Volume()
        new = screw.intersect(receivers[row["second_member"]]).Volume()
        if old - new > TOL or new <= TOL:
            receiver_loss[row["name"]] = round(old - new, 3)
    protected = {r["name"]: cylinder(r) for r in panel_rows}
    checks = {
        "rail_to_parent_wood": hits(wood[RAIL_NAME], parent_wood),
        "rail_to_parent_brackets": hits(wood[RAIL_NAME], header_brackets),
        "bracket_to_parent_wood": hits(bracket, parent_wood),
        "bracket_to_parent_brackets": hits(bracket, header_brackets),
        "bolt_to_parent_wood": {
            n: v for n, s in bolts.items() if (v := hits(s, parent_wood))
        },
        "washer_to_parent_wood": {
            n: v for n, s in washers.items() if (v := hits(s, parent_wood))
        },
        "tool_to_parent_wood": {
            n: v for n, s in tools.items() if (v := hits(s, parent_wood))
        },
        "hardware_to_parent_hardware": {
            n: v for n, s in hardware.items() if (v := hits(s, parent_hardware))
        },
    }
    screw_hardware = {n: v for n, s in protected.items() if (v := hits(s, hardware))}
    panel_hardware = {n: v for n, s in hardware.items() if (v := hits(s, panels))}
    local_fail = (
        bool(receiver_loss or screw_hardware or panel_hardware or any(checks.values()))
        or any(h["receiver_thickness_mm"] < MIN_WOOD - TOL for h in holes)
        or any(
            not h["receiver_continuous"] or not h["factory_hole_clear"] for h in holes
        )
        or any(h["bore_missing_receiver_mm3"] > TOL for h in holes)
    )
    return {
        "status": "nominal_geometry_conflict"
        if local_fail
        else "partial_nominal_geometry_clear",
        "retail_model": "UB66",
        "manufacturer_model": "B66",
        "retail_url": "https://www.homedepot.com/p/313507617",
        "factory_dxf_url": "https://www.mitek-us.com/wp-content/uploads/files/Drawing%20Library/B66_3view.dxf",
        "esr_url": "https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf",
        "width_option": KERF_RIGHT,
        "rib_spacing_mm": SPACING,
        "station": "bottom right only",
        "protected_panel_screw_count": len(panel_rows),
        "fixed_screw_receiver_loss_mm3": receiver_loss,
        "factory_hole_count": len(holes),
        "factory_free_end_offsets_mm": list(OFFSETS),
        "factory_nominal_hole_diameter_mm": HOLE,
        "esr_minimum_wood_thickness_mm": MIN_WOOD,
        "esr_bolt_specification": "3/8-in ASTM A307 Grade A; Fy,b >= 45,000 psi",
        "esr_steel_specification": "12-ga ASTM A653 SS Grade 40 G90; base t >= 0.099 in",
        "illustrative_plate_thickness_mm": SHEET,
        "holes": holes,
        "parent_header_bracket_count": len(header_brackets),
        "parent_neighbor_checks": checks,
        "protected_screw_hardware_clashes": screw_hardware,
        "panel_hardware_clashes": panel_hardware,
        "nominal_access_envelopes_only": True,
        "actual_hardware_access_verified": False,
        "other_rail_ends_open": 5,
        "existing_frame_bolt_axes_resolved": False,
        "normal_duration_rating_adopted": False,
        "full_joint_resistance_verified": False,
        "connected_architecture_verdict": False,
        "drilling_released": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(screen_b66_route(), indent=2) + "\n")


if __name__ == "__main__":
    main()
