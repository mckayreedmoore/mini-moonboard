"""Reject a centered, paired Y-face HL35 common-post pose; not a drill plan."""

import argparse
import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
POST_X = 184.15  # nominal actual 8-in side of a hypothetical solid 6x8
POST_Y = 139.7  # nominal actual 6-in side; equals existing front/back depth
HL35_LENGTH = 127.0
HL35_REACH = 82.55
PLATE = 4.55  # illustrative 7-gauge envelope, not a delivered measurement
SCREW_OCCUPIED = 50.8  # frozen occupied envelope, not purchased overall length


def _box(xmin, ymin, zmin, xlen, ylen, zlen):
    return cq.Solid.makeBox(xlen, ylen, zlen, cq.Vector(xmin, ymin, zmin))


def _rows():
    with AXES.open(newline="") as handle:
        rows = [r for r in csv.DictReader(handle)
                if r["shop_opening_kind"] == "hillman_panel"]
    if len(rows) != 66 or len({r["name"] for r in rows}) != 66:
        raise ValueError("expected 66 distinct protected panel/kicker axes")
    return rows


def screen_yface():
    """Screen only the installed lower pair; one unavoidable clash rejects it."""
    rows = _rows()
    parts = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    header = parts["base_header"].BoundingBox()
    kicker_left = parts["kicker_left"].BoundingBox()
    kicker_right = parts["kicker_right"].BoundingBox()
    # A single solid centered receiver preserves the two original post
    # footprints and continuously backs both inner kicker edges at Y=-36.
    post = _box(-POST_X / 2, header.ymax - POST_Y, 0,
                POST_X, POST_Y, header.zmin)
    front_y = post.BoundingBox().ymax
    rear_y = post.BoundingBox().ymin
    x0 = -HL35_LENGTH / 2  # Simpson requires centering on the member face.
    # Best-case ideal rectangular envelopes: the front leg projects into
    # the kicker panel. Holes, bend radius, coating and tolerances omitted.
    front_vertical = _box(x0, front_y, header.zmin - HL35_REACH,
                          HL35_LENGTH, PLATE, HL35_REACH)
    front_seat = _box(x0, front_y, header.zmin - PLATE,
                      HL35_LENGTH, HL35_REACH, PLATE)
    rear_vertical = _box(x0, rear_y - PLATE, header.zmin - HL35_REACH,
                         HL35_LENGTH, PLATE, HL35_REACH)
    panel_names = ["kicker_left", "kicker_right", "main_lower_left",
                   "main_lower_right", "main_upper_left", "main_upper_right"]
    panel_clashes = []
    for name in panel_names:
        panel = parts[name]
        for flange_name, flange in (("front_vertical", front_vertical),
                                     ("front_seat", front_seat),
                                     ("rear_vertical", rear_vertical)):
            volume = flange.intersect(panel).Volume()
            if volume > 0.01:
                panel_clashes.append({"panel": name, "flange": flange_name,
                                      "overlap_mm3": round(volume, 3)})
    screw_clashes = []
    receivers = []
    for row in rows:
        start = cq.Vector(*(float(row[f"start_{a}_mm"]) for a in "xyz"))
        direction = cq.Vector(*(float(row[f"direction_{a}"]) for a in "xyz"))
        screw = cq.Solid.makeCylinder(float(row["occupied_diameter_mm"]) / 2,
                                      SCREW_OCCUPIED, start, direction)
        if row["second_member"].startswith("base_post_center_"):
            receivers.append({"name": row["name"],
                              "common_post_intersection_mm3": round(post.intersect(screw).Volume(), 3)})
        for flange_name, flange in (("front_vertical", front_vertical),
                                     ("front_seat", front_seat),
                                     ("rear_vertical", rear_vertical)):
            volume = flange.intersect(screw).Volume()
            if volume > 0.01:
                screw_clashes.append({"name": row["name"], "flange": flange_name,
                                      "overlap_mm3": round(volume, 3)})
    post_missing_original = {}
    for side in ("left", "right"):
        old = parts[f"base_post_center_{side}"]
        post_missing_original[side] = round(old.cut(post).Volume(), 3)
    other_wood_clashes = []
    for name, part in parts.items():
        if name.startswith("base_post_center_") or name == "base_header":
            continue
        volume = post.intersect(part).Volume()
        if volume > 0.01:
            other_wood_clashes.append({"part": name, "overlap_mm3": round(volume, 3)})
    return {
        "status": "rejected_installed_geometry_trial",
        "concept": "single centered nominal 6x8 solid post with opposed centered Y-face HL35 lower angles at existing header underside",
        "source": str(AXES.relative_to(ROOT)),
        "all_66_panel_axes_unchanged": True,
        "common_post_bounds_mm": [-POST_X / 2, POST_X / 2, rear_y, front_y, 0, header.zmin],
        "kicker_inner_edges_x_mm": [kicker_left.xmax, kicker_right.xmin],
        "original_post_material_missing_mm3": post_missing_original,
        "other_wood_overlap": other_wood_clashes,
        "front_face_and_kicker_back_y_mm": [front_y, kicker_left.ymin],
        "front_angle_nominal_envelope": {"length_x_mm": HL35_LENGTH,
                                          "reach_mm": HL35_REACH,
                                          "assumed_plate_mm": PLATE},
        "panel_flange_clashes": panel_clashes,
        "protected_screw_flange_clashes": screw_clashes,
        "common_post_kicker_receivers": receivers,
        "number_of_protected_axes_screened": len(rows),
        "bores_and_hardware": "Not sized: this centered face-mounted angle already occupies the fixed kicker panel. Post/header/principal bores, washer/head/nut stacks and tool access cannot rescue that overlap; no factory hole or drilling location is established.",
        "disposition": "Reject this paired Y-face HL35 pose. To retain continuous kicker-edge backing, the post front face meets the panel back at Y=-36 mm; a face-mounted front bracket of nonzero thickness necessarily occupies panel space. Moving the post rearward removes that direct support and is a different blocking concept. No load rating, fabrication, or drilling follows.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_yface(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
