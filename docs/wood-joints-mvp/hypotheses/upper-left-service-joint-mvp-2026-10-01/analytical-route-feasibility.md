# Upper-left service joint analytical-route feasibility

**Disposition: HOLD. No simple, defensible classical calculation presently
closes this complete joint.** This is a bounded feasibility finding for
`left_service_outer_upper_cleat` on the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` geometry. It changes no geometry,
criterion, or release status.

The frozen [joint packet](README.md) retains 84 same-state bolt actions and
21 complete cleat-boundary wrenches across the four axes, both receivers, and
16 ports. Its 33.808 N lateral and 57.210 N tension peaks occur at different
bolt states. The proposed 100 N lateral / 150 N tension per-bolt box is not an
adopted action contract and does not bound moments or prying. The peak
1.913 N·m quantity is a receiver-datum moment; it is not bolt bending moment.
The source histories also remain three rear cases, not a complete frame
envelope.

Existing calculations are useful component references, but none supplies
the local transfer needed to combine them. The six-mode wood/wood lateral
calculation depends on hypothetical quarter-inch `Fyb` and an unadopted
resistance budget. Ideal washer-annulus pressure is an average over assumed
area, not a seat-pressure field. The same-root bolt axial/shear ratio omits
bolt bending, head/nut bearing, and thread stripping. These boundaries are
documented in the [upper-block local-stress note](../upper-block-strength-2026-10-01/local-stresses.md),
[hardware applicability note](../upper-block-strength-2026-10-01/hardware.md),
and [washer-method investigation](../corner-washer-method-investigation-2026-10-01/source-note.md).

A bolt-group equilibrium sketch is insufficient here. The rail and side
interfaces are two orthogonal two-bolt groups on one cleat. Their concurrent
forces, receiver moments, eccentric bearing, and unilateral face contact make
the internal bolt forces and contact patches compatibility-dependent. The
existing receiver actions authenticate equilibrium of the source model, but
do not determine those internal forces, bolt moments, or wood tractions. The
generic annular-plate helper assumes uniform pressure and both radii clamped;
it is not the washer/head-or-nut/wood boundary condition. The available
parallel-grain Appendix E checks and the EC5 splitting route do not establish
mixed-grain splitting for the shared cleat under both orthogonal groups. The
[outer-host splitting note](../upper-outer-load-path-2026-10-01/splitting.md)
is a limited host-member route for different receiver paths. Its host-specific
calculation cannot be presumed for the service receivers without remapping
their finished geometry and actions, and it expressly leaves combined cleat
interaction open. Finally,
the diagnostic connector laws provide no adopted joint slip or rotational
stiffness. Geometric tool-route clearance does not supply that stiffness.

The smallest useful next step is a **conditional compatibility analysis** of
the existing joint:

1. Freeze a local duty contract as simultaneous signed six-component
   wrenches at the rail/cleat and side/cleat cut datums, with the applicable
   load factors and material/service assumptions. It may be explicitly
   limited to a declared local scenario; the 100/150 N box alone is not enough.
   Set the required slip and rotation bounds from the frame compatibility
   demand.
2. With the pinned cleat/host geometry and specified bolt, nut, washer, and
   seat contact geometry, solve equilibrium **and compatibility** for the
   two groups together. Use no friction or preload credit unless separately
   supported, and represent unilateral contact, actual bearing footprints,
   clearance, and finite member/fastener compliance. A source-backed
   analytical component model could do this; a native solve is not a blanket
   prerequisite, but no verified transfer model is currently bound to this
   joint. The method must return same-state force and moment at each
   bolt, seat-pressure/contact resultants, and joint slip/rotation. Validate
   its load-transfer and contact response against known-answer cases before
   using it for this cleat.
3. Check those outputs against applicable timber bearing, finished-section,
   bolt, head/nut, washer, and splitting resistances. For the quarter-inch
   dowel-yield route, a claim of test-derived NDS `Fyb` needs applicable
   F1575/F606 evidence; the 92 ksi J429 tensile-yield value is not itself
   NDS `Fyb`. An explicitly assumed minimum `Fyb` or washer yield may define
   a hypothetical material contract, with conformance unobserved. The washer
   lead has no published yield minimum. Those assumptions do not resolve
   the missing transfer calculation. Splitting requires a method that covers each
   actual host path and the shared cleat's orthogonal-group interaction; two
   independent host or single-group capacities cannot be added to qualify
   the cleat.

The minimum inputs to resume are therefore: (a) the signed simultaneous
interface-wrench contract and allowable slip/rotation; (b) a computable
load-transfer/compliance method with explicit contact, clearance, and
fastener geometry that resolves internal actions; (c) explicit
material strength and resistance scenarios, plus matched head/nut bearing
and engagement geometry; and (d) an applicable criterion for the finished
cleat and host splitting paths under the resolved oblique actions. If no
published splitting rule covers the two-group cleat, that specific gap needs
a validated applicable analytical model or representative resistance
evidence; generic external sign-off is not a substitute or a blanket
prerequisite. The existing DF-L No. 2, dry, normal-temperature specification
and declared 6 in / 8 in partial-thread profile targets can remain explicit
conditional material and procurement requirements. They are not delivery
observations and do not supply the missing transfer model or its applicability.
Conditional material specifications remain distinct from test-derived or
catalog-qualified resistance claims and the full 47-criterion authority.

Until those inputs exist, no defensible utilization can include local
washer/head/nut stress, coupled bolt bending, timber splitting, or slip and
rotation. Preserve the packet's HOLD and all current geometry. The separate
four-axis [tool-access register](../evaluation-resume-2026-09-24/current-fit-transport-closeout-attempt02/evidence-register.json)
reports 24/24 component geometry routes clear with no hits. Root rejoined
all twelve raw manifest/access/coverage records for these four axes and
verified their file and canonical record hashes; the register SHA-256 is
`dbfe1049d01f936bb034531699ff333d07916240c367851239fb665c1b4f17dc`.
Turning,
counterhold, and physical access remain unestablished. This geometry result
does not supply mechanical slip/rotation.

The primary's separate fixed-60-second KILL coupon launcher preserves stock
runner `ff7a81…` and shares its ledger. The
[source receipt](../mvp-integration-2026-10-01/sti17-hard-stop-source-parent-validation.json)
records 20 tests / 42 subtests and Ruff passing. A tiny Python control fixture
that ignores TERM was also killed in the old pinned base image. This qualifies
that control behavior, not a mechanics method; independent source review and
the final STI17-image gates remain open, and native readiness is false.
No new native, paid, geometry, or further agent/review task is assigned by
this note. Continue from the
[canonical handoff](../../NEXT-AGENT-HANDOFF-2026-10-01.md).
