# Wood-joints MVP orchestration plan

## Current evaluation checkpoint, September 24 evening

The owner has reviewed `led-clearance-2x6-runner-seated-blocks-v1` and explicitly
resumed evaluation with Luna/max agents. This supersedes the viewer-phase pause
and the historical layout counts below. The current model has 24 blocks in
seven designs, 92 candidate bolt axes, 66 panel/kicker axes (58 fixed and eight
recorded moves), and twelve starting frame-bolt arrangements. Geometry review
is permission to evaluate, not structural acceptance. The parent owns frozen
inputs and serialized native execution. Current evidence is collected in the
[evaluation-resume packet](hypotheses/evaluation-resume-2026-09-24/README.md).
The selected angle-frame and historical evidence remain preserved.


Status: active parent-owned persistent goal, 2026-09-24.

## Owner-directed viewer phase, September 24

The owner now requests a 3D model MVP and design review before further
engineering calculations. Prioritize the local viewer and owner design
adjustments. Hold mechanics implementation, native runs, and additional
engineering calculations until that review is complete. Preserve existing
diagnostics and unfinished work as checkpoints; no previous pass transfers to
a changed design. The broader conditional engineering MVP remains unfinished.
The owner explicitly requires a further sign-off before joint evaluations
resume. Finish the current kicker-post relocation, center-backer removal,
outer-rim sandwich blocks and center-principal/header block redesign, then
notify the owner and wait for that sign-off.
The local WJ24 viewer is served at
`http://127.0.0.1:8765/wood-joints-wj24-viewer.html` by parent tool session
`27963`. Quiet-hours publication restrictions remain unchanged.

## Resumed session, September 24, 15:14 Denver time

The owner reloaded the session and requested useful saturation of the new
twenty-subagent limit. The parent recovered the preceding conversation and
current working tree, restored the full MVP goal, and verified twenty workers
running concurrently. The older allocation table below is historical. Existing
tracked edits, untracked implementations, and diagnostic archives are retained.
No prior Python/CAD session or full-test process survived the reload.

The complete WJ24 composition remains the current integrated diagnostic:
24 duties, 28 connector pieces, 104 proposed bolts, and zero accepted
replacements. The public viewer and selected authority are unchanged. The
local viewer HTML expects the new compact encoding, while its scene still
contains the earlier large payload; regenerate and browser-check them together.
The interrupted full pytest log reaches approximately 46% and contains
failures, without a final summary. It is not a completed validation run.

| Worker | Bounded responsibility |
| --- | --- |
| `access_relief` | Connector-only G1/G12 hold and G7 LED relief experiments and producer checks. |
| `steel_mesh` | Physical hardware mesh adapter and independent output audit. |
| `contact_adapter` | Authenticated contact surfaces and preparation fragments. |
| `joint_boundary` | Representative unit-load, restraint, and free-mode contract. |
| `material_contract` | Explicit orthotropic scenario and material-axis validation. |
| `reaction_accounting` | Signed interface wrenches and equilibrium accounting. |
| `hardware_lengths` | Sixteen unresolved bolt lengths and conditional stack fit. |
| `hardware_costs` | Source-backed quantities, package prices, and unknown costs. |
| `timber_yield` | Connector blanks, grain, and bounded stock yield. |
| `viewer_review` | Complete-layout viewer behavior and browser verification. |
| `test_triage` | Interrupted test failures and bounded reproduction planning. |
| `transport_sequence` | Complete-layout assembly, support, and harness dependencies. |
| `full_layout_tools` | Bolt-station tool and removal evidence coverage. |
| `backer_loadpath` | Redirected screw receivers through backers and headers. |
| `frame_bolts` | Twelve retained frame-bolt obligations in changed hosts. |
| `fixed_receivers` | All 66 fixed axes, receiver support, and kerf-right edges. |
| `geometry_reconcile` | Earlier representative mesh versus complete-layout geometry. |
| `criteria_coverage` | Candidate-specific demand and resistance evidence gaps. |
| `source_integrity` | Independent source hashes and preservation audit. |
| `shop_packet` | Coherent development packet using the bounded outputs above. |

Each worker has separate file ownership. Parent owns integration, archived
report generation, and serialized heavy CAD, mesh, and native execution.
The first physical hardware mesh was launched only after its adapter, tests,
dependency hashes, and pinned container invocation were rechecked. This is
mesh preparation, not a structural response. Failures remain evidence.

