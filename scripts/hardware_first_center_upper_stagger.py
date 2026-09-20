"""Rearward inward HL33 pair on the unchanged center-tongue wood pose."""

import argparse
import csv
import json
from math import hypot
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.bolted_candidate_ab205_center_fit import (
    _grain_edge_lines,
    _line_y,
    _principal_broad_face,
)
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
from scripts.hardware_first_center_tongue_wood import (
    _axis_record,
    _face_ray,
    screen_center_tongue_wood,
)

BOLT_DIAMETER = 12.7
BORE_DIAMETER = 14.2875  # ideal diagnostic envelope
SHIFTS = (63.5, 66.0, 70.0)  # mm rearward from outer HL33; bounded screen


def _overlaps(shapes, targets):
    return {n: found for n, s in shapes.items() if (found := hits(s, targets))}


def _wood_and_context():
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
    return raw, panels, wood, adjacent, hb


def _principal_axis_geometry(member, center, y):
    face = _principal_broad_face(member, member.BoundingBox().xmin)
    lines = _grain_edge_lines(face)
    if len(lines) != 2 or abs(lines[0][2] - lines[1][2]) > 1e-6:
        raise ValueError("Expected parallel principal grain edges")
    slope = lines[0][2]
    gy, gz = slope / hypot(slope, 1), 1 / hypot(slope, 1)
    z = TOP + LEG_HOLE
    lower_y, upper_y = sorted(_line_y(line, z) for line in lines)
    transverse = ((y - lower_y) * gz, (upper_y - y) * gz)
    return _axis_record(
        "principal",
        (center, y, z),
        (0, gy, gz),
        (_face_ray(face, y, z, gy, gz, -1), _face_ray(face, y, z, gy, gz, 1)),
        transverse,
        oblique=True,
    )


