# Luna task-queue integrity audit — attempt03

Audit date: 2026-09-28. This read-only report binds the exact queue, live-status, and artifact-manifest byte snapshots below. It records consistency evidence only; it does not revise queue, status, manifest, source, criteria, or release state.

## Bound inputs and result

- `docs/wood-joints-mvp/luna-max-task-queue.json` — SHA-256 `0bb82ded0a5f923bf67453146d86121c7eeffee4ea8e96d62b5b8ea545cc9d0d`.
- `docs/wood-joints-mvp/luna-max-status-2026-09-28.md` — SHA-256 `5ff927f4257dc138bc78856a0e40352b73318fd0ebc7bc00ad29870e516960a1`.
- `docs/wood-joints-mvp/artifact-manifest.json` — SHA-256 `726f0134274a58cd01556c7306c8de3e8fde4109285ee9efa0e69738814eb692`.

Both JSON files parse with duplicate-key rejection and declare `wood_joint_luna_max_completion_queue/v1` and `wood_joint_artifact_manifest/v1`. Their required top-level fields and expected value types are present. No standalone JSON Schema for these two versioned objects was found, so this validates strict JSON, declared schema IDs, and structural/state semantics rather than an external schema document. The manifest binds the queue and status hashes above; all 33 manifest paths exist and match their listed SHA-256 values.

**Result:** queue, status, and manifest bindings pass for this snapshot. T02, T03, and T06 current task states align with the current status note. All referenced report/evidence paths checked from the queue and status note resolve. One historical-checkpoint wording caveat is recorded below; it does not contradict the current task rows or newest attempt checkpoints.

## State and evidence checks

- Candidate/revision remain `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`; the queue preserves the Full MVP-E goal scope. The queue has 14 unique task IDs and state counts of 2 `done`, 4 `active`, 6 `queued`, and 2 `waiting_dependency`.
- The 47 criterion-ownership rows have 47 unique IDs: 36 `adopted_legacy` and 11 `new_candidate_obligation`; all 47 handoff statuses are `pending`. The six current case IDs are unique: `a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear`, and `a1-rear`.
- Queue `release=false`, queue `engineering_mvp_complete=false`, and manifest `release=false`. No current-joint case is frozen or run, and the status says no auditable current-joint response exists. The queue's current-map benchmark freeze/run fields are separately scoped and do not establish a current-joint result.
- **T02 capture attempt09:** queue state is `waiting_dependency`, with 39 offline tests, 18/18 parent inventory checks, zero-fuzz replay, modified-source hash match, and the three completed reviews. The source-pins file hashes to the queued `bcbf1bc560cbf436fb0ad6547ac5e6abf10e83b849829c42eac256f66c60de62`. Production build and native authorization remain false; pinned runtime access is unavailable. This agrees with the live status.
- **T03 coupon attempt07:** queue state is `waiting_dependency`. The input-freeze file matches SHA-256 `c4cc230277d321d5fdf5e255270291cbc5825adaa3829632a5a774240d62a775`; terminal-hashes matches `69ceb7ff3ca8df2311328d6dfc5600f7d8934e7f97c93c930410eaf2ab99652a`. The three reviews and 9/9 parent static checks are recorded; readiness, authorization, and execution-artifact presence are false. The status agrees that it remains unrun pending pinned runtime, durable run-once tracking, and fresh readiness/authorization.
- **T06 current group-action attempt10:** task phase and current checkpoint identify parent-validated bounded-method scope. The parent-validation file matches SHA-256 `ab9c5afae086dfb901befa2841cd5de61e181b573592dcfb22dbf350df76d44a`; terminal-hashes matches queued SHA-256 `4705c261742527dfb7f2edd9bcf4668d0c388d7d4cb0bc6b3f9290e9f0d0fe94`. The 51-test result is recorded as NDS-2024 `Cg` for one-to-three-member rows and declared sensitivity-path reconciliation only; no capacity, per-bolt force distribution, or criterion disposition follows. Four-plus-member applicability remains unsupported. The current task's terminal artifacts include producer and parent-validation outputs.
- **Steel-direct attempt03:** the task and status describe a bounded applicability gap for timber through-bolt N+V+M transferability, not proof that no method exists. No capacity or criterion disposition is claimed.
- Queue path scanning found 187 distinct repository-relative file references; all exist. All four local Markdown links in the live status resolve. Manifest and queue/status checks were read-only; no tests, coupon runner, solver, Docker command, or native work was run. Test counts above are recorded packet results, not tests executed by this audit.

## Historical checkpoint wording

The queue retains attempt-scoped prior checkpoint entries: attempt01's single-case preparation state, the attempt04 replay's `next_route_review` text about preparing a fresh coupon freeze, and attempt03's 29-test group-action review state. These entries describe their named prior attempts. Current T03/T06 task phases, attempt07/attempt10 checkpoint records, active-subtask states, the refreshed plan-review note, and the live status identify the later attempt07/attempt10 states. Treat the old checkpoint prose as historical; it does not change the current no-run/no-readiness state or the 47 pending criteria.

## Audit method and limits

I parsed queue and manifest with duplicate-key rejection; checked declared schema IDs, structure, task/criterion/case uniqueness and state invariants; recomputed every manifest digest; checked queue and status bindings; verified listed T02/T03/T06 evidence hashes; and resolved queue path references and status links. No project tests or native actions were executed. This report binds only the three input snapshots listed above. Its own SHA-256 is supplied with the completion message; the queue and manifest were not changed during this audit.
