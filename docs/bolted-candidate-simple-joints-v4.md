# Bolted candidate: active V4 simple-timber-joint plan

Status through the six-case bore-member envelope: **PB-02 ADVANCE for development only;
G1 remains open; no
cutting, drilling, fabrication, or structural release.** This plan implements the owner's V4
direction for the separate `compact-floor-flush-bolted-development` lane. It supersedes the
prior [rated-HL bracket focus](bolted-candidate-rated-hardware-focus.md) as the active design
sequence without erasing its test results or the selected
`compact-floor-flush-development` baseline.

The owner's name for the rectangular timber connector is a **bolted solid-wood corner block**,
or **corner block** below. Historical documents, file names, and machine identities use
`cleat` for the same part; those identifiers remain stable for traceability.

## Fixed scope and design order

The physical board is kerf-right, cut from two 4×8 panels. Preserve its climbing surface,
panel outlines, holds, T-nuts, LED requirements, all 48 main-panel and 18 kicker screw axes,
and the existing panel-screw policy. Verify actual receiving timber and both inner kicker edge
supports after any hidden-frame change. Keep the selected baseline and authenticated six-case
archives separate. The twelve old frame-bolt arrangements are starting references, not
automatically valid after changing frame geometry.

Use ordinary through bolts, metal nuts, and suitable bearing washers for structural move
interfaces. A plain full-section face overlap is permitted; it retains both member thicknesses
and has a real centerline offset. A rectangular solid-timber corner block with separate
through-bolt groups is permitted where it simplifies a butt corner. A small block may remain
bolted to one transport member. Any metal connector introduced into the remaining work must be
a documented factory connector. No half-lap, housed or interlocking joinery, custom steel,
panel through-bolts, new panel fasteners, unqualified inserts, structural wood-thread removal
per move, manufacturer contact, or glued structural assembly is authorized. Do not inherit HL
bracket timber minima for ordinary timber joints.

Keep floor support and landing-space assumptions explicit. Do not claim that nominal CAD fit,
a single wood-bearing mode, bolt-shaft strength, or one old proxy load is a complete structural
joint. Evaluate actual simultaneous actions, contact-only bearing, slip and rotation,
load-to-grain directions, bolt group and eccentricity, wood, washer and bolt resistance,
access, stock, disassembly, and cost before selection. No member has been physically inspected,
cut, or drilled.

For installation access, distinguish permanent hardware that collides with the finished panel
from a temporary tool that can be used with a removable panel off. Panel removal never excuses
a finished-state hardware clash. Check tool clearance for the actual assembly order, socket,
extension, and ratchet rather than assuming clearance from a generic cylinder.

## Bounded sequence and current state

- **PB-00 — scope:** reconcile candidate authority and tests; archive the bracket-only decision
  without changing baseline rules. This remains historical scope work.
- **PB-01 — representative joint:** compare full-section overlap and a rectangular corner block
  at one actual rail duty, including geometry, action path, access, and purchased cost. Its
  local studies remain development inputs, not a selected complete-frame joint.
- **PB-02 — G1 concept:** connect the center and base assembly, backing, and adjoining rail ends;
  map original duties and select a costed architecture. The rear-clear center now has a bounded
  **ADVANCE** decision, but PB-02 has not passed G1.
- **PB-03 — physical geometry:** build one coherent kerf-right CAD assembly with full hardware
  stacks, receivers, no unintended SDS path, and an individual-member transport sequence. This
  remains open. Six service-rail stations are geometrically converted, but 16 legacy
  connector stations remain and no coherent final all-bolted frame exists.
- **PB-04 — G2 analysis inputs:** complete applicable 2024 NDS local checks, contact and stiffness
  inputs, and all 36 criteria without waiving their safety questions. This remains open and G2
  has not been reached or passed.
- **PB-05 — candidate evidence:** run all six required cases on one frozen candidate, including
  the forward case, then reconcile convergence and resistance. The six numerical cases are now
  accepted; resistance reconciliation remains incomplete and does not close PB-04 or G1.
