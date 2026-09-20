"""Conditional rear-backed center HL35 geometry screen; never drilling data."""

import argparse
import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
ANGLE_LENGTH = 127.0
ANGLE_REACH = 82.55
PLATE = 4.55  # illustrative 7-gauge envelope, not measured steel
POST_X = 184.15  # hypothetical solid nominal 6x8, actual supply unverified
POST_Y = 139.7
HEADER_Z = 88.9  # hypothetical solid 4x receiving thickness
BORE = 14.2875  # conditional 9/16-in wood clearance for 1/2-in bolt
SEAT_CLEARANCE = 1.0  # nominal CAD gap; not manufacturing tolerance


def _box(x0, y0, z0, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x0, y0, z0))


def _bounds(shape):
    b = shape.BoundingBox()
    return [round(v, 4) for v in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)]


def _hits(shape, candidates):
    return [
        {"name": name, "overlap_mm3": round(shape.intersect(other).Volume(), 3)}
        for name, other in candidates.items()
        if shape.intersect(other).Volume() > 0.01
    ]


def screen_rearback():
    """Test one lower-joint pose; upper joint and transfer remain unqualified."""
    with AXES.open(newline="") as handle:
        rows = [
            r
            for r in csv.DictReader(handle)
            if r["shop_opening_kind"] == "hillman_panel"
        ]
    if len(rows) != 66 or len({r["name"] for r in rows}) != 66:
        raise ValueError("expected 66 distinct protected kerf-right axes")
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    hb = raw["base_header"].BoundingBox()
    panel_back = raw["kicker_left"].BoundingBox().ymin
    if abs(raw["kicker_right"].BoundingBox().ymin - panel_back) > 1e-6:
        raise ValueError("kicker back planes differ")
    minimum_setback = ANGLE_REACH
    setback = minimum_setback + SEAT_CLEARANCE
    front = panel_back - setback
    rear = front - POST_Y
    header_rear = rear - ANGLE_REACH
    header = _box(
        hb.xmin, header_rear, hb.zmin, hb.xlen, hb.ymax - header_rear, HEADER_Z
    )
    post = _box(-POST_X / 2, rear, 0, POST_X, POST_Y, hb.zmin)
    # A permanent timber spline is needed at both fixed kicker screw axes
    # and the inner seam. This notched ideal solid avoids the lower bracket;
    # its transfer to the structural post is NOT qualified by contact alone.
    lower_top = hb.zmin - ANGLE_REACH
    upper_top = hb.zmin - PLATE
    backing_lower = _box(-POST_X / 2, front, 0, POST_X, panel_back - front, lower_top)
    backing_upper = _box(
        -POST_X / 2,
        front + PLATE,
        lower_top,
        POST_X,
        panel_back - front - PLATE,
        upper_top - lower_top,
    )
    backing = backing_lower.fuse(backing_upper).clean()
    x0 = -ANGLE_LENGTH / 2
    plates = {
        "front_vertical": _box(x0, front, lower_top, ANGLE_LENGTH, PLATE, ANGLE_REACH),
        "front_seat": _box(
            x0, front, hb.zmin - PLATE, ANGLE_LENGTH, ANGLE_REACH, PLATE
        ),
        "rear_vertical": _box(
            x0, rear - PLATE, lower_top, ANGLE_LENGTH, PLATE, ANGLE_REACH
        ),
        "rear_seat": _box(
            x0, rear - ANGLE_REACH, hb.zmin - PLATE, ANGLE_LENGTH, ANGLE_REACH, PLATE
        ),
    }
    # Simpson's drawing establishes the vertical bend offset and X pitch.
    # Applying the same offset to the horizontal flange is a nominal
    # symmetry assumption, not a factory-drilling dimension.
    bores = {}
    for i, x in enumerate((-31.75, 31.75), 1):
        bores[f"post_{i}"] = cq.Solid.makeCylinder(
            BORE / 2, POST_Y, cq.Vector(x, rear, hb.zmin - 50.8), cq.Vector(0, 1, 0)
        )
        for face, y in (("front", front + 50.8), ("rear", rear - 50.8)):
            bores[f"header_{face}_{i}"] = cq.Solid.makeCylinder(
                BORE / 2, HEADER_Z, cq.Vector(x, y, hb.zmin), cq.Vector(0, 0, 1)
            )
    panels = {k: v for k, v in raw.items() if k.startswith(("kicker_", "main_"))}
    panel_plate_clashes = [
        {"plate": name, **hit}
        for name, plate in plates.items()
        for hit in _hits(plate, panels)
    ]
    panel_backing_clashes = _hits(backing, panels)
    backing_front_angle_clashes = [
        {
            "plate": name,
            "overlap_mm3": round(backing.intersect(plates[name]).Volume(), 3),
        }
        for name in ("front_vertical", "front_seat")
        if backing.intersect(plates[name]).Volume() > 0.01
    ]
    screw_clashes = []
    kicker_axes = []
    for row in rows:
        start = cq.Vector(*(float(row[f"start_{a}_mm"]) for a in "xyz"))
        direction = cq.Vector(*(float(row[f"direction_{a}"]) for a in "xyz"))
        screw = cq.Solid.makeCylinder(
            float(row["occupied_diameter_mm"]) / 2,
            float(row["occupied_length_mm"]),
            start,
            direction,
        )
        hit_names = [
            name
            for name, solid in {**plates, **bores}.items()
            if screw.intersect(solid).Volume() > 0.01
        ]
        if hit_names:
            screw_clashes.append({"name": row["name"], "hardware": hit_names})
        if row["name"].startswith("round_kicker_") and "_center_" in row["name"]:
            axis_in_backing = max(
                0.0, min(float(row["occupied_length_mm"]), start.y - panel_back)
            )
            axis_in_backing = float(row["occupied_length_mm"]) - axis_in_backing
            kicker_axes.append(
                {
                    "name": row["name"],
                    "frozen_axis_in_backing_mm": round(axis_in_backing, 4),
                    "frozen_cylinder_backing_intersection_mm3": round(
                        screw.intersect(backing).Volume(), 3
                    ),
                }
            )
    excluded = {"base_header", "base_post_center_left", "base_post_center_right"}
    nonpanels = {k: v for k, v in raw.items() if k not in excluded and k not in panels}
    return {
        "status": "rejected_incomplete_installed_trial",
        "concept": "rearward solid common center post, notched permanent kicker-edge backing, opposed Y-face HL35 at a widened solid header",
        "source": str(AXES.relative_to(ROOT)),
        "protected_axis_count": len(rows),
        "kicker_center_axis_count": len(kicker_axes),
        "minimum_setback_for_front_seat_mm": minimum_setback,
        "trial_setback_mm": setback,
        "nominal_front_seat_panel_gap_mm": round(panel_back - (front + ANGLE_REACH), 4),
        "post_bounds_mm": _bounds(post),
        "header_bounds_mm": _bounds(header),
        "backing_bounds_mm": _bounds(backing),
        "lower_backing_depth_mm": round(panel_back - front, 4),
        "upper_backing_depth_mm": round(panel_back - front - PLATE, 4),
        "backing_gap_below_header_mm": PLATE,
        "kicker_center_axes": kicker_axes,
        "panel_plate_clashes": panel_plate_clashes,
        "panel_backing_clashes": panel_backing_clashes,
        "header_panel_clashes": _hits(header, panels),
        "post_panel_clashes": _hits(post, panels),
        "backing_front_angle_clashes": backing_front_angle_clashes,
        "protected_screw_hardware_clashes": screw_clashes,
        "post_other_wood_clashes": _hits(post, nonpanels),
        "header_other_wood_clashes": _hits(header, nonpanels),
        "backing_other_wood_clashes": _hits(backing, nonpanels),
        "post_header_contact_gap_mm": round(
            header.BoundingBox().zmin - post.BoundingBox().zmax, 4
        ),
        "nominal_post_bore_missing_wood_mm3": [
            round(max(0.0, bore.Volume() - bore.intersect(post).Volume()), 3)
            for name, bore in bores.items()
            if name.startswith("post_")
        ],
        "nominal_header_bore_missing_wood_mm3": [
            round(max(0.0, bore.Volume() - bore.intersect(header).Volume()), 3)
            for name, bore in bores.items()
            if name.startswith("header_")
        ],
        "horizontal_hole_offset_status": "assumed symmetry; manufacturer drawing does not explicitly dimension this offset",
        "front_bolt_head_outward_clearance_mm": 0.0,
        "front_bolt_head_status": "backing starts at the ideal front plate's outer face at bolt Z; any outward head/washer projection needs an unmodeled relief or access pocket",
        "backing_to_post_structural_connection": "unsolved",
        "upper_principal_to_header_joint": "unsolved; no common solid principal, installed upper angles, or upper bores modeled",
        "assembly_path": "Conditional order: install/inspect rear and front lower HL35 and bolts before removable backing; then fit notched backing and kicker panels. Removing backing for bolt access may require panel removal. Captive nuts, washer/head clearance, tools, maintenance access, and backing fastening are unverified.",
        "disposition": "Reject this installed trial as incomplete: a full-reach setback clears the fixed panels and accommodates frozen kicker axes, but the widened header intersects existing side timbers and principal toes, the backing leaves no outward head clearance at front post bolts, and the upper principal/header joint is undefined. The backing-to-post force path, small backing/header support gap, wood and steel resistance, tolerances, and assembly/disassembly remain unresolved. Hidden timber rework and bolt-head relief require a distinct complete trial. No fabrication or drilling coordinates.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_rearback(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
