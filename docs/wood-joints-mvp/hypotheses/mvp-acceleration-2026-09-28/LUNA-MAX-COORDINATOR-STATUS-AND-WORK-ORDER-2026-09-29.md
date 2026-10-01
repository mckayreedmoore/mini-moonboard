# Luna Max coordinator status and work order — 2026-09-29

This is a status addendum to the
[execution brief](LUNA-MAX-COORDINATOR-EXECUTION-BRIEF-2026-09-29.md) and
[root continuation note](root-continuation-note-2026-09-29.md). It answers
whether a fresh Luna Max coordinator can continue safely and defines its next
bounded work. `AGENTS.md` remains controlling. This addendum supersedes the
root note only on the current T09 disposition; otherwise use the root note as
the current operational authority. It assigns read-only evidence work and
preparation only; it does not authorize geometry changes, meshing, native
solves, fabrication, or climbing use.

## Handoff decision

**Ready for a Luna Max coordinator to continue the read-only evidence and
method-preparation phase. Not ready to freeze or run a complete six-case
structural model.** The current revision is sufficiently bounded: the reviewed
geometry and scope are explicit, the six applied load cases are registered,
the c11 result is dispositioned, and the architecture and demand-coverage
decisions have independent exact-hash reviews. The next coordinator should
close or precisely disposition four named load-path gates rather than repeat
the A/B comparison, recreate the demand register, or continue the spent c11
branch.

For this work phase, the parent defers the T09 mesh freeze and all mesh
generation, including smoke tests. The 50-body identity audit is already
complete; a mesh would not resolve the four load-path gates, and its API route,
element settings, and quality limits remain unsettled. Reopen T09 only if the
integrated gate review identifies a specific required mesh result that cannot
be obtained from the planned reduced model and code/product checks.

## Verified progress

- The attempt04 source manifest, member-solids bundle, and source audit agree
  on 50 distinct one-solid STEP bodies: 20 timber members, six panels/kickers,
  and 24 blocks. The source audit confirms the identities and file hashes.
  The older patch mesh covers only three current bodies; full-frame solver
  body/element/DOF maps are still incomplete.
- The current MVP architecture is conventional whole-frame response plus
  applicable code/product connection checks (Option B). The exact-hash reviewed
  demand register found no path-complete member or joint demand subset.
- All 47 MVP-E criteria remain pending for this development lane; the source
  and diagnostic work below does not close them.
- c11 is one equilibrated `a12-rear` linear branch with six failed
  compression-only contact checks. Its independent audit confirms equilibrium
  and output recovery, while numerical and mechanical acceptance remain false.
  Its one-run budget is spent. Do not create c12 or transfer its forces as
  demands.
- Gmsh 4.12.1 and Docker are reported available, and exact-version Gmsh methods
  have been reviewed. The current shell lacks the Gmsh Python binding; the
  executable/API route, element settings, mesh sizing, and numeric quality
  limits are not frozen. No current full-frame mesh was generated.
- Luna Max has completed read-only reviews of all four gates. The beam review
  confirms that whole-member gravity wrenches and a longest-axis OBB do not
  establish exact beam line loads or section forces. The four reviews establish
  the current blockers, not gate closure.

## Four open integration gates

1. **Conditional floor support.** The current c11 model uses externally
   switched finite tangential springs, not ideal zero slip only while a floor
   cell bears. One active cell separates while carrying tensile normal force
   and 328.526 N paired tangent force; another penetrates while inactive. The
   assumed no-slip support remains unverified. A method packet needs a precise
   first-bearing and re-engagement reference, open/bearing/release cases,
   coupled tangent behavior, and a reviewed termination/failure policy. Do not
   infer floor friction, anchorage, or physical floor capacity.
2. **Panel withdrawal.** The six cases have positive panel-normal resultants
   from 1,199.82 to 1,659.44 N. They are panel resultants, not screw demands.
   The record does not establish applicable Hillman 42605 withdrawal
   resistance or stiffness, installed penetration, root/head/panel limits,
   group sharing, or a complete receiver-to-frame route. Do not transfer
   another product's values or divide load equally among screws.
