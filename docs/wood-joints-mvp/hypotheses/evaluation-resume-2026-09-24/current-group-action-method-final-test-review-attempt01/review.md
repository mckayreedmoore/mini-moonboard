# Final test review: NDS-2024 group-action factor

Review date: 2026-09-27

## Finding

There is one substantial test-coverage gap in the four-or-more-member boundary: the suite tests that boundary only through `evaluate_group_action_factor`. It does not assert the same fail-closed behavior through the second public result-producing API, `evaluate_group_factor_sensitivity`, which returns baseline and sensitivity Cg values when successful.

A concrete missing regression case is a valid baseline with one main and two side members (three total) and a valid sensitivity case with one main and three side members (four total), with matching independent source bindings, canonical payload digests, and a reviewed sensitivity contract. The comparator must return `pending` and expose no numeric baseline or sensitivity Cg. A second case with both scenarios at four total members would cover the same path from both sides. The existing positive sensitivity test uses three total members in both scenarios; the direct boundary parametrization uses three-fastener rows and four/five total members, but calls only the single-record evaluator.

The current implementation does block both missing cases: `evaluate_group_factor_sensitivity` calls `evaluate_group_action_factor` for each input and returns pending unless both statuses are `calculated_method_only` ([module](../../../../../mini_moonboard/nds_2024_group_action.py#L630)). The single-record evaluator rejects four or more total members before area calculation or the Cg equation ([module](../../../../../mini_moonboard/nds_2024_group_action.py#L398)). An ad hoc read-only exercise of the two sensitivity cases above returned `pending`, with no numeric `baseline_cg` or `sensitivity_cg`. That demonstrates current behavior, but it does not make the alternate-path guarantee part of pytest regression coverage.

## Coverage that is present

The suite has positive source-table checks for rows of two, three, and four fasteners, plus the sub-quarter-inch exception, equal-EA case, the perpendicular-to-grain area path, and a three-total-member double-shear example. It rejects non-straight and nonuniform rows, mixed and out-of-scope diameters, unsupported member material, unsuitable grain orientation, malformed geometry, and inconsistent source evidence. The four-or-more-member test parametrizes three and four side members, so it exercises four and five total members and asserts pending status, null Cg and capacity, and pending criterion disposition. The sensitivity tests verify that a supported sensitivity case can calculate and that missing, altered, or mismatched contracts fail closed.

No current four-or-more-member bypass was found in the maintained module. There is a minor untested branch for a non-dowel fastener type (`unsupported_fastener_type`); the test fixtures cover accepted dowels, but the negative parameter set does not mutate a fastener's `type`. This is not the substantial gap reported above.

## Verification and hash binding

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py
```

Result: `29 passed in 1.36s`.

SHA-256 review subjects:

- `mini_moonboard/nds_2024_group_action.py`: `8dac7e4b749d7b9253b5a4801c169d759e486030aac719b8c55dae80d9606488`
- `tests/test_nds_2024_group_action.py`: `5a63579be46d795068e44f77244366d6d2bc411d574eb52e5fe9af9ccf9d0365`

This review covered only the maintained module and its focused tests. The ad hoc sensitivity exercises were read-only and were not added as repository tests.
