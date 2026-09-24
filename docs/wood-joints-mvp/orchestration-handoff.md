# Wood-joints MVP orchestration handoff

Snapshot: 2026-09-24. The paused separate Luna session was not resumed; it is
idle and no longer writes shared files. Parent `/root` now owns orchestration,
source decisions, serial report generation, integration acceptance, final
validation, and all Git operations. This handoff records the current checkpoint
and outstanding shared-tree work.

## Branch and delivery state

Since `0ebf90eb`, master received `616a9f4e` (archive one isolated full-stock
probe), `06e401f0` (candidate-only fixed-service-hole machining helper and
tests), and `0c9de19d` (ordinary-bolt option documentation). The archived
full-stock probe is not the active WJ-04 trial. The prior deployment in Pages
run `35959025255` returned HTTP 200 for the HTML and scene, matching their
then-current local hashes. The default-off tool/socket overlay remains live,
with all 20 installed WJ-05 hardware objects visible. The final candidate-panel
scene is deployed in Pages run `35963729016`: HTML SHA-256
`3c6549949ca4c3a91a56e84142943f99d8a52a73faa3324f0def515db4d173ad` and scene
SHA-256 `df7efcda2bc2b603962eb7cf87e4d1399a47f7575af4b09934eb106786a2e721`,
both HTTP 200. Parent browser review passed. This 169-solid scene has 110
WJ-03, 23 WJ-04, 32 WJ-05, and four shared solids; the previously deployed
scene hash `f4693633…ffd57f8e` is historical. Parent owns report/export review
and all Git actions. The selected-baseline source reference remains pinned at
`df7f5eca`; source inventory and release flags are unchanged.

## Latest checkpoint and next actions, 2026-09-24

The active WJ-04 configuration remains
`narrow_x95p25_ordinary_bolt_candidate`; deployed viewer remains at `40b97ecf`;
the active registry remains at 5/24 geometry and zero accepted replacements.
New work below stays isolated diagnostic work and does not change those
boundaries.

- The [part-count review](hypotheses/part-count-and-merge-review.md) projects
  28 connector pieces and 104 candidate bolt positions against the original
  10–14-piece aim. No simple documented merge reaches that aim under current
  constraints. Parent is deciding whether to proceed with or revise
  replication of the remaining twelve duties; this is a planning choice, not a
  new acceptance gate.
- WJ-03 head-withdrawal screen is archived. Its 20 coarse shaft-box hits are
  limited to each shaft's own receiver bores and washer rings. The [exact
  coaxial supplement](hypotheses/wj03-head-withdrawal-exact-shaft.md) clears
  all 20 nominal shafts against fixed geometry and four separately sampled
  counterhold headings; the 80 coarse self-bore/washer pairs disappear, with
  no exact-only hits. Bounded operation-route summary remains pending; this
  does not establish physical tool fit.
- WJ-05 ±190 mm center-post rerun is archived as
  [`nominal_geometry_clear_diagnostic`](hypotheses/wj05-center-post-x190/README.md).
  Body, bore, hardware, receiver, washer-seat, contact-face, wire, and preferred
  modeled-route geometry checks pass. Rejected stroke sectors still have
  diagnostic hits; physical access and mechanics remain open.
- Right four-duty shared-host source machining and ordinary-body sensitivity
  received static review. Sensitivity uses 6.604 mm occupied diameter only for
  four WJ-06 side-bolt shafts; nominal steel remains 6.35 mm. First
  materialization built family geometry for 66.77 s, then stopped assembling
  the combined report at missing `wj04_base._source_inventory`; second failed
  source reconstruction at `base_principal_center_right` by 1,260.109751 mm³.
  Eight extra candidate purchased-length cuts explain the principal delta.
  Each rail's three outer-duty SDS axes shift −3.175 mm through
  `WidthAdapter.connections`, while finished-rail trim retains the original
  holes. Official native cuts reconstruct 0/0; the per-host translated side
  requires shifted cuts. Owner is splitting per-host native cuts from
  candidate purchase cuts. No combined report or geometry verdict exists; no
  tolerance is waived.

Next sequence: finish the right per-host/candidate cut split and rerun;
summarize WJ-03 removal operations from the exact shaft result; then compose
the existing twelve-duty hypotheses into one coherent diagnostic model before
any viewer refresh. Mechanical review found no categorical topology
incompatibility. After geometry integration, run bounded, capacity-independent
net-section checks for bevels, G7 crosscut, center relief, and backer
counterbores; keep backer-to-header resistance unresolved pending an applicable
method; and triage signed wrench closure, contact, and bolt demand using
historical actions as diagnostics. Use results to inform broader replication,
not as a new gate. No native solve is authorized.

