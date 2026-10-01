# Attempt 04 architecture and integration review

Reviewed 2026-09-27. This is a read-only review of the attempt04 method boundary, its criterion-map registration, and its bound source artifacts. Prior review reports were not used. No tests, solver, or Docker were run for this review.

## Assessment

Attempt04 stays within a coherent method-only boundary: it returns `Cg` for a narrowly defined row, leaves capacity and criterion disposition pending, and documents that it does not establish source authority or candidate acceptance. The attempt packet’s recorded source hashes match the maintained module, tests, and method map; the three pinned attempt03 snapshots also match. The packet records 34 focused tests passing, but that result was read from its hash-bound output rather than rerun here.

Two integration gaps remain. The public helper can calculate a factor after an overflowing load-vector norm has collapsed to a zero unit vector, and the current criterion coverage register does not point readers to the newly registered producer. Neither issue changes the current acceptance state: `additional_group_reduction_sensitivity` remains pending.

## Ranked findings

1. **P2 — An unrepresentable load-vector norm can pass row-direction validation.** In `mini_moonboard/nds_2024_group_action.py`, `_unit` divides vector components by `_norm` without checking that the norm is finite (`:159`). The group-action helper rejects only a zero lateral norm before normalizing, then checks alignment (`:407`). For finite components such as `[1.6e308, 1.6e308, 0]`, `math.hypot` returns infinity; normalization produces `(0, 0, 0)`, whose cross product with any row axis is zero. A valid otherwise-bound payload can therefore receive `calculated_method_only` `Cg` for a load direction that was never established. Reject non-finite norms before normalization, or use a scale-stable direction normalizer and fail closed when it cannot produce a finite unit vector.

2. **P3 — The current coverage register does not surface the producer.** `criteria-method-map.md` now names both public helpers and states their scope (line 45). The current coverage table and its machine record still show only the generic `M2 → R1 → C1/F1` dependency and “no candidate group factors,” with no link to this method implementation (`current-criteria-coverage.md:41`, `current-criteria-coverage.json`). This is not an acceptance conflict—the method map says all criteria remain pending, and the helper emits no disposition—but it leaves the producer discoverable only through the method map or code search. Add a cross-reference in the current coverage row when that register is next maintained.

The production-caller search found no imports or calls from `mini_moonboard/` or `scripts/`; the only current references are the implementation and its tests. This is consistent with the documented method-only stage and the still-required WJ-08 criteria producer. Candidate acceptance remains separate: the helper returns `capacity: null` and `criterion_disposition: "pending"`, while both criteria registers retain pending status.

## Exact files reviewed and SHA-256

Hashes identify the exact bytes reviewed. The report itself is excluded from this list.

| File | SHA-256 |
| --- | --- |
| `AGENTS.md` | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| `mini_moonboard/nds_2024_group_action.py` | `d0d8cf193c9fb26206e459e749c176f0ace5b41bb472ffc24217d8a5942874f6` |
| `tests/test_nds_2024_group_action.py` | `c0137a5144e135e2bac3a4eb6861e0e85d10750b0b3471eb4fc55df13222c3f2` |
| `docs/wood-joints-mvp/criteria-method-map.md` | `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7` |
| `docs/wood-joints-mvp/current-criteria-coverage.md` | `ccda149cf7add227a7a038311625595764331c57a43af6b23de973a88d1b6e0a` |
| `docs/wood-joints-mvp/current-criteria-coverage.json` | `c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt04/README.md` | `5efac9335e7ba43da6d221c6ef62864ef971b4d2efb186048497bcf3c2987bd6` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt04/attempt04.patch` | `df4268c1fb255f228ff1da58865a6085efc342509b16d6c1c5cc3951f233ba1a` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt04/offline-test-output.txt` | `73240cdaab3350e1db617e842b82ef4ecec3d2cdf4a6ae90cb8af443127e297b` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt04/source-pins.json` | `dcf5fd27defe0c50f1db0f46eea079f80e05a3d0b303bc033a3b970c9824f0ee` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt04/terminal-hashes.json` | `74ef1baf1469d15338b8fdea823ace903c924ba289e6bceb3208a3357ba3f3a0` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt04/validation.json` | `ac92545e0b530924b275db13432a376f3908c0dfd2b368b7c2ea99187366fb7e` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt04/base/mini_moonboard/nds_2024_group_action.py` | `8dac7e4b749d7b9253b5a4801c169d759e486030aac719b8c55dae80d9606488` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt04/base/tests/test_nds_2024_group_action.py` | `5a63579be46d795068e44f77244366d6d2bc411d574eb52e5fe9af9ccf9d0365` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt04/base/docs/wood-joints-mvp/criteria-method-map.md` | `2ab30c154d75306cb83c88fdde98f7af8082b3c57089a9fdf587c5b3b9818182` |
