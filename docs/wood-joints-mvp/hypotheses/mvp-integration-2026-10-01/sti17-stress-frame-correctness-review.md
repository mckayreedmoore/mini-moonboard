# Independent STI17 and stress-frame correctness review

Review date: 2026-10-01

This was a read-only source review of the STI17 coupon-preparation packet and
the rotated orthotropic stress-frame producer/checker. I read their READMEs,
Python source and synthetic tests, the existing `fea/wood_joint_reduced_native.py`
runner, and the pinned CalculiX 2.23 `*EL PRINT`, `*ORIENTATION`, and `*ELASTIC`
manual sections. I did not run tests, Ruff, Docker, a build, a solver, CAD or
mesh tools; read the run ledger or `.sti`/`.mas` outputs; or change readiness,
freeze, candidate, or implementation files. The included-usage check was fresh
at 98% when review began.

## Finding

**Medium — STI17 coupon result can pass without proving the reserved runner
launch.** In `check_sti17_coupon.py:155-180`, the checker reads the local
`authorization.json`, `execution.json`, and independent review and validates
their fields. `check_sti17_coupon.py:106-113` binds output-file hashes to the
local execution record. It never checks the matching row in
`docs/wood-joints-mvp/luna-max-native-run-ledger.json`, including the ledger's
hashes of those records and its consumed-terminal, one-launch state. Therefore
self-consistent local JSON and output files can satisfy the checker without
proving that the existing runner reserved and consumed the single native slot
for this freeze. This weakens the stated run-provenance claim, although a pass
still makes no candidate-acceptance claim.

**Fix:** Read the ledger without modifying it and require exactly one row for
the recorded run ID with the expected scope, attempt directory, freeze hash,
`max_launches == launches_consumed == 1`, terminal state, and matching hashes
for `authorization.json` and `execution.json`. Preserve the existing checks of
the review and raw output hashes.

## Review notes

The stress-frame deck producer’s extraction of the first two orientation axes
matches the pinned rectangular-orientation convention. Its output requests
global stress explicitly and local stress both explicitly and by default;
the pinned manual specifies local output by default and the orientation name
suffix for local rows. The checker compares all expected integration points,
all displacement nodes, the frame tags, time, and analytical energy. I found
no other substantial source-level correctness issue in the scoped preparation
or numerical-checker code. The stress fixture remains unfrozen and unexecuted,
and its separate output-provenance wrapper remains unfinished as its README
states; this review does not establish solver behavior or joint qualification.

The reported synthetic-test and Ruff results were not rerun. All 47 formal
criteria remain pending, and no physical release is implied.