At 15:26 the owner asked whether multiple local processes could run together.
The parent measured sixteen logical CPUs, approximately 18 GiB available of
29 GiB RAM, a one-minute load of 0.85, and no current memory or I/O pressure.
The earlier blanket CAD/verification serialization is therefore relaxed to
two independent jobs with separate outputs and monitoring. Shared live-model
writes and native load-case runs remain serialized under parent control.

After the owner's velocity question at approximately 16:05, the parent
rechecked resources: about 17.2 GiB remained available, with no current memory
or I/O pressure. Up to three independent local jobs may overlap when they
have separate outputs and bounded memory. This allows a mesh or numerical
audit alongside the full test suite and one live CAD operation. The shared
Python/CAD session still accepts only one operation at a time, and native
solver cases remain serialized. Stop adding jobs if resource pressure appears.
Agent priority is now the representative mechanics pipeline and the complete
layout's access/hardware decisions. Defer supplementary reports and optional
helper features; use one implementer and one reviewer per critical deliverable.

Denver quiet hours continue until 18:00: leave work uncommitted and unpublished.
Weekly usage at resume was 26% used, 74% remaining; retain the owner's stop
instruction at 20% remaining and check fresh telemetry during continued work.

### Subsequent parent integration checkpoint

The full WJ24 model was reconstructed in 290.10 seconds using one shared
right-family source object throughout WJ12 and WJ16. Its composition report
exactly equals the archived WJ24 report, with all 68 input hashes unchanged.
The recovery record is `/tmp/wj24-session-recovery-20260924-attempt01/`;
the live parent Python process is tool session `37771`. Reuse its `g16`,
`g18`, and `g24` objects after confirming the process remains live.

The compact viewer export now exists: 9,181,070 bytes, scene SHA-256
`b80baec6b4435f4cfad724efdc25df787d04251f1a1b7203ba63782fb4b485f0`.
The export completed in 12.47 seconds without source changes and reused the
same-configuration static diagnostic. Browser review now passes the implemented
desktop/mobile, layer, camera, keyboard, and error checks; parent reviewed the
desktop and 320-pixel screenshots. Nothing is published. Its launch record and frozen sources
are in `/tmp/wj24-viewer-resume-20260924-attempt01/`.

The [physical hardware mesh](hypotheses/wj04-hardware-patch-mesh/README.md)
and independent deck audit are archived. Parent's separate 18-test batch for
the material and equilibrium helpers passed; later portability/completeness
edits require their own validation. The independent geometry comparison now
proves four representative bodies unchanged, while the principal loses
6,732.825756 mm³ and gains 6,944.063705 mm³ through four new bolt bores and
six removed legacy holes. The old principal mesh is not the final geometry.

Access-relief attempt 01 stopped before geometry on an adapter schema defect:
it incorrectly required source-bundle names and trial names to match. Actual
WJ24 has nine bundles and ten trials. The corrected producer validates each
set independently and the exact 68-path merged closure. Attempt 02 completed
in 50.80 seconds, preserving source geometry and all fixed axes. Both attempts
are now archived in `hypotheses/wj24-access-relief/`. Parent and independent
review found a conservative summary bug: four bolts have eight washer seats,
all individually resolved, but the aggregate expected four. The producer is
corrected in the v2 producer to distinguish eight seats, local section losses
versus an unchanged sampled minimum elsewhere, and nominal LED motion versus
an enlarged clearance envelope. Attempt 03 completed in 55.0528 seconds with
source hashes unchanged. All nine variants retain the local contact and eight
washer-seat probes; local sampled area losses remain explicit. The nominal G7
LED route clears the relieved wood but intersects two fixed wire envelopes.
No relief or handling sequence is accepted. The retained parent Python session
is idle and remains available; confirm it is live before reusing it.