- **PB-06 — owner decision packet:** deliver costed stock, cut, drill, hardware, and assembly
  records plus independent review and explicit physical receiving checks. This remains open and
  cannot release work before PB-03 and PB-04 close.

PB-01 compares both simple joint types at the same rail duty but does not force both to be
selected. A 2×2 corner block is a screening suggestion, not an approved section; size it from
actual edge, end, group, and action checks. Its two bolt groups are serial load-transfer
interfaces, not capacities to add. Orthogonal bores must not collide, and both ends of each bolt
need washer, nut, and tool access. Avoid precision joinery or a new generic optimization
framework.

Purchased cost includes full bolt, nut, and washer stacks, changed timber, retained factory
brackets if any, tooling and consumables, and known delivery and tax. Unknown prices stay
unknown. Keep owner-owned stock, sunk hardware, fabrication effort, and move operations
separate. The historical $122.70 ML24Z and SDS subtotal is not a complete frame budget or a
price ceiling.

## Claim and evidence boundary

Use the existing
[2024 NDS component helpers](../mini_moonboard/bolted_timber_checks.py) only within their
documented scope. A two-member lateral-yield result does not cover corner-block integrity,
splitting, axial separation, group effects, formed steel, or an entire frame. Preserve failed
and nonconverged diagnostics as history; never substitute them for accepted forces. No
selected-candidate hash may be edited merely to silence a stale-snapshot CI gate.

At the historical PR head `1711d30`, the V4 scope tests, normal suite, and CAD smoke stage
passed CI. Selected-candidate verification then stopped on the pre-existing
`compact_floor_flush_frame.py` geometry-source mismatch, and historical-export verification did
not run. The saved `bolted-candidate-native-input.json` was an unrun, unready older
bracket-layout producer record. That checkpoint remains useful history but is not the current
PB-02 evidence state.

The later
[signed replacement-duty fixture](bolted-candidate-prototypes/simple-center-signed-duty-fixture.md)
showed that five authenticated historical right-center actions required compression-only face
contact and no-preload bolt tension. The subsequent
[stiffness sensitivity](bolted-candidate-prototypes/simple-center-stiffness-sensitivity.md)
converged all 50 historical-action scenario combinations. Within a fixed case, its largest
reaction ratio across trial stiffnesses was about 1.47868. Those imported historical actions and
their wider cross-case envelopes remain history; they are not the current source-bound PB-02
demands.

## Current PB-02 rear-clear evidence

The active ten-bore rear-clear geometry fingerprint is
`4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb`.
The rear cleat spans Z=5–460 mm, has a 455 mm length, and has no modeled floor bearing. The
panel and kicker screw layout remains unchanged at 66 axes, both inner kicker panel edges remain
supported, and only one center support moved outward.

The
[rear-clear evidence](../fea/results/diagnostics/pb02-rear-clear-10333d2-v1/README.md)
contains six source-bound, numerically accepted cases on that geometry:

- A12 forward: `[0, -300, -2224.111]` N;
- A12 rear: `[0, 300, -2224.111]` N;
- A12 left: `[-300, 0, -2224.111]` N;
- K12 right: `[300, 0, -2224.111]` N;
- K12 rear: `[0, 300, -2224.111]` N; and
- A1 rear: `[0, 300, -2224.111]` N.

The
[six-case authenticator](../scripts/simple_center_pb02_six_case_evidence.py) pins each report,
full load vector, model and scope identity, contact partition, common 278-file source closure,
and retained final-cycle solver artifacts. Every case passes its recorded contact and
tension-only active-set, equilibrium, MPC, and numerical-acceptance gates.

All six cases use the 8×8 reference-density contact model and a conditional floor-contact
stiffness of **10,000 N/mm**. That floor value is a developmental input, not a measured or
qualified property. The source-bound A12-forward case and current reference-density demands are
therefore present; the older claims that they were missing no longer apply.

