# Simple frame calculation and immediate priorities

The owner stopped the recurring agent review loop on October 1 and requested
a simple model directed toward a working MVP. The current calculation uses
the reviewed `led-clearance-2x6-runner-seated-blocks-v1` geometry. No geometry
or hardware axis has changed.

## What is being evaluated

[simple_frame.py](simple_frame.py) reuses the existing elastic member and
connector reduction. Timber faces and floor support carry compression;
outer bolt ties carry tension. Lateral bolt connections retain the existing
conditional spring stiffnesses. The eight existing floor footprints each
have one resultant compression spring and a no-slip restraint while bearing.
This replaces the detailed floor-cell support calculation with a footprint
mean. It evaluates independent static loads, without contact-history tracking.

Loads retain the six recorded 250 lb, dynamic-factor-2 climber cases and
300 N horizontal forces. Modeled self-weight is 224.42 kg. An additional
25 kg planning accessory allowance is distributed in proportion to modeled
body masses. That distribution is an analytical assumption, not an observed
installation or a worst-placement bound.

All six scenarios pass the stated equilibrium and spring-law checks in
[simple-frame-results.json](simple-frame-results.json). This is a working
approximate calculation model, not six newly authenticated native responses
or complete joint acceptance. Existing source material assumptions, omitted
bore stiffness effects and parametric panel-screw springs remain assumptions.
Local floor pressure and actual friction are not qualified.

The first attempt with individual floor cells converged for the rear cases
and cycled for forward/left/right. Its results are preserved in
[cell-floor-static-results.json](cell-floor-static-results.json). The original
A12 raw-H 27-failure STOP remains unchanged. Export-precision, stress-frame
and washer-mesh method work remain parked.

## What the simple checks show

[bolt_demands.py](bolt_demands.py) exports 648 simultaneous lateral-interface
states for 92 candidate bolts and 12 retained bolts. Axial ties remain
separate from local shear-plane actions. [lateral_reference.py](lateral_reference.py)
applies the existing individual-bolt equations to 76 transverse, two-receiver
candidate axes across all six cases. Twelve end-grain axes and four
continuous three-receiver axes retain explicit separate-method dispositions.

The two top outer corner cleats remain the clearest component concerns:

| Controlling side bolt | Case | Demand/reference with 106 ksi hypothesis |
| --- | --- | ---: |
| Top outer left `side_2` | A12-left | 1.19 |
| Top outer right `side_2` | K12-rear | 1.38 |

The 106 ksi value is the existing Grade 5 Commentary estimate, not a
guaranteed product minimum. References precede group and geometry adjustments.
The preserved upper-block packet already identified the same two top outer
cleats using the authenticated rear cases. The concern therefore merits
targeted joint work under either response method.

[top-corner-size-sensitivity.json](top-corner-size-sensitivity.json) explores
larger diameters at fixed actions. It is a sizing sensitivity only. Larger
bolts consume the existing edge and spacing margins, and would change load
sharing. No bolt size or changed layout is selected by that calculation.

The subsequent [complete top-corner action and section screens](top-corner-checks.md)
now cover 24 interface states and 30 whole-body balances, including every
incident contact/bolt action and recomposed nodal loads. They retain the
20.7–24.4 kN·mm side-pair couples, both-side host shear, two possible
loaded-edge characteristic references and 120 cleat section traces.
The same side-bolt concern remains. Intact-cut beam screens and host-plane
references do not close the actual bore-region splitting or complete-joint
resistance checks.

The [local corner calculations](top-corner-local-checks.md) additionally
retain neighboring bores in 32 shear-plane area queries, with a largest
parallel path component/reference of 0.1954. Rail end/group-factor scenarios
and the 0.5892 maximum ideal washer wood-pressure ratio are now calculated.
These results preserve the side-bolt priority and support a bounded local
correction; complete splitting and washer metal transfer remain distinct.

## What comes first

1. Check each top outer corner as a complete joint: rail-to-cleat-to-side
   force and moment transfer, paired bolt sharing, face bearing, timber
   splitting and finished edge/spacing geometry. Check ordinary hardware and
   access together with any proposed dimensional correction.
2. Use those results to prepare the smallest local correction. Report changed
   members, bores or axes before changing the reviewed model; then rerun this
   same simple frame calculation with the corrected connection assumptions.
3. Extend the basic checks to the remaining connection families and members,
   retained frame bolts and panel load paths. Complete assembly, removal,
   transport and the compatible BOM alongside those checks.

The existing joint owner retains the upper-left **service** cleat. These two
**top outer corner** cleats are a different parent-owned scope. No further
independent agent review round is required by this workflow. All 47 formal
criterion dispositions remain pending and physical release flags remain false.

## Reproduction

The cached numerical environment supplies OSQP 1.0.4, NumPy 2.2.6 and
SciPy 1.15.3 without changing repository dependencies. The numerical method
uses the documented [OSQP convex QP formulation](https://osqp.org/docs/solver/index.html)
and [solver settings](https://osqp.org/docs/interfaces/solver_settings.html).
The small compression/no-slip/tension-refusal oracle runs before the frame.
The frame calculation takes the shared analysis lock; no native ledger row
or native launch is created.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /usr/bin/timeout --signal=KILL 180s \
  uv run --offline --no-project --python 3.12 \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 \
  python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/simple_frame.py
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/bolt_demands.py
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/lateral_reference.py
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top_corner_actions.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /usr/bin/timeout --signal=KILL 60s \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top_corner_local.py
```
