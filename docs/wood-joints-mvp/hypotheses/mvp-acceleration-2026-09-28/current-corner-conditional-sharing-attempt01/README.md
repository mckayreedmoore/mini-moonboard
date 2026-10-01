# Complete corner: conditional simultaneous sharing

This parent-scoped calculation uses all five corner members, eight bolt shear
planes, six outer-seat ties and seven bearing pairs. It calculates simultaneous
actions under 48 balanced **imposed local probes**, not the six climber cases.
It preserves geometry and native budgets. No C11 force/active state is reused,
no floor anchor is introduced and no original leg/runner resistance is reopened.

The probes apply ±1 N forces or ±1 N·m couples to each of four corner members
(spine, side, inner block, header), with equal/opposite actions on the post
at common datum `(-1219.2,-137.6,192.475) mm`. Full member wrenches include
the required moment translations to each reporting datum. Setting the post's
six displacement coordinates to zero removes common rigid motion; its
prescribed balancing actions remain in every per-member equilibrium check.
This is a local mathematical reference, not a candidate floor support.

The model uses existing frozen spring coefficients, rigid members, zero
preload/gaps, independent two-plane BG003 lateral springs and four contact
centroids per bearing pair. It excludes actual member flexure, bolt clearance,
continuous-shaft bending, washer bending, actual seat/contact conditions and
outward frame/panel/floor carriers. Its contact sampling is deliberately the
frozen coarse abstraction; earlier BG001 refinement demonstrates its possible
bias. These results are not adopted joint demands or strength envelopes.
Do not superpose the 48 separate unit responses to obtain a combined case:
unilateral engagement can change with the simultaneous wrench. A supplied
frame-case boundary action must be solved as one balanced combined action
under the applicable compatibility scenario and checked on all five members.
No load-factor scaling across a changed active state is established here.

## Result and displacement limitation

**All 48 imposed probes** satisfy equilibrium, the original spring laws,
unilateral force signs and two-start force agreement. Signed actions and both
compatible displacement witnesses are in
[conditional-corner-energy.json](conditional-corner-energy.json).
Independent physical-point cross-product recovery checks all five members;
maximum force/moment residual is 6.54e-9 N or N·mm. Maximum constitutive
force error is 1.22e-9 N and start-to-start force difference is 7.55e-12 N.
These checks do not establish physical applicability or joint stability.

The negative-X spine probe formerly excluded for a 1.883 N constitutive
mismatch is now resolved as a **conditional force result**. Equality-multiplier
recovery supplied an incompatible displacement at one start, although its
QP forces balanced. A separate linear feasibility recovery finds a witness
for the original laws without changing any force. Both starts now meet the
unchanged balance, force-sign and spring-law tolerances. They produce 0.5 N
in each BG001 axial tie, with the other actions zero to numerical precision.
An independent analytic witness translates all four non-post bodies equally
in X by `-0.5/4670.054188 mm`, keeping rotations zero: the two post ties
stretch, post/spine contact opens and the other internal carriers have zero
relative displacement. This matches the computed forces and full-body balance.

The two numerical displacement witnesses differ by up to 0.00194336 mm in
scaled displacement coordinates (rotation coordinates are 100 mm times
radians), so this probe is explicitly marked as having different compatible
displacements. Positive stiffness makes complementary energy strictly convex
in carrier forces, giving a unique feasible minimizing force vector;
zero-force unilateral carriers can leave displacement freedom. Accordingly,
the force-reporting guard compares forces and verifies each displacement's
original spring law, rather than requiring displacement uniqueness. It does
not weaken equilibrium, constitutive or unilateral tolerances. This is not
a stability finding. The prior 47-closed multiplier-only output is preserved
in [conditional-corner-energy-multiplier-only.json](conditional-corner-energy-multiplier-only.json).

An example shows why simultaneous transfer matters. For an imposed +1 N·m
header My and opposite post couple, axial actions occur in all three groups:

