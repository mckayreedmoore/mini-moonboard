"""Nominal access screen for the unselected AB205 shared center-header trial.

This is a collision diagnostic, not an installation sequence or joint approval.
The modeled angle is an ideal square-corner envelope with nominal clearance
holes; an actual purchased angle, bolt, washer, and tool must be checked later.
"""

import csv
from math import isfinite
from pathlib import Path

import cadquery as cq

from mini_moonboard import floor_flush_width
from scripts.bolted_candidate_center_y_stagger import (
    BOLT_D_MM,
    BORE_D_MM,
    LONG_OFFSETS_MM,
    PLATE_THICKNESS_MM,
    _angle_blocks,
)

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
ROW_Y_MM = -95.382052
DISTINCT_UNDERSIDE_Y_MM = -119.666026
COLLISION_VOLUME_MM3 = 1e-5


def _cylinder(x: float, y: float, z0: float, z1: float, radius: float) -> cq.Solid:
    return cq.Solid.makeCylinder(
        radius, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1)
    )


def _hits(probe: cq.Solid, obstacles: list[tuple[str, cq.Shape]]) -> list[str]:
    a = probe.BoundingBox()
    return sorted(
        name
        for name, shape in obstacles
        if not (
            a.xmax < shape.BoundingBox().xmin
            or a.xmin > shape.BoundingBox().xmax
            or a.ymax < shape.BoundingBox().ymin
            or a.ymin > shape.BoundingBox().ymax
            or a.zmax < shape.BoundingBox().zmin
            or a.zmin > shape.BoundingBox().zmax
        )
        and probe.intersect(shape).Volume() > COLLISION_VOLUME_MM3
    )


def _retained_axes() -> tuple[dict[str, int], list[tuple[str, cq.Solid]]]:
    counts = {"hillman_panel": 0, "bolt_clearance": 0}
    occupied = []
    with AXES.open(newline="") as handle:
        for row in csv.DictReader(handle):
            kind = row["shop_opening_kind"]
            if kind not in counts:
                continue
            counts[kind] += 1
            start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
            direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
            if kind == "hillman_panel" and abs(
                float(row["shop_purchased_length_mm"]) - 63.5
            ) > 1e-6:
                raise ValueError("Retained panel screw purchased length changed")
            # Keep the historical length and diameter together as one legacy
            # analysis envelope; neither is a physical Hillman screw envelope.
            length = float(row["occupied_length_mm"])
            occupied.append(
                (
                    f"retained:{row['name']}",
                    cq.Solid.makeCylinder(
                        float(row["occupied_diameter_mm"]) / 2,
                        length,
                        start,
                        direction,
                    ),
                )
            )
    if counts != {"hillman_panel": 66, "bolt_clearance": 12}:
        raise ValueError("Frozen retained-axis inventory changed")
    return counts, occupied


