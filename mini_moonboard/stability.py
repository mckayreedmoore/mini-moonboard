"""Rigid-body unanchored stability screen for the V1 CAD assembly.

This is deliberately separate from FEA: fixing the feet in a linear solver
would hide an uplift mechanism. It is a pre-FEA check, not structural approval.
"""

import math
from dataclasses import dataclass

from .model import (
    ANGLE_FROM_VERTICAL_DEG,
    PANEL_THICKNESS_MM,
    V1_PANEL_SIZE_MM,
    build_v1_concept,
    v1_leg_geometry,
    v1_support_side_point,
)

GRAVITY_MM_S2 = 9_806.65
SCREENING_DENSITY_KG_M3 = 600.0
UNROPED_CLIMBER_LOAD_N = 1_200.0


@dataclass(frozen=True)
class StabilityCase:
    """Vertical floor reactions under one 1.2 kN normal load at the top row."""

    direction: str
    front_reaction_n: float
    rear_reaction_n: float
    minimum_weight_n: float


@dataclass(frozen=True)
class StabilityScreen:
    """CAD-derived mass properties and two opposite normal-load reactions."""

    mass_kg: float
    centre_y_mm: float
    front_toe_y_mm: float
    rear_toe_y_mm: float
    load_y_mm: float
    load_z_mm: float
    cases: tuple[StabilityCase, StabilityCase]


def render_v1_stability_screen() -> str:
    """Render the reproducible pre-FEA stability result for the current CAD."""
    screen = v1_stability_screen()
    rows = "\n".join(
        f"| {case.direction} | {case.front_reaction_n:.0f} | {case.rear_reaction_n:.0f} | {case.minimum_weight_n / 9.80665:.1f} |"
        for case in screen.cases
    )
    worst_mass = max(case.minimum_weight_n / 9.80665 for case in screen.cases)
    return f"""# V1 unanchored stability screen

This is a rigid-body **pre-FEA** screen generated from the current CAD
assembly. It is not structural approval and it does not replace a contact,
connection, or material model. Its purpose is to prevent a fixed-foot FEA from
hiding an unanchored uplift mechanism.

## Declared screen inputs

- CAD volume is assigned a provisional uniform density of
  {SCREENING_DENSITY_KG_M3:.0f} kg/m³; this produces {screen.mass_kg:.1f} kg total
  mass. The purchased C-3 birch stock has no verified structural density or
  grade in this project, so this is a sensitivity input, not a material claim.
- Dead weight acts at the CAD volume centroid, Y={screen.centre_y_mm:.1f} mm.
- The floor support interval is the kicker forward edge at
  Y={screen.front_toe_y_mm:.1f} mm through the rear leg floor centreline at
  Y={screen.rear_toe_y_mm:.1f} mm.
- The source-backed 1.2 kN unroped-climber force is applied at the top-row
  climbing-face point Y={screen.load_y_mm:.1f}, Z={screen.load_z_mm:.1f} mm in
  both opposite board-normal directions. A negative reaction is uplift and is
  impossible without an anchor.

| Load direction | Front floor reaction N | Rear floor reaction N | Minimum total dead mass kg |
| --- | ---: | ---: | ---: |
{rows}

## Result

The current unanchored footprint fails this screen in **both** normal
directions: one floor contact has negative reaction in each case. The governing
direction needs at least {worst_mass:.1f} kg of total dead mass at the current
centre of mass, versus the screened {screen.mass_kg:.1f} kg. Treat that
{worst_mass - screen.mass_kg:.1f} kg difference as a warning, not a ballast
prescription: moving the feet/base can be much more effective than adding mass.

Do not continue to a fixed-foot FEA as evidence of unanchored stability. First
revise and model the base footprint/ballast strategy and the kicker-to-main
load path; then solve contact, sliding, and overturning with the reviewer-set
floor friction and material data.
"""


def v1_stability_screen(density_kg_m3: float = SCREENING_DENSITY_KG_M3) -> StabilityScreen:
    """Return reactions for both normal directions without crediting anchors.

    The front toe is the forward edge of the floor-bearing kicker and the rear
    toe is the CAD lower-leg floor centreline. A negative reaction means that
    contact must pull on the floor: an unanchored board would lift/tip.
    """
    if density_kg_m3 <= 0:
        raise ValueError("density_kg_m3 must be positive")
    volume_mm3 = 0.0
    first_y_moment = 0.0
    for child in build_v1_concept().children:
        shape = child.toCompound()
        volume = shape.Volume()
        volume_mm3 += volume
        first_y_moment += volume * shape.centerOfMass(shape).y
    mass_kg = volume_mm3 / 1_000_000_000 * density_kg_m3
    centre_y = first_y_moment / volume_mm3
    front_toe, rear_toe = -PANEL_THICKNESS_MM, v1_leg_geometry()["foot_y"]
    load_y, load_z = v1_support_side_point(2 * V1_PANEL_SIZE_MM, -PANEL_THICKNESS_MM)
    weight_n = mass_kg * GRAVITY_MM_S2 / 1_000
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)

    def reactions(direction: int, label: str) -> StabilityCase:
        force_y = direction * UNROPED_CLIMBER_LOAD_N * math.cos(angle)
        force_z = -direction * UNROPED_CLIMBER_LOAD_N * math.sin(angle)
        span = rear_toe - front_toe
        load_moment = (load_y - front_toe) * force_z - load_z * force_y
        rear = (weight_n * (centre_y - front_toe) - load_moment) / span
        front = weight_n - force_z - rear
        rear_weight = max(0.0, load_moment / (centre_y - front_toe))
        front_weight = max(0.0, (force_z - load_moment / span) * span / (rear_toe - centre_y))
        return StabilityCase(label, front, rear, max(rear_weight, front_weight))

    return StabilityScreen(
        mass_kg,
        centre_y,
        front_toe,
        rear_toe,
        load_y,
        load_z,
        (reactions(1, "normal +Y / -Z"), reactions(-1, "normal -Y / +Z")),
    )
