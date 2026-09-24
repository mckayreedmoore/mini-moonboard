# Wood-joints MVP orchestration handoff

Snapshot: 2026-09-23. The paused separate Luna session was not resumed; it is
idle and no longer writes shared files. Parent `/root` now owns orchestration,
source decisions, serial report generation, integration acceptance, final
validation, and all Git operations. This handoff records the current checkpoint
and outstanding shared-tree work.

## Branch and delivery state

The public combined viewer deployment succeeded. Its live HTML and scene both
returned HTTP 200; the 35,665,899-byte scene and viewer HTML matched their local
SHA-256 pins. Independent browser review passed family toggles and camera
controls with no JavaScript exceptions. Parent owns current Git state and all
remaining serialized staging/commit/push. The selected-baseline source
reference remains pinned at `df7f5eca`. No selected-candidate source bytes or
release flags changed; authority-integrity check passed for both authority
files and all 725 kerf-right exports.

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
  tool motion remain unverified. The current probe binds that trial to config
  hash `d1c63e1f…206c0e`, with release flags false. Its local cleat body has
  0.0 mm ordinary-N excess; modeled stacks/seats clear, but the generic 50 mm
  rail tool gap is 0.764 mm and temporary nut exit exceeds the ordinary limit
  by 21.872532 mm. Early mechanics is config-bound but uses six unreplayed
  historical angle-demand cases; each has four mismatched source files, so
  fresh candidate demand and capacity remain unresolved. Mechanics now uses
  the probe's finite-probe area basis and reports the canonical bounds area
  separately as a coordinate audit. The tool-access
  report is current, with broad-envelope overlaps; it proves neither physical
  access nor impossibility.
- **WJ-05:** The fresh transfer report remains nominal geometry only. The
  receiver audit is `blocked_center_receiver_path`; the four center duties,
  both backer/header attachments, and complete receiver-to-frame capacities
  are not accepted. The right upper socket proxy reports 2.959434 mm seated
  and 1.661248 mm full-sweep wire clearance; that is not proof of internal
  hex fit, ratchet access, service motion, tolerance, or capacity.
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
| `/root/luna_center_loadpath` | `scripts/wood_joint_wj04_probe.py`, `tests/test_wood_joint_wj04_probe_adapter.py`; preserves old probe bytes at `wj04-narrow-3p5in-historical.json` | Adapter and four focused tests plus Ruff/compile pass. Config-bound report is current for `narrow_x95p25_ordinary_bolt_candidate`, config SHA `d1c63e1f…206c0e`; producer SHA `ed3c3b18…b612840`; source binding matches and release flags are false. |
| `/root/luna_joint_mechanics` | `scripts/wood_joint_wj04_early_mechanics.py`, its test, and generated `wj04-early-mechanics.json/.md` | Reconciled area basis now consumes active probe finite-probe values and reports canonical rectangle separately; JSON SHA-256 `a65fc65b…19eb0bd8`, Markdown `26b066cf…79b5aaa`. Ruff and seven focused tests pass. Status remains diagnostic-only and `UNRESOLVED_DEMAND`; no fresh candidate forces or capacity are claimed. |
| `/root/luna_viewer_audit` | `scripts/export_wood_joint_scene.py`, generated `site/owner-wood-joints-layout-scene.json` | Scene v2 with WJ-03/WJ-04/WJ-05 overlays and stale-report gates is published in `f5c40093`; `integrated_clearance=not_run`. Independent browser review passed and parent verified the deployed bytes. |
| `/root/luna_hardware_tools` | Viewer `site/wood-joints-outer-viewer.html`, `site/index.html`; also completed the ordinary fastener stack method, tests, and basis doc | UI/link and stack lane published. Viewer claims remain bounded by current diagnostic scene. |
| `/root/luna_wj04_tool_access` | `scripts/wood_joint_wj04_tool_access.py`, its test, and generated `wj04-tool-access.json/.md` | Report is generated and source/config bound; status is `diagnostic_overlap_present`. Nine focused tests and Ruff pass. Conservative envelopes overlap modeled solids; no physical access or impossibility conclusion is established. JSON SHA-256 is `04b175c8…a3eff1f`. |
| `/root/luna_snapshot_integrity` | `scripts/wood_joint_snapshot_integrity.py` and its tests | Audit code and 13 focused tests plus Ruff/read-only CLI pass. Active manifest scope includes WJ-04 probe, mechanics, tool-access, and viewer JSON; historical screens are byte-pinned only. |
| `/root/luna_duty_registry` | `scripts/wood_joint_duty_registry.py`, its test, `duty-registry.json`; WJ-06 producer source edit | Registry refreshed from stable inputs; SHA-256 `0baa4261…fb31ec9a`. Source binding is current, counts remain 24/144 duties/axes, retained 66/12, and zero accepted replacements. WJ-06 report JSON is absent; 540 corridors remain potential, with zero materialized or full stacks. Regenerate only if a bound input changes. |
| `/root/luna_checkpoint_prep` | `docs/wood-joints-mvp/orchestration-plan.md` | Owns the plan exclusively and is updating its delivery path for the pushed master checkpoint. |
| `/root/luna_review_contract`, `/root/luna_review_resistance` | Read-only review lanes; no shared-file ownership | Review feedback is still pending; parent decides whether it changes the checkpoint. |
| `/root/luna_outer_path`, `/root/luna_socket_spec`, `/root/luna_transport_ops` | WJ-03 sequence, WJ-05 diagnostic producers, and transport narrative in their assigned files | Source/report work is complete for this checkpoint. WJ-03 endpoint source mismatch remains conditional as described above; WJ-05 remains diagnostic. |

This handoff and the narrative docs (`completion-ledger.md`, `next-mvp-plan.md`,
`plan.md`, `wj04-workhorse-probe.md`, and `outer-node-result.md`) are owned by
`/root/luna_handoff`. The active WJ-04 tool-access report is not the historical
`wj04-bolt-tool-receiving-screen.json`; preserve that screen as history.

## Parent-controlled closeout sequence

1. Combined v2 scene browser review and public deployment are complete. The
   live HTML and scene return HTTP 200 and match the pinned local bytes;
   independent review passed family toggles/cameras with no JavaScript
   exceptions.
2. Review the generated WJ-04 tool-access result. Keep the FACOM catalog
   nomination distinct from proven tool motion; its broad envelope overlaps
   do not prove either actual access or physical impossibility.
3. The WJ-06 duty registry is refreshed and source-bound. Regenerate it only
   if a bound input changes; its current counts include zero accepted
   replacements.
4. Narrative, candidate-contract, and artifact manifest describe/pin WJ-03
   through WJ-06 as current diagnostics without gate promotion. Manifest pins
   active probe/mechanics/tool-access/viewer outputs, historical
   receiving/spacer/narrow 3.5-in/rejected-wide JSONs, and refreshed final
   docs. Snapshot owner reports `snapshot_state=consistent`, including
   manifest bytes, producer/input fingerprints, WJ-04 dimensions, active
   identity, viewer, and tool-access checks. No changed or missing dependency
   remains. Snapshot tests (13), Ruff, and parent audit/manifest tests (14)
   pass.
5. Do not launch native solves; no complete joint capacities or release gates
   are established.

No worker should stage, commit, or push; parent owns the final serialized Git
actions.
