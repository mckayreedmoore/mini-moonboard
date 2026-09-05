# V1 unanchored stability: load-basis audit

Generated from unchanged CAD. This is a sagittal (Y/Z) rigid-body sensitivity
screen, **not structural approval or a complete standards check**.

## Basis and coordinates

- Timber-only CAD mass: 188.6 kg at assumed uniform 600 kg/m³;
  centroid Y=715.3 mm. Holds, steel, glue and LEDs are omitted.
- Kicker-side extreme floor toe: Y=-265.3 mm;
  leg-side extreme floor toe: Y=1399.8 mm. These are floor-face
  extrema, not foot centrelines. +Y points toward the climber; +Z is upward.
  The old report's front/rear reaction headings were misleading and are retired.
- Actual row 12 bolt centre projected onto the climbing face:
  Y=1447.6, Z=1971.6 mm; board-local S=2280 mm.
  Hold projection and distributed hand/foot contacts are not yet included.
- The [CWA specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf)
  Table 1 supplies 1.2 kN for an unroped climber. Sections 4.5–4.7 discuss
  stability and a minimum 1.5 overturning factor, but do not prescribe our
  opposite board-normal vectors. Scope/applicability and load combinations
  need qualified review; this is not a claim of CWA compliance.

## Separate baseline and exploratory vectors

| Case | Force Y N | Force Z N | Classification |
| --- | ---: | ---: | --- |
| Downward 1.2 kN | 0.0 | -1200.0 | gravity-direction baseline |
| Downward 2.4 kN | 0.0 | -2400.0 | 2x magnitude sensitivity; not a prescribed dynamic load |
| Downward + outward 0.3 kN | 300.0 | -1200.0 | illustrative horizontal sensitivity |
| Downward + inward 0.3 kN | -300.0 | -1200.0 | illustrative horizontal sensitivity |
| Outward/downward normal | 919.3 | -771.3 | exploratory legacy direction |
| Inward/upward normal | -919.3 | 771.3 | exploratory legacy direction |

The 2x and ±300 N cases are illustrative sensitivities, not measured dynamic
loads or new design requirements. No arbitrary inward/upward force is treated
as a proven governing use case. Nor is any exploratory failure discarded.

## Row 12 results

| Case | Kicker reaction N | Leg reaction N | Overturning factor | Required friction coefficient | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| Downward 1.2 kN | 726 | 2324 | 22.08 | 0.000 | MEETS 2D MARGIN ONLY |
| Downward 2.4 kN | 691 | 3558 | 11.04 | 0.000 | MEETS 2D MARGIN ONLY |
| Downward + outward 0.3 kN | 371 | 2679 | 1.95 | 0.098 | MEETS 2D MARGIN ONLY |
| Downward + inward 0.3 kN | 1081 | 1968 | no overturning demand | 0.098 | MEETS 2D MARGIN ONLY |
| Outward/downward normal | -350 | 2971 | 0.68 | not applicable: uplift | UPLIFT |
| Inward/upward normal | 1871 | -793 | 0.58 | not applicable: uplift | UPLIFT |

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
| Downward 1.2 kN | 12 | MEETS 2D MARGIN ONLY |
| Downward 2.4 kN | 12 | MEETS 2D MARGIN ONLY |
| Downward + outward 0.3 kN | 12 | MEETS 2D MARGIN ONLY |
| Downward + inward 0.3 kN | 1 | MEETS 2D MARGIN ONLY |
| Outward/downward normal | 12 | UPLIFT |
| Inward/upward normal | 12 | UPLIFT |

## Historical top-edge comparison (not row 12)

The previous code loaded S=2438.4 mm, incorrectly called top row. For continuity:

| Case | Kicker reaction N | Leg reaction N | Overturning factor | Required friction coefficient | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| Outward/downward normal | -464 | 3085 | 0.62 | not applicable: uplift | UPLIFT |
| Inward/upward normal | 1985 | -907 | 0.55 | not applicable: uplift | UPLIFT |

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