## Current technical state

- **WJ-03:** The final sampled sequence report (`b547a604…7e0f4`) includes
  WJ-05 diagnostic backers, shifted posts, bolts, stacks, and four center
  receiver IDs. The pre-helper report at checkpoint `0ebf90eb` recorded 35
  right-return LED hits; candidate-only machining from `06e401f0` restores
  fixed service-bore datums, and the final right return clears them. The left
  return was already clear. With the lower panel retained, the kicker path
  still overlaps by 1–18 mm; staging/removing the lower panel lets kicker
  extraction and return pass. No LED disconnection is needed or inferred.
  Other paths and tools are unchanged. Both staged poses remain at 0 mm nominal
  base-floor gap; permanent rear projection is +86.018477 mm past the ordinary
  reference and the 315.648756 mm bolt stroke remains temporary workspace.
  Sequence, support, tolerance, envelope, and capacity gates remain open.
- **WJ-04:** The canonical diagnostic trial is
  `narrow_x95p25_ordinary_bolt_candidate`: a 95.25 × 38.1 × 119.7 mm cleat,
  grain N, with K.L. Jack 3.75-in rail and 6-in principal bolt candidates,
  `25CNFH5Z` nuts, and two Type A Wide washers per stack. The 2×6 stock route
  requires regrading after the rip; species group, final grade, treatment,
  local availability, delivered bolt transitions, nut engagement, and real
  tool motion remain unverified. The 88.9 × 88.9 × 119.7 mm full 4×4 is a
  separate isolated prototype under development, not the active WJ-04 trial
  and not an accepted stock or connection. The current probe binds
  that trial to config hash `d1c63e1f…206c0e`, with release flags false. Its
  local cleat body has 0.0 mm ordinary-N excess; modeled stacks/seats clear.
  The generic 50 mm rail-tool gap remains 0.764 mm and temporary nut exit
  remains 21.872532 mm beyond the ordinary limit; both are probe values, not
  tolerance passes. Early mechanics is config-bound but uses six unreplayed
  historical angle-demand cases; each has four mismatched source files, so
  fresh candidate demand and capacity remain unresolved. The principal bolts
  have 19.05 mm T-edge distance versus a conditional 25.4 mm perpendicular-
  grain loaded-edge 4D reference. Signed demands remain unresolved; this is
  not a universal failure claim, but the narrow trial cannot satisfy that
  criterion if a nonzero ±T lateral component governs. Mechanics now uses the
  probe's finite-probe area basis and reports the canonical bounds area
  separately as a coordinate audit. The regenerated tool report remains
  `diagnostic_overlap_present`. Its corrected placement centers the modeled
  3.0 mm wrench slab within target head/nut axial thickness. In two synthetic
  headings, head counterhold clears at both principal upright stacks and
  overlaps at both rails; paired-wrench bounds clear at all four. Nut
  stroke/reindex and the full-turn wrench-plus-axial nut-removal bound overlap
  at all four. Separate loose-nut and nut-washer translation sweeps clear at
  upright stacks but overlap at rails. Bolt withdrawal clears at all four;
  head-washer removal overlaps at rail stacks and clears at upright stacks.
  The report retains 30° working strokes,
  detached 60° reindex, conservative continuous-rotation enclosures, a 22 mm
  open-end exit proxy, full-turn nut advancement, and nut/washer translation.
  For wrench contact, only the active fastener head or nut and its own shaft
  are excluded; washers remain obstacles. The nut washer's same-stack shaft is
  excluded only during nominal axial sliding, based on source-bounded washer ID
  exceeding modeled shaft diameter; thread major diameter and delivered-part
  fit remain unverified. Full bolt withdrawal assumes all same-stack hardware
  is removed first, with host wood retained as an obstacle. These broad
  envelopes establish neither actual access nor physical impossibility.
- **WJ-05:** The fresh transfer report remains nominal geometry only. The
  receiver audit is `blocked_center_receiver_path`; the four center duties,
  both backer/header attachments, and complete receiver-to-frame capacities
  are not accepted. The right upper socket proxy reports 2.959434 mm seated
  and 1.661248 mm full-sweep wire clearance; that is not proof of internal
  hex fit, ratchet access, service motion, tolerance, or capacity.
  The receiver JSON now uses 1e-5 mm bound rounding; its serialized bounds
  changed, but geometry and collision tolerance did not. The artifact manifest
  pins the current report. The deployed scene binds it and includes the
  candidate panel overlay. Separate ±190 mm center-post geometry is archived
  as `nominal_geometry_clear_diagnostic`; body, bore, installed hardware,
  receiver, washer-seat, contact-face, wire, and preferred modeled-route checks
  pass. Rejected stroke sectors remain diagnostic hits; access and mechanics
  remain open.
