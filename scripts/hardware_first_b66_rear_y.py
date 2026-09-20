"""Screen one rear-Y MiTek B66/retail UB66 installed center pose."""

import argparse
import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
REACH = 152.4
WIDTH = 38.1
SHEET = 2.66  # Ideal envelope, not a delivered bend or coating measurement.
HOLE = 10.3  # DXF nominal circle, not a wood drill-bit specification.
OFFSETS = (25.4, 126.744)  # Approximate free-end centers from official B66 DXF.
HEADER_Z = 76.2
POST_X = 184.15
POST_Y = 139.7
PRINCIPAL_X = 88.9


def box(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def bounds(shape):
    b = shape.BoundingBox()
    return [round(v, 3) for v in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)]


def axis(row):
    return cq.Solid.makeCylinder(
        float(row["occupied_diameter_mm"]) / 2,
        float(row["occupied_length_mm"]),
        cq.Vector(*(float(row[f"start_{a}_mm"]) for a in "xyz")),
        cq.Vector(*(float(row[f"direction_{a}"]) for a in "xyz")),
    )


def clashes(first, second):
    return [
        {"a": a, "b": b, "overlap_mm3": round(volume, 3)}
        for a, shape in first.items()
        for b, other in second.items()
        if (volume := shape.intersect(other).Volume()) > 0.01
    ]


