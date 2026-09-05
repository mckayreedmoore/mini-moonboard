"""Auditable sagittal rigid-body screen; not a contact or compliance model."""
import math
from dataclasses import dataclass

from .model import (
    ANGLE_FROM_VERTICAL_DEG,
    PANEL_THICKNESS_MM,
    V1_PANEL_SIZE_MM,
    build_v1_concept,
    v1_support_side_point,
)
from .panel_grid import MAIN_ROWS, main_tnut_datums

SCREENING_DENSITY_KG_M3 = 600.0
UNROPED_CLIMBER_LOAD_N = 1200.0
GRAVITY_MM_S2 = 9806.65
OVERTURNING_TARGET = 1.5


@dataclass(frozen=True)
class LoadCase:
    name: str
    basis: str
    force_y_n: float
    force_z_n: float


def load_cases() -> tuple[LoadCase, ...]:
    a = math.radians(ANGLE_FROM_VERTICAL_DEG)
    return (
        LoadCase("Downward 1.2 kN", "gravity-direction baseline", 0, -1200),
        LoadCase("Downward 2.4 kN", "2x magnitude sensitivity; not a prescribed dynamic load", 0, -2400),
        LoadCase("Downward + outward 0.3 kN", "illustrative horizontal sensitivity", 300, -1200),
        LoadCase("Downward + inward 0.3 kN", "illustrative horizontal sensitivity", -300, -1200),
        LoadCase("Outward/downward normal", "exploratory legacy direction", 1200*math.cos(a), -1200*math.sin(a)),
        LoadCase("Inward/upward normal", "exploratory legacy direction", -1200*math.cos(a), 1200*math.sin(a)),
    )


@dataclass(frozen=True)
class StabilityCase:
    load: LoadCase
    kicker_reaction_n: float
    leg_reaction_n: float
    overturning_factor: float
    friction_required: float | None

    @property
    def status(self) -> str:
        if min(self.kicker_reaction_n, self.leg_reaction_n) < 0:
            return "UPLIFT"
        return "MARGIN BELOW 1.5" if self.overturning_factor < OVERTURNING_TARGET else "MEETS 2D MARGIN ONLY"


def evaluate_load(*, mass_kg: float, centre_y_mm: float, kicker_toe_y_mm: float,
                  leg_toe_y_mm: float, load_y_mm: float, load_z_mm: float,
                  load: LoadCase) -> StabilityCase:
    """Exact two-toe equilibrium. +Y faces climber; +Z is up.

    Moment margin = dead restoring moment / destabilizing net moment of this
    ONE live-force resultant, at each toe. Stabilizing live moments earn no
    added restoring credit. No second climber or separate ballast load.
    Friction is the aggregate Coulomb demand, only with both contacts loaded.
    """
    values = (mass_kg, centre_y_mm, kicker_toe_y_mm, leg_toe_y_mm, load_y_mm, load_z_mm,
              load.force_y_n, load.force_z_n)
    if not all(math.isfinite(v) for v in values) or mass_kg <= 0 or load_z_mm < 0:
        raise ValueError("finite inputs, positive mass and nonnegative load height required")
    a, b, c = kicker_toe_y_mm, leg_toe_y_mm, centre_y_mm
    if not a < c < b:
        raise ValueError("centroid must lie strictly between ordered support toes")
    w = mass_kg * GRAVITY_MM_S2 / 1000
    fy, fz = load.force_y_n, load.force_z_n
    ma = (load_y_mm-a)*fz-load_z_mm*fy
    mb = (load_y_mm-b)*fz-load_z_mm*fy
    rb = (w*(c-a)-ma)/(b-a)
    ra = w-fz-rb
    margins = [restoring/demand if demand > 0 else math.inf
               for restoring, demand in ((w*(c-a), ma), (w*(b-c), -mb))]
    mu = abs(fy)/(w-fz) if min(ra, rb) >= 0 and w-fz > 0 else None
    return StabilityCase(load, ra, rb, min(margins), mu)


@dataclass(frozen=True)
class StabilityScreen:
    mass_kg: float
    centre_y_mm: float
    kicker_toe_y_mm: float
    leg_toe_y_mm: float
    load_y_mm: float
    load_z_mm: float
    cases: tuple[StabilityCase, ...]

    def at(self, load: LoadCase, y: float, z: float) -> StabilityCase:
        return evaluate_load(mass_kg=self.mass_kg, centre_y_mm=self.centre_y_mm,
                             kicker_toe_y_mm=self.kicker_toe_y_mm, leg_toe_y_mm=self.leg_toe_y_mm,
                             load_y_mm=y, load_z_mm=z, load=load)


def row_point(row: int) -> tuple[float, float]:
    return v1_support_side_point(main_tnut_datums()[f"F{row}"][1], -PANEL_THICKNESS_MM)


def v1_stability_screen(density_kg_m3: float = SCREENING_DENSITY_KG_M3) -> StabilityScreen:
    if not math.isfinite(density_kg_m3) or density_kg_m3 <= 0:
        raise ValueError("density must be positive and finite")
    shapes = [child.toCompound() for child in build_v1_concept().children]
    volume = sum(s.Volume() for s in shapes)
    mass = volume/1e9*density_kg_m3
    centre = sum(s.Volume()*s.centerOfMass(s).y for s in shapes)/volume
    faces = [f for s in shapes for f in s.Faces()
             if abs(f.BoundingBox().zmin) < 1e-5 and abs(f.BoundingBox().zmax) < 1e-5]
    a = min(f.BoundingBox().ymin for f in faces)
    b = max(f.BoundingBox().ymax for f in faces)
    y, z = row_point(12)
    cases = tuple(evaluate_load(mass_kg=mass, centre_y_mm=centre, kicker_toe_y_mm=a,
                               leg_toe_y_mm=b, load_y_mm=y, load_z_mm=z, load=load) for load in load_cases())
    return StabilityScreen(mass, centre, a, b, y, z, cases)


