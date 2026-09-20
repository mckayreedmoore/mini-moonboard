"""Wide HL53 rib spacing and one one-piece rail receiver fit probe."""

import argparse
import csv
import json
import math
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
    blank_envelope,
    bounds,
    box,
    cylinder,
    hits,
)
from scripts.hardware_first_hl53_spaced_ribs import (
    ACCESS_DEPTH,
    ACCESS_DIAMETER,
    BOLT,
    HL53_MIN_WOOD_THICKNESS,
    RAIL_GAP,
    RIB_WIDTH,
    WASHER_DIAMETER,
    WASHER_THICKNESS,
    _bore,
    _case,
    _principal,
)

OUTPUT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_hl53_wide_ribs.json"
SPACINGS = (620, 660, 700)
JOINT_SPACING = 660
JOINT_Y = -60.0
INTEGRAL_RAIL_DEPTH = 100.0
INTEGRAL_RAIL_LENGTH = ANGLE_REACH + 1.0
INTEGRAL_RAIL_Y_MIN = -92.0
INTEGRAL_RAIL_Y_MAX = -28.0
SQUARE_SAMPLE_STEP_DEG = 0.001
LOWES_6X6_URL = (
    "https://www.lowes.com/pd/6-in-x-6-in-x-8-ft-douglas-fir-lumber-"
    "common-5-652-in-x-5-652-in-x-8-ft-actual/1000009798"
)


def _sampled_square_blank(shape):
    """Find the smallest sampled maximum Y/Z extent about the rail's X axis."""
    points = [(vertex.Y, vertex.Z) for vertex in shape.Vertices()]
    best = None
    # A square exchanges its sides at 90 degrees, so [0, 90] covers all poses.
    for step in range(90001):
        angle = step * SQUARE_SAMPLE_STEP_DEG
        radians = math.radians(angle)
        cosine, sine = math.cos(radians), math.sin(radians)
        y_values = [y * cosine + z * sine for y, z in points]
        z_values = [-y * sine + z * cosine for y, z in points]
        y_width = max(y_values) - min(y_values)
        z_width = max(z_values) - min(z_values)
        candidate = (max(y_width, z_width), angle, y_width, z_width)
        if best is None or candidate < best:
            best = candidate
    maximum, angle, y_width, z_width = best
    return {
        "method": "Rail vertices rotated about X through 0–90 degrees; minimum sampled max(Y,Z) extent, not minimum area.",
        "sample_step_deg": SQUARE_SAMPLE_STEP_DEG,
        "rotation_about_x_deg": round(angle, 3),
        "x_length_mm": round(shape.BoundingBox().xlen, 4),
        "yz_extents_mm": [round(y_width, 4), round(z_width, 4)],
        "max_yz_extent_mm": round(maximum, 4),
    }


def _retail_blank_comparator(blank):
    """Record a listing-sized comparator without accepting delivered stock."""
    listed = [5.652 * 25.4, 5.652 * 25.4, 8 * 12 * 25.4]
    return {
        "retailer": "Lowe's",
        "listing": "6-in x 6-in x 8-ft #2 Better Douglas Fir Green Lumber",
        "model": "637643",
        "grade": "#2 Better",
        "species": "Douglas fir",
        "listed_condition": "green; anti-stain treated per listing",
        "listing_url": LOWES_6X6_URL,
        "listed_actual_inches": [5.652, 5.652, 96],
        "listed_actual_mm": [round(value, 4) for value in listed],
        "nominal_dimensions_enclose_sampled_blank": (
            blank["max_yz_extent_mm"] <= min(listed[:2])
            and blank["x_length_mm"] <= listed[2]
        ),
        "stock_accepted": False,
        "open_checks": [
            "local availability",
            "delivered dimensions",
            "moisture and drying",
            "grade verification",
            "machining allowance",
            "treatment suitability",
        ],
    }


