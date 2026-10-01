# Current group-action method — attempt04

Status: focused correctness and coverage patch applied to the maintained method. The patch replays from the exact attempt03 source snapshots without fuzz. Fresh independent correctness, test, and architecture reviews are the next gate.

Attempt04 makes three narrow changes:

- `_finite` returns false when converting an unusually large integer for `math.isfinite` overflows; it no longer leaks `OverflowError` from input validation.
- A whitespace-only `load_case.case_id` is treated as missing. Derived row offsets, projections, transverse residuals, and pitches must remain finite or the input returns `pending`.
- The tests exercise four-member rejection through the sensitivity API for both 4/4 and 3/4 baseline/sensitivity comparisons. The maintained criteria method map now states the helper contract and its limits.

The focused suite reports 34 passed. The patch replay is exact and no-fuzz. All cases are synthetic or published-table method fixtures. Four-or-more-member results remain pending; no resistance, per-bolt force distribution, demand/capacity comparison, or criterion disposition is produced. All candidate criteria remain pending. No solver, Docker, or current-joint run was performed.

`base/` contains the attempt03 snapshots used for replay. [`attempt04.patch`](attempt04.patch), [`source-pins.json`](source-pins.json), [`validation.json`](validation.json), and [`offline-test-output.txt`](offline-test-output.txt) bind the source change and focused validation. This packet is method implementation evidence only, not candidate acceptance.
