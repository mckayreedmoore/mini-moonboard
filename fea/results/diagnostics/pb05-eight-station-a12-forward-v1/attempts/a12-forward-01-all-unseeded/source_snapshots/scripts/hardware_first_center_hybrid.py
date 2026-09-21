"""One ideal HL35 hybrid center screen; dimensions are diagnostic, never drill data."""

import argparse
import csv
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
REACH = 82.55
LENGTH = 127.0
PLATE = 4.55
BORE = 14.2875
TOP = 327.8
POST_HALF = 92.075
PRINCIPAL_CENTER = 70.0
PRINCIPAL_WIDTH = 88.9
TOL = 0.01


def box(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def bounds(shape):
    b = shape.BoundingBox()
    return [round(v, 4) for v in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)]


def blank_envelope(shape, sloped=False):
    """Smallest sampled Y/Z rotation envelope for one unspliced shape."""
    b = shape.BoundingBox()
    if not sloped:
        return [round(b.xlen, 4), round(b.ylen, 4), round(b.zlen, 4)]
    points = [(v.Y, v.Z) for v in shape.Vertices()]
    candidates = []
    for step in range(1801):
        angle = math.radians(step / 10)
        c, s = math.cos(angle), math.sin(angle)
        along = [y * c + z * s for y, z in points]
        across = [-y * s + z * c for y, z in points]
        candidates.append((max(along) - min(along), max(across) - min(across)))
    length, depth = min(candidates, key=lambda pair: pair[0] * pair[1])
    return [
        round(b.xlen, 4),
        round(min(length, depth), 4),
        round(max(length, depth), 4),
    ]


def hits(shape, others):
    return {
        name: round(shape.intersect(other).Volume(), 3)
        for name, other in others.items()
        if shape.intersect(other).Volume() > TOL
    }


def cylinder(row, length=None):
    return cq.Solid.makeCylinder(
        float(row["occupied_diameter_mm"]) / 2,
        float(row["occupied_length_mm"]) if length is None else length,
        cq.Vector(*(float(row[f"start_{a}_mm"]) for a in "xyz")),
        cq.Vector(*(float(row[f"direction_{a}"]) for a in "xyz")),
    )


def bore(point, direction, length):
    return cq.Solid.makeCylinder(
        BORE / 2, length, cq.Vector(*point), cq.Vector(*direction)
    )