The separate steel Jacobian audit has also completed: all 870,702 recomputed
integration-point determinants are positive. The equilibrium helper was made
independent of CadQuery without changing existing `mini_moonboard` sources;
its new pure-wrench module, wood/steel material helpers, equilibrium checks,
and independent Jacobian audit pass the parent's 49-test batch.
The metadata-only cross-packet equality bug is repaired in two historical
bolted-screen producers, with geometry-mismatch regressions. The stale native
input test's exact expected mismatch set was updated to include the
historically attributed September 22 kerf-right CSV change, leaving its saved
hashes and non-ready state untouched; its focused 12-test batch passed. The
current full-suite process started at 15:37 and has passed 45% progress with
at least one failure marker; wait for its terminal trace before claiming a
result. Its handle is `79198`, log
`/tmp/wood-joints-full-pytest-20260924-1537.log`.
Weekly telemetry most recently showed 71% remaining.

The current WJ24 representative five-body STEP export completed with
reconciliation SHA-256
`256af45c2a6b2b48726d86f95e2f4febdd8cad726d690738e9cb1fad87a89711`.
It has its own WJ24 schema and does not reuse old mesh geometry. The separate
WJ24 mesh attempt 01 completed in 13.8156 seconds: 89,743 nodes and 46,629
C3D10 elements across five current bodies. Output is
`fea/generated/wj24-baseline-patch-mesh/attempt-01/`, launch record
`/tmp/wj24-baseline-mesh-attempt-01/`. Independent deck/archive review belongs
to `steel_mesh`. The original hardware-only Jacobian auditor rejected this
new input schema; `geometry_reconcile` is adding an explicit WJ24 wood contract
before the parent retries the audit. Preserve the rejected attempt's scope;
no Jacobians were recomputed in it. Contact engagement, objective constraint
kinematics, finite loading patches, and internal free-mode treatment remain
the representative native model's critical path. The full-layout tool helper
now uses separate role sweeps to avoid a whole-bolt bounding box falsely
dragging head width through the receiver during withdrawal. Its actual
attempt 01 completed in 305.6821 seconds in live Python session `37771`, launched by
`/tmp/run-wj24-tool-operation-20260924-attempt01.py`. Its raw report is
`/tmp/wj24-tool-operation-20260924-attempt01/geometry.json`. It includes 36
temporary frame-bolt operation proxies; `full_layout_tools` is preparing a
separate JSON classification to distinguish those temporal comparisons from
retained geometry envelopes, preserving the raw report. `transport_sequence`
is deriving removal dependencies from those results rather than assuming all
other parts must remain installed during every operation. The backer mechanics
extraction also completed against `g24` in 0.3493 seconds, with unchanged source
hashes: `/tmp/wj24-backer-mechanics-20260924-attempt01/`. It binds two interfaces,
four bolts and four fixed Hillman entry axes. `backer_loadpath` owns its archive
and readback check. The retained Python session is idle again.

Parent independently verified all seven members of the archived WJ24 STEP
bundle, all five corrected relief payloads, and all 33 viewer archive files
against their recorded sizes and hashes. The unit-case helper also passes
18 parent tests. Quiet hours still apply, and no publication or commit has
occurred during this resumed work.

## Goal and authority boundary

Continue `compact-floor-flush-wood-joints-development` toward the conditional
DIY engineering MVP in [`next-mvp-plan.md`](next-mvp-plan.md). Parent owns
planning, source decisions, integration, final validation, and Git delivery;
GPT-6 Luna workers handle bounded implementation and review tasks. The earlier
separate paused Luna session was not resumed.

Preserve selected candidate authority, baseline source pin
`df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`, all 66 panel/kicker screw axes,
and the separate-development lane. The owner authorized native mechanics for
this lane on 2026-09-24 after model/method readiness; parent serializes execution.
Physical work remains outside scope.
No task here authorizes cut, drill, fabrication, structural use, climbing, or
release. Keep every release flag false until its evidence gate passes.
Continue frequent, dependency-closed commits and pushes through parent. Keep
reported checkpoint identity separate from selected-baseline source identity.

## Completed diagnostic checkpoint

The integrated diagnostic checkpoint was committed and pushed as `be540ea9`;
`master` and its remote were clean and aligned at that checkpoint. It closes
first integrated modeling milestone only, without joint or capacity acceptance.
Preserved source reference and release flags did not change.

Follow-up master commits are `616a9f4e` (archived isolated full-stock probe),
`06e401f0` (candidate-only fixed-service-hole machining helper and tests), and
`0c9de19d` (ordinary-bolt option documentation). The archived 4×4 remains an
unaccepted separate prototype, not the active WJ-04 trial.

