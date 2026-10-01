# Independent correctness review: attempt06

Review target: `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt06/`.

Result: one confirmed correctness issue in changed-path detection. Frozen artifact hashes and the patch replay are consistent. The focused maintained test file passes (39 tests). The review was read-only outside this new sibling directory; no solver, Docker, candidate disposition, or maintained-file change was made.

## Finding C1: signed-zero changes can be omitted from a sensitivity contract

At [nds_2024_group_action.py:550](../../../../../mini_moonboard/nds_2024_group_action.py:550), `_changed_payload_paths` treats same-typed leaves as equal using Python `==`. IEEE floating-point `-0.0 == 0.0`, while the canonical JSON encoder serializes them differently (`-0.0` and `0.0`) and produces different SHA-256 digests. The sensitivity API therefore can accept a contract that does not enumerate every changed payload path.

Reproduction used otherwise valid synthetic records with the test fixture's pitch changes plus `producer_extension: -0.0` in the baseline and `producer_extension: 0.0` in the sensitivity record. The canonical record digests differed. `_changed_payload_paths` omitted `producer_extension`; a contract listing only the two pitch paths returned `status="calculated_method_sensitivity_only"` with no reason codes. Expected behavior for an omitted serialized input path is `pending` with `sensitivity_changed_input_paths_do_not_match_contract`.

This does not change the Cg arithmetic for that unused extension field, and the result still has `capacity: null` and `criterion_disposition: "pending"`. It weakens the exact-change audit promised by the sensitivity contract. Compare finite scalar leaves according to the canonical JSON representation (or explicitly distinguish the signs of zero) and add a regression covering an omitted signed-zero path.

## Maintained API and method boundary

The public evaluator checks schema and identities, coordinator-provided source bindings, the complete canonical payload digest, one uniform straight row, load alignment, supported wood member inputs, and finite positive stiffness terms before returning a Cg. Unsupported geometry, mixed diameters, non-finite derived values, unsupported grain directions, four-or-more total members, and arithmetic/result-range failures return `pending`. The API reports no capacity and leaves the criterion disposition pending.

The bounded arithmetic matches the reviewed NDS Eq. 11.3-1 path: wood-to-wood dowel gamma `180000 * D^1.5`, the lesser-to-greater `EA` ratio, and the numerically stable equivalent `m = 1 / (u + sqrt(u*u - 1))` for `u - sqrt(u*u - 1)`. The D < 1/4 in special case and the D <= 1 in boundary are explicit. The new overflowing-axis regression is consistent with scaled vector normalization. The recursion regression exercises the updated catch around both strict-value validation and JSON encoding; the deep record returns `None` from hashing and `pending` from the evaluator. I found no separate formula, applicability, or fail-closed defect in those bounded paths. The official AWC 2024 errata corrects the §11.3.6.1 gamma term to use `D^1.5`, matching the implementation ([AWC 2024 NDS errata](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf); [AWC 2024 NDS resource](https://awc.org/resources/2024-nds/)).

## Hash and replay evidence

All declared source pins matched at report creation; the report also binds the terminal-hashes manifest and included frozen artifacts. The attempt06 patch applied to the included attempt05 base with `patch --fuzz=0`; both replayed files were byte-identical to the maintained files. Focused verification command: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py` → `39 passed in 1.24s`.

| Artifact | SHA-256 |
| --- | --- |
| `attempt06/README.md` | `c89a90a34cfb37dad9f1291f48b8ead6c8432c55ef6a25c0dc510688888f1243` |
| `attempt06/terminal-hashes.json` | `9b098dcf7bb23991c0fbf0e711e6a5eb651664c29cbd16a035617abedd01c3fa` |
| `attempt06/attempt06.patch` | `e33f660e04a7dd0b1a03ebbd05fc204610d31f23192ce7e4c432fe3227323f1f` |
| `attempt06/offline-test-output.txt` | `8426988acd080f590f1fc1eb1d7db825ac33e04c96044753f4f810e19a35842e` |
| `attempt06/source-pins.json` | `2ebf7a3de52ab771e44ec7db81490001d228c2429c79a7e73feed6980f2a092d` |
| `attempt06/validation.json` | `c964f1563da4d81daffa8dabf14816a09247b91882ca1a0d6d035fddd74e6208` |
| `attempt06/base/mini_moonboard/nds_2024_group_action.py` | `95305398bf4fc9590f33fe877aafaf0544dce91503b0f09d84db590a938c8122` |
| `attempt06/base/tests/test_nds_2024_group_action.py` | `91868751abfef9ceab746927904d7cbab9c0ba0881867980d89e2f2ab0b828e7` |
| `maintained/mini_moonboard/nds_2024_group_action.py` | `65a8a5ea7fb4c76e84dc8f2ec475c17355fbbc29665f88f7f913432ca719daf9` |
| `maintained/tests/test_nds_2024_group_action.py` | `93824b6857307d22da974edaae54002760c3f6e8fc7c1e439f7307c9752aadee` |
| `attempt06.patch pin` | `e33f660e04a7dd0b1a03ebbd05fc204610d31f23192ce7e4c432fe3227323f1f` |
| `criteria-method-map pin` | `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7` |
| `attempt05.patch pin` | `e9f829bab63b6977e9ec071ab6e52e1fee82fa13113841f9b705dae46c7d5c36` |
| `attempt05 terminal-hashes.json pin` | `2fa27a9decddd8b2118078c0ccca5dddfba87eef703765d22875c02e8050d248` |