- **WJ-06:** The active duty registry still maps 24 duties / 144 former SDS
  axes, retains 66 panel/kicker axes and twelve frame-bolt obligations, records
  geometry for 5/24 duties, and accepts zero replacements. Its residual-probe
  entry still lists 540 potential generic corridors with none materialized in
  that registry; its `replacement_complete_stack_evidence_count` remains zero.
  Separate report `b69ca5fa` now materializes static installed geometry for two
  far-end right rail pairs with eight provisional stacks; it does not change
  registry counts or acceptance. Right four-duty integration has no combined
  report yet: its first run failed while assembling the report on a missing
  loader helper; its second failed source reconstruction at
  `base_principal_center_right` by 1,260.109751 mm³. Eight extra candidate
  purchased-length cuts explain the principal delta. Each rail's three
  outer-duty SDS axes shift −3.175 mm through `WidthAdapter.connections`, but
  finished-rail trim retains original holes; native cuts reconstruct 0/0,
  while the per-host translated side requires shifted cuts. Owner is splitting
  per-host native cuts from candidate purchase cuts. Neither attempt provides
  a geometry verdict. Four provisional WJ-05 axes remain unaccepted.
  Regenerate registry only if a bound input changes.

All current outputs remain diagnostics. Do not infer a complete replacement,
accepted resistance, MVP-L, six-case readiness, shop release, or physical
acceptance from nominal clearance or component tests.

## Isolated installed-fit hypotheses

These local screens do not change the canonical narrow WJ-04 trial, source
authority, or deployed viewer. None is integrated or accepted.

- [WJ-03 compact outer bevel](hypotheses/wj03-compact-outer-probe.md),
  `c99751db`: N = 137.7 mm leaves 2 mm nominal rear-envelope reserve; installed
  stacks, timber, and protected geometry screens clear. Its separate
  [compact access archive](hypotheses/wj03-compact-outer-access.md),
  `b3a949e9`, reports six body-removal translations and 40 shaft/head checks
  across 20 bolt stations clear, 42 panel-screw tool/withdrawal proxies clear,
  and lower-panel-first
  kicker extraction/return clear in sampled geometry. The [outer tool
  archive](hypotheses/wj03-compact-outer-tools.md) reports 40 coaxial socket
  approaches clear, four socket-plus-nut exits that overlap under-header
  links, two nut-washer slides that hit base rails, and no tool proxy below
  the analytical z = 0 plane. Its broad FACOM full-turn envelope overlaps all
  20 stacks; it proposes turning/withdrawing the bolt from the head side while
  holding the nut stationary, then removing the nut and washer. These screens
  establish neither actual tool fit, continuous motion, physical floor
  clearance, nor acceptance; the hypothesis remains isolated. Its separate
  [exact coaxial-shaft supplement](hypotheses/wj03-head-withdrawal-exact-shaft.md)
  clears 20/20 nominal shafts against fixed geometry and four separately
  sampled counterhold headings. The 80 broad self-bore/washer pairs disappear;
  no exact-only hits remain. This nominal envelope does not establish actual
  tool fit or complete operation order; bounded route summary is pending.
- [WJ-04 upper G7 crosscut](hypotheses/wj04-upper-g7-crosscut.md),
  `5555c646`: the upper cleat is crosscut and its upper-rail bolt stack
  reversed. Bodies, stacks, and 16 washer seats clear, but all four rail-bolt
  insertion paths are blocked with neighbors retained. Duty-registry work is
  planning rail-plus-cleat subassemblies outside the frame.
- [WJ-04 local +N access](hypotheses/wj04-pair-access-local-n.md): refined
  lower/upper right rail-cleat screens find eight distinct obstacle pairs per
  move with sampled exact intersections: three retained far-end outer-duty SDS
  beams and five service wires. This remains discrete, unaccepted evidence;
  neither continuous blockage nor a physical route is established.
