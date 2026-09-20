"""One full-center HL33 tongue CAD screen; analysis geometry, never drill data."""

import argparse
import csv
import json
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.hardware_first_center_hl33 import (
    ALONG_BEND,
    LEG_HOLE,
    LENGTH,
    PLATE,
    REACH,
)
from scripts.hardware_first_center_hybrid import (
    AXES,
    ROOT,
    TOL,
    TOP,
    blank_envelope,
    bore,
    bounds,
    box,
    cylinder,
    hits,
)
from scripts.hardware_first_center_hybrid_toe import _principal

POST_HALF = 95.25
POST_DEPTH = 90.47
TONGUE_HALF = POST_HALF - REACH
RAIL_END_X = 120.0
UPPER_Y0 = -100.0
HOLE_INSET = 50.8  # assumed; HL33 horizontal-flange offset is undimensioned
SEAM_X = -1.5875
MIN_RECEIVER = 88.9


def clashes(shapes, targets):
    return {n: found for n, shape in shapes.items() if (found := hits(shape, targets))}


def pair_clashes(shapes, *, skip_same_angle=False):
    result = {}
    entries = list(shapes.items())
    for i, (name, shape) in enumerate(entries):
        for other_name, other in entries[i + 1 :]:
            if (
                skip_same_angle
                and name.rsplit("_", 1)[0] == other_name.rsplit("_", 1)[0]
            ):
                continue
            volume = shape.intersect(other).Volume()
            if volume > TOL:
                result[f"{name} / {other_name}"] = round(volume, 3)
    return result


