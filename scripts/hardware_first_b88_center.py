"""One nominal B88 center-joint fit screen; never fabrication geometry."""

import argparse
import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
REACH = 203.2
WIDTH = 50.8
PLATE = 2.66  # Illustrative 12-gauge sheet, not delivered thickness.
HEADER_DEPTH = 76.2  # MiTek minimum receiving thickness, conceptual solid stock.
POST_WIDTH = 184.15  # Conceptual solid common lower receiver; supply unverified.
PRINCIPAL_WIDTH = 88.9  # Conceptual solid upper receivers, 3.5-in actual.
HORIZONTAL = (28.6, 92.2, 155.8)  # DXF free-end offsets, mm.
VERTICAL = (29.0, 92.6, 156.2)
NOMINAL_HOLE_DIAMETER = 10.3  # DXF circle, not a wood bit specification.


def _box(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def _hit(shape, other):
    return shape.intersect(other).Volume() > 0.01


def _screw_rows():
    with AXES.open(newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["shop_opening_kind"] == "hillman_panel"
        ]
    if len(rows) != 66 or len({row["name"] for row in rows}) != 66:
        raise ValueError("expected 66 distinct protected kerf-right axes")
    return rows


def _screw(row):
    start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
    direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
    return cq.Solid.makeCylinder(
        float(row["occupied_diameter_mm"]) / 2,
        float(row["occupied_length_mm"]),
        start,
        direction,
    )


def screen_b88_center():
    """Screen one outer-X-face upper/lower B88 arrangement in kerf-right CAD."""
    rows = _screw_rows()
    original = {
        part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()
    }
    hb = original["base_header"].BoundingBox()
    front = hb.ymax
    back = hb.ymin
    upper_y = front - WIDTH
    lower_y = back
    if upper_y - (lower_y + WIDTH) < 0:
        raise ValueError("opposed brace widths overlap")

    # New conceptual solids are explicit; the protected panel shapes and axes
    # are read unchanged. Upper toe cuts are needed to meet the thicker header.
    header = _box(hb.xmin, back, hb.zmin, hb.xlen, hb.ylen, HEADER_DEPTH)
    post = _box(-POST_WIDTH / 2, back, 0, POST_WIDTH, hb.ylen, hb.zmin)
    principals = {}
    for side, cx in (("left", -70.0), ("right", 70.0)):
        source = original[f"base_principal_center_{side}"]
        growth = (PRINCIPAL_WIDTH - source.BoundingBox().xlen) / 2
        wide = source.fuse(
            *(
                source.translate((delta, 0, 0))
                for delta in (-growth, -growth / 2, growth / 2, growth)
            )
        ).clean()
        bounds = wide.BoundingBox()
        keep = _box(
            bounds.xmin - 1,
            bounds.ymin - 1,
            hb.zmin + HEADER_DEPTH,
            bounds.xlen + 2,
            bounds.ylen + 2,
            bounds.zmax - hb.zmin - HEADER_DEPTH + 1,
        )
        principals[side] = wide.intersect(keep).clean()

    plates = {}
    hole_paths = {}
    receiving = {}
    for level, z, upper in (
        ("lower", hb.zmin, False),
        ("upper", hb.zmin + HEADER_DEPTH, True),
    ):
        for side, sign in (("left", -1), ("right", 1)):
            y = lower_y if (level == "lower") == (side == "left") else upper_y
            member = principals[side] if upper else post
            face = member.BoundingBox().xmin if sign < 0 else member.BoundingBox().xmax
            # Outer face leg and inward seat. Free ends define DXF offsets.
            vx = face - PLATE if sign < 0 else face
            vz = z if upper else z - REACH
            sx = face if sign < 0 else face - REACH
            sz = z if upper else z - PLATE
            key = f"{level}_{side}"
            plates[f"{key}_vertical"] = _box(vx, y, vz, PLATE, WIDTH, REACH)
            plates[f"{key}_seat"] = _box(sx, y, sz, REACH, WIDTH, PLATE)
            receiving[key] = member
            for offset in VERTICAL:
                cz = z + (REACH - offset if upper else -(REACH - offset))
                path = cq.Solid.makeCylinder(
                    NOMINAL_HOLE_DIAMETER / 2,
                    member.BoundingBox().xlen,
                    cq.Vector(member.BoundingBox().xmin, y + WIDTH / 2, cz),
                    cq.Vector(1, 0, 0),
                )
                hole_paths[f"{key}_vertical_{VERTICAL.index(offset) + 1}"] = path
            for offset in HORIZONTAL:
                cx = sx + REACH - offset if sign < 0 else sx + offset
                path = cq.Solid.makeCylinder(
                    NOMINAL_HOLE_DIAMETER / 2,
                    HEADER_DEPTH,
                    cq.Vector(cx, y + WIDTH / 2, hb.zmin),
                    cq.Vector(0, 0, 1),
                )
                hole_paths[f"{key}_seat_{HORIZONTAL.index(offset) + 1}"] = path

    panels = {
        name: solid
        for name, solid in original.items()
        if name.startswith(("kicker_", "main_"))
    }
    panel_clashes = [
        f"{name}:{panel}"
        for name, shape in plates.items()
        for panel, solid in panels.items()
        if _hit(shape, solid)
    ]
    screw_plate = []
    screw_paths = []
    receiver_intersections = 0
    for row in rows:
        screw = _screw(row)
        screw_plate.extend(
            f"{row['name']}:{name}"
            for name, shape in plates.items()
            if _hit(screw, shape)
        )
        screw_paths.extend(
            f"{row['name']}:{name}"
            for name, shape in hole_paths.items()
            if _hit(screw, shape)
        )
        target = (
            post
            if row["second_member"].startswith("base_post_center_")
            else principals.get(row["second_member"].split("_")[-1])
            if row["second_member"].startswith("base_principal_center_")
            else original.get(row["second_member"])
        )
        if target is not None and _hit(screw, target):
            receiver_intersections += 1

    missing_wood = []
    for name, path in hole_paths.items():
        key = "_".join(name.split("_")[:2])
        target = header if "_seat_" in name else receiving[key]
        if path.Volume() - path.intersect(target).Volume() > 0.01:
            missing_wood.append(name)
    plate_plate = [
        f"{a}:{b}"
        for i, (a, first) in enumerate(plates.items())
        for b, second in list(plates.items())[i + 1 :]
        if _hit(first, second)
    ]
    excluded = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
    }
    neighbors = {
        k: v for k, v in original.items() if k not in excluded and k not in panels
    }
    changed_wood = {
        "post": post,
        "header": header,
        **{f"principal_{k}": v for k, v in principals.items()},
    }
    neighbor_clashes = [
        f"{changed}:{name}"
        for changed, shape in changed_wood.items()
        for name, other in neighbors.items()
        if _hit(shape, other)
    ]
    plate_neighbor_clashes = [
        f"{plate}:{name}"
        for plate, shape in plates.items()
        for name, other in neighbors.items()
        if _hit(shape, other)
    ]
    kicker_support = {
        side: {
            "inner_edge_x_within_post": post.BoundingBox().xmin
            <= edge
            <= post.BoundingBox().xmax,
            "post_touches_panel_back": abs(
                post.BoundingBox().ymax - original[f"kicker_{side}"].BoundingBox().ymin
            )
            < 1e-5,
        }
        for side, edge in (
            ("left", original["kicker_left"].BoundingBox().xmax),
            ("right", original["kicker_right"].BoundingBox().xmin),
        )
    }
    return {
        "status": "nominal_installed_geometry_diagnostic_only",
        "layout": "one common solid lower post; two widened upper principals; four B88 braces on outer X faces, opposed left/right braces staggered across header depth; butt contact and removable through-bolts only",
        "width_option": KERF_RIGHT,
        "source_axes": str(AXES.relative_to(ROOT)),
        "factory_pattern_source": "docs/bolted-candidate-prototypes/mitek-b88-drawing-followup.md",
        "protected_axis_count": len(rows),
        "nominal_dxf_offsets_from_free_end_mm": {
            "horizontal": list(HORIZONTAL),
            "vertical": list(VERTICAL),
        },
        "bracket_count": len(receiving),
        "factory_circle_paths_screened": len(hole_paths),
        "conceptual_receiver_thickness_mm": {
            "post_x": POST_WIDTH,
            "principal_x": PRINCIPAL_WIDTH,
            "header_z": HEADER_DEPTH,
        },
        "assumed_plate_thickness_mm": PLATE,
        "nominal_circle_diameter_mm": NOMINAL_HOLE_DIAMETER,
        "left_right_brace_width_gap_mm": round(upper_y - (lower_y + WIDTH), 3),
        "kicker_inner_edge_support": kicker_support,
        "protected_screw_receiver_intersection_count": receiver_intersections,
        "panel_plate_conflicts": panel_clashes,
        "protected_screw_plate_conflicts": screw_plate,
        "protected_screw_nominal_hole_path_conflicts": screw_paths,
        "nominal_hole_paths_missing_wood": missing_wood,
        "plate_plate_conflicts": plate_plate,
        "changed_wood_neighbor_conflicts": neighbor_clashes,
        "plate_neighbor_conflicts": plate_neighbor_clashes,
        "unresolved": [
            "Header-to-neighbor and altered frame-bolt fit must be checked after any hidden-frame redesign.",
            "Full bolt heads, washers, nuts, grip, tool sweep, and disassembly are not modeled.",
            "DXF circles and illustrative sheet thickness have no delivered-part tolerances.",
            "Receiving wood, edge/end distances, load direction, and connection resistance are not qualified.",
            "ESR-3455 C_D=1.6 F1/F2 loads cannot be adjusted to ordinary duration; no board rating is inferred.",
        ],
        "disposition": "Diagnostic only. Conflicts block this exact installed pose until resolved; no capacity, fabrication, or drilling approval.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = json.dumps(screen_b88_center(), indent=2) + "\n"
    if args.output:
        args.output.write_text(data)
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