def render_v1_stability_screen() -> str:
    s = v1_stability_screen()
    def row(case):
        factor = f"{case.overturning_factor:.2f}" if math.isfinite(case.overturning_factor) else "no overturning demand"
        mu = f"{case.friction_required:.3f}" if case.friction_required is not None else "not applicable: uplift"
        return f"| {case.load.name} | {case.kicker_reaction_n:.0f} | {case.leg_reaction_n:.0f} | {factor} | {mu} | {case.status} |"
    rows = "\n".join(row(c) for c in s.cases)
    vectors = "\n".join(f"| {c.name} | {c.force_y_n:.1f} | {c.force_z_n:.1f} | {c.basis} |" for c in load_cases())
    sweep = []
    for load in load_cases():
        governing = min(((r, s.at(load, *row_point(r))) for r in MAIN_ROWS), key=lambda pair: pair[1].overturning_factor)
        sweep.append(f"| {load.name} | {governing[0]} | {governing[1].status} |")
    edge = "\n".join(row(s.at(load, *v1_support_side_point(2*V1_PANEL_SIZE_MM, -PANEL_THICKNESS_MM))) for load in load_cases()[-2:])
    return f"""# V1 unanchored stability: load-basis audit

Generated from unchanged CAD. This is a sagittal (Y/Z) rigid-body sensitivity
screen, **not structural approval or a complete standards check**.

## Basis and coordinates

- Timber-only CAD mass: {s.mass_kg:.1f} kg at assumed uniform 600 kg/m³;
  centroid Y={s.centre_y_mm:.1f} mm. Holds, steel, glue and LEDs are omitted.
- Kicker-side extreme floor toe: Y={s.kicker_toe_y_mm:.1f} mm;
  leg-side extreme floor toe: Y={s.leg_toe_y_mm:.1f} mm. These are floor-face
  extrema, not foot centrelines. +Y points toward the climber; +Z is upward.
  The old report's front/rear reaction headings were misleading and are retired.
- Actual row 12 bolt centre projected onto the climbing face:
  Y={s.load_y_mm:.1f}, Z={s.load_z_mm:.1f} mm; board-local S=2280 mm.
  Hold projection and distributed hand/foot contacts are not yet included.
- The [CWA specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf)
  Table 1 supplies 1.2 kN for an unroped climber. Sections 4.5–4.7 discuss
  stability and a minimum 1.5 overturning factor, but do not prescribe our
  opposite board-normal vectors. Scope/applicability and load combinations
  need qualified review; this is not a claim of CWA compliance.

## Separate baseline and exploratory vectors

| Case | Force Y N | Force Z N | Classification |
| --- | ---: | ---: | --- |
{vectors}

The 2x and ±300 N cases are illustrative sensitivities, not measured dynamic
loads or new design requirements. No arbitrary inward/upward force is treated
as a proven governing use case. Nor is any exploratory failure discarded.

## Row 12 results

| Case | Kicker reaction N | Leg reaction N | Overturning factor | Required friction coefficient | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
{rows}

Negative reaction means contact would have to pull on the floor: uplift.
Factor is the minimum, over both toes, of dead-weight restoring moment divided
by destabilizing net moment from the single live-force resultant. Stabilizing
live moments add no restoring credit. The 1.5 target is a screening margin;
it does not implement all governing code load combinations.

Required friction is |Fy|/(weight-Fz), assuming a common Coulomb coefficient
and compressive support reactions. It has **no sliding safety factor** built
in. At a chosen sliding target of 1.5, measured/design friction would need
to be at least 1.5 times this demand; that target is illustrative, not a
prescribed CWA sliding factor. No actual floor coefficient is assumed, so
sliding remains unverified. No friction pass is reported after uplift.

## Check every main-panel row

All 12 main rows are evaluated; columns share Y/Z only in this sagittal model.
Listed row has the lowest moment margin (first row if tied).

| Case | Governing row | Outcome |
| --- | ---: | --- |
{chr(10).join(sweep)}

## Historical top-edge comparison (not row 12)

The previous code loaded S=2438.4 mm, incorrectly called top row. For continuity:

| Case | Kicker reaction N | Leg reaction N | Overturning factor | Required friction coefficient | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
{edge}

## Decision

Read baseline and exploratory outcomes separately: the current baseline does
not reproduce the earlier blanket failure. Do not size ballast from the old
345.6 kg threshold. Establish a justified dynamic force envelope and measured
mass/centre of mass before selecting a footprint change. The reference video
is geometry evidence, not a load rating or proof of absent restraints.

Unresolved: dynamic force/time histories, hold stand-off and hand/foot force
distribution, kicker loads, off-centre lateral/3D overturning, sliding/contact,
directional plywood properties, actual joints and buckling. The fixed-floor
bulk FEA remains a separate stiffness experiment, not evidence of stability.
"""
