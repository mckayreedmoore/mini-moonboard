"""AB90 steel/hardware applicability screens, not steel resistance."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SteelGeometryScreen:
    product: str
    steel_thickness_mm: float
    factory_hole_mm: float
    bolt_diameter_mm: float
    diametric_clearance_mm: float
    hole_status: str
    resistance_status: str


def screen_ab90(factory_hole_mm: float = 11.0, bolt_diameter_mm: float = 10.0) -> SteelGeometryScreen:
    if factory_hole_mm <= 0 or bolt_diameter_mm <= 0:
        raise ValueError("hole and bolt diameters must be positive")
    clearance = factory_hole_mm - bolt_diameter_mm
    return SteelGeometryScreen(
        "Simpson Strong-Tie AB90", 2.5, factory_hole_mm, bolt_diameter_mm, clearance,
        "nominal_fit" if clearance >= 0 else "nominal_fail",
        "unresolved bolt/plate bearing, net section, tear-out, bending, and prying",
    )


def unresolved_limit_states() -> tuple[str, ...]:
    return (
        "factory-hole bearing and net section",
        "angle bending and prying",
        "bolt tensile/lateral resistance and washer bearing",
        "steel/wood load introduction and regional product applicability",
    )