def _screen_case(
    *,
    underside_y_mm: float,
    raw: dict[str, cq.Shape],
    retained: list[tuple[str, cq.Solid]],
    bolt_length_mm: float,
    washer_probe_radius_mm: float,
    radial_probe_mm: float,
    radial_depth_mm: float,
    extra_obstacles: tuple[tuple[str, cq.Shape], ...],
) -> dict[str, object]:
    header = raw["base_header"]
    top_z = header.BoundingBox().zmax
    bottom_z = header.BoundingBox().zmin
    shared = abs(underside_y_mm - ROW_Y_MM) < 1e-6
    axes = []
    angle_blocks: list[tuple[str, cq.Shape]] = []
    bores = []
    for side, sign in (("left", -1), ("right", 1)):
        principal = raw[f"base_principal_center_{side}"].BoundingBox()
        post = raw[f"base_post_center_{side}"].BoundingBox()
        top_bend_x = principal.xmin if sign < 0 else principal.xmax
        bottom_bend_x = post.xmin if sign < 0 else post.xmax
        if abs(top_bend_x - bottom_bend_x) > 1e-6:
            raise ValueError("Top and underside nominal X axes no longer align")
        for index, offset in enumerate(LONG_OFFSETS_MM, start=1):
            x = top_bend_x + sign * offset
            rows = (
                (("shared", ROW_Y_MM),)
                if shared
                else (
                    ("top", ROW_Y_MM),
                    ("underside", underside_y_mm),
                )
            )
            for face, y in rows:
                axes.append((f"{side}_{face}_{index}", x, y, face))
                bores.append(_cylinder(x, y, bottom_z, top_z, BORE_D_MM / 2))
        for face, y, z, above in (
            ("top", ROW_Y_MM, top_z, True),
            ("underside", underside_y_mm, bottom_z, False),
        ):
            blocks = _angle_blocks(top_bend_x, y, z, sign, above=above)
            for index, block in enumerate(blocks):
                if index == 0:
                    for offset in LONG_OFFSETS_MM:
                        block = block.cut(
                            _cylinder(
                                top_bend_x + sign * offset,
                                y,
                                z - PLATE_THICKNESS_MM if not above else z,
                                z if not above else z + PLATE_THICKNESS_MM,
                                BORE_D_MM / 2,
                            )
                        )
                angle_blocks.append((f"angle:{side}:{face}:{index}", block))

    drilled_header = header
    for bore in bores:
        drilled_header = drilled_header.cut(bore)
    obstacles = [(name, solid) for name, solid in raw.items() if name != "base_header"]
    obstacles.append(("wood:base_header_after_nominal_bores", drilled_header))
    obstacles.extend(angle_blocks)
    obstacles.extend(retained)
    obstacles.extend(extra_obstacles)

    results = []
    for name, x, y, face in axes:
        stack_top = top_z + PLATE_THICKNESS_MM if face != "underside" else top_z
        stack_bottom = bottom_z - PLATE_THICKNESS_MM if face != "top" else bottom_z
        top_travel = _cylinder(
            x, y, stack_bottom, stack_top + bolt_length_mm, BOLT_D_MM / 2
        )
        bottom_travel = _cylinder(
            x, y, stack_bottom - bolt_length_mm, stack_top, BOLT_D_MM / 2
        )
        top_radial = _cylinder(
            x, y, stack_top, stack_top + radial_depth_mm, radial_probe_mm
        )
        bottom_radial = _cylinder(
            x, y, stack_bottom - radial_depth_mm, stack_bottom, radial_probe_mm
        )
        top_washer = _cylinder(
            x, y, stack_top, stack_top + PLATE_THICKNESS_MM, washer_probe_radius_mm
        )
        bottom_washer = _cylinder(
            x,
            y,
            stack_bottom - PLATE_THICKNESS_MM,
            stack_bottom,
            washer_probe_radius_mm,
        )
        results.append(
            {
                "axis": name,
                "x_mm": round(x, 6),
                "y_mm": y,
                "stack_mm": round(stack_top - stack_bottom, 6),
                "top_insertion_or_withdrawal_shaft_hits": _hits(top_travel, obstacles),
                "bottom_insertion_or_withdrawal_shaft_hits": _hits(
                    bottom_travel, obstacles
                ),
                "top_radial_envelope_hits": _hits(top_radial, obstacles),
                "bottom_radial_envelope_hits": _hits(bottom_radial, obstacles),
                "top_washer_envelope_hits": _hits(top_washer, obstacles),
                "bottom_washer_envelope_hits": _hits(bottom_washer, obstacles),
            }
        )
    return {
        "case": "coincident_shared_row" if shared else "distinct_row_midpoint",
        "top_y_mm": ROW_Y_MM,
        "underside_y_mm": underside_y_mm,
        "shared_through_header_axes": shared,
        "axes": results,
    }


