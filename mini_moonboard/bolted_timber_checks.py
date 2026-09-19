"""Timber geometry screens for the AB90 prototype.

These are fit/edge-envelope checks, not NDS resistance calculations. Capacity
and species/grain applicability remain unresolved until an applicable design
basis is selected.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class TimberGeometryScreen:
    receiver_face_mm: float
    receiver_thickness_mm: float
    bolt_diameter_mm: float
    edge_distance_mm: float
    end_distance_mm: float
    edge_4d_reserve_mm: float
    end_7d_reserve_mm: float
    geometry_status: str
    capacity_status: str


def screen_geometry(
    receiver_face_mm: float,
    receiver_thickness_mm: float,
    bolt_diameter_mm: float,
    edge_distance_mm: float,
    end_distance_mm: float,
) -> TimberGeometryScreen:
    values = (receiver_face_mm, receiver_thickness_mm, bolt_diameter_mm, edge_distance_mm, end_distance_mm)
    if any(value <= 0 for value in values):
        raise ValueError("timber geometry inputs must be positive")
    edge_reserve = edge_distance_mm - 4.0 * bolt_diameter_mm
    end_reserve = end_distance_mm - 7.0 * bolt_diameter_mm
    return TimberGeometryScreen(
        receiver_face_mm, receiver_thickness_mm, bolt_diameter_mm, edge_distance_mm, end_distance_mm,
        edge_reserve, end_reserve,
        "nominal_pass" if min(edge_reserve, end_reserve) >= 0 else "nominal_fail",
        "unresolved_applicable_timber_resistance",
    )


def unresolved_limit_states() -> tuple[str, ...]:
    return (
        "dowel bearing and fastener bending",
        "splitting, row/block failure, and net section",
        "grain-angle and existing-bore interaction",
        "axial bolt bearing and local wood fracture",
    )


def dfl_dowel_bearing_psi(diameter_in: float, load_angle_degrees: float) -> float:
    """Return only the solid DF-L dowel-bearing input from NDS 12.3.3–12.3.4.

    This is not a bolt or joint design value. G=0.50 is the NDS-assigned DF-L
    value; the large-dowel reference strengths are rounded to 50 psi before
    angle-to-grain interpolation. End-grain and panel cases are excluded.
    """
    if not math.isfinite(diameter_in) or diameter_in < 0.25:
        raise ValueError("solid-wood large-dowel diameter must be at least 1/4 inch")
    if not math.isfinite(load_angle_degrees) or not 0 <= load_angle_degrees <= 90:
        raise ValueError("load angle to grain must be between 0 and 90 degrees")

    specific_gravity = 0.50
    parallel_psi = round(11200 * specific_gravity / 50) * 50
    perpendicular_psi = round(
        6100 * specific_gravity**1.45 / math.sqrt(diameter_in) / 50
    ) * 50
    angle_radians = math.radians(load_angle_degrees)
    sine_squared = math.sin(angle_radians) ** 2
    cosine_squared = math.cos(angle_radians) ** 2
    return (parallel_psi * perpendicular_psi /
            (parallel_psi * sine_squared + perpendicular_psi * cosine_squared))