def screen_hybrid():
    with AXES.open(newline="") as stream:
        all_rows = list(csv.DictReader(stream))
    panel_rows = [r for r in all_rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in all_rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(panel_rows) != 66 or len({r["name"] for r in panel_rows}) != 66:
        raise ValueError("expected 66 distinct protected panel/kicker axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 existing frame axes for clash screening")
    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    hb = raw["base_header"].BoundingBox()
    front, rear = hb.ymax, hb.ymin
    lower_rear = rear - REACH
    # Single shaped solid header: original full-span beam, with a central
    # deeper raised region. The fuse is a CAD construction, not a built-up joint.
    header = (
        raw["base_header"]
        .fuse(box(-230, lower_rear, hb.zmin, 460, front - lower_rear, TOP - hb.zmin))
        .clean()
    )
    post = box(-POST_HALF, rear, 0, POST_HALF * 2, front - rear, hb.zmin)
    principals = {}
    for side, center in (("left", -PRINCIPAL_CENTER), ("right", PRINCIPAL_CENTER)):
        name = f"base_principal_center_{side}"
        original = raw[name]
        spread = (PRINCIPAL_WIDTH - 38.1) / 2
        widened = original.fuse(
            original.translate((-spread, 0, 0)), original.translate((spread, 0, 0))
        ).clean()
        b = widened.BoundingBox()
        principals[name] = widened.intersect(
            box(b.xmin - 1, b.ymin - 1, TOP, b.xlen + 2, b.ylen + 2, b.zmax - TOP + 2)
        ).clean()
    wood = {"post": post, "header": header, **principals}
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

    plates = {
        "lower_vertical": box(
            -LENGTH / 2, rear - PLATE, hb.zmin - REACH, LENGTH, PLATE, REACH
        ),
        "lower_seat": box(
            -LENGTH / 2, lower_rear, hb.zmin - PLATE, LENGTH, REACH, PLATE
        ),
    }
    # Upper HL35 bend runs in Y; vertical legs bear on outward X faces.
    # Two longitudinal holes on each leg are modeled independently.
    upper_y0 = rear
    for side, center in (("left", -PRINCIPAL_CENTER), ("right", PRINCIPAL_CENTER)):
        outer = center + (
            -PRINCIPAL_WIDTH / 2 if side == "left" else PRINCIPAL_WIDTH / 2
        )
        x0 = outer - PLATE if side == "left" else outer
        seat_x = outer - REACH if side == "left" else outer
        plates[f"upper_{side}_vertical"] = box(x0, upper_y0, TOP, PLATE, LENGTH, REACH)
        plates[f"upper_{side}_seat"] = box(seat_x, upper_y0, TOP, REACH, LENGTH, PLATE)

    bores = {}
    for i, x in enumerate((-31.75, 31.75), 1):
        bores[f"lower_post_{i}"] = (
            "post",
            bore((x, rear, hb.zmin - 50.8), (0, 1, 0), front - rear),
        )
        bores[f"lower_header_{i}"] = (
            "header",
            bore((x, rear - 50.8, hb.zmin), (0, 0, 1), TOP - hb.zmin),
        )
    for side, center in (("left", -PRINCIPAL_CENTER), ("right", PRINCIPAL_CENTER)):
        member = f"base_principal_center_{side}"
        outer = center + (
            -PRINCIPAL_WIDTH / 2 if side == "left" else PRINCIPAL_WIDTH / 2
        )
        hx = outer + (-50.8 if side == "left" else 50.8)
        for i, y in enumerate((upper_y0 + 31.75, upper_y0 + 95.25), 1):
            bores[f"upper_{side}_principal_{i}"] = (
                member,
                bore(
                    (center - PRINCIPAL_WIDTH / 2, y, TOP + 50.8),
                    (1, 0, 0),
                    PRINCIPAL_WIDTH,
                ),
            )
            bores[f"upper_{side}_header_{i}"] = (
                "header",
                bore((hx, y, hb.zmin), (0, 0, 1), TOP - hb.zmin),
            )

    screws = {r["name"]: cylinder(r) for r in panel_rows}
    long_screws = {r["name"]: cylinder(r, 63.5) for r in panel_rows}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    plate_pairs = {}
    for i, (a, solid) in enumerate(plates.items()):
        for b, other in list(plates.items())[i + 1 :]:
            if a.rsplit("_", 1)[0] == b.rsplit("_", 1)[0]:
                continue  # legs of the same ideal angle share a bend
            v = solid.intersect(other).Volume()
            if v > TOL:
                plate_pairs[f"{a} / {b}"] = round(v, 3)
    crossing = {}
    for lower in (n for n in bores if n.startswith("lower_")):
        for upper in (n for n in bores if n.startswith("upper_")):
            v = bores[lower][1].intersect(bores[upper][1]).Volume()
            if v > TOL:
                crossing[f"{lower} / {upper}"] = round(v, 3)
    missing = {
        n: round(max(0, solid.Volume() - solid.intersect(wood[member]).Volume()), 3)
        for n, (member, solid) in bores.items()
    }
    original_receiver_loss = {}
    protected_receiver_missing = {}
    for row in panel_rows:
        member = row["second_member"]
        receiver = principals.get(
            member,
            post
            if member.startswith("base_post_center_")
            else header
            if member == "base_header"
            else raw.get(member),
        )
        if receiver is None:
            raise ValueError(f"unknown protected screw receiver: {member}")
        old = screws[row["name"]].intersect(raw[member]).Volume()
        new = screws[row["name"]].intersect(receiver).Volume()
        if old - new > TOL:
            original_receiver_loss[row["name"]] = round(old - new, 3)
        if new <= TOL:
            protected_receiver_missing[row["name"]] = member
    kicker_receivers = {
        n: round(s.intersect(post).Volume(), 3)
        for n, s in screws.items()
        if n.startswith("round_kicker_") and "_center_" in n
    }
    screw_plate = {n: hits(s, plates) for n, s in screws.items() if hits(s, plates)}
    long_screw_plate = {
        n: hits(s, plates) for n, s in long_screws.items() if hits(s, plates)
    }
    screw_bore = {
        n: hits(s, {k: v for k, (_, v) in bores.items()})
        for n, s in screws.items()
        if hits(s, {k: v for k, (_, v) in bores.items()})
    }
    long_screw_bore = {
        n: hits(s, {k: v for k, (_, v) in bores.items()})
        for n, s in long_screws.items()
        if hits(s, {k: v for k, (_, v) in bores.items()})
    }
    frame_hardware = {
        n: hits(s, {**plates, **{k: v for k, (_, v) in bores.items()}})
        for n, s in frame.items()
        if hits(s, {**plates, **{k: v for k, (_, v) in bores.items()}})
    }
    panel_wood = {n: hits(s, panels) for n, s in wood.items()}
    adjacent_wood = {n: hits(s, adjacent) for n, s in wood.items()}
    plate_panel = {n: hits(s, panels) for n, s in plates.items()}
    plate_adjacent = {n: hits(s, adjacent) for n, s in plates.items()}
    plate_intended = {n: hits(s, wood) for n, s in plates.items()}
    # Measure upper toe occupancy independently of the full-bore wood fraction.
    toe = {n: missing[n] for n in bores if "principal" in n}
    one_piece = {n: len(s.Solids()) == 1 for n, s in wood.items()}
    blanks = {
        n: blank_envelope(s, n.startswith("base_principal_")) for n, s in wood.items()
    }
    # These are dimensional comparators, not confirmation of availability,
    # species, grade, defect-free yield, or machinability from delivered stock.
    stock_examples = {
        "post": [184.15, 139.7, 3048.0],
        "header": [88.9, 241.3, 3048.0],
        "base_principal_center_left": [139.7, 139.7, 3048.0],
        "base_principal_center_right": [139.7, 139.7, 3048.0],
    }
    stock_dimension_fit = {
        n: all(a <= b + TOL for a, b in zip(sorted(blank), sorted(stock_examples[n])))
        for n, blank in blanks.items()
    }
    eight_foot_header_surplus = round(2438.4 - blanks["header"][0], 4)
    eight_foot_principal_shortfall = round(
        blanks["base_principal_center_left"][2] - 2438.4, 4
    )
    failures = []
    for label, condition in (
        (
            "plate collision",
            bool(plate_pairs)
            or any(plate_panel.values())
            or any(plate_adjacent.values())
            or any(plate_intended.values()),
        ),
        ("new wood collision", any(panel_wood.values()) or any(adjacent_wood.values())),
        ("protected screw collision", bool(screw_plate) or bool(screw_bore)),
        ("independent bore crossing", bool(crossing)),
        ("bore exits receiving wood", any(v > TOL for v in missing.values())),
        (
            "protected screw receiver loss",
            bool(original_receiver_loss) or bool(protected_receiver_missing),
        ),
        ("existing frame bolt collision", bool(frame_hardware)),
        (
            "missing kicker center receiving wood",
            len(kicker_receivers) != 4
            or any(v <= TOL for v in kicker_receivers.values()),
        ),
        ("missing kicker seam support", not (-POST_HALF <= -1.5875 <= POST_HALF)),
        ("CAD wood is not one connected solid", not all(one_piece.values())),
        (
            "no considered ordinary stock blank can contain shape",
            not all(stock_dimension_fit.values()),
        ),
    ):
        if condition:
            failures.append(label)
    # Access, delivered-hole positions, edge distances and resistance cannot
    # be inferred from ideal envelopes. They bar release even if no clash occurs.
    return {
        "status": "rejected_installed_geometry_trial"
        if failures
        else "geometry_only_unqualified",
        "pose": "one rear-Y lower HL35 on front-aligned solid post; two outward-X upper HL35 on widened solid principals; single shaped solid header",
        "source": str(AXES.relative_to(ROOT)),
        "protected_axis_count": len(panel_rows),
        "retained_frame_bolt_axis_count": len(frame_rows),
        "post_bounds_mm": bounds(post),
        "header_bounds_mm": bounds(header),
        "principal_bounds_mm": {n: bounds(s) for n, s in principals.items()},
        "one_piece_cad_solid": one_piece,
        "minimum_sampled_blank_envelope_mm": blanks,
        "blank_envelope_method": "Post/header axis-aligned. Principal Y/Z rectangle minimized over 0.1-degree rotations about X; approximate geometric bound only, no machining allowance.",
        "ordinary_stock_example_actual_envelope_mm": stock_examples,
        "ordinary_stock_example_dimension_fit": stock_dimension_fit,
        "eight_foot_4x10_header_comparison": {
            "listed_actual_envelope_mm": [88.9, 241.3, 2438.4],
            "remaining_total_length_mm": eight_foot_header_surplus,
            "production_blank_feasible": False,
            "reason": "Only 3.175 mm remains in nominal length before end trim, saw kerf, defects, or delivered-length variation; no cutting allowance established.",
        },
        "eight_foot_principal_length_shortfall_mm": eight_foot_principal_shortfall,
        "no_considered_ordinary_stock_blank_can_contain_shape": not all(
            stock_dimension_fit.values()
        ),
        "retail_blank_status": "8-ft 4x10 listings are near-matches, not production blanks; 8-ft principal stock is too short. Ten-foot 4x10 and 6x6 are dimensional leads, but current local availability and delivered one-piece blanks are unverified. DF-L No. 2 grade, defects, machining allowance, and handling remain open. A missing fitting ordinary retail blank rejects this concept.",
        "stock_length_handling_condition": "Each part must be cut from one continuous blank at least as long as its listed envelope, with verified delivery, transport, support, and shop handling at full length; do not splice or laminate.",
        "cad_union_qualification": "Fusion is only a CAD union defining a one-piece machined timber shape; overlapping translated solids are not assembled plies or a lap joint.",
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "kicker_center_receivers_mm3": kicker_receivers,
        "kicker_seam_x_mm": -1.5875,
        "principal_screw_receiver_loss_mm3": original_receiver_loss,
        "protected_screw_receiver_missing": protected_receiver_missing,
        "plate_pair_clashes_mm3": plate_pairs,
        "plate_panel_clashes_mm3": plate_panel,
        "plate_adjacent_wood_clashes_mm3": plate_adjacent,
        "plate_intended_wood_clashes_mm3": plate_intended,
        "new_wood_panel_clashes_mm3": panel_wood,
        "new_wood_adjacent_clashes_mm3": adjacent_wood,
        "protected_screw_plate_clashes_mm3": screw_plate,
        "conditional_63_5_overall_screw_plate_clashes_mm3": long_screw_plate,
        "protected_screw_bore_clashes_mm3": screw_bore,
        "conditional_63_5_overall_screw_bore_clashes_mm3": long_screw_bore,
        "bore_missing_receiver_wood_mm3": missing,
        "upper_principal_toe_bore_missing_wood_mm3": toe,
        "independent_upper_lower_bore_crossings_mm3": crossing,
        "existing_frame_axis_hardware_clashes_mm3": frame_hardware,
        "failures": failures,
        "unresolved": [
            "delivered HL35 hole positions and bend",
            "heads, washers, nuts, tool and withdrawal access",
            "wood edge/end distances",
            "bracket and bolt resistance",
            "joint load path",
        ],
        "qualification": "Ideal 4.55-mm rectangles, assumed 50.8-mm horizontal hole offset and 14.2875-mm bores. Axes are occupied analysis envelopes, never drilling coordinates. No lap, custom steel, or capacity claim.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen_hybrid(), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
