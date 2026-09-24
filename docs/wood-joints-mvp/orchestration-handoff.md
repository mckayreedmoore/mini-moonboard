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
full-stock probe is not the active WJ-04 trial. The published HTML and scene
returned HTTP 200 and matched their local hashes; Pages run `35959025255`
succeeded. The default-off tool/socket overlay remains live, with all 20
installed WJ-05 hardware objects visible. A candidate panel overlay is wired
into the local exporter. Its final 169-solid scene export
(`df7efcda…a2e721`) has 110 WJ-03, 23 WJ-04, and 32 WJ-05 solids plus four
shared solids; it awaits parent review and publication. The live site still
serves the previously verified scene (`f4693633…ffd57f8e`). Parent owns
report/export review and all Git actions. The selected-baseline source
reference remains pinned at `df7f5eca`; source inventory and release flags are
unchanged.

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
  local cleat body has
  0.0 mm ordinary-N excess; modeled stacks/seats clear, but the generic 50 mm
  rail tool gap is 0.764 mm and temporary nut exit exceeds the ordinary limit
  by 21.872532 mm. Early mechanics is config-bound but uses six unreplayed
  historical angle-demand cases; each has four mismatched source files, so
  fresh candidate demand and capacity remain unresolved. The principal bolts
  have 19.05 mm T-edge distance versus a conditional 25.4 mm perpendicular-
  grain loaded-edge 4D reference. Signed demands remain unresolved; this is
  not a universal failure claim, but the narrow trial cannot satisfy that
  criterion if a nonzero ±T lateral component governs. Mechanics now uses
  the probe's finite-probe area basis and reports the canonical bounds area
  separately as a coordinate audit. The refined tool report remains
  `diagnostic_overlap_present`: it screens two synthetic heading samples with
  a 30° working stroke, detached 60° reindex, and conservative continuous
  rotation enclosures, plus a 22 mm open-end exit proxy. It also screens
  full-turn nut advancement, nut/washer translation, bolt withdrawal, and
  later head-washer removal. For wrench contact, only the active fastener head
  or nut and its own shaft are excluded; washers remain obstacles. The nut
  washer's same-stack shaft is excluded only during nominal axial sliding,
  based on source-bounded washer ID exceeding modeled shaft diameter; thread
  major diameter and delivered-part fit remain unverified. Full bolt
  withdrawal assumes all same-stack hardware is removed first, with host wood
  retained as an obstacle. The refreshed broad tool envelope overlaps the
  lower panel; that remains a conservative diagnostic, not a physical access
  finding. The model proves neither actual access nor physical impossibility.
- **WJ-05:** The fresh transfer report remains nominal geometry only. The
  receiver audit is `blocked_center_receiver_path`; the four center duties,
  both backer/header attachments, and complete receiver-to-frame capacities
  are not accepted. The right upper socket proxy reports 2.959434 mm seated
  and 1.661248 mm full-sweep wire clearance; that is not proof of internal
  hex fit, ratchet access, service motion, tolerance, or capacity.
  The receiver JSON now uses 1e-5 mm bound rounding; its serialized bounds
  changed, but geometry and collision tolerance did not. The artifact manifest
  pins the current report. The local scene export binds it and includes the
  candidate panel overlay; this refreshed scene is not yet claimed as deployed.
- **WJ-06:** The current source-bound duty registry maps 24 former angle duties / 144 SDS axes,
  retains all 66 panel/kicker axes and twelve frame-bolt obligations, and
  accepts zero replacements. It records 540 potential corridors with none
  materialized or fully stacked, and four provisional WJ-05 axes with no
  complete stacks. Regenerate only if a bound input changes.

All current outputs remain diagnostics. Do not infer a complete replacement,
accepted resistance, MVP-L, six-case readiness, shop release, or physical
acceptance from nominal clearance or component tests.

`wood-joints-candidate.json` now identifies the lane as partial diagnostic
development, links the current WJ-03 through WJ-06 evidence, and retains all
source pins, fixed-scope invariants, and false release flags. Its document
references resolve to existing files.

## Active ownership and dependency order