def screen_center_tongue():
    """Screen the one-piece tongue pose against every fixed occupied envelope."""
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    protected = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    if len(protected) != 66 or len({r["name"] for r in protected}) != 66:
        raise ValueError("expected 66 unique fixed panel/kicker axes")
    if len(frame_rows) != 12:
        raise ValueError("expected 12 fixed frame axes")

    raw = {p.name: p.shape for p in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    hb = raw["base_header"].BoundingBox()
    front = hb.ymax
    post_rear = front - POST_DEPTH
    lower_top = hb.zmin - PLATE
    # This union describes one machined timber. The tongue fills only the
    # center gap between seats and reaches the header's underside.
    tongue = box(-TONGUE_HALF, post_rear, lower_top, 2 * TONGUE_HALF, POST_DEPTH, PLATE)
    post = (
        box(-POST_HALF, post_rear, 0, 2 * POST_HALF, POST_DEPTH, lower_top)
        .fuse(tongue)
        .clean()
    )
    header = (
        raw["base_header"]
        .fuse(
            box(
                -230,
                hb.ymin - REACH,
                hb.zmin,
                460,
                front - hb.ymin + REACH,
                TOP - hb.zmin,
            )
        )
        .clean()
    )
    wood = {"post": post, "header": header}
    for side in ("left", "right"):
        wood[f"base_principal_center_{side}"] = _principal(side)
    rail_names = tuple(
        f"base_rail_{level}_{side}"
        for side in ("left", "right")
        for level in ("bottom", "service_lower", "service_upper")
    )
    for name in rail_names:
        original = raw[name]
        b = original.BoundingBox()
        x0, x1 = (
            (b.xmin - 1, -RAIL_END_X)
            if name.endswith("left")
            else (RAIL_END_X, b.xmax + 1)
        )
        wood[name] = original.intersect(
            box(x0, b.ymin - 1, b.zmin - 1, x1 - x0, b.ylen + 2, b.zlen + 2)
        ).clean()
    replaced = {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_principal_center_left",
        "base_principal_center_right",
        *rail_names,
    }
    adjacent = {n: s for n, s in raw.items() if n not in panels and n not in replaced}

    plates = {}
    bores = {}
    for side, sign in (("left", -1), ("right", 1)):
        outer = sign * POST_HALF
        plates[f"lower_{side}_vertical"] = box(
            outer - PLATE if sign < 0 else outer,
            post_rear,
            lower_top - REACH,
            PLATE,
            LENGTH,
            REACH,
        )
        plates[f"lower_{side}_seat"] = box(
            min(outer, outer - sign * REACH), post_rear, lower_top, REACH, LENGTH, PLATE
        )
        bores[f"lower_{side}_header"] = (
            "header",
            bore(
                (outer - sign * HOLE_INSET, post_rear + ALONG_BEND, hb.zmin),
                (0, 0, 1),
                TOP - hb.zmin,
            ),
        )
    bores["shared_post"] = (
        "post",
        bore(
            (-POST_HALF, post_rear + ALONG_BEND, lower_top - LEG_HOLE),
            (1, 0, 0),
            2 * POST_HALF,
        ),
    )
    for side, center in (("left", -70.0), ("right", 70.0)):
        outer = center + (-44.45 if side == "left" else 44.45)
        plates[f"upper_{side}_vertical"] = box(
            outer - PLATE if side == "left" else outer,
            UPPER_Y0,
            TOP,
            PLATE,
            LENGTH,
            REACH,
        )
        plates[f"upper_{side}_seat"] = box(
            outer - REACH if side == "left" else outer,
            UPPER_Y0,
            TOP,
            REACH,
            LENGTH,
            PLATE,
        )
        bores[f"upper_{side}_principal"] = (
            f"base_principal_center_{side}",
            bore(
                (center - 44.45, UPPER_Y0 + ALONG_BEND, TOP + LEG_HOLE), (1, 0, 0), 88.9
            ),
        )
        bores[f"upper_{side}_header"] = (
            "header",
            bore(
                (
                    outer + (-LEG_HOLE if side == "left" else LEG_HOLE),
                    UPPER_Y0 + ALONG_BEND,
                    hb.zmin,
                ),
                (0, 0, 1),
                TOP - hb.zmin,
            ),
        )

    bore_shapes = {n: s for n, (_, s) in bores.items()}
    hardware = {**plates, **bore_shapes}
    screws = {r["name"]: cylinder(r) for r in protected}
    long_screws = {r["name"]: cylinder(r, 63.5) for r in protected}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    receivers = dict(raw)
    receivers.update(wood)
    receivers["base_header"] = header
    receivers["base_post_center_left"] = post
    receivers["base_post_center_right"] = post
    receiver_loss = {}
    receiver_missing = {}
    for row in protected:
        name, member = row["name"], row["second_member"]
        old = screws[name].intersect(raw[member]).Volume()
        new = screws[name].intersect(receivers[member]).Volume()
        if old - new > TOL:
            receiver_loss[name] = round(old - new, 3)
        if new <= TOL:
            receiver_missing[name] = member

    bore_missing = {
        n: round(max(0, s.Volume() - s.intersect(wood[member]).Volume()), 3)
        for n, (member, s) in bores.items()
        if s.Volume() - s.intersect(wood[member]).Volume() > TOL
    }
    bore_other = {
        n: found
        for n, (member, s) in bores.items()
        if (found := hits(s, {k: v for k, v in wood.items() if k != member}))
    }
    blanks = {
        n: blank_envelope(s, n.startswith("base_principal_") or n in rail_names)
        for n, s in wood.items()
    }
    stock = {
        "post": [90.47, 190.5, 2438.4],
        "header": [90.4748, 241.3, 3657.6],
        **{n: [139.7, 139.7, 3048.0] for n in wood if n.startswith("base_principal_")},
        **{n: [38.1, 139.7, 3048.0] for n in rail_names},
    }
    stock_fit = {
        n: all(a <= b + TOL for a, b in zip(sorted(blanks[n]), sorted(stock[n])))
        for n in wood
    }
    backing = {
        "left": round(SEAM_X + TONGUE_HALF, 4),
        "right": round(TONGUE_HALF - SEAM_X, 4),
    }
    half_plywood = 19.05 / 2
    lower_header_x = [sign * (POST_HALF - HOLE_INSET) for sign in (-1, 1)]
    upper_header_x = [sign * (70.0 + 44.45 + LEG_HOLE) for sign in (-1, 1)]
    header_axis_spacing = min(
        abs(a - b) for a in lower_header_x for b in upper_header_x
    )
    result = {
        "width_option": KERF_RIGHT,
        "source": str(AXES.relative_to(ROOT)),
        "protected_axis_count": len(protected),
        "retained_frame_axis_count": len(frame_rows),
        "changed_rail_count": len(rail_names),
        "fixed_panel_outline_count": len(panels),
        "wood_bounds_mm": {n: bounds(s) for n, s in wood.items()},
        "tongue_bounds_mm": bounds(tongue),
        "lower_seat_center_x_gap_mm": round(2 * TONGUE_HALF, 4),
        "tongue_backing_width_each_edge_mm": backing,
        "tongue_backing_width_qualification": (
            "Ideal CAD contact widths only; no bearing minimum, delivered tolerance pass, "
            "or actual edge-support criterion is established."
        ),
        "illustrative_half_19_05_plywood_mm": half_plywood,
        "illustrative_left_width_over_half_plywood_mm": round(
            backing["left"] - half_plywood, 4
        ),
        "tongue_meets_header": abs(tongue.BoundingBox().zmax - hb.zmin) <= TOL,
        "minimum_upper_lower_header_bore_axis_spacing_mm": round(
            header_axis_spacing, 4
        ),
        "minimum_upper_lower_header_bore_surface_gap_mm": round(
            header_axis_spacing - 14.2875, 4
        ),
        "kicker_seam_x_mm": SEAM_X,
        "kicker_center_receivers_mm3": {
            n: round(s.intersect(post).Volume(), 3)
            for n, s in screws.items()
            if n.startswith("round_kicker_") and "_center_" in n
        },
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "bore_bounds_mm": {n: bounds(s) for n, s in bore_shapes.items()},
        "plate_pair_clashes_mm3": pair_clashes(plates, skip_same_angle=True),
        "plate_wood_clashes_mm3": clashes(plates, wood),
        "plate_panel_clashes_mm3": clashes(plates, panels),
        "plate_adjacent_wood_clashes_mm3": clashes(plates, adjacent),
        "changed_wood_pair_clashes_mm3": pair_clashes(wood),
        "wood_panel_clashes_mm3": clashes(wood, panels),
        "wood_adjacent_clashes_mm3": clashes(wood, adjacent),
        "bore_missing_receiver_wood_mm3": bore_missing,
        "independent_bore_crossings_mm3": pair_clashes(bore_shapes),
        "bore_other_wood_clashes_mm3": bore_other,
        "bore_panel_clashes_mm3": clashes(bore_shapes, panels),
        "bore_adjacent_wood_clashes_mm3": clashes(bore_shapes, adjacent),
        "protected_screw_hardware_clashes_mm3": clashes(screws, hardware),
        "conditional_63_5_overall_screw_hardware_clashes_mm3": clashes(
            long_screws, hardware
        ),
        "protected_screw_receiver_loss_mm3": receiver_loss,
        "protected_screw_receiver_missing": receiver_missing,
        "existing_frame_axis_hardware_clashes_mm3": clashes(frame, hardware),
        "existing_frame_axis_changed_wood_clashes_mm3": clashes(frame, wood),
        "one_piece_cad_solid": {n: len(s.Solids()) == 1 for n, s in wood.items()},
        "minimum_sampled_blank_envelope_mm": blanks,
        "ordinary_stock_example_actual_envelope_mm": stock,
        "ordinary_stock_example_dimension_fit": stock_fit,
        "post_listed_4x8_thickness_margin_over_hl_minimum_mm": round(
            3.562 * 25.4 - MIN_RECEIVER, 4
        ),
    }
    failures = []
    for label, bad in (
        (
            "receiver thickness",
            2 * POST_HALF + TOL < MIN_RECEIVER or TOP - hb.zmin + TOL < MIN_RECEIVER,
        ),
        (
            "plate collision",
            any(
                result[k]
                for k in (
                    "plate_pair_clashes_mm3",
                    "plate_wood_clashes_mm3",
                    "plate_panel_clashes_mm3",
                    "plate_adjacent_wood_clashes_mm3",
                )
            ),
        ),
        (
            "wood collision",
            any(
                result[k]
                for k in (
                    "changed_wood_pair_clashes_mm3",
                    "wood_panel_clashes_mm3",
                    "wood_adjacent_clashes_mm3",
                )
            ),
        ),
        (
            "bore collision",
            any(
                result[k]
                for k in (
                    "bore_missing_receiver_wood_mm3",
                    "independent_bore_crossings_mm3",
                    "bore_other_wood_clashes_mm3",
                    "bore_panel_clashes_mm3",
                    "bore_adjacent_wood_clashes_mm3",
                )
            ),
        ),
        (
            "protected screw collision",
            bool(result["protected_screw_hardware_clashes_mm3"]),
        ),
        (
            "conditional full-length screw collision",
            bool(result["conditional_63_5_overall_screw_hardware_clashes_mm3"]),
        ),
        ("protected screw receiver loss", bool(receiver_loss or receiver_missing)),
        (
            "existing frame axis collision",
            bool(
                result["existing_frame_axis_hardware_clashes_mm3"]
                or result["existing_frame_axis_changed_wood_clashes_mm3"]
            ),
        ),
        (
            "kicker seam backing failure",
            not result["tongue_meets_header"]
            or abs(2 * TONGUE_HALF - 25.4) > TOL
            or any(v <= TOL for v in backing.values())
            or len(result["kicker_center_receivers_mm3"]) != 4
            or any(v <= TOL for v in result["kicker_center_receivers_mm3"].values())
            or abs(post.BoundingBox().ymax - front) > TOL,
        ),
        ("header upper/lower bore separation", header_axis_spacing <= 14.2875 + TOL),
        ("one-piece wood failure", not all(result["one_piece_cad_solid"].values())),
        ("stock dimension failure", not all(stock_fit.values())),
    ):
        if bad:
            failures.append(label)
    result["failures"] = failures
    result["status"] = (
        "rejected_installed_geometry_trial" if failures else "geometry_only_unqualified"
    )
    result["unresolved"] = [
        "One outward-X upper HL33 per principal has no demonstrated reversible-F1 coverage.",
        "The shared lower post bolt action and the six rail-to-center attachments are unqualified.",
        "Full bolt stacks, head/nut/washer and tool access, delivered hole locations, wood edge/end distances, and capacities remain unverified.",
    ]
    result["qualification"] = (
        "Ideal 4.55-mm plates and 14.2875-mm bores; fixed occupied axes are analysis geometry only. No fabrication coordinates or approval."
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_center_tongue(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