The bounded stiffness evaluator now authenticates complete, source-comparable six-case suites at
5,000, 10,000, and 15,000 N/mm from the compact
[stiffness evidence
package](../fea/results/diagnostics/pb02-floor-stiffness-5k-10k-15k-v1/manifest.json).
It reports **material numerical change detected** under its 5% screening rule: governing identity,
governing ratio, and signed action each change. The largest governing-ratio change is 16.30%, from
the 10,000 N/mm block/header end-grain ratio of 0.09813 to 0.11413 at 5,000 N/mm. At 15,000 N/mm,
the governing interface-moment and two bolt-ratio identities change. Eleven small signed
components reverse sign; the largest relative change is a 48.31 N-mm change around a near-zero
baseline moment. The 5% rule is numerical triage, not a physical or acceptance limit.

The listed conditional ratios remain at or below 0.20284 over the three accepted trials, so the
**ADVANCE for development only** decision survives this range even though numerical insensitivity
is not claimed. A separate 20,000 N/mm run failed to converge at A12 rear under both bounded retry
strategies; only its failure metadata is retained, and none of its forces or artifacts enter the
comparison. These inputs are numerical trials, not measured floor properties or physical bounds.

## Six-case component-demand envelope

The
[component envelope](../scripts/simple_center_pb02_six_case_component_envelope.py) preserves
every bolt's simultaneous axial and lateral action from each accepted solve. It also reports
complete interface resultants and moments, including contact and bolt actions. Its disposition
is **ADVANCE for development only**, not acceptance.

Governing actions are:

- combined bolt force: **196.391 N** at `principal_block_principal/bolt_1`, A12 rear;
- bolt tension: **75.576 N** at `header_principal_block/bolt_1`, A12 rear;
- bolt lateral force: **181.849 N** at `principal_block_principal/bolt_1`, A12 rear;
- complete interface force: **195.771 N** at `principal_block_principal`, A12 rear;
- complete interface moment: **5,147.700 N-mm** at `header_principal_block`, A12 rear; and
- peak cell-average pressure: **0.01765 N/mm²** at `header_principal_block`, A12 left.

The A12-rear governing combined bolt action contains 74.165 N tension and 181.849 N lateral
force from the same solve. The supported conditional comparison ratios govern as follows:

- individual wood yield: **0.19984**, `principal_upright_block/bolt_1`, K12 rear,
  0.180-inch root sensitivity;
- A307 direct-shaft comparator: **0.17441**, `block_header/bolt_1`, A12 forward;
- block and header end-grain yield: **0.09813**, `block_header/bolt_1`, A12 forward,
  0.180-inch root sensitivity; and
- ideal 20 mm washer wood-bearing sensitivity: **0.06441**,
  `header_principal_block/bolt_1`, A12 rear.

All currently supported six-case conditional ratios are below 1.0. The separate A12-forward
density-2× sensitivity has a 0.22815 direct-shaft ratio, also below 1.0. These comparisons do
not qualify the A307 long-grip method, delivered bolts, washer metal, preload, prying, wood
splitting, group behavior, contact pressure, or a complete joint. The six-case envelope uses
reference contact density; its local pressure is not qualified.

The [six-case bore-member envelope](../scripts/simple_center_pb02_six_case_member_envelope.py)
also checks both sides of four 7.3 mm diagnostic bore cuts in every accepted case. Its governing
applicable exact-cut ratio is **0.04335** at the rear-cleat link bore in K12 rear; the same cut's
average net-shear ratio is **0.00134**. Dimension-lumber values omit size-factor benefit and the
4x4 side cleat uses the separately classified 2024 NDS Table 4D DF-L No. 2 post-and-timber
values. This remains an **ADVANCE for development only** result: the principal cut is
extrapolated and excluded, while torsion, stability, splitting and near-hole behavior remain
unqualified.

