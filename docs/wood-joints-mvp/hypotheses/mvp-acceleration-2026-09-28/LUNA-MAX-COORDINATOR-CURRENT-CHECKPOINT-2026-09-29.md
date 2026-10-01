# Luna Max coordinator checkpoint — 2026-09-29

This checkpoint carries forward the beam self-weight evidence, records the
completed receiver/load-path ledger and conditional material-crosswalk
reviews, and updates the immediate work order in the
[coordinator status and work order](LUNA-MAX-COORDINATOR-STATUS-AND-WORK-ORDER-2026-09-29.md).
That earlier addendum remains controlling on scope and the T09 deferral. This
checkpoint does not authorize geometry changes, meshing, native solves,
fabrication, or climbing use. `AGENTS.md` remains the governing authority.
The local [README](README.md), [coordinator handoff](COORDINATOR-HANDOFF.md),
and [next coordinator plan](NEXT-COORDINATOR-PLAN.md) now route to this
checkpoint and keep T09 parked.

## Handoff decision

**Ready for a Luna Max coordinator to continue bounded evidence integration
and read-only method preparation. Not ready to freeze or run the six-case
structural response.** The candidate and revision are
`compact-floor-flush-wood-joints-development` /
`led-clearance-2x6-runner-seated-blocks-v1`. Use Luna Max subagents for
independent focused reviews when useful. Parent/root retains frozen-input
readiness, mesh or native-run decisions, serialized run budget, and final
validation.

## Progress to carry forward

- The source audit and attempt04 manifest agree on 50 current one-solid STEP
  bodies. The reviewed lane preserves 92 candidate bolt axes, 12 starting
  frame-bolt arrangements, 66 Hillman panel/kicker screw axes, and the six
  registered load cases.
- Option B—whole-frame demands plus applicable code/product connection
  checks—is the selected MVP architecture. The exact-hash reviewed demand
  register found no path-complete member or joint demand subset. All 47 MVP-E
  criteria remain pending.
- c11 is one globally equilibrated `a12-rear` linear branch, not a valid
  unilateral-contact solution. Six compression-only sign checks fail, the
  independent audit leaves numerical/mechanical acceptance false, and its
  one-run budget is spent. Do not make c12 or transfer c11 forces as demands.
- The four-gate matrix passed an independent Luna Max cold review. Its
  arithmetic, cited hashes, and links checked. Its “Readiness: BLOCKED” label
  refers to member/joint demand readiness; read-only coordination may continue.
- The beam self-weight evidence advanced after that matrix was written. The
  new [attempt01 packet](../evaluation-resume-2026-09-24/current-frame-beam-selfweight-profile-attempt01/README.md)
  profiles 20 exact timber STEP bodies in 599 finite bins along the pinned
  grain-aligned member descriptors. Its rotated-box fixture and locked
  recomputation pass; the independent cold review found no blocking issue.
  At the conditional modeled density of 600 kg/m³, total frame-timber mass is
  127.5321817203 kg. Combined gravity-force closure is
  `4.67e-9 N`, and first-moment closure is `4.60e-6 N·mm`.
- The profile is a finite-bin mass/centroid and whole-wrench accounting result.
  It does not define the structural support spans, exact continuous `q(s)`,
  beam end conditions, section-force recovery, or accepted beam demands. It
  advances the load-input evidence; it does not close the beam-demand gate.
- The source- and revision-bound [receiver/load-path ledger](receiver-load-path-ledger-2026-09-29.md)
  baseline was independently cold-reviewed **PASS** at SHA-256
  `c1181907e211673d746741dcb47e95cf40fe0cb7ba858642e2ea53240c9c2673`.
  That review remains the record for the baseline. A later, bounded row update
  reconciles the 88 geometric order proposals in the candidate inventory with
  the four axes in the reviewed three-member supplement; a direct ID-set check
  covers all 92 candidate axes exactly once. A second narrow note identifies
  the 12 candidate axes with a parallel-to-proposed-grain receiver and keeps
  them outside the perpendicular-axis NDS scenario unless its end-grain
  conditions are established. The current ledger hash is
  `5892a2426cddfd8665bfcae9f6afc85761f38db66548da729ec5a46e70af2cf5`.
  These additions correct method routing only: delivered orientation, contact
  restraint, carriers, laws, stiffness, sharing, solver mappings, signed
  actions, and downstream transfer remain unestablished. No current
  member/joint demand path is closed. The earlier review receipt remains at
  [cold-review-receipts-update-2026-09-29.md](cold-review-receipts-update-2026-09-29.md).
- The exact-body [conditional material-assignment crosswalk](../evaluation-resume-2026-09-24/current-full-frame-conditional-material-crosswalk-attempt01/conditional-material-assignment-crosswalk.json)
  is complete and independently cold-reviewed **PASS**. The reviewer checked
  all 69 source pins, 50 STEP identity joins, and 88 orientations against the
  pinned packet. Its false-readiness flags remain controlling: it does not
  assign adopted wood density or panel layups, close steel/hardware roles,
  define connection laws, establish the solver body/element/node/DOF map, or
  make the model ready for a native run. Exact packet hashes and review status
  are recorded in the [receipt update](cold-review-receipts-update-2026-09-29.md).

## Remaining gates

1. **Floor support — BLOCKED.** Define the adopted conditional no-slip-while-
   bearing law, including open/release behavior, initial bearing and
   re-engagement references, and a bounded state-selection rule. The minimum
   input is an owner-confirmed idealized law consistent with the recorded
   conditional assumption plus a reproducible known-answer state fixture; do
   not introduce an unsupported friction coefficient or a floor-friction test.
   c11's finite paired tangent springs do not implement that law; one active
   floor cell separated while carrying tensile normal force and 328.526 N
   tangent force.
2. **Panel withdrawal — BLOCKED.** The six panel resultants are outward
   `1,199.82–1,659.44 N`. Closing this gate needs applicable resistance and
   load-slip evidence for the exact Hillman 42605 product and installation,
   including engagement, head/panel limits, defensible group interaction or
   sharing, and a source-supported downstream receiver route. If exact product
   evidence is unavailable, an owner-selected alternate complete load path and
   its supporting design basis are required; do not borrow SPAX data or invent
   a rating.
3. **Receiver and hardware paths — BLOCKED.** Geometric intersections and
   source gravity-wrench bookkeeping do not establish active attachment or
   bearing, stiffness, force sharing, mechanical carriers, complete
   receiver-to-frame transfer, or solver body/element/node/DOF mappings. The
   minimum inputs are owner-confirmed carrier/connection roles and route for
   every loaded receiver, source-backed product or design properties/laws
   (including group/stack interaction and stiffness where sharing depends on
   it), and a signed equal/opposite transfer map through the frame. No force
   sharing or capacity is inferred from the 92 candidate axes, 12 retained
   frame-bolt arrangements, or geometry alone.
4. **Beam/member demand — BLOCKED.** The reviewed profile supplies conditional
   finite-bin member-weight resultants and eccentric couples, not accepted
   distributed structural loads. Closing this gate needs adopted material
   density/assignment, defensible member load mapping, defined support spans
   and connection end behavior from the closed receiver paths, signed section
   force recovery requirements, and a known-answer recovery check. Do not
   treat the 600 kg/m³ scenario or mean equivalent line load as exact member
   demand.

These gates interact. Closing one data packet alone does not produce a
path-complete current-revision demand table. The profile's recorded values are
conditional modeled values, not observations of delivered lumber.

## Next coordinator sequence

**Immediate next bounded action:** complete item 7, the integrated four-gate
table and binary readiness recommendation. The demand register, ledger,
crosswalk, beam profile, and their specified reviews are complete; do not repeat
them. The table must keep all four gates blocked unless their exact missing
inputs are evidenced, identify cross-dependencies, and recommend no model
freeze while any gate remains blocked. Do not create another solver/method task
unless the integration identifies a specific unresolved technical question.

1. Read `AGENTS.md`, this checkpoint, the earlier status addendum, the
   [four-gate matrix](four-gate-closure-matrix-2026-09-29.md), the closed
   demand register, the [review-receipt addendum](cold-review-receipts-update-2026-09-29.md),
   and the new beam-profile packet. Verify the exact pins before reusing
   values. Do not recreate the A/B comparison or demand register.
2. **Completed:** the source-derived beam-profile packet is verified and
   independently reviewed, and its conditional input result is appended to
   the [four-gate matrix](four-gate-closure-matrix-2026-09-29.md) with a passing
   Luna Max cold review. The matrix retains exact beam demands as blocked.
   Do not recreate the packet or repeat the completed matrix update. The
   [Hillman 42605 withdrawal preflight](panel-withdrawal-preflight.md) and
   product-source review also exist; do not create a duplicate screen. Its
   resistance and load-slip gate remains blocked.
3. **Completed:** the source- and revision-bound [receiver/load-path
   ledger](receiver-load-path-ledger-2026-09-29.md) has a passing exact-hash
   Luna Max cold review. It distinguishes source geometry/identity and
   conditional wrench accounting from proven carriers, attachment/contact
   laws, stiffness, sharing, signed actions, solver mappings, and downstream
   transfer. It covers panels/Hillman, both center-kicker identity routes, 92
   candidate axes, 12 retained frame-bolt arrangements, 142 T-nuts, the 25 kg
   allowance scenarios, block/frame bearing, and frame/floor. Keep its
   no-path-complete conclusion and open gate statuses; do not recreate it.
4. **Completed; independent exact-hash review PASS:** the current [producer](../evaluation-resume-2026-09-24/current-full-frame-conditional-material-crosswalk-attempt01/produce.py),
   [crosswalk JSON](../evaluation-resume-2026-09-24/current-full-frame-conditional-material-crosswalk-attempt01/conditional-material-assignment-crosswalk.json),
   [README](../evaluation-resume-2026-09-24/current-full-frame-conditional-material-crosswalk-attempt01/README.md),
   and [SHA256SUMS](../evaluation-resume-2026-09-24/current-full-frame-conditional-material-crosswalk-attempt01/SHA256SUMS)
   are pinned at SHA-256 `9f87054729b11041c13bfdac42ed6a63fb0b8dde417b61ff31077d8732d43fd3`,
   `540601bdbcc2cd321cdd600971d8eb3cc4b0f4436a19916513ec0d72705cc65b`,
   `2dc502af7061a2e50d3e2ff92ed7aead9e5c93a2e6faa7a57c55c42d255eced8`, and
   `fcff0c46be85c8100365c15fb65c1c43d14af3601b21d3d2c592f0f6f09cd31f`.
   The JSON binds the current producer and records exact-body conditional
   property/orientation coverage for 44 wood bodies (20 timber members plus
   24 candidate blocks) and 88 conditional transverse cases. Its readiness
   flags remain false for wood density, all six plywood panel layups, steel
   body/role assignments, connection laws, solver body/element/node/DOF map,
   full-frame inputs, and native execution; no candidate/design release is
   asserted. The independent reviewer confirmed all 69 source pins, 50 STEP
   identity joins, and 88 orientations. Keep these limitations and the
   44-body scope. The material packet does not close
   floor support, Hillman withdrawal, receiver transfer, or member
   section-demand gates, and it authorizes no freeze, mesh, or native run.
5. Keep floor support, panel withdrawal, and receiver/hardware transfer open.
   Retain the analytical open/bear/release and tangent fixture in the
   feasibility plan as a review specification only. Do not assume stiffness,
   engagement, group sharing, capacities, or contact behavior to manufacture
   a pass.
6. Defer beam section-force recovery until support spans and connection
   behavior are specifiable. Then validate the chosen line-load and section
   recovery method against a known-answer case before any full-model freeze.
7. **NEXT:** Return one integrated gate table and a binary recommendation to the parent.
   If any gate remains blocked, report the specific next input or decision and
   stop before model freeze. If all prerequisites close, parent separately
   decides exact full-model freeze, known-answer checks, readiness, and any
   serialized six-case run.

This sequence supersedes the earlier status/work-order instruction to prepare
four new packets in parallel: the beam profile and matrix update are complete,
the receiver/load-path ledger is complete, the current withdrawal preflight
remains blocked, and the exact-body material crosswalk packet has passed
independent exact-hash review. The four mechanical demand gates remain open.
The integrated gate table/binary readiness recommendation is next; the demand
register and preceding evidence reviews are closed and must not be repeated.

## Run boundary

The parent has deferred T09 mesh preparation and all mesh generation, including
smoke tests. No native solve is authorized by this checkpoint; c11's run cap
is spent. Do not change the reviewed geometry, create an alternate candidate,
or carry over historical/selected-baseline acceptance. A mesh, a solver exit
code, or a passing evidence audit alone would not establish mechanical
acceptance. Older T09 go/no-go wording in the root continuation note and
execution brief is superseded by the later status/work-order addendum and this
checkpoint; keep T09 deferred unless a specific need is identified and the
parent separately decides to reopen it.

## Exact pins for the new beam packet

- Producer SHA-256: `3125a026f0fdba2f2ce960f276418f52824ba20858be67c4c5bd40f9e0e72b2a`.
- Record file SHA-256: `c3569f1c33b7b6044098c508ca6906fe325b8d430faaf1cf9110cbb9dd0f6fa3`.
- Canonical record digest: `3d3f11095091609940a3b0525ee4f65cb54bb0afc58772b5084eecbcb928b984`.
- README SHA-256: `b0b86d8add77ad5b0906de542bbf7ce20634507ef784757d076f795ae2ed6cc0`.
- Independent cold review: Luna Max reviewer returned PASS with no blocking
  findings; parent also reran the pinned `uv --locked ... --verify` producer
  command successfully.

## Native-method readiness inventory

Existing known-answer work validates useful pieces, but no method validates
the complete current-revision six-case response. Keep the validations within
their tested scopes:

- The [CalculiX 2.23 reduced-static spring fixtures](reduced-static-methods-attempt02/README.md)
  (`e8442a94dc9b2ae458fb9f8d268c78eb1d3d5ddb78edb96b647abdc65e36cf17`)
  pass a rotated `SPRING2` direction/MPC map, scalar compression sign, and an
  active radial-gap branch with reference-load correction. The [frozen
  inputs](reduced-static-methods-attempt02/freeze.json) and [independent
  postrun review](reduced-static-methods-attempt02/postrun-review.json) bind
  the methods to the pinned CCX 2.23 manual. These are isolated linear
  active-branch checks; they do not show active-set convergence or joint
  capacity.
- The [RF-to-opening fixture status](rf-opening-known-answer-attempt02/POSTRUN-STATUS.md)
  (`a238a515eb719ffababdbc0d8db42975aa03ccb2af7137fc4f3ee468ade02734`)
  passes isolated spring action/reaction and `kΔu` recovery. Its spring remains
  active in tension, so it does not validate unilateral release or floor
  support state selection.
- The [penalty-contact work check](../evaluation-resume-2026-09-24/contact-penalty-touch-work-known-answer-attempt01/RESULTS.md)
  and [C3D10 section-output check](../evaluation-resume-2026-09-24/contact-section-force-known-answer-attempt02/RESULTS.md)
  pass small normal-contact and `SOF` output fixtures. They do not validate
  bearing-conditional floor stick or beam-member `N/V/M/T` recovery.
- The beam-profile packet above passes rotated-box and finite-bin
  force/first-moment accounting for conditional timber mass. It does not
  supply continuous line loads, supports, or section forces.
- The [Code_Aster 17.4 checks](../code-aster-candidate-checks-2026-09-27/RESULTS.md)
  cover separate mapping and curved-contact procedures. They do not validate
  the planned CCX joint/frame model or authorize a solver substitution.

Before a six-case model can be frozen, the coordinator must close or
disposition the four demand gates, complete source-backed member/panel
material and solver-body/element/DOF mappings, and define attachment/support
laws and load transfer for the full path. The section-force known-answer
fixture follows those inputs. Parent retains freeze readiness, any run budget
and authorization, serialized execution, and final validation.

## Parent integration update — 2026-09-29