- WJ-03 sequence includes WJ-05 center receivers and diagnostic backers. The
  final report (`b547a604…7e0f4`) clears the 35 right-return LED endpoint hits
  recorded at earlier checkpoint `0ebf90eb`; candidate-only fixed-service-bore
  machining corrects the inherited kerf-right datum mismatch. The left return
  was already clear. Kicker motion
  with the lower panel retained still overlaps by 1–18 mm; staging the lower
  panel makes kicker extraction and return pass. No LED disconnection is
  needed or inferred. Both staged poses have zero nominal floor gap; permanent
  rear projection remains +86.018477 mm beyond the ordinary reference. The
  sequence remains diagnostic, with envelope, support, and tolerance gates
  open.
- A separate WJ-03 compact outer-bevel hypothesis (`c99751db`) and [access
  archive](hypotheses/wj03-compact-outer-access.md) (`b3a949e9`) report six
  body-removal translations, 40 shaft/head checks across 20 bolt stations,
  42 panel-screw tool/withdrawal proxies, and lower-panel-first kicker
  extraction/return clear in sampled geometry. Its [outer tool archive](hypotheses/wj03-compact-outer-tools.md)
  reports 40 coaxial socket approaches clear, four socket-plus-nut exits
  overlapping under-header links, two nut-washer slides hitting base rails,
  and no tool proxy below the analytical z = 0 plane. A broad FACOM full-turn
  envelope overlaps all 20 stacks; turning/withdrawing the bolt from the head
  side while holding the nut stationary, then removing nut and washer, is the
  next proposed screen. These diagnostics do not establish actual tool fit,
  continuous motion, physical floor clearance, or acceptance; the hypothesis
  remains separate from active layout.
- WJ-04 binds the 95.25 × 38.1 × 119.7 mm grain-N trial across probe,
  mechanics, and tool-access artifacts. Mechanics now uses the probe's finite
  contact-area method and lists the canonical rectangle separately. Historical
  angle actions remain unreplayed; no fresh demand or capacity is established.
  Its principal bolts have 19.05 mm T-edge distance versus a conditional
  25.4 mm perpendicular-grain loaded-edge 4D reference. Signed demand remains
  unresolved, so this is not a universal failure claim; the narrow trial
  cannot meet that criterion if a nonzero ±T lateral component governs.
  The refreshed tool report remains `diagnostic_overlap_present`. Its corrected
  placement centers the modeled 3.0 mm wrench slab within target head/nut axial
  thickness. In two synthetic headings, paired-wrench and upright counterhold
  bounds clear; rail counterhold and nut stroke/reindex overlap. The full-turn
  wrench-plus-axial nut-removal bound overlaps at all four stacks; separate
  loose-nut/washer translation sweeps clear at uprights but overlap at rails.
  Bolt withdrawal clears at all four; head-washer removal overlaps at rails
  but clears at uprights. These broad bounds establish
  neither actual access nor impossibility. The probe's 0.764 mm generic 50 mm
  rail-tool gap and 21.872532 mm temporary nut-exit excess are unchanged and
  remain outside tolerance acceptance. The 2×6 rip requires post-rip
  regrading.
- WJ-05 transfer and receiver reports remain diagnostic; center receiver path
  remains blocked and backer/header duties remain unaccepted.
- WJ-06 registry maps 24 duties / 144 former SDS axes, retains 66 screw axes
  and 12 frame-bolt arrangements, and accepts zero replacements. It records
  540 potential WJ-06 corridors, zero materialized/full stacks, and four
  provisional WJ-05 axes with zero complete stacks.
- Combined viewer v2 contains WJ-03/WJ-04/WJ-05 overlays;
  `integrated_clearance=not_run`, all release flags false. The WJ-04 tool
  report, WJ-05 receiver audit, duty registry, and final WJ-03 sequence are
  refreshed. The final candidate-panel scene is deployed and verified in Pages
  run `35963729016`: HTML SHA-256
  `3c6549949ca4c3a91a56e84142943f99d8a52a73faa3324f0def515db4d173ad`, scene
  SHA-256 `df7efcda2bc2b603962eb7cf87e4d1399a47f7575af4b09934eb106786a2e721`;
  both returned HTTP 200. Parent browser review passed. It has 169 solids: 110
  WJ-03, 23 WJ-04, 32 WJ-05, and four shared. All reports remain diagnostic;
  no acceptance gate is promoted.

