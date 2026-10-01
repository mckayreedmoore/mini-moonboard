# Bounded stock-cut arithmetic

`nesting.py` groups proposed blanks by their original stock section (`4x4`,
`4x6`, or `2x6`) and lays their lengths along one-dimensional nominal boards.
Lengths are in millimetres. The helper accepts stock-length options for each
source section, crosscut kerf, and independent start- and end-trim allowances.
An end-trim allowance is the total length charged at that end; callers may
include the trim cut's saw loss in that declared value. The helper adds one
separate crosscut-kerf reserve after each placed blank, including the final
blank before any positive tail remnant.

Each placement records the blank ID, source section and optional prepared
width/height after a later rip, board ID and length, start and end coordinates,
blank length, and its trailing kerf reserve. Each board records both end trims,
total blank and kerf lengths, the remainder interval and length, and the source
section retained by that remainder. Length balance is:

```text
stock length = start trim + end trim + blank lengths + separation kerfs + remainder
```

The optional `rip_to_section` value is a two-number prepared width/height in
millimetres for a later operation on that individual blank. Length nesting
treats the blank as its original source section, so a proposed rip from `4x6`
does not split it into a different stock group. The helper does not apply the
rip, calculate rip waste, or reclassify a board remnant. A `4x6` remnant
remains `4x6` even when one of its placed blanks has later prepared dimensions.
Conditional grade remains unresolved.

Packing is the deterministic first-fit-decreasing heuristic: blanks are
ordered by decreasing length and then ID, existing boards are tried in their
creation order, and a new board uses the shortest declared nominal length that
fits. It is not an optimum search, yield guarantee, or purchase-count
recommendation. An item that fits no declared stock length is listed in
`infeasible_item_ids`; all other IDs are placed once. Empty input returns no
boards and zero totals, including a zero length-yield fraction.

Illustrative parameter scenarios may use nominal stock lengths of 8, 10, 12,
or 16 ft (2438.4, 3048, 3657.6, or 4876.8 mm), a 3.2 mm separation kerf, and
10 mm or 20 mm at each end for the separately declared trim allowances. Zero
kerf or trim is also supported for sensitivity comparisons. These are
optimistic arithmetic cases with zero defect loss. They do not account for
physical defects, rejection rates, receiving or section cleanup, or price, and
they make no claim about actual stock, cuts, grade, fabrication, or material
availability. The output is not a stock order, release, or added physical-test
prerequisite.
