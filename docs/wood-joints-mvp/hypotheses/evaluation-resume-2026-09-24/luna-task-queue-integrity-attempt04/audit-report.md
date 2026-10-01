# Luna coordinator consistency audit — attempt04

Audit date: 2026-09-28. This review binds the exact queue, status, handoff, and manifest byte snapshots listed below. It is a read-only consistency review; it does not establish engineering acceptance or alter source-snapshot authority.

## Result

**PASS — current coordinator bindings and the T04 attempt07 record are internally consistent.** All 268 artifact-manifest paths exist and match their listed SHA-256 digests. Queue, status, handoff, and manifest pins agree; all checked queue paths and local Markdown links resolve. The 47 criteria remain uniquely identified and pending, and engineering/release completion flags remain false. T04 attempt07 is correctly represented as geometry-only evidence with mechanical duties and `overlap_contact` acceptance still open.

The queue's `plan_review.status` remains `checkpoint_update_pending_independent_consistency_review`, as requested. After this independent result is reported, that review can be closed as a coordinator-consistency checkpoint without changing `source_snapshot_sha256` or any source-snapshot authority. The closeout should bind this report and the queue/manifest digests, then refresh the manifest's queue entry because the queue metadata changed; it should leave the 12 pinned source-snapshot entries unchanged.

## Bound coordinator snapshot

- `docs/wood-joints-mvp/luna-max-task-queue.json` — SHA-256 `a50122a85d9a1ff5db558d658dce8d052580e858293e9abeba3fe08834bba7af`.
- `docs/wood-joints-mvp/luna-max-status-2026-09-28.md` — SHA-256 `9262839f25f7d0219d734e9fbb2926cf3f77bb46790ba46c5fb86cbaac5d5d05`.
- `docs/wood-joints-mvp/luna-max-completion-handoff.md` — SHA-256 `667673720ad417f36da50742aa50862c9e8d14fabfa4d4134c8d49d8f1c21f33`.
- `docs/wood-joints-mvp/artifact-manifest.json` — SHA-256 `93b2e9f790e52b5825c3a73ff3f491373a03cd05337abb7b528e26e017409411`.

Queue and manifest parse as strict JSON with duplicate-key rejection and declare `wood_joint_luna_max_completion_queue/v1` and `wood_joint_artifact_manifest/v1`. The manifest has 268 entries: 268 paths exist, zero hash mismatches. It binds the queue, status, and handoff to the exact digests above. The queue's `checkpoint.live_status_path` resolves to the bound status file, and `plan_review.handoff_document_sha256` equals the live handoff digest. All 29 local links in the status note and all 68 local links in the handoff resolve. The queue's 309 repository-relative file references resolve; all 40 T04 terminal-artifact paths exist.

The candidate is `compact-floor-flush-wood-joints-development` and the revision is `led-clearance-2x6-runner-seated-blocks-v1` throughout the coordinator records. The queue's 12 `source_snapshot_sha256` entries all exist and match their pinned hashes. Current case IDs remain the six unique entries `a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear`, and `a1-rear`.

The 47 criterion-ownership rows have 47 unique IDs and all 47 handoff statuses are `pending`. Queue `release=false`, queue `engineering_mvp_complete=false`, checkpoint `engineering_mvp_complete=false`, and manifest `release=false`. The scoped current-map method fixture has `current_map_readiness=true` and a prior native execution; those fields describe its separate bounded fixture and do not establish candidate readiness, current-joint response, or MVP completion. T02 production-build/native authorization and T03 readiness/native authorization remain false in their current queue rows. The status states there is no response-validated joint and no auditable current-joint response.

## T04 attempt07 verification

The active T04 task and its `overlap_contact_geometry_evidence_attempt07` subtask agree: attempt07 is parent- and independently reviewed at geometry-only scope, while mechanics remain open. Its next action calls for source-bound interface ownership, active bearing/engagement, and T03/T09 response/map evidence; it preserves the six unresolved pairs and 1,078 AABB-only observations as limited evidence and keeps all criteria pending.

Attempt07 declares candidate/revision as above, criterion `overlap_contact`, disposition `pending`, and evidence status `partial_geometry_inventory_only`. The 50-node inventory contains 1,225 unordered pairs: 147 exact-BRep evaluations, 1,078 AABB-separated pairs not evaluated exactly, 115 finite opposed-planar classifications, 26 exact-BRep-separated classifications, and six zero-area/unresolved pairs. The evidence explicitly sets active contact, bearing/pressure, load-path ownership, contact law, force transfer, and criterion acceptance to false. It excludes connector/fastener solids and does not infer face ownership. The queue/status/handoff use matching counts and state that geometry does not establish mechanics or acceptance.

The queue's nine current attempt07 artifact pins all match, and all nine paths exist:

| Attempt07 artifact | SHA-256 |
| --- | --- |
| `scripts/wood_joint_wj08_overlap_contact_geometry_attempt07.py` | `5b34c94bb1bf072b4128d694425129b651a144c44099b90f2bc7da2e312f2c57` |
| `tests/test_wood_joint_wj08_overlap_contact_geometry_attempt07.py` | `ab7911763dd65f0a1f2349f0cc00f465f785b31d82d0961f83721de727fe0552` |
| Attempt07 `README.md` | `b8b5d4f053f247b6efc9b0ed9262222bcbec7a27cf80b15fa665d60cb6c24020` |
| Attempt07 `geometry-evidence.json` | `24282db614089fcff73d11fcfd1216aaaff5e2d7babc1af2fa971390c29a7448` |
| Attempt07 `source-pins.json` | `c187f27a838a56407411a53a7a9b54285b651f414e3827697a2bbf6c40a71500` |
| Attempt07 `SHA256SUMS` | `86bfc71d7fd8f2d4a23b5cc27ca632b36242de01586f2932d5a5616b7266e0e6` |
| Correctness `review-record.md` | `a7f5c0f7dcbe18e7a13a8b9c8e339eedb4a8ace4b7b1fda82f991e7eae289863` |
| Testing `review-record.md` | `8101bd2074274a78af16fa878cd2f73004c434fcf871bb697ffd76f4c41b4769` |
| Architecture `review-record.md` | `1306af7c2a43f2ba8f0a6913f9cf0bc5bb68619e126ea22b97eb5ea59a3fd952` |

Both attempt07 packet JSON files parse with duplicate-key rejection. The source-pin record binds 62 repository inputs; all 62 paths and hashes match. Its four attempt06 predecessor-packet file pins and three predecessor-review pins also match. The three current attempt07 reviews report no findings in their declared scopes. Their records document 20 focused tests and packet verification as passing; this audit did not rerun tests or the producer verifier.

The superseded attempt06 architecture-review path in the queue had pointed to a nonexistent `architecture-review.md`; the final audited queue now points to the existing `review-record.md`, matching the T04 terminal-artifact list and attempt07 predecessor chain. No missing queue path remains.

## Method and limits

I used duplicate-key-rejecting JSON parsing; recomputed all manifest hashes; checked queue/status/handoff bindings and local links; resolved queue and T04 artifact paths; checked the 12 source-snapshot pins, 62 attempt07 source pins, predecessor packet/review pins, and all nine current attempt07 artifact hashes; and compared criterion, release, candidate/revision, count, and scope fields. Test counts are quoted from frozen packet/review records, not run by this audit. No project tests, producer verification, solver, Docker command, native mechanics run, or engineering disposition was performed. This report is intentionally outside the audited artifact manifest; its own SHA-256 is supplied with the audit result.
