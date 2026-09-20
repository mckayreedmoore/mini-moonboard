"""Nominal paired-HL35 center-assembly screen; never a drill plan."""

import argparse
import csv
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
HOLE = 14.2875  # conditional 9/16-in wood clearance for a 1/2-in bolt
THICK = 88.9  # 3.5-in delivered solid receiving timber assumed
RISE = 50.8
LENGTH = 127.0
HOLE_END = 31.75
PITCH = 63.5
OFFSET = 50.8
FLANGE_REACH = 82.55  # HL35 W1/W2 = 3 1/4 in in Simpson's catalog
IDEAL_PLATE_THICKNESS = 4.55  # illustrative 7-gauge envelope, not a delivered measurement
FROZEN_SCREW_LENGTH = 50.8  # occupied envelope in the frozen connection-axes CSV
PURCHASED_SCREW_LENGTH = 63.5  # purchased overall length, not verified shaft occupancy


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _cylinder(point: tuple[float, float, float], direction: cq.Vector,
              length: float, diameter: float) -> cq.Solid:
    return cq.Solid.makeCylinder(diameter / 2, length, cq.Vector(*point), direction)


def _wood() -> dict[str, cq.Shape]:
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    header = raw["base_header"]
    b = header.BoundingBox()
    cap = cq.Solid.makeBox(b.xlen, b.ylen, RISE, cq.Vector(b.xmin, b.ymin, b.zmax))
    raw["base_header"] = header.fuse(cap).clean()
    for side in ("left", "right"):
        for kind in ("principal", "post"):
            name = f"base_{kind}_center_{side}"
            shape = raw[name]
            raw[name] = shape.fuse(shape.translate((-RISE / 2, 0, 0)),
                                   shape.translate((RISE / 2, 0, 0))).clean()
        name = f"base_principal_center_{side}"
        p = raw[name]
        pb = p.BoundingBox()
        keep = cq.Solid.makeBox(pb.xlen + 2, pb.ylen + 2,
                                pb.zmax - b.zmax - RISE + 2,
                                cq.Vector(pb.xmin - 1, pb.ymin - 1, b.zmax + RISE))
        raw[name] = p.intersect(keep).clean()
    return raw


def _inner_flange(side: str, level: str, y_min: float, header: cq.BoundBox) -> cq.Solid:
    """Ideal rectangular HL35 seat; excludes bend radii, holes, and delivered tolerances."""
    center_x = -70 if side == "left" else 70
    inner_face_x = center_x + (THICK / 2 if side == "left" else -THICK / 2)
    tip_x = inner_face_x + (FLANGE_REACH if side == "left" else -FLANGE_REACH)
    z_min = header.zmax if level == "upper" else header.zmin - IDEAL_PLATE_THICKNESS
    return cq.Solid.makeBox(abs(tip_x - inner_face_x), LENGTH, IDEAL_PLATE_THICKNESS,
                            cq.Vector(min(inner_face_x, tip_x), y_min, z_min))


