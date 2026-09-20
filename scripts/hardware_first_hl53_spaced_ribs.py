"""Coarse HL53 spaced-rib component screen; no drilling coordinates."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hl53 import (
    ANGLE_LENGTH,
    ANGLE_REACH,
    BORE,
    FIRST_OFFSET,
    GAUGE7_NOMINAL,
    SECOND_OFFSET,
)
from scripts.hardware_first_center_hybrid import (
    AXES,
    ROOT,
    TOL,
    TOP,
    bounds,
    box,
    cylinder,
    hits,
)

OUTPUT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_hl53_spaced_ribs.json"
SPACINGS = (480, 520, 560)
RIB_WIDTH = 88.9
HL53_MIN_WOOD_THICKNESS = 88.9
ORIGINAL_RAIL_SECTION_THICKNESS = 38.1
REAR_DEEPENING = 80.0
HEADER_REAR = -250.0
HEADER_FRONT = -36.0
POST_HALF = 92.075
RAIL_GAP = 15.0
BOLT = 12.7
WASHER_DIAMETER = 25.4
WASHER_THICKNESS = 3.0
ACCESS_DIAMETER = 38.1
ACCESS_DEPTH = 30.0
POSE_Y = {
    "upper_front": -85.0,
    "upper_rib": -150.0,
    "lower_front": -165.0,
    "lower_rib": -70.0,
}


def _bore(point, direction, length, diameter=BORE):
    import cadquery as cq

    return cq.Solid.makeCylinder(
        diameter / 2, length, cq.Vector(*point), cq.Vector(*direction)
    )


def _principal(original, center):
    b = original.BoundingBox()
    growth = (RIB_WIDTH - b.xlen) / 2
    wide = original.fuse(
        *(
            original.translate((dx, 0, 0))
            for dx in (-growth, -growth / 2, growth / 2, growth)
        )
    ).clean()
    w = wide.BoundingBox()
    trimmed = wide.intersect(
        box(w.xmin - 1, w.ymin - 1, TOP, w.xlen + 2, w.ylen + 2, w.zmax - TOP + 2)
    ).clean()
    return (
        trimmed.fuse(trimmed.translate((0, -REAR_DEEPENING, 0)))
        .clean()
        .translate((center - (b.xmin + b.xmax) / 2, 0, 0))
    )


def _case(spacing, raw, panel_rows, frame_rows, panels):
    hb = raw["base_header"].BoundingBox()
    cap_half = spacing / 2 + RIB_WIDTH / 2
    header = (
        raw["base_header"]
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
        .clean()
    )
    post = box(
        -POST_HALF, HEADER_REAR, 0, 2 * POST_HALF, HEADER_FRONT - HEADER_REAR, hb.zmin
    )
    wood = {"base_header": header, "base_post_center": post}
    for side, sign in (("left", -1), ("right", 1)):
        wood[f"front_principal_{side}"] = _principal(
            raw[f"base_principal_center_{side}"], sign * 70
        )
        wood[f"rib_principal_{side}"] = _principal(
            raw[f"base_principal_center_{side}"], sign * spacing / 2
        )
        wood[f"rib_post_{side}"] = box(
            sign * spacing / 2 - RIB_WIDTH / 2,
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
    rail_inner = spacing / 2 + RIB_WIDTH / 2 + RAIL_GAP
    for name in rail_names:
        b = raw[name].BoundingBox()
        left = name.endswith("left")
        x0, x1 = (b.xmin - 1, -rail_inner) if left else (rail_inner, b.xmax + 1)
        wood[name] = (
            raw[name]
            .intersect(box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2))
            .clean()
        )

    # Preserve original receiver names for the fixed kerf-right axes.
    receivers = dict(raw)
    receivers.update(wood)
    for side in ("left", "right"):
        receivers[f"base_principal_center_{side}"] = wood[f"front_principal_{side}"]
        receivers[f"base_post_center_{side}"] = post
    replaced = {
        "base_header",
        *rail_names,
        "base_principal_center_left",
        "base_principal_center_right",
        "base_post_center_left",
        "base_post_center_right",
    }
    adjacent = {n: s for n, s in raw.items() if n not in replaced and n not in panels}

    brackets = {}
    paths = {}
    bores = {}
    section_probes = {}
    washers = {}
    access = {}
    bolt_checks = []
    wrong_sign = []

    def add_bracket(name, member, seat_member, face, direction, y, bend_z, rise):
        """X-face HL53: both flange offsets follow the actual seat direction."""
        mb = wood[member].BoundingBox()
        plate_x = face if direction == 1 else face - GAUGE7_NOMINAL
        seat_x = face if direction == 1 else face - ANGLE_REACH
        z0 = bend_z if rise == 1 else bend_z - ANGLE_REACH
        seat_z = bend_z if rise == 1 else bend_z - GAUGE7_NOMINAL
        vertical = box(
            plate_x, y - ANGLE_LENGTH / 2, z0, GAUGE7_NOMINAL, ANGLE_LENGTH, ANGLE_REACH
        )
        seat = box(
            seat_x,
            y - ANGLE_LENGTH / 2,
            seat_z,
            ANGLE_REACH,
            ANGLE_LENGTH,
            GAUGE7_NOMINAL,
        )
        hole_solids = {}
        for index, offset in enumerate((FIRST_OFFSET, SECOND_OFFSET), 1):
            for flange in ("vertical", "seat"):
                key = f"{name}_{flange}_{index}"
                if flange == "vertical":
                    z = bend_z + rise * offset
                    hole = _bore((plate_x, y, z), (1, 0, 0), GAUGE7_NOMINAL)
                    bore = _bore((mb.xmin, y, z), (1, 0, 0), mb.xlen)
                    section_probes[key] = _bore(
                        (mb.xmin, y, z), (1, 0, 0), mb.xlen, 0.2
                    )
                    start = (min(mb.xmin, plate_x), y, z)
                    path = _bore(start, (1, 0, 0), mb.xlen + GAUGE7_NOMINAL, BOLT)
                    # Explicit ideal washer and tool clearance outside both X faces.
                    outer = face + direction * GAUGE7_NOMINAL
                    opposite = mb.xmin if direction == 1 else mb.xmax
                    ends = ((outer, direction), (opposite, -direction))
                    normal = (1, 0, 0)
                else:
                    x = face + direction * offset
                    if (
                        not min(seat_x, seat_x + ANGLE_REACH)
                        <= x
                        <= max(seat_x, seat_x + ANGLE_REACH)
                    ):
                        wrong_sign.append(key)
                    hole = _bore((x, y, seat_z), (0, 0, 1), GAUGE7_NOMINAL)
                    sb = wood[seat_member].BoundingBox()
                    bore = _bore((x, y, sb.zmin), (0, 0, 1), sb.zlen)
                    section_probes[key] = _bore(
                        (x, y, sb.zmin), (0, 0, 1), sb.zlen, 0.2
                    )
                    start = (x, y, min(sb.zmin, seat_z))
                    path = _bore(start, (0, 0, 1), sb.zlen + GAUGE7_NOMINAL, BOLT)
                    outer = bend_z + rise * GAUGE7_NOMINAL
                    opposite = sb.zmin if rise == 1 else sb.zmax
                    ends = ((outer, rise), (opposite, -rise))
                    normal = (0, 0, 1)
                hole_solids[key] = hole
                paths[key] = path
                bores[key] = (member if flange == "vertical" else seat_member, bore)
                washers[key] = []
                access[key] = []
                for coordinate, sense in ends:
                    point = (
                        (coordinate, y, z)
                        if flange == "vertical"
                        else (x, y, coordinate)
                    )
                    vector = tuple(sense * component for component in normal)
                    washers[key].append(
                        _bore(point, vector, WASHER_THICKNESS, WASHER_DIAMETER)
                    )
                    access[key].append(
                        _bore(point, vector, ACCESS_DEPTH, ACCESS_DIAMETER)
                    )
        body = vertical.fuse(seat).clean()
        for hole in hole_solids.values():
            body = body.cut(hole)
        brackets[name] = body.clean()
        for key, hole in hole_solids.items():
            path = paths[key]
            receiver, bore = bores[key]
            section = section_probes[key].intersect(wood[receiver])
            axis = "x" if "_vertical_" in key else "z"
            local_thickness = round(
                sum(
                    getattr(solid.BoundingBox(), f"{axis}len")
                    for solid in section.Solids()
                ),
                3,
            )
            bolt_checks.append(
                {
                    "id": key,
                    "receiver": receiver,
                    "wood_thickness_along_bolt_mm": local_thickness,
                    "meets_hl53_minimum_wood_thickness": (
                        local_thickness >= HL53_MIN_WOOD_THICKNESS - TOL
                    ),
                    "own_hole_corridor_mm3": round(path.intersect(hole).Volume(), 3),
                    "receiver_overlap_mm3": round(
                        path.intersect(wood[receiver]).Volume(), 3
                    ),
                    "bore_missing_receiver_mm3": round(
                        max(0, bore.Volume() - bore.intersect(wood[receiver]).Volume()),
                        3,
                    ),
                    "own_steel_clash_mm3": round(
                        path.intersect(brackets[name]).Volume(), 3
                    ),
                }
            )

    for side, sign in (("left", -1), ("right", 1)):
        front = wood[f"front_principal_{side}"].BoundingBox()
        rib = wood[f"rib_principal_{side}"].BoundingBox()
        rib_post = wood[f"rib_post_{side}"].BoundingBox()
        add_bracket(
            f"upper_front_{side}",
            f"front_principal_{side}",
            "base_header",
            front.xmin if sign < 0 else front.xmax,
            sign,
            POSE_Y["upper_front"],
            TOP,
            1,
        )
        add_bracket(
            f"upper_rib_{side}",
            f"rib_principal_{side}",
            "base_header",
            rib.xmax if sign < 0 else rib.xmin,
            -sign,
            POSE_Y["upper_rib"],
            TOP,
            1,
        )
        add_bracket(
            f"lower_front_{side}",
            "base_post_center",
            "base_header",
            -POST_HALF if sign < 0 else POST_HALF,
            sign,
            POSE_Y["lower_front"],
            hb.zmin,
            -1,
        )
        add_bracket(
            f"lower_rib_{side}",
            f"rib_post_{side}",
            "base_header",
            rib_post.xmax if sign < 0 else rib_post.xmin,
            -sign,
            POSE_Y["lower_rib"],
            hb.zmin,
            -1,
        )
    rail_probe = None
    if spacing == 520:
        rail = wood["base_rail_bottom_right"].BoundingBox()
        rib = wood["rib_principal_right"].BoundingBox()
        add_bracket(
            "rail_probe_bottom_right",
            "rib_principal_right",
            "base_rail_bottom_right",
            rib.xmax,
            1,
            (rail.ymin + rail.ymax) / 2,
            rail.zmax,
            1,
        )
        rail_checks = [v for v in bolt_checks if v["id"].startswith("rail_probe_")]
        rail_probe = {
            "factory_bracket": "HL53",
            "station": "bottom right only",
            "original_rail_section_thickness_mm": ORIGINAL_RAIL_SECTION_THICKNESS,
            "rail_retains_original_1_5_in_section": True,
            "bolt_checks": rail_checks,
            "all_bolts_meet_hole_and_receiver": all(
                v["own_hole_corridor_mm3"] > TOL and v["receiver_overlap_mm3"] > TOL
                for v in rail_checks
            ),
            "all_bores_contained": all(
                v["bore_missing_receiver_mm3"] <= TOL for v in rail_checks
            ),
            "all_receivers_meet_88_9_mm_minimum": all(
                v["meets_hl53_minimum_wood_thickness"] for v in rail_checks
            ),
        }

    screw_loss = {}
    for row in panel_rows:
        screw = cylinder(row)
        old = screw.intersect(raw[row["second_member"]]).Volume()
        new = screw.intersect(receivers[row["second_member"]]).Volume()
        if old - new > TOL or new <= TOL:
            screw_loss[row["name"]] = round(old - new, 3)
    panel_screws = {row["name"]: cylinder(row) for row in panel_rows}
    frame = {row["name"]: cylinder(row) for row in frame_rows}
    pair_bores = {key: solid for key, (_, solid) in bores.items()}
    washer_solids = {
        f"{key}_{i}": solid
        for key, pair in washers.items()
        for i, solid in enumerate(pair)
    }
    access_solids = {
        f"{key}_{i}": solid
        for key, pair in access.items()
        for i, solid in enumerate(pair)
    }

    def pair_hits(shapes):
        items = list(shapes.items())
        return {
            f"{name} / {other}": round(volume, 3)
            for i, (name, solid) in enumerate(items)
            for other, target in items[i + 1 :]
            if (volume := solid.intersect(target).Volume()) > TOL
        }

    foreign_wood = {
        key: hits(path, {n: s for n, s in wood.items() if n != bores[key][0]})
        for key, path in paths.items()
    }
    checks = {
        "bracket_panel": {n: v for n, s in brackets.items() if (v := hits(s, panels))},
        "bracket_wood": {n: v for n, s in brackets.items() if (v := hits(s, wood))},
        "bracket_adjacent": {
            n: v for n, s in brackets.items() if (v := hits(s, adjacent))
        },
        "bolt_panel": {n: v for n, s in paths.items() if (v := hits(s, panels))},
        "bolt_foreign_wood": {n: v for n, v in foreign_wood.items() if v},
        "bolt_foreign_bracket": {
            n: v
            for n, s in paths.items()
            if (
                v := hits(
                    s, {k: b for k, b in brackets.items() if not n.startswith(k + "_")}
                )
            )
        },
        "screw_hardware": {
            n: v
            for n, s in panel_screws.items()
            if (v := hits(s, {**brackets, **pair_bores}))
        },
        "frame_hardware": {
            n: v for n, s in frame.items() if (v := hits(s, {**brackets, **pair_bores}))
        },
        "washer_panel": {
            n: v for n, s in washer_solids.items() if (v := hits(s, panels))
        },
        "washer_foreign_wood": {
            n: v for n, s in washer_solids.items() if (v := hits(s, wood))
        },
        "access_panel": {
            n: v for n, s in access_solids.items() if (v := hits(s, panels))
        },
        "access_foreign_wood": {
            n: v for n, s in access_solids.items() if (v := hits(s, wood))
        },
        "changed_wood_panel": {n: v for n, s in wood.items() if (v := hits(s, panels))},
        "changed_wood_adjacent": {
            n: v for n, s in wood.items() if (v := hits(s, adjacent))
        },
        "changed_wood_pairs": pair_hits(wood),
        "independent_bracket_pairs": pair_hits(brackets),
    }
    missing_hole = [v["id"] for v in bolt_checks if v["own_hole_corridor_mm3"] <= TOL]
    missing_receiver = [
        v["id"] for v in bolt_checks if v["receiver_overlap_mm3"] <= TOL
    ]
    incomplete = [v["id"] for v in bolt_checks if v["bore_missing_receiver_mm3"] > TOL]
    steel_hits = [v["id"] for v in bolt_checks if v["own_steel_clash_mm3"] > TOL]
    thin_wood = [
        v["id"] for v in bolt_checks if not v["meets_hl53_minimum_wood_thickness"]
    ]
    failure = set()
    if wrong_sign or missing_hole or missing_receiver or incomplete or steel_hits:
        failure.add("bolt_or_bore_geometry")
    if thin_wood:
        failure.add("catalog_inapplicable_wood_thickness")
    if screw_loss:
        failure.add("fixed_screw_receiver_loss")
    for label, found in checks.items():
        if found:
            failure.add(label)
    # Only one of six affected rail ends gets a probe in the 520-mm case.
    failure.add("rail_to_rib_connection_open")
    front_names = ["front_principal_left", "front_principal_right", "base_post_center"]
    rib_names = [
        f"rib_{kind}_{side}"
        for side in ("left", "right")
        for kind in ("principal", "post")
    ]
    front_rib = {
        n: v
        for n in front_names
        if (v := hits(wood[n], {r: wood[r] for r in rib_names}))
    }
    header_links = [v for v in bolt_checks if not v["id"].startswith("rail_probe_")]
    return {
        "rib_spacing_mm": spacing,
        "status": "rejected_nominal_geometry" if failure else "nominal_fit_only",
        "failure_classes": sorted(failure),
        "bracket_count": len(brackets),
        "header_link_bracket_count": 8,
        "header_links_have_holes_and_receivers": len(header_links) == 32
        and all(
            v["own_hole_corridor_mm3"] > TOL and v["receiver_overlap_mm3"] > TOL
            for v in header_links
        ),
        "front_carrier_rib_overlaps_mm3": front_rib,
        "rail_connection_probe": rail_probe,
        "connected_architecture_verdict": False,
        "bolt_checks": bolt_checks,
        "wrong_side_header_holes": wrong_sign,
        "bolt_missing_own_hole_corridor": missing_hole,
        "bolt_missing_receiver": missing_receiver,
        "bore_exits_receiver": incomplete,
        "bolt_hits_own_steel": steel_hits,
        "below_hl53_minimum_wood_thickness": thin_wood,
        "hl53_wood_thickness_catalog_applicable": not thin_wood,
        "checks_mm3": checks,
        "fixed_screw_receiver_loss_mm3": screw_loss,
        "kicker_seam_supported": (
            post.BoundingBox().xmin < -1.5875 < post.BoundingBox().xmax
        ),
        "changed_wood_bounds_mm": {n: bounds(s) for n, s in wood.items()},
        "bracket_bounds_mm": {n: bounds(s) for n, s in brackets.items()},
        "rail_inner_end_abs_x_mm": rail_inner,
        "rail_to_rib_gap_mm": RAIL_GAP,
        "one_piece_wood": {n: len(s.Solids()) == 1 for n, s in wood.items()},
    }


def screen_spaced_ribs():
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len({r["name"] for r in panel_rows}) != 66:
        raise ValueError("expected 66 fixed panel/kicker axes")
    if len(frame_rows) != 12 or len({r["name"] for r in frame_rows}) != 12:
        raise ValueError("expected 12 original frame axes")
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    cases = [
        _case(spacing, raw, panel_rows, frame_rows, panels) for spacing in SPACINGS
    ]
    return {
        "status": "coarse_comparator_only",
        "source_axes": str(AXES.relative_to(ROOT)),
        "width_option": KERF_RIGHT,
        "fixed_panel_kicker_axis_count": len(panel_rows),
        "fixed_panel_solid_count": len(panels),
        "existing_frame_axis_count": len(frame_rows),
        "hl53_nominal_mm": {
            "bend_length": ANGLE_LENGTH,
            "leg_reach": ANGLE_REACH,
            "hole_offsets_from_bend": [FIRST_OFFSET, SECOND_OFFSET],
            "assumed_7_gauge_envelope": GAUGE7_NOMINAL,
            "assumed_hole_diameter": BORE,
            "hl53_minimum_wood_thickness": HL53_MIN_WOOD_THICKNESS,
            "ideal_bolt_diameter": BOLT,
            "ideal_washer_diameter": WASHER_DIAMETER,
            "ideal_washer_thickness": WASHER_THICKNESS,
            "ideal_tool_diameter": ACCESS_DIAMETER,
            "ideal_tool_depth": ACCESS_DEPTH,
        },
        "upper_lower_pose_y_mm": POSE_Y,
        "header_rear_front_y_mm": [HEADER_REAR, HEADER_FRONT],
        "rearward_principal_deepening_mm": REAR_DEEPENING,
        "cases": cases,
        "old_outward_seat_header_bore_sign": "Quarantined: each seat axis is face_x + seat_direction * factory offset, then checked inside its own modeled flange; no outward-seat axes are imported.",
        "connection_limit": "Eight nominal HL53 links join fixed front carriers/central backing and separated ribs to one header, but their bodies clash with neighboring wood. Only one of six rail ends has an HL53 fit probe; rail-to-rib factory connections and a connected architecture are not established.",
        "unresolved": [
            "delivered HL53 bend, gauge and holes",
            "actual bolt stacks and tool sweep",
            "formal edge/end distances and wood joint resistance",
            "rail-to-rib factory connection",
            "complete frame load path",
        ],
        "material_or_rating_adopted": False,
        "drilling_released": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_spaced_ribs(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
