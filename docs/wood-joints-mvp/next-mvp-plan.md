# Wood-joint candidate: next plan to MVP-E

Status: execution plan, updated 2026-09-24. This plan continues the
[`compact-floor-flush-wood-joints-development`](../../wood-joints-candidate.json)
lane from its recorded WJ-03 partial result. The endpoint is **MVP-E**, a
conditional engineering-development and shop-document package under stated
loads, materials, hardware, and floor assumptions. It is not an inspected
build or an unconditional climbing rating. WJ-11 physical receiving and
prototype observations belong to the later MVP-P record.

## Refined execution plan, September 24 evening

This section is the current execution sequence. It supersedes sequencing and
current-status language in the preserved checkpoints below, without changing
adopted criteria or transferring historical results. The owner requested this
plan before creation of the refined execution goal.

**Endpoint:** complete a source-bound engineering evaluation of the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` design and a coordinated conditional
development package. Report each applicable criterion as supported pass,
supported failure, or specifically unresolved, with evidence and consequences.
An unresolved item is not closed merely by listing it: pursue available
analysis and sourcing, and record the concrete limit if it cannot be resolved.
MVP-E requires the applicable gates to pass; a completed adverse evaluation
does not make MVP-E complete. Fabrication, physical receiving, climbing release,
candidate selection, and apartment-floor qualification are outside this goal.

### Ordered work and completion evidence

| Step | Remaining work | Required result and dependency |
| --- | --- | --- |
| 1. Freeze and reconcile | Keep the approved viewer/model stable. Bind current geometry, axes, grain scenarios, hardware roles, source files, and applied loads. Use the current geometry entry point and exact STEP exports; archive older adapters without migrating unused ones. | One consistent revision: 24 blocks, 92 candidate bolts, 12 retained frame bolts, and 66 Hillman axes (58 unchanged plus eight recorded moves). Geometry replay and current receiver/grip screens are available; full contact graph remains open. |
| 2. Finish one joint end to end | Mesh the exported ordinary bottom-center right joint: three full timber members, four bolt stacks, and all three wood contacts. Verify ownership, volumes, element quality, contact coverage and normals. Freeze material, clearance, assembly/preload, bolt/nut engagement, boundary and load assumptions. Validate only the missing numerical methods, then run a bounded joint response. | Authenticated mesh and contact inputs, audited equilibrium and transferred wrenches, interpretable opening/slip/rotation and bolt/wood actions, with mesh and assumption sensitivity. Solver convergence alone is insufficient. The contact-output benchmark passed its limited checks; current-joint response has not run. |
| 3. Cover all complete joints | Reuse the validated method where geometry, grain, hardware and loading justify it. Evaluate ordinary, tall-center and complete exterior sandwich joints; include both inner-header bolts per side, direct seats, retained host connections and all twelve frame bolts. Close the complete timber/panel contact and attachment graph and all 24 replaced angle duties. | A documented equivalence or separate evaluation for every station; complete center-kicker/header paths and kerf-right edge support. No acceptance by block shape alone, shared part name, or historical pass. |
| 4. Establish full-frame response | Build the current complete-frame model with justified joint response or reduced stiffness and sensitivity. Include current panel/kicker load transfer, dead load, actual recess/sections and conditional no-slip supports. Freeze the model and six source-bound applied-load cases; run heavy/native cases serially. | Fresh six-case reactions, signed member/joint demands, displacements and stability evidence; force/moment closure and numerical/model sensitivity. No arbitrary force split or inherited old actions. Local unit responses are not these load cases. |
| 5. Resolve structural criteria | Apply the [47-item register](current-criteria-coverage.md) to fresh demands. Check complete-joint wood/bolt resistance, axial and lateral interaction, signed grain/end/edge/group effects, washer support/bending, splitting, bearing, finished/net sections, taper/notch/shear/torsion and stability. Confirm method applicability and hardware basis. | Evidence-linked disposition for all 36 inherited criteria and 11 candidate obligations. Unsupported capacities remain unresolved. A failed adopted check or missing path stops the affected operation and produces a specific finding before any model change. |
| 6. Finish fit and use checks in parallel | Extend beyond the 16 priority bolt access screens to all candidate and retained stacks. Check real installation/counterhold/removal envelopes and sequence, tolerances, individual-member transport, panel screw operations, current holds/T-nuts, LEDs and wiring service. Reconcile G6/G12 and any other historical findings against the current model. Restate the hypothetical denser-grid midpoint review separately from actual product compatibility. | Current complete layout/access disposition, explicit unresolved real-tool or physical-observation limits, and dimensioned ordinary-N exceptions where applicable. Feed findings back to mechanics only when analyzed geometry, receivers or paths change. |
| 7. Finish materials, hardware and cost in parallel | Reconcile lumber blanks, grain, finished patterns and drilling variants. Source suitable bolt grades, lengths, shank/thread transitions, nuts and washers for all 92 candidate and 12 retained stacks. Preserve the 66 purchased Hillman policy and do not infer screw properties from another product. Refresh whole-board quantities, costs and weight as selections resolve. | Source-backed hardware/stock schedule and cost range with missing specifications clearly identified. Nominal CAD length is not delivered shank; physical receiving cells remain blank. Sourcing supports final criteria but need not delay explicitly provisional method diagnostics. |
| 8. Integrate and review | Update this plan, the completion ledger, criterion evidence and candidate development instructions from validated outputs. Independently review critical calculations and source bindings. Reconcile drawings, dimensions, hardware, cost, access and result summaries. Commit and push completed chunks outside quiet hours. | One coherent reviewable package and clear pass/revise/unresolved conclusion. Selected authority and historical evidence remain intact; apartment notes remain local. No declaration of MVP-E while required evidence is missing. |

Step 2 includes a zero-load, zero-preload free-mode preflight before signed
force-controlled response cases. Check internal mechanisms for the declared
contact states as well as removal of global rigid-body motion; do not add
artificial restraints or stabilization to obtain a response. A detected
mechanism stops that force-controlled sweep and must be dispositioned before
interpreting stiffness. Unsupported bolt/nut axial engagement remains
`UNRESOLVED_ENGAGEMENT`, not a zero bolt force or an accepted restraint.
Explicitly bounded engagement/stiffness scenarios remain diagnostic only.
The completed contact benchmark is the independent 100 N fixture's corrected
output-accounting re-audit; its original duplicate-time parser rejection is
preserved, and neither result validates current candidate contact behavior.

### Execution changes now in force

- The parent owns the critical path from frozen input through native execution
  and acceptance review. Use one implementer and one focused reviewer per
  dependent deliverable; hand off actual input/output artifacts, not speculative
  schemas. Keep independent Luna/max work active where it advances the plan.
- Exercise each new adapter on the actual frozen artifact promptly. Finish the
  first current joint response before building a general family framework or
  duplicating the preparation across every joint.
- Reuse the current geometry entry point and frozen exports. Do not repeatedly
  rebuild the baseline or repair historical adapters that no current consumer
  needs. Keep the viewer stable; only an identified defect warrants viewer work.
- Run independent lightweight reviews, sourcing and documentation alongside the
  critical path. Serialize heavy/native jobs and shared CAD mutations. Cache
  repeated obstacle bounds when extending access checks; verify equivalence
  before treating cached output as evidence.
- Test changed behavior and the actual integration boundary. Repeat passed
  checks only after relevant changes or a specific unresolved concern. Keep one
  current progress record here and in the ledger; preserve old reports as history.
- Do not alter the reviewed model to make a result pass. Report a required
  geometry change and its affected evidence before implementing it.

The next concrete milestone is step 2's first current-joint response, not another
viewer, planning report, or historical adapter migration. Steps 3–7 may overlap
only where their inputs are ready; all remain necessary for the final package.

The subsequent [execution checkpoint](completion-ledger.md#current-evaluation-checkpoint-september-24-evening)
records completed current mesh, material and contact classification, the full
timber/panel contact graph and all 92 candidate axial-motion screens. These
advance the preparation described in the table. The current rigid-motion
preflight identifies unresolved slip under open bolt-hole clearances; clearance
seating and engagement are the immediate response-model task. No current-joint
or six-case full-frame response has yet been accepted.

## Current priority: evaluate the owner-reviewed model

The owner has approved resuming evaluation of
`led-clearance-2x6-runner-seated-blocks-v1`, reviewed at commit `b1e8707d`.
This supersedes the earlier viewer-phase pause. Use Luna agents at maximum
reasoning effort for bounded independent tasks; the parent owns integration,
frozen inputs and serialized native execution. The current viewer remains at
`http://localhost:8765/wood-joints-wj24-viewer.html`.

