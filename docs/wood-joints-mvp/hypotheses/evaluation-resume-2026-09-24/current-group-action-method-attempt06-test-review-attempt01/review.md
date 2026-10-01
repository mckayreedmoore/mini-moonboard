# Independent test-coverage review — current group-action method attempt06

Review date: 2026-09-28  
Scope: independent verification of the attempt06 pins and patch replay, focused tests, and positive / negative boundary coverage. Read-only review of maintained files; the only written artifacts are this report and its checksum in this new sibling directory.

## Verdict

**PASS — adequate test coverage for the attempt06 delta; no reproduced correctness defect or blocking test gap.**

The three new tests correspond to the documented behaviors: finite row-axis normalization with an overflowing raw norm, canonical JSON fail-closed behavior on excessive nesting, and sensitivity-path detection when Python scalar values compare equal but have distinct JSON types. Existing tests continue to cover equation known answers, malformed and unsupported geometry, binding and digest mismatch, and pending-only outputs.

## Pins and replay

The attempt06 source pins resolve:

- The packaged attempt05 base files hash to 95305398bf4fc9590f33fe877aafaf0544dce91503b0f09d84db590a938c8122 (module) and 91868751abfef9ceab746927904d7cbab9c0ba0881867980d89e2f2ab0b828e7 (tests), matching source-pins.json.
- The referenced attempt05 patch and terminal-hash manifest match e9f829bab63b6977e9ec071ab6e52e1fee82fa13113841f9b705dae46c7d5c36 and 2fa27a9decddd8b2118078c0ccca5dddfba87eef703765d22875c02e8050d248.
- The criteria method map matches 2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7.
- Attempt06 patch SHA-256 is e33f660e04a7dd0b1a03ebbd05fc204610d31f23192ce7e4c432fe3227323f1f, matching its source pin. git apply --check and replay in a temporary copy of the packaged attempt05 base both succeeded; replayed module and test bytes exactly match maintained hashes 65a8a5ea7fb4c76e84dc8f2ec475c17355fbbc29665f88f7f913432ca719daf9 and 93824b6857307d22da974edaae54002760c3f6e8fc7c1e439f7307c9752aadee.
- The attempt06 terminal manifest's listed hashes for README, patch, test output, source pins, and validation record were independently recomputed and match.

## Test execution and coverage

Command run independently:

    PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py

Result: **39 passed in 1.55s**.

The positive overflowing-axis case asserts calculated method-only status and the expected sqrt(32) inch uniform pitch while keeping capacity unset and disposition pending. It changes row, load, and grain vectors together, so the case exercises the direction-normalization path through a successful evaluation. Existing published-table fixtures check the equation's numeric answers.

The 600-level nested payload case checks both the public canonical digest (None) and evaluator fail-closed output (pending, no factor or capacity). An independent probe also confirmed that deeply nested sensitivity-contract content returns no canonical digest through the same helper.

The sensitivity regression confirms that integer 1 versus boolean true appears in the exact changed-path list, yields method-sensitivity-only output when declared, and returns pending when that path is omitted. This directly protects the equality corner case that motivated the change.

## Non-blocking coverage note

The nested-payload regression exercises recursion failure during strict-value validation before ordinary JSON encoding begins. It does not isolate the separate json.dumps RecursionError catch clause. Under the tested CPython runtime, the validator reaches its recursion limit first for the ordinary nested built-in JSON shapes used here; the public digest and evaluator still fail closed as intended. No behavioral defect was reproduced.

## Hash-bound reviewed inputs

- Attempt06 README: c89a90a34cfb37dad9f1291f48b8ead6c8432c55ef6a25c0dc510688888f1243
- Attempt06 patch: e33f660e04a7dd0b1a03ebbd05fc204610d31f23192ce7e4c432fe3227323f1f
- Attempt06 source pins: 2ebf7a3de52ab771e44ec7db81490001d228c2429c79a7e73feed6980f2a092d
- Attempt06 terminal hash manifest: 9b098dcf7bb23991c0fbf0e711e6a5eb651664c29cbd16a035617abedd01c3fa
- Attempt06 validation record: c964f1563da4d81daffa8dabf14816a09247b91882ca1a0d6d035fddd74e6208
- Attempt06 offline test output: 8426988acd080f590f1fc1eb1d7db825ac33e04c96044753f4f810e19a35842e
- Maintained module: 65a8a5ea7fb4c76e84dc8f2ec475c17355fbbc29665f88f7f913432ca719daf9
- Maintained focused tests: 93824b6857307d22da974edaae54002760c3f6e8fc7c1e439f7307c9752aadee
- Criteria method map: 2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7
