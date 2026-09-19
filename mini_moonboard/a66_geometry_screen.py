"""Nominal A66 fit screens for the preserved single-2x6 envelope.

These calculations are geometric only. They do not establish A66 steel,
bolt, timber, or combined-joint resistance.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class A66GeometryScreen:
    member_face_mm: float
    member_thickness_mm: float
    flange_width_mm: float
    leg_length_mm: float
    bolt_diameter_mm: float
    wide_face_edge_distance_mm: float
    narrow_face_edge_distance_mm: float
    wide_face_edge_reserve_mm: float
    narrow_face_edge_reserve_mm: float
    leg_overhang_mm: float
    wide_face_status: str
    narrow_face_status: str
    capacity_status: str


def screen_a66_geometry(
    member_face_mm: float = 139.7,
    member_thickness_mm: float = 38.1,
    flange_width_mm: float = 38.1,
    leg_length_mm: float = 149.225,
    bolt_diameter_mm: float = 9.525,
) -> A66GeometryScreen:
    """Screen the best-case centered bolt lines on broad and narrow 2x6 faces.

    The 4d screen measures from bolt center to the timber edge. Actual A66
    hole locations and station orientations must still be established.
    """
    values = (
        member_face_mm,
        member_thickness_mm,
        flange_width_mm,
        leg_length_mm,
        bolt_diameter_mm,
    )
    if any(value <= 0 for value in values):
        raise ValueError("A66 geometry inputs must be positive")
    wide_edge = member_face_mm / 2.0
    narrow_edge = member_thickness_mm / 2.0
    required_edge = 4.0 * bolt_diameter_mm
    return A66GeometryScreen(
        member_face_mm,
        member_thickness_mm,
        flange_width_mm,
        leg_length_mm,
        bolt_diameter_mm,
        wide_edge,
        narrow_edge,
        wide_edge - required_edge,
        narrow_edge - required_edge,
        leg_length_mm - member_face_mm,
        "best_case_screen_pass" if wide_edge >= required_edge else "best_case_screen_fail",
        "best_case_screen_pass" if narrow_edge >= required_edge else "best_case_screen_fail",
        "unresolved_A66_bolt_plate_timber_and_combined_resistance",
    )
