# STI17 test-fix handoff

Completed the assigned source-only fixes for testing-review findings 2 and 3
on 2026-10-01. The scope was
`compact-floor-flush-wood-joints-development` /
`led-clearance-2x6-runner-seated-blocks-v1`.

Changed paths:

- `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_sti17_preparation.py`
- `docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-review-pass2-2026-10-01/sti17-test-fix-handoff.md`

The owned test file changed from SHA-256
`5cf7fde69fb3b723c21f913708c51b135fab9d887b11ce199e82d77899c0ac83`
(24,324 bytes) to
`76f12fac44bea9efa3c06fa77411ac96ea338c5fc20ff0f945e83daadd8da2ad`
(27,232 bytes). Readiness coverage retains the build-receipt rejection and
adds independent readiness `image_id` and `image_receipt_sha256` mutations.
Recorded-output coverage hashes synthetic `.sti`, `.mas`, and `.dof` fixture
files, checks the successful record, and independently rejects mismatched and
missing recorded hashes for each name.

Focused checks using the repository `.venv`:

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_sti17_preparation.py` — 16 passed.
- `.venv/bin/ruff check --no-cache docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_sti17_preparation.py` — all checks passed. An initial attempt placed `--no-cache` before `check`; Ruff rejected that argument order, and the corrected command passed.

Included-usage checks observed 98% and later 99%; every observation reported
`ordinary_usage_allowed=true` and `limit_reached_type=null`.

The immutable `source-review-target.json` remains at SHA-256
`02452912a8882bff4fbca15ee347d539a51c3bf827b3ac27154a6b763dd3b650`.
The original review source archive and receipts also remain byte-identical:

- `review-target-sources.tar.gz`: `59d7479655db39f62b09a40ff1e635c0e32d89b269556155d31279d651c74c62`
- `correctness-review.md`: `fc359a1ce371274fbb902bebb56e8ec2639e581ed990cb85d7649e2b7a662d70`
- `testing-review.md`: `ebdf56c7f7561a180dd8ba6a7344f1b143936f90f59710d0c8b6d2f7183ab2d3`
- `architecture-review.md`: `34ca37e20a112f94bc9267f2e217735c3cf79059de90bfc1b8d64a9b0d88e190`

All 47 formal criteria remain pending and parent readiness remains false. Work
was limited to synthetic source tests and this note: no production code,
stress-frame tests, Docker, native execution, CAD, build, freeze, saved solver
or matrix-output reads, or ledger mutation. The separate TERM-only timeout
fix remains parent-owned.