| New physical bolt | Conditional axial action (N) |
| --- | ---: |
| BG001 post 1 | 19.815 |
| BG001 post 2 | 0.040 |
| BG003 side 1 | 4.694 |
| BG003 side 2 | 6.599 |
| BG045 inner/header 1 | 4.609 |
| BG045 inner/header 2 | 2.473 |

These are actions for that declared unit probe only; they are not capacities
and must not be summed as a joint strength. The JSON also retains all lateral
plane and bearing actions, including the direct header/post, header/side and
header/spine routes. A one-way bolt chain would omit part of this response.

## Method and validation boundary

The initial direct equilibrium-residual trial stalled on inactive branches
and closed none of the 48 probes. Its rejected diagnostics remain in
[conditional-corner.json](conditional-corner.json); none is adopted. Its
equations were `A.T @ k*g_active - w_free` with the piecewise stiffness
Jacobian, SciPy `least_squares` TRF, two seed-20260929 starts of amplitude
1e-5 in 24 coordinates, 200 evaluations and 1e-12 stopping tolerances.
Residual minimization can stop without equilibrium; the guard correctly
excluded every output.

The replacement uses minimum complementary spring energy
`sum(f_i²/(2 k_i))`, subject to `B_free f = -w_free` and nonnegative axial-tie
and contact actions. Bilateral lateral actions are signed. Positive-definite
energy removes algebraic force-sharing freedom if the constraint set is
feasible, under this idealization. Cholesky row scaling normalizes the linear
constraints without changing them. [SciPy SLSQP documentation](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)
describes the existing optimizer and returned equality multipliers; optimizer
success alone is not acceptance. The code first recovers displacement from those
multipliers and checks the spring law as well as all-body balance. Where that
law check fails, [SciPy HiGHS linear-program documentation](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html)
supports a bounded recovery of a compatible witness: positive-force unilateral
and all bilateral carriers impose `A_i u = -f_i/k_i`; zero-force unilateral
carriers impose `A_i u >= 0`. All coordinates have explicitly free bounds.
The recovery changes no forces. Its active classification threshold is 1e-8 N,
linear feasibility tolerances are 1e-10, and the final original spring-law
check still uses every raw force with the unchanged 1e-5 N tolerance. Full
physical equilibrium tolerance is 1e-6 N or N·mm, unilateral force tolerance
1e-10 N, and two-start force tolerance 1e-5 N. Optimizer success alone is never
acceptance. An additional known-answer fixture with a free inactive coordinate
checks this recovery before the coupled cases.

Before the coupled probes, independent opposing unilateral-spring known
answers pass: stiffnesses 2/3, external +10 yields actions 0/10 and displacement
10/3; external −9 yields actions 9/0 and displacement −4.5. The coupled run
uses two starts and a 200-iteration bound per start. A focused independent
Luna/max review confirmed contact/tie signs, energy duality and the post gauge.
Its bounded follow-up confirmed that force agreement plus each witness's
original spring law and full equilibrium is the appropriate conditional-force
criterion; displacement uniqueness is not implied. These are mathematical
reviews, not engineering acceptance. Parent reproduction and independent
physical-wrench, both-witness law and analytic-translation checks pass.

The exact engineering result gained is a reproducible signed **conditional
complete-corner** response for all 48 declared probes. Still required for
actual case checks: simultaneous source-bound frame/corner boundary actions;
applicable member, contact and seat compliance; pressure/clearance/three-member
shaft treatment; and applicable timber, washer, bolt/nut and engagement
resistance checks. Global floor, receiver sharing and member-response gates
remain explicit. No criterion or fabrication disposition changes.

Reproduce:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-conditional-sharing-attempt01/produce.py --verify
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-conditional-sharing-attempt01/check_closure.py
```

Both authoritative input hashes are embedded and checked before calculation.
No native solver, mesh, CAD regeneration or full-frame response is executed.