- [WJ-05 center wire-relief](hypotheses/wj05-center-node-relieved.md): the
  L = 82 mm body geometry clears; right wire gap is 2.303793 mm and the left
  result is a 9.25 mm bounding-box lower bound. It keeps 48 + 18 fixed axes,
  with installed fastener components clear. Two properly seated generic
  head-tool proxies overlap center posts at upper-header row 2 (left and
  right), 1,481.459916 mm³ each. The [catalog-sized tool comparison](hypotheses/wj05-center-tools/README.md)
  now records socket/extension hits on same-side lower-post bolt heads,
  counterhold overlap with row-1 nut/shaft/timber, and ratchet-stroke overlaps
  with backers or washer/timber. These external proxies prove neither actual
  fit nor impossibility. The separate ±190 mm post/lower-cleat/axis variant is
  archived below.
- [WJ-05 ±190 mm center-post variant](hypotheses/wj05-center-post-x190/README.md):
  corrected trial moves posts, lower cleats, and eight lower axes outward
  10 mm. Body/bore, installed-hardware, receiver, washer-seat, contact-face,
  wire, and selected modeled-route checks pass. Rejected stroke sectors remain
  diagnostic hits. No physical tool access or strength is established.
- [WJ-06 right outer paired rails](hypotheses/wj06-outer-pair.md), `b69ca5fa`:
  static installed geometry is materialized for two far-end right rail pairs,
  with eight provisional stacks and 16 supported washer seats. Whether +N
  insertion needs side release remains untested. Next screen tests the rail
  and two cleats moving +N with principal/side members retained and X bolts
  absent. Assembly sequence, wrench access, and capacity remain untested.
  Right four-duty integration still lacks a combined report after loader and
  source-reconstruction failures. Eight extra candidate cuts explain the
  principal delta; owner is separating native per-host cuts from candidate
  purchase cuts to resolve rail-axis offsets. No replacement is accepted.

Next work stays operation-specific: reconcile right shared-host source cuts,
summarize the exact WJ-03 withdrawal route, then integrate the twelve existing
duty hypotheses before any viewer refresh. After geometry integration, run
bounded net-section and signed wrench/contact/bolt-demand triage; historical
actions remain diagnostic and no native solve is authorized. Parent reviews
source-bound results before integration. The deployed viewer remains at
`40b97ecf`; these hypotheses do not change viewer or active-registry scope.

`wood-joints-candidate.json` now identifies the lane as partial diagnostic
development, links the current WJ-03 through WJ-06 evidence, and retains all
source pins, fixed-scope invariants, and false release flags. Its document
references resolve to existing files.

## Ownership and verified work

Current patch ownership supersedes the historical boundaries below: right-rail integration belongs to `luna_viewer_audit`; the 12-duty compositor belongs to `luna_wj04_tool_access`; the outer route parser belongs to `luna_hardware_tools`; and the exporter, viewer HTML, and generated scene belong to `luna_integration_checks` once the compositor interface freezes. `luna_snapshot_integrity` is reviewing the compositor. Parent remains the only Git writer and serializes heavy CAD runs.

