# Independent testing review

Reviewed `produce.py` (SHA-256 `662404918c93bb9d96fa48b0b9f02237aaf260b8db1c510dfe866334017e4da7`) and `test_sections.py` (SHA-256 `2632083c4e393b0d212426522405463f642f11cf488155a50617579eb6517aad`).

Checks run:

- `.venv/bin/pytest -q docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01/test_sections.py` — 16 passed.
- `.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01/produce.py docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01/test_sections.py` — passed.

No full extraction or native solve was run. The existing section test uses only a small synthetic CadQuery solid.

## Findings

1. **P2 — The emitted artifact has no synthetic integration or replay test.** `test_sections.py` exercises `plan_planes`, the generic hash verifier, selected point-action helpers, contact crossing, and one synthetic section, but never calls `produce()` (`produce.py:263–499`). Consequently, the suite does not establish that the actual case/state/member/plane loops emit the complete identity set, that the output carries the required geometry and source identities, or that all claim-limit and per-cut non-acceptance fields remain false. The current producer checks only aggregate totals of 252 cut rows and 63 body rows; the tests do not assert unique complete identities or replay equality. Add a temporary-file-backed synthetic fixture that monkeypatches the source documents, hashes, method modules, and STEP importer, then calls `produce()` twice. Assert the exact case × increment × member × plane × trace key sets, unique rows, expected source and geometry identities, repeatable output, refusal after representative case/STEP identity or gate corruption, and the emitted negative claim flags. This can run without private raw evidence or a full CAD extraction.
