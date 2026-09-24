# Wood-joints MVP orchestration handoff

Snapshot: 2026-09-23. The paused separate Luna session was not resumed; it is
idle and no longer writes shared files. Parent `/root` now owns orchestration,
source decisions, serial report generation, integration acceptance, final
validation, and all Git operations. This handoff records the current checkpoint
and outstanding shared-tree work.

## Branch and delivery state

The prior public combined viewer deployment's HTML and scene returned HTTP 200
and matched their local SHA-256 pins. The later `86968b09` UI HTML is also live,
returns HTTP 200, and matches its local hash; browser review passed toggles and
cameras with no JavaScript exceptions. That UI keeps eight existing temporary
tool/socket envelopes behind a separate orange toggle that is off by default;
all 20 installed WJ-05 hardware objects remain visible. The current local scene
refresh binds the updated receiver report and is not yet published. Parent owns
current Git state and all remaining serialized staging/commit/push. The
selected-baseline source reference remains pinned at `df7f5eca`. No
selected-candidate source bytes or release flags changed; authority-integrity
check passed for both authority files and all 725 kerf-right exports.

## Current technical state

- **WJ-03:** The integrated sequence report includes WJ-05 diagnostic backers,
  shifted posts, bolts, stacks, and four center receiver IDs. Forty-two
  screw/tool and withdrawal screens, both 250 mm lower-panel extraction
  paths, and both staged 100 mm kicker paths have no sampled unrelated hits.
  Both reverse kicker paths clear. The left lower-panel return clears; the
  right return reports fixed LED hits G1–K7 only at the 250 mm endpoint. This
  is an inherited source-pose mismatch: the kerf-right panel and its 13 mm
  service bores shift by `-KERF_EACH_MM` (1.5875 mm), while electrical parts
  remain at their earlier datums. The outward samples omit installed zero;
  the inverse return includes it. WJ-05 backers did not cause the mismatch.
  Resolve the candidate service-bore convention and re-run both paths; do not
  prescribe LED removal or disconnection. The selected baseline is unchanged.
  Both the 250 mm panel pose and 25 mm kicker pose have 0 mm nominal gap to
  base-floor wood. The permanent rear envelope remains +86.018477 mm beyond
  the ordinary reference; the 315.648756 mm bolt stroke is separate temporary
  assembly workspace. No WJ-03 sequence, layout, or capacity gate is closed.
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
  retained as an obstacle. The model proves neither actual access nor physical
  impossibility.