The current [geometry packet](hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/README.md)
has 24 blocks in seven finished designs, 92 candidate bolt axes, 66 panel/kicker
screws (58 unchanged and eight recorded moves) and twelve starting frame bolts.
Exterior sandwich blocks are single 2×6 blanks seated on the runners; the tall
central blocks are trimmed, and G2's LED hole/body and wire endpoints move 5 mm
outward. Current geometry must drive the mechanics and receiver checks.
The historical 28-block/104-axis mesh, backer and contact records below do not
transfer by shared part name or by solver convergence.

Begin with focused current fastener/receiver checks and independent method
benchmarks. Establish complete joint inputs and numerical prerequisites before
candidate-native responses and the six full-frame cases. The
[evaluation-resume packet](hypotheses/evaluation-resume-2026-09-24/README.md)
records this work. Open wiring, G6/G12 hold-clearance, panel-edge-support,
assembly and hardware-selection obligations remain explicit. Owner model
review is permission to evaluate, not structural or fabrication acceptance.

## Plan-authoring baseline and non-transfer rules

The [completion ledger](completion-ledger.md) records WJ-00 through WJ-02
complete. This plan's initial WJ-03 snapshot recorded four panel-on nut-removal
paths per side blocked, a 1.0 mm minimum nominal tool gap, and a
`revise_named_constraint` result. A later pre-integration geometry snapshot
raised the post-nut tool gap to 19.0 mm and showed nominal detached-hardware
clearance with the kicker removed. Both reports are historical diagnostics;
neither is the current integrated WJ-03 sequence report or an acceptance.
The connector body's last recorded ordinary-envelope excess was 86.018477 mm.
Its 175.948756 mm excess was temporary bolt-stroke workspace, not permanent
depth. See [outer-node result](outer-node-result.md) for the snapshot boundary.

Keep the kerf-right climbing surface, panel outlines, hold grid, kicker,
all 66 purchased panel/kicker screw axes, and panel-screw policy fixed in this
lane. Map all 24 former angle duties and 144 structural SDS axes to complete
replacement paths; recheck the twelve starting frame-bolt arrangements.
Keep ordinary local-N limits and any named exceptions explicit. No primary
member housing is a default; any proposed house needs its own cut and joint
evidence. Preserve individual-member transport and the no-slip floor
assumption without claiming an anchor or extra floor contact.

The selected angle-frame authority in [`current-candidate.json`](../../current-candidate.json)
and the preserved barrel work do not supply new-joint capacities or case passes.
Do not change selected authority to make this development lane appear complete.

## Current diagnostic checkpoint, 2026-09-24

This checkpoint is source and geometry work only. Component tests and nominal
clearance do not close a stage gate.

The owner confirmed the repository quiet-hours schedule on 2026-09-24:
Monday–Thursday, 07:30 inclusive to 18:00 exclusive, America/Denver with
seasonal daylight-saving transitions, as recorded in the clone's common Git
`QUIET_HOURS.md`. During that window continue local implementation, review and
serialized validation; leave changes uncommitted and unpublished. Outside it,
follow the local resume procedure, finish required validation, and commit and
push the intended increments normally. No further timing permission is needed.
This does not change the selected baseline or development gates.