Viewer commit `f5c40093` was publicly deployed and verified: live HTML and
scene returned HTTP 200 with exact local SHA-256 matches; the scene was
35,665,899 bytes. Independent browser review passed family toggles and camera
controls with no JavaScript exceptions.

A later UI checkpoint `86968b09` moves eight existing temporary
socket-envelope meshes behind a separate orange overlay toggle, off by default.
Four envelopes extend below floor; all 20 installed WJ-05 hardware objects
remain visible (minimum Z 0.1928 mm). Browser review passed 687 HTTP 200
responses, toggle composition, and JavaScript checks; parent checked screenshot.
This display control does not remove actual bolts or change structural geometry.
Pages run `35959025255` succeeded. Parent verified live HTML SHA-256
  `eaf2e593…b4682e6` and scene SHA-256 `f4693633…ffd57f8e`, both HTTP 200; those
  are the previous deployment hashes. Pages run `35963729016` deployed the
  updated HTML and final 169-solid candidate-panel scene; both matched the
  current local hashes and returned HTTP 200. Parent browser review passed.
  Candidate panel machining is wired into WJ-03/WJ-04/WJ-05 and the exporter,
  with the source inventory unchanged.

## Current work allocation

| Work area | Owner | Current scope and boundary |
| --- | --- | --- |
| Scope, shared decisions, integration, validation, delivery | Parent `/root` | Resolve conflicts, authorize dependent edits, own serialized commit/push and final gates. |
| WJ-04 tool refinement | `luna_wj04_tool_access` | Refreshed report is source/config bound and keeps `diagnostic_overlap_present`. Corrected placement centers the modeled 3.0 mm slab within target fastener head/nut thickness. Synthetic 15°/75° headings, 30° stroke, 60° reindex, analytic rotation enclosure, and separate nut/washer removal remain. Paired-wrench and upright counterhold bounds clear; rail counterhold and nut stroke/removal overlaps remain. The washer's same-stack shaft is excluded only during axial slide (7.7978 mm source-bounded minimum ID vs 6.35 mm modeled shaft max); unrelated obstacles remain. Exact FACOM jaw/handle shape, delivered tolerances, and working sweep remain unsupported. Manifest pins refreshed. |
| WJ-03 service alignment | `luna_outer_path` | Candidate-only `mini_moonboard/wood_joint_panel_machining.py` and tests restore fixed service-bore datums without editing `floor_flush_width.py` or changing source inventory. The final sequence clears the prior 35 right-return LED hits; no disconnection is needed or inferred. |
| WJ-03 transport narrative | `luna_transport_ops` | Current order clears return after staging the lower panel. Kicker motion with that panel retained still overlaps; sequence remains diagnostic and does not prescribe service disconnection. |
| WJ-05 center paths | `luna_center_loadpath` | Implements an isolated center-node prototype. Keep it separate from the active candidate and current receiver report; no receiver duty, load path, or capacity is accepted. |
| WJ-05 socket model and parity | `luna_socket_spec` | Owns socket exterior occupancy/datums, transfer/receiver producers, focused geometry tests, and viewer parity assertion. The receiver audit is regenerated and pinned; its bounds are rounded to 1e-5 mm without changing geometry or collision tolerance. Center receiver path remains blocked. |
| WJ-04 full-section stock | `luna_duty_registry`; material comparison by `luna_timber_stock` | Isolated probe `scripts/wood_joint_wj04_full_stock_probe.py` is in development for a staggered 88.9 × 88.9 × 119.7 mm 4×4 block with reversed rail-bolt directions and 33 mm pitch. It is a separate diagnostic prototype, not the active WJ-04 trial or an accepted stock/connection; no purchase or fabrication release. |
| WJ-03 outer envelope | `luna_review_contract` | Read-only rear-envelope and connector-geometry/stack tradeoff review; no source or report edits. |
| WJ-06 residual topologies | `luna_duty_registry` | Maps 15 generic WJ-06 duties against WJ-04 geometry, station transforms, conflicts, and next independent station. The refreshed registry remains source-bound with zero replacements accepted. |
| WJ-04 analytical helper | `luna_bolt_resistance` | Implemented/tested `mini_moonboard/wood_joint_directional_geometry.py` and focused tests (9 worker, 9 parent). `classify_member_fastener_load(...)` reports signed grain-end/cross-grain-edge components and distances; makes no demand, capacity, or pass claim. Test vector is synthetic; existing resistance basis unchanged. |
| WJ-04 directional end/edge | `luna_wood_limit_states` | Read-only exact grain/end/edge review against NDS 12.5.1 for both-sign alternatives. Keeps conditional minima distinct from the candidate directional-edge criterion. |
| Viewer UI | `luna_hardware_tools`; browser review by `luna_review_resistance` | Owns viewer HTML. Default-off temporary tool/socket overlay is live and reviewed; installed WJ-05 hardware remains displayed. Final shared-geometry labels and candidate-panel scene are deployed and browser-reviewed. |
| CI workflow and run status | `luna_checkpoint_prep` | Owns `.github/workflows/ci.yml` only. Current run records below; no worker stages, commits, or pushes. |
| Integration test and CI failure triage | `luna_integration_checks` | WJ04 config/report parity and WJ03 dependency/T-nut/reverse-order tests pass (7 and 8); now doing bounded CI failure investigation, with no producer edits. |

