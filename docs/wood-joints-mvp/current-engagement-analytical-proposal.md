# Current WJ24 thread-engagement analytical proposal

**Prepared:** 2026-09-25. **Status:** conditional model-form proposal; no
hardware or physical engagement acceptance. This note addresses the current
WJ24 nominal 6.35 mm (1/4 in), 1/4-20 comparison geometry. It does not import
the older WJ04 K.L. Jack product or its measured/assumed thread details.

## Finding

A finite *post-seating elastic tangent scenario* can be calculated at the
current nominal size without requiring a paper test at every diameter.
Matsubara and Teranishi's published component model gives the thread-engagement
spring as `K_th = A_s E_b / L_th`, with `L_th = 0.85 d`. Substituting the
nominal Unified tensile stress area for `A_s`, the WJ24 nominal diameter, and
the project's generic `E = 200,000 MPa` reference gives
`K_th = 760.709 kN/mm` (compliance `0.00131456 mm/kN`). The exact inputs and
the declared `E` sensitivity points are recorded in the
[calculation artifact](hypotheses/current-engagement-analytical-attempt01/README.md)
and its [machine-readable calculation](hypotheses/current-engagement-analytical-attempt01/calculation.json).

This is a source-derived engineering scenario, not a validated 1/4-20
bolt/matched-nut constitutive law, a conservative bound, or a whole-joint
stiffness. The paper applies a JIS stress-area form to M12 bolts and compares
the *combined timber-joint tightening stiffness* against tests; it does not
isolate the engagement component or validate the `0.85 d` component for
Unified 1/4-20. ASME B1.1 defines Unified geometry and fit classes, not
engagement compliance. The formula makes a nominal-size calculation
well-defined; it does not prove transfer accuracy at this thread size or fit.

## How to use the number

If the mechanics model needs one named finite diagnostic, use this value only
as `ANALYTICAL_POST_SEATING_TANGENT_SCENARIO`, with the steel-modulus values
`180,000`, `200,000`, and `220,000 MPa` retained as analyst sensitivity
points. These points are the existing generic-material perturbations, not
physical material bounds. Use one engagement element per represented
bolt/nut stack only where the engaged-thread deformation is otherwise omitted.
The source places this component in series with the bolt's thread-play,
cylindrical, and head components. Do not add it in parallel with an explicit
thread/contact zone or double-count a bolt segment already represented by the
element model. If the nut stays as a deformable explicit body while its thread
engagement is condensed to one connector, define which nut/interface
deformation the connector replaces before using the model.

Interpret the value as a local axial tangent after a thread flank has seated
and while that same contact branch remains engaged. The ideal zero-slack
linearization is a useful labeled comparison case; it is not the initial
condition of an unpreloaded real fastener. The paper reports an initial
low-force slip region before its nearly linear “snag point,” but gives no
thread-fit backlash value. Its `L_s` “thread play” term is the free threaded
bolt length in the series extension model, not flank-to-flank backlash or nut
clearance. WJ24 has no selected external/internal thread classes, measured
thread profiles, delivered full-form overlap, or installed fit from which to
calculate the seating travel. Preserve the free-travel branch as unresolved;
do not assign a convenient gap or convert the tangent into a zero-preload
physical path.

The stiffness equation supplies no tensile proof, bolt yield, internal or
external thread stripping, pullout, or nut-proof capacity. `A_s` is a stress
area used in tensile-strength calculations, not a capacity or a measured
elastic contact area. Thread resistance needs separate strength/material
classes, actual full-form engagement and profile limits, and an applicable
thread-strength calculation. Do not report force capacity by multiplying this
stiffness by an assumed displacement.

## Next implementable output

Register the calculated point as a sensitivity-only scenario at the current
WJ24 1/4-20 nominal geometry, preserving the status
`UNRESOLVED_AXIAL_ENGAGEMENT` for physical stacks. Keep it separate from the
infinite-stiffness branch and any analyst-selected ratio sweep. Before
connecting it to a signed physical response, bind the current patch source
hashes and define the exact bolt/nut generalized coordinates, active-flank
direction, element-versus-connector compliance partition, and contact-force
recovery. In a distinct input record, resolve the actual class/fit and full
thread overlap from applicable standard limits plus the selected product or
receiving evidence. If the later physical claim needs a finite pre-seating
curve that the standard-bounded model does not supply, then obtain an
applicable matched test or validate an explicit profile/contact model; this is
not a blanket requirement for creating or using the present analytical
sensitivity scenario.

Sources and applicability detail are in the [bounded calculation artifact](hypotheses/current-engagement-analytical-attempt01/README.md).
