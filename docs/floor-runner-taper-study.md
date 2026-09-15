# Tapered floor-runner recess

`compact-floor-taper-development` preserves the two full 2×6 outboard runners,
complete kicker panels and twelve bolt stacks of the square-recess trial.
The full 38.1 mm recess clears the runner before a 457.2 mm runout along grain
returns the leg to its full 88.9 mm thickness. The taper is 1:12; the remaining
foot thickness is 50.8 mm. No shoulder bearing or composite action is credited.

**All six current native cases meet all 35 implemented conditional criteria.**

**September 14 completion review: additional method and contact checks remain
open.** The passing count does not resolve whether the support-notch method
and uniform-section shear comparison adequately cover this side-width taper,
or whether omitted runner/leg contact affects the load path. The current notch
factor is 1.0 in both legs in all six cases, and native clearance-monitor and
member-contact lists are empty. These require specific justification or corrected
checks before asserting completion. See the
[completion plan](tapered-runner-completion-plan.md).
These are finite-case comparisons under the assumptions below, not an unconditional
climber rating or a change to the selected design.

| Case | Bolt lateral ratio | Sampled net-member ratio | Listed criteria |
| --- | ---: | ---: | ---: |
| a12-rear | 0.857639 | 0.607636 | 35/35 |
| a12-left | 0.919498 | 0.630641 | 35/35 |
| a12-forward | 0.928189 | 0.482039 | 35/35 |
| k12-right | 0.907366 | 0.618939 | 35/35 |
| k12-rear | 0.848580 | 0.595162 | 35/35 |
| a1-rear | 0.127127 | 0.188559 | 35/35 |

Evidence: `fea/results/clear-space-floortaper/<case>/` contains the native report,
geometry, assessment, authenticated source archive and saved search controller.
The listed criteria use the specified nominal-diameter hardware basis. Separate
full-root sensitivities fail five cases, reaching 1.168023 with actual directional
Ktheta and 1.263432 with fixed Ktheta = 1.25. Neither is an adopted acceptance
criterion; actual shank and thread coverage must satisfy the hardware requirements.
Passing the listed criteria does not mean all sensitivities pass.
Each case has its own converged native response; mirrored or preceding-case
floor states were search seeds only.

The selected exterior candidate and its six passing cases remain unchanged.
See [the square-recess trial](floor-runner-recess-study.md) for the preceding
unqualified sharp corner. Its forces do not qualify this changed geometry.

The comparison retains actual axial/biaxial net-section checks and adds a
separate notch-reduced shear and rectangular torsion comparison. The published
1:10 taper condition permits disregarding certain axial/bending notch stress
concentrations; it does not waive shear checks. The implementation applies an
EC5 geometric notch reduction to the existing DF-L ASD shear reference as an
explicit conditional comparison, not a claim of EC5 certification. Lower
bolt-hole regions retain the separate connection/net-section checks; the
unbored rectangular torsion comparison does not qualify local bore stresses.

References: [Swedish Wood, notch method](https://www.swedishwood.com/siteassets/5-publikationer/pdfer/glulamhandbook2-240508.pdf),
[Stora Enso, axial/bending versus shear requirements](https://www.storaenso.com/-/media/documents/download-center/documents/product-specifications/wood-products/lvl-technical/stora-enso-lvl-holes-and-notches---2023.pdf),
and [Mississippi State, rectangular torsion](https://www.ae.msstate.edu/tupas/SA2/chA6.4_text.html).

The model retains the six-case 250 lb doubled-downward load inquiry, 300 N
horizontal actions, stated equipment allowance and per-cell Coulomb floor
scenario at assumed μ = 0.4. Floor friction is unmeasured; no cyclic slip or
unconditional climber rating is established. Only this candidate's own native
reports, actual geometry and resulting assessments can change its status.

Use the [hardware requirements](floor-runner-taper-hardware.md) and matching
`clear-space-floortaper-construction` profiles together. The 1:12 removal profile
is measured along grain, not vertically. Preserve all other bevels and bores.
The artificial full-height 50.8 mm band diagnostic is not the actual leg shape.
