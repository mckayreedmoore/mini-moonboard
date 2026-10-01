# Attempt06 architecture review

Review date: 2026-09-28  
Review type: fresh, read-only architecture review  
Scope: attempt06 packet, maintained group-action module and tests, criteria method map, current criteria coverage, and source criteria. No previous review reports were inspected.

## Executive assessment

No material architecture finding blocks attempt06. The patch stays inside the existing pure group-action method module and its focused test module. It hardens two input-boundary cases and makes sensitivity path reporting respect JSON scalar encodings without adding dependencies, I/O, candidate state, or a new runtime boundary. The evaluator continues to require caller-supplied independent bindings and returns method-only results with capacity absent and criterion disposition pending; that is consistent with the method map and current coverage register.

The module remains a cohesive, narrowly scoped producer for NDS-2024 Eq. 11.3-1. Its method boundary is explicit in the module docstring and result payload ([module](/home/mckay-linux/repos/mini-moonboard/mini_moonboard/nds_2024_group_action.py:1), [result contract](/home/mckay-linux/repos/mini-moonboard/mini_moonboard/nds_2024_group_action.py:493)). The current docs keep the larger coordinator, fresh group inventory, bolt actions, and criterion disposition outside this method helper ([method map](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/criteria-method-map.md:45), [coverage register](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/current-criteria-coverage.md:41)).

## Scores

| Criterion | Score | Evidence |
| --- | ---: | --- |
| Modularity | 4/5 | Existing module and test boundary remains focused on one calculation method. |
| Cohesion | 5/5 | Hash validation, row geometry, Eq. 11.3-1, and sensitivity contracts belong to this method boundary. |
| Separation of concerns | 4/5 | Source authority and candidate acceptance remain external; the evaluator explicitly disclaims verifying those authorities. |
| Abstraction | 4/5 | The canonical digest and pending-result helpers centralize repeated contracts without hiding the calculation scope. |
| Loose coupling | 4/5 | No new imports or runtime dependencies; inputs and independent bindings are passed explicitly. |
| Testability | 4/5 | Focused deterministic regression tests cover the changed edge cases and contract failure. |
| Deploy-ability | N/A | This is a pure analysis library with no deploy unit or runtime configuration. |

## Findings

No architecture findings.

The three changes are localized and preserve the existing API shape:

- Canonical JSON hashing now catches recursion exhaustion around both strict-value traversal and JSON encoding, allowing the public evaluation path to return pending for an excessively nested payload ([hash helper](/home/mckay-linux/repos/mini-moonboard/mini_moonboard/nds_2024_group_action.py:100), [regression](/home/mckay-linux/repos/mini-moonboard/tests/test_nds_2024_group_action.py:521)).
- Stable vector normalization remains the existing method; the new regression demonstrates a finite row axis with an overflowing raw norm can still produce the expected row pitch when all directions align ([normalization](/home/mckay-linux/repos/mini-moonboard/mini_moonboard/nds_2024_group_action.py:159), [regression](/home/mckay-linux/repos/mini-moonboard/tests/test_nds_2024_group_action.py:501)).
- Sensitivity-path comparison now detects equal-valued JSON scalars with distinct Python JSON encodings, and the test verifies that omitting the changed path leaves evaluation pending ([path comparison](/home/mckay-linux/repos/mini-moonboard/mini_moonboard/nds_2024_group_action.py:518), [regression](/home/mckay-linux/repos/mini-moonboard/tests/test_nds_2024_group_action.py:540)).

These changes do not make the helper an evidence producer for the current candidate. The method map says it supplies no resistance, per-bolt force distribution, demand/capacity comparison, or criterion disposition. The current coverage row still reports no candidate group factors or bolt-group actions and marks the criterion pending. The machine criteria retain all release flags false and engineering MVP incomplete ([criteria](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/criteria.json:9)).

## Verification

- Attempt06 packet file hashes match `terminal-hashes.json`.
- Packaged attempt05 base hashes match `source-pins.json`.
- The attempt06 patch applies with `patch --fuzz=0`; replayed module and test hashes exactly match the maintained files and `terminal-hashes.json`.
- The pinned criteria method-map hash matches the reviewed method map.
- Reproduced the focused suite: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py` — **39 passed in 1.24s**.
- No solver or Docker command was run.

## Reviewed input hashes

SHA-256 values bind this review to the exact packet, maintained source, tests, and allowed criteria documents reviewed.

| Input | SHA-256 |
| --- | --- |
| Attempt06 `README.md` | `c89a90a34cfb37dad9f1291f48b8ead6c8432c55ef6a25c0dc510688888f1243` |
| Attempt06 `attempt06.patch` | `e33f660e04a7dd0b1a03ebbd05fc204610d31f23192ce7e4c432fe3227323f1f` |
| Attempt06 `offline-test-output.txt` | `8426988acd080f590f1fc1eb1d7db825ac33e04c96044753f4f810e19a35842e` |
| Attempt06 `source-pins.json` | `2ebf7a3de52ab771e44ec7db81490001d228c2429c79a7e73feed6980f2a092d` |
| Attempt06 `terminal-hashes.json` | `9b098dcf7bb23991c0fbf0e711e6a5eb651664c29cbd16a035617abedd01c3fa` |
| Attempt06 `validation.json` | `c964f1563da4d81daffa8dabf14816a09247b91882ca1a0d6d035fddd74e6208` |
| Packaged attempt05 base module | `95305398bf4fc9590f33fe877aafaf0544dce91503b0f09d84db590a938c8122` |
| Packaged attempt05 base tests | `91868751abfef9ceab746927904d7cbab9c0ba0881867980d89e2f2ab0b828e7` |
| Maintained `mini_moonboard/nds_2024_group_action.py` | `65a8a5ea7fb4c76e84dc8f2ec475c17355fbbc29665f88f7f913432ca719daf9` |
| Maintained `tests/test_nds_2024_group_action.py` | `93824b6857307d22da974edaae54002760c3f6e8fc7c1e439f7307c9752aadee` |
| `criteria-method-map.md` | `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7` |
| `current-criteria-coverage.md` | `ccda149cf7add227a7a038311625595764331c57a43af6b23de973a88d1b6e0a` |
| `current-criteria-coverage.json` | `c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c` |
| `criteria.json` | `fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784` |
