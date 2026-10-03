# CURRENT conditional hardware order

Fourteen structural families require **104 bolts, 104 matched nuts and 208 separate washers**. Counts below are axis needs. Bolt lengths use current `working_order_nominal_length_in`; member-specific body and thread conditions use `working_profile`. Routes are conditional planning only.

Bolt grade scenarios: SAE J429 Grade 5 for 1/4-, 3/8- and 1/2-inch bolts; Grade 8 for four 5/16-inch top-side bolts.

Family route and quantity fields come from [attempt03 working order](rawlocal/working-order/attempt03/working-order.json). Exact per-axis body-end and full-form thread intervals are in the [axis export](rawlocal/working-order/attempt03/working-order-axes.csv) and [hardware worksheet](hardware-engagement.md#working-order-export).

| Family / thread | Need | Current bolt route: supplier · SKU · nominal | Matched nut · two-washer route |
| --- | ---: | --- | --- |
| Ordinary candidate, 1/4-20 | 44 | K.L. Jack · `25C600HCS5Z` · 6 in | K.L. Jack `25CNFH5Z` · K.L. Jack `25NWUS` |
| Center post, 1/4-20 | 4 | K.L. Jack · `25C600HCS5Z` · 6 in | K.L. Jack `25CNFH5Z` · K.L. Jack `25NWUS` |
| Side, 1/4-20 | 12 | Lawson · `FA21103` · 8 in | K.L. Jack `25CNFH5Z` · K.L. Jack `25NWUS` |
| Top rail, 1/4-20 | 4 | Lawson · `FA21103` · 8 in | Bolt Depot `2569` · Lowe's Hillman `885522` (retailer `755754`) |
| Inner knee/header, 1/4-20 | 4 | Lawson · `FA21103` · 8 in | K.L. Jack `25CNFH5Z` · K.L. Jack `25NWUS` |
| Center principal/header, 1/4-20 | 4 | Lawson · `FA21103` · 8 in | K.L. Jack `25CNFH5Z` · K.L. Jack `25NWUS` |
| Top side, 5/16-18 | 4 | Bolt Depot · `28650` · 8 in | Bolt Depot `2583` · Bolt Depot `2995` |
| Outer post, 1/4-20 | 4 | K.L. Jack · `25C400HCS5Z` · 4 in | K.L. Jack `25CNFH5Z` · K.L. Jack `25NWUS` |
| Center principal, 1/4-20 | 4 | K.L. Jack · `25C550HCS5Z` · 5.5 in | K.L. Jack `25CNFH5Z` · K.L. Jack `25NWUS` |
| Center post/header, 1/4-20 | 4 | HiStrength · `104-049` · 7.5 in | K.L. Jack `25CNFH5Z` · K.L. Jack `25NWUS` |
| Continuous knee side, 1/4-20 | 4 | Ro-Brand · `HC5127` · 9.5 in | K.L. Jack `25CNFH5Z` · K.L. Jack `25NWUS` |
| Retained front, 3/8-16 | 4 | Bolt Depot · `367` · 4 in | Bolt Depot `2571` · Bolt Depot `15023` |
| Retained rear, 3/8-16 | 4 | Bolt Depot · `368` · 4.5 in | Bolt Depot `2571` · Bolt Depot `15023` |
| Retained upper leg, 1/2-13 | 4 | Bolt Depot · `407` · 8 in | Bolt Depot `2573` · Bolt Depot `15025` |

Each stack uses one nut and two separate washers, one under head and one under nut.

## Pooled and matched quantities

- K.L. Jack `25C600HCS5Z`: **48** six-inch bolts (44 ordinary + 4 center post); one 100-piece box, **52 spare**.
- Lawson `FA21103`: **24** eight-inch bolts (12 side + 4 top rail + 4 inner knee/header + 4 center principal/header); one 25-pack, **1 spare**.
- K.L. Jack `25C400HCS5Z`: **4** four-inch outer-post bolts; one 100-piece box, **96 spare**.
- Nuts: 84 K.L. Jack `25CNFH5Z` + 4 Bolt Depot `2569` + 4 `2583` + 8 `2571` + 4 `2573` = **104**.
- Washers: 168 K.L. Jack `25NWUS` + 8 Hillman `885522` / Lowe's `755754` (two listed four-packs) + 8 Bolt Depot `2995` + 16 `15023` + 8 `15025` = **208**.
- Purchased **66 Hillman `42605` panel/kicker screws** remain separate from structural stacks.

## Conditional profile and purchase limits

For four top-rail bolts, current working profile is `LB ≥ 145.375 mm`, minimum physical length `Lmin = 192.3504 mm`, and full-form male-thread coverage `182.8000–188.5404 mm`. This profile uses a 2.5 mm working rail-washer thickness; washer dimensions and conformity remain unverified. Older rail-profile values are historical. Use axis export for every other member-specific `LB` and thread interval. Nominal bolt length or a catalog thread-length field does not establish delivered profile; request/confirm each bolt against its working profile and matched nut.

The 12 nominal length changes are complete: four center-post bolts at 6 in, four center principal/header bolts at 8 in, and four inner knee/header bolts at 8 in. The completed [hardware-length fit](hardware-length-fit.md) cleared all 48,192 saved-source query/obstacle pairs; separate [top-washer fit](top-washer-fit.md) cleared 37,352 pairs. Delivered bolt profiles and actual tool operation remain conditional.

Current prices and delivered-part conformity are null. Other pack quantities are unrecorded. No current total is available. Historical `$189.58` recipe is not this order total. No delivered part is physically selected or inspected, and this table establishes no climbing rating.