def screen_b66_rear_y():
    """Return nominal CAD occupancy; no load, access, or drilling approval."""
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len(frame_rows) != 12:
        raise ValueError("expected 66 panel screws and 12 old frame axes")
    if len({r["name"] for r in rows}) != len(rows):
        raise ValueError("protected axis names must be unique")

    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    old_header = raw["base_header"].BoundingBox()
    front = raw["kicker_left"].BoundingBox().ymin
    rear_post = front - POST_Y
    rear_principal = min(
        raw[f"base_principal_center_{side}"].BoundingBox().ymin
        for side in ("left", "right")
    )
    top = old_header.zmin + HEADER_Z
    # One full-depth header gives both under-seat and top-seat bolt paths wood.
    header_rear = min(rear_post, rear_principal) - REACH
    header = box(
        old_header.xmin,
        header_rear,
        old_header.zmin,
        old_header.xlen,
        front - header_rear,
        HEADER_Z,
    )
    post = box(-POST_X / 2, rear_post, 0, POST_X, POST_Y, old_header.zmin)
    principals = {}
    for side in ("left", "right"):
        source = raw[f"base_principal_center_{side}"]
        growth = (PRINCIPAL_X - source.BoundingBox().xlen) / 2
        wide = source.fuse(
            *(
                source.translate((d, 0, 0))
                for d in (-growth, -growth / 2, growth / 2, growth)
            )
        ).clean()
        b = wide.BoundingBox()
        # Butt against raised header, retaining the complete upper member.
        principals[side] = wide.intersect(
            box(b.xmin - 1, b.ymin - 1, top, b.xlen + 2, b.ylen + 2, b.zmax - top + 1)
        ).clean()

    plates = {}
    bores = {}
    targets = {}
    stations = (("post", 0.0, rear_post, old_header.zmin, POST_Y),) + tuple(
        (f"principal_{side}", x, rear_principal, top, POST_Y)
        for side, x in (("left", -70.0), ("right", 70.0))
    )
    for name, x, rear, joint_z, bore_depth in stations:
        # Lower angle hangs below the header and seats under it. Upper angles
        # rise from the header and seat on it; all upright flanges face rear Y.
        lower = name == "post"
        vz = joint_z - REACH if lower else joint_z
        seat_z = joint_z - SHEET if lower else joint_z
        plates[f"{name}_vertical"] = box(
            x - WIDTH / 2, rear - SHEET, vz, WIDTH, SHEET, REACH
        )
        plates[f"{name}_seat"] = box(
            x - WIDTH / 2, rear - REACH, seat_z, WIDTH, REACH, SHEET
        )
        upright = post if lower else principals[name.removeprefix("principal_")]
        for number, offset in enumerate(OFFSETS, 1):
            # DXF offsets are from each leg's free end, toward the bend.
            z = vz + offset if lower else vz + REACH - offset
            y = rear - REACH + offset
            vertical = f"{name}_vertical_{number}"
            seat = f"{name}_seat_{number}"
            bores[vertical] = cq.Solid.makeCylinder(
                HOLE / 2, bore_depth, cq.Vector(x, rear, z), cq.Vector(0, 1, 0)
            )
            bores[seat] = cq.Solid.makeCylinder(
                HOLE / 2, HEADER_Z, cq.Vector(x, y, old_header.zmin), cq.Vector(0, 0, 1)
            )
            targets[vertical] = upright
            targets[seat] = header

    panels = {n: s for n, s in raw.items() if n.startswith(("kicker_", "main_"))}
    excluded = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
    }
    neighbors = {n: s for n, s in raw.items() if n not in excluded and n not in panels}
    changed = {
        "post": post,
        "header": header,
        **{f"principal_{s}": p for s, p in principals.items()},
    }
    screws = {r["name"]: axis(r) for r in panel_rows}
    old_frame = {r["name"]: axis(r) for r in frame_rows}
    receivers = {}
    for row in panel_rows:
        member = row["second_member"]
        if member.startswith("base_post_center_"):
            receivers[row["name"]] = post
        elif member.startswith("base_principal_center_"):
            receivers[row["name"]] = principals[
                member.removeprefix("base_principal_center_")
            ]
        else:
            receivers[row["name"]] = raw[member]
    received = sum(
        screws[n].intersect(receiver).Volume() > 0.01
        for n, receiver in receivers.items()
    )
    missing = {
        n: round(max(0, bore.Volume() - bore.intersect(targets[n]).Volume()), 3)
        for n, bore in bores.items()
        if bore.Volume() - bore.intersect(targets[n]).Volume() > 0.01
    }
    plate_pairs = [
        item
        for i, (a, shape) in enumerate(plates.items())
        for b, other in list(plates.items())[i + 1 :]
        if a.rsplit("_", 1)[0] != b.rsplit("_", 1)[0]
        if (volume := shape.intersect(other).Volume()) > 0.01
        for item in ({"a": a, "b": b, "overlap_mm3": round(volume, 3)},)
    ]
    bore_pairs = [
        item
        for i, (a, shape) in enumerate(bores.items())
        for b, other in list(bores.items())[i + 1 :]
        if (volume := shape.intersect(other).Volume()) > 0.01
        for item in ({"a": a, "b": b, "overlap_mm3": round(volume, 3)},)
    ]
    neighbor_conflicts = clashes(changed, neighbors)
    kicker_edges_backed = {
        side: post.BoundingBox().xmin <= edge <= post.BoundingBox().xmax
        and abs(post.BoundingBox().ymax - front) < 1e-5
        for side, edge in (
            ("left", raw["kicker_left"].BoundingBox().xmax),
            ("right", raw["kicker_right"].BoundingBox().xmin),
        )
    }
    results = {
        "status": (
            "rejected_nominal_installed_geometry"
            if missing or neighbor_conflicts
            else "conditional_nominal_fit_only"
        ),
        "pose": "one center rear-Y post B66 under header; two rear-Y principal B66 atop one raised solid header",
        "width_option": KERF_RIGHT,
        "axis_source": str(AXES.relative_to(ROOT)),
        "factory_pattern_source": "docs/bolted-candidate-prototypes/mitek-b66-drawing-followup.md",
        "protected_screw_axes": len(panel_rows),
        "retained_frame_axes": len(frame_rows),
        "protected_screw_receiver_intersections": received,
        "kicker_inner_edges_backed": kicker_edges_backed,
        "brackets": len(stations),
        "bolts_per_brace": 4,
        "factory_hole_paths": len(bores),
        "nominal_dxf_free_end_offsets_mm": list(OFFSETS),
        "nominal_dxf_circle_diameter_mm": HOLE,
        "illustrative_plate_thickness_mm": SHEET,
        "minimum_receiver_thickness_mm": min(HEADER_Z, POST_Y, PRINCIPAL_X),
        "post_bounds_mm": bounds(post),
        "header_bounds_mm": bounds(header),
        "principal_bounds_mm": {s: bounds(p) for s, p in principals.items()},
        "plate_bounds_mm": {n: bounds(p) for n, p in plates.items()},
        "upper_rear_reference_y_mm": rear_principal,
        "rear_y_upper_bore_missing_wood_mm3": {
            n: v
            for n, v in missing.items()
            if n.startswith("principal_") and "vertical" in n
        },
        "all_bores_missing_wood_mm3": missing,
        "plate_pair_conflicts": plate_pairs,
        "bore_pair_conflicts": bore_pairs,
        "plate_panel_conflicts": clashes(plates, panels),
        "plate_neighbor_conflicts": clashes(plates, neighbors),
        "changed_wood_panel_conflicts": clashes(changed, panels),
        "new_wood_neighbor_conflicts": neighbor_conflicts,
        "screw_plate_conflicts": clashes(screws, plates),
        "screw_bore_conflicts": clashes(screws, bores),
        "bore_panel_conflicts": clashes(bores, panels),
        "bore_neighbor_conflicts": clashes(bores, neighbors),
        "old_frame_hardware_conflicts": clashes(old_frame, {**plates, **bores}),
        "old_frame_changed_wood_intersections": clashes(old_frame, changed),
        "one_piece_blank_envelopes_mm": {
            "post_xyz": [POST_X, POST_Y, round(old_header.zmin, 3)],
            "header_xyz": [
                round(old_header.xlen, 3),
                round(front - header_rear, 3),
                HEADER_Z,
            ],
            "principal_width_x_each": PRINCIPAL_X,
        },
        "qualification": "Nominal occupancy only. ESR-3455 B66 Table 3 uses C_D=1.6 and forbids duration conversion; ordinary-duration joint resistance requires separate wood/bolt/formed-steel analysis. Its steel is ASTM A653 Structural Steel Grade 40, minimum 0.099-in base thickness. No F1/F2 value is transferred.",
        "unmodeled": "Delivered bend/hole tolerances, 3/8-in A307-or-better bolt stacks, washers, edge/end-distance design, tool access and removal, one-piece stock grade/availability, and actual load path. No drilling approval.",
    }
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(screen_b66_rear_y(), indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
