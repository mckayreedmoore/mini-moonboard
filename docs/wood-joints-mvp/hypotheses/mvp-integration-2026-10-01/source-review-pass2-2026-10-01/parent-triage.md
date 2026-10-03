# Primary triage of source review pass 2

The three independent roles reviewed target SHA-256
`02452912a8882bff4fbca15ee347d539a51c3bf827b3ac27154a6b763dd3b650`.
All 15 input pins matched through review closure. Their original bytes are
preserved in `review-target-sources.tar.gz`, authenticated by
`review-target-archive.json`; test fixes do not rewrite this target.

## Confirmed findings and ownership

- Correctness: the stock runner uses TERM-only `timeout 60s` and permits the
  Docker client 90 seconds before cleanup. A solver ignoring SIGTERM can
  exceed the stated 60-second native ceiling. The STI17 checker accepts that
  command. This is a confirmed execution-control defect and keeps build/run
  readiness false. Primary owns its future fix, command binding, independent
  review and small timeout known-answer qualification. Increasing the budget
  does not resolve it. Preserve the original stock runner, immutable source
  snapshots and historical output gates while accounting for any source/pin
  changes. No timeout-control code was changed during this pass.
- Testing, finding 1: the DAT fixture copies expected tensors from the same
  producer; the existing independent tensor test validates the parent oracle
  but not the producer's global/local label assignment. Confirmed. Second
  secondary owns a test-only fix in `test_output.py` and
  `test_constitutive_answer.py`.
- Testing, finding 2: coupon readiness tests lack independent image-ID and
  image-receipt-digest mutations. Confirmed. First secondary owns test fixes.
- Testing, finding 3: the recorded-output test passes one hash mapping as both
  observed and recorded data; mismatch/missing-record refusals are uncovered.
  Confirmed. First secondary owns test fixes.

Architecture's initial live-oracle finding was withdrawn after reviewing the
full chain. Coupon preparation snapshots and pins the oracle, and the checker
calls the stock verifier with its default `check_live=True` before import.
Primary independently exercised a synthetic freeze: unchanged live oracle
passes and changed live oracle is refused. The evidence is in
`parent-live-oracle-drift-triage.json`. No source change is justified by that
reported scenario. Final architecture receipt reports no substantial finding.

## Independent-review provenance

Correctness used exactly one Luna/max reviewer through first secondary.
Architecture used one Luna/max reviewer through primary. Testing's assigned
Luna reviewer mistakenly spawned an extra helper; second secondary interrupted
that helper to enforce the single-reviewer limit, read no helper findings and
confirmed its terminal state. The assigned reviewer completed its own static
review and wrote `testing-review.md`. This interruption was not an observation
timeout or a restart. The receipts disclose the deviation.

The later implementation tasks use exactly one Luna/max worker per secondary,
with separate test-file ownership and no nested helpers. Primary owns final
validation. A fresh three-role review of any final corrected source remains
pending. The account reached 99% included usage during these bounded tasks;
finish/checkpoint assigned work only, start no further review round or native
run, and stop on fresh unknown/exhausted quota without credits or paid fallback.

No build, image creation, coupon freeze, native solve, CAD or mesh job occurred.
The stress provenance wrapper remains unimplemented. All 47 criteria and the
full conditional MVP-E remain pending; physical release flags remain false.

## Separate owner-directed joint work

Research/status thread `01a0f877-dd48-7ce1-a025-39a6fc1a88f3`, tmux `main:9.4`,
reports a later owner instruction to carry one open joint to conditional MVP
completion with reasonable assumptions. Its proposed upper-left service outer
block is disjoint from these source tasks. Primary acknowledged ownership and
asked it to preserve reviewed geometry, complete force/moment and joint-mode
accounting, label the assumed local load/material contract, retain the missing
frame-case distinction and link its final packet to the canonical handoff.
Its closure packet is not yet reported. Do not infer authenticated six-case
frame acceptance or change the full criterion/release authority from that work.

## Post-fix primary disposition

Both assigned test-only fixes are complete and primary-verified. STI17 passes
16 tests and 41 subtests; stress-frame passes 19 tests; Ruff passes the three
changed test files. Those are the only three changed target inputs; twelve
other target inputs and the original stock runner remain unchanged. Exact
current hashes and worker/reviewer pins are in
[post-fix-parent-validation.json](post-fix-parent-validation.json).

The runtime hard-stop defect is still open and the stress provenance wrapper
is still unimplemented. Fresh final independent review remains pending.
At 99% included use no further worker/review/native task is assigned to the
two secondaries. Their scoped deliverables are complete; this does not complete
the primary's full MVP-E. Research's separate owner-directed joint packet
remains pending and must be obtained from `main:9.4` before using it.