3. **Receiver and hardware transfer.** Geometric intersections and identity
   paths exist, but they do not establish carriers, active bearing, attachment
   stiffness, simultaneous interface actions, or force sharing. The center-
   kicker routes, edge-support intervals, 92 candidate bolt axes, 12 retained
   frame-bolt arrangements, T-nuts, and accessory mass representation need an
   explicit current-revision closure ledger. Source-mapped gravity wrenches
   are accounting, not mechanical connections.
4. **Beam self-weight distribution.** Source mass and body gravity wrenches
   close for the modeled members, but they do not establish beam section
   actions. A geometry-derived beam axis and line-mass profile need to be
   justified; a uniform resultant with a correction couple preserves a total
   wrench but not local section-force distribution. Keep the exploratory OBB
   equivalent-load script, if inspected, explicitly non-accepted until an
   exact profile and section-force known-answer check are available. A
   read-only estimate using the 600 kg/m³ density scenario gives 127.5322 kg
   and 1,250.6635 N for 20 frame timbers; mean equivalent loads from reduced
   member descriptor lengths range from about 30.04 to 71.83 N/m. These are
   modeled scenario values, not measurements or exact local `q(s)`. The
   source centroid is offset about 53.8 mm from a leg's descriptor-line
   midpoint; a correction couple can restore the whole-member wrench (up to
   about 2,095 N·mm in the reviewed
   calculation) but cannot recover the beam's correct section-force diagram.
   See the [source mass/centroid inventory](../evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json)
   (SHA-256 `4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a`)
   and [reduced member geometry](reduced-static-attempt01/member-geometry.json)
   (SHA-256 `121f1940d0180367f953a1f92443964ded901ca775536750a9b028e37d6c8187`).

## Next work for the coordinator

1. Re-read `AGENTS.md`, the root continuation note, this addendum, the
   execution brief, the closed demand register, and the exact-hash review
   receipts. Verify the pins before relying on copied values. Treat the root
   continuation note as the current operational entry point.
2. Prepare four append-only, source-bound packets in parallel: (a) a floor
   support method and known-answer specification; (b) a Hillman 42605 panel
   withdrawal evidence screen; (c) a receiver/load-path closure ledger; and
   (d) a member self-weight distribution and beam-section recovery method.
   Each packet must state revision and source hashes, units, what is observed
   versus assumed, equations or transfer rules, checks performed, unresolved
   inputs, and a clear `CLOSED`, `CONDITIONAL`, or `BLOCKED` disposition.
3. For any `BLOCKED` gate, state the smallest concrete evidence, owner
   decision, or model change that could unblock it. Do not fill missing
   stiffness, resistance, engagement, or load-sharing values with guessed
   numbers. Preserve the current screw policy and reviewed geometry unless a
   required change is first reported as a decision request.
4. Obtain an independent Luna Max exact-hash cold review of each packet, then
   merge only the reviewed dispositions into a single readiness table. The
   table must identify cross-gate dependencies and show whether a complete
   current-revision six-case input can actually be frozen.
5. Keep the Gmsh mesh-only workflow parked. Do not prepare a new mesh freeze or
   generate even a smoke-test mesh during this phase. A later proposal must
   identify the exact decision or criterion that needs a mesh, pin a usable
   API/CLI route, and predeclare element and quality checks before the parent
   considers a separate go/no-go.
6. Return the evidence table and any required decision to the parent. Before
   any full-frame response, the parent owns exact input freeze, readiness,
   serialized run budget, native-run authorization, and final output
   validation. A native response is eligible only after all material,
   section, receiver, support, load, and solver mappings are complete and the
   relevant known-answer checks and independent input review pass.

## Stop conditions and deliverable

