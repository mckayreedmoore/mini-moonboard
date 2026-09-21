# PB02 compatibility-aware stiffness sensitivity

The active PB02 point topology has a compatible one-sided spring solution in
all 50 authenticated historical-action sensitivities. Two bolt-dominant,
contact-soft trials encounter a singular intermediate active set; the solver
advances along its null direction until another unilateral row activates and
then continues to a converged solution. Those intermediate states are not
proven physical mechanisms. The result does not provide qualified stiffness,
current PB02 design demand, strength, or fabrication release.

The [reproducible script](../../scripts/simple_center_stiffness_sensitivity.py)
uses the same fingerprinted ten-bore geometry and actual CAD-face contact
samples as the signed equilibrium fixture. It preserves all five accepted
historical right-center action examples and their exact header opposites.
`a12-forward` remains missing.

## Compatibility and one-sided laws

The model has 20 bilateral bolt-shear rows, ten no-preload tension-only bolt
rows, and 28 compression-only contact rows. Generalized rotations use the
existing 100 mm work-conjugate scale. Fixing the post's six coordinates is
only a rigid-body gauge: each input is first required to be self-equilibrated,
and the final reaction solution must balance all 42 coordinates, including
the omitted post equations.

For relative displacement `g`, signed reaction `r`, and trial stiffness
`k`:

- bolt shear uses `r = −k g`;
- bolt axial action uses `r = −k max(g, 0)`; and
- face contact uses `r = −k min(g, 0)`.

A convex energy minimization seeds the active set. An exact 36-coordinate
linear refinement then has to satisfy every one-sided law and close force and
moment equilibrium. If an intermediate active tangent is singular, refinement
advances along its energy-reducing null direction to the next unilateral-row
activation and resumes. The seed optimizer's stopping flag is not used as
acceptance; the exact constitutive and equilibrium checks govern.

## Inputs are sensitivities, not properties

The nine principal scenarios use an already exercised numerical reference of
10,000 N/mm and factors 0.1, 1, and 10. They independently vary lateral bolt,
axial bolt, and total face-contact stiffness, including opposite
bolt-dominant and contact-dominant contrasts. Total face stiffness is divided
among four samples so contact sampling density does not multiply the face
law.

A tenth scenario uses 3,086.746 N/mm for lateral bolt slip from the recorded
`rho_mean^1.5 d / 23` analogy with assumed 500 kg/m³ density and the active
6.35 mm trial diameter. Density, clearance, service state, axial stiffness,
washer-seat behavior, and applicability are unverified. Neither this analogy
nor the 1,000/10,000/100,000 levels are qualified PB02 inputs.

## Results

All 50 combinations converge with maximum whole-system residual below
0.000001 N and 0.00002 N·mm after exact refinement. The bolt-dominant contrast
passes through a singular intermediate active set for `a12-left` and
`k12-rear`; null-direction advance reaches the next unilateral activation and
the final compatible solution. A singular intermediate set alone does not
establish a physical mechanism.

The following ranges span different old-action cases as well as sensitivity
scenarios. They are cross-case diagnostic reaction envelopes, not measures of
fixed-load stiffness sensitivity, design demands, or capacities.

| Edge | Max one shear component, N | Total tension, N | Contact compression, N |
| --- | ---: | ---: | ---: |
| post–post block | 1,118–4,974 | 6,813–23,069 | 6,859–22,820 |
| post block–header | 1,928–5,680 | 1,452–7,610 | 1,229–7,523 |
| header–principal block | 101–887 | 48–424 | 0 |
| principal block–principal | 101–887 | 55–398 | 51–162 |
| principal–upright block | 228–748 | 849–4,352 | 843–4,074 |
| upright–rear block | 34–278 | 855–4,390 | 1,083–5,139 |
| rear block–post | 17–908 | 1,955–8,527 | 1,727–7,779 |

Within each fixed historical case, post-block tension is essentially invariant
across the deliberately unqualified stiffness scenarios. The largest
fixed-case ratio is about 1.47868 for principal-block–principal tension in
`a12-rear` (about 54.78–80.996 N). Larger spreads in the table above result
from mixing different historical load cases with different stiffness
scenarios; they are not stiffness sensitivity. These conditional compatible
responses still do not establish qualified stiffness or a design demand.

Next work must derive or bound the actual bolt lateral, bolt axial, and
washer/contact stiffnesses from frozen stack geometry and applicable sources,
then run the complete selected topology including the missing forward case.
Bolt/wood resistance, pressure, clearance, preload, splitting, group action,
and whole-frame response remain separate. Do not purchase, cut, or drill from
this sensitivity.
