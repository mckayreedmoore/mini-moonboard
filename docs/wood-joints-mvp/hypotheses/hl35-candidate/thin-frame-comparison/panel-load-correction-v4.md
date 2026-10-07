# Panel load correction and warp applicability diagnostics

The [new saved-field diagnostic](panel-load-correction-a12-rear-finished-floor-v4.json)
quantifies the six panel RHS corrections used by the frozen coupled producer.
The corrections are numerically small in this state. They do not explain the
large conditional head demands or establish first-order applicability. No CAD,
stiffness assembly, contact assembly or response solve occurred; every release
flag remains false. Prior producers and reports remain intact.

The source is the corrected finished-floor A12 rear field, state
`thin-v4-84ad844f63afddc032cf922c`, SHA256
`8d90941f9d1cb20d938ddc65992b2db7b0fe0c38420bf6bfc10fc0684281256d`.
It retains the original top accessory placement, eight panel intervals and all
conditional material, spring, contact, floor and shared-shaft assumptions
recorded in the [coupled panel evidence](panel-coupled-a12-rear-finished-floor-v4.md).
The independent finished-support/arithmetic gate passes.

The [helper](../../../../../scripts/thin_bolted_panel_load_diagnostics.py)
reconstructs only the frozen mass quadrature: unperforated area minus actual
full bores and the tiny kicker bevel. It calls the frozen `panel_case_load`
and compares all six uncorrected load vectors with the authenticated
interval-eight NPZ. It then adds every panel-owned metal gravity port from
the actual state: 208 shares among the assembly's 706 shares. The remaining
498 shares belong to other bodies and are excluded from panel RHS arithmetic.
The exact body loads supply the desired wrench about `(0,750,1100)` mm.

For six rigid-motion coefficient columns `R`, the frozen correction is
`delta_f = R (RᵀR)⁻¹ (desired_wrench − Rᵀ f_uncorrected)`. This is the minimum
Euclidean-norm coefficient load adjustment satisfying the six wrench equations.
Every coefficient displacement is in mm, so generalized load and work are
reported in N and N·mm. Force and moment residuals stay separate; no norm mixes
their units.

| Panel | Force correction norm (N) | Moment correction norm (N·mm) | Correction load norm / corrected load norm | Correction work on actual `q` (N·mm) |
| --- | ---: | ---: | ---: | ---: |
| Main lower left | 4.31348e-8 | 0.0855584 | 1.06759e-6 | 0.00119329 |
| Main lower right | 4.29768e-8 | 0.0944154 | 1.17916e-6 | 0.00033742 |
| Main upper left | 7.91866e-7 | 0.0875542 | 1.22901e-8 | 0.00050359 |
| Main upper right | 8.18247e-8 | 0.0953717 | 2.16399e-7 | 0.00068259 |
| Kicker left | 1.06581e-14 | 0.0266010 | 6.59109e-6 | 0.00252529 |
| Kicker right | 1.42109e-14 | 0.0304468 | 6.65763e-6 | 0.00156002 |

The six force and moment correction vectors, generalized norms, reconstructed
uncorrected/corrected external work, and post-correction closure are retained
in JSON. Their combined correction work is **0.006802208 N·mm**, compared
with saved assembly total potential **−44639.390902 N·mm**. The absolute
ratio is **1.523813e-7**. Removing the corrections at this unchanged `q`
would increase potential by 0.006802208 N·mm. This fixed-field work comparison
does not bound changes in response, contact branch or stability.

A formal affine global traction over the same net mass-area quadrature can
reproduce each exact six-wrench correction. The affine traction's coefficient
load differs from the producer's Euclidean projection; its difference and work
on actual `q` are explicit in JSON. It is an alternative wrench-equivalent
interpretation, and no alternate load is substituted into the solved field.
The maximum sampled alternative traction norm is 1.499e-9 N/mm². This resolves
the arithmetic meaning and magnitude of the RHS adjustment without inventing
an observed physical force distribution or a local load-introduction pass.

Warp diagnostics fit an affine outward displacement field, subtract its two
slopes, and sample the remaining slope at 81 points per axis. The following
`0.5|gradient(warp)|²` values are geometric membrane-strain scales, not an
adopted limit, objective finite-rotation strain or a nonlinear solution.

| Panel | Maximum affine-removed slope norm | Maximum half slope norm squared |
| --- | ---: | ---: |
| Main lower left | 0.00562822 | 1.58385e-5 |
| Main lower right | 0.00585869 | 1.71621e-5 |
| Main upper left | 0.08703406 | 0.00378746 |
| Main upper right | 0.01839432 | 0.00016918 |
| Kicker left | 0.02620191 | 0.00034327 |
| Kicker right | 0.01987570 | 0.00019752 |

At the upper-left maximum slope witness, the simultaneous squared-slope
terms `(epsilon_x, epsilon_upslope, engineering_gamma)` are
`(0.00112628, 0.00266118, 0.00346251)`; the saved first-order membrane
strains at that same point are
`(2.23836e-5, −1.03307e-6, 0.000210437)`. Substantial terms remain after
removing overall affine tilt. A nonlinear plate/frame treatment would need to
update in-plane displacement, material/load directions and contact kinematics;
these markers cannot be added to the original stresses as accepted demands.
Opening boundaries, the kicker bevel tip and hold/seat footprints remain local
resolution limits. This diagnostic supplies no numerical drift criterion or
structural pass/failure.

Four [known-answer tests](../../../../../tests/test_thin_bolted_panel_load_diagnostics.py)
pass: exact bore area/first moments, minimum-norm six-wrench projection,
uniform affine traction force/centroid moment, and centered quadratic warp
slopes/squared-slope terms. Ruff passes. The
[validation receipt](panel-load-correction-validation-v4.json) binds sources,
commands and results. The 38.5 kB result and small receipt stay active with the
saved NPZ/datum dependencies; no archive or prune operation occurred.