Stop a gate on a source mismatch, an unclosed load path, unsupported mechanics,
or a failed known-answer check. Report the affected claim and minimum evidence
or decision needed; do not compensate by changing geometry, switching
solvers, weakening a threshold, or running a partial structural case.

The next coordinator deliverable is a reviewed four-gate evidence table and a
binary readiness recommendation with its exact source pins. The current
recorded answer is **not ready for a full-frame solve**. If any gate remains
blocked, return the smallest actionable next request and keep the milestone
open. No criterion or candidate is accepted by this work order.

## Owner-directed continuation refinement — September 29, 2026

The owner's parallel-review guidance supersedes the packet-recreation and
per-packet cold-review steps above where they would repeat completed work.
Continue Option B: whole-frame static demands followed by applicable
code/product checks. Reuse the completed A/B comparison, demand register,
reviewed fixtures, and four-gate evidence. Repeat a review only when an input
changed or a specific unresolved concern warrants it. The upper-panel
direction-cone audit was warranted by the saved LP's unbounded-variable
roundoff caveat; it is recorded in the
[four-gate matrix](four-gate-closure-matrix-2026-09-29.md). No new mesh or
native-run authority follows.

| Next task | Reuse | Engineering result it unlocks | Stop condition |
|---|---|---|---|
| Receiver/load-path closure, first priority | [Receiver ledger](receiver-load-path-ledger-2026-09-29.md), [aggregate panel/screw subsystem wrench](panel-screw-subsystem-boundary-wrench-attempt01/README.md), gravity-inclusive [panel-group screen](panel-screw-group-total-withdrawal-attempt02/README.md), and the upper-panel [direction-cone check](reduced-static-attempt01/panel_direction_cone_audit.py). | A source-bound disposition for each loaded panel-to-receiver route, retaining the six aggregate frame-on-panel-subsystem wrenches and the five bounded total-group withdrawal actions without inventing per-axis shares. | Stop at the first absent carrier law, load-sharing basis, exact product/engagement property, receiver DOF mapping, or downstream path. Do not divide forces equally or treat missing evidence as physical failure. |
| Hillman 42605 withdrawal checkability | Existing exact-product source review and the preceding group-total results. | Either an applicable resistance and axial load-slip basis for the purchased screw/installation, or a precise `UNCHECKABLE` disposition and the evidence/owner choice needed next. | Stop if exact-product withdrawal data, installed thread engagement, head/panel limit, or a supported group rule is absent. Do not transfer another product's values or elevate NDS reference arithmetic to a product rating. |
| Conditional floor support | c11's audited false branch and the existing hand-solvable open/bear/release fixture in the [feasibility plan](next-gate-feasibility-plan-2026-09-29.md). | A bounded analytical support rule for zero tangential slip only while bearing, or a precise method blocker for Option B. | Stop if the rule cannot release on opening and re-reference on re-engagement, has no bounded state-selection/termination behavior, or needs unsupported friction/anchorage. Do not repeat a CalculiX contact coupon or start solver development. |
| Member self-weight and beam actions | The reviewed 599-bin, 20-timber exact-BRep profile and its mass/first-moment closure. | A justified sectioned line-load and known-answer section-force recovery for spans whose axes, supports, and end conditions are source-bound. | Stop at missing support span/end conditions or an unsupported continuous load profile. A whole-member wrench or correction couple is not local `N/V/M`. |
| Integrated readiness decision | The four updated gate dispositions and existing closed demand register. | A binary answer on whether a complete current-revision six-case input can be frozen; otherwise the shortest exact list of blockers. | Any open load path, unsupported law, failed fixture, or incomplete body/DOF/material/load map keeps readiness false. No mesh, freeze, native run, criterion closure, or candidate acceptance follows automatically. |

Give each Luna/max worker one bounded row from this table and its listed
inputs. The coordinator merges only new engineering results, changed pins, or
specific concerns; it does not repeat completed comparisons or cold reviews
for process completeness.

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