def _rail_joint(raw, panels, panel_rows, parent_case, gap_mm):
    """Probe one HL53 from the right rib to a locally deep one-piece rail."""
    side = "right"
    name = f"base_rail_bottom_{side}"
    rib = _principal(raw[f"base_principal_center_{side}"], JOINT_SPACING / 2)
    rib_box = rib.BoundingBox()
    original = raw[name]
    b = original.BoundingBox()
    rail_inner = JOINT_SPACING / 2 + RIB_WIDTH / 2 + gap_mm
    trimmed = original.intersect(
        box(
            rail_inner,
            b.ymin - 1,
            b.zmin - 1,
            b.xmax + 1 - rail_inner,
            b.ylen + 2,
            b.zlen + 2,
        )
    ).clean()
    t = trimmed.BoundingBox()
    integral = box(
        rail_inner,
        INTEGRAL_RAIL_Y_MIN,
        t.zmax - INTEGRAL_RAIL_DEPTH,
        INTEGRAL_RAIL_LENGTH,
        INTEGRAL_RAIL_Y_MAX - INTEGRAL_RAIL_Y_MIN,
        INTEGRAL_RAIL_DEPTH,
    )
    rail = trimmed.fuse(integral).clean()
    face = rib_box.xmax
    bend_z = t.zmax
    y0 = JOINT_Y - ANGLE_LENGTH / 2
    upright = box(face, y0, bend_z, GAUGE7_NOMINAL, ANGLE_LENGTH, ANGLE_REACH)
    seat = box(face, y0, bend_z, ANGLE_REACH, ANGLE_LENGTH, GAUGE7_NOMINAL)
    # A thin horizontal slice measures actual wood contact below the full
    # nominal flange footprint; bolt overlap alone cannot establish support.
    contact = rail.intersect(
        box(face, y0, bend_z - 0.1, ANGLE_REACH, ANGLE_LENGTH, 0.1)
    )
    contact_bounds = contact.BoundingBox() if contact.Volume() > TOL else None
    supported_length = round(contact_bounds.xlen, 3) if contact_bounds else 0.0
    leading_unsupported = (
        round(max(0, contact_bounds.xmin - face), 3) if contact_bounds else ANGLE_REACH
    )
    holes = {}
    bores = {}
    paths = {}
    washers = {}
    tools = {}
    bolt_checks = []
    for index, offset in enumerate((FIRST_OFFSET, SECOND_OFFSET), 1):
        for flange in ("vertical", "seat"):
            key = f"rail_{flange}_{index}"
            if flange == "vertical":
                z = bend_z + offset
                receiver = rib
                hole = _bore((face, JOINT_Y, z), (1, 0, 0), GAUGE7_NOMINAL)
                bore = _bore((rib_box.xmin, JOINT_Y, z), (1, 0, 0), rib_box.xlen)
                path = _bore(
                    (rib_box.xmin, JOINT_Y, z),
                    (1, 0, 0),
                    rib_box.xlen + GAUGE7_NOMINAL,
                    BOLT,
                )
                section = _bore(
                    (rib_box.xmin, JOINT_Y, z), (1, 0, 0), rib_box.xlen, 0.2
                ).intersect(receiver)
                thickness = sum(s.BoundingBox().xlen for s in section.Solids())
                ends = [
                    ((face + GAUGE7_NOMINAL, JOINT_Y, z), (1, 0, 0)),
                    ((rib_box.xmin, JOINT_Y, z), (-1, 0, 0)),
                ]
            else:
                x = face + offset
                receiver = rail
                hole = _bore((x, JOINT_Y, bend_z), (0, 0, 1), GAUGE7_NOMINAL)
                centerline = _bore(
                    (x, JOINT_Y, t.zmin - 1), (0, 0, 1), t.zlen + 2, 0.2
                ).intersect(rail)
                section_box = centerline.BoundingBox()
                bottom, top = section_box.zmin, section_box.zmax
                thickness = sum(s.BoundingBox().zlen for s in centerline.Solids())
                bore = _bore((x, JOINT_Y, bottom), (0, 0, 1), top - bottom)
                path = _bore(
                    (x, JOINT_Y, bottom), (0, 0, 1), top - bottom + GAUGE7_NOMINAL, BOLT
                )
                ends = [
                    ((x, JOINT_Y, bend_z + GAUGE7_NOMINAL), (0, 0, 1)),
                    ((x, JOINT_Y, bottom), (0, 0, -1)),
                ]
            holes[key] = hole
            bores[key] = bore
            paths[key] = path
            washers[key] = [
                _bore(point, axis, WASHER_THICKNESS, WASHER_DIAMETER)
                for point, axis in ends
            ]
            tools[key] = [
                _bore(point, axis, ACCESS_DEPTH, ACCESS_DIAMETER)
                for point, axis in ends
            ]
            bolt_checks.append(
                {
                    "id": key,
                    "receiver": "rib_principal_right" if flange == "vertical" else name,
                    "own_hole_corridor_mm3": round(path.intersect(hole).Volume(), 3),
                    "receiver_overlap_mm3": round(path.intersect(receiver).Volume(), 3),
                    "bore_missing_receiver_mm3": round(
                        max(0, bore.Volume() - bore.intersect(receiver).Volume()), 3
                    ),
                    "wood_thickness_along_bolt_mm": round(thickness, 3),
                    "meets_hl53_88_9_mm_minimum": thickness
                    >= HL53_MIN_WOOD_THICKNESS - TOL,
                }
            )
    bracket = upright.fuse(seat).clean()
    for hole in holes.values():
        bracket = bracket.cut(hole)
    bracket = bracket.clean()
    for item in bolt_checks:
        item["bolt_hits_own_steel_mm3"] = round(
            paths[item["id"]].intersect(bracket).Volume(), 3
        )

    nearby = {"rib_principal_right": rib, name: rail}
    screw_loss = {}
    for row in panel_rows:
        if row["second_member"] != name:
            continue
        screw = cylinder(row)
        old = screw.intersect(original).Volume()
        new = screw.intersect(rail).Volume()
        if old - new > TOL or new <= TOL:
            screw_loss[row["name"]] = round(old - new, 3)
    screws = {r["name"]: cylinder(r) for r in panel_rows}
    screw_hardware = {
        key: value
        for key, shaft in screws.items()
        if (value := hits(shaft, {"bracket": bracket, **bores}))
    }
    checks = {
        "rail_panel": hits(rail, panels),
        "rail_rib": hits(rail, {"rib_principal_right": rib}),
        "bracket_panel": hits(bracket, panels),
        "bracket_wood": hits(bracket, nearby),
        "bolt_panel": {
            key: found for key, path in paths.items() if (found := hits(path, panels))
        },
        "screw_hardware": screw_hardware,
        "washer_panel": {
            f"{key}_{i}": found
            for key, pair in washers.items()
            for i, solid in enumerate(pair)
            if (found := hits(solid, panels))
        },
        "tool_panel": {
            f"{key}_{i}": found
            for key, pair in tools.items()
            for i, solid in enumerate(pair)
            if (found := hits(solid, panels))
        },
        "washer_wood": {
            f"{key}_{i}": found
            for key, pair in washers.items()
            for i, solid in enumerate(pair)
            if (found := hits(solid, nearby))
        },
        "tool_wood": {
            f"{key}_{i}": found
            for key, pair in tools.items()
            for i, solid in enumerate(pair)
            if (found := hits(solid, nearby))
        },
    }
    failures = {label for label, found in checks.items() if found}
    if any(
        v["own_hole_corridor_mm3"] <= TOL
        or v["receiver_overlap_mm3"] <= TOL
        or v["bore_missing_receiver_mm3"] > TOL
        or v["bolt_hits_own_steel_mm3"] > TOL
        for v in bolt_checks
    ):
        failures.add("bolt_or_bore_geometry")
    if any(not v["meets_hl53_88_9_mm_minimum"] for v in bolt_checks):
        failures.add("catalog_inapplicable_wood_thickness")
    if screw_loss:
        failures.add("fixed_screw_receiver_loss")
    if len(rail.Solids()) != 1:
        failures.add("one_piece_rail")
    if ANGLE_REACH - supported_length > TOL:
        failures.add("unsupported_hl53_seat")
    if failures == {"unsupported_hl53_seat"}:
        status = "isolated_bolt_geometry_unsupported_seat"
    else:
        status = (
            "rejected_isolated_geometry"
            if failures
            else "isolated_joint_geometry_clear"
        )
    result = {
        "rib_spacing_mm": JOINT_SPACING,
        "bracket_model": "HL53",
        "station": "bottom right only",
        "status": status,
        "failure_classes": sorted(failures),
        "rail_to_rib_gap_mm": gap_mm,
        "seat_nominal_reach_mm": ANGLE_REACH,
        "seat_leading_unsupported_mm": leading_unsupported,
        "seat_supported_length_mm": supported_length,
        "seat_unsupported_total_mm": round(ANGLE_REACH - supported_length, 3),
        "seat_contact_area_mm2": round(contact.Volume() / 0.1, 3),
        "catalog_applicability_verified": False,
        "rail_profile": "Original rail resected at inner end, locally deepened as one continuous machined blank; no joined plies.",
        "rail_inner_end_x_mm": rail_inner,
        "rail_bounds_mm": bounds(rail),
        "sampled_one_piece_rail_blank_mm": blank_envelope(rail, True),
        "blank_method": "Minimum sampled Y/Z rectangle every 0.1 degree plus X extent; no trim, defects or machining allowance.",
        "one_piece_stock_status": "unverified; nominal dimensional comparator is not delivered-stock acceptance",
        "rib_bounds_mm": bounds(rib),
        "bracket_bounds_mm": bounds(bracket),
        "bolt_checks": bolt_checks,
        "checks_mm3": checks,
        "fixed_screw_receiver_loss_mm3": screw_loss,
        "one_piece_rail": len(rail.Solids()) == 1,
        "all_66_axes_preserved": parent_case["fixed_screw_receiver_loss_mm3"] == {}
        and not screw_loss,
        "kicker_seam_supported": parent_case["kicker_seam_supported"],
        "connected_architecture_verdict": False,
        "screened_wood": ["rib_principal_right", name],
        "parent_neighbor_integration_checked": False,
        "not_screened_against": [
            "changed parent header and front carriers",
            "other original wood members",
            "eight parent header-link brackets and their bolt/tool envelopes",
        ],
        "scope_limit": "Only this rail, its rib, fixed panels and screw axes, and the one HL53 joint were checked together; no full parent-assembly fit claim.",
        "modeled_access_scope": "Approximate 25.4-mm washer and 38.1-mm by 30-mm straight tool cylinders only.",
        "actual_head_nut_stack_verified": False,
        "actual_tool_access_verified": False,
        "open_checks": [
            "full bolt head and nut envelopes and exact purchased bolt length",
            "tool sweep beyond the modeled 30-mm access cylinders",
            "delivered HL53 dimensions and full catalog installation applicability",
        ],
    }
    if gap_mm == 0:
        blank = _sampled_square_blank(rail)
        result["sampled_square_rail_blank"] = blank
        result["retail_blank_comparator"] = _retail_blank_comparator(blank)
    return result


