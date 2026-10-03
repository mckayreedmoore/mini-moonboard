# STI17 source testing review — pass 2

## Review basis

Reviewed target `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/sti17-source-review-pass2/source-review-target.json`, SHA-256 `c20fba495d8d025933aa6e2551367df9e570943d1cdc96a98b51bfb6674c3570` (4,325 bytes). All 15 listed input files matched both their declared SHA-256 hashes and byte sizes before review. Read repository `AGENTS.md`, the preparation packet README, and the parent-validation handoff for scope and provenance.

Parent-reported source checks: 26 tests / 47 subtests and Ruff passed. I did not rerun them. The immutable base-image timeout known-answer is reported as passed; final STI17 image build and isolated coupon remain unexecuted.

## Finding

### Medium — launcher can authorize a run using a stale review decision

[`launch_sti17_coupon.py`](../../ccx223-sti17-build-coupon-preparation-2026-10-01/launch_sti17_coupon.py:92) reads and validates the review before Docker image and utility preflight. Later, inside the ledger lock, it hashes the review path for the authorization record but does not reread or compare the review contents ([lines 180–182](../../ccx223-sti17-build-coupon-preparation-2026-10-01/launch_sti17_coupon.py:180)). If the review file changes during preflight, the launcher can proceed using the previously parsed `ready_for_scoped_native_run: true` value while recording the hash of the replacement review. Native execution can therefore start without the review currently bound by its authorization record.

Fix by retaining the hash of the exact bytes parsed, then rereading and checking that hash and approval fields under the ledger lock immediately before writing authorization and reserving the slot. Record that validated hash. Add a synthetic test that changes the review during mocked Docker preflight and asserts launch refusal with no ledger reservation.

## Limits

This was static-source review only. No Docker, build, solver, CAD, mesh, native-output, freeze, ledger mutation, or Git action occurred. This report makes no runtime or engineering-acceptance claim; no physical work or candidate acceptance was performed.
