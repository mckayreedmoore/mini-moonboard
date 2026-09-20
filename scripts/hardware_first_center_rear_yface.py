"""One rear-Y-face HL35 center-joint envelope; diagnostic, never drilling data."""

import argparse
import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
LENGTH = 127.0
REACH = 82.55
PLATE = 4.55  # illustrative 7-gauge rectangle, not measured steel
BORE = 14.2875  # hypothetical wood clearance, not a bit instruction
HEADER_DEPTH = 88.9  # nominal solid 4x receiver
POST_WIDTH = 184.15  # hypothetical solid nominal 6x8, supply unverified


def box(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def bounds(solid):
    b = solid.BoundingBox()
    return [round(v, 4) for v in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)]


def hits(solid, others):
    return [
        {"name": name, "overlap_mm3": round(volume, 3)}
        for name, other in others.items()
        if (volume := solid.intersect(other).Volume()) > 0.01
    ]


def screen_rear_yface():
    """Screen a fixed lower and upper rear-face pose against actual kerf solids."""
    with AXES.open(newline="") as stream:
        all_rows = list(csv.DictReader(stream))
    rows = [r for r in all_rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in all_rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(rows) != 66 or len({r["name"] for r in rows}) != 66:
        raise ValueError("expected 66 distinct protected kerf-right axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 retained frame-bolt axes")
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    old_header = raw["base_header"].BoundingBox()
    front = raw["kicker_left"].BoundingBox().ymin
    assert front == raw["kicker_right"].BoundingBox().ymin == old_header.ymax
    rear = old_header.ymin
    top = old_header.zmin + HEADER_DEPTH
    # Upper toe reaches 7 mm farther rear than the original header. Both
    # ideal rear-facing horizontal seats need a continuous header beneath.
    principal_rear = min(
        raw[f"base_principal_center_{s}"].BoundingBox().ymin for s in ("left", "right")
    )
    header_rear = min(rear - REACH, principal_rear - REACH)
    header = box(
        old_header.xmin,
        header_rear,
        old_header.zmin,
        old_header.xlen,
        front - header_rear,
        HEADER_DEPTH,
    )
    post = box(-POST_WIDTH / 2, rear, 0, POST_WIDTH, front - rear, old_header.zmin)
    trim = box(-300, -500, -1, 600, 2400, top + 1)
    principals = {
        f"base_principal_center_{s}": raw[f"base_principal_center_{s}"]
        .cut(trim)
        .clean()
        for s in ("left", "right")
    }
    lower_plates = {
        "lower_vertical": box(
            -LENGTH / 2, rear - PLATE, old_header.zmin - REACH, LENGTH, PLATE, REACH
        ),
        "lower_seat": box(
            -LENGTH / 2, rear - REACH, old_header.zmin - PLATE, LENGTH, REACH, PLATE
        ),
    }
    upper_plates = {}
    for side, x in (("left", -70.0), ("right", 70.0)):
        upper_plates[f"upper_{side}_vertical"] = box(
            x - LENGTH / 2, principal_rear - PLATE, top, LENGTH, PLATE, REACH
        )
        upper_plates[f"upper_{side}_seat"] = box(
            x - LENGTH / 2, principal_rear - REACH, top, LENGTH, REACH, PLATE
        )
    plates = {**lower_plates, **upper_plates}
    panels = {n: s for n, s in raw.items() if n.startswith(("kicker_", "main_"))}
    adjacent = {
        n: s
        for n, s in raw.items()
        if n not in panels
        and n
        not in {
            "base_header",
            "base_post_center_left",
            "base_post_center_right",
            "base_principal_center_left",
            "base_principal_center_right",
        }
    }
    wood = {"post": post, "header": header, **principals}
    screw_clashes = []
    receivers = []
    receiver_losses = []
    screws = {}
    for row in rows:
        start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
        direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
        screw = cq.Solid.makeCylinder(
            float(row["occupied_diameter_mm"]) / 2,
            float(row["occupied_length_mm"]),
            start,
            direction,
        )
        screws[row["name"]] = screw
        collisions = hits(screw, plates)
        if collisions:
            screw_clashes.append({"axis": row["name"], "plates": collisions})
        if row["name"].startswith("round_kicker_") and "_center_" in row["name"]:
            receivers.append(
                {
                    "axis": row["name"],
                    "post_overlap_mm3": round(screw.intersect(post).Volume(), 3),
                }
            )
        member = row["second_member"]
        if member in principals:
            old_volume = screw.intersect(raw[member]).Volume()
            new_volume = screw.intersect(principals[member]).Volume()
            if old_volume - new_volume > 0.01:
                receiver_losses.append(
                    {
                        "axis": row["name"],
                        "member": member,
                        "lost_overlap_mm3": round(old_volume - new_volume, 3),
                    }
                )
    bores = {}
    # X pitch and vertical offset follow the nominal HL drawing. The same
    # 50.8-mm horizontal offset is only a symmetry assumption.
    for i, x in enumerate((-31.75, 31.75), 1):
        bores[f"lower_post_{i}"] = cq.Solid.makeCylinder(
            BORE / 2,
            front - rear,
            cq.Vector(x, rear, old_header.zmin - 50.8),
            cq.Vector(0, 1, 0),
        )
        bores[f"lower_header_{i}"] = cq.Solid.makeCylinder(
            BORE / 2,
            HEADER_DEPTH,
            cq.Vector(x, rear - 50.8, old_header.zmin),
            cq.Vector(0, 0, 1),
        )
    for side, xcenter in (("left", -70.0), ("right", 70.0)):
        for i, x in enumerate((xcenter - 31.75, xcenter + 31.75), 1):
            bores[f"upper_{side}_principal_{i}"] = cq.Solid.makeCylinder(
                BORE / 2,
                139.7,
                cq.Vector(x, principal_rear, top + 50.8),
                cq.Vector(0, 1, 0),
            )
            bores[f"upper_{side}_header_{i}"] = cq.Solid.makeCylinder(
                BORE / 2,
                HEADER_DEPTH,
                cq.Vector(x, principal_rear - 50.8, old_header.zmin),
                cq.Vector(0, 0, 1),
            )
    bore_missing = []
    for name, bore in bores.items():
        member = (
            "post"
            if "lower_post" in name
            else "header"
            if "header" in name
            else "base_principal_center_left"
            if "left" in name
            else "base_principal_center_right"
        )
        bore_missing.append(
            {
                "name": name,
                "receiver": member,
                "outside_receiver_mm3": round(
                    max(0, bore.Volume() - bore.intersect(wood[member]).Volume()), 3
                ),
            }
        )
    bore_crossings = []
    for lower in (n for n in bores if n.startswith("lower_header")):
        for upper in (n for n in bores if n.startswith("upper_") and "header" in n):
            volume = bores[lower].intersect(bores[upper]).Volume()
            if volume > 0.01:
                bore_crossings.append(
                    {"lower": lower, "upper": upper, "overlap_mm3": round(volume, 3)}
                )
    plate_pairs = []
    names = list(plates)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if a.rsplit("_", 1)[0] == b.rsplit("_", 1)[0]:
                continue  # two legs of one ideal angle share their bend envelope
            volume = plates[a].intersect(plates[b]).Volume()
            if volume > 0.01:
                plate_pairs.append({"a": a, "b": b, "overlap_mm3": round(volume, 3)})
    frame_clashes = []
    for row in frame_rows:
        cylinder = cq.Solid.makeCylinder(
            float(row["occupied_diameter_mm"]) / 2,
            float(row["occupied_length_mm"]),
            cq.Vector(*(float(row[f"start_{a}_mm"]) for a in "xyz")),
            cq.Vector(*(float(row[f"direction_{a}"]) for a in "xyz")),
        )
        collisions = hits(cylinder, {**plates, **bores})
        if collisions:
            frame_clashes.append({"axis": row["name"], "hardware": collisions})
    return {
        "status": "rejected_installed_geometry_trial",
        "source": str(AXES.relative_to(ROOT)),
        "pose": "front-aligned solid common post; one rear-Y lower HL35; two rear-Y upper HL35; raised and rear-extended solid header; trimmed original principal toes",
        "protected_axis_count": len(rows),
        "retained_frame_bolt_axis_count": len(frame_rows),
        "post_bounds_mm": bounds(post),
        "header_bounds_mm": bounds(header),
        "principal_rear_reference_y_mm": principal_rear,
        "upper_principal_width_x_mm": {
            n: round(s.BoundingBox().xlen, 4) for n, s in principals.items()
        },
        "upper_principal_bolt_x_mm": {
            "left": [-101.75, -38.25],
            "right": [38.25, 101.75],
        },
        "kicker_inner_edges_x_mm": [
            round(raw["kicker_left"].BoundingBox().xmax, 4),
            round(raw["kicker_right"].BoundingBox().xmin, 4),
        ],
        "kicker_center_receivers": receivers,
        "principal_screw_receiver_losses": receiver_losses,
        "original_principal_header_overlaps_mm3": {
            n: round(s.intersect(header).Volume(), 3)
            for n, s in raw.items()
            if n in principals
        },
        "upper_vertical_face_gaps_mm": {
            n: round(
                s.intersect(box(-200, -500, top, 400, 2500, REACH)).BoundingBox().ymin
                - principal_rear,
                4,
            )
            for n, s in principals.items()
        },
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "plate_pair_clashes": plate_pairs,
        "plate_panel_clashes": {n: hits(s, panels) for n, s in plates.items()},
        "plate_other_wood_clashes": {n: hits(s, adjacent) for n, s in plates.items()},
        "plate_intended_wood_clashes": {n: hits(s, wood) for n, s in plates.items()},
        "new_wood_panel_clashes": {n: hits(s, panels) for n, s in wood.items()},
        "new_wood_adjacent_clashes": {n: hits(s, adjacent) for n, s in wood.items()},
        "protected_screw_plate_clashes": screw_clashes,
        "bore_missing_wood": bore_missing,
        "header_bore_crossings": bore_crossings,
        "bore_screw_clashes": {
            n: [
                axis
                for axis, screw in screws.items()
                if bore.intersect(screw).Volume() > 0.01
            ]
            for n, bore in bores.items()
        },
        "retained_frame_bolt_new_hardware_clashes": frame_clashes,
        "bolt_access": "Rear lower and upper bolt heads, washers, nuts, tool swing, and withdrawal paths unmodeled; rear extension also crosses existing principal toes. No installed access established.",
        "missing_load_path": "No qualified post/header/principal force transfer or bracket resistance. Butt contact alone supplies no tension path; toe trimming and unknown bolt access preclude a complete joint.",
        "assumptions": "Ideal plate rectangles; nominal 7-gauge thickness and assumed horizontal hole offset. Bores are diagnostic cylinders, not delivered factory holes or a drilling plan. No lap or custom steel.",
        "disposition": "Reject this single rear-Y-face pose on installed geometry and unresolved connection/access; no structural claim or drilling release.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_rear_yface(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
