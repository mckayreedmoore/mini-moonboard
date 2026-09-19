"""Timber geometry and conditional DF-L reference-input screens.

The reference calculations are not complete NDS connections or capacity
approvals. They require actual hole layouts, load directions and adjustments.
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
        "actual group tear-out geometry, splitting, and changed member net section",
        "actual grain/load orientation and existing-bore interaction",
        "actual washer contact, axial bolt loading, and local wood fracture",
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


def dfl_net_parallel_tension_reference_lbf(
    thickness_in: float, width_in: float, bore_diameters_in: tuple[float, ...]
) -> float:
    """NDS-2024 Appendix E.2 dry DF-L No.2 net tension, not joint capacity.

    Bores must be distinct openings on one critical cross section. The caller
    owns section selection, neighboring cuts, grain/load and adjustments.
    """
    if (not math.isfinite(thickness_in) or thickness_in <= 0 or
            not math.isfinite(width_in) or width_in <= 0 or not bore_diameters_in or
            any(not math.isfinite(bore) or bore <= 0 for bore in bore_diameters_in)):
        raise ValueError("net-section dimensions and bores must be positive and finite")
    net_width_in = width_in - math.fsum(bore_diameters_in)
    if net_width_in <= 0:
        raise ValueError("bores leave no net member width")
    return 575.0 * thickness_in * net_width_in


def dfl_parallel_row_tear_out_reference_lbf(
    thickness_in: float, bolt_count: int, end_distance_in: float,
    pitch_in: float | None = None,
) -> float:
    """NDS-2024 Appendix E.3 one-row dry DF-L No.2 reference, not joint capacity.

    The actual force must act parallel to grain toward the end. This does not
    check minimum end/bolt spacing, group action, splitting or adjustments.
    """
    if (not math.isfinite(thickness_in) or thickness_in <= 0 or
            not isinstance(bolt_count, int) or isinstance(bolt_count, bool) or
            bolt_count < 1 or not math.isfinite(end_distance_in) or
            end_distance_in <= 0):
        raise ValueError("row geometry must have positive finite dimensions and bolt count")
    if bolt_count > 1 and (pitch_in is None or not math.isfinite(pitch_in) or pitch_in <= 0):
        raise ValueError("multiple bolts require a positive finite row pitch")
    if bolt_count == 1 and pitch_in is not None:
        raise ValueError("single-bolt row has no pitch")
    critical_spacing_in = min(end_distance_in, pitch_in) if pitch_in else end_distance_in
    return 180.0 * bolt_count * thickness_in * critical_spacing_in


def dfl_parallel_group_tear_out_reference_lbf(
    first_boundary_row_lbf: float, last_boundary_row_lbf: float,
    net_group_area_in2: float,
) -> float:
    """NDS-2024 Appendix E.4 dry DF-L No.2 two-boundary reference only.

    Caller must select the critical connected group area and obtain each
    actual bounding row value. No force sharing or group action is implied.
    """
    values = (first_boundary_row_lbf, last_boundary_row_lbf, net_group_area_in2)
    if (any(not math.isfinite(value) for value in values) or
            first_boundary_row_lbf <= 0 or last_boundary_row_lbf <= 0 or
            net_group_area_in2 < 0):
        raise ValueError("group tear-out inputs must be finite and nonnegative")
    return (first_boundary_row_lbf + last_boundary_row_lbf) / 2 + 575.0 * net_group_area_in2


def dfl_axial_wood_bearing_reference_lbf(
    washer_outer_diameter_in: float, wood_bore_diameter_in: float,
    washer_inner_diameter_in: float,
) -> float:
    """Dry DF-L No.2 ideal full-contact Fc-perp washer annulus, not bolt load.

    The full washer footprint must actually fit sound wood and be stiff enough
    to distribute load. This omits preload, Cb increases and service factors.
    """
    values = (washer_outer_diameter_in, wood_bore_diameter_in, washer_inner_diameter_in)
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("washer and bore diameters must be positive and finite")
    unsupported_diameter_in = max(wood_bore_diameter_in, washer_inner_diameter_in)
    if washer_outer_diameter_in <= unsupported_diameter_in:
        raise ValueError("washer leaves no wood-contact annulus")
    annular_area_in2 = math.pi / 4 * (
        washer_outer_diameter_in**2 - unsupported_diameter_in**2
    )
    return 625.0 * annular_area_in2
