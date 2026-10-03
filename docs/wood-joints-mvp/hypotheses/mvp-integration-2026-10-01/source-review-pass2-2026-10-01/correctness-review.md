# Correctness review

Target: `docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-review-pass2-2026-10-01/source-review-target.json`  
Target SHA-256: `02452912a8882bff4fbca15ee347d539a51c3bf827b3ac27154a6b763dd3b650`  
Candidate/revision: `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
Role: independent correctness review, source-only.  
Observed quota: 98% included weekly usage; ordinary usage allowed; no reached limit. Fresh checks at start, during review, and before writing agreed.

The target measured 4,278 bytes. All 15 target-listed files matched their pinned byte sizes and SHA-256 hashes both before review and at closure. The target hash also matched at closure.

## Finding 1 — Coupon runtime lacks a hard 60-second stop

Evidence: `fea/wood_joint_reduced_native.py:129-132` invokes `timeout 60s` without a kill-after bound; `fea/wood_joint_reduced_native.py:173-189` allows the Docker client 90 seconds before attempting forced container removal. The exact-command check in `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/check_sti17_coupon.py:194-229` accepts that TERM-only command.

Impact: if CalculiX does not terminate on SIGTERM, the single coupon attempt can continue beyond its declared 60-second ceiling, until the runner's 90-second timeout triggers cleanup. The attempt then fails closed because the checker requires a successful terminal execution, but the runtime ceiling is not enforced as stated.

Remedy: impose a hard stop within the total 60-second allowance (for example, configure a bounded kill-after interval with a correspondingly shorter TERM interval, or enforce container termination at the 60-second deadline) and bind that command in the checker and its synthetic command cases.

The stress-frame fixture's reciprocal-compliance calculation, rotated tensor components, and strain-energy density independently reproduce the pinned oracle to floating-point precision. The pinned CalculiX manual pages support the local-by-default and explicit-global output behavior and the orientation definition. The explicitly deferred stress provenance wrapper remains a later deliverable and is not a finding here.

Limitations: no Docker, build, native execution, CAD, freeze, ledger mutation, actual solver or matrix-output reads, tests, code fixes, or Git operations were performed. The 15 STI17 synthetic tests/Ruff and 17 stress-frame tests/Ruff are recorded claims in the reviewed preparations, not rerun results from this review. All 47 formal criteria remain pending.
