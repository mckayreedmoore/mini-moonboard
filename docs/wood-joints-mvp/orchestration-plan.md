# Wood-joints MVP orchestration plan

Status: active parent-owned persistent goal, 2026-09-24.

## Goal and authority boundary

Continue `compact-floor-flush-wood-joints-development` toward the conditional
DIY engineering MVP in [`next-mvp-plan.md`](next-mvp-plan.md). Parent owns
planning, source decisions, integration, final validation, and Git delivery;
GPT-6 Luna workers handle bounded implementation and review tasks. The earlier
separate paused Luna session was not resumed.

Preserve selected candidate authority, baseline source pin
`df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`, all 66 panel/kicker screw axes,
and the separate-development lane. Do not run native solves or physical work.
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
- WJ-04 binds the 95.25 × 38.1 × 119.7 mm grain-N trial across probe,
  mechanics, and tool-access artifacts. Mechanics now uses the probe's finite
  contact-area method and lists the canonical rectangle separately. Historical
  angle actions remain unreplayed; no fresh demand or capacity is established.
  Its principal bolts have 19.05 mm T-edge distance versus a conditional
  25.4 mm perpendicular-grain loaded-edge 4D reference. Signed demand remains
  unresolved, so this is not a universal failure claim; the narrow trial
  cannot meet that criterion if a nonzero ±T lateral component governs.
  Generic tool envelopes overlap modeled solids, but establish neither actual
  access nor impossibility. The 2×6 rip requires post-rip regrading.
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
| WJ-04 tool refinement | `luna_wj04_tool_access` | Refined report is frozen and source/config bound. It uses synthetic 15°/75° headings, 30° stroke, 60° reindex, analytic rotation enclosure, and separately screened nut/washer removal. The washer's same-stack shaft is excluded only during axial slide (7.7978 mm source-bounded minimum ID vs 6.35 mm modeled shaft max); unrelated obstacles remain. `diagnostic_overlap_present` remains; bounds prove neither actual access nor impossibility. Exact FACOM jaw/handle shape and working sweep remain unsupported. Manifest pins refreshed. |
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

No native solves are authorized or run; another solve requires new user
authorization. Keep one owner per shared file. Parent owns report regeneration
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
