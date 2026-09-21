# PB02 compatibility-aware stiffness sensitivity

The active PB02 point topology has a compatible one-sided spring solution in
all 50 authenticated historical-action sensitivities. No trial requires a
singular-refinement traversal. The result also exposes strong dependence on
the deliberately unqualified relative stiffnesses: one fixed-case contact
result changes by a factor of about 122. This is a development warning, not a
qualified stiffness, current PB02 design demand, strength result, or
fabrication release.

The [reproducible script](../../scripts/simple_center_stiffness_sensitivity.py)
uses the same fingerprinted ten-bore geometry and actual CAD-face contact
cells as the signed equilibrium fixture. It preserves all five accepted
historical right-center action examples and their exact header opposites.
`a12-forward` remains missing.

## Compatibility and one-sided laws

The model has 20 bilateral bolt-shear rows, ten no-preload tension-only bolt
rows, and 28 compression-only exact-face tributary contact rows. Generalized rotations use the
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
bolt-dominant and contact-dominant contrasts. Every contact spring uses one
common areal density. The selected mean interface total calibrates that density,
so unequal net face areas intentionally produce unequal interface totals.

A tenth scenario uses 3,086.746 N/mm for lateral bolt slip from the recorded
`rho_mean^1.5 d / 23` analogy with assumed 500 kg/m³ density and the active
6.35 mm trial diameter. Density, clearance, service state, axial stiffness,
washer-seat behavior, and applicability are unverified. Neither this analogy
nor the 1,000/10,000/100,000 levels are qualified PB02 inputs.

## Results

All 50 combinations converge with maximum whole-system residual below
0.000000024 N and 0.000004 N·mm after exact refinement. None records a singular
refinement advance.

The following ranges span different old-action cases as well as sensitivity
scenarios. They are cross-case diagnostic reaction envelopes, not measures of
fixed-load stiffness sensitivity, design demands, or capacities.

| Edge | Max one shear component, N | Total tension, N | Contact compression, N |
| --- | ---: | ---: | ---: |
| post–post block | 174–1,496 | 1,413–5,294 | 1,768–6,132 |
| post block–header | 858–2,919 | 497–3,925 | 22–3,385 |
| header–principal block | 125–1,136 | 1,821–11,167 | 1,673–10,136 |
| principal block–principal | 148–1,030 | 578–5,222 | 955–5,905 |
| principal–upright block | 91–658 | 0–2,170 | 81–2,980 |
| upright–rear block | 113–1,197 | 0–1,875 | 82–1,934 |
| rear block–post | 185–2,807 | 139–1,993 | 78–1,759 |

Within one fixed `a12-left` historical case, `block_header` contact compression
ranges from 22.195 N to 2,708.889 N, a maximum/minimum ratio of 122.047. This
means the current local loop does not support a stiffness-insensitive force
claim over the deliberately broad trial range. The cross-case table also mixes
different historical loads and must not be read as a fixed-load ratio. These
conditional compatible responses do not establish qualified stiffness or a
design demand.

Next work must derive or bound the actual bolt lateral, bolt axial, and
washer/contact stiffnesses from frozen stack geometry and applicable sources,
then run the complete selected topology including the missing forward case.
Bolt/wood resistance, pressure, clearance, preload, splitting, group action,
and whole-frame response remain separate. Do not purchase, cut, or drill from
this sensitivity.
