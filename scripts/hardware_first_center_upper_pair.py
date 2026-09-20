"""Opposing upper HL33s on the center-tongue pose; diagnostic geometry only."""

import argparse
import csv
import json
import math
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
    bore,
    bounds,
    box,
    cylinder,
    hits,
)
from scripts.hardware_first_center_hybrid_toe import _principal
from scripts.hardware_first_center_tongue import (
    HOLE_INSET,
    POST_DEPTH,
    POST_HALF,
    RAIL_END_X,
    TONGUE_HALF,
    UPPER_Y0,
    pair_clashes,
    screen_center_tongue,
)

BORE_DIAMETER = 14.2875  # ideal clearance envelope, not a drill size


def _overlaps(shapes, targets):
    return {
        name: found for name, shape in shapes.items() if (found := hits(shape, targets))
    }


def screen_upper_pair():
    """Test a second, inward-facing factory HL33 at each original upper Y station."""
    baseline = screen_center_tongue()
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    protected = [row for row in rows if row["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [row for row in rows if row["shop_opening_kind"] == "bolt_clearance"]
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    panels = {n: s for n, s in raw.items() if n.startswith(("main_", "kicker_"))}
    hb = raw["base_header"].BoundingBox()
    post_rear = hb.ymax - POST_DEPTH
    lower_top = hb.zmin - PLATE
    post = (
        box(-POST_HALF, post_rear, 0, 2 * POST_HALF, POST_DEPTH, lower_top)
        .fuse(
            box(-TONGUE_HALF, post_rear, lower_top, 2 * TONGUE_HALF, POST_DEPTH, PLATE)
        )
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
                hb.ymax - hb.ymin + REACH,
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

    new_plates = {}
    new_bores = {}
    principal_axes = {}
    header_axes = {}
    for side, center in (("left", -70.0), ("right", 70.0)):
        inner = center + (44.45 if side == "left" else -44.45)
        direction = 1 if side == "left" else -1
        new_plates[f"upper_{side}_inner_vertical"] = box(
            inner if direction > 0 else inner - PLATE,
            UPPER_Y0,
            TOP,
            PLATE,
            LENGTH,
            REACH,
        )
        new_plates[f"upper_{side}_inner_seat"] = box(
            inner if direction > 0 else inner - REACH,
            UPPER_Y0,
            TOP,
            REACH,
            LENGTH,
            PLATE,
        )
        principal_axes[side] = [center - 44.45, UPPER_Y0 + ALONG_BEND, TOP + LEG_HOLE]
        header_axes[side] = [inner + direction * LEG_HOLE, UPPER_Y0 + ALONG_BEND]
        new_bores[f"upper_{side}_inner_principal"] = bore(
            principal_axes[side], (1, 0, 0), 88.9
        )
        new_bores[f"upper_{side}_inner_header"] = bore(
            (*header_axes[side], hb.zmin), (0, 0, 1), TOP - hb.zmin
        )

    old_plates = {}
    for name, extent in baseline["plate_bounds_mm"].items():
        x0, x1, y0, y1, z0, z1 = extent
        old_plates[name] = box(x0, y0, z0, x1 - x0, y1 - y0, z1 - z0)
    old_bores = {
        "shared_post": bore(
            (-POST_HALF, post_rear + ALONG_BEND, lower_top - LEG_HOLE),
            (1, 0, 0),
            2 * POST_HALF,
        )
    }
    old_header_axes = {}
    for side, sign in (("left", -1), ("right", 1)):
        outer = sign * POST_HALF
        old_header_axes[f"lower_{side}"] = [
            outer - sign * HOLE_INSET,
            post_rear + ALONG_BEND,
        ]
        old_bores[f"lower_{side}_header"] = bore(
            (*old_header_axes[f"lower_{side}"], hb.zmin), (0, 0, 1), TOP - hb.zmin
        )
        center = sign * 70.0
        outer = center + sign * 44.45
        old_header_axes[f"upper_{side}"] = [
            outer + sign * LEG_HOLE,
            UPPER_Y0 + ALONG_BEND,
        ]
        old_bores[f"upper_{side}_header"] = bore(
            (*old_header_axes[f"upper_{side}"], hb.zmin), (0, 0, 1), TOP - hb.zmin
        )
        old_bores[f"upper_{side}_principal"] = bore(
            principal_axes[side], (1, 0, 0), 88.9
        )

    screws = {row["name"]: cylinder(row) for row in protected}
    long_screws = {row["name"]: cylinder(row, 63.5) for row in protected}
    frame = {row["name"]: cylinder(row) for row in frame_rows}
    new_hardware = {**new_plates, **new_bores}
    # Coincident principal bores are intentional shared axes, not independent crossings.
    independent_old_bores = {
        n: s for n, s in old_bores.items() if not n.endswith("_principal")
    }
    bore_wood = {
        n: (
            wood[f"base_principal_center_{n.split('_')[1]}"]
            if n.endswith("principal")
            else header
        )
        for n in new_bores
    }
    missing = {
        n: round(shape.Volume() - shape.intersect(bore_wood[n]).Volume(), 3)
        for n, shape in new_bores.items()
        if shape.Volume() - shape.intersect(bore_wood[n]).Volume() > TOL
    }
    new_plate_pair = pair_clashes(new_plates, skip_same_angle=True)
    new_to_old_plate = {
        n: found
        for n, shape in new_plates.items()
        if (found := hits(shape, old_plates))
    }
    all_header_axes = {
        **old_header_axes,
        **{f"inner_{s}": a for s, a in header_axes.items()},
    }
    header_distances = {
        f"inner_{side} / {name}": round(math.dist(axis, other), 4)
        for side, axis in header_axes.items()
        for name, other in all_header_axes.items()
        if name != f"inner_{side}"
    }
    inner_gap = 2 * (70.0 - 44.45)
    left_seat = new_plates["upper_left_inner_seat"].BoundingBox()
    right_seat = new_plates["upper_right_inner_seat"].BoundingBox()
    result = {
        "width_option": KERF_RIGHT,
        "source": str(AXES.relative_to(ROOT)),
        "pose": "inward HL33 on each principal at original upper Y = -100 mm",
        "catalog_nominal_mm": {
            "leg": REACH,
            "bend_length": LENGTH,
            "hole_along_bend": ALONG_BEND,
            "vertical_hole_from_bend": LEG_HOLE,
        },
        "ideal_plate_thickness_mm": PLATE,
        "ideal_bore_diameter_mm": BORE_DIAMETER,
        "protected_axis_count": len(protected),
        "retained_frame_axis_count": len(frame_rows),
        "fixed_panel_outline_count": len(panels),
        "changed_wood_bounds_unchanged": baseline["wood_bounds_mm"],
        "baseline_failures": baseline["failures"],
        "protected_screw_receiver_loss_mm3": baseline[
            "protected_screw_receiver_loss_mm3"
        ],
        "protected_screw_receiver_missing": baseline[
            "protected_screw_receiver_missing"
        ],
        "new_plate_bounds_mm": {n: bounds(s) for n, s in new_plates.items()},
        "new_bore_bounds_mm": {n: bounds(s) for n, s in new_bores.items()},
        "new_plate_pair_clashes_mm3": new_plate_pair,
        "new_to_existing_plate_clashes_mm3": new_to_old_plate,
        "new_plate_changed_wood_clashes_mm3": _overlaps(new_plates, wood),
        "new_plate_adjacent_wood_clashes_mm3": _overlaps(new_plates, adjacent),
        "new_plate_panel_clashes_mm3": _overlaps(new_plates, panels),
        "new_bore_missing_receiver_wood_mm3": missing,
        "new_bore_other_changed_wood_clashes_mm3": {
            n: found
            for n, shape in new_bores.items()
            if (
                found := hits(
                    shape, {k: v for k, v in wood.items() if v != bore_wood[n]}
                )
            )
        },
        "new_bore_panel_clashes_mm3": _overlaps(new_bores, panels),
        "new_bore_adjacent_wood_clashes_mm3": _overlaps(new_bores, adjacent),
        "new_independent_bore_crossings_mm3": {
            **{
                n: found
                for n, shape in new_bores.items()
                if (found := hits(shape, independent_old_bores))
            },
            **{
                n: found
                for n, shape in new_bores.items()
                if (
                    found := hits(shape, {k: v for k, v in new_bores.items() if k != n})
                )
            },
        },
        "protected_screw_new_hardware_clashes_mm3": _overlaps(screws, new_hardware),
        "conditional_63_5_screw_new_hardware_clashes_mm3": _overlaps(
            long_screws, new_hardware
        ),
        "existing_frame_axis_new_hardware_clashes_mm3": _overlaps(frame, new_hardware),
        "upper_principal_axis_relationship": "shared_per_principal",
        "upper_principal_axis_centers_mm": principal_axes,
        "upper_principal_shared_bore_overlap_mm3": {
            side: round(
                new_bores[f"upper_{side}_inner_principal"]
                .intersect(old_bores[f"upper_{side}_principal"])
                .Volume(),
                3,
            )
            for side in ("left", "right")
        },
        "upper_header_axis_relationship": "independent",
        "new_header_axis_centers_xy_mm": header_axes,
        "new_header_to_other_header_axis_distances_mm": header_distances,
        "minimum_header_bore_surface_gap_mm": round(
            min(header_distances.values()) - BORE_DIAMETER, 4
        ),
        "principal_inner_face_gap_mm": round(inner_gap, 4),
        "upper_pair_seat_overlap_x_mm": round(
            max(
                0,
                min(left_seat.xmax, right_seat.xmax)
                - max(left_seat.xmin, right_seat.xmin),
            ),
            4,
        ),
        "combined_seat_reach_beyond_inner_face_gap_mm": round(2 * REACH - inner_gap, 4),
        "minimum_y_shift_to_clear_equal_length_seats_mm": LENGTH,
    }
    failures = list(baseline["failures"])
    for label, keys in (
        (
            "upper paired plate collision",
            ("new_plate_pair_clashes_mm3", "new_to_existing_plate_clashes_mm3"),
        ),
        (
            "new plate wood collision",
            (
                "new_plate_changed_wood_clashes_mm3",
                "new_plate_adjacent_wood_clashes_mm3",
            ),
        ),
        ("new plate panel collision", ("new_plate_panel_clashes_mm3",)),
        (
            "new bore collision",
            (
                "new_bore_missing_receiver_wood_mm3",
                "new_bore_other_changed_wood_clashes_mm3",
                "new_bore_panel_clashes_mm3",
                "new_bore_adjacent_wood_clashes_mm3",
                "new_independent_bore_crossings_mm3",
            ),
        ),
        (
            "protected screw collision",
            (
                "protected_screw_new_hardware_clashes_mm3",
                "conditional_63_5_screw_new_hardware_clashes_mm3",
            ),
        ),
        (
            "existing frame axis collision",
            ("existing_frame_axis_new_hardware_clashes_mm3",),
        ),
    ):
        if any(result[key] for key in keys):
            failures.append(label)
    result["failures"] = failures
    result["status"] = (
        "rejected_installed_geometry_trial" if failures else "geometry_only_unqualified"
    )
    result["qualification"] = (
        "Ideal plates and bore envelopes only; assumed horizontal-flange hole inset. "
        "No capacity, drilling, installation, or acceptance claim."
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_upper_pair(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