| Owner | Owned files / boundary | Current state and next dependency |
|---|---|---|
| `/root` | Shared configuration decisions, serialization, report regeneration, integrated acceptance, validation, Git delivery | Owns the serial slots and all staging/commit/push. |
| `/root/luna_center_loadpath` | Stable WJ-04 probe adapter/report; isolated WJ-05 center-node prototype | WJ-04 config-bound report remains current for `narrow_x95p25_ordinary_bolt_candidate`, config SHA `d1c63e1f…206c0e`; source binding matches and release flags are false. The center tool comparison and corrected ±190 mm post variant are archived. Variant passes nominal body/bore/washer/contact/wire/preferred-route checks, but changes neither the four blocked receiver duties nor their unaccepted load paths. |
| `/root/luna_joint_mechanics` | `scripts/wood_joint_wj04_early_mechanics.py`, its test, and generated `wj04-early-mechanics.json/.md` | Reconciled area basis consumes active probe finite-probe values and reports the canonical rectangle separately. Ruff and seven focused tests pass. Status remains diagnostic-only and `UNRESOLVED_DEMAND`; no fresh candidate forces or capacity are claimed. Current artifact hashes are pinned in the manifest. |
| `/root/luna_viewer_audit` | `scripts/wood_joint_right_rail_integration.py`, `scripts/export_wood_joint_scene.py`, generated scene | Shared-host machining and 6.604 mm WJ-06 side-shaft occupancy sensitivity received static review; nominal steel remains 6.35 mm. First materialization reached family geometry but failed report assembly on a missing loader helper; second failed source reconstruction at `base_principal_center_right` by 1,260.109751 mm³. Eight extra candidate cuts explain principal delta. Six rail SDS axes shift −3.175 mm through `WidthAdapter.connections`, but rail trim retains original holes; owner is implementing separate native per-host cuts and candidate purchase cuts. No combined report or geometry verdict exists. Viewer remains at `40b97ecf`, with browser-reviewed 169-solid scene and `integrated_clearance=not_run`. |
| `/root/luna_hardware_tools` | Viewer `site/wood-joints-outer-viewer.html`, `site/index.html`; also completed the ordinary fastener stack method, tests, and basis doc | Default-off tool/socket overlay and UI are live; the reviewed “Shared geometry” labels are deployed. Viewer claims remain bounded by the diagnostic scene. |
| `/root/luna_wj04_tool_access` | `scripts/wood_joint_wj04_tool_access.py`, its test, and generated `wj04-tool-access.json/.md` | Refreshed source/config-bound report remains `diagnostic_overlap_present`; modeled 3.0 mm wrench slab is centered within target head/nut axial thickness. Paired-wrench and upright counterhold bounds clear; rail counterhold, nut stroke/reindex, and full-turn wrench-plus-axial removal bounds overlap. Separate loose-nut/washer translation clears at uprights and overlaps at rails. Actual jaw/handle access is unproved. Current artifact hashes are pinned in the manifest. |
| `/root/luna_snapshot_integrity` | `scripts/wood_joint_snapshot_integrity.py` and its tests | Audit code, 15 focused tests, Ruff, and read-only CLI pass. Active manifest scope includes WJ-04 probe, mechanics, tool-access, viewer, WJ-05 receiver audit, and duty registry; historical screens are byte-pinned only. |
| `/root/luna_duty_registry` | `scripts/wood_joint_duty_registry.py`, its test, `duty-registry.json`; `scripts/wood_joint_wj04_full_stock_probe.py` and its test | Registry source binding is current: 24/144 duties/axes, retained 66/12, active trial geometry 5/24, and zero accepted replacements. Its residual-probe entry still has 540 potential generic corridors and none materialized in that registry; `replacement_complete_stack_evidence_count` remains zero. Separate WJ-06 pair geometry is archived; the failed shared-host materializations do not update registry counts or acceptance. No stock or hardware is selected. |
| `/root/luna_checkpoint_prep` | `next-mvp-plan.md`, `orchestration-handoff.md` | Owns this bounded checkpoint status refresh; parent retains final validation and Git actions. |
| `/root/luna_review_contract`, `/root/luna_review_resistance` | Read-only review lanes; no shared-file ownership | Review and browser feedback is used only within its assigned scope; parent decides whether it changes the checkpoint. |
| `/root/luna_outer_path`, `/root/luna_socket_spec`, `/root/luna_transport_ops` | WJ-03 sequence, WJ-05 diagnostic producers, and transport narrative in their assigned files | The fixed service-bore correction clears all 35 terminal right-return LED overlaps. Kicker removal passes after the lower panel is staged. WJ-03 exact coaxial supplement clears 20/20 shafts against fixed geometry and four separately sampled counterhold headings; bounded route summary remains pending. WJ-05 remains diagnostic. |

The handoff and narrative docs are ordinarily owned by `/root/luna_handoff`;
this bounded refresh of `next-mvp-plan.md` and `orchestration-handoff.md` is
owned by `/root/luna_checkpoint_prep`. The active WJ-04 tool-access report is
not the historical `wj04-bolt-tool-receiving-screen.json`; preserve that
screen as history.

## Parent-controlled closeout sequence

1. The final 169-solid candidate-panel scene is deployed and verified in Pages
   run `35963729016`; HTML and scene both returned HTTP 200 and matched their
   pinned hashes. Parent browser review passed.
2. The refreshed WJ-04 tool-access result is pinned. Its corrected slab
   placement refines the head/nut contact envelope; keep FACOM catalog
   nomination and synthetic partial-sweep/removal bounds distinct from actual
   tool motion. Clear bounds and overlaps prove neither access nor
   impossibility.
3. The WJ-06 duty registry is refreshed and source-bound. Regenerate it only
   if a bound input changes; its current counts include zero accepted
   replacements.
4. Narrative, candidate-contract, and artifact manifest describe/pin WJ-03
   through WJ-06 as current diagnostics without gate promotion. Refresh the
   changed sequence, scene, tool-access, receiver, registry, and narrative
   hashes, then run the final snapshot audit. Historical receiving/spacer/narrow
   3.5-in/rejected-wide JSON pins remain byte checks only.
5. No native solves are authorized or run; another solve requires new user
   authorization. No complete joint capacities or release gates are
   established.

No worker should stage, commit, or push; parent owns the final serialized Git
actions.
