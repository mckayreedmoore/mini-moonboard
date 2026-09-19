"""Timber geometry screens for the AB90 prototype.

These are fit/edge-envelope checks, not NDS resistance calculations. Capacity
and species/grain applicability remain unresolved until an applicable design
basis is selected.
"""

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