def screen_center_access(
    *,
    bolt_length_mm: float = 76.2,
    washer_probe_radius_mm: float = 17.5,
    radial_probe_mm: float = 25.0,
    radial_depth_mm: float = 20.0,
    extra_obstacles: tuple[tuple[str, cq.Shape], ...] = (),
) -> dict[str, object]:
    """Check straight Z shaft travel and radial exterior envelopes at four axes.

    The 3-inch length and washer/tool cylinders are illustrative, not chosen hardware.
    Extra obstacles support controlled collision tests without editing the CAD.
    """
    if any(
        not isfinite(value) or value <= 0
        for value in (
            bolt_length_mm,
            washer_probe_radius_mm,
            radial_probe_mm,
            radial_depth_mm,
        )
    ):
        raise ValueError("Probe dimensions must be positive finite millimeters")
    if bolt_length_mm < 38.1 + 2 * PLATE_THICKNESS_MM:
        raise ValueError("Bolt shaft must span both flanges and the header")
    if min(washer_probe_radius_mm, radial_probe_mm) < BOLT_D_MM / 2:
        raise ValueError("Radial envelopes cannot be narrower than the nominal shaft")

    physical = floor_flush_width.variant(floor_flush_width.KERF_RIGHT)
    raw = {part.name: part.shape for part in physical.uncut_wood_parts()}
    panel_names = sorted(
        name
        for name in raw
        if name.startswith(("main_lower_", "main_upper_", "kicker_"))
    )
    if panel_names != sorted(
        (
            "main_lower_left",
            "main_lower_right",
            "main_upper_left",
            "main_upper_right",
            "kicker_left",
            "kicker_right",
        )
    ):
        raise ValueError("Kerf-right panel/kicker solid inventory changed")
    counts, retained = _retained_axes()
    cases = [
        _screen_case(
            underside_y_mm=y,
            raw=raw,
            retained=retained,
            bolt_length_mm=bolt_length_mm,
            washer_probe_radius_mm=washer_probe_radius_mm,
            radial_probe_mm=radial_probe_mm,
            radial_depth_mm=radial_depth_mm,
            extra_obstacles=extra_obstacles,
        )
        for y in (ROW_Y_MM, DISTINCT_UNDERSIDE_Y_MM)
    ]
    return {
        "status": "nominal_access_diagnostic_only",
        "trial": "unselected_AB205_shared_center_header",
        "width_option": floor_flush_width.KERF_RIGHT,
        "top_row_y_mm": ROW_Y_MM,
        "distinct_underside_midpoint_y_mm": DISTINCT_UNDERSIDE_Y_MM,
        "nominal_bolt_diameter_mm": BOLT_D_MM,
        "illustrative_bolt_length_mm": bolt_length_mm,
        "illustrative_washer_radius_mm": washer_probe_radius_mm,
        "radial_probe_radius_mm": radial_probe_mm,
        "radial_probe_depth_mm": radial_depth_mm,
        "kerf_right_panel_kicker_solid_obstacles": panel_names,
        "retained_axis_counts": counts,
        "panel_screw_clearance_input": {
            "purchased_length_mm": 63.5,
            "shaft_external_diameter_mm": None,
            "head_external_diameter_mm": None,
            "physical_clearance_status": "unresolved_external_envelope",
            "collision_obstacle_basis": "legacy_analysis_length_and_diameter",
        },
        "cases": cases,
        "limits": (
            "Raw kerf-right wood including four main panels and two kicker "
            "panel solids, plus historical analysis-envelope panel screw axes; "
            "the 63.5 mm purchased screws have no supported external shaft/head "
            "diameter here and physical screw clearance remains unresolved; "
            "ideal square-corner AB205 envelopes with nominal holes. Shaft is a "
            "12.7 mm cylinder; 76.2 mm length is illustrative, not a specified SKU. "
            "17.5 mm washer and 25 mm tool radii are sensitivity probes, not "
            "identified products, socket/wrench swing, bolt head, or hand clearance. "
            "Actual head/nut "
            "shape, shoulder/thread lengths, washers, tools, assembly order, "
            "bend radii, installed hardware, manufacturing/drilling tolerances, "
            "deflection and service access are unknown. A clear probe does not "
            "verify installed-panel access, installation or removal."
        ),
        "joint_selected": False,
        "access_verified": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(screen_center_access(), indent=2))
