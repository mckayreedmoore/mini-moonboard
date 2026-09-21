# PB02 compatibility-aware stiffness sensitivity

The active PB02 point topology has a compatible one-sided spring solution in
48 of 50 authenticated historical-action sensitivities. Two bolt-dominant,
contact-soft trials expose a rank-35 relative mechanism and remain unresolved.
The result does not provide qualified stiffness, current PB02 design demand,
strength, or fabrication release.

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
linear refinement then has to retain full rank, satisfy every one-sided law,
and close force and moment equilibrium. The seed optimizer's stopping flag is
not used as acceptance; the exact constitutive and equilibrium checks govern.

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

All 48 converged combinations have maximum whole-system residual below
0.000001 N and 0.00001 N·mm after exact refinement. The bolt-dominant contrast
has a rank-35 active tangent for `a12-left` and `k12-rear`; those cases are
preserved as unresolved rather than assigned reactions.

The following ranges span all converged old-action cases and sensitivity
scenarios. They are diagnostic reactions, not design demands or capacities.

| Edge | Max one shear component, N | Total tension, N | Contact compression, N |
| --- | ---: | ---: | ---: |
| post–post block | 1,118–4,974 | 6,813–23,069 | 6,859–22,820 |
| post block–header | 1,928–5,680 | 1,452–7,610 | 1,229–7,523 |
| header–principal block | 101–887 | 48–424 | 0 |
| principal block–principal | 101–887 | 55–398 | 51–162 |
| principal–upright block | 228–748 | 849–4,352 | 843–4,074 |
| upright–rear block | 34–278 | 855–4,390 | 1,083–5,139 |
| rear block–post | 17–908 | 1,955–8,527 | 1,727–7,779 |

The post-block tension range changes by more than 3× across these deliberately
unqualified inputs. The center therefore cannot be force-sized from one
arbitrary stiffness choice. The mechanism in two contrast trials also means
the earlier equilibrium-feasibility result is not enough to establish a
compatible response.

Next work must derive or bound the actual bolt lateral, bolt axial, and
washer/contact stiffnesses from frozen stack geometry and applicable sources,
then run the complete selected topology including the missing forward case.
Bolt/wood resistance, pressure, clearance, preload, splitting, group action,
and whole-frame response remain separate. Do not purchase, cut, or drill from
this sensitivity.
