# Current WJ24 cost and quantity coverage — 2026-09-27

**Status:** source-bound coverage bridge for
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. This reconciles current quantities
with dated price observations already recorded in the repository. It is not a
cost estimate, purchase BOM, selected-product schedule, or release. No new
vendor lookup was made.

## Current quantity basis

| Scope | Current quantity basis | Cost status |
| --- | --- | --- |
| Candidate structural stacks | 92 axes: 92 bolts, 92 nuts, and 184 washer roles. | No SKU or matched delivered stack is selected; the current coverage reports 0 of 92 axes fit-qualified. Dated listing comparisons cover only some families and do not establish WJ24 suitability. |
| Retained starting frame | 12 separate stacks: 12 bolts, 12 nuts, and 24 washer roles. | Catalog references and dated comparison prices exist, but stock ownership, delivered identity, fit, and current WJ24 mechanics are unverified. Keep these separate from the 92 candidate axes. |
| Structural stack total | 104 stacks: 104 bolts, 104 nuts, and 208 washer roles. | Quantity reconciliation only; not a selected BOM or cost total. |
| Panel/kicker screws | 66 separate purchased Hillman 42605 axes. | Preserve the purchase policy. The receipt amount is not recorded; do not infer cost or properties from another screw product. |
| Current connector blocks | 24 proposed blanks: 18 nominal 4×4, 4 proposed 4×6 section-ripped blanks, and 2 nominal 2×6. Proposed length sums are 2,140.2 mm, 547.4 mm, and 552.6 mm, respectively. | No matching candidate stock price or quote. These are proposed blank dimensions, not released cut quantities or whole-board yield. |

The current timber source/yield schedule also carries 20 preserved frame-source
records (four nominal 4×6 and sixteen nominal 2×6). Sixteen frame hosts are
rebuilt in the reviewed geometry, so those source blank lengths do not define a
current purchase cut list. They are not added to the 24 connector-block blank
quantities above. The schedule has no nesting plan, kerf/end-trim allowance,
defect allowance, stock count, receiving loss, or usable-yield result.

The four proposed 4×6 block rips are nonstandard sections. The current grade
disposition requires a traceable post-rip inspection/regrade record before
assigning any grade-specific values; no supplier, stock, inspection, or grade
has been selected. No original grade or design value transfers to a ripped
block.

## Dated price coverage already on file

The following are bounded observations from the pinned current schedule and
coverage notes. They are not summed here; each remains a comparison or
conditional sourcing scenario.

| Existing observation | Dated source record | Applicability limit |
| --- | --- | --- |
| 48 nominal 6-inch candidate-axis comparisons at $0.39 each; 16 nominal 8-inch comparisons at $0.90 each. | Current hardware schedule reproduces the Bolt Depot/WJ-03 observations dated 2026-09-23. | The cited bolt examples are zinc-plated low-carbon Grade 2/A307A price references, not selected Grade 5 WJ24 products. Price and nominal length do not establish fit or acceptance. |
| 92 candidate nut comparisons at $0.07 each; 184 washer comparisons at $0.09 each. | Current hardware schedule records these Bolt Depot observations dated 2026-09-24. | Comparison listings only; no universal nut/washer product is selected or fit-qualified across current axes. |
| One 25-piece Lawson bolt pack plus 100-piece nut and washer boxes for a conditional 20-axis 8-inch option; nut and washer boxes displayed $4.71 and $3.47. | Current hardware coverage records the page observations dated 2026-09-25. | The Lawson bolt price was not found. The package scenario combines 16 side and 4 knee inner-header axes; it is not a chosen route or total. |
| Other family-specific listing/package observations, including a 100-piece 5.5-inch K.L. Jack box and eight displayed HiStrength 7.5-inch units at $2.54 each ($20.32 at that displayed rate). | Current hardware coverage records these observations dated 2026-09-25. | Conditional alternatives only. Availability, complete package rules, matched nuts/washers, functional engagement, and fit remain open. |
| Retained-frame catalog comparison amount of $31.12. | Current hardware schedule's dated price-source coverage. | Not evidence of physical ownership, current price, delivered fit, or WJ24 acceptance. |
| Local lumber listing observations for seller-labeled Grade A or WRC stock. | Current timber price lookup attempt02, accessed 2026-09-27. | None identifies the candidate's DF-L No. 2 scenario, suitable treatment and dimensions, usable quantity, or a candidate quote. Do not include these offers in a candidate material total. |