| Owner | Owned files / boundary | Current state and next dependency |
|---|---|---|
| `/root` | Shared configuration decisions, serialization, report regeneration, integrated acceptance, validation, Git delivery | Owns the serial slots and all staging/commit/push. |
| `/root/luna_center_loadpath` | Stable WJ-04 probe adapter/report; isolated WJ-05 center-node prototype | WJ-04 config-bound report remains current for `narrow_x95p25_ordinary_bolt_candidate`, config SHA `d1c63e1f…206c0e`; source binding matches and release flags are false. Current implementation work is a separate center-node prototype; it does not change the four blocked receiver duties or accept their load paths. |
| `/root/luna_joint_mechanics` | `scripts/wood_joint_wj04_early_mechanics.py`, its test, and generated `wj04-early-mechanics.json/.md` | Reconciled area basis consumes active probe finite-probe values and reports the canonical rectangle separately. Ruff and seven focused tests pass. Status remains diagnostic-only and `UNRESOLVED_DEMAND`; no fresh candidate forces or capacity are claimed. Current artifact hashes are pinned in the manifest. |
| `/root/luna_viewer_audit` | `scripts/export_wood_joint_scene.py`, generated `site/owner-wood-joints-layout-scene.json` | Final local candidate-panel scene export has 169 solids (110 WJ-03, 23 WJ-04, 32 WJ-05, four shared) and `integrated_clearance=not_run`. The deployed scene is the previously verified one recorded above; the refreshed scene awaits parent review. |
| `/root/luna_hardware_tools` | Viewer `site/wood-joints-outer-viewer.html`, `site/index.html`; also completed the ordinary fastener stack method, tests, and basis doc | Default-off tool/socket overlay and UI are live; the final local HTML includes reviewed “Shared geometry” labels. Viewer claims remain bounded by the diagnostic scene. |
| `/root/luna_wj04_tool_access` | `scripts/wood_joint_wj04_tool_access.py`, its test, and generated `wj04-tool-access.json/.md` | Refined report is source/config bound; status remains `diagnostic_overlap_present`. Parent reports 13 focused tool-access checks and Ruff pass. Current artifact hashes are pinned in the manifest. |
| `/root/luna_snapshot_integrity` | `scripts/wood_joint_snapshot_integrity.py` and its tests | Audit code, 15 focused tests, Ruff, and read-only CLI pass. Active manifest scope includes WJ-04 probe, mechanics, tool-access, viewer, WJ-05 receiver audit, and duty registry; historical screens are byte-pinned only. |
| `/root/luna_duty_registry` | `scripts/wood_joint_duty_registry.py`, its test, `duty-registry.json`; `scripts/wood_joint_wj04_full_stock_probe.py` and its test | Registry source binding is current. Counts remain 24/144 duties/axes, retained 66/12, zero accepted replacements, and 540 potential WJ-06 corridors with none materialized or fully stacked. The separate 88.9 × 88.9 × 119.7 mm full 4×4 prototype is in development; it is unaccepted, does not change the active WJ-04 trial, and authorizes no stock or hardware purchase or fabrication. Current artifact hashes are pinned in the manifest. |
| `/root/luna_checkpoint_prep` | `.github/workflows/ci.yml` | Owns the CI workflow edit; the orchestration plan now reflects the verified public viewer checkpoint. |
| `/root/luna_review_contract`, `/root/luna_review_resistance` | Read-only review lanes; no shared-file ownership | Review and browser feedback is used only within its assigned scope; parent decides whether it changes the checkpoint. |
| `/root/luna_outer_path`, `/root/luna_socket_spec`, `/root/luna_transport_ops` | WJ-03 sequence, WJ-05 diagnostic producers, and transport narrative in their assigned files | The fixed service-bore correction clears all 35 terminal right-return LED overlaps. Kicker removal passes after the lower panel is staged; WJ-05 remains diagnostic. |

This handoff and the narrative docs (`completion-ledger.md`, `next-mvp-plan.md`,
`plan.md`, `wj04-workhorse-probe.md`, and `outer-node-result.md`) are owned by
`/root/luna_handoff`. The active WJ-04 tool-access report is not the historical
`wj04-bolt-tool-receiving-screen.json`; preserve that screen as history.

## Parent-controlled closeout sequence

1. The deployed scene and default-off UI passed live HTTP/hash and browser
   checks. The final candidate-panel scene export is local
   (`df7efcda…a2e721`); parent will review it before any publication claim.
2. The refined WJ-04 tool-access result is pinned. Keep the FACOM catalog
   nomination and conservative partial-sweep/removal screens distinct from
   proven tool motion; broad-envelope overlaps prove neither actual access nor
   physical impossibility.
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
