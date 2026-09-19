"""Nominal AB205 geometry at one actual narrow/opposing station; no approval."""

import csv
from math import pi
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
) -> dict[str, object]:
    """Place the nominal bend at the raw-CAD rail/principal contact."""
    if rail_leg not in ("long", "short"):
        raise ValueError("Rail AB205 leg must be long or short")
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
            center = origin + along * (offset * 25.4)
            bore = cq.Solid.makeCylinder(bore_radius, 38.1, center, inward)
            bores.append(bore)
            holes.append(
                {
                    "member": member,
                    "offset_from_bend_in": offset,
                    "entry_xyz_mm": _round_vector(center),
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
    width_bounds = [vertex.Center().dot(width_direction) for vertex in rail.Vertices()]
    center_width = origin.dot(width_direction)
    half_flange_width = 1.625 * 25.4 / 2
    nearest_broad_edge = min(
        center_width - min(width_bounds), max(width_bounds) - center_width
    )
    return {
        "station": name,
        "source_cad": "mini_moonboard.compact_floor_flush_frame.uncut_wood_parts() and stations()",
        "source_axes": str(AXES.relative_to(ROOT)),
        "placement": f"Nominal AB205 bend at rail-end/principal-side contact; {rail_leg} leg along rail, {'short' if rail_leg == 'long' else 'long'} leg along principal",
        "contact_xyz_mm": _round_vector(origin),
        "rail_direction_xyz": _round_vector(rail_direction),
        "principal_direction_xyz": _round_vector(principal_direction),
        "rail_through_thickness_mm": round(rail_thickness, 6),
        "clear_gap_between_center_principals_mm": round(
            opposite_principal.BoundingBox().xmin - principal.BoundingBox().xmax, 6
        ),
        "rail_broad_face_nearest_edge_mm": round(nearest_broad_edge, 6),
        "rail_broad_face_four_d_edge_reserve_mm": round(
            nearest_broad_edge - 4 * bolt_diameter, 6
        ),
        "factory_flange_width_mm": round(2 * half_flange_width, 6),
        "rail_width_direction_nominal_flange_edge_reserve_mm": round(
            nearest_broad_edge - half_flange_width,
            6,
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