The 66 Hillman screws have no recorded receipt amount. No usable candidate
lumber price or local inventory was found for the current source schedule. The
separate current frame dead-load scenario reports 224.4207767 kg across its
778-row modeled inventory and a separate 25 kg accessory allowance; these are
analysis mass scenarios, not received-product or purchase weights.

## Reconciliation with the earlier cost screen

The preserved [2026-09-24 preliminary development cost screen][old-cost] is
bound to a predecessor 104-candidate-axis / 28-blank layout. Its $71.72
by-each subtotal prices only part of that predecessor's proposed bolts and
its nuts and washers; its $63.96 bag/loose illustration uses separate package
assumptions. Neither amount is carried forward or treated as a current WJ24
total. Preserve that screen as historical evidence.

This bridge does not calculate a current total, lower bound, or cost range. It
does not add together alternatives, price unavailable lines, infer a quantity
of whole boards, or count the 66 purchased Hillman screws as new hardware. Tax,
freight, live availability, stock quantity, delivered identity, and receiving
measurements remain absent. Physical receiving cells stay blank.

## Frozen source references

These hashes identify the source files used for the quantity and cost-status
reconciliation. The sources are read-only inputs to this bridge.

| Source | SHA-256 |
| --- | --- |
| [Current hardware schedule][hardware-schedule] | `47a1de21705570cfd23fb493c640d8983945ee410623e15484cf53ed7596bffa` |
| [Current hardware coverage][hardware-coverage] | `6bda5d032d52c8da38e069548153dbfe93c6bdfeea6f8ded1ba4f650cf75dd8c` |
| [Current hardware coverage JSON][hardware-coverage-json] | `011dcf33c8a99d5072623db06388ffc0e409c8824be15015e68b454c31e7305d` |
| [Current timber source/yield README][yield-readme] | `fe8d8ef513b03aedaee6acdc81aa53891c2dbfde2f2d0d90a993d9402423e442` |
| [Current timber source/yield JSON][yield-json] | `2c710708d5e775d742375e28fadd323ecfe7f8e81c186c6028704c903a65266c` |
| [Current timber grade disposition][grade] | `7266a00f72dbe46ac6917cfc7ee3588f85ca5d42d9daf4a916ff6fa529a873b0` |
| [Current timber price lookup attempt02][timber-price] | `9c88c0c784d1389e5b3caec31c207b70e87a7588bca6dd70c3e0812a0e7b2a9a` |
| [Current frame dead-load scenario][dead-load] | `770c3c7325a7fd9df3850a527eb35f7386590e95fac4d589204cef9e2ccf7fab` |
| [Preserved predecessor cost screen][old-cost] | `f862191ad53e180f4876412217f2c339c57e6e087437c5762db73a124b69c661` |

[hardware-schedule]: current-hardware-schedule.md
[hardware-coverage]: current-hardware-coverage.md
[hardware-coverage-json]: current-hardware-coverage.json
[yield-readme]: hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/README.md
[yield-json]: hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json
[grade]: hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/README.md
[timber-price]: hypotheses/evaluation-resume-2026-09-24/current-timber-price-research-attempt02/README.md
[dead-load]: hypotheses/evaluation-resume-2026-09-24/current-frame-dead-load-scenarios-attempt01/README.md
[old-cost]: wj24-development-costs.md
