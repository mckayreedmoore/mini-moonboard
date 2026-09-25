# Conditional bolt-to-nut thread engagement method

Status: response-method proposal for the WJ04 local patch, 2026-09-24. It
defines a conditional axial load path for the current partial-thread 1/4-20
candidate. It is not an accepted connector law, solved response, resistance,
or hardware qualification.

## Current gate and proposed representation

The prepared contact fragment has a continuous bolt solid, a separate hollow
nut solid, and a frictionless radial contact pair between a projected bolt
root cylinder and the nut's basic-reference bore. That pair can prevent radial
penetration after it closes; it cannot carry axial bolt tension. The fragment
correctly leaves axial thread engagement unbound. `ThreadConstraint` in the
[rigid-mode diagnostic](../../fea/wood_joint_patch_rigid_modes.py) is a
caller-declared kinematic rank row only. It adds no force law, compliance,
capacity, or evidence that the thread is engaged.

For an axial response diagnostic without a helical solid mesh, use one
source-bound, one-dimensional axial connector per physical bolt, between the
bolt and nut. Its force law must come from a separate thread-engagement coupon
or a directly applicable test for the same thread form, size, class, nut,
engagement length, and material scenario. Do not assign its stiffness from
nominal diameter, `E A/L`, the nut's catalog grade, the wood stack, or the
radial contact penalty. No eligible force-displacement curve or test is in the
current evidence, so the proposed connector has no numeric law yet and the
physical thread response remains `UNRESOLVED_AXIAL_ENGAGEMENT`. A thread
coupon is not a prerequisite for every conditional diagnostic: the separate
[WJ24 bottom-center sensitivity method](thread-engagement-sensitivity-options.md)
defines parametric spring and zero-slack/no-slip diagnostic branches using an
elastic bolt and a finite rigid nut. That route is specific to its three-wood,
four-stack WJ24 patch; none of its assumed intervals, parameter values, or
results transfer to this WJ04 patch. A WJ04 stiff-limit route would need its
own source-bound input and one-time connector/member check. Neither sensitivity
is a finite delivered-thread law or product-specific result. A finite physical
engagement stiffness still needs a matched coupon or other directly applicable
source/test/model evidence.

Keep the spring endpoints on the bolt axis at the centroids of the finite
engagement regions, clipped to the **measured full-form thread overlap** inside
the nut. Transfer each spring resultant to its owning solid through a named
finite patch using a non-rigid distributing load map. Do not kinematically
rigidize that patch. The spring acts only along the bolt axis and returns equal
and opposite axial force to bolt and nut. It adds no transverse force,
torsional resistance, bending couple, friction, or clamp force. Keep the
existing root-to-bore radial contact separately; it can carry radial normal
force only after its declared clearance closes. If any signed case requires
thread torque, radial thread bearing, or a nut-tilt couple, this scalar axial
reduction does not represent that case and a different explicit method is
required.

Use CalculiX `SPRINGA` / `*SPRING` only after its two-node force direction,
force-displacement sign, and nonlinear force curve have passed the small
coupon below. A nonlinear spring curve may include an initial axial deadband
only when its value is supported by the matched thread fit; do not copy radial
root clearance into that deadband. Use separate positive and negative axial
branches where the two thread flanks or assembly slack differ. No preload is
present in the current patch, so the initial force is zero. The spring's
calibration span must represent only engagement compliance absent from the
explicit bolt and nut solids. Exclude shank stretch, washer-seat compression,
and timber compression already carried by the larger solids, or those terms
will be counted twice. CalculiX documents spring elements as force-versus-
elongation relations and documents distributing versus kinematic surface
coupling as distinct formulations; the pinned [2.21 manual](../../fea/generated/connection/ccx_2.21.pdf)
is archived with SHA-256
`16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8` (see
`*SPRING`, `*COUPLING`, `*DISTRIBUTING`, `*KINEMATIC`, and `*TIE`).

## Why a surface tie is not the engagement law

CalculiX `*TIE` imposes displacement compatibility over tied surfaces. It
does not resolve thread flanks, the screw lead, root clearance, one-sided
flank bearing, or the thread's axial compliance. A radial-cylinder tie across
the root-to-bore gap would suppress radial clearance while also bonding
tangential motion and axial separation across the whole cylindrical area. An
adjusted tie would additionally close the initial gap. Neither operation
models a thread. The existing WJ16 adapter investigation also found that a
conventional unadjusted tie across its radial gap fails the required rigid
rotation invariance; see the [readiness record](native-adapter-readiness.md).

Do not substitute a full-surface `*COUPLING,*KINEMATIC` or an axial
`*EQUATION`/MPC. A kinematic surface coupling makes the coupled patch move as a
rigid region. A directional MPC is an equality row, not a finite stiffness or
contact law. Either can be useful in a deliberately labeled kinematic or
rank-only diagnostic, but neither is the proposed bolt/nut response model.
The [CalculiX 2.21 manual](../../fea/generated/connection/ccx_2.21.pdf)
defines the different constraint and spring cards; the final implementation
must also pass the coupon with the pinned 2.21 executable.

## Candidate geometry and conditional inputs