def _pose(shift, baseline, panels, wood, adjacent, hb, screws, long_screws, frame):
    y0 = UPPER_Y0 - shift
    plates = {}
    bores = {}
    axes = {}
    header_centers = {}
    for side, center in (("left", -70.0), ("right", 70.0)):
        inner = center + (44.45 if side == "left" else -44.45)
        direction = 1 if side == "left" else -1
        plates[f"upper_{side}_inner_vertical"] = box(
            inner if direction > 0 else inner - PLATE, y0, TOP, PLATE, LENGTH, REACH
        )
        plates[f"upper_{side}_inner_seat"] = box(
            inner if direction > 0 else inner - REACH, y0, TOP, REACH, LENGTH, PLATE
        )
        principal_y = y0 + ALONG_BEND
        header_x = inner + direction * LEG_HOLE
        header_centers[side] = (header_x, principal_y)
        principal = wood[f"base_principal_center_{side}"]
        bores[f"upper_{side}_inner_principal"] = bore(
            (center - 44.45, principal_y, TOP + LEG_HOLE), (1, 0, 0), 88.9
        )
        bores[f"upper_{side}_inner_header"] = bore(
            (header_x, principal_y, hb.zmin), (0, 0, 1), TOP - hb.zmin
        )
        axes[f"upper_{side}_inner_principal"] = _principal_axis_geometry(
            principal, center, principal_y
        )
        hbox = wood["header"].BoundingBox()
        axes[f"upper_{side}_inner_header"] = _axis_record(
            "header",
            (header_x, principal_y, (hb.zmin + TOP) / 2),
            (1, 0, 0),
            (header_x + 230, 230 - header_x),
            (principal_y - hbox.ymin, hbox.ymax - principal_y),
        )
        axes[f"upper_{side}_inner_header"]["grain_boundary_kind"] = (
            "raised_profile_shoulder_not_free_end"
        )
        axes[f"upper_{side}_inner_header"][
            "full_span_grain_rays_at_lower_section_mm"
        ] = [round(header_x - hbox.xmin, 4), round(hbox.xmax - header_x, 4)]

    old_plates = {}
    for name, extent in baseline["plate_bounds_mm"].items():
        x0, x1, oy0, oy1, z0, z1 = extent
        old_plates[name] = box(x0, oy0, z0, x1 - x0, oy1 - oy0, z1 - z0)
    old_bores = {}
    existing_header_centers = {}
    for side, sign in (("left", -1), ("right", 1)):
        lower = (sign * (POST_HALF - HOLE_INSET), hb.ymax - POST_DEPTH + ALONG_BEND)
        outer = (sign * (70 + 44.45 + LEG_HOLE), UPPER_Y0 + ALONG_BEND)
        existing_header_centers[f"lower_{side}"] = lower
        existing_header_centers[f"outer_{side}"] = outer
        old_bores[f"lower_{side}_header"] = bore(
            (*lower, hb.zmin), (0, 0, 1), TOP - hb.zmin
        )
        old_bores[f"outer_{side}_header"] = bore(
            (*outer, hb.zmin), (0, 0, 1), TOP - hb.zmin
        )
        old_bores[f"outer_{side}_principal"] = bore(
            (sign * 70 - 44.45, UPPER_Y0 + ALONG_BEND, TOP + LEG_HOLE),
            (1, 0, 0),
            88.9,
        )
    old_bores["shared_post"] = bore(
        (-POST_HALF, hb.ymax - POST_DEPTH + ALONG_BEND, hb.zmin - PLATE - LEG_HOLE),
        (1, 0, 0),
        2 * POST_HALF,
    )
    receiver = {
        n: (
            wood[f"base_principal_center_{n.split('_')[1]}"]
            if n.endswith("principal")
            else wood["header"]
        )
        for n in bores
    }
    missing = {
        n: round(s.Volume() - s.intersect(receiver[n]).Volume(), 3)
        for n, s in bores.items()
        if s.Volume() - s.intersect(receiver[n]).Volume() > TOL
    }
    header_distances = {
        f"inner_{side} / {name}": round(hypot(x - other[0], y - other[1]), 4)
        for side, (x, y) in header_centers.items()
        for name, other in {
            **existing_header_centers,
            **{f"inner_{k}": v for k, v in header_centers.items()},
        }.items()
        if name != f"inner_{side}"
    }
    all_new = {**plates, **bores}
    principal_grain = axes["upper_left_inner_principal"]["grain_unit_xyz"]
    result = {
        "shift_rearward_mm": shift,
        "inner_upper_y_range_mm": [y0, y0 + LENGTH],
        "outer_upper_y_range_mm": [UPPER_Y0, UPPER_Y0 + LENGTH],
        "plate_bounds_mm": {n: bounds(s) for n, s in plates.items()},
        "bore_bounds_mm": {n: bounds(s) for n, s in bores.items()},
        "axis_boundary_rays": axes,
        "principal_bolt_center_separation_mm": shift,
        "principal_bolt_separation_along_grain_mm": round(
            shift * principal_grain[1], 3
        ),
        "principal_bolt_separation_across_grain_mm": round(
            shift * principal_grain[2], 3
        ),
        "principal_bolt_center_separation_3d_comparator_margin_mm": round(
            shift - 3 * BOLT_DIAMETER, 4
        ),
        "principal_bolt_center_separation_4d_comparator_margin_mm": round(
            shift - 4 * BOLT_DIAMETER, 4
        ),
        "header_axis_distances_mm": header_distances,
        "minimum_header_bore_surface_gap_mm": round(
            min(header_distances.values()) - BORE_DIAMETER, 4
        ),
        "new_plate_pair_clashes_mm3": pair_clashes(plates, skip_same_angle=True),
        "new_to_existing_plate_clashes_mm3": _overlaps(plates, old_plates),
        "new_plate_changed_wood_clashes_mm3": _overlaps(plates, wood),
        "new_plate_adjacent_wood_clashes_mm3": _overlaps(plates, adjacent),
        "new_plate_panel_clashes_mm3": _overlaps(plates, panels),
        "new_bore_missing_receiver_wood_mm3": missing,
        "new_bore_other_changed_wood_clashes_mm3": {
            n: found
            for n, s in bores.items()
            if (found := hits(s, {k: v for k, v in wood.items() if v != receiver[n]}))
        },
        "new_bore_panel_clashes_mm3": _overlaps(bores, panels),
        "new_bore_adjacent_wood_clashes_mm3": _overlaps(bores, adjacent),
        "new_independent_bore_crossings_mm3": {
            n: found
            for n, s in bores.items()
            if (
                found := hits(
                    s, {**old_bores, **{k: v for k, v in bores.items() if k != n}}
                )
            )
        },
        "protected_screw_new_hardware_clashes_mm3": _overlaps(screws, all_new),
        "conditional_63_5_screw_new_hardware_clashes_mm3": _overlaps(
            long_screws, all_new
        ),
        "existing_frame_axis_new_hardware_clashes_mm3": _overlaps(frame, all_new),
    }
    failures = []
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
        ("new bore receiver loss", ("new_bore_missing_receiver_wood_mm3",)),
        (
            "new bore collision",
            (
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
        "rejected_installed_geometry_trial" if failures else "conditional_geometry_only"
    )
    return result


def screen_upper_stagger():
    """Sample the first 6.5 mm beyond the minimum rearward band separation."""
    baseline = screen_center_tongue()
    baseline_wood = screen_center_tongue_wood()
    with AXES.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    protected = [r for r in rows if r["shop_opening_kind"] == "hillman_panel"]
    frame_rows = [r for r in rows if r["shop_opening_kind"] == "bolt_clearance"]
    _, panels, wood, adjacent, hb = _wood_and_context()
    screws = {r["name"]: cylinder(r) for r in protected}
    long_screws = {r["name"]: cylinder(r, 63.5) for r in protected}
    frame = {r["name"]: cylinder(r) for r in frame_rows}
    samples = [
        _pose(shift, baseline, panels, wood, adjacent, hb, screws, long_screws, frame)
        for shift in SHIFTS
    ]
    return {
        "status": "rejected_installed_geometry_trial"
        if all(s["failures"] for s in samples)
        else "conditional_geometry_only",
        "width_option": KERF_RIGHT,
        "source": str(AXES.relative_to(ROOT)),
        "source_pose": "scripts.hardware_first_center_tongue",
        "outer_upper_y0_mm": UPPER_Y0,
        "shift_samples_mm": list(SHIFTS),
        "catalog_nominal_mm": {
            "leg": REACH,
            "bend_length": LENGTH,
            "along_bend_hole": ALONG_BEND,
            "vertical_leg_hole": LEG_HOLE,
        },
        "ideal_plate_thickness_mm": PLATE,
        "ideal_bore_diameter_mm": BORE_DIAMETER,
        "bolt_center_diameter_comparator_mm": BOLT_DIAMETER,
        "protected_axis_count": len(protected),
        "retained_frame_axis_count": len(frame_rows),
        "fixed_panel_outline_count": len(panels),
        "baseline_failures": baseline["failures"],
        "existing_fastener_axis_boundary_rays": baseline_wood["axis_margins"],
        "protected_screw_receiver_loss_mm3": baseline[
            "protected_screw_receiver_loss_mm3"
        ],
        "protected_screw_receiver_missing": baseline[
            "protected_screw_receiver_missing"
        ],
        "samples": samples,
        "qualification": "Ideal factory-shape envelope with assumed horizontal hole inset. Centerline rays at an oblique principal end and header shoulder are not code end-distance classifications. No capacity, drilling, installation, or acceptance claim.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(screen_upper_stagger(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
