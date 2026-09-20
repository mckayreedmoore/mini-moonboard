"""One front-Y upper B66/UB66 center pose; nominal occupancy only."""

import argparse
import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_b66_rear_y import (
    AXES,
    HEADER_Z,
    HOLE,
    OFFSETS,
    POST_X,
    POST_Y,
    PRINCIPAL_X,
    REACH,
    ROOT,
    SHEET,
    WIDTH,
    axis,
    bounds,
    box,
    clashes,
)


def front_at_toe(principal, top):
    """Locate the frontmost wood at the header contact, before upward rake."""
    b = principal.BoundingBox()
    toe = principal.intersect(
        box(b.xmin - 1, b.ymin - 1, top, b.xlen + 2, b.ylen + 2, 0.05)
    )
    if toe.Volume() < 0.01:
        raise ValueError("principal has no wood at raised header")
    return toe.BoundingBox().ymax


def rear_at_hole(principal, z):
    """Find the opposite Y surface at a factory-hole center elevation."""
    b = principal.BoundingBox()
    slice_ = principal.intersect(
        box(b.xmin - 1, b.ymin - 1, z - 0.025, b.xlen + 2, b.ylen + 2, 0.05)
    )
    if slice_.Volume() < 0.01:
        raise ValueError("principal has no wood at upper factory hole")
    return slice_.BoundingBox().ymin