The checkpoint's prior item 7 is complete in the append-only [integrated
readiness decision](four-gate-closure-matrix-2026-09-29.md#append-only-integrated-readiness-decision--2026-09-29).
It incorporates the already completed receiver/load-path ledger and exact-body
material crosswalk with the reviewed A/B comparison, demand register, beam
profile, and Hillman preflight. The original matrix cold review predates this
parent addition; no repeated handoff or cold review was commissioned. The
integrated decision remains **BLOCKED** for model freeze and six-case response.
This denotes missing evidence, not physical failure, and it adds no mesh or
native-run authority.

The next bounded engineering task is to resolve the already specified
conditional floor-stick state rule against its hand-solvable open/bear/release
and re-engagement fixture. The result it unlocks is a finite, unambiguous
local state rule that allows a later parent decision on whether to scope a
frame implementation; it does not validate a full-frame solver or produce
support reactions. Stop if the state/reset rule cannot be made finite and
unambiguous or does not satisfy the fixture; keep every floor-dependent action
blocked in that event. Do not create another generic contact coupon or expand
the solver scope. Afterward, advance the exact Hillman withdrawal and
receiver-transfer inputs; no equal sharing, c11 force transfer, model freeze,
or solver run follows automatically.

## Owner-guided Option B continuation — 2026-09-29

This append-only update supersedes the preceding immediate-next-task
paragraph: the local normal/tangent fixture is now complete and reviewed.
Continue Option B (whole-frame static demands plus applicable code/product
checks), prioritize the four demand gates and receiver/load-path work, and
reuse the completed A/B comparison, demand register, receiver ledger, material
crosswalk, beam profile, and reviewed fixtures. Do not repeat a cold handoff or
recreate those packets unless a changed input or a specific discrepancy
requires it. Every new task must name the engineering result it unlocks and a
stop condition. Detailed contact work must answer a bounded missing mechanism;
the two-cell fixture now does so for normal release/re-engagement plus one
ideal-stick direction. This update grants no mesh or native-run authority and
changes no geometry, criteria, or run controls.

### Evidence gained without closing a demand gate

- The exact-hash reviewed [two-cell normal/tangent fixture](conditional-floor-two-cell-coupled-stick-fixture-attempt01/README.md)
  tests eight stages. Each has a unique normal state; open contacts carry zero
  tangent force; re-engagement references reset as specified; maximum normal
  residual is `2.274e-13`. Luna Max reviewed the exact input, verifier, result,
  source pins, equations, and limits and returned **PASS**, with no blocking
  or nonblocking findings. It does not model full-frame flexibility,
  multidirectional contact, floor resistance, or actual support reactions.
- The [accessory-aware global support screen](accessory-support-resultant-attempt01/README.md)
  reconstructs 54 load/accessory scenario wrenches. All normal-resultant CoPs
  fall inside the modeled support hull; minimum margin is `389.254 mm`, and
  normal resultant is `4,670.093 N`. This is necessary gross-hull equilibrium
  evidence only; it does not give member foot reactions, floor capacity, or a
  complete load path.
- The [panel screw-group screen](panel-screw-group-total-withdrawal-attempt01/README.md)
  gives conditional total withdrawal lower bounds of `1,199.82–1,659.44 N`
  for five cases under its explicit normal-only/no-tangential-contact
  assumptions. `a1-rear` remains unbounded because of the modeled opposing-
  normal kicker/panel patch. No per-screw force or capacity is inferred.
- The [three-member bolt-stack order supplement](bolt-groups/three-member-stack-order-attempt01/README.md)
  resolves modeled receiver sequence for four axes in two three-member stacks.
  This adds member identity/order for later checks, not installed orientation,
  force sharing, or resistance.

These results make the remaining inputs more specific but produce no
path-complete member/joint demand subset. The floor, panel withdrawal,
receiver/hardware, and exact member-demand gates remain **BLOCKED**; all 47
MVP-E criteria remain pending. Missing evidence is not physical failure.

### Next coordinator sequence

1. **Resolve the panel-product gate using existing product research.** The
   engineering result is either an applicable Hillman 42605 resistance and
   load-slip basis for comparison with the five group-total bounds, together
   with resolution of the `a1-rear` alternate contact, or a precise
   `uncheckable` disposition that lists what evidence is absent. Inputs are
   exact product qualification/properties, thread-root/head geometry, actual
   installed penetration and pilot/countersink basis, panel/head limit, and a
   defensible group-sharing basis. Stop if a source does not apply to the
   purchased product and installation; do not borrow SPAX values, divide
   equally, or convert an NDS reference value into a product rating. If a
   complete alternate tension path or matched test is required, return that
   concrete owner decision rather than adding a speculative design.
2. **Continue receiver closure from identified paths.** The engineering
   result is signed equal-and-opposite interface actions along a complete
   panel/block/frame/runner/support route and the corresponding applicable
   bolt, wood-bearing/splitting, and group checks. Reuse the receiver ledger
   and stack-order result. Required inputs are the adopted connector/member
   roles, a supportable attachment/bearing law and stiffness where action
   distribution depends on it, delivered connector properties/dimensions,
   member/panel properties, and body/element/DOF mapping. Stop at the first
   loaded interface without a known carrier, supported force-sharing basis,
   or downstream route; geometry intersections and c11 forces are not
   substitutes.
3. **Recover member actions after transfer paths close.** The engineering
   result is signed per-case member `N/V/M/T` plus deflection/stability
   quantities that can be checked against the adopted criteria. Reuse the
   finite-bin mass profile, but first establish adopted material/density,
   support spans/end behavior, and a justified local load/section-recovery
   method with its small known-answer check. Stop if supports or load mapping
   remain undefined.

The floor fixture and support-hull check allow a later parent decision on
whether a complete frame implementation is ready for consideration. They do
not authorize one. No further local contact coupon, model freeze, mesh, or
native solve follows automatically. Parent retains frozen-input readiness,
serialized heavy execution, any run decision, and final validation.
## Current owner-guided continuation — 2026-09-29

This update supersedes the prior immediate task ordering where the public
product-source screen or floor-reaction envelope is concerned. Continue Option
B with the reviewed source inputs and no repeated A/B, register, ledger,
crosswalk, or generic contact work.

- The exact-product public screen now supports an **UNCHECKABLE** disposition
  for Hillman 42605 under the recorded installation. Lowe's identifies the
  purchased model; its product Q&A says a tensile rating is not listed. The
  public sources provide no applicable withdrawal resistance, load-slip
  stiffness, root/head dimensions, or qualification basis. The existing
  [panel preflight](panel-withdrawal-preflight.md) distinguishes generic NDS
  reference arithmetic from a product rating. Do not repeat public searches
  without a new source lead. Reopen this path only with exact-product data,
  matched testing, or a separate owner-directed complete alternate tension
  path. Missing data is not a physical failure.
- The exact-hash reviewed
  [normal foot-reaction envelope](normal-foot-reaction-equilibrium-bounds-attempt01/README.md)
  shows that all 54 case/accessory wrenches admit at least one vertical
  compression-reaction allocation on the eight modeled support faces. Each
  face can independently have a zero reaction in a statically admissible
  arrangement; the largest individual-face upper bound is 3,605.070 N.
  These are outer statics bounds, not actual reactions, pressure, or floor
  capacity, and they do not close the floor gate.
- The next engineering result is a signed, equal-and-opposite action path
  through an interface whose carrier and force law are actually supportable,
  followed by applicable connection checks. Reuse the receiver ledger and
  stop at the first loaded interface lacking a carrier, law, force-sharing
  basis, or downstream route. Do not infer sharing from axis count or c11.
- Member N/V/M/T recovery remains downstream of closed receiver paths and
  support spans/end behavior. Reuse the reviewed finite-bin mass profile;
  stop if material assignment, the load mapping, or section method is
  unresolved.

This is sufficiently scoped for a Luna Max coordinator to continue bounded
evidence integration and source-backed mechanics preparation. It is not
six-case model/run readiness: **binary readiness remains NO**, all four gates
remain **BLOCKED**, and all 47 MVP-E criteria remain pending. Parent ownership
of freeze readiness, any mesh/native-run decision, serialized execution, and
final validation is unchanged.

## Panel group threshold update — 2026-09-29

The exact-hash [gravity-inclusive panel-group packet](panel-screw-group-total-withdrawal-attempt02/README.md)
updates the earlier climber-only group minima using each loaded panel's
conditional self-weight and same-panel T-nut gravity. At the modeled 600
kg/m³ panel density, five cases have a conditional normal-only lower bound of
**1,304.24–1,763.87 N total axial tension over the twelve aligned screws**.
`a12-rear` governs at 1,763.868 N. The `a1-rear` loaded-panel resultant is
1,763.734 N, but no group bound is asserted because a finite
`kicker_left`/`main_lower_left` contact permits an opposing compression
reaction.

Luna Max independently checked the source pins, applied-force-plus-gravity
reconciliation, panel density, axes, contact signs, and limits: **PASS**.
This gives an updated group-total threshold only; it supplies no per-screw
sharing, Hillman resistance, or receiver-to-frame demand. The panel gate stays
**BLOCKED / UNCHECKABLE from current public product data** and receiver paths
remain open. Do not repeat public-source searches without a new lead. Overall
readiness remains **NO**, and this update grants no geometry, mesh, or native
run authority.

The [four-gate matrix](four-gate-closure-matrix-2026-09-29.md) records the
packet hashes and retains all gate dispositions. Continue from its bounded
receiver-action sequence; stop at the first interface lacking an identified
carrier, supported transfer law, force-sharing basis, or downstream route.

## Owner priority correction — current bolt/block joints, September 29, 2026

This supersedes any next-work instruction above that makes complete panel
qualification a prerequisite for investigating all joints. Preserve existing
panel packets; stop expanding panel-group studies and repeating Hillman
catalog searches. The [bounded applicability comparison](prior-panel-applicability-bounded-2026-09-29.md)
records the eight moved screw stations and four receiver-name changes against
the owner's accepted panel-construction scope. Missing exact-product capacity
remains explicit, without blocking prescribed-load conditional joint work.

The next representative connection is BG001: `knee_outer_left_post_1/2`,
joining `base_post_outer_left` and `knee_outer_left_spine`. Reuse reviewed
single-bolt NDS equations with its actual modeled receiver lengths and
42.05 mm inter-axis pitch. Calculate bolt forces from a prescribed shear and
moment; do not label that assumed wrench an accepted six-case frame demand.
The accompanying dependency check identifies end/edge distances, splitting,
washer/axial transfer, delivered shank/engagement, and onward spine transfer.
Stop this slice when its conditional demand coefficients, reference values,
and exact outstanding inputs are reproducible. No geometry, mesh, native-run,
physical-work or acceptance authority changes. Parent retains validation.

## BG001 conditional calculation result — September 29, 2026

The [current knee-post packet](current-knee-post-conditional-bolt-screen-attempt01/README.md)
now supplies an actual-geometry, prescribed-wrench lateral force map and
conditional individual-bolt NDS/TR12 reference screens. Both modeled bearing
lengths are 38.1 mm; bolt pitch is 42.05 mm. Per-bolt references are 567.848 N
for global-Y loading and 796.262 N for global-Z loading, under the packet's
explicit full-body bolt/wood assumptions. Each 1 N·m of Mx produces opposite
23.781 N bolt-Y actions. These are neither adjusted group capacities nor
accepted current frame forces.

Parent reproduced the packet and independently recovered a mixed prescribed
force/moment case using 3D cross products. The [dependency note](current-knee-post-check-dependencies.md)
records modeled post terminal distance 25.4 mm at the upper axis, a
load-direction-dependent end-distance concern; spine descriptor distances
remain distinct from cut-aware finished-profile distances. Axial/washer laws,
delivered shank and nut overlap, group/geometry/splitting checks and onward
BG003/BG045 transfer remain unclosed. No criterion changes disposition.

The missing demand is the signed six-component BG001 wrench at its recorded
centroid for each case. This is an input to full joint assessment, not a reason
to stop conditional joint investigation. Next useful slice: determine the
cut-aware spine end distances and load-direction branches for BG001, and
bound axial tie/washer actions from a prescribed full wrench. Stop on an
unrepresentable component or absent resistance input; report it explicitly
without changing reviewed geometry or inventing a capacity. Reuse this packet;
do not repeat handoff/cold-review cycles without a specific concern.

## BG045 onward-header lateral branch — September 29, 2026

The [current knee/header end-grain screen](current-knee-header-endgrain-screen-attempt01/README.md)
uses the current 139 mm block and 38.1 mm header bearing intervals under
explicit conditional main/side roles. Parent checked the pinned primary NDS
PDF's §§12.3.3.4 and 12.5.2.2 directly: eligible main-member end-grain axes use
perpendicular-grain main bearing and Ceg=0.67. The resulting per-bolt
Ceg-only references are 401.636 N for header-grain-parallel lateral loading
and 380.458 N perpendicular to header grain. All other factors and checks,
actual signed demands and complete BG003 transfer remain missing. Opposite
head orientations do not create separate group capacities. The reproducible
screen and independent mode-IV calculation pass; no criterion passes and no
geometry or native-run control changes.

## Finished knee profile and axial-transfer results — September 29, 2026

The [48-ray finished-profile packet](current-knee-finished-profile-attempt01/README.md)
replaces descriptor-only uncertainty for the two BG001 receivers. All terminal
faces are square in the queried directions; distances repeat at the three
sampled depths. Post upper-axis end distance is 25.40 mm (4D), spine lower-axis
end distance 31.75 mm (5D). Under the applicable opposed softwood tension
branch, their preliminary end factors are 4/7 and 5/7; the NDS minimum-factor
rule would apply 4/7 to all BG001 fasteners. Reversed tension and the recorded
compression/perpendicular end-distance branches have end factor 1.0. These
are conditional geometry results, not overall adjusted resistance. All
queried edges exceed 4D. Continuous minima, splitting/net-section and the
remaining adjustments are not established. Parent replay matched all 48 rays
and verified source/output/producer hashes.

The [axial/contact envelope](current-knee-axial-contact-bounds-attempt01/README.md)
retains the actual contact face with its two bore voids and transforms moments
from shaft centroid to face datum. It demonstrates normal-force equilibrium
routes for both My and Mz using nonnegative bolt tensions and compression
resultants. For zero net axial force, ideal minimum total ties per 1 N·m are
13.550/14.826 N for positive/negative My and 10.499/26.247 N for Mz. Vertex
resultants describe an unrestricted-pressure closure envelope, not a physical
pressure solution. Self-equilibrated tension/contact modes leave upper tie
forces unbounded until compatibility, pressure limits and preload/stiffness
are specified. Parent reproduction and an independent mixed signed-wrench
check pass; no accepted six-case joint wrench, washer capacity or mechanical
criterion disposition follows.

Next bounded result: bind the reviewed Cg helper to the source geometry and
explicit pure-grain-parallel conditional BG001 actions, with material/section
sensitivity and the relevant Cdelta branch. Preserve the separate axial and
lateral maps; do not combine component reference ratios into an invented
interaction. Then treat the complete BG003 three-member stack with its actual
ordered receivers, rather than multiplying pairwise single-shear capacities.
Stop either slice when applicable inputs cannot be bound, and name that input.
No geometry, mesh, native-run or physical-work authority changes.

## Owner clarification: corner-block replacement scope — September 29, 2026

BG001/BG003/BG045 are the complete **left outer corner-block assembly**:
post/exterior spine, continuous spine/side/inner-block stack, and inner
block/header. These six introduced axes belong to the 92 replacement
block-attachment axes, distinct from the twelve original leg/floor-runner
axes with recorded baseline checks (four leg, eight runner). Continue current
corner replacements as the primary deliverable. Reuse unchanged original
bolt resistance/geometry/hardware calculations. Reopen a retained-bolt check
only after naming a concrete changed receiver, geometry, hardware or demand;
do not restart blanket qualification or transfer historical case passes.

The [complete corner summary](current-knee-joint-check-summary.md) separates
these inventories and assembles current bearing/contact, bolt-group,
end/edge, washer/axial and onward-transfer results and exact missing inputs.
No geometry or native-run control changes follow from this clarification.

## New corner bolt-group and three-member calculations — September 29, 2026

Current **left outer corner-block** results are consolidated in the
[complete corner-path summary](current-knee-joint-check-summary.md).
The [BG001 Cg packet](current-knee-post-group-factor-attempt01/README.md)
reproduces Cg=1 for the two supported ring scenarios, matched conditional
longitudinal EA and actual 42.05 mm pitch. Cg/Cdelta-only per-bolt references
are 455.007 N toward the short ends and 796.262 N in the reverse branch.
The [BG003 double-shear packet](current-knee-three-member-transfer-attempt01/README.md)
retains the physical 38.1/88.9/88.9 mm stack and applies the pinned NDS
§12.3.5.4 minimum-side-bearing rule. Its matched-property, equal-outer-action
one-bolt scenarios give 1,160.581–1,486.407 N in the three recorded directions.
No pairwise capacities are added. Parent verifies all four modes, independent
mode IV, and the [72-ray BG003 profiles](current-knee-three-member-profile-attempt01/README.md).
All results remain conditional; no accepted demand/capacity or criterion pass.

Minimum next mechanics inputs are simultaneous signed member actions at the
corner cuts and compatible active bearing/contact plus axial/lateral bolt
load-sharing behavior. Code/product/local wood checks must then use those
actions and explicit supported material/hardware conditions. The twelve
original leg/runner axes are not reopened by these new corner calculations.
Next bounded work should address BG003 axial/washer and splitting/net-section
mechanisms or the source-backed corner compatibility assumptions, with a
specific result and stop; avoid an open-ended contact/solver project.
Geometry, native-run controls and selected-baseline evidence are unchanged.

## Recovered corner compatibility inputs — September 29, 2026

The later frozen C11 input already includes one tension-only outer-seat tie
per physical corner bolt. Parent extraction confirms BG001/BG003/BG045
paired axial stiffnesses of 4,670.054 / 4,234.008 / 3,207.383 N/mm and lateral
stiffness 3,086.746 N/mm per plane/component. BG003 retains two lateral planes
and a single outer-seat tie, not separate two-member bolt capacities. Earlier
preparation notes saying there is no axial law are not the later input state.
These source-bound coefficients remain conditional idealizations. Their
recovery supplies no accepted forces or active contact states from the failed
C11 response and grants no run authority.

Current bounded work targets the new left corner's local wood sections,
modeled washer-seat pressures and the implemented compatibility assumptions.
It unlocks explicit per-unit checks and a precise account of what a complete
corner demand evaluation still needs. Stop at unsupported product properties,
unsupported splitting arrangements or unresolved simultaneous member actions;
do not repeat original LEG/FLOOR-RUNNER resistance work. The complete corner
summary remains the consolidated result, with new/retained inventories separate.

### Completed local section and seat slices

The [local wood screen](current-corner-local-wood-screen-attempt01/README.md)
reproduces candidate net areas of 5,036.820 mm² for the spine's separate bore
planes and 11,099.708 mm² for the inner block at a BG003 bore plane with both
BG045 longitudinal holes. Their uniform axial stress coefficients are
0.000198538 and 0.0000900925 MPa/N. The holes occupy separate voids in the
same section plane; no strip/circle overlap is subtracted twice. Parent
verification passes. These are geometry inputs, not splitting or capacity.

The [six-axis washer-seat screen](current-corner-washer-seat-screen-attempt01/README.md)
reproduces modeled annular area
222.726212151 mm² and thickness 1.651 mm, giving average pressure
0.0044898173 MPa/N under uniform full support. Its ideal transverse DF-L No. 2
wood-bearing comparison is 959.777 N per eligible post/header seat only.
The proposed end-grain BG045 block seat and unsourced block strength do not
inherit it; washer metal bending remains separate. Parent six-axis source and
arithmetic verification passes with maximum seat closure residual 1.11e-16 N.

The minimum next demand input is one simultaneous signed corner/member-action
set at explicit datums under a justified compatibility/contact scenario;
then bind applicable timber and hardware assumptions to those actions.
No original leg/runner resistance check was reopened, no native solve was
run, and no accepted corner demand or assembly-capacity claim follows.

## Complete-corner carrier inventory — next continuation

The preceding goal turn made progress: both bounded section/washer packets
were completed, parent-reproduced, and integrated into the corner summary.
This continuation checks source-bound force-recovery coverage without using
the rejected C11 forces. Parent extraction finds seven internal contact pairs
(28 sampled cells) among outer post, spine, side, inner block and header.
Direct header/post, header/side and header/spine bearing can share or bypass
the nominal BG001/BG003/BG045 bolt chain. Spine/runner bearing is another
onward route. These change the required local cut inventory; none proves
activation, resistance or an accepted load path by itself.

The bounded interface-recovery map must enumerate these cells, the six new
bolt axes (eight lateral planes and six outer-seat ties), the affected member
cuts and outward boundary carriers. It unlocks source-complete individual
member and aggregate-corner equilibrium recovery after a valid response;
aggregate closure alone cancels internal forces and cannot qualify a bolt
group. Stop at the map and precise absent compatibility/output evidence;
do not recover the failed response as design demand or repeat baseline
retained-bolt resistance work. Native budgets and reviewed geometry remain
unchanged. The consolidated corner report now records the seven pairs and
their modeled areas.

### Carrier map completed and verified

The delegated agent handle became absent before its map was written. Parent
finished the bounded [source inventory](current-corner-interface-recovery-map-attempt01/README.md)
directly rather than restarting that work. Its producer verifies the frozen
input hash, each of the six physical corner axes, seven internal contact
pairs / 28 cells and all four paired post/floor normal/tangent rows. The full
five-member inventory has 36 contact pairs / 236 cells, with 29 boundary pairs
identified only for force accounting. Saved JSON reproduces exactly. No
response forces, active states, geometry or native execution are involved.
The corner summary links the map and retains signed demand as outstanding.

Next mechanics work must supply justified simultaneous corner cut actions
and compatibility, not another carrier inventory. A local prescribed-action
scenario is conditional and cannot replace the six-case frame response.
Complete frame readiness remains false under the recorded global support,
receiver sharing and member-response gates. Do not transfer original bolt
case passes or restart their unchanged resistance calculations.

## BG001 conditional sharing: new mechanics result

The [prescribed-action packet](current-post-spine-conditional-sharing-attempt01/README.md)
now calculates sharing for the existing two axial ties and four contact
centroids with rigid local members, zero gap/preload and no other corner
carriers. This is bounded arithmetic under a parent-defined scope, not a
native/full-frame response. All 64 branches are checked; inconsistent signs,
singular matrices and differing compatible displacement states stop results.
Four imposed 1 N·m moment probes give total ties 22.622/23.489 N for My and
16.152/207.169 N for Mz. Independent scalar known answers and parent 3D
wrench recovery pass; largest reported residual is 1.46e-11 N or N·mm.
Pure positive Fx remains unresolved under the uniqueness guard.

The reverse-Mz action is about 7.9 times the ideal footprint lower bound:
the fixed centroid carriers restrict the short-side contact lever to 4.827 mm.
This establishes an actual resolution dependency in the reduced contact
idealization. Next bounded mechanics should check pressure-resolution
sensitivity or a supported distributed-pressure representation; stop before
claiming a physical pressure field, complete-corner sharing or adopted forces.
Keep all seven corner contact pairs and real simultaneous boundary actions
in the eventual complete response. No native budget, geometry, original
bolt resistance disposition or criterion changed.

## BG001 resolution issue bounded with fixed-law refinement

The [pressure quadrature experiment](current-post-spine-pressure-resolution-attempt01/README.md)
holds geometry, two tie stiffnesses and the 100 N/mm³ normal penalty fixed.
Six grids (16² through 512²) exclude the two modeled circular bores. At 512²,
the reverse-Mz total tie action is 28.119 N per imposed N·m rather than the
four-centroid 207.169 N; all four moment probes change less than 0.009% on the
last refinement. Exact footprint area differs from represented area by only
0.048730 mm². This establishes coarse-sampling bias for this rigid local
experiment, not a weak-block finding or accepted actual demand.

Source-pinned reproduction, independent-start agreement and a separate
diagonal-spring oracle pass; maximum physical residual across 24 probes is
1.60e-12 N or N·mm. Runtime SciPy 1.18.1, API documentation and versions are
recorded. No native/frame solve, geometry or criterion changes occurred.
Do not repeat this completed resolution experiment without a changed input
or specific concern. The remaining next dependency is applicable compliance
and simultaneous complete-corner boundary actions, retaining all seven
internal bearing pairs and the source-bound outward carriers. The local
fixed penalty law is still not measured wood/contact behavior.

## Existing compliance scenarios: completed local sensitivity

The [BG001 compliance packet](current-post-spine-compliance-sensitivity-attempt01/README.md)
applies all 24 existing paired ring/depth/steel-E scenarios at fixed 256²
pressure quadrature. Effective ties span 1,780.926–8,869.699 N/mm. Negative-Mz
total tie action remains 27.429–28.781 N per imposed N·m, compared with the
coarse-cell 207.169 N. The other three moment ranges and individual ties are
source-bound and reproduced; all 96 probes close, maximum residual 3.02e-12.
Independent starting points agree. This is progress in conditional sensitivity,
not a physical stiffness guarantee, six-case response or criterion closure.

Do not repeat the completed BG001 resolution/compliance sweeps without a
changed input or specific concern. Next mechanics must move to simultaneous
complete-corner actions/compatibility and applicable resistance inputs,
retaining the seven internal bearing pairs and boundary-carrier map. Global
floor/receiver/member readiness gates remain explicit. Native-run budgets,
reviewed geometry and original bolt resistance evidence are unchanged.

## Complete five-member operator: coupled mechanics coverage

The [corner equilibrium packet](current-corner-equilibrium-operator-attempt01/README.md)
now assembles all 50 internal components into 30 member force/moment rows.
Bolt-only rank is 18 (six relative rigid-member modes); including all seven
potential contact pairs raises algebraic rank to 24. This is a bilateral rank
test, not unilateral engagement/stability acceptance. The full operator has
26 algebraic force-sharing directions and therefore cannot determine actions
from balance alone. Source reproduction, independent global internal-wrench
cancellation and nullspace closure pass with residuals below 3e-15 in scaled
components. Singular-value separation makes the reported ranks unambiguous.

Next complete-corner work must bind simultaneous outward actions and compatible
unilateral response. Do not remove direct bearing paths or repeat isolated
BG001 sweeps to substitute for that coupled result. No native/full-frame run,
criterion closure, geometry or original leg/runner resistance changes.

## Complete-corner conditional sharing calculated

The [five-member sharing packet](current-corner-conditional-sharing-attempt01/README.md)
uses all 50 internal carrier components with existing spring inputs and 48
balanced imposed force/couple pairs. The initial residual-root approach
closed none and is preserved as rejected diagnostics. Constrained minimum
complementary energy using existing SciPy SLSQP closes 47, with explicit
equilibrium, unilateral sign, constitutive and two-start guards. Independent
hand-spring fixtures and all-five-member physical-point wrench checks pass.
One negative-X spine probe is excluded: static balance closes, recovered
displacement gives 1.883 N constitutive mismatch. Do not treat it as a
physical failure or relax the guard. A focused Luna/max sign/duality/gauge
check is pending, not another broad cold-review cycle.

The output supplies simultaneous signed BG001/BG003/BG045 and bearing actions
for those declared probes only. Fixed coarse contact sampling, rigid members,
zero clearance/preload and absent outward frame carriers remain limitations.
Next work must resolve the specific excluded consistency state and applicable
complete-corner compliance/boundary actions, then actual resistance checks;
do not relabel probes as six-case frame demands. Native budgets, geometry,
original bolt resistance and all pending criteria remain unchanged.


## Complete-corner force closure: 48 probes, displacement limitation retained

The former negative-X spine exception now has a compatible witness for the
original laws. Linear feasibility recovery changes no QP forces; the original
constitutive, unilateral and physical-balance tolerances remain unchanged.
Both starts give 0.5 N per BG001 tie and negligible other actions. An independent
analytic witness translates all four non-post bodies equally in negative X,
opening post/spine contact and stretching those ties. Its full-body balance
and predicted actions match. All 48 imposed probes now close; maximum physical
residual is 6.54e-9 N or N·mm, spring-law error 1.22e-9 N and start-to-start
force difference 7.55e-12 N. Source reproduction and independent recovery pass.

The negative-X probe has different compatible displacement witnesses; both
are saved. A focused Luna/max follow-up confirmed comparing the strictly
convex energy's minimizing forces while checking each original spring law,
rather than imposing displacement uniqueness. This is conditional force
closure, not stability or design acceptance. The earlier multiplier-only
47-closed output is preserved. The focused sign/duality/gauge review is also
complete; no repeated broad review cycle is needed.

Primary work remains the NEW BG001/BG003/BG045 left outer corner-block path,
including seven internal bearing pairs and onward transfer. The 92 introduced
block axes stay separate from 12 original LEG/FLOOR-RUNNER axes. Reuse original
resistance evidence; reopen only a named changed detail or calculated demand.
No geometry, native-run budget, criterion or fabrication disposition changes.

Next task must unlock actual corner demand or an applicable resistance check,
not repeat completed unit probes. Minimum outstanding inputs are simultaneous
source-case boundary wrenches, physically applicable complete-corner compliance
(including BG003 shaft and contact resolution), and matched block/hardware
resistance/engagement data. Global floor/receiver/member readiness remains
unresolved; no accepted six-case demand is created by these local probes.


## Corner-demand dependency: coupled support rule and exact limitation

The [bounded structural-coupling fixture](conditional-floor-structural-coupling-fixture-attempt01/README.md)
now tests normal/tangent coupling, ideal stick only while bearing, release,
and discrete reference reset. Four hand-answer stages each have exactly one
admissible mask. Standard-library KKT and independent constrained-coordinate
elimination agree on all 16 candidate states, with selected force-balance
residual below 3.56e-15 N. This closes that small-fixture coupling question,
not the full-frame support gate or any corner-demand check.

The [exact-rational applicability counterexample](conditional-floor-structural-coupling-fixture-attempt01/parent-reference-counterexample.md)
also proves that this fixed preceding-open-state reference rule does not
ensure existence or uniqueness under arbitrary coupled loads. One cell with
fixture carrier `[[20,5],[5,100]] N/mm`, normal penalty 100 N/mm and reference
x=0 has no admissible static branch under `(Hx,Pz)=(4,+0.5) N`: its open
branch penetrates; its stuck branch requires negative normal force. The
sign-reversed load has two admissible branches. These are method examples,
not source-case loads or physical failure findings. The corner's convex
force-energy argument does not prove uniqueness for this disjunctive floor law.

Parent source-pin extraction finds 100 frozen floor-normal cells, each with
a paired old tangent ownership row: 38 per runner and four per remaining
six supported posts/legs. Exhaustive normal-mask enumeration has up to
`2^100` candidates and is not a practical frame selector. No C11 force or
finite-tangent acceptance transfers.

The precise remaining floor dependency is an applicable reference-capture
and loading-history/state-selection treatment for the coupled frame, with
bounded failure behavior; neither four passing stages nor selecting one
admissible mask supplies it. Do not fix it by accepting negative normal
forces, retaining tangent restraint at zero bearing, or changing stiffness
until a branch passes. No frame/native run, geometry, criterion or original
LEG/FLOOR-RUNNER resistance change occurred. Signed actual-case corner
boundary forces and applicable member/hardware checks remain outstanding.


## Six-case aggregate support feasibility: all-bearing witnesses exist

The [global floor-wrench screen](current-global-floor-wrench-screen-attempt01/README.md)
reconstructs all 778 gravity sources and the six external force wrenches,
using frozen input floor coordinates. For all six cases, both without the
accessory diagnostic allowance and with the recorded 25 kg mean placement,
aggregate equilibrium admits strictly positive normal forces at all 100
floor cells. Full six-component force/moment witnesses close independently
within 1.52e-11 N / 1.18e-8 N·mm. Source reconstruction, known-answer square
support fixtures and reproduction pass. These are algebraic witnesses, not
compatible actual reactions, a tipping pass or signed corner demands.

Global balance therefore does not force lift-off in these scenarios. This
supports testing an all-bearing branch for compatibility; it does not prove
that branch, remove the fixed-reference counterexamples, or close global
readiness. The next response check must verify actual normal signs and full
body closure with the supported frame/receiver/member mappings. No native
run, floor-law change, geometry or old-bolt resistance work is authorized by
this screen. Corner-block demand remains the primary missing result.

A targeted official-documentation search found Abaqus rough contact, together
with reopening limitations, and Code_Aster's Coulomb friction description.
Neither provides a verified immediate substitution for the present floor
predicate/reference policy. Details and links are in the packet; no new
solver-selection campaign or unsupported friction value follows.


## September 29: corner priority and bounded native method result

BG001 (post/exterior spine), BG003 (spine/side/inner block) and BG045
(inner block/header) are the left outer corner-block assembly. The primary
engineering deliverable remains its complete transfer path, including member
bearing/contact, physical bolt groups, splitting/net section, washers and
onward transfer. The 92 introduced block-attachment axes replacing old
ML24Z/SDS duties are separate from the twelve retained original LEG and
FLOOR-RUNNER bolt arrangements. Reuse unchanged original resistance and
geometry calculations; reopen an original arrangement only after naming its
specific changed geometry, receiver, hardware or calculated demand.

The independently reviewed, frozen nonlinear SPRING2 known-answer coupon
used its single serialized 60-second launch budget. Docker and the pinned
2.23 binary ran successfully; the solver returned 201 after exhausting
increment cuts at the zero crossing in step 2. Step 1 attained the known
answer: +10 N applied, +0.1 mm displacement, +10 N positive internal spring
force, zero negative spring force, and -10 N ground reaction. All 17 printed
converged increments before failure obey the intended table force law within
8.9e-16 N (printed precision); the negative branch and reversal did not
complete. This is partial method evidence, not a method pass. The assessor
correctly rejects the run. No automatic retry, new full-frame launch,
criterion change or geometry change follows.

See [the bounded coupon packet](nonlinear-spring2-known-answer-attempt01/README.md)
and its partial-observations.json. Actual six-case signed boundary actions
for this corner remain missing; aggregate support witnesses and local unit
probes cannot substitute for compatible frame demands. Remaining corner
checks also need applicable member/seat/washer and delivered bolt compatibility
evidence at the resulting combined actions. Existing evidence is reused where
applicable; no general LEG/FLOOR-RUNNER qualification campaign is started.


## Source-bound carrier law inventory for the corner-demand dependency

The [input-only law inventory](current-native-carrier-law-inventory-attempt01/README.md)
now binds all 1,840 scalar carriers to the frozen frame input and their
physical owners: 1,122 compression rows, 170 tension rows, 348 bilateral
lateral components and 200 conditional all-bearing floor tangent components.
The physical bolt-axis partition is checked explicitly: 92 new block axes
and 12 original LEG/FLOOR-RUNNER axes are disjoint, and their union is exactly
the 104 outer-seat axial ties. The four extra new-bolt shear planes remain
planes on existing physical bolts, not extra bolts or extra axial ties.
All frozen stiffnesses, force bases and attachment datums are preserved; no
rejected response or historical active states enter the intended laws.

The inventory unlocks an exact input/output mapping if a native method passes
its branch-switching fixture. It is not a replacement solve or native run
authority. If an all-bearing response is tested, every paired normal must
be strictly positive before its floor tangent hypothesis is usable; aggregate
support equilibrium is insufficient. Current frame readiness remains false.


## Native branch diagnosis and exact workaround fixture freeze

Inspected 2.23 source computes current signed force correctly for SPRING2,
but its nonlinear tangent branch selects the interval with an unassigned
`val`; SPRING1 has the same limitation. The failed coupon stopped at the
load zero crossing and never verified the negative branch. This is a strong
source-based explanation, not binary causation proof or a physical failure.
The SPRINGA branch explicitly calculates current-minus-initial length.

A [separate straight-line SPRINGA coupon](nonlinear-springa-known-answer-attempt01/README.md)
is frozen at SHA c782f4c39c764691b6de0ed608798d43bd3b7310badf769eee3b8aa13ca230ba.
It preserves the same opposing laws, three force ramps and hand answers,
uses 100 mm numerical spans with fixed transverse motion, and remains
unexecuted pending focused independent review and parent readiness. It
changes no pinned runtime or frame inputs and grants no frame run.

The carrier inventory additionally binds engagement signs to the existing
helpers: their current tension and compression branches both engage for
`u_second-u_first > 0`, hence both use negative native
`delta=u_first-u_second`. Ordered physical endpoints and projected axes
distinguish the mechanisms. No generic tension-sign assumption is used.


## SPRINGA native signed-law and reversal method verified

The [straight-line SPRINGA coupon](nonlinear-springa-known-answer-attempt01/README.md)
passed its controlled single native launch with the same pinned 2.23 binary.
All three hand answers, signed endpoint actions, physical/ground equilibrium,
MPC closure and fixed directions pass: +10 N -> +0.1 mm, -20 N -> -0.1 mm,
then +10 N -> +0.1 mm. Parent's additional 18-increment check has maximum
table-law / ground-balance residual 1.78e-15 / 7.11e-15 N. No residual, sign
criterion, stiffness or geometry was relaxed to obtain this result. The
SPRING2 packet remains failed; its source diagnosis is an inference and no
pinned binary was patched.

Engineering result unlocked: a built-in signed unilateral scalar carrier
that opens and recloses across reversal, with verified endpoint RF meaning.
The next task is a bounded two-moving-body nested relative-coordinate MPC
fixture; it stops when complete physical-body transfer and its known answers
are verified or a specific incompatibility is exposed. This method bridge
retains the old physical projection equations and tests the newly introduced
relative layer. It provides no fresh frame run authority. Actual six-case
corner demands, applicable floor support and complete corner resistance
evidence remain pending.


## Exact-stick constraint representation at the frozen floor points

The [floor constraint expressibility audit](current-floor-stick-constraint-audit-attempt01/README.md)
expands all 200 tangential rows onto 800 unconstrained physical solid DOFs.
Their rank is 200. A distinct-pivot representation reconstructs every
original source row within 1.95e-16 coefficient residual and satisfies
the pinned manual's unique dependent-DOF rule. An admissible trial field
closes all original constraints within 2.92e-16. This avoids the illegal
approach of directly fixing an already dependent projection ghost.

Engineering result unlocked: an exact geometric representation for a
conditional all-bearing stick branch, preserving every source floor point.
Existing finite tangential springs are not automatically exact stick. No
frame deck or native solve is produced by the audit. Native constraint
reaction recovery, compatible positive normal bearing and history/recontact
remain unverified; no fixed-reference counterexample is dismissed. A native
method check must settle force transfer/reaction output before frame use.


## Bounded applicability work after the native scalar-law pass

Primary deliverable remains complete BG001/BG003/BG045 left outer corner
path under source-case demands; unchanged original LEG/FLOOR-RUNNER
resistance evidence remains separate and reusable.

| Current task | Engineering result unlocked | Stop condition |
| --- | --- | --- |
| Two-moving-body nested relative-coordinate SPRINGA fixture | Correct equal/opposite force recovery on both physical bodies through existing projection ghosts plus new relative MPC | Agent stops at inspectable source/deck/assessor; parent freezes, independently checks authored inputs and owns any separately scoped single native run; stop on any method discrepancy |
| Exact floor MPC/reaction fixture | Tangential reaction recovery when a physical pivot DOF is constrained through a grounded reference, including applied load on that dependent DOF | Agent stops at inspectable source/deck/assessor; parent freezes and checks it before any separately scoped single native run; stop if native output cannot establish force closure |

These tasks test specific changed native behaviors; they are not broad cold
reviews or a solver-port campaign. Parent review of agent-authored fixtures
can provide the focused independent input check without another handoff
cycle. A fixture result cannot waive frame readiness or close material,
product, compatibility, floor-history or complete-joint gates. Fresh frame
inputs require their own assembled/audited mechanics scope and parent run
authority; exhausted C11 controls are not extended by these coupon tasks.


## Nested moving-body transfer and geometric-linear iteration verified

The [relative-coordinate fixture](current-springa-relative-coordinate-fixture-attempt01/README.md)
passed its single scoped native run. Existing projection ghosts plus
`Q=u_second-u_first` with positive unilateral table law transfer equal and
opposite forces to both moving bodies and close each body. Opening and
reclosing hand answers pass. Parent independently checks all 18 printed
increments: maximum body residual 4.01e-6 N, physical global residual zero.
The numerical SPRINGA ground is explicitly excluded from physical balance.

The verified runtime also uses Newton iterations while geometric effects
are off under the frozen `NLGEOM,NLGEOM=NO` option sequence, preserving the
original small-deformation frame/body-audit assumption. The positive
relative coordinate leaves a closed-side tangent at the zero knot without
changing force law, preload or stiffness. A negative-coordinate/min law
would pick an initially zero tangent in the pinned interval lookup.

Engineering result unlocked: source-owned unilateral carrier assembly with
verified nested-MPC physical transfer and stable initial closed-side tangent.
Luna now prepares a bounded input-only a12-rear frame adapter using these
stock native carriers and the exact floor constraint representation. It
stops at source-bound deck/model/audit; no freeze, force solve or acceptance
is delegated. Exact floor reference RF interpretation remains a separate
small method check. Full-frame readiness remains false pending that mapping
and response-audit integration. No C12 authority or old-bolt resistance
requalification follows.


## Exact-floor reaction recovery verified; corner scope reaffirmed

The left outer corner assembly under evaluation is BG001 (post to exterior
spine), BG003 (spine/side/inner block through two continuous three-member
bolts), and BG045 (inner block to header). Its complete load path includes
member contact/bearing, lateral and axial bolt actions, splitting/net
sections, washer seats and onward transfer. The 92 introduced block axes
replace former ML24Z/SDS duties; they are distinct from the twelve original
LEG/FLOOR-RUNNER arrangements. Reuse unchanged baseline resistance methods
and evidence for those twelve. Reopen only an identified geometry, receiver,
hardware or demand difference; do not transfer historical case acceptance.

The [exact-floor method attempt01](current-exact-floor-mpc-fixture-attempt01/README.md)
ended before mechanics because the linear stiffness token `20` lacked a
real-data decimal point. It remains preserved as failed. The separate
[attempt02](current-exact-floor-mpc-fixture-attempt02/README.md) changes only
real-number formatting and its run identity, preserving numeric inputs and
hand answers. Its one authorized native launch returned zero. Both known
answers, Newton/geometrically-linear runtime, isolated spring forces and
physical body balance pass. Parent independently checked all twelve printed
increments: maximum RF error 5e-6 N and body-balance residual 3.56e-15 N.

Exactly one of the four predeclared reaction interpretations passes both
cases: `RF_REFERENCE_MINUS_DEPENDENT_CLOAD`. Raw reference RF is -0.5/-1 N;
after subtracting the respective applied dependent loads +6/-4 N, actual
floor x reactions are -6.5/+3 N. This is a source-load correction, not a
force fitted to residuals. Numerical SPRINGA grounds are excluded from
physical balance. For the transformed frame constraints, recover the
transferred load from `(S^-1)^T F_pivot` and restore original row ownership.
The adapter must retain raw output and this explicit source correction.

Engineering result unlocked: exact stick reference-force recovery for the
verified small compression-bearing model. Luna's next deliverable remains
an input-only source-bound a12-rear adapter; its stop condition is an
inspectable deck, model and mapping audit. Whole-frame response recovery and
positive-bearing compatibility must still pass before a scoped frame run
can produce usable corner demands. No new frame launch is authorized by
this coupon result. Minimum outstanding mechanical input is the signed
current-frame corner actions with compatible contact states and verified
body/global transfer. Applicable hardware/material and washer/splitting
exceptions remain explicit conditional checks, not accepted capacities.


## Current frame input preparation and bounded response work

Parent source inspection found and returned three draft adapter issues for
correction before native use: material orientation overrides were bypassed;
the relative-coordinate audit did not handle omitted zero components; the
new response needed an explicit schema. Parent's separate
[current serialized-input checker](current-springa-parent-input-audit-attempt01/README.md)
also checks actual emitted floor coefficients and their applied-load
transfer, rather than relying only on full-precision algebra. No input pass
or frame readiness is claimed before outputs exist and that checker runs.

Luna prepares a response auditor using existing physical ownership, force
rounding and body/global wrench methods. Its stop condition is implementation
and verification on passed native method fixtures, with no native launch.
One additional input-only two-reference fixture addresses the specific
nonidentity matrix/permutation force-recovery behavior required by the exact
floor representation; it does not reopen general contact research. All work
is a dependency of current corner demands. No original LEG/FLOOR-RUNNER
resistance qualification or panel study is restarted.


## Source floor force/moment ownership verified

Parent independently checked all 200 original source tangent rows against
their physical master-node reactions and recorded floor-point/tangent
owners. Each unit reference channel preserves force and moment, with
maximum errors 1.82e-13 and 2.27e-10 mm per unit force. The reproducible
[parent input-audit packet](current-springa-parent-input-audit-attempt01/README.md)
records this source-only result. Its serialized-deck checker also verifies
reference-transfer coefficients, emitted CLOAD corrections and every
reference channel's physical wrench; no serialized pass is claimed before
the adapter emits its files. No corner forces, floor qualification or new
frame launch follows from this algebra check.


## Nonidentity floor equation reaction map verified natively

The [transformed-reaction method coupon](current-transformed-floor-reaction-fixture-attempt01/README.md)
passed its single scoped stock 2.23 launch, returned zero and reproduced both
predeclared known answers. Its nonidentity matrix and reversed source-row/
physical-pivot orders recover original-row reactions [-11.25,+7.75] and
[+6,-9] N. Those reconstruct physical support forces [-6.5,+3] and
[+2.25,-5.25] N and preserve the source/physical yaw moments -300/+525 Nmm.
The transformed source-load subtraction and row permutation are now observed
native behavior, not an extrapolation solely from the scalar coupon.

Parent independently checked every twelve printed increments: maximum RF
and body residual 5e-6 N; maximum source/physical/global yaw residual
5.69e-13 Nmm. This closes the bounded force-output-method question. It does
not close frame floor-bearing compatibility, stiffness/engagement
applicability, 50-body equilibrium or six-case corner demands. The frame
input adapter and new physical response auditor remain the next bounded
deliverables; no C12 or complete-joint acceptance follows.


## Frame builder load representation identified

The first corrected fresh assembly stopped before emission because its raw
builder load-node map differs from the frozen C11 deck's physical load map.
This is a representation dependency: the original
`freeze_trial` resets `structure.loads` from the freshly compiled
`physical_external_loads` before configuring trial springs. Panel attachment
slave loads are expanded onto physical C3D20 nodes by the existing
`_equation_load_expander`/`_record_panel_loads` virtual-work mapping.

The adapter will use that existing normalization, compare fresh body and
global physical load maps to the pinned source input, and independently
verify that raw builder loads expand to the same map before emission. Its
source-load reaction correction then uses the actual serialized physical
CLOADs. No source case load is borrowed from the rejected C11 response; no
nodal-load difference is waived without the explicit transfer proof. A
frame input pass remains pending this reassembly and parent serialized audit.


## Corrected current frame input and independent serialized check passed

The one source-bound a12-rear [adapter](current-springa-frame-input-adapter-attempt01/README.md)
has emitted its model, deck and audit. The freshly normalized physical loads
match the pinned source input, while raw attachment loads expand to that map
with maximum nodal discrepancy 1.14e-13 N. It retains 1,903 C3D20 solids,
1,292 SPRINGA carriers and 348 unchanged bilateral SPRING2 components.
All 218 material/orientation/section cards match the source deck.

Parent's independent serialized audit passes: 50 bodies and source ownership/
loads preserved; exact floor reconstruction error 7.54e-14; reference-transfer
error 4.76e-14; unit channel force/moment errors 3.61e-13 / 4.45e-10 mm;
emitted-load correction discrepancy zero; all 21,998 pivots distinct and
unfixed. Model and deck digests are respectively
`61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8` and
`11674a8b50f0c292e7e03288697afa7bbfaebc0f3db5f49b0439c125a5ab9a4c`.

Next engineering gate: the source-bound physical-force auditor must pass its
actual native fixture replays and exact model/deck contract. Parent then owns
a fresh, one-launch diagnostic freeze/review; this input pass itself supplies
no run authority, frame forces or joint acceptance. The complete corner
exporter is being prepared in parallel for verified current results only.
Original LEG/FLOOR-RUNNER resistance evidence remains separate and reused.


## Corner priority confirmed; first current-frame diagnostic launched

BG001/BG003/BG045 are the left outer corner-block path: post/exterior spine,
spine/side/inner block, and inner block/header. The 92 new block-attachment
axes replace former angle/SDS duties. The twelve original LEG/FLOOR-RUNNER
arrangements remain a separate evidence class; their unchanged resistance
calculations are reused. A retained arrangement is reopened only for a named
changed geometry, receiver, hardware or current demand issue.

The final physical-response auditor passed 42 printed method-fixture states
and a near-zero SPRINGA endpoint-length arithmetic witness. Parent froze the
one a12-rear diagnostic and independently rechecked its actual serialized
inputs. Deck SHA remains `11674a8b50f0c292e7e03288697afa7bbfaebc0f3db5f49b0439c125a5ab9a4c`;
frozen model SHA is `58daa4d557c929b83fdffd989ba53ac75b82f6c87f3bc848cb1af28562a0e8fe`.
The standard serializer changes only diagnostic scope and truthful
always-active bilateral metadata. The source geometry, constitutive inputs,
loads and exact-floor reaction mappings are preserved.

[Attempt packet](current-springa-frame-a12-rear-attempt01/README.md) owns exactly
one 240-second/4-GiB serialized launch. Every printed state must pass physical
law, MPC, all-positive floor normal, global and all-50-body balance gates
before any corner force is usable. This remains a zero-gap, zero-accessory,
all-bearing exact-stick diagnostic; it supplies no joint acceptance or
historical pass transfer. The complete corner exporter is being prepared for
source-bound verified outputs. Minimum next dependency is a passing current
response; splitting, washer, bearing/contact and onward-transfer checks still
require their recorded applicable material/hardware and compatibility inputs.


## Current-frame attempt terminal: no accepted increment

The one scoped a12-rear launch ended with return code 201 after 51.43 seconds,
six failed cutbacks and accepted time zero. No usable corner forces were
gained. The same normalized residual/correction pattern persists as the
load increment is quartered, so smaller increments alone are not an evidenced
remedy. Rejected best-iterate FRD results are not promoted to demands.
This does not establish physical failure of the corner blocks.

The native slot is idle, the launch budget is consumed, and there is no
automatic retry. A bounded read-only pinned-manual/source and primary-online
diagnosis will identify at most two mechanics-preserving next methods. The
complete corner exporter remains blocked on precisely a passing current,
source-bound response; no blanket original LEG/FLOOR-RUNNER resistance work
was reopened.


## Native iteration issue resolved; exact remaining floor compatibility issue

The fresh controlled-iteration a12-rear diagnostic returned zero in 45.06
seconds and reached full load in seven accepted increments. The first took
13 iterations; later increments took two. No geometry, material, source load,
connection law, FIELD criterion or physical closure criterion changed. The
documented time controls delayed the premature residual-growth cutoff.

The strict response audit correctly rejected this all-bearing support branch.
A source-bound diagnostic screen of all 100 nonlinear normals at all seven
printed states found 17 strictly positive cells and 83 strictly separating
cells, with the same set throughout. Exact tangent restraint at those 83 open
cells is incompatible with the specified bearing-dependent no-slip law.
No corner demand is usable and no physical corner failure is established.

The next bounded engineering result is one conditional selected-bearing
branch: retain every normal law and physical input, impose exact zero tangent
motion only at the 17 proposed bearing cells, and release the 83 others.
This is a proposed state from a rejected branch, not accepted support evidence.
Fresh input/algebra and physical-response checks must prove normal/tangent
compatibility and all-body/global balance before any BG001/BG003/BG045 action
is recovered. There is no general recontact or uniqueness claim and no
unbounded native mask iteration. The original LEG/FLOOR-RUNNER resistance
work stays separate; any later affected demand is a concrete demand-only
check using unchanged resistance where applicable.


## Selected-bearing subset independently expressible; response not yet evaluated

Parent independently derived the proposed 17-cell / 34-row restraint subset
from the original source equations. Rank is 34; singular ratio is 0.158114;
pivot condition is 11.6773; source/reference reconstruction residuals are
1.11e-16 / 2.78e-16. The independent actual-deck checker is prepared in
`current-springa-selected-floor-parent-input-audit-attempt01/`. These are input
algebra results, not accepted floor reactions or corner demands.

The input adapter and response auditor have agreed the source-row, physical
pivot, reference and active/inactive map contract. Their bounded stop is one
prepared branch and a checked response method; parent still owns fresh frozen
inputs, readiness, one serialized run and final validation. Every normal,
active tangent, released tangent and physical-body/global balance must pass.
No geometry change, original bolt resistance restart or general recontact
solver is authorized by this record. BG001/BG003/BG045 remain the primary
complete corner path, and all six cases and sensitivities remain outstanding.


## Owner corner priority confirmed; two conditional support proposals rejected

BG001 (post/exterior spine), BG003 (spine/side/inner block through two
continuous three-member bolts), and BG045 (inner block/header) are the left
outer corner-block assembly: six physical bolts, eight lateral planes and six
axial ties. The 92 new block-attachment axes replace former ML24Z/SDS duties;
the twelve original LEG/FLOOR-RUNNER arrangements are separate. Their unchanged
resistance evidence is reused. No original resistance work was reopened and
no historical frame-case pass transferred. The complete corner deliverable
includes contact/member bearing, lateral and axial bolt groups, splitting,
washer seats and onward transfer, rather than isolated bolt capacities.

The 17-cell proposal reached full load (native return 0, seven printed states),
but its strict floor audit rejected inactive SPR1185. All 100 normal laws
were independently screened at every state: 23 cells bear and 77 separate,
with the same inventory throughout. A fresh input-only 23-cell proposal
passed the parent actual-deck audit and three replayed method fixtures.
Its 46 exact tangent constraints reproduce the source equations within
7.32e-14; source unit-wrench errors are 1.70e-13 N / 2.08e-10 Nmm.
Geometry, loads, laws, materials and the 92+12+66 axis classes are preserved.

Parent froze and ran that single proposal in
`current-springa-selected-floor-a12-rear-attempt02/`: native return 0,
59.56 seconds, confirmed terminal, full factor 1. Its strict response audit
rejected inactive SPR1215 at time 0.1. Diagnostic screening of all 100 normal
laws at all seven states gives 25 bearing / 75 separated cells, adding
`floor_base_floor_right_26` and `floor_base_floor_right_28`, losing none.
This diagnoses an incompatible prescribed bearing set; it does not establish
physical corner failure or usable corner forces. No response is promoted, no
third native mask run is authorized by this record, and tolerances remain
0.1 N / 2 Nmm. The two terminal assessments and diagnostic screens preserve
the exact rejection and file pins.

Minimum calculation dependency: a compatible source-bound frame support
response, with signed corner/onward interface actions and all-body/global
closure. Then reuse the existing conditional NDS/washer/net-section arithmetic
with those concurrent forces. Accepted corner resistance additionally needs
applicable member design strengths/grain/service assumptions, washer/bolt
compatibility and an applicable splitting treatment for the actual topology
(in particular BG003's oblique middle-member end and orthogonal bore families).
These are explicit conditional limits, not a new inspection or blanket external
sign-off prerequisite. All six cases and stiffness/engagement sensitivities
remain outstanding; solver convergence alone closes none of those gates.


## One current conditional response closes the numerical demand gate

The freshly frozen 25-bearing / 75-separated a12-rear proposal in
`current-springa-selected-floor-a12-rear-attempt03/` completed with native
return 0 in 60.37 seconds, confirmed terminal, seven printed increments and
full load factor 1. All source MPC, 1,292 SPRINGA, 348 bilateral, 100 floor
normal and 50 active / 150 inactive tangent checks pass at every increment.
The prescribed bearing set remains compatible. Raw and rounding-interval
all-body/global equilibrium pass without changed tolerances.

The independent parent sums also pass all 50 physical bodies and the global
frame at all seven increments. Maximum raw force residual is 0.000813895 N;
maximum raw moment residual is 0.877489569 Nmm, within 0.1 N / 2 Nmm. Numerical
ground reactions are excluded. Frozen model/deck/live-source verification
passes after terminal assessment. Response SHA-256 is
`892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274`.

The immutable auditor passed its calculation but its CLI could not encode
NumPy Boolean values as JSON. The separately recorded parent writer converts
only NumPy scalars to Python scalar values, uses strict JSON, and reruns the
unchanged pinned audit. No native run, threshold, mechanical computation,
frozen source or response gate was changed for serialization. The independent
parent audit reads the serialized response and passes.

Parent adopts this response only as conditional numerical case forces:
ring A, Hillman axial proxy ratio 1, zero bolt gap, zero accessories and an
unverified no-slip floor assumption on the reviewed geometry. It is not a
joint resistance pass, six-case envelope, sensitivity closure or floor/build
qualification. BG001/BG003/BG045 complete-path export and applicable screens
are the next immediate result. The 92 new axes remain separate from the
twelve original LEG/FLOOR-RUNNER arrangements; unchanged original resistance
evidence is reused. The remaining five cases need their own compatible
support responses, and stiffness/engagement/accessory exceptions stay open.


## Complete left corner numerical path exported for the first conditional case

`current-corner-native-demand-export-attempt03/corner-demand-report.json`
now reports all 338 owned interfaces, including incoming/onward transfer,
232 contact rows and twelve outer head/nut washer-seat records. All five
corner members close independently at each of seven increments; worst local
raw residual is 0.000696 N / 0.4754 Nmm. Parent additionally checked exact
signed exported vectors against the passed native response, complete source
inventory, all six physical bolts / eight planes / six ties, and all four
local released zero-action floor groups at every increment.

At full load in this conditional a12-rear scenario:

| Group | Separate lateral-plane resultant magnitudes (N) | Axial tie magnitudes, one per physical bolt (N) |
|---|---|---|
| BG001 post/spine | 301.657; 335.061 | 64.966; 18.473 |
| BG003 spine/side/inner block | bolt 1: 483.948 / 65.913; bolt 2: 239.230 / 86.983 | 95.967; 43.508 |
| BG045 inner block/header | 90.116; 24.946 | 119.343; 19.882 |

These magnitudes summarize separate signed vectors preserved in the report.
They are not independent capacities, a force envelope or joint acceptance.
BG003's unequal outer-plane actions prevent blindly applying its earlier
equal-outer-action double-shear reference. Maximum modeled full-annulus
washer pressure is approximately 0.536 MPa; this is a geometry conversion,
not a washer steel/pull-through or wood resistance pass. Splitting/net
section work still requires applicable methods and actual section actions,
not the whole-body equilibrium resultants.

The remaining five fresh case inputs and the source load register are in
progress. Each case needs its own compatible support response; no force or
bearing-mask transfer from this first case is allowed. The conditional
resistance comparison reuses reviewed original methods and keeps genuine
applicability exceptions explicit. All original LEG/FLOOR-RUNNER resistance
evidence remains separate and unchanged.


## Six fresh source cases registered; five native inputs in progress

`current-six-case-source-load-register-attempt01/register.json` contains fresh
source assemblies for a12-rear, a12-forward, a12-left, k12-right, k12-rear and
a1-rear, with a common non-load geometry/carrier signature and exact per-case
load/wrench maps. Parent checked all recorded source hashes and independently
recomputed the hold-standoff moments for every case. Register SHA-256 is
`7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508`.
Only a12-rear has a passed conditional native response. The five remaining
inputs are being prepared in `current-springa-six-case-frame-input-adapter-attempt01/`,
with no native/freeze authority delegated and no bearing-mask transfer.

Final corner report SHA-256 is
`812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`.
Parent exact signed-force/inventory audit passes for that final report at all
seven increments. A stale washer-source unit-action caveat was corrected
only in the fresh export projection; forces and original source evidence
were unchanged. Applicable component resistance arithmetic is being recorded
separately; it remains conditional and cannot supply a combined joint pass.


## First resistance comparability screen and five audited case inputs

`current-corner-a12-conditional-resistance-screen-attempt01/` is complete and
its pinned producer replay passes. For the passed conditional a12-rear
response, BG001's separate Y/Z component/reference ratios are
0.266/0.328 and 0.375/0.325; BG045's are 0.222/0.0369 and
0.0604/0.0151. These are necessary individual component screens, not
combined-action DCRs, adjusted design capacities or joint passes. BG003 has
no applicable symmetric double-shear comparison: paired plane magnitudes
differ by 7.342 and 2.750, with non-collinear actions. Four eligible
base-post/header washer references have conditional ratios 0.0192–0.1243;
block seats are not given a perpendicular-grain reference. Splitting,
section actions, adjustment/interaction and bolt/washer compatibility stay
explicitly unresolved. No original resistance check was reopened.

All five remaining fresh source-bound frame inputs now pass independent
parent serialized-input audits in
`current-springa-six-case-frame-input-adapter-attempt01/`. Their load maps
match the fresh register; material/orientation/geometry are preserved.
No a12-rear bearing mask or response is transferred.

The separately frozen forward all-bearing diagnostic completed at full
load with native return 0 in 40.85 seconds. Its source-bound normal-law
screen gives 35 bearing / 65 separated cells at each of seven increments,
so all-bearing tangent restraint is rejected and its forces are withheld.
One forward-specific 35-cell/70-row proposal is being prepared. The left
case all-bearing diagnostic is independently frozen/audited and running
under parent serialized control. One conditional six-case response is
usable; the other five response/support pairs and sensitivities remain open.


## September 30: five diagnostic runs complete; forward selected branch underway

All five remaining case-bound all-bearing native diagnostics reached full
load with confirmed terminal execution. The summary is
`current-five-case-native-diagnostic-register-attempt01/register.json`.
Their forces remain withheld because tangent restraints include separated
cells. Stable positive-normal counts are forward 35, left 10, K12-right 10,
K12-rear 16 and A1-rear 44. K12-rear has one first-increment cell whose
printed displacement interval is inconclusive; a bounded zero-SPC evidence
check is in progress, without relaxing physical criteria.

The forward-specific 35-bearing/65-released proposal passed independent
serialized-deck and frozen case-context checks. It is now under one
parent-owned serialized native run in
`current-springa-selected-floor-a12-forward-attempt01/`. Its frozen model
SHA-256 is `50edee6194d3abdb758e8e7eb17f361b10cae7fc839dcedfa9f24f070d25324b`;
the deck is `401930f909d503e388a68f3eade5ebfaa1e228d5bc48712a217e170fe8bef553`.
The stop condition is terminal execution followed by strict support,
carrier-law and all-50-body/global balance checks at every increment.
Until those pass, only the earlier conditional a12-rear corner response is
usable. No mask, force or acceptance is transferred between cases.

BG001/BG003/BG045 are the left outer corner assembly: post to spine,
spine/side/inner block, then inner block to header. The six physical bolts,
eight lateral planes and six axial ties form one complete path. The 92 new
block axes remain separate from the twelve original LEG/FLOOR-RUNNER
arrangements. Their unchanged resistance evidence is reused; none was
reopened by this work. Remaining joint dependencies include the response
envelope, unequal three-member BG003 action compatibility, timber splitting
and section actions, and actual bolt/washer/grain compatibility.


### Forward selected proposal terminal result

The forward 35-bearing proposal reached full load with native return 0 in
43.06 seconds and confirmed terminal execution. Its strict case-bound
response audit rejected inactive normal SPR1026: strict separation with
zero endpoint RF was not established. Forward corner forces are withheld;
this is a support-pattern mismatch, not a demonstrated physical joint
failure. `current-springa-selected-floor-a12-forward-attempt01/parent-terminal-assessment.json`
records the exact rejection. A bounded fresh normal-law screen is identifying
changed support states; no automatic iteration or geometry change is authorized.
The usable conditional case count remains one, and the native slot is idle.


### Exact forward support mismatch localized

Parent read-only diagnosis binds the terminal DAT and confirms SPR1026,
`floor_base_floor_left_1`, is strictly bearing at all seven increments despite
being designated inactive. Its final normal force is 9.570275 N with a
0.0000005 N printed-force radius; projected closing displacement is
0.00005257167 mm with a 0.000000500005 mm printed-displacement radius.
This is not merely an ambiguous zero token. Evidence is
`current-springa-selected-floor-a12-forward-attempt01/parent-offending-cell-diagnosis.json`.
The full normal-only diagnostic screen reports a stable 31 bearing / 69
separated inventory; that remains diagnostic, not a validated replacement
branch. A future proposal must explicitly record support-stage lineage and
pass complete compatibility again. No corner force adoption follows here.


### Forward mask changes and bounded follow-on work

The fresh selected-floor normal-law screen pins terminal output and records
31 strictly bearing / 69 strictly separated / zero ambiguous cells at all
seven increments. Relative to the proposed 35-cell mask, six selected cells
became separated and two released cells became bearing: left runner cell 1
and right runner cell 7. This eight-cell change must be explicitly carried
in any next proposal; a convergence flag cannot replace complementarity.

The source-bound screen is
`current-springa-a12-forward-selected-floor-screen-attempt01/screen.json`.
Parent verified its source pins and separately recovered SPR1026's positive
force at every increment. Fresh work is bounded to a left-case input
proposal from that case's own ten-cell diagnostic, the BG003 asymmetric-action
applicability check, and a representation-only scientific-zero U-token proof.
The zero-token investigation must preserve nonzero-U and all-RF intervals,
source/method guards and physical criteria. It cannot fix the forward mask's
real contact changes or justify accepting its corner forces.


### Independent forward native normal replay

`current-forward-floor-parent-interval-audit-attempt01/check.py` independently
parses the recorded native U/RF tokens, emitted node coordinates, and source
projection/normal bindings without importing any FEA recovery kernel. Its
`audit.json` passes all 700 cell/increment classifications, reproducing the
31 positive / 69 strictly separated / zero ambiguous pattern. It pins the
exact model/deck/DAT/screen and its own source. This strengthens the support
mismatch diagnosis only; it does not promote rejected forces or establish
any joint resistance or floor qualification.


### BG003 unequal-action method boundary and conditional references

`current-bg003-unequal-action-applicability-attempt01/` is complete and its
producer replay and parent independent Mode Is arithmetic pass. Current
NDS-2024 single/symmetric-double yield provisions and unequal-side-length
rules do not supply a complete resistance comparison for the observed
unequal, non-collinear three-member actions. The historical 2018 asymmetric
clause also assumed equivalent side-member loads. The four separate
outer-receiver bearing-mode reference ratios are 0.2754, 0.0313, 0.1533 and
0.0434, under the explicit DF-L G=0.50, full-shank quarter-inch, proposed
grain and conservative effective-length scenario. These are component
reference comparisons, not adjusted complete-joint DCRs or passes; they are
not summed. Coupled middle-member action, dowel bending across both planes,
axial/lateral interaction, group adjustment and splitting remain separate
unresolved checks. The current consolidated AWC errata was considered;
its sub-quarter-inch KD correction does not alter this quarter-inch term.
No original LEG/FLOOR-RUNNER resistance was reopened and geometry is unchanged.


### September 30: left and K12-right selected diagnostics terminal

Parent independently audited and froze the case-specific left and K12-right
10-bearing/90-released proposals. The left native execution is terminal with
return 0 in 51.83 seconds; strict response audit rejects inactive SPR1269,
`floor_base_post_center_right_2`. Parent source-bound diagnosis finds its
positive normal force rises from 0.9737118 N to 9.737118 N; its final closing
coordinate is 0.00007317606 mm ± 0.000000500005 mm. This is a real mask
mismatch, not a printed-zero ambiguity. K12-right similarly reached full
load with confirmed terminal return 0 in 52.33 seconds, but its strict audit
rejects inactive SPR1257. Both native packets contain exact terminal
assessments and withhold corner forces pending complete normal-state screens.
No physical corner failure is inferred and unchanged original bolt
resistance is not reopened.

The A1-rear 44-bearing/56-released input passed source-bound input checks and
is under parent-owned frozen readiness/execution. The forward 31-bearing
proposal is prepared from the explicit selected-stage screen projection,
which preserves both original all-bearing physics authority and its direct
rejected selected35 output lineage. It is not a transferred pass or force
source. Neither prepared input implies support compatibility or joint
acceptance. The six-case response envelope and sensitivities remain open.


### September 30: six-case response register and K12-rear terminal exception

The [current six-case corner response register](current-six-case-corner-response-register-attempt01/README.md)
authenticates all six terminal executions and keeps the usable-demand count
at one conditional rear case. K12-rear's source-bound 16-bearing proposal
completed in 53.19 seconds, return zero; the validated zero-U representation
audit rejects inactive SPR1074. Exact model/deck/DAT and exception pins are
in its parent terminal assessment. No forces from that response are adopted.

The bounded forward31 diagnosis shows selected SPR1026 is strictly separated
at every increment, not interval-ambiguous: its full-load projected q is
about −0.02885715 mm, native table force zero. The observed 37-positive/
63-separated pattern is stable through seven increments and equals none
of the previous 35- or 31-cell patterns. It is not an adopted replacement
mask and does not trigger an automatic retry. A case-local reproducible
diagnosis is being recorded. Geometry, laws, criteria and unchanged original
LEG/FLOOR-RUNNER resistance remain preserved.


### Current actual-direction single-bolt lateral references

The [resultant-direction packet](current-corner-resultant-direction-single-shear-attempt01/README.md)
now evaluates the actual a12-rear lateral direction for both connected
members at each BG001 and BG045 bolt. It replaces the need to infer a
lateral comparison by combining separate coordinate components. Under the
existing smooth full-body quarter-inch, Fyb 45,000 psi, zero-gap, proposed
grain and Fe 5,600/4,450 psi endpoint scenarios, all six yield modes are
retained and Mode IV governs all four bolts. BG001 ratios are 0.42363 and
0.49082 against 712.070 and 682.661 N references. BG045 ratios are 0.22468
and 0.06230 against 401.080 and 400.416 N after the existing conditional
Ceg=0.67 once. They remain individual-bolt lateral reference comparisons,
not adjusted design DCRs, group/axial interaction checks or complete-joint
passes. BG003 remains a coupled unequal, non-collinear three-member problem.

Parent independently recomputed force norms, proposed grain angles,
Hankinson Fe interpolation, reduction angle and Mode IV arithmetic without
importing the yield helpers. The parent audit binds final screen SHA-256
`d3b1ce4448ea90929b6410424f0212d86b4caee5130bca7c93209e06ad5b3c10`.
The producer replay and its final checksum manifest pass. All four actual
axial tie vectors/magnitudes remain separate; no missing field is defaulted
to zero. Twelve original LEG/FLOOR-RUNNER arrangements remain out of scope.


### A1-rear now passes its conditional response and independent body sums

The source-bound A1-rear 46-bearing/54-released proposal ran once and is
terminal, return zero in 40.10 seconds. All seven increments through full
load pass the pinned zero-U response method's support, MPC, spring-law and
physical balance gates. The immutable auditor's CLI failed only while
serializing a NumPy boolean after mechanics checks had completed. The new
parent writer converts NumPy scalar types to native JSON types and reruns
the same unchanged audit; no native rerun, criterion or force change occurs.

Response SHA-256 is `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c`.
Parent independently summed all 50 physical bodies and global force/moment
resultants at every increment without importing the recovery balance kernel.
Maximum raw residuals are 0.0002213 N and 0.159621 Nmm, within the frozen
0.1 N/2 Nmm criteria. The exact parent terminal assessment permits this
conditional case's forces, not joint resistance or a historical pass.

There are now two usable conditional physical responses and one completed
signed corner export; A1's complete BG001/BG003/BG045 corner projection is
in progress. Four remaining load cases and whole-frame engagement/stiffness
sensitivity still require compatible audited responses. The twelve original
LEG/FLOOR-RUNNER resistance arrangements remain separately preserved.


### September 30: two complete corner exports and the next bounded exception

A1-rear's source-bound signed corner export is complete, report SHA-256
`2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce`.
The parent independently checks all 338 interfaces across seven increments,
including native vectors, two active corrected floor-tangent groups and two
released zero groups, six physical bolts/eight planes/six ties, and the
separate twelve retained arrangements. The [two-case comparison](current-corner-two-case-demand-comparison-attempt01/README.md)
records each signed action; maximum lateral-plane resultants for a12-rear / a1-rear
are BG001 335.061 / 146.049 N, BG003 483.948 / 137.900 N and BG045
90.116 / 87.077 N. Some BG003 directions reverse, so resistance checks cannot
inherit the other case's loaded ends or directions. These are demands,
not accepted capacities or the six-case envelope.

The parent froze and ran one K12-rear 21-bearing/79-released proposal, derived
from that case's own complete normal-interval diagnostic. It completed in
53.68 seconds, native return zero, and the unchanged strict 711 response
method rejects inactive SPR1104 as not strictly separated with zero endpoint
RF. The exact assessment in `current-springa-selected-floor-k12-rear-attempt02/`
withholds all corner forces and records no physical failure. No automatic
mask retry follows; a bounded source-bound diagnosis is in progress.
The [six-case register](current-six-case-corner-response-register-attempt01/README.md)
now records two complete usable corner exports and four rejected case responses.

The [independent BG001 reference audit](current-bg001-geometry-wood-parent-audit-attempt01/README.md)
verifies the existing recorded angle/end-distance arithmetic and conditional
parallel-component row/net references. Geometry-scaled lateral comparisons
are 0.60184 and 0.69728, with mixed-direction Cg unapplied. Unadjusted
parallel-component row comparisons are 0.17301 spine / 0.21626 post; the
Chapter 5 glulam Cvr factor has no supported application to this solid-sawn
scenario and is omitted. Mixed-action splitting, adjusted resistance,
complete contact/member path, washers/axial interactions and coupled BG003
continuous-bolt behavior remain open. Each active follow-up is bounded to
these corner dependencies; unchanged original LEG/FLOOR-RUNNER resistance
is not reopened. Geometry, loads, criteria and native controls are preserved.

`current-knee-joint-check-summary.md` is retained at its currently pinned
state because the reproducible A1 projection freezes that legacy context
source. This later checkpoint and the current response register carry the
new results without invalidating the historical evidence pin.


### Corner axial/washer components and bounded K12-rear diagnosis

The [axial tie/seat screen](current-corner-axial-tie-seat-screen-attempt01/README.md)
and fresh parent independent arithmetic/vector audit cover all six full-load
a12-rear ties and twelve end seats. Conditional minimum-annulus DF-L No. 2
perpendicular-bearing comparisons for four base-post/header seats are
0.02007–0.12964. These are unadjusted component references on ideal supported
annuli, not washer plate response or accepted pressure/capacity. Candidate
blocks have a distinct elastic-only material map with no strength grade;
the separate DF-L No. 2 what-if comparison does not assign that grade.
BG045 block seats load parallel to proposed grain, so Fc-perpendicular is
inapplicable. The hypothetical Grade 5 bolt Fy×At reference is 13.014 kN,
component ratios 0.00142–0.00917; bolt interaction, nut/thread engagement,
washer spreading/bending and exact supported areas remain unresolved.
The final screen hash is
`cae5c67d1166205aaa442c8ae889c95245162b7d1569cf264b13bc260d712ac4`.

The [K12-rear attempt02 interval diagnosis](current-springa-k12-rear-selected-floor-normal-interval-diagnostic-attempt01/README.md)
classifies all 100 normals at all seven increments with no ambiguity: stable
23 bearing/77 separated, versus the proposed 21/79. Only inactive SPR1104
and SPR1110 bear, both strictly at every state; no selected cell separates.
Parent rehashed all 19 source pins and exact producer/report pins. This is a
real support-branch mismatch, not a tolerance or printed-zero problem.
Parent selected one fresh 23-cell input proposal for preparation, with no
native authority from the diagnosis itself or automatic further iteration.

The [BG003 continuous-dowel note](current-bg003-continuous-dowel-method-candidate-attempt01/README.md)
records a research method family and the exact unvalidated biaxial/material-law
gap. It is not an implementation queue or accepted resistance method.
Conditional calculations can use clearly specified hypotheses without claiming
inspected material; physical qualification is a separate claim boundary.


### Owner corner-block priority and latest case-specific results, September 30

BG001/BG003/BG045 are the complete left outer corner-block assembly: post to
exterior spine, spine/side/inner block, and inner block to header. Its six
new bolts include eight lateral shear planes, six axial ties and twelve
washer seats. They belong to the 92 new block-attachment axes replacing
ML24Z/SDS duties. The twelve original LEG/FLOOR-RUNNER arrangements retain
their separate baseline resistance evidence. Reopen a retained arrangement
only for an identified changed receiver, geometry, hardware or demand;
unchanged resistance work is reused and historical case passes do not transfer.

Two responses, A12-rear and A1-rear, have independent all-body/global audits
and complete signed corner exports. Their [comparison](current-corner-two-case-demand-comparison-attempt01/README.md)
now includes all sixteen primary contact cells at all seven increments.
At full load A12-rear has resolved post/spine compression while the
inner-block/header forces contain zero; A1-rear reverses those conditions.
A zero-containing force interval alone does not prove finite separation.
Maximum lateral plane demands are 335.061 N for BG001, 483.948 N for BG003,
and 90.116 N for BG045 across these two cases, not a six-case envelope.
The [A1 axial/seat screen](current-corner-a1-rear-axial-seat-screen-attempt01/README.md)
and its parent audit complete six ties/twelve seats. Individual post-2,
side-2 and header-2 ties exceed A12-rear despite smaller group maxima.
These remain conditional component references, not complete joint passes.

Four additional serialized native runs completed to full load with return
zero; all remain rejected and supply no adopted corner forces:

- K12-rear attempt03: its 23/77 floor set is strictly consistent at all seven
  states, but SPR489 fails the strict qghost/source output-interval check at
  factor 0.2 by 1.6344e-11 mm beyond its radius plus guard. Source projections
  pass; no tolerance waiver or geometry failure is inferred. See the
  [source-bound diagnosis](current-springa-selected-floor-k12-rear-qghost-diagnosis-attempt01/README.md).
- K12-right attempt02: inactive SPR1311 bears. The observed stable 11/89 set
  adds only right-leg cell 0 to the latest ten-cell input, without recurrence
  to either earlier ten-cell set. Parent rehashed all 52 diagnostic source
  pins and selected one fresh input preparation; no automatic native retry.
- A12-left attempt03: selected SPR1302 separates. The [700-row diagnosis](current-springa-a12-left-normal-interval-diagnostic-attempt02/README.md)
  confirms the local ten-to-eleven-to-ten set recurrence. Parent rehashed all
  46 sources. Repeating those masks is not a justified next step.
- A12-forward attempt03: selected SPR1050 fails strict bearing compatibility;
  the case-local set comparison is pending. No rejected force is exported.

The [BG003 middle-zone feasibility check](current-bg003-middle-zone-cut-feasibility-attempt01/README.md)
finds that two 44.45 mm geometrical halves do not establish independent bolt
segments or a simultaneous lower-bound resistance. Balancing each plane's
force over finite bearing depth leaves a midpoint moment without a proven
contact couple; axial tension also persists. This excludes that unsupported
shortcut, not the joint itself.

Minimum remaining evaluation dependencies are (1) four usable case responses
and bounded full-frame stiffness/engagement sensitivity, (2) a justified
continuous-bolt resistance treatment for BG003's unequal, non-collinear plane
actions plus axial tie, and (3) explicit block strength/grain hypotheses and
compatible bolt shank/root, washer support/bending and nut/thread engagement
inputs. Mixed-action splitting and the complete onward member-transfer checks
remain necessary. Conditional calculations may use labeled hypotheses;
missing physical/product evidence is not a demonstrated physical failure.
Reviewed geometry, load authority, strict criteria and native controls remain
unchanged. The goal remains active and the corner assembly is not accepted.


### Forward compatibility diagnosis completed

Parent independently rehashed all 170 sources of the
[A12-forward attempt03 diagnosis](current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/README.md).
All seven states classify 37 strictly bearing / 63 strictly separated, no
ambiguity. This stationary observed mask matches none of the three tested
forward inputs (35, 31, 37 cells); the latest 37-cell input shares 34 cells
with it. Selected SPR1050 separates throughout. No update-cycle or convergence
claim follows, and the rejected run supplies no adopted demands.
Parent independently audited and froze the source-bound K12-right eleven-cell
proposal for one serialized attempt03 run; terminal compatibility and all-body
balance still determine whether any forces are usable. No original leg/runner
resistance check or reviewed geometry was changed.

K12-right attempt03 completed in 51.48 seconds at full load with native return zero. The unchanged strict 711 response audit rejects selected SPR1311 as not strictly positive. Exact terminal assessment withholds forces. The full-set comparison is pending; no further mask update or native run is selected. Two usable signed corner cases remain.

[A1 BG001 lateral component references](current-bg001-a1-resultant-reference-attempt01/README.md) reuse unchanged reviewed resistance/geometry with A1 signed vectors. At actual grain angles 11.421/44.567 degrees, raw Mode IV references are 767.897/667.352 N and unadjusted comparisons 0.14181/0.21885. Parent independent source/Mode IV arithmetic passes; no loaded-end/group/splitting/axial interaction or joint acceptance follows.

[A1 BG001 signed geometry](current-bg001-a1-signed-geometry-attempt01/README.md) explicitly verifies the same loaded grain ends and changed cross-grain loaded edge at post bolt 2 in both receivers. Sampled listed edge minima are met. Recorded conditional interpolation yields group Cdelta 0.72537 and geometry-scaled comparisons 0.19550/0.30171; actual group row-alignment sine 0.50720 leaves Cg and mixed-direction splitting unresolved. No complete resistance or case-envelope acceptance follows.

The [K12-right attempt03 diagnosis](current-springa-k12-right-attempt03-normal-interval-diagnostic-attempt01/README.md) confirms an exact ten-to-eleven-to-ten recurrence for the two latest inputs, differing only at SPR1311. Parent rehashed all 65 sources and independently checked the 700-row partition and exact prior-set match. SPR1311 at full load has strictly separated gap [-0.0057160855,-0.0057160845] mm; this is not a printed-zero ambiguity. No further fixed-mask update is selected. A bounded current ideal-stick support-method investigation now covers both left and right cycles.
The [conditional BG001 stiffness input](current-a12-rear-bg001-seat-stiffness-variant-attempt01/README.md) changes only two runtime ties from 4670.054 to 2401.714 N/mm, using a documented uncalibrated local compliance scenario. Parent independently checked all eight JSON differences and two deck records. It is not yet native-ready; a dedicated override-aware input/method validator must preserve strict floor and all-body gates before a scoped response sensitivity run.


### Bounded SPR489 representation remedy under preparation

The pinned-source investigator traced SPR489's physical-point interpolation,
projection and qghost equations. The current replay reports tiny independent
coefficient removal by CalculiX 2.23 cascade.c; no selected-floor H/D equation
is in this dependency chain and no dependent-zero coefficient repair occurs.
At factor 0.2, the reported pruned/unpruned scalar difference is -1.2340e-11 mm,
versus a strict scalar interval overrun of 1.6344e-11 mm. This is a credible
partial numerical mechanism, not complete causal proof or a tolerance waiver.
A reproducible source-pinned trace is being prepared for parent verification.
The next candidate is a small known-answer direct scalar/interpolation
projection fixture that bypasses the intermediate projection cascade while
proving the same scalar q and owner action/reaction. Production input remains
unchanged and its response rejected. No native fixture is authorized until
parent reviews exact equations, analytic answer, pins and readiness.

The [independent ideal-stick hand-fixture audit](current-ideal-stick-hand-fixture-parent-audit-attempt01/README.md) exhaustively enumerates two tangent masks and two normal-law sectors in exact rational arithmetic. Both sector-consistent equilibria violate their own stick gate, including the zero-normal boundary in the inactive sector. This demonstrates that a generally convergent positive-normal mask update cannot be assumed. It does not prove that the full frame lacks another admissible branch, verify a new native algorithm, or demonstrate physical joint failure. No further repeats of the confirmed left/right two-mask cycles are selected.

Parent independently executed the exact two-tie sensitivity validator and obtained its sealed source-bound contract. Only SPR1771/SPR1772 runtime constitutive bindings are replaced; all geometry, loads, other carriers and floor equations remain fixed. Native sensitivity is still not ready: the current response API always revalidates the unchanged baseline, so a separate minimal pinned 711 response-core adaptation must explicitly accept the authenticated override contract and retain every physical gate. Baseline response replay and rejection of inherited forces under changed stiffness are required before a run.

BG045 primary-source follow-up finds no end-grain exemption from edge detailing. A conditional rectangular-face loaded-edge comparison is being finalized: A1 inner-block axis 2 points toward a −Y envelope face 20 mm away, versus 25.4 mm under the perpendicular-grain 4D branch. The 5.4 mm difference is a potential detailing requirement under that named interpretation, not an adopted joint failure or a model-change authorization. Header mixed-direction actions require a separate applicability boundary. All inspected/as-built claims remain excluded.

The [left-corner onward-transfer register](current-corner-left-leg-onward-transfer-register-attempt01/README.md) isolates the two retained LEG arrangements directly joining base_side_left to lumber_leg_left. Across both usable cases it records all 56 signed lateral/tie actions with exact action/reaction checks. A12 full-load lateral resultants are 1183.332/1723.082 N and ties 262.707/529.439 N; A1 lateral resultants are 377.513/276.079 N and ties 71.602/178.438 N. No resistance is recomputed and no old pass is transferred. A bounded evidence map will link only these two arrangements to existing checks and identify any concrete demand/receiver/geometry/hardware difference. This closes a demand-register linkage beyond the new corner blocks, not full joint acceptance.


### BG045 two-case component screen finalized

The [BG045 signed wood-mode screen](current-corner-bg045-two-case-wood-mode-screen-attempt01/README.md)
is finalized at report SHA-256
`6b63e59dbbc1e77ad46eb582b97fead1a6d874a0df8e01353f0ff049065d864b`.
Parent replayed its source verifier and independently rehashed project sources
and recomputed all four conditional Mode IV references with Ceg applied once.
The largest single-bolt lateral component comparison is 0.22495. Header washer
seats are cross-grain compression; block seats are parallel-grain compression,
so the header Fc-perpendicular reference does not cover the block seats.

The named rectangular-face interpretation for A1 block axis 2 selects its
−Y envelope face at 20.0 mm versus 25.4 mm under the conditional 4D rule:
a potential 5.4 mm detailing deficit. NDS defines a loaded edge by the action
direction but the reviewed text does not supply a general oblique rectangular
corner selection recipe. The report distinguishes source geometry rays from
normative edge selection. A12 block axis 1's short +Y component face is a
conservative sensitivity; its geometric ray first reaches +X at 44.45 mm.
Header component comparisons also remain sensitivities for the full oblique
actions. No adopted joint failure, geometry change or drilling instruction
follows. Mixed-action splitting, net/row applicability, block parallel-seat
strength and complete resistance remain open.


### Sensitivity response-method review in progress

Parent reviewed the separate 711 response-core adaptation. The physical force
and equilibrium audit body is factored without deliberate tolerance changes;
the added API must authenticate the exact two-tie override contract. The first
diff accepted arbitrary callable builders. The agent added fixed class/seal
checks, and parent independently verified rejection of a fake builder before
invocation, without reading native output. A fixed validator-source pin and
baseline physical replay/stale-force rejection remain required before native
readiness. The [parent review packet](current-sensitivity-response-core-parent-review-attempt01/README.md)
records the exact tested source and the snapshot timing limitation; the
snapshot followed the correction and does not preserve the initial diff.
No sensitivity force or extra usable case is claimed.
### Owner clarification: complete new corner path remains primary

BG001, BG003 and BG045 evaluate the left outer corner-block assembly:
post to exterior spine; spine through side member to inner block; inner
block to header. The complete path includes member bearing/contact, six
new bolts with eight lateral planes and six axial ties, twelve washer seats,
member splitting and onward transfer. The 92 introduced block-attachment
axes remain separate from the twelve original LEG/FLOOR-RUNNER arrangements.
Unchanged original resistance calculations are reused. No blanket bolt
qualification campaign or historical case-pass transfer is selected.

Parent replayed the finalized BG045 screen and retained-left-LEG evidence
map successfully. The specific affected input for those two retained LEG
arrangements is ten new candidate bores in their shared base_side_left
receiver; their original axis positions, receiver pair and nominal hardware
are retained. The new frame's signed demands also differ. These identify
bounded demand and receiver-section questions, not a reason to redo
unchanged bolt resistance work or reopen every original runner arrangement.

The sensitivity method packet now passes its baseline replay and negative
checks: seven increments reproduce the existing raw forces and printed
global/50-body balances, while inherited DAT fails both changed BG001 tie
laws at every increment. This validates the input/response method boundary,
not a changed-stiffness frame result. The source-pinned SPR489 cascade trace
and direct-scalar known-answer coupon also reproduce deterministically; no
new native result is claimed. Parent verified both packets using the project
Python environment.

The remaining complete-corner dependencies are four additional usable case
responses and a fresh stiffness sensitivity; an applicable coupled BG003
continuous-bolt method for its unequal, non-collinear plane actions; mixed
action splitting and applicable BG045 loaded-edge interpretation; and the
block strength/grain and bolt/washer/shank/engagement basis. Conditional
calculations continue without treating these missing inputs as physical
failure or making complete panel qualification a prerequisite.

### Parent sensitivity method review closed; scalar coupon preparation

The separate BG001 sensitivity fork's final parent review now passes. Parent
replayed its verifier and compared its AST to the pinned 711 wrapper:
27 physical audit statements are unchanged; the report dictionary differs
only in optional case-context access before explicit sensitivity provenance.
The loader adds a wrapper-source hash check. The fixed validator-source pin
is checked before fresh and cached imports. See
`current-sensitivity-response-core-parent-review-attempt01/final-method-review.json`.
This permits readiness preparation for a fresh response; it supplies no
variant forces and does not qualify the copied 25-cell floor mask.

The parent direct-scalar preparation independently parses the exact SPR489
coupon's emitted MPC, three load maps and spring tables. All three rank-one
analytical answers pass, including tiny common-mode compression and an open
state. Preparation refuses to freeze before the independent native-output
checker exists. Source input and reviewed frame geometry remain unchanged.
See `current-k12-rear-direct-scalar-parent-freeze-attempt01/parent-analytic-audit.json`.
The engineering result sought is a method that recovers scalar force and
physical owner force/moment without the observed projection cascade issue;
no K12-rear force adoption follows from analytical agreement alone.

### September 30: fresh corner stiffness response and direct-scalar fixture

The exact A12-rear BG001 two-tie stiffness variant was frozen and run once
through the serialized parent runner. Native exit was zero in 53.929 seconds.
The sealed response fork passes all seven increments, every source spring
law/MPC, retained bilateral checks and strict 25-bearing/75-separated floor
compatibility. Parent independently recomputed all 50 bodies and global
balances: maximum printed component residuals are 0.001330 N and 0.570069 Nmm,
within unchanged 0.1 N/2 Nmm criteria. Native slot is now idle. This is one
conditional sensitivity point, not an additional base load case, six-case
sensitivity envelope or calibrated physical stiffness bound.

The postprocessor's original JSON write failed on a NumPy boolean after all
mechanical gates passed. The separate parent writer reran that exact pinned
audit and recovered only its final report at the serialization statement,
converting NumPy scalars via item(). No force, uncertainty, gate or tolerance
was changed; the original writer/source snapshots were preserved.
The native response and independent audit are in
`current-a12-rear-bg001-seat-stiffness-native-attempt01/`.
The reproducible signed comparison is
`current-a12-rear-bg001-seat-stiffness-parent-native-preparation-attempt01/corner-sensitivity-comparison.json`.

At full load, reducing the two BG001 tie stiffnesses from 4670.054 to
2401.714 N/mm changes post ties 64.966/18.473 N to 52.434/11.707 N.
BG003 first tie rises 95.967 to 103.092 N; its largest lateral plane changes
483.948 to 485.775 N. BG045 first lateral plane rises 90.116 to 92.812 N.
All fourteen signed bolt actions are retained at each of seven matched
increments. These are redistribution results, not resistance acceptance.

The SPR489 direct-scalar method coupon also ran once and terminated at zero.
Its original checker rejected an intermediate table comparison because it
used scalar q without the actual SPRINGA dd-dd0 and the established length-
subtraction representation bound. Original rejection and frozen checker remain
preserved. Parent reviewed the separate corrected checker against pinned 711
geometry/16-epsilon span arithmetic and independently replayed the same output:
all 18 printed states pass source-MPC/table/support checks, and all three
full-step endpoints pass analytical displacement and physical owner force/
moment checks. Intermediate applied-load ramps are not inferred.
See `current-k12-rear-direct-scalar-native-attempt01/parent-method-validation.json`.
This validates the bounded coupon method; the K12-rear frame response remains
rejected until its exact replacement input and full response audit pass.

The retained-left-LEG affected-demand screen reproduced successfully.
Its largest conditional individual lateral ratio is 0.58087 and washer bending
ratio 0.37028, using unchanged original nominal/partial-thread methods and new
signed forces. The ten new base_side_left bores still require affected group/
net/splitting treatment; no original twelve-bolt campaign or case pass transfer
is selected. See `current-corner-left-leg-affected-demand-screen-attempt01/`.

The rigid-normal limit screen was independently checked in exact arithmetic:
it does not resolve the existing toy stick cycle. It is not a full-frame
existence claim, a selected cycle fix or a new native queue.


### September 30: exact SPR489 replacement preflight and parent review

The original K12-rear output was checked at all seven increments: 9,044
unilateral-carrier comparisons give one strict source-coordinate exception,
SPR489 at factor 0.2. The other 9,043 comparisons pass. This diagnosis does
not accept the response or establish force equilibrium.

The corrected input attempt02 changes only model equation rows 19,433 and
19,434 and the same two emitted equation cards. All other 21,842 serialized
model equation rows remain exact. Seventeen non-equation leaf changes are
confined to declared SPR489 method metadata. Attempt01's unrelated JSON
coefficient rounding is preserved as history and is not the run input.

Parent independently checked the exact differences and actual emitted-row
owner force/first-moment transfer. AST comparison proves that the physical
response gate statements remain unchanged except the SPR489-only callback;
its geometric table law, interval bounds and action/reaction checks remain
unchanged. The scoped source scalar and token radius now use the frozen 80
physical master DOFs, matching the reviewed known-answer coupon. Parent also
replayed the complete input/method verifier: all eleven negative probes reject.
See `current-k12-rear-direct-parent-method-review-attempt01/review.json` and
`current-k12-rear-spr489-direct-response-audit-attempt02/`.

This is method/input readiness evidence. It does not produce variant frame
forces or change the two-usable-base-case count. A fresh exact-byte native
response, every-increment floor checks and independent fifty-body/global
balance audit are still required.

Parent reproduced the BG045 stiffness-sensitivity report, SHA-256
`3c114c84e9d0f2ba0292db9af97b538005bde10af99a0f5538976b7a26c1aed8`.
Its largest named Mode-IV/Ceg component ratio changes 0.22468 to 0.23137;
header seat ratios stay below 0.13 under the same conditional reference.
The existing 20 mm edge applicability questions remain explicit. These are
individual component comparisons, not complete-joint resistance acceptance.


### September 30: K12-rear response recovered; three usable cases

The one exact-byte direct-master K12-rear run terminated successfully in
53.222505 s. Its separate method audit passes all seven increments, all 9,044
unilateral-carrier checks, retained bilateral laws and generic MPC checks.
All 100 floor normal cells retain the strictly compatible 23-bearing/77-open
branch at every increment; 46 tangent channels act only at bearing cells and
154 released channels have zero action. No mask sweep, geometry, stiffness,
load, tolerance or floor-capacity assumption was changed.

The independent parent audit also passes every physical body and global
balance at all seven increments. Maximum printed component residuals are
0.000553259 N and 0.723365 Nmm within the unchanged 0.1 N/2 Nmm criteria.
The exact freeze, execution, response and audit hashes are bound in
[current K12 parent assessment](current-k12-rear-spr489-direct-native-attempt01/parent-terminal-assessment.json).
The original rejected K12 output and original method attempts remain intact.
The native slot is idle.

The [fresh corner export](current-corner-k12-rear-case-bound-export-attempt01/README.md)
retains all seven increments, 338 interfaces/232 contact rows per increment,
six new corner bolts, eight lateral planes, six ties and twelve washer seats.
It includes the complete post/spine, spine/side/inner-block, inner-block/header
path and incoming/onward transfers. Parent reproduced the exporter and
independently compared every exported owner/point/force/radius row to the
fresh response: 334 native interface rows and four independently grouped
floor vectors at each increment, 2,366 interface rows total. This is numerical
force evidence, not a complete-joint resistance pass.

The [updated six-case progress register](current-six-case-corner-response-register-attempt02/register.json)
now records three usable conditional physical responses with corner exports:
A12 rear, A1 rear and K12 rear. A12 forward, A12 left and K12 right remain
unusable; their proposed support branches have not passed strict compatibility.
The preserved attempt01 register is historical two-case evidence, not the
latest progress count. The six-case envelope, physical stiffness/engagement
bounds and complete corner resistance remain incomplete.

At full load, K12 rear gives BG001 lateral resultants 24.877/68.767 N and
post/block tie tensions 56.542/13.978 N. BG003's four lateral plane resultants
are 64.929/5.552/59.449/4.550 N, while its outer ties are 99.238/73.628 N.
BG045 lateral resultants are 74.090/15.619 N with ties 22.962/15.135 N.
Signs and physical owners are preserved in the export. The BG003 second tie
is greater than the earlier A12 value 43.508 N, so older case-specific checks
cannot simply be transferred. The affected retained left LEG bolt 2 also has
new axial tension 530.575 N versus earlier A12 529.439 N; unchanged original
resistance methods are reused only for that changed-demand screen. No blanket
revalidation of the original twelve arrangements is selected.

Current bounded follow-through: apply existing component methods to these
new corner forces; finish the explicit BG003 full-bolt statics construction
without claiming bearing/contact compatibility or an NDS capacity; diagnose
the exact A12-forward support-branch lineage without native mask iteration.
Remaining material/hardware questions include assigned block properties,
delivered shank/thread engagement and washer support/bending, alongside
splitting/net/group and lateral/axial interaction checks. Missing evidence is
not a physical failure or a fabrication release.


### September 30: bounded BG003 full-bolt statics result

The [piecewise bearing-profile packet](current-bg003-piecewise-bearing-profile-feasibility-attempt01/README.md)
now constructs all four contiguous zones per BG003 bolt: 38.1 mm spine,
two 44.45 mm middle-member halves, and 88.9 mm inner block. Opposite-flank
compressive line reactions balance the unequal, non-collinear source plane
forces while preserving the source member wrenches. The lateral diagram has
zero shear/moment at both outboard wood faces and the middle cut. The axial
tie remains through that cut; it is not a zero full internal wrench.

Parent reproduced the source-bound producer (14 increments/112 segment
states) and independently checked all profile resultants, first moments,
whole-bolt force/moment equilibrium and constructed moment maxima. The report
SHA-256 is `215bfecdd74e11688a5289c85c3179b79dbb7751c67376ff4def955f8fd6bb9e`.
At full A12 load, the two constructed peak bolt moments are 4455.172 and
2202.327 Nmm. For A1 they are 1887.848 and 1083.803 Nmm. These are values of
the explicit field, not conservative bounds on the actual bolt response.

This resolves only whether a zero-lateral-middle-cut construction is
statically possible. It does not prove opposite-flank engagement/deformation
compatibility, wood bearing/splitting, steel/thread strength, axial/lateral
interaction or an NDS/TR12 resistance. The earlier one-sided centroid argument
does not rule out this signed field, but the original warning that geometry
alone cannot justify independent single-shear capacities remains correct.
No native solve, force adoption or new geometry was needed for this result.


### September 30: K12-rear corner component and affected LEG screens

Parent reproduced `current-corner-k12-rear-component-screen-attempt01/screen.py --verify` against the fresh seven-increment K12 demand export and independent physical/export audits. The report SHA-256 is `72e0ebbccff35828c43a5bdcc55cca7cf92c0e4d5f2bedb4c8c1e4da10628db5`. BG001's largest full-load individual lateral demand is 68.77 N; its conditional Cdelta-only reference ratio is 0.1244. BG045's largest demand is 74.09 N; its conditional Ceg-only Mode-IV ratio is 0.18448 (second axis 0.03908). These are component comparisons, not complete-joint DCRs or acceptance. The six ties and twelve washer seats are retained with signs; the largest uniform modeled-annulus pressure conversion is 0.44556 MPa at BG003 side bolt 1's spine seat. Block wood grade, delivered hardware/shank/engagement, washer behavior, splitting and combined actions remain unresolved. The conditional 20 mm face-distance questions remain explicit without promoting an oblique-action comparator to an adopted pass or failure.

BG003's two outer-plane pairs have full-load magnitude ratios 11.69 and 13.07 and direction differences 41.29 and 162.97 degrees. The reused equal-action double-shear references do not establish its coupled capacity. The statically balanced piecewise-bearing construction recorded above addresses equilibrium only; it does not supply compatible bearing/contact, yield, splitting or axial-interaction resistance.

The scoped retained left LEG K12 screen is `current-corner-left-leg-k12-affected-demand-screen-attempt01/affected-demand-screen.json`, SHA-256 `f00c528f1e5dd884ce34b40cfb96f1357e6bef4a586c65b727740dc9ab6550ac`; parent reproduced its producer. Bolt 2's tie rose 1.1354 N (+0.21445%) versus A12 rear. Reused nominal partially threaded hardware calculations give conditional bolt-2 ratios 0.12027 lateral, 0.03003 steel, 0.15794 washer bearing and 0.37108 washer bending. This reuses unchanged resistance work for the exact changed demand; it does not restart qualification of the twelve original arrangements. The ten new base-side-left bores still need the affected group/net-section/splitting treatment.

Parent froze the explicitly source-derived A12-forward M4 support proposal and rechecked the unchanged pinned response input validator on the frozen model, deck and case context. It changes only the selected floor support hypothesis, retaining 37 bearing and 63 open cells. One serialized bounded run (`springa-selected-a12-forward-attempt04`) is authorized for this exact freeze, with no automatic mask iteration. New forces become usable only after every-increment source-law/floor compatibility and independent all-50-body/global equilibrium checks pass. The usable-response register remains at three cases until those gates settle the test.


### September 30: bounded A12-forward M4 test rejected

The exact frozen M4 proposal finished normally in 40.6922 seconds with zero native return code and confirmed terminal cleanup (`current-springa-selected-floor-a12-forward-attempt04`, run ID `springa-selected-a12-forward-attempt04`). Its frozen model/deck/DAT SHA-256 values are respectively `c6ff4f67459bef5217502d0f61b25e19ef2aae0c21c0f10444de0c9936795cfc`, `394653fbe1aa0d6ad5d36f66f19eabf6ddd45fef072466ec828d044aa3cf67e1`, and `2cd771182864e24d8f4ba3f71e56651a4e77e41eb450d962132b190dd70364ad`. The unchanged strict response checker rejected selected floor normal SPR1068 as not strictly positive after rounding. The parent rejection and terminal assessment preserve that result; none of the run's corner forces are adopted. This is an incompatibility of the selected conditional support branch, not evidence of physical frame failure. A bounded signed-normal diagnostic is checking recurrence against existing masks; no further native run or automatic mask iteration is queued. Usable conditional cases remain A12 rear, A1 rear and K12 rear (3/6).

Next useful corner work is a source-bound section-action reconstruction at the existing spine/block bore stations, retaining simultaneous neighboring joint/contact forces and explicit source discrete gravity. It will establish conditional N/V/M on declared cuts if opposite-side reconstruction is justified, and will stop before physical gravity-distribution, wood-strength, splitting or complete-joint claims. No changed geometry or hardware scope is authorized by this calculation.

Latest preserved six-case status is now `current-six-case-corner-response-register-attempt03/register.json`; its producer and `--verify` replay bind the M4 rejection while preserving the three usable cases and all prior register evidence. The bounded forward-test result and stop condition are described in `current-a12-forward-m4-parent-preparation-attempt01/README.md`.


The bounded M4 diagnostic found 34 strictly positive / 66 strictly separated / zero ambiguous floor cells at every printed factor, with the same sign pattern across all seven states. SPR1068 is `floor_base_floor_left_15`; the other selected-but-separated cells are `floor_base_floor_left_17` (SPR1074) and `floor_base_post_outer_left_1` (SPR1278). At full load their source scalar q intervals are respectively [-0.014633195,-0.014633185], [-0.011069735,-0.011069725] and [-0.00067066475,-0.00067066465] mm, all with zero endpoint reaction. This is not rounding ambiguity. The observed 34-cell set differs from each M1–M4 input, so no M3/M4 two-mask recurrence is established. Parent assigned preparation of one source-derived M5 input-only hypothesis using that exact stable set, with no new geometry, law, stiffness, case control or automatic follow-on run. The parent separately owns its frozen-input readiness and one bounded test; this preparation does not adopt any M4 forces.


### September 30: M5 forward hypothesis rejected; stop further mask runs

Parent independently froze and validated the source-derived 34-cell M5 proposal using the unchanged pinned input checker, then ran one serialized attempt (`springa-selected-a12-forward-attempt05`). Frozen model/deck/DAT SHA-256 values and exact execution/rejection sources are bound in `current-springa-selected-floor-a12-forward-attempt05/parent-terminal-assessment.json`. Native execution was zero-return, terminal and 43.4053 seconds. The unchanged response gate rejected inactive floor normal SPR1026 as not strictly separated with zero endpoint RF. No M5 forces are adopted, and no accepted fourth case was gained. Parent is stopping further forward mask proposals/runs; the final bounded diagnostic will name the offending cells, signed intervals and recurrence against M1–M5. No law, tolerance, source geometry or stiffness was changed, and no physical failure or global nonexistence claim is inferred.

The latest preserved status is `current-six-case-corner-response-register-attempt04/register.json`; its producer replay passes and retains three usable conditional responses and corner exports, with both fresh forward rejections and prior evidence preserved. Detailed test scope and stop condition are in `current-a12-forward-m5-parent-preparation-attempt01/README.md`. The native slot is free. Primary engineering continuation is the corner spine/block section-action reconstruction and the bounded BG003 coupled bearing/contact/resistance gap; panel qualification and unchanged original bolts are not restarted as blanket prerequisites.


### September 30: corner source-discrete section actions recovered

The completed `current-corner-conditional-section-demands-attempt01` packet supplies signed N/V/M at the four existing spine X-bore stations and two inner-block BG003 X-bore stations, including all simultaneous neighboring joint/contact forces and source discrete member loads. It covers seven increments in each of A12 rear, A1 rear and K12 rear, 42 body-state rows and 252 one-sided section results. Parent corrected the draft's source-schema reads and exact-zero assumption, kept the existing source response gates and 0.1 N / 2 Nmm physical limits, and retained whole-body residuals and point-load jumps explicitly. Both producer replay and independent native-force reconstruction pass; the independent maximum force and moment differences are zero. Source native forces, geometry, loads and laws were not changed.

Full-load section magnitudes include spine axial up to 371.47 N (A1 rear) and inner-block axial up to 141.01 N (A12 rear); complete signed shear, bending/torsion and just-below/above results are in the packet. These are source-discrete-load actions, not qualified physical self-weight distribution, bore stresses or wood resistance. Original geometry-only net areas remain context, with no capacity inferred. This fills a conditional local-action dependency without claiming splitting or BG003 continuous-bolt acceptance. The exact missing inputs remain adjusted block/member strengths, compatible bearing/contact and continuous-bolt mechanics, applicable splitting/net/group treatment, section properties/local stress transfer and delivered washer/shank/engagement information. Three load cases and physical stiffness/engagement bounds remain unresolved. No blanket original LEG/runner or panel requalification was added.


Final forward diagnostic early result: all seven M5 states classify 32 positive / 68 separated / zero ambiguous normals with one stable sign pattern. This exact pattern matches none of the M1–M5 input masks; it is the M2 31-cell input plus `floor_base_post_center_right_0`. SPR1026 is positive while assigned inactive, so strict incompatibility remains. This does not establish a recurrence or nonexistence across all support patterns. No M6 preparation/native run is queued. The usable-case count stays three. Native ledger records 53 terminal runs with the parent slot idle; source pins for the completed independent section reconstruction revalidate.


### September 30: independent support/corner packet adopted for bounded continuation

Parent read and reproduced the [independent support/corner packet](../support-corner-review-2026-09-30/README.md), with `PASS_BYTE_IDENTICAL_SMALL_MODEL_DIAGNOSTICS`. Its diagnostic JSON SHA-256 is `174f8f945e41a273318a41fc401f1ef484160b500d624d80f57cd3480a343c98`. No source geometry or native evidence changed. The source-discrete section producer and latest six-case register were replayed successfully: the three usable conditional cases remain A12 rear, A1 rear and K12 rear. Forward/left/right remain unresolved.

The primary corner is the left outer assembly: BG001 post/spine, BG003 spine/side/inner block, then BG045 inner block/header, including neighboring bearing and onward transfer. The twelve original LEG/FLOOR-RUNNER arrangements are separate from the 92 introduced block axes. Reuse their unchanged resistance work; the scoped K12 changed-demand screen remains the only newly evaluated retained-LEG demand here.

The reviewed BG003 continuous-bolt diagnostic replaces the arbitrary piecewise profile as the next small compatibility method baseline. It retains one continuous middle receiver, free physical ends, zero gauge reactions and each source receiver wrench applied once. Eighteen zero-gap isotropic scenarios pass signed mesh refinement and wrench closure. A12-rear bolt 1 at beta=100 has middle-cut V=108.356 N and M=5933.768 Nmm. This demonstrates that the source equilibrium does not require zero middle-cut actions; it does not establish actual bearing, a conservative bound or strength. The earlier independently assembled scalar elastic packet is preserved as an exploratory cross-check, with its sign mapping and disposition now documented rather than treated as a second method-development path.

The new [smooth-section action conversion](current-bg003-smooth-section-action-conversion-attempt01/README.md) authenticates those diagnostics and matching case-specific axial ties for all 18 scenarios. For A12-rear bolt 1 at beta=100, a hypothetical smooth 6.35 mm gross section under the 95.96739 N source tie has nominal middle-cut extreme normal stresses -233.023/+239.083 MPa; the separate sampled peak bending conversion is 266.565 MPa. Producer replay and independent circular-section arithmetic pass. These are conditional action conversions, not actual steel stress predictions, product strength ratios, thread/runout qualification or mixed-location equivalent stresses. Exact physical clearance, grain-bearing law, shared timber/group compatibility, splitting, axial/thread/washer interaction and delivered shank/engagement remain missing. A bounded Luna task will test off-diagonal Y/Z coupling using a synthetic ratio-2 rotated foundation, first passing a known vector-beam oracle and isotropic agreement, then only twelve finite case/bolt/beta scenarios; no native or general solver implementation is authorized by that task.

BG045 A1 axis 2 retains the concrete conditional 20 mm minus-Y edge versus 25.4 mm reference, a 5.4 mm deficit under the stated interpretation. A conservative both-Y-face band is only a geometry proposal. Preliminary coordinate arithmetic shows the inward axis-1 move would reduce spacing to a neighboring BG003 orthogonal bore from 14.953 to 9.553 mm, leaving a nominal 2.053 mm web between 7.5 mm envelopes. That is not a new strength criterion or approved move. The bounded detailing task must preserve current geometry and identify finished-profile, applicable edge/splitting, receiver and access consequences.

The next support method is a separately named gravity-settle then climber-ramp scenario, not another fixed-zero guessed mask. All original member/panel/T-nut/mapped-hardware gravity must be retained, with exact final nodal and first-moment recomposition. Episode references must be captured at first bearing/re-engagement events, with coupled state selection, reaction-free gauge/rank checks, event refinement and explicit no-state/multiple-state/cycle/budget stops. Existing two-cell/reset and no-state/multiple-state fixtures are the required replay baseline. This is preparation, not a guarantee of a fourth usable case or a frozen native run. No M6 guessed-mask retry, rejected-force adoption, tolerance relaxation, complete panel qualification campaign or reviewed-axis alteration is queued.


### September 30: bounded coupling, detailing and event results verified

All three assigned Luna Max tasks are complete. Parent replayed the rotated-foundation diagnostic byte-identically, checked its manifest from repository root, read its assembly/load/sign conventions, replayed the final gravity decomposition, and replayed the BG045 producer byte-identically with its write intercepted (no source artifact rewritten). The earlier two-cell/reset and structural-coupling fixtures passed parent replay; the independent elimination and no-state/multiple-state artifacts reproduced byte-identically with writes intercepted. No native run or reviewed geometry change occurred.

The BG003 coupled vector operator passes its off-diagonal infinite-beam oracle within 7.3e-6 relative error and reproduces the reviewed isotropic signed cut results within 1.23e-10. Twelve synthetic rotated-foundation scenarios (two beta points, both bolts, three full-load rear cases) meet 16/32 signed refinement and receiver/free-end/gauge closure. With beta defined by the perpendicular eigenvalue and a synthetic 2:1 ratio, the largest signed middle-cut change at beta=100 is 0.458% for bending and 0.088% for shear; at beta=10000 it is 22.96% and 7.79%. These finite diagnostic points demonstrate that off-diagonal coupling can matter. They are not physical stiffness bounds, calibrated timber behavior or complete-joint resistance. The modeled 0.575 mm clearance and physical contact law remain absent, alongside shared timber, axial/washer/thread and splitting/group behavior.

The final BG045 packet keeps the specific A1-axis-2 5.4 mm conditional loaded-edge deficit. Axis 1 is not required to move by that named A1 loaded/unloaded reading; the both-Y-face band remains a separate conservative sensitivity, not a universal NDS rule. Its axis-1 move would reduce the nearest nominal bore web from 7.453 to 2.053 mm. Conditional proposals may be described with their dependencies; actual reviewed-axis alteration is held for the required geometry/mechanics review. Preserve all 66 screws and recheck only affected corner receiver/clearance/transfer dependencies, currently the ten base_header axes; expand only for an identified consequence. Actual profile, applicable edge interpretation, supported splitting/group treatment and washer access/seat support remain exact dependencies, not a stock-inspection blanket prerequisite to conditional arithmetic.

The staged-load decomposition retains all 778 gravity entities (50 physical solids, 142 T-nuts and 586 mapped hardware entities), 952 receiver-wrench rows and 50 body wrenches. Each case's gravity+climber maps reproduce its registered nodal map exactly, with force/first-moment closure; recovered gravity maps differ across cases by at most 4.55e-13 N. The new loading-history contract remains input-only. Common six rigid modes must be separated from any additional internal zero modes by a rank check; extra modes cannot be hidden with anchors.

Parent additionally completed an exact coupled contact-event fixture. Under its explicitly synthetic settling/ramp history, the contact event reaches t=-2 mm at alpha=1/2, then legitimately reaches the owner's nonzero-reference final toy equilibrium. Opening releases that reference; another synthetic open-stage load and re-engagement capture t=-1 mm. Nineteen states and ten event brackets pass independent exact Fraction equilibrium, contact-law and event checks. Odd step counts 3/7/15/31/63 localize the identical event, while recorded last-open-reference errors shrink as 1/(3n) or 2/(3n). This fills a small analytical event-validation dependency; it does not prove actual-gravity/frame existence, a 100-cell selector, native constraint updates, nonlinear event convergence or a reaction-free frame gauge.

Current usable corner cases remain three, with complete signed source-discrete section results for those cases. Minimum next mechanics work is the modeled-clearance/contact dependency for the continuous BG003 bolt, and the applicable BG045 edge/splitting/detail interpretation; no general solver port or catalog search is selected. Before a staged native frame run, the episode/event/state method, initial rank/gauge and pinned native constraint mapping still need their own bounded known-answer evidence and parent readiness/freeze. No rejected forces, historical pass transfer, guessed-mask retry or full-joint acceptance is adopted.

Final report pins:
- BG003 rotated foundation: `current-bg003-rotated-foundation-diagnostic-attempt01/diagnostics.json`, SHA-256 `4299919a3d3bfa8ef56589e8741ca62f3e88cb7b6077d46053ac3ba06af12918`.
- BG045 detailing: `current-bg045-conditional-detailing-exception-attempt01/detail-screen.json`, SHA-256 `0d295b5790ecb707c12effe3f51a850177269b8533e93bdc792ed1058e34b0db`.
- gravity decomposition: `current-gravity-settle-climber-ramp-scenario-attempt01/decomposition.json`, SHA-256 `39d1530ee888bb824c2bd1624072890385c19a1448f4d146567a041aff5d14dc`.
- exact event fixture: `current-coupled-contact-event-reference-fixture-attempt01/fixture.json`, SHA-256 `0e5e5f6953a34be3b2078159cd51eb0f5398cb15ff2f22efd9b1d6e7df75b19e`.


### September 30: corrected net-section context and nominal normal traction

Parent found an actual context-field error in the preserved source-discrete section report: its inner-block BG003 cuts carry the 11,766.458 mm² area away from a cross-bore, instead of the applicable 11,099.708 mm² at the cross-bore center. The matching-axis geometry screen already subtracts the additional 666.75 mm² full-width strip correctly. Signed native/export/cut actions and their equilibrium verification are unaffected. The original report and source hashes are preserved; its README now points explicitly to the additive correction, which flags all 84 affected one-sided metadata rows rather than silently using the old area.

The new [net-section normal-traction packet](current-corner-net-section-normal-traction-attempt01/README.md) supplies centroids and second moments for all six reviewed spine/block sections and nominal affine normal-traction conversions for 252 signed cuts. Producer replay and independent integration over gross rectangles minus strips/circles pass. The independent maximum reconstructed N/Mx/My discrepancies are 1.71e-13 N and 9.10e-12 Nmm. At full A12 rear, the screened spine nominal range is -0.3022 to +0.4277 MPa and inner block -0.04118 to +0.04144 MPa. The values are explicit source-discrete, common-affine-strain proxies; the cross-bore center cuts have disconnected ligaments, and actual local transfer/strain/contact is not qualified. No wood strength, hole concentration, shear/torsion, splitting, stability or complete-joint acceptance is inferred. Corrected report SHA-256: `4ac5094c733f4497c69f9890858581c1a283cb2782c1922f0a149185df66c386`.

Bounded continuation remains BG003 radial-clearance mechanics under a declared synthetic bearing law, an axis-2-only conditional BG045 proposal comparison, and pinned native scalar-reference boundary-release mapping. The clearance task must start from the validated gap-zero solution and report finite continuation/rank/refinement stops without hidden stabilizers. The native mapping task must distinguish fixed equations from changing independent reference SPCs and examine release from nonzero tangent reaction, not merely a zero-reaction toy. Parent retains freeze/readiness/serialized-run ownership; no frame deck or guessed-mask iteration is queued.

### September 30: radial clearance replay and axis-2-only alternative

Parent replay of `current-bg003-radial-clearance-diagnostic-attempt01/run_diagnostic.py --verify` returned `PASS_BYTE_IDENTICAL_RADIAL_GAP_DIAGNOSTICS`. The diagnostic retains the continuous two-plane beam, three free rigid receivers, source lateral wrenches applied once, free physical ends and zero gauge reactions. Eight A12-rear bolt-1 solutions cover k=100/1000 N/mm², gap=0/0.575 mm and 16/32 meshes; all converge and pass signed refinement below 0.15%. Gap homotopy is numerical continuation, not a physical load history. The hypothetical E=190000 MPa and isotropic foundations are not calibrated timber properties or conservative bounds.

At 32 elements, introducing the gap changes middle-cut shear magnitude from 93.542 to 51.528 N at k=100, and 31.920 to 22.777 N at k=1000. Corresponding bending changes are 2938.993 to 2300.459 Nmm and 151.185 to 1063.546 Nmm. The large percentage increase at k=1000 is relative to a small zero-gap middle-cut action; it is not a physical capacity result. Clearance cannot simply be omitted as an automatically conservative choice. Report SHA-256: `2a6ee00883ab242ddd5f6c144e07b618aa58a604a007fb24edeebeae5461fc77`.

Parent also reproduced the BG045 axis-2-only proposal byte-identically with writes intercepted. Keeping axis 1 fixed while shifting axis 2 from Y=-155.70 to -150.30 mm changes the stated loaded minus-Y distance from 20 to 25.4 mm and retains the nearest modeled 7.453 mm bore web. Bolt pitch reduces from 93.35 to 87.95 mm; the closest projected header-screw distance to axis 2 reduces from 122.337 to 118.551 mm. These use analysis envelopes and current demands. Other case-direction edge interpretations, oblique header applicability, splitting/group transfer, washer seating/access and actual post-move demands remain unresolved. No reviewed geometry was changed. Report SHA-256: `c0899e9b4efdb3c1e2b44f4bd0bdde824656d4bb3d5dd8668f615eaba69e9a30`.

The parallel [uppermost-block packet](../upper-frame-joint-review-2026-09-30/README.md) was read and its producer replay passed. It supplies 336 bolt actions, 672 signed member directions and 84 block balances for four upper blocks across the same three accepted rear responses. Its root-yield scouting assumptions, oblique terminal-end questions and G7 exclusion remain explicit; no scouting exceedance is promoted to an adopted failure or complete-joint acceptance. Its report SHA-256 is `0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6`. The parallel thread is separately addressing remaining service-upper duties; lower-corner work does not duplicate that study.

The staged native mapping proposal had stale generated expected-state metadata, detected by parent replay before freeze. A bounded Luna task is correcting that consistency and preparing the nonzero-reaction boundary-release coupon first. A second task is recovering the seven actual corner timber-contact pair resultants and average cell pressures from accepted exports. Neither task authorizes a frame run or expands panel qualification. Three of six conditional frame responses remain usable; current geometry and original bolt resistance evidence are preserved.
