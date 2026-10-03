# Stress-frame test finding 1 fix handoff

Fixed finding 1 from `testing-review.md` with test-only changes. The synthetic
DAT fixture now labels `SGLOBAL`, `SLOCAL`, and `SDEFAULT` stress rows from the
independently labeled parent oracle, rather than from `prepare.prepare()`'s
expected tensors. A direct test compares the producer's global and local
expected tensors to the separate reciprocal-compliance calculation. The
calculation remains based on the stated engineering constants, strain, and
axes, and its known-answer test still checks both stress tensors and energy
against the parent oracle.

The swapped-label regression replaces the producer's expected fields with a
global/local swap while keeping fixture stress rows oracle-labeled. It asserts
that the checker refuses the mismatch. Under the former coupled fixture, the
synthetic rows would inherit that simulated swap and the expected refusal
would fail, so the regression protects the producer-to-answer binding.

Changed test files and SHA-256:

| File | SHA-256 |
| --- | --- |
| `docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/test_output.py` | `da222d3ca526ee5700ed9692adebf5c4296405e73ab099cf3874360d27aa88e3` |
| `docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/test_constitutive_answer.py` | `1e862499c16005fa10421594e6c4470a75a8ae65f7c5ca0893bcc1cd164c5fd6` |

Focused verification passed:

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/test_prepare.py docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/test_output.py docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/test_constitutive_answer.py` — 19 passed.
- `.venv/bin/ruff check --no-cache docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/test_output.py docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/test_constitutive_answer.py` — all checks passed.

System-level `pytest` and `ruff` executables were unavailable; the repository
virtual environment supplied both tools. No packages were installed.

This closes only the assigned stress-frame testing finding. All 47 formal
criteria remain pending and readiness remains false. The fixture uses
synthetic analytic DAT text; it does not establish solver behavior or
mechanical acceptance. The planned stress run-provenance wrapper remains
deferred, and the separate TERM-only timeout correctness fix remains with the
parent.

No Docker, native solver, CAD, build, freeze, real solver-output read, ledger
mutation, or Git staging/commit/push occurred. The source-review target and
existing reviewer receipts were not edited.