The crossed-bore local wood envelope evaluates 24 signed case/incidence records around the
18.7 and 20.2 mm nominal ligaments without force cancellation. Its governing conditional NDS
Appendix E parallel row-tear-out ratio is **0.02373** at the upright-side-cleat link bore in K12
rear; the separate supplemental EC5 splitting ratio governs at **0.01071** at the shifted-post
high bore in K12 right. This advances only the listed local mechanism. Three-dimensional
orthogonal-hole stress concentration and near-hole interaction remain unqualified.

## PB-03 service-rail geometry core

At `3c282c5e`, the PB03 adapter replaces the two lower-center, two lower-outer,
and two upper-outer service-rail stations. Each station is built independently
from actual kerf-right geometry. The four outer stations join their service
rails to `base_side_left` and `base_side_right` at coincident physical butt
faces. The core adds six 300 mm solid timber corner blocks and 24 complete
generic through-bolt stack envelopes while removing six angle duties and 36
SDS axes.

The outer upright stacks use a **228.6 mm illustrative wood grip**; the outer
rail stacks use 95.25 mm. The upper rail bores use a 125 mm offset to clear the
lower-pair hardware and tool paths. Each upper block has 86.9 mm actual-shape
clearance from its same-side lower block. Those are geometric inputs, not
selected retail bolt lengths or qualified resistance. Exact retail bolts,
washers, nuts, threads, orientations, and tolerances remain unresolved. No PB02
or PB01 resistance result has been transferred to the PB03 service-rail joints.

The bounded CAD gates check contact, complete 7.5 mm bores, finished panels,
unrelated timber, all 66 fixed panel/kicker axes, all bore pairs, all stack
components, and outward tool paths. Current geometry passes those gates. Exact
retail hardware, tolerances, strength, drilling, and fabrication remain
unselected and unreleased.

The live V4 viewer is current. It hides the six replaced angle solids and 36
SDS visuals and shows six PB03 blocks and 24 stacks alongside the unchanged
PB02 visual contract. The partial inventory is **16 legacy stations, 96 legacy
SDS axes, six PB03 blocks, 24 PB03 stacks, 198 total connections, and 36
bolt-kind connections**. All 66 fixed panel/kicker axes remain unchanged. This
is not the final frame. Hardware, resistance, drilling, and fabrication remain
unresolved and unreleased.

## PB-02 G1 status and remaining boundaries

PB-02 is **ADVANCE, development only; G1 remains open**. The accepted cases and component
envelope support continued work on this architecture. They do not establish G2, final all-bolted
frame geometry, drilling, fabrication, construction, or structural acceptance. The current
PB03 development adapter still retains **16 legacy angle and SDS connector stations** outside
the converted service-rail core.

PB-04 must still resolve three-dimensional crossed-bore stress concentration and nearby-hole
interaction, the inclined
principal's clipped local section and 0.490 mm nominal unloaded-edge reserve, the extrapolated
principal bore cut, torsion/shear mechanics, stability, group effects, perpendicular tension,
washer metal,
preload, prying, nut and thread behavior, delivered hardware, fabrication tolerances, and a
defensible floor-contact stiffness range or receiving criterion. It must map those results to all
36 criteria before any G2 claim.

PB-03 must convert and geometrically check the remaining 16 legacy stations, then demonstrate
one coherent kerf-right final all-bolted CAD assembly with actual stacks, receivers, tool access,
panel clearance, and individual-member transport. Current PB02/PB03 evidence must not be
described as that final frame.

PB-06 remains downstream of those tasks. It still requires a complete costed stock, cut, drill,
hardware, assembly, inspection, and independent-review packet with physical receiving checks.
No purchase for construction, drilling, fabrication, or structural release follows from the
current ADVANCE decision.

Source scope: [AWC TR12](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
describes dowel-yield lateral methods and exclusions. The
[USDA Wood Handbook, Chapter 8](https://research.fs.usda.gov/download/treesearch/62253.pdf)
provides illustrative loaded-edge guidance, not a complete 2024 NDS joint verdict. The
task-supplied V4 plan remains the scope handoff; current authenticated sources and fresh
candidate evidence govern current numbers.
