"""Factory connector geometry screens, not steel resistance."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SteelGeometryScreen:
    product: str
    steel_thickness_mm: float
    factory_hole_mm: float | None
    bolt_diameter_mm: float
    diametric_clearance_mm: float | None
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


def screen_a66(
    factory_hole_mm: float | None = None,
    bolt_diameter_mm: float = 9.525,
) -> SteelGeometryScreen:
    """Screen the common-retail A66 bolt option without claiming its capacity.

    The retailer/manufacturer installation references identify 3/8-inch
    structural through bolts. The exact hole diameter and plate resistance
    still need to be confirmed from the delivered part before fabrication.
    """
    if bolt_diameter_mm <= 0 or (factory_hole_mm is not None and factory_hole_mm <= 0):
        raise ValueError("hole and bolt diameters must be positive")
    clearance = None if factory_hole_mm is None else factory_hole_mm - bolt_diameter_mm
    return SteelGeometryScreen(
        "Simpson Strong-Tie A66", 2.5, factory_hole_mm, bolt_diameter_mm,
        clearance,
        "unresolved_factory_hole" if clearance is None else (
            "nominal_fit" if clearance >= 0 else "nominal_fail"
        ),
        "unresolved bolt/plate bearing, net section, angle bending, timber bearing, and access",
    )


def unresolved_limit_states() -> tuple[str, ...]:
    return (
        "factory-hole bearing and net section",
        "angle bending and prying",
        "bolt tensile/lateral resistance and washer bearing",
        "steel/wood load introduction and regional product applicability",
    )