- **WJ-05:** The fresh transfer report remains nominal geometry only. The
  receiver audit is `blocked_center_receiver_path`; the four center duties,
  both backer/header attachments, and complete receiver-to-frame capacities
  are not accepted. The right upper socket proxy reports 2.959434 mm seated
  and 1.661248 mm full-sweep wire clearance; that is not proof of internal
  hex fit, ratchet access, service motion, tolerance, or capacity.
  The receiver JSON now uses 1e-5 mm bound rounding; its geometry and collision
  tolerance did not change. Its SHA-256 is
  `166eed185236b4ba1f260c55afb9097c655b603f7d1516412a2d4e23b405c610`. The
  refreshed scene separately binds that report; parent confirmed its solids,
  axes, and source binding match the deployed scene, with only the producer
  metadata changed. The local scene awaits publication.
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
| `/root/luna_joint_mechanics` | `scripts/wood_joint_wj04_early_mechanics.py`, its test, and generated `wj04-early-mechanics.json/.md` | Reconciled area basis now consumes active probe finite-probe values and reports canonical rectangle separately; JSON SHA-256 `a65fc65b…19eb0bd8`, Markdown `26b066cf…79b5aaa`. Ruff and seven focused tests pass. Status remains diagnostic-only and `UNRESOLVED_DEMAND`; no fresh candidate forces or capacity are claimed. |
| `/root/luna_viewer_audit` | `scripts/export_wood_joint_scene.py`, generated `site/owner-wood-joints-layout-scene.json` | Refreshed local scene v2 binds the current receiver report (SHA-256 `f469363355102cdb0e66a3cc2b6f55d9743aaa8463cfcfc3f0bc26cbffd57f8e`); it awaits parent publication. Parent confirmed solids, axes, and source binding are unchanged from the deployed scene; only producer metadata changed. `integrated_clearance=not_run`. Prior public deployment and independent browser review passed. |
| `/root/luna_hardware_tools` | Viewer `site/wood-joints-outer-viewer.html`, `site/index.html`; also completed the ordinary fastener stack method, tests, and basis doc | UI/link and stack lane published. Viewer claims remain bounded by current diagnostic scene. |
| `/root/luna_wj04_tool_access` | `scripts/wood_joint_wj04_tool_access.py`, its test, and generated `wj04-tool-access.json/.md` | Refined report is source/config bound; status remains `diagnostic_overlap_present`. Parent reports 13 focused tool-access checks and Ruff pass. JSON SHA-256 is `bb775d4157b9a92265992c960c569fde34cb655601c158ee5ae5c5238db7de49`; Markdown SHA-256 is `51a5ca2a37a2d04cd0d9bb7a379af2927ca77381b3ba273e4d0737fdd1d3c036`. |
| `/root/luna_snapshot_integrity` | `scripts/wood_joint_snapshot_integrity.py` and its tests | Audit code, 15 focused tests, Ruff, and read-only CLI pass. Active manifest scope includes WJ-04 probe, mechanics, tool-access, viewer, WJ-05 receiver audit, and duty registry; historical screens are byte-pinned only. |
| `/root/luna_duty_registry` | `scripts/wood_joint_duty_registry.py`, its test, `duty-registry.json`; `scripts/wood_joint_wj04_full_stock_probe.py` and its test | Registry SHA-256 is `251b92e806496a53c465a4f01c29de11748e0514873c52f8aa7f58d9dbd03ac7`; source binding is current. Counts remain 24/144 duties/axes, retained 66/12, zero accepted replacements, and 540 potential WJ-06 corridors with none materialized or fully stacked. The separate 88.9 × 88.9 × 119.7 mm full 4×4 prototype is in development; it is unaccepted, does not change the active WJ-04 trial, and authorizes no stock or hardware purchase or fabrication. |
| `/root/luna_checkpoint_prep` | `.github/workflows/ci.yml` | Owns the CI workflow edit; the orchestration plan now reflects the verified public viewer checkpoint. |
| `/root/luna_review_contract`, `/root/luna_review_resistance` | Read-only review lanes; no shared-file ownership | Review and browser feedback is used only within its assigned scope; parent decides whether it changes the checkpoint. |
| `/root/luna_outer_path`, `/root/luna_socket_spec`, `/root/luna_transport_ops` | WJ-03 sequence, WJ-05 diagnostic producers, and transport narrative in their assigned files | Source/report work is complete for this checkpoint. WJ-03 endpoint source mismatch remains conditional as described above; WJ-05 remains diagnostic. |

This handoff and the narrative docs (`completion-ledger.md`, `next-mvp-plan.md`,
`plan.md`, `wj04-workhorse-probe.md`, and `outer-node-result.md`) are owned by
`/root/luna_handoff`. The active WJ-04 tool-access report is not the historical
`wj04-bolt-tool-receiving-screen.json`; preserve that screen as history.

## Parent-controlled closeout sequence

1. The prior combined v2 scene deployment passed HTTP and hash checks; the
   current default-off UI is live with matching HTML bytes and passed browser
   review. The refreshed local scene binds the current receiver report but
   still awaits parent publication. The overlay changes display only.
2. The refined WJ-04 tool-access result is pinned. Keep the FACOM catalog
   nomination and conservative partial-sweep/removal screens distinct from
   proven tool motion; broad-envelope overlaps prove neither actual access nor
   physical impossibility.
3. The WJ-06 duty registry is refreshed and source-bound. Regenerate it only
   if a bound input changes; its current counts include zero accepted
   replacements.
4. Narrative, candidate-contract, and artifact manifest describe/pin WJ-03
   through WJ-06 as current diagnostics without gate promotion. Manifest pins
   active probe/mechanics/tool-access/viewer outputs, the WJ-05 receiver audit
   and duty registry, historical receiving/spacer/narrow 3.5-in/rejected-wide
   JSONs, and refreshed final docs. Snapshot owner reports
   `snapshot_state=consistent`, including manifest bytes, producer/input
   fingerprints, WJ-04 dimensions, active identity, viewer, and tool-access
   checks. No changed or missing dependency remains. Snapshot tests (13), Ruff,
   and parent audit/manifest tests (14) pass.
5. No native solves are authorized or run; another solve requires new user
   authorization. No complete joint capacities or release gates are
   established.

No worker should stage, commit, or push; parent owns the final serialized Git
actions.
