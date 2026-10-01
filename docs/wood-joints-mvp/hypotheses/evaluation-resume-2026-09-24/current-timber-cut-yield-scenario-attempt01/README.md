# Current timber cut-length scenarios, attempt 01

**Status:** source-pinned conditional arithmetic for the 24 proposed block
blanks on `led-clearance-2x6-runner-seated-blocks-v1`. This packet is not a
cut list, order quantity, lumber selection, price estimate, material
acceptance, or fit result.

The input schedule contributes the exact 24 `part_id` values and each row's
`proposed_stock_class`, `proposed_blank_cross_section_mm`,
`proposed_blank_stock_length_mm`, and `pattern_group`. The producer checks those
IDs against the reviewed attempt04 full-frame manifest and checks the four
proposed 4×6 section-rip IDs against the current grade-disposition record. It
also pins the current T08 material-status record, geometry revision source,
and selected-baseline authority. Source hashes are in
[`source-pins.json`](source-pins.json).

The 30 arithmetic results use the dated source packet's published length
inputs: 4×4 at 8, 10, 12, 16, and 20 ft; 4×6 at 8, 10, 12, and 16 ft; and two
separate 2×6 leads, one 8-ft kiln-dried listing and one 16-ft green listing.
These are scenario dimensions from catalog or supplier pages, not claims of
on-hand stock. The 2×6 descriptions stay separate and unselected. No prices or
purchase quantities are calculated.

Each scenario partitions blanks by stock class and exact proposed blank
cross-section. The two 4×6 post-rip sections are packed separately; this
packet does not combine them on a shared unsawn 4×6 stick before ripping. Each
blank carries its pattern group into the result. The packing routine uses
stable first-fit-decreasing length arithmetic; it does not claim an optimal
nesting plan.

The two explicit cut-loss cases charge 3.2 mm of kerf per proposed blank,
including the last blank in an arithmetic bin, and either 0 mm or 25.4 mm of
end trim once per bin. These are scenario inputs only. They do not identify a
saw, measured kerf, trim requirement, board tolerance, or actual cutting
sequence. An arithmetic bin is not a purchased stick.

All four proposed 4×6 rips remain flagged
`unresolved_after_cross_section_remanufacture`; no original grade transfers
and no post-rip grade is assigned. Defects, stock-length tolerance, section
cleanup, receiving loss, and cut feasibility are outside this arithmetic.

Run the focused test and packet verifier from the repository root:

```sh
python3 -m pytest -q tests/test_current_timber_cut_yield_scenario_attempt01.py
python3 scripts/build_current_timber_cut_yield_scenario_attempt01.py --check
```

The verifier fails on any pinned source drift or generated-report mismatch.
`--write` regenerates only this packet's
[`current-timber-cut-yield-scenarios.json`](current-timber-cut-yield-scenarios.json)
and [`verification.json`](verification.json) after all source pins pass.
The report keeps purchase, price, grade acceptance, physical fit, cutting
authorization, and candidate-release claims false.
