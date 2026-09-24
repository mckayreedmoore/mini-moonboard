# Wood-joints MVP orchestration plan

Status: parent-approved execution plan, 2026-09-23. This plan coordinates
implementation for the separate `compact-floor-flush-wood-joints-development`
lane. It does not reopen or resume a previously paused goal, change the
selected candidate, or authorize a native solve or physical work.

## Ownership and work model

The parent owns scope and configuration decisions, integration acceptance,
final validation, and the serialized commit and push. Implementation work is
delegated to GPT-6 Luna Max workers. The available configuration supports 20
subagents, excluding the parent; this capacity was confirmed for this run.
Workers do not stage, commit, or push. Source and report editors use separate
file ownership; reviews and cross-file integration stay with the parent.

| Work area | Owner | Boundary |
| --- | --- | --- |
| Candidate scope, shared configuration, integration acceptance, final validation, delivery | Parent | Resolve conflicts and approve the checkpoint; serialize all Git writes. |
| WJ-04 configuration | `luna_joint_contract` | Keep one canonical diagnostic geometry and shared trial configuration. |
| WJ-04 center-load-path probe | `luna_center_loadpath` | Update the probe against the canonical diagnostic geometry and ordinary-joint layout. |
| WJ-04 bolt stack | `luna_hardware_tools` | Ordinary hardware stack, thread engagement, and receiving inputs. |
| WJ-05 producers | `luna_socket_spec` | Correct seated socket geometry in WJ-05 producer(s). |
| WJ-03 receiver sequence | `luna_outer_path` | Integrate WJ-05 receivers into the sequence and preserve all fixed screw axes. |
| WJ-04 mechanics | `luna_joint_mechanics` | Recompute diagnostic mechanics for the bound geometry and stack. |
| Cross-consumer tests | `luna_integration_checks` | Check consumers against the shared configuration and refreshed artifacts. |
| Snapshot integrity audit | `luna_snapshot_integrity` | Add independent source and artifact integrity checks. |
| Criteria, duty registry, stock/wood/bolt/transport bases, and reviews | Assigned workers | Keep each bounded to its named records; report findings to parent. |

No worker runs native solves. Parent explicitly permits heavy CAD work when
needed, serialized by the parent after its required inputs are integrated.
Do not combine unbound trial outputs with the active diagnostic model.

## Checkpoint progress

Dependency-closed implementation checkpoints are being committed separately
so reviewers can inspect stable foundations while later consumers continue.
Commits `49647ffd`, `fb63da58`, `505bca16`, and `27125144` record the WJ-04
configuration and stack, shared geometry primitives, preserved source
inventory and frame binding, and seated WJ-05 center-backer diagnostics.
Their focused test and Ruff results were reported to the parent per checkpoint;
they do not establish an integrated pass for the remaining working tree.

Parent fast-forwarded the seven validated checkpoint commits to `master` and
pushed `origin/master` at `55ede246`, then pushed mode fix `1f5f6b0`. Continue
integration on `master`; no feature branch is the active delivery path. The
selected-baseline source reference stays pinned to `df7f5eca`; implementation
commits do not move that reference.

## First integrated milestone

Produce one reviewable diagnostic checkpoint containing:

1. One source-bound WJ-04 ordinary joint using the current diagnostic cleat
   section of **95.25 × 38.1 mm**, with geometry, bolt stack, tool access,
   thread engagement, and mechanics bound to the same configuration.
2. A **100 × 53.34 mm** WJ-04 section retained only as an unbound alternate
   until its geometry, hardware, tools, tolerances, and mechanics are shown to
   match.
3. Corrected WJ-05 seated-socket envelopes and regenerated dependent reports.
   Intended hex engagement must be distinguished from unrelated obstacle
   clearance.
4. WJ-03 receiver and removal-sequence evidence integrated with the WJ-05
   center backers, while all 66 panel and kicker screw axes remain fixed.
5. Source-bound cross-consumer tests, fresh dependent artifacts, and a
   reviewed artifact manifest.

This milestone is diagnostic. It does not accept a joint, establish capacity,
complete the 24-duty frame, pass MVP-L, authorize a native solve, or release
drilling, fabrication, structural use, or climbing.

## Dependency order

Freeze scope and the shared WJ-04 configuration first. Then bind CAD and bolt
stack; calculate mechanics from that exact geometry; run cross-consumer tests;
refresh all affected evidence and hashes; review the integrated diff and
limitations; only then prepare the diagnostic checkpoint for the parent's
commit and push. Snapshot and duty-registry work can proceed independently.
Criteria plus stock, wood, bolt, and transport bases support later gates but
do not waive them. No native solve starts before its applicable geometry,
mechanics, and evidence gates pass and the parent authorizes it.

## Checkpoint gates and delivery

Use focused checks for each dependency-closed source-only checkpoint. Do not
require the full repository suite or full CAD rebuild before every such
commit. After integrated edits settle, run repository CI from the pushed
`master` commit and complete parent-owned final validation before reporting a
full pass:

```sh
uv sync --locked
uv run ruff check .
uv run pytest
uv run scripts/smoke_test.py
uv run python -m scripts.current_candidate --check-exports
```

The broad focused integration batch, once its producers and artifacts settle,
is:

```sh
uv run pytest tests/test_wood_joint_frame.py tests/test_wood_joint_geometry.py tests/test_wood_joint_inventory.py tests/test_wood_joint_clearance.py tests/test_wj04_fastener_stack_method.py tests/test_wood_joint_wj04_early_mechanics.py tests/test_wood_joint_wj05_receiver_audit.py tests/test_wood_joint_wj05_socket_geometry.py tests/test_wood_joint_snapshot_fixes.py
```

CI workflow is `.github/workflows/ci.yml` (`CI`); pushes to `master` trigger it.
The run for `55ede246` failed at lint with `EXE001` in
`scripts/prototype_barrel_clearance_active_set.py:1`: it has a shebang but Git
records it as non-executable. Tests, smoke test, and export verification were
skipped. Baseline run `35821973929` also failed at lint; the flagged file,
Ruff configuration, and lockfile are unchanged from its `df7f5eca` source, so
the same `EXE001` explains that baseline failure. Parent pushed executable
mode fix `1f5f6b0`. Its CI run `35945309344` passed lint and has tests in
progress; later checks remain pending. Do not report full CI success until the
run passes.

Regenerate each source-bound artifact with its documented producer after its
inputs settle; then check producer hashes and artifact-manifest parity. Do not
present earlier worker test results as a pass for the integrated tree.

The local pre-commit and pre-push hooks enforce only the Denver quiet-hours
rule. They do not run tests or lint. The repository CI runs the commands above;
the optional historical-export CI path is outside this diagnostic checkpoint.

Parent has fast-forwarded the reviewed checkpoint to `master` and pushed
Parent retains all Git writes and validation ownership. The owner explicitly
authorized updating the online viewer. Its live URL is
<https://mckayreedmoore.github.io/mini-moonboard/>. Pages deployment uses
`.github/workflows/static.yml`, which publishes from `master`; run
`35944973424` was cancelled when the next master push started replacement run
`35945309339`. That replacement run is in progress. The viewer HTML and scene
and `site/index.html` link remain local changes; they are not in current
`master`. Integrate those files through parent review and a master commit, then
verify the resulting Pages run and live viewer before reporting publication.
No feature-branch preview or branch-policy bypass is in scope.