The current hardware profile is a dimensional candidate, not a receipt
record. It identifies an external 1/4-20 UNC Class 2A thread on K.L. Jack
`25C600HCS5Z` and an internal 1/4-20 UNC Class 2B thread on
`25CNFH5Z`; the [manufacturer product records](https://www.kljack.com/products/25c600hcs5z/)
and [nut record](https://www.kljack.com/products/25cnfh5z/) state those
designations. The [ASME B1.1-2024 record](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
defines Unified thread form, series, class, allowance, tolerance, and
designation. These sources do not authenticate the delivered fastener lot or
its measured engagement.

The hardware inventory currently carries only basic reference thread sizes:
0.1887 in (4.79298 mm) external minor diameter and 0.1959 in (4.97586 mm)
internal minor diameter for 1/4-20 UNC. The archived source is NBS Circular
No. 479, Table 2, printed page 21, from the
[primary NBS publication](https://www.govinfo.gov/content/pkg/GOVPUB-C13-2edad299c8f39c5cc9909c067728f932/pdf/GOVPUB-C13-2edad299c8f39c5cc9909c067728f932.pdf);
the checked excerpt and PDF hash are in the [local hardware inventory](hypotheses/wj04-mechanics-hardware/README.md).
Those basic diameters are neither class limits nor production tolerances. Do
not use them as verified root or bore sizes, or as a manufacturing acceptance
window. A thread-profile coupon must bind the applicable B1.1 limits or
measured delivered profiles, not just the two basic minor diameters.

Keep the bolt partially threaded. For the 6 in candidate, the current source
states `Lb = 127.0 mm` as minimum body length to the **last thread scratch**
and `Lg = 133.35 mm` as maximum grip-gaging length; neither locates the first
full-form thread on the delivered part. The actual first full-form thread,
runout, and end condition are unmeasured. Use the current full-length smooth
body and root-diameter sensitivity only as separately named geometric
scenarios. Neither makes the candidate thread start or the assumed full nut
engagement true. The [hardware basis](ordinary-hardware-basis.md) and
[WJ04 full-stock thread screen](hypotheses/wj04-full-stock-thread-screen/README.md)
retain the receiving measurements required to establish full-form thread
through the nut. If the delivered thread does not cover the nut's active
thickness, the part fails the [WJ04 full-height engagement receiving
condition](ordinary-hardware-basis.md). A separate conditional response
diagnostic may represent only the measured full-form overlap when an
applicable law supports that partial length; it does not pass the receiving
condition. Otherwise leave the physical axial path unresolved.

The elastic steel card in
[`steel_material.py`](../../fea/wood_joint_patch_steel_material.py) is a
generic proposal (`E = 200,000 MPa`, `ν = 0.30`, with declared numerical
sensitivities), not a measured property of either fastener. A connector curve
derived using that card is an assumed-material response scenario. It cannot
produce thread-strip, bolt-yield, nut-proof, or complete-joint resistance.

## Smallest useful numerical coupon

Before attaching a spring to the five-body patch, prepare one one-bolt/one-nut
axial coupon. The simple geometric reference is an axisymmetric section with
non-helical, annular 1/4-20 thread flanks across the measured engagement
length. Use the exact external/internal class or measured profile, actual
partial-thread transition, the actual nut thickness, explicit flank/root
clearances, and frictionless unilateral flank contact. The annular profile is
a declared zero-lead surrogate: it lets finite solid deformation and flank
normal pressure carry axial force without tying the two bodies. It does not
model the thread helix, circumferential force, nut rotation, friction, or
torque and can change how load shares among turns. Do not assume that its
stiffness is conservative. If the pinned CalculiX contact formulation cannot
represent the axisymmetric coupon reliably, use a short 3-D segment of the
same annular profile, still without a helix.

Apply a predeclared small axial displacement at remote end sections, fixing
only the nut's remote axial datum and the minimum radial/rigid modes needed by
the chosen formulation. Start with zero preload and the documented thread
clearance. Run tension and reverse axial polarity from the same initial state;
record any backlash travel before flank contact. For two successive mesh
refinements and changed numerical contact penalties, compare the force versus
relative axial displacement across the engagement region, integrated flank
force, total reaction balance, contact state, and elastic energy. The coupon
must show that axial force enters through the named flank surfaces and that
the contact resultant equals the applied/reaction force. A zero-load
convergence or solver rank row is not this check.

Extract the engagement-only force-displacement curve after removing the
elastic extension of any shaft or remote nut material that the full patch
already models. Fit only the range actually demonstrated by the coupon. Then
run a separate two-reference-node spring check with that curve: verify force
sign in both directions, net action/reaction, axial work, and invariance to
mesh refinement and distributing-patch size. If a curve fit changes materially
with the annular-profile mesh, thread-clearance scenario, or steel-property
scenario, keep the spring response unresolved instead of choosing a favorable
fit.

This coupon establishes numerical implementation of the declared
zero-lead, frictionless elastic surrogate only. It cannot establish delivered
thread fit, bolt/nut strength, thread stripping, loosening, installation torque,
preload, service resistance, or a physical connection stiffness. A measured
matched fastener/nut axial test or a justified higher-fidelity comparison is
needed before the connector curve can stand for delivered hardware. Even
then, the coupon does not qualify the timber joint.

## Required patch result record

For each physical bolt, bind the connector to the fastener ID, source geometry
hashes, axis, reference points, finite distribution patches, signed force
law, curve provenance, calibration range, thread designation/class,
full-form engagement length, initial axial slack, and steel material scenario
hash. Export the axial connector force separately from radial root/nut
contact, shaft/wood bearing, and washer-seat forces. Check equal and opposite
connector forces and shift the force to the interface datum for moment
accounting. Preserve any axisymmetric-surrogate, mesh, penalty, or clearance
failures. Do not report zero bolt force when a tensile case fails to reach an
active thread flank, and do not reinterpret rank or solver convergence as
thread acceptance.

Until the matched curve, patch-to-reference mapping, and signed coupon checks
are source-bound, physical axial thread transfer remains
`UNRESOLVED_AXIAL_ENGAGEMENT`. Axial cases cannot be reported as accepted
physical stiffness or as passing constraints. The separately named no-slip
branch may be run only as `STIFF_LIMIT_SENSITIVITY_ONLY`; it does not close
that status.