def screen_hl35_center() -> dict[str, object]:
    """Try independent upper/lower bolts at the largest possible HL35 Y stagger."""
    panel = [r for r in _rows(AXES) if r["shop_opening_kind"] == "hillman_panel"]
    if len(panel) != 66 or len({r["name"] for r in panel}) != 66:
        raise ValueError("expected 66 unique frozen kerf-right panel/kicker axes")
    baseline = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    wood = _wood()
    hb = wood["base_header"].BoundingBox()
    upper_y = [hb.ymin + HOLE_END + i * PITCH for i in range(2)]
    lower_y = [hb.ymax - LENGTH + HOLE_END + i * PITCH for i in range(2)]
    bores = []
    solids = {}
    for side in ("left", "right"):
        center_x = -70 if side == "left" else 70
        for face in ("outer", "inner"):
            sense = (-1 if side == "left" else 1) * (1 if face == "outer" else -1)
            header_x = center_x + sense * (THICK / 2 + OFFSET)
            for level, ys, z, member in (
                ("upper", upper_y, hb.zmax + OFFSET, f"base_principal_center_{side}"),
                ("lower", lower_y, hb.zmin - OFFSET, f"base_post_center_{side}"),
            ):
                for i, y in enumerate(ys, 1):
                    key = f"{side}_{face}_{level}_{i}"
                    v = _cylinder((center_x - THICK / 2, y, z), cq.Vector(1, 0, 0), THICK, HOLE)
                    h = _cylinder((header_x, y, hb.zmin), cq.Vector(0, 0, 1), hb.zlen, HOLE)
                    v_missing = max(0, v.Volume() - wood[member].intersect(v).Volume())
                    h_missing = max(0, h.Volume() - wood["base_header"].intersect(h).Volume())
                    bores.append({"id": key, "vertical_center_mm": [center_x, y, z],
                                  "header_center_mm": [header_x, y],
                                  "vertical_missing_wood_mm3": round(v_missing, 3),
                                  "header_missing_wood_mm3": round(h_missing, 3)})
                    solids[key] = (v, h)
    panel_results = []
    for row in panel:
        start = tuple(float(row[f"start_{a}_mm"]) for a in "xyz")
        direction = cq.Vector(*(float(row[f"direction_{a}"]) for a in "xyz"))
        screws = {
            "frozen_occupied_50_8_mm": _cylinder(
                start, direction, FROZEN_SCREW_LENGTH, float(row["occupied_diameter_mm"])),
            "purchased_overall_63_5_mm_conditional": _cylinder(
                start, direction, PURCHASED_SCREW_LENGTH, float(row["occupied_diameter_mm"])),
        }
        received = wood[row["second_member"]].intersect(
            screws["frozen_occupied_50_8_mm"]).Volume()
        clashes = {
            envelope: [key for key, (v, h) in solids.items()
                       if v.intersect(screw).Volume() > 0.01
                       or h.intersect(screw).Volume() > 0.01]
            for envelope, screw in screws.items()
        }
        panel_results.append({"name": row["name"], "receiver": row["second_member"],
                              "receiving_volume_mm3": round(received, 3),
                              "nominal_bore_clashes_by_envelope": clashes})
    overlap = []
    for side in ("left", "right"):
        for face in ("outer", "inner"):
            for i in (1, 2):
                top = f"{side}_{face}_upper_{i}"
                bottom = f"{side}_{face}_lower_{i}"
                volume = solids[top][1].intersect(solids[bottom][1]).Volume()
                overlap.append({"upper": top, "lower": bottom,
                                "axis_separation_mm": round(lower_y[i - 1] - upper_y[i - 1], 4),
                                "overlapping_header_bore_mm3": round(volume, 3)})
    kicker_upper = [r for r in panel_results if "round_kicker_" in r["name"]
                    and r["name"].endswith("center_2")]
    # Bracket seats are separate from the bore solids. A positive overlap is a
    # nominal fit failure, not a measured collision volume for a purchased part.
    inner_plates = {
        (side, level): _inner_flange(side, level, y_min, hb)
        for level, y_min in (("upper", hb.ymin), ("lower", hb.ymax - LENGTH))
        for side in ("left", "right")
    }
    plate_collisions = []
    for level in ("upper", "lower"):
        left = inner_plates[("left", level)]
        right = inner_plates[("right", level)]
        opposite_kind = "principal" if level == "upper" else "post"
        plate_collisions.append({
            "level": level,
            "left_right_plate_overlap_mm3": round(left.intersect(right).Volume(), 3),
            "left_plate_opposite_timber_mm3": round(left.intersect(
                wood[f"base_{opposite_kind}_center_right"]).Volume(), 3),
            "right_plate_opposite_timber_mm3": round(right.intersect(
                wood[f"base_{opposite_kind}_center_left"]).Volume(), 3),
        })
    panel_names = {row["first_member"] for row in panel}
    plate_panel_intersections = [
        {"side": side, "level": level, "panel": name,
         "intersection_mm3": round(plate.intersect(baseline[name]).Volume(), 3)}
        for (side, level), plate in inner_plates.items()
        for name in sorted(panel_names)
        if plate.intersect(baseline[name]).Volume() > 0.01
    ]
    # The raised-header option retains all original post wood and enlarges its
    # footprint, not just the two screw-axis points.
    post_retained = {}
    inner_edge_overhang = {}
    for side in ("left", "right"):
        name = f"base_post_center_{side}"
        post_retained[side] = round(baseline[name].cut(wood[name]).Volume(), 3)
        kb = baseline[f"kicker_{side}"].BoundingBox()
        pb = wood[name].BoundingBox()
        inner_edge_overhang[side] = round((kb.xmax - pb.xmax) if side == "left"
                                          else (pb.xmin - kb.xmin), 4)
    old_header_bottom = baseline["base_header"].BoundingBox().zmin
    old_post_top = baseline["base_post_center_left"].BoundingBox().zmax
    downward_bottom = round(old_header_bottom - RISE, 4)
    downward_overlap = round(old_post_top - downward_bottom, 4)
    return {
        "status": "rejected_installed_geometry_trial",
        "concept": "full-width 3.5-in solid header rises 50.8 mm; center principal toes trimmed, 3.5-in solid center posts remain at original top; paired HL35 each face and upper/lower rows maximally staggered",
        "source": str(AXES.relative_to(ROOT)),
        "all_66_panel_axes_unchanged": True,
        "header_z_mm": [round(hb.zmin, 4), round(hb.zmax, 4)],
        "principal_min_z_mm": round(wood["base_principal_center_left"].BoundingBox().zmin, 4),
        "post_max_z_mm": round(wood["base_post_center_left"].BoundingBox().zmax, 4),
        "prior_downward_header_failure": {
            "new_header_bottom_z_mm": downward_bottom,
            "unchanged_post_overlap_mm": downward_overlap,
            "shortened_post_end_z_mm": downward_bottom,
            "protected_upper_kicker_screw_z_mm": 192.0,
            "screw_above_shortened_post_end_mm": round(192.0 - downward_bottom, 4),
        },
        "original_post_material_removed_mm3": post_retained,
        "remaining_kicker_inner_edge_overhang_mm": inner_edge_overhang,
        "full_kicker_inner_edge_support": all(v <= 0 for v in inner_edge_overhang.values()),
        "known_projection_nonclash": {
            "nominal_header_bolt_x_mm": -139.85,
            "protected_kicker_screw_x_mm": -70.0,
            "x_axis_separation_mm": 69.85,
            "sum_nominal_radii_mm": round(HOLE / 2 + 4.1402 / 2, 4),
            "finding": "a Y/Z projection overlap in that older pose is not a 3D collision",
        },
        "upper_y_mm": upper_y,
        "lower_y_mm": lower_y,
        "nominal_wood_bore_diameter_mm": HOLE,
        "horizontal_flange_hole_x_offset": {
            "assumed_nominal_mm": OFFSET,
            "qualification": "Undimensioned in the cited Simpson HL catalog drawing; symmetric placement is a modeling assumption, not a factory drilling coordinate.",
        },
        "ideal_inner_plate_envelope": {
            "flange_reach_mm": FLANGE_REACH,
            "assumed_plate_thickness_mm": IDEAL_PLATE_THICKNESS,
            "qualification": "Rectangular nominal 7-gauge seats; not delivered geometry. Bend radii, holes, coating, and tolerances omitted.",
            "collisions": plate_collisions,
            "panel_solid_intersections_over_0_01_mm3": plate_panel_intersections,
        },
        "bores": bores,
        "same_face_header_bore_pairs": overlap,
        "screw_envelope_lengths_mm": {
            "frozen_occupied": FROZEN_SCREW_LENGTH,
            "purchased_overall_conditional": PURCHASED_SCREW_LENGTH,
        },
        "panel_receivers_with_nominal_intersection": sum(r["receiving_volume_mm3"] > 0 for r in panel_results),
        "upper_kicker_receivers_with_nominal_intersection": sum(r["receiving_volume_mm3"] > 0 for r in kicker_upper),
        "panel_bore_clashes_by_envelope": {
            envelope: [r["name"] for r in panel_results
                       if r["nominal_bore_clashes_by_envelope"][envelope]]
            for envelope in ("frozen_occupied_50_8_mm",
                             "purchased_overall_63_5_mm_conditional")
        },
        "receiver_check_qualification": "Positive cylinder/receiver volume proves only some intersection, not required embedment, screw-body fit, or full panel-edge backing. Overhang is relative to these center posts, not all possible backing.",
        "disposition": "Reject this installed geometry: inner ideal HL35 seats overlap each other and opposite timbers; independent upper/lower header bores overlap at maximal Y stagger; the lower post bolt bore intersects both protected upper kicker screws even at the frozen 50.8-mm envelope; the inner kicker edges overhang these center posts; and the first upper principal bolt misses timber at its oblique toe. Shared bolts or shifted posts are different unqualified concepts. Washer, head/nut, tool, withdrawal, delivered-hole, neighbor-frame, edge/end, and load-path checks are not warranted for this rejected layout; no drilling or structural acceptance.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_hl35_center(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