def screen_wide_ribs():
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
    cases = []
    for spacing in SPACINGS:
        case = _case(spacing, raw, panel_rows, frame_rows, panels)
        header_clear = case["failure_classes"] == ["rail_to_rib_connection_open"]
        case["header_fit_status"] = (
            "nominal_clash_clear" if header_clear else "nominal_clash_found"
        )
        case["assembly_status"] = "incomplete_connected_assembly"
        if header_clear:
            case["status"] = "partial_nominal_header_fit"
        cases.append(case)
    joint = _rail_joint(raw, panels, panel_rows, cases[1], RAIL_GAP)
    zero_gap = _rail_joint(raw, panels, panel_rows, cases[1], 0.0)
    return {
        "status": "geometry_comparison_only",
        "source_axes": str(AXES.relative_to(ROOT)),
        "width_option": KERF_RIGHT,
        "fixed_panel_kicker_axis_count": len(panel_rows),
        "fixed_panel_solid_count": len(panels),
        "existing_frame_axis_count": len(frame_rows),
        "rib_spacings_mm": list(SPACINGS),
        "cases": cases,
        "rail_joint": joint,
        "zero_gap_probe": zero_gap,
        "connected_architecture_verdict": False,
        "load_axis_scope": "The corrected HL load-axis audit is separate. This report makes no load-axis or capacity verdict.",
        "remaining_open_rail_ends": 5,
        "seat_support_limit": "The 15-mm joint has an unsupported leading HL53 flange; no rated gap allowance is adopted. The zero-gap probe is a separate geometry alternative, not catalog acceptance.",
        "open_checks": [
            "five remaining rail-to-rib factory connections and full load path",
            "full bolt head/nut stacks and tool sweep beyond ideal cylinders",
            "delivered HL53 geometry and exact catalog installation applicability",
        ],
        "material_or_rating_adopted": False,
        "drilling_released": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_wide_ribs(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
