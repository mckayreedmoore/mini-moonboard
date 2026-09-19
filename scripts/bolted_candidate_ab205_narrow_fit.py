"""Nominal AB205 geometry at one actual narrow/opposing station; no approval."""

import csv
from math import isfinite, pi
from pathlib import Path
from typing import Literal

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as frame

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"


def _round_vector(point: cq.Vector) -> list[float]:
    return [round(value, 6) for value in point.toTuple()]


def screen_narrow_fit(
    rail_leg: Literal["long", "short"] = "long",
    row_shift_mm: float = 0.0,
) -> dict[str, object]:
    """Screen a bounded row shift on the actual rail/principal contact faces."""
    if rail_leg not in ("long", "short"):
        raise ValueError("Rail AB205 leg must be long or short")
    if not isfinite(row_shift_mm):
        raise ValueError("Row shift must be finite")
    parts = {part.name: part.shape for part in frame.uncut_wood_parts()}
    station = next(
        item for item in frame.stations() if item[0] == "clip_horizontal_bottom_left_2"
    )
    name, origin, rail_direction, principal_direction, rail_name, principal_name = (
        station
    )
    rail = parts[rail_name]
    principal = parts[principal_name]
    opposite_principal = parts["base_principal_center_right"]
    width_direction = rail_direction.cross(principal_direction)
    center_width = origin.dot(width_direction)
    half_flange_width = 1.625 * 25.4 / 2
    width_limits = [
        (
            min(vertex.Center().dot(width_direction) for vertex in solid.Vertices()),
            max(vertex.Center().dot(width_direction) for vertex in solid.Vertices()),
        )
        for solid in (rail, principal)
    ]
    shift_lower = max(low + half_flange_width - center_width for low, _ in width_limits)
    shift_upper = min(
        high - half_flange_width - center_width for _, high in width_limits
    )
    if not shift_lower - 1e-6 <= row_shift_mm <= shift_upper + 1e-6:
        raise ValueError("Row shift exceeds common nominal flange-width bounds")
    contact = origin + width_direction * row_shift_mm
    long_offsets = (1.4375, 3.3125)
    short_offsets = (0.8125, 2.6875)
    rail_offsets = long_offsets if rail_leg == "long" else short_offsets
    principal_offsets = short_offsets if rail_leg == "long" else long_offsets
    bore_radius = 0.5625 * 25.4 / 2
    bolt_diameter = 0.5 * 25.4
    rail_thickness = max(
        vertex.Center().dot(principal_direction) for vertex in rail.Vertices()
    ) - min(vertex.Center().dot(principal_direction) for vertex in rail.Vertices())
    holes = []
    bores = []
    for member, solid, offsets, along, inward in (
        (rail_name, rail, rail_offsets, rail_direction, -principal_direction),
        (
            principal_name,
            principal,
            principal_offsets,
            principal_direction,
            -rail_direction,
        ),
    ):
        for offset in offsets:
            center = contact + along * (offset * 25.4)
            bore = cq.Solid.makeCylinder(bore_radius, 38.1, center, inward)
            bores.append(bore)
            holes.append(
                {
                    "member": member,
                    "offset_from_bend_in": offset,
                    "entry_xyz_mm": _round_vector(center),
                    "opposing_face_xyz_mm": _round_vector(center + inward * 38.1),
                    "axis_xyz": _round_vector(inward),
                    "raw_wood_full_bore_fraction": round(
                        solid.intersect(bore).Volume() / (pi * bore_radius**2 * 38.1), 6
                    ),
                }
            )
    counts = {"hillman_panel": 0, "bolt_clearance": 0}
    conflicts = []
    with AXES.open(newline="") as handle:
        for row in csv.DictReader(handle):
            kind = row["shop_opening_kind"]
            if kind not in counts:
                continue
            counts[kind] += 1
            start = cq.Vector(*(float(row[f"start_{axis}_mm"]) for axis in "xyz"))
            direction = cq.Vector(*(float(row[f"direction_{axis}"]) for axis in "xyz"))
            occupied = cq.Solid.makeCylinder(
                float(row["occupied_diameter_mm"]) / 2,
                float(row["occupied_length_mm"]),
                start,
                direction,
            )
            if any(bore.intersect(occupied).Volume() > 1e-6 for bore in bores):
                conflicts.append(row["name"])
    if counts != {"hillman_panel": 66, "bolt_clearance": 12}:
        raise ValueError("Frozen retained-axis inventory changed")
    width_bounds = width_limits[0]
    trial_width = contact.dot(width_direction)
    nearest_broad_edge = min(
        trial_width - width_bounds[0], width_bounds[1] - trial_width
    )
    principal_bounds = width_limits[1]
    principal_nearest_edge = min(
        trial_width - principal_bounds[0], principal_bounds[1] - trial_width
    )
    four_d = 4 * bolt_diameter
    four_d_lower = max(low + four_d - center_width for low, _ in width_limits)
    four_d_upper = min(high - four_d - center_width for _, high in width_limits)
    return {
        "station": name,
        "source_cad": "mini_moonboard.compact_floor_flush_frame.uncut_wood_parts() and stations()",
        "source_axes": str(AXES.relative_to(ROOT)),
        "placement": f"Nominal AB205 bend at rail-end/principal-side contact; {rail_leg} leg along rail, {'short' if rail_leg == 'long' else 'long'} leg along principal",
        "original_contact_xyz_mm": _round_vector(origin),
        "contact_xyz_mm": _round_vector(contact),
        "row_shift_along_width_mm": round(row_shift_mm, 6),
        "width_direction_xyz": _round_vector(width_direction),
        "common_nominal_flange_shift_bounds_mm": [
            round(shift_lower, 6),
            round(shift_upper, 6),
        ],
        "common_conditional_four_d_shift_bounds_mm": [
            round(four_d_lower, 6),
            round(four_d_upper, 6),
        ],
        "rail_direction_xyz": _round_vector(rail_direction),
        "principal_direction_xyz": _round_vector(principal_direction),
        "rail_through_thickness_mm": round(rail_thickness, 6),
        "clear_gap_between_center_principals_mm": round(
            opposite_principal.BoundingBox().xmin - principal.BoundingBox().xmax, 6
        ),
        "rail_broad_face_nearest_edge_mm": round(nearest_broad_edge, 6),
        "rail_broad_face_four_d_edge_reserve_mm": round(nearest_broad_edge - four_d, 6),
        "principal_broad_face_nearest_edge_mm": round(principal_nearest_edge, 6),
        "principal_broad_face_four_d_edge_reserve_mm": round(
            principal_nearest_edge - four_d, 6
        ),
        "factory_flange_width_mm": round(2 * half_flange_width, 6),
        "rail_width_direction_nominal_flange_edge_reserve_mm": round(
            nearest_broad_edge - half_flange_width,
            6,
        ),
        "principal_width_direction_nominal_flange_edge_reserve_mm": round(
            principal_nearest_edge - half_flange_width, 6
        ),
        "bolt_diameter_mm": bolt_diameter,
        "factory_hole_diameter_mm": 2 * bore_radius,
        "holes": holes,
        "retained_axes_inspected": counts,
        "intersecting_retained_axis_ids": conflicts,
        "opposing_flange_and_washer_access_verified": False,
        "complete_bolt_stack_and_withdrawal_verified": False,
        "angle_placement_verified": False,
        "drilling_released": False,
    }