The owner authorized native mechanics on 2026-09-24; no fresh wood-candidate
cases have run. Freeze model and methods before execution. Keep one owner per
shared file. Parent owns report regeneration
that requires serialized CAD, integrated checks, and all Git actions.

## Next dependency order

1. Preserve the candidate-only `wood_joint_panel_machining.py` correction.
   Keep `floor_flush_width.py`, source inventory, panel outlines, holds, and
   screw policy unchanged. The current right return clears the historical LED
   endpoint hits; kicker extraction/return still requires the lower panel
   staged first. Keep the operation diagnostic pending support, tolerance, and
   permanent-envelope disposition; do not prescribe LED disconnection.
2. Complete bounded WJ-04 tool and full-section stock comparisons. Keep the
   4×4 prototype separate from the active 95.25 × 38.1 × 119.7 mm trial; do not
   treat it as selected, stock-qualified, or connected. Require source-supported
   tool geometry, useful operation sequence, and traceable stock/grade route
   before treating any candidate as buildable. Keep tool envelopes diagnostic
   until credible wrench/hand motion and tolerances exist.
3. Resolve center-path interfaces and backer/header stack limits; keep receiver
   path, floor access, bearing, resistance, and tool access separate checks.
4. Review WJ-04 signed end/edge alternatives and integrate the bounded helper
   after parent review. Keep load classification separate from fresh demand,
   resistance, and acceptance.
5. Map residual WJ-06 topologies only after station transforms and physical
   interfaces are reconciled. Keep all replacement acceptance counts at zero.
6. Confirm latest CI and live Pages results with parent/checkpoint prep. Parent
   then integrates returned findings, regenerates only affected artifacts,
   reviews manifest/source bindings, and publishes dependency-closed
   checkpoints.

No component test, nominal clearance, catalog listing, registry owner map, or
viewer interaction closes connection capacity, full-frame clearance, MVP-L,
shop package, physical observation, or release gates.

## CI and deployment status

The deployed HTML and scene passed parent HTTP/hash checks and browser review.
The final HTML hash is
`3c6549949ca4c3a91a56e84142943f99d8a52a73faa3324f0def515db4d173ad`; the scene
hash is `df7efcda2bc2b603962eb7cf87e4d1399a47f7575af4b09934eb106786a2e721`.
The current clearance artifact exactly matched a fresh run in an isolated
Python 3.12.14 / CadQuery 2.8 / OCP 7.9.3.1.1 environment (zero diff). This is
a bounded clearance check. Focused local checks passed for the candidate panel
machining, WJ-03 sequence, WJ-04 tool access and probe adapter, duty registry,
and snapshot/bounds updates. Broad CI is not established green for this
checkpoint; historical CI failures remain unresolved.

CI workflow `.github/workflows/ci.yml` runs `uv sync --locked`, Ruff, pytest,
smoke test, and current-candidate export verification. Local pre-commit and
pre-push hooks enforce only Denver quiet hours; they do not replace CI or
parent-owned validation. No feature-branch preview or branch-policy bypass is
in scope.