def screen_b66_front_y():
    """Screen complete ideal plate and bore solids, without a rating claim."""
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    panel_rows = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len(frame_rows) != 12:
        raise ValueError("expected 66 panel screws and 12 old frame axes")
    if len({r["name"] for r in rows}) != len(rows):
        raise ValueError("protected axis names must be unique")

    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    hb = raw["base_header"].BoundingBox()
    front = raw["kicker_left"].BoundingBox().ymin
    rear_post = front - POST_Y
    top = hb.zmin + HEADER_Z
    post = box(-POST_X / 2, rear_post, 0, POST_X, POST_Y, hb.zmin)
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
        principals[side] = wide.intersect(
            box(b.xmin - 1, b.ymin - 1, top, b.xlen + 2, b.ylen + 2, b.zmax - top + 1)
        ).clean()
    front_faces = {s: front_at_toe(p, top) for s, p in principals.items()}
    # Full rectangular one-piece header: lower rear seat and both upper seats
    # receive continuous wood. Its front reaches the upper toe contact plane.
    header_rear = min(rear_post - REACH, min(front_faces.values()) - REACH)
    header_front = max(front, *front_faces.values())
    header = box(
        hb.xmin, header_rear, hb.zmin, hb.xlen, header_front - header_rear, HEADER_Z
    )

    plates = {}
    bores = {}
    targets = {}
    upper_exit_shortfall = {}
    # The lower B66 remains on the post's rear Y face. Both upper vertical
    # flanges turn to the principal toe's front Y, with seats reaching rearward.
    stations = (("post", 0.0, rear_post, hb.zmin, post),) + tuple(
        (f"principal_{side}", x, front_faces[side], top, principals[side])
        for side, x in (("left", -70.0), ("right", 70.0))
    )
    for name, x, face_y, joint_z, receiver in stations:
        lower = name == "post"
        vz = joint_z - REACH if lower else joint_z
        seat_z = joint_z - SHEET if lower else joint_z
        vertical_y = face_y - SHEET if lower else face_y
        plates[f"{name}_vertical"] = box(
            x - WIDTH / 2, vertical_y, vz, WIDTH, SHEET, REACH
        )
        plates[f"{name}_seat"] = box(
            x - WIDTH / 2, face_y - REACH, seat_z, WIDTH, REACH, SHEET
        )
        for number, offset in enumerate(OFFSETS, 1):
            # Official nominal DXF free-end offsets on both factory legs.
            z = vz + offset if lower else vz + REACH - offset
            y = face_y - REACH + offset
            vertical = f"{name}_vertical_{number}"
            seat = f"{name}_seat_{number}"
            bores[vertical] = cq.Solid.makeCylinder(
                HOLE / 2,
                POST_Y,
                cq.Vector(x, face_y, z),
                cq.Vector(0, 1 if lower else -1, 0),
            )
            if not lower:
                far_face_y = rear_at_hole(receiver, z)
                shortfall = max(0, face_y - POST_Y - far_face_y)
                if shortfall > 0.01:
                    upper_exit_shortfall[vertical] = round(shortfall, 3)
            bores[seat] = cq.Solid.makeCylinder(
                HOLE / 2, HEADER_Z, cq.Vector(x, y, hb.zmin), cq.Vector(0, 0, 1)
            )
            targets[vertical] = receiver
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
    receiver_by_screw = {}
    for row in panel_rows:
        member = row["second_member"]
        if member.startswith("base_post_center_"):
            receiver_by_screw[row["name"]] = post
        elif member.startswith("base_principal_center_"):
            receiver_by_screw[row["name"]] = principals[
                member.removeprefix("base_principal_center_")
            ]
        else:
            receiver_by_screw[row["name"]] = raw[member]
    received = sum(
        screws[n].intersect(receiver).Volume() > 0.01
        for n, receiver in receiver_by_screw.items()
    )
    missing = {
        n: round(max(0, bore.Volume() - bore.intersect(targets[n]).Volume()), 3)
        for n, bore in bores.items()
        if bore.Volume() - bore.intersect(targets[n]).Volume() > 0.01
    }
    plate_pairs = [
        {"a": a, "b": b, "overlap_mm3": round(volume, 3)}
        for i, (a, shape) in enumerate(plates.items())
        for b, other in list(plates.items())[i + 1 :]
        if a.rsplit("_", 1)[0] != b.rsplit("_", 1)[0]
        if (volume := shape.intersect(other).Volume()) > 0.01
    ]
    bore_pairs = [
        {"a": a, "b": b, "overlap_mm3": round(volume, 3)}
        for i, (a, shape) in enumerate(bores.items())
        for b, other in list(bores.items())[i + 1 :]
        if (volume := shape.intersect(other).Volume()) > 0.01
    ]
    front_upper_wood = clashes(
        {n: p for n, p in plates.items() if n.startswith("principal_")},
        {f"principal_{s}": p for s, p in principals.items()},
    )
    changed_panels = clashes(changed, panels)
    changed_neighbors = clashes(changed, neighbors)
    plate_panels = clashes(plates, panels)
    screw_plates = clashes(screws, plates)
    screw_bores = clashes(screws, bores)
    bore_panels = clashes(bores, panels)
    plate_neighbors = clashes(plates, neighbors)
    bore_neighbors = clashes(bores, neighbors)
    old_frame_hardware = clashes(old_frame, {**plates, **bores})
    blockers = (
        missing
        or upper_exit_shortfall
        or front_upper_wood
        or changed_panels
        or changed_neighbors
        or plate_panels
        or plate_neighbors
        or screw_plates
        or screw_bores
        or bore_panels
        or bore_neighbors
        or old_frame_hardware
        or plate_pairs
        or bore_pairs
        or received != 66
    )
    return {
        "status": "rejected_nominal_installed_geometry"
        if blockers
        else "conditional_nominal_fit_only",
        "pose": "one rear-Y post B66 under one-piece header; two front-Y principal-to-header B66 with rearward top seats",
        "width_option": KERF_RIGHT,
        "axis_source": str(AXES.relative_to(ROOT)),
        "factory_pattern_source": "docs/bolted-candidate-prototypes/mitek-b66-drawing-followup.md",
        "protected_screw_axes": len(panel_rows),
        "retained_frame_axes": len(frame_rows),
        "protected_screw_receiver_intersections": received,
        "kicker_inner_edges_backed": {
            side: post.BoundingBox().xmin <= edge <= post.BoundingBox().xmax
            and abs(post.BoundingBox().ymax - front) < 1e-5
            for side, edge in (
                ("left", raw["kicker_left"].BoundingBox().xmax),
                ("right", raw["kicker_right"].BoundingBox().xmin),
            )
        },
        "brackets": len(stations),
        "bolts_per_brace": 4,
        "factory_hole_paths": len(bores),
        "nominal_dxf_free_end_offsets_mm": list(OFFSETS),
        "nominal_dxf_circle_diameter_mm": HOLE,
        "illustrative_plate_thickness_mm": SHEET,
        "minimum_receiver_thickness_mm": min(HEADER_Z, POST_Y, PRINCIPAL_X),
        "upper_front_toe_y_mm": {s: round(y, 3) for s, y in front_faces.items()},
        "post_bounds_mm": bounds(post),
        "header_bounds_mm": bounds(header),
        "principal_bounds_mm": {s: bounds(p) for s, p in principals.items()},
        "plate_bounds_mm": {n: bounds(p) for n, p in plates.items()},
        "front_upper_plate_wood_conflicts": front_upper_wood,
        "front_upper_bore_missing_wood_mm3": {
            n: v
            for n, v in missing.items()
            if n.startswith("principal_") and "vertical" in n
        },
        "front_upper_nominal_bore_exit_shortfall_mm": upper_exit_shortfall,
        "all_bores_missing_wood_mm3": missing,
        "plate_pair_conflicts": plate_pairs,
        "bore_pair_conflicts": bore_pairs,
        "plate_panel_conflicts": plate_panels,
        "plate_neighbor_conflicts": plate_neighbors,
        "changed_wood_panel_conflicts": changed_panels,
        "changed_wood_neighbor_conflicts": changed_neighbors,
        "screw_plate_conflicts": screw_plates,
        "screw_bore_conflicts": screw_bores,
        "bore_panel_conflicts": bore_panels,
        "bore_neighbor_conflicts": bore_neighbors,
        "old_frame_hardware_conflicts": old_frame_hardware,
        "old_frame_changed_wood_intersections": clashes(old_frame, changed),
        "one_piece_blank_envelopes_mm": {
            "post_xyz": [POST_X, POST_Y, round(hb.zmin, 3)],
            "header_xyz": [
                round(hb.xlen, 3),
                round(header_front - header_rear, 3),
                HEADER_Z,
            ],
            "principal_width_x_each": PRINCIPAL_X,
        },
        "access_and_load_axis_limit": "Front-facing upper plates are geometrically buried as the principals rake forward; heads, washers, nuts, wrench sweep and disassembly with panels installed are not established. ESR-3455 F1/F2 axes and paired-brace conditions do not rate this joint's combined force, moment, or reversal.",
        "qualification": "Nominal fit only. ESR-3455 B66 Table 3 is C_D=1.6 and forbids duration conversion. Ordinary-duration resistance requires separate wood/bolt/formed-steel analysis; ASTM A653 Structural Steel Grade 40, minimum 0.099-in base steel. No F1/F2 value transfers.",
        "unmodeled": "Delivered bend/hole tolerances, actual 3/8-in A307-or-better bolt stacks, edge/end-distance design, tool access, one-piece stock grade/availability, and load path. No drilling or rating approval.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(screen_b66_front_y(), indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