The owner authorized WJ-09 native mechanics execution on 2026-09-24 after
clarification of the earlier prohibition; see the
[decision record](../history/decision-log.md#wood-joint-native-mechanics-authorization-september-24-2026).
Finish and freeze the candidate geometry, methods, and evidence contract before
running the six cases serially. The later owner sign-off on the current viewer
model now permits joint evaluations to resume. Historical actions cannot
replace fresh demands, and required missing mechanics evidence still prevents
MVP-E completion.
No fresh candidate cases have run at this checkpoint. The
[native adapter readiness plan](native-adapter-readiness.md) identifies reusable
runner infrastructure and the missing candidate-specific mechanics inputs.
The [full-stock input report](hypotheses/wj16-full-stock-mechanics-inputs/README.md)
now extracts eight bolts and four interfaces from the actual WJ16 composition,
with authenticated axes, grain, and contact planes. It provides no fresh
demands, joint stiffness, resistance, or native-readiness acceptance.

### Latest follow-up and next actions

The [complete WJ24 composition](hypotheses/wj24-integrated-static/README.md)
now passes all eighteen implemented static and source-tracking checks. It
contains sixteen rebuilt hosts, twenty-eight connector pieces, 104 proposed
bolt axes and 520 CAD hardware roles. All 24 duties and 144 former SDS axes
map to modeled WJ24 paths, and no legacy angles/SDS or source-only receiver
overlays remain in the proposed layout. This is path mapping, not accepted
replacement: the composition still has zero accepted duties. The 66 fixed
panel/kicker axes, four backer redirects, candidate-shifted center posts and
twelve retained frame bolts reconcile. Eleven focused compositor tests pass.
Three preparation failures and one failed full diagnostic are preserved with
the corrected integration defects.

The layout remains `REVISE`. G1 and G12 provisional rear hold-bolt envelopes
intersect the right bottom-center and top-center cleats by 745.512902 and
562.789151 mm³. The left bottom-center rail face measures 10,385.137652 mm²,
with a 0.984095945 contact-slab material fraction after the E1–E2 passage;
finite area does not establish bearing adequacy. The [continuous LED
extraction screen](hypotheses/wj24-led-extraction/README.md) tests all 132
lights against 842 stationary shapes: G7's 19.25625 mm rearward withdrawal
intersects the lower full-stock cleat by 319.657955 mm³. The other 131 sweeps
have no positive-volume hits in that operation; whole-harness feeding,
support, slack and panel transport remain unproved. A durable access-relief
attempt 03 exists and its canonical README is being updated. This checkpoint
does not report its result; the baseline G1/G12/G7 findings remain open pending
the report and review.

The [source-bound inventory](hypotheses/wj24-hardware-inventory/README.md)
now reconciles 104 proposed bolts, 104 nuts and 216 washers, separately from
the retained frame bolts and Hillman screws. It identifies 52 ordered receiver
pair groups and 28 connector blanks. The [conditional center-axis length
screen](wj24-bolt-length-screen.md) groups its 16 axes as 4 × 4.75 in,
8 × 5.75 in and 4 × 7.5 in nominal lengths; no SKU, supplier, final stack or
receiving dimensions are selected or accepted. The [cost screen](wj24-development-costs.md)
shows a $71.72 each-price subtotal and a $63.96 mixed-pack/loose illustration
for 84 nominal 6-in/8-in comparison bolts plus 104 nuts and 216 washers.
Twenty bolt prices and all 28 timber blank costs remain open; stock, grade,
availability, shipping and tax are unverified.

The compact [WJ24 viewer](wj24-viewer-review.md) is 9,181,070 bytes and has
been browser-reviewed locally. It has not been published; screen-reader review
remains pending. A representative WJ04 physical-steel mesh
([report](hypotheses/wj04-hardware-patch-mesh/README.md)) contains 32 metal
bodies and 62,193 C3D10 elements. An independent 14-point audit recomputed
870,702 positive integration-point Jacobians; response is pending, and this is
not a WJ24 mesh. Five representative finished solids from current WJ24 were
exported to STEP ([reconciliation](hypotheses/wj24-patch-reconciliation/README.md)).
The older WJ16 mesh does not match the changed principal; no WJ24 mesh or
response exists.

Next, review and disposition the durable access-relief report when its
canonical README is ready, then close the integrated access and transport
findings. Resolve delivered hardware stacks and product/receiving evidence,
complete timber stock and full cost, and close the candidate-specific center
backer/header load paths and frozen WJ-08 mechanics contract. Keep the fresh
six-case WJ-09 run gated until its geometry, methods and evidence inputs are
frozen. No duty replacement, assembly, capacity, or release is accepted.

### Preserved integration checkpoints

The accounts below describe their named snapshots. Statements about residual
duties, unintegrated hypotheses and the narrow WJ04 trial are historical;
the WJ24 checkpoint above governs current development work. Preserve their
source-bound reports without transferring acceptance to WJ24.

The active WJ-04 configuration remains
`narrow_x95p25_ordinary_bolt_candidate`; deployed viewer remains at `40b97ecf`.
The completed WJ24 geometry remains a separate diagnostic; its viewer and
registry promotion are pending, and it carries no acceptance. The [part-count review](hypotheses/part-count-and-merge-review.md)
projects 28 connector pieces and 104 candidate bolt positions against the
original 10–14-piece aim. No simple documented merge meets that aim under
current constraints. WJ24 confirms those counts. Review assembly complexity
and costs using that full layout; this is not a new acceptance gate.

The [eighteen-duty composition](hypotheses/wj18-integrated-static/README.md)
now passes all eighteen implemented static/provenance checks. It merges the
top outer pair into WJ16, rebuilds fourteen shared hosts, combines twenty-two
connector pieces and eighty proposed bolt stations, and removes 108 former
SDS axes. Two remaining bottom-rail overlays retain four purchase-length cuts.
The six remaining duties are the two top-center and four bottom connections.
All 66 fixed screw axes and twelve starting frame-bolt arrangements reconcile.
No assembly, capacity, or replacement acceptance follows from these checks.
The separate [top-center pair](hypotheses/top-center-integration/README.md)
now clears its local nominal wood, installed hardware, receiver, and source
reconstruction screens against WJ18. Its two unique tool-envelope overlaps
are between nut tools for different physical bolts; assess sequential
operation before changing geometry. Actual counterhold, turning, tolerances,
and final acceptance remain open. This pair is now included in WJ24.
The representative joint's [coarse mesh](hypotheses/wj04-patch-mesh/README.md)
also passes its implemented quality and independent ownership checks after
two preserved adapter failures. It contains no structural response or
capacity result. The [surface classification](hypotheses/wj04-patch-surfaces/README.md)
now binds all four wood interfaces and sixteen bore/member pairs; a separate
parent audit verifies signed planar mesh normals. The mechanics model and
response remain pending.
The [local validation checkpoint](local-validation-2026-09-24.md) records a
pre-existing selected-baseline source mismatch that stops its required CI
check. Authority/export byte preservation passes independently; do not
interpret that narrower result as a current baseline analysis pass.
The [bottom-outer pair](hypotheses/bottom-outer-integration/README.md) now
clears local nominal wood, installed hardware, receiver-layer and washer-seat
checks against WJ18. Head-tool approaches hit two wire runs, and new rail-bolt
hardware occupies existing WJ03 nut-tool envelopes. Resolve wiring state and
supported operation order; the pair is included in WJ24 but remains unaccepted. The
[bottom-duty investigation](hypotheses/bottom-duty-investigation.md) retains
the source station map. The [bottom-center local report](hypotheses/bottom-center-integration/README.md)
clears installed wood/hardware and washer/layer checks but has a left rail
contact-slab material fraction of 98.4095945%, a G1 hold-projection overlap,
and timber/wire/tool access findings. All six residual duties now have local
diagnostic producers and are now included in WJ24. The disposition of their
contact/access findings remains unfinished; no replacements are accepted.
The [finite-contact supplement](hypotheses/bottom-center-contact-and-hold/README.md)
attributes the entire left contact shortfall to the existing E1–E2 service
passage and measures 10,385.137652 mm² of actual shared bearing face. G1's
provisional hold envelope first intersects the right cleat 10 mm behind the
panel. Neither finding establishes bearing adequacy or an acceptable hold-bolt
length; both remain explicit mechanics/access obligations.

The [corrected twelve-duty composition](hypotheses/wj12-integrated-static/README.md)
now passes all seventeen implemented static/provenance checks. It reconstructs
eleven joint hosts and combines sixteen connector pieces, 56 proposed bolt
stations, and all 66 fixed screw axes. Five additional canonical finished
rails receive twelve candidate-only purchased-length cuts, independently
replayed against the source. This resolves the twelve 157.513719 mm³ overlaps
preserved in the [first combined run](hypotheses/wj12-before-receiver-completion/README.md).
Raw receiver material and clearance are present at all 66 axes; this is not
an embedment, support, or load-path acceptance. The twelve retained frame-bolt
arrangements reconcile as 60 installed components plus twelve axis proxies.
The [sampled cut sections](hypotheses/wj12-sampled-sections/README.md) now
quantify representative bevel, crosscut, wire-relief, and both backer
counterbore/bolt planes. These are local geometry measures, not minimum
sections or adequacy checks. Continue capacity-independent backer/contact
mechanics and bounded left-service investigation before broad replication.
The [backer unit-wrench witnesses](hypotheses/wj12-backer-unit-statics/README.md)
now close all twenty-four signed synthetic cases with finite patches checked
in both actual finished members. Actual demands, fastener bearing, wood and
washer resistance, and complete backer/header acceptance remain open.
The [remaining-duty sequence](hypotheses/remaining-duty-sequence.md) records
their host pairs and the left-side kerf/service asymmetries that prevent
blind mirroring or reuse of the older residual-probe scope.
The [left service diagnostic](hypotheses/left-service-integration/README.md)
now reconstructs all four left hosts and clears its local sixteen-stack
nominal screens with the full-depth upper inner cleat. The sixteen-duty
composition now integrates those shared-host cuts and rechecks the combined
scene; WJ18 now extends that integrated static evidence with the top outer pair.

The [upper-right rail motion diagnostic](hypotheses/wj12-right-rail-motion/README.md)
now uses all six panels and the complete finished-wood obstacle map. The seated
pose clears, but the +25 and +50 mm N samples intersect five modeled wire runs;
negative motion also intersects panel/hold geometry. Clear distant poses do
not establish a path. Investigate supported panel/wiring staging before
accepting assembly, reverse removal, or transport; no wire disconnection or
new machining is inferred from this report.

The [WJ18 harness topology probe](hypotheses/wj18-panel-harness-topology/README.md)
now maps all 132 lights to the four main panels. Twelve wires cross panel
boundaries; neither factory string connector lies at one of those crossings.
Unplugging only the supplied string connectors therefore does not isolate the
panels. Investigate reverse whole-strand feeding and supported bulb/panel
handling under the existing lights-last passage concept, without inferring
wire cutting or treating an unwired build as a transport solution.

The [WJ16 unwired continuous enclosure](hypotheses/wj16-unwired-rail-sweep/README.md)
now finds no positive-volume intersection through 0–200 mm +N translation
of the same rail subassembly against 839 stationary shapes. Five zero-gap
timber contacts remain. The entire lighting harness is not yet installed in
this modeled initial-build state; this does not resolve the wired transport
path, support, tool access, or tolerance clearance.

The [right four-duty report](hypotheses/right-rail-integration.md)
now completes: all four native source hosts reconstruct at zero reported
symmetric difference, sixteen modeled stacks are present, and all implemented
installed-geometry checks pass. Installation, complete-layout clearance,
tolerances, and capacity remain open. Parent verified the archived input
hashes; no authority, acceptance count, or viewer was promoted.

Earlier right-adapter attempts are implementation history. The first
materialized family geometry for 66.77 s,
then stopped assembling the combined report on missing
`wj04_base._source_inventory`. After loader repair, the second stopped at a
source-reconstruction mismatch of 1,260.109751 mm³ for
`base_principal_center_right`; eight extra candidate purchased-length cuts
explain the principal delta. The separate rail-hole mismatch is also traced:
each rail's three outer-duty SDS axes shift by −3.175 mm through
`WidthAdapter.connections`, while finished-rail trim retains the original
holes. Official native cuts reconstruct 0/0; the per-host translated side
requires shifted cuts. The repaired adapter separates per-host native cuts
from candidate purchase cuts. The later report also corrects a candidate-cleat
lookup in the machining summary. No reconstruction tolerance was waived.
Static review of shared-host machining and the 6.604 mm WJ-06 side-shaft
occupancy sensitivity is complete; nominal shaft diameter remains 6.35 mm,
and sensitivity adds no strength claim. The [exact WJ-03 coaxial-cylinder
supplement](hypotheses/wj03-head-withdrawal-exact-shaft.md) has run: all 20
shafts clear fixed obstacles and all four separately sampled counterhold
headings, the 80 coarse self-bore/washer hit pairs disappear, and there are no
exact-only hits. This sampled shaft result alone does not establish physical
access. The subsequently
archived [bound route summary](hypotheses/wj03-head-withdrawal-bound-summary.md)
now records 244 clear sampled combinations at 14 of 20 stacks. Six stacks
retain counterhold or detached-hardware exit proxy overlaps against the
under-header links or bottom rails. The separate
[maximum-shaft sensitivity](hypotheses/wj03-head-withdrawal-max-shaft.md)
clears all 20 installed and withdrawing shafts at 6.604 mm occupancy, but
does not retest complete tool routes against enlarged peer shafts. Neither
result accepts a complete removal sequence.
The twelve-duty hypotheses now share one coherent static diagnostic model;
the viewer awaits parent review and the end of quiet hours. Mechanical review
found no categorical topology incompatibility. Run bounded,
capacity-independent checks for net sections (bevels, G7 crosscut, center
relief, backer counterbores), backer-to-header resistance, and signed wrench
closure/contact/bolt-demand triage. Use historical actions as diagnostics;
these results inform the parent’s broader-replication choice, not a new gate.
Native execution is authorized after model/method readiness. Keep the deployed viewer and active registry
unchanged until parent review.

- **WJ-03:** the current `wj03-sequence-diagnostic.json` includes the WJ-05
  diagnostic backers, shifted posts, bolts, stacks, and four center receiver
  IDs. All 42 nominal screw/tool and withdrawal screens, both 250 mm lower
  panel extractions, and both staged 100 mm kicker extraction/reverse paths
  show no sampled unrelated hits. The earlier pre-helper report at checkpoint
  `0ebf90eb` recorded 35 right-return LED endpoint hits; the current report
  clears them after candidate-only fixed-service-bore machining. The earlier
  mismatch came from the kerf-right panel and its LED bores shifting
  `-KERF_EACH_MM` while electrical parts remained at their fixed source
  datums, with different endpoint sampling on outbound and return. The
  correction is candidate-only; it does not edit the selected baseline or
  source inventory. The left return was already clear. Kicker motion still
  overlaps the lower panel by 1–18 mm when it stays installed, while extraction
  and return pass after the lower panel is staged. No LED disconnection is
  needed or inferred. Both the staged panel at 250 mm and kicker
  at 25 mm have 0 mm nominal gap to base-floor wood. The last body geometry
  report measured 225.718477 mm permanent rear projection, or 86.018477 mm
  beyond the ordinary 139.7 mm reference. These diagnostics do not close a
  gate; retain `revise_named_constraint` pending a dimensioned
  permanent-envelope disposition and support, continuous-motion, and tolerance
  evidence.
- **WJ-04:** the active config is
  `narrow_x95p25_ordinary_bolt_candidate`: a 95.25 × 38.1 × 119.7 mm cleat,
  grain N, K.L. Jack `25C375HCS5Z` rail and `25C600HCS5Z` principal bolt
  candidates, `25CNFH5Z` nuts, and two Type A Wide washers per stack. The
  current probe is config-bound: the cleat has 0.0 mm nominal ordinary-N
  excess, modeled stacks and washer seats clear locally, a generic 50 mm rail
  tool envelope has 0.764 mm gap, and the temporary nut exit exceeds the
  ordinary limit by 21.872532 mm. Conditional end/edge references remain
  unresolved by signed loading. Mechanics now consumes the probe's finite-probe
  rail contact area (11,401.398713 mm²) and lists the canonical 11,401.425 mm²
  bounding rectangle separately (−0.026287 mm² delta); principal values
  reconcile within rounding. The 95.25 mm X width can be cut from a 2×6,
  but ripping changes the stock grade; post-rip regrade evidence or another
  traceable source is required. The current early mechanics report uses six
  historical angle-demand cases without replay; each has four mismatched
  source files, and no fresh candidate demand/capacity is established. The
  current tool-access report remains `diagnostic_overlap_present`. Its
  corrected placement centers the modeled 3.0 mm wrench slab within the target
  head/nut axial thickness. In the broad 22 mm envelope and two synthetic
  headings, head counterhold clears at both upright stacks and overlaps at
  both rails; the paired-wrench envelope clears at all four. Nut stroke/reindex
  and the full-turn wrench-plus-axial nut-removal bound overlap at all four.
  Separate loose-nut and nut-washer translation sweeps clear at the uprights
  but overlap at the rails. Bolt withdrawal clears at all four, and head-washer
  removal overlaps at the rails but clears at the uprights. These bounds
  establish neither actual access nor impossibility;
  actual jaw fit, handle sweep, and placement remain unverified. The principal
  bolts have 19.05 mm T-edge distance versus a
  conditional 25.4 mm perpendicular-grain loaded-edge 4D reference. Signed
  demands remain unresolved; this is not a universal failure claim, but the
  narrow trial cannot satisfy that criterion if a nonzero ±T lateral component
  governs. The 100 × 53.34 mm pose remains an unbound
  alternative; it has no matching stock, bolt, tool, or mechanics bundle. The
  cataloged FACOM wrench pair is a tool candidate, not proof of installed
  access or working sweep.
- **WJ-05:** fresh transfer and receiver reports remain diagnostic. They keep
  all 66 axes fixed, route 62 into frame timber and four into two separate
  backers, and report 2.959434 mm seated and 1.661248 mm full-sweep nominal
  wire clearance at the repaired right upper socket station. The receiver
  audit remains `blocked_center_receiver_path`: four center structural duties
  and both backer/header attachments lack accepted load paths. The socket
  model omits internal 12-point fit, ratchet/extension space, tolerances, and
  actual access.
- **WJ-06:** the active duty registry still maps 24 duties and 144 former SDS
  axes, preserves 66 Hillman axes and twelve frame-bolt obligations, records
  geometry for 5/24 duties, and accepts zero replacements. Its residual-probe
  entry still has 540 potential generic corridors, none materialized there,
  and replacement complete-stack evidence remains zero. Separate commit
  `b69ca5fa` now materializes installed-state geometry for two far-end right
  rail pairs; the later [right four-duty integration](hypotheses/right-rail-integration.md)
  now completes its implemented static checks. These hypotheses do not change
  registry counts or acceptance. Verify complete interfaces and stacks before
  updating any acceptance count.

### Isolated installed-fit hypotheses, 2026-09-24

These follow-up screens do not change the active
`narrow_x95p25_ordinary_bolt_candidate`, selected source pins, or deployed
viewer. None is integrated, promoted, or accepted.

- **WJ-03 compact outer bevel** (`c99751db`,
  [archived probe](hypotheses/wj03-compact-outer-probe.md)) trims the connector
  rear bevel to N = 137.7 mm, leaving 2 mm nominal reserve to the ordinary
  envelope. Installed hardware, timber, and protected-geometry screens clear.
  Its separate [compact access archive](hypotheses/wj03-compact-outer-access.md)
  reports six body-removal translations, 40 shaft/head checks across 20 bolt
  stations, 42 panel-screw tool/withdrawal proxies, and lower-panel-first
  kicker extraction/return clear in sampled geometry. The [outer tool
  archive](hypotheses/wj03-compact-outer-tools.md) reports all 40 coaxial
  socket approaches clear, four socket-plus-nut exits overlapping under-header
  links, two nut-washer slides hitting base rails, and no tool proxy below the
  analytical z = 0 plane. Its broad FACOM full-turn envelope overlaps all 20
  stacks; the report proposes turning/withdrawing the bolt from the head side
  while holding the nut stationary, then removing the nut and washer. These
  operation screens do not establish actual tool fit, continuous motion,
  physical floor clearance, or acceptance; this hypothesis is not integrated.
  The [head-withdrawal report](hypotheses/wj03-head-withdrawal.md) now screens
  20 stacks: seated socket envelopes clear all 20; broad shaft boxes hit the
  same stacks' own receiver bores and washer rings all 20, a conservative-box
  artifact rather than demonstrated blockage. Ratchet and washer-exit proxy
  hits remain as reported. The [exact coaxial-cylinder supplement](hypotheses/wj03-head-withdrawal-exact-shaft.md)
  clears all 20 nominal shafts against fixed geometry and all four separately
  sampled counterhold headings (20/20 each). It removes 80 coarse self-bore/
  washer pairs and reports no exact-only hits. Minimum Z is 126.251 mm above
  the analytical floor. This nominal proxy result does not establish physical
  tool fit or a complete removal route; the bound route summary above retains six unresolved stacks.
- **WJ-04 upper G7 crosscut** (`5555c646`, [archived probe](hypotheses/wj04-upper-g7-crosscut.md)) crosscuts the upper cleat and reverses its upper-rail bolt stack. Bodies, stacks, and all 16 washer seats clear, but all four rail-bolt insertion paths are blocked with neighboring parts retained. The duty-registry workstream is planning rail-plus-cleat subassemblies outside the frame.
- **WJ-04 local +N access** ([refined sampled screen](hypotheses/wj04-pair-access-local-n.md)) tests lower and upper right rail/cleat moves with far-end duties retained. Each move has eight distinct obstacle pairs with sampled exact intersections: three retained outer-duty SDS beams and five service wires. The report remains an unaccepted discrete screen; it proves neither continuous blockage nor a physical route.
- **WJ-05 center wire-relief** ([archived probe](hypotheses/wj05-center-node-relieved.md)) clears the L = 82 mm wire-relief body geometry. The right station is 2.303793 mm from the wire; the mirrored left result is a 9.25 mm bounding-box lower bound. It retains 48 + 18 fixed axes. Two properly seated generic head-tool proxies overlap the center posts at upper-header row 2 (left and right), 1,481.459916 mm³ each. This generic proxy-to-wood screen establishes neither actual wrench access nor a complete operation path; see the catalog-sized comparison below for current tool-envelope evidence.
- **WJ-05 center tool screen** ([catalog-envelope comparison](hypotheses/wj05-center-tools/README.md)) records overlaps for socket/extension, counterhold, and ratchet proxies at both upper-header row-2 stations. Opposite ratchet strokes still hit lower-post washer/timber. These are external envelopes, not proof of tool fit or impossibility; the separate ±190 mm trial below screens a preferred modeled route.
- **WJ-05 ±190 mm center-post variant** ([corrected geometry archive](hypotheses/wj05-center-post-x190/README.md)) moves both posts, lower cleats, and eight lower axes outward 10 mm. The corrected report is `nominal_geometry_clear_diagnostic`: body, bore, installed hardware, receiver, washer-seat, contact-face, wire, and preferred modeled tool-route checks pass. Rejected ratchet sectors retain diagnostic hits. This variant widens post and lower-bolt-group spacing while reducing upper-cleat/post overlap; fresh mechanics, physical access, and complete-joint evidence remain open.
- **WJ-06 right outer paired rails** ([installed-geometry archive](hypotheses/wj06-outer-pair.md), `b69ca5fa`) materializes two far-end right rail-pair geometries and eight provisional bolt stacks. It is static installed geometry only; whether +N insertion needs side release is untested. The next screen tests the rail and two cleats moving +N with principal/side members retained and X bolts absent. Assembly sequence, wrench access, and capacity remain untested. The later [four-duty integration](hypotheses/right-rail-integration.md) combines both rail families and passes its implemented static checks. It reconstructs all four hosts from native cuts before applying candidate purchase cuts and sixteen stack bores. No replacement is accepted.

The right-adapter loader, native replay, and candidate-cleat report-key
failures are preserved as implementation history in the latest-follow-up
section and the integrated report note. Its successful report includes the
6.604 mm ordinary-body occupancy sensitivity for the four WJ-06 side-bolt
shafts; nominal modeled steel diameter remains 6.35 mm. Neither that
sensitivity nor static clearance establishes an installation route or
capacity.

Keep these as separate hypotheses. Continue tool, withdrawal, and staged-motion
work against retained obstacles; integrate only after parent review of
source-bound results. Parent is deciding whether to proceed with or revise
replication of the remaining twelve duties after the count review; this is a
planning choice, not a new acceptance gate.

No joint has accepted resistance or capacity. MVP-L, fresh six-case evidence,
and MVP-E remain gated by the work below.

## Critical path

This table retains the original stage obligations. Development now uses the
complete WJ24 diagnostic, including its compact outer-node revision and
full-stock ordinary cleats. The narrow WJ04 trial remains preserved in the
registry, but is not the geometry being prepared for mechanics. Rebind each
affected stage to the reviewed final WJ24 revision before closing it; narrow
trial dimensions, old tool routes and old demands cannot establish its pass.

| Stage | Work | Gate to advance |
| --- | --- | --- |
| **1. Repair outer nodes (finish WJ-03)** | Preserve the final candidate-only service-bore correction and lower-panel-first order before kicker extraction/return; kicker motion with the panel installed still overlaps. No LED disconnection is needed or inferred. Resolve the +86.018477 mm permanent rear projection by a dimensioned geometry revision or named exception; verify the separate temporary bolt-stroke workspace. | Both sides have feasible stock/cuts, complete transfer paths, supported washer seats, the required staged removal order, tolerance-aware installed and removal clearances, and a recorded `advance_layout` result. Keep `revise_named_constraint` until the permanent disposition and remaining local sequence checks pass; do not defer required WJ-03 work to WJ-07. |
| **2. Prove one ordinary joint (WJ-04)** | Keep every consumer bound to `narrow_x95p25_ordinary_bolt_candidate` at `clip_horizontal_lower_right_1`. Probe/mechanics contact areas now share the finite-probe basis; the mechanics report lists the canonical rectangle separately as a coordinate audit. The probe's 0.764 mm generic 50 mm rail-tool gap and 21.872532 mm temporary nut-exit excess are unchanged; neither is a tolerance pass. The refreshed tool screen centers its 3.0 mm slab within target head/nut thickness. Paired-wrench and upright counterhold bounds clear; rail counterhold, nut stroke/reindex, and full-turn wrench-plus-axial nut-removal bounds overlap. Loose nut/washer translation sweeps clear at upright stacks and overlap at rails. Replace broad envelopes with source-supported wrench geometry and a bounded operation path; neither clear bounds nor overlaps prove actual access or impossibility. Rebuild mechanics only on fresh candidate actions; the current early screen uses stale angle-demand inputs. Resolve conditional end/edge geometry with signed loads, and use the 2×6 rip only with post-rip grade evidence. | One complete nominal and tolerance-aware joint with a traceable stock/cut route, matched geometry/hardware/tool/mechanics, an evidenced disassembly path, fresh demands, and signed end/edge treatment. List only station families whose geometry can reuse it; screen mirrored and service-different stations independently. |
| **3. Close center and kicker subsystem (WJ-05)** | Preserve the fresh nominal transfer and receiver reports as diagnostics. Complete the four center principal/header and moved-post/header structural duties, both backer/header attachments, and both inner kicker edge supports. Recheck E1/G1, T-nuts, LEDs, wire, and all twelve retained frame-bolt arrangements. | The 66 axes retain supported finished-wood receivers and required embedment; center and edge-support load paths reach the frame through accepted joints. Each backer attachment and complete joint has evidence; socket outside-envelope clearance is not treated as tool fit. |
| **4. Finish whole-frame geometry (WJ-06)** | Assign one accountable replacement owner to every former angle duty. Add residual top, rail, inclined, and splice details only where the actual topology needs them. Generate one source-bound finished-part model and viewer, including all new and retained fasteners and all machining. | Exactly 24 duties and 144 removed SDS axes reconcile with physical interfaces; all 66 fixed screw axes and twelve rechecked frame-bolt arrangements appear; no legacy structural SDS path survives; part, assembly, bolt, and move-operation counts are separate. |
| **5. Close MVP-L (WJ-07)** | Run complete installed, tool, insertion, reverse-removal, same-family, cross-family, protected-service, floor/pad, and tolerance screens on the integrated model. Define manufacturable cut setups, tool needs, and forward/reverse assembly order. | No known unintended collision or unsupported seat; required separations stay positive under stated dimensional bounds; every joint can be assembled and removed without routine structural wood-thread removal. Publish a complete owner-reviewable layout with limits, not a drilling release. |
| **6. Freeze mechanics before final cases (WJ-08)** | For every host and connector interface, define unilateral contact, opening, bolt tension/lateral action, slip, rotational stiffness, reference point, and all three moment components. Check finished wood sections, end/edge/grain directions, splitting, bolt groups, connector internal joints, washers, bolts, retained frame bolts, and any house shoulders. Migrate all 36 frozen legacy safety questions plus the 11 new obligations in [`criteria.json`](criteria.json) with an applicable method or explicit reason. | A fingerprinted, fail-closed candidate and check contract. No unknown resistance or inherited angle capacity is marked pass. Select bounded stiffness/contact sensitivities before solving. |
| **7. Run fresh complete-frame evidence (WJ-09)** | Run the six required cases serially on one frozen candidate. Authenticate geometry, producers, convergence, force sources, simultaneous signed interface actions, monitors, and check outputs. Revise failed joints or methods, then rerun every affected case and check. | All six source-comparable cases meet numerical prerequisites and every applicable adopted/new criterion has a supported disposition. Report governing case, mode, and margin; retain failed and nonconverged runs as diagnostics. |
| **8. Deliver MVP-E packet (WJ-10)** | Generate coordinated cut/drill/hardware, cost, assembly, and inspection documents from the same frozen model. Bind actual proposed stock, hardware SKUs/specifications, delivered-length and tool assumptions, whole-stock yield, quantities, and costs. Leave Actual/Disposition fields blank until observed. Obtain an independent review of the finished geometry, mechanics, evidence, and shop instructions; fix confirmed findings and rerun affected gates. | One internally consistent conditional development packet and completion ledger with no contradictory instruction or unresolved required load path. Record every remaining receiving or physical-observation condition precisely. |

## Avoid a late mechanical dead end

Before copying the WJ-04 workhorse to many stations, run a **bounded
representative mechanics screen** on the WJ-03 and WJ-04 joint topologies.
Use actual interface graphs and load directions, but label old-case actions
as diagnostic until the new full-frame solution exists. Reject an obviously
unworkable split, washer, bolt-group, or connector-body detail early. This
does not replace WJ-08's complete method contract or WJ-09's fresh demands.

## Decision and evidence discipline

- Each stage returns `advance`, `revise_named_constraint`, or `blocked` with
  exact geometry, method, source, and remaining obligation. Do not infer a
  pass from an empty collision list, a single force component, or a favorable
  diagnostic case.
- Select real bolt, nut, washer, stock, and tool dimensions before claiming
  tolerance-aware MVP-L. Until then, label occupied shapes and bores as
  provisional, never as drilling instructions.
- A failed adopted criterion, missing load path, contradictory shop instruction,
  or incompatible delivered part stops the affected operation. Do not add
  external sign-off, floor-friction testing, or unrelated redesign as blanket
  prerequisites.
- After MVP-E, make an explicit owner decision whether to select this
  candidate. Selection is not automatic and does not fill unobserved physical
  receiving cells. WJ-11 records delivered parts, actual cuts/holes, assembly,
  disassembly, and deviations if a prototype is built.

## Historical progress and review notes

The following pre-integration snapshots remain as reasoning history; they are
not the current WJ-03 sequence or active WJ-04 probe. The old sequence report
recorded 42 adjacent-panel/kicker screw tool and withdrawal sweeps without
unrelated nominal hits, but lacked the four WJ-05 backers. It sampled direct
kicker hits at 1–18 mm, no sampled hits on a 100 mm path after staging the
lower panel, and 0 mm lower-panel clearance to the base-floor member at the
staged pose. Support, continuous movement, handling, service disconnection,
real tool access, and tolerances were open. Its short nut/washer disengagement
path had no hardware capture or retrieval method. The 86.018477 mm permanent
rear excess and 175.948756 mm temporary bolt-stroke workspace were reported
separately. The old WJ-04 report used a 95.25 × 50.8 × 119.7 mm cleat with a
generic 50 mm tool collision and a 3.652 mm 40 mm-tool gap. It is not evidence
for the current 95.25 × 38.1 mm configuration.

The earlier WJ-03 geometry review found that shortening the under-header link
moved its first header bolt 30.1 mm from the grain end instead of 48.1 mm,
using a provisional 6.35 mm bolt. That is a geometry tradeoff, not a signed
end-distance verdict. The temporary-stroke excess is workspace, not permanent
depth. The historical link geometry still needs a complete integrated tool,
support, service, movement, and tolerance screen before reuse.

## Next decisions and gates

1. **Preserve the integrated records.** The final WJ-03 report includes current
   WJ-05 geometry and the candidate-only service-bore correction. The prior
   right-return endpoint hits are historical; the current return is clear.
   Keep refreshed artifacts bound to their source fingerprints and preserve
   the lower-panel-first kicker order.
2. **Resolve the WJ-03 geometry and sequence gates.** Choose a dimensioned
   geometry revision or a named exception for the 86.018477 mm last-reported
   rear excess against the ordinary 139.7 mm limit. Confirm the separate
   bolt-stroke workspace and positive tolerance margin for both staged poses.
   Keep `revise_named_constraint` until the permanent disposition, support,
   tolerance, and local sequence checks are resolved.
3. **Keep WJ-04 on one matched trial.** The active diagnostic config is
   `narrow_x95p25_ordinary_bolt_candidate`; it uses a 95.25 × 38.1 × 119.7 mm
   cleat, grain N, K.L. Jack 3.75-in rail and 6-in principal candidates, and
   two Type A Wide washers per bolt. The 100 × 53.34 mm pose is unbound until
   stock, bolt grip, delivered thread engagement, tools, tolerances, and
   mechanics all match. The cataloged FACOM `34.7/16` wrench pair is only a
   tool candidate. The updated conservative screen centers its modeled slab
   axially on the fastener and clears paired-wrench/upright counterhold
   envelopes, but remaining overlaps and unsupported jaw/handle geometry leave
   actual install/removal access unproved. The 2×6 rip is only a raw-stock lead
   until post-rip grade evidence exists. No joint or capacity is accepted.
4. **Complete WJ-05 load paths.** Fresh transfer and receiver reports are
   nominal geometry diagnostics. The four center screw receivers terminate in
   separate backers; two provisional bolts per backer do not establish the
   backer/header joint. Complete those two attachments and all four
   principal/header and moved-post/header duties, with tool access and
   mechanics, while retaining all 66 screw axes and rechecking all twelve
   starting frame-bolt arrangements.
5. **Keep the duty registry source-bound.** Current registry covers 24 duties
   and 144 former SDS axes, preserves 66 screw axes and twelve frame-bolt
   obligations, records geometry for 5/24 duties, and accepts zero
   replacements. Its residual-probe entry still lists 540 potential WJ-06
   corridors with none materialized in that registry; its replacement
   complete-stack evidence count remains zero. The separate WJ-06 paired-rail
   geometry remains a hypothesis, outside registry acceptance. Regenerate
   only if a bound input changes; source binding alone does not accept a
   connection.

Only after source-bound geometry, methods, tolerance screens, and complete
joint evidence pass should WJ-08/WJ-09 work begin. Do not launch native
six-case work from component tests, receiver continuity, or nominal clearance
alone.
