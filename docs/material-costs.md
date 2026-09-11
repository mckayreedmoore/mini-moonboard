# Materials cost ledger

The current [insert-candidate build draft](round-insert-build-plan.md) retains
the framing hardware priced here but replaces the panel screws with **56
E-Z LOK 801420-13 inserts and 56 Dottie FMDD14114 machine screws**. Both new
items remain unpriced and are excluded from every subtotal below. The SPAX
comparisons on this page belong to the preserved screw candidate, not the new
insert purchasing schedule.

**The currently priced remaining-material scenario is $260.41 USD, before the selected panel screws, missing hold hardware, any demonstrated plywood shortage, tax and shipping. Retain the already purchased Roseburg face plywood.** This is neither a complete additional-spend total nor the full value of installed materials, and it is not a construction release. Prices were checked on **September 11, 2026**. Of that portion, $17.80 is a displayed price for unavailable 8-foot boards; the remaining listed-available portion is $242.61. Neither figure is a local delivered quote.

Quantities follow the [round-service purchasing draft](round-service-build-plan.md), which retains the previous 18 lumber blanks. The [purchased-material record](purchased-materials.md) separately confirms owned Roseburg face plywood, Lowe’s item 12235 / model 119055. Its purchased quantity, receipt cost and verified usable yield are not recorded here. The current round candidate has 56 panel/kicker screws: twelve on each main face and four on each kicker. The 87- and 75-screw patterns remain historical comparison scenarios. Final hardware quantities must be reconciled with that candidate's released export; a cost entry does not qualify its strength, installation or delivered material.

## Priced materials

Prices and quantities are stored separately in the [dated ledger](material-costs.json). Prices below are per retail package; purchases round up to complete packages. No coupon, bulk-price assumption or arbitrary contingency is included.

| Material | Needed | Package and price | Purchase cost | Source and qualification |
| --- | ---: | ---: | ---: | --- |
| Douglas fir, #2 & better, KD-HT S4S, 2x6 × 8 ft | 2 boards | 1 board × $8.90 | $17.80 | [Fence and Lumber](https://fenceandlumber.com/products/2x6x12-doug-fir-2-better-stamped-s4s-kd-ht), select 8-foot variant; unavailable at retrieval |
| Same, 2x6 × 10 ft | 4 boards | 1 board × $12.25 | $49.00 | [Fence and Lumber](https://fenceandlumber.com/products/2x6x12-doug-fir-2-better-stamped-s4s-kd-ht), select 10-foot variant |
| Same, 2x6 × 12 ft | 2 boards | 1 board × $14.65 | $29.30 | [Fence and Lumber](https://fenceandlumber.com/products/2x6x12-doug-fir-2-better-stamped-s4s-kd-ht), select 12-foot variant |
| Douglas fir, #1 & better, kiln-dried, 2x10 × 12 ft | 1 board | 1 board × $35.05 | $35.05 | [Supply On Time, SKU 274943](https://supply-ontime.com/products/framing-stud-2-in-x-10-in-x-12-ft-1-btr-kiln-dried-douglas-fir-dimensional-lumber); advertised dimensional #1 & better despite “Stud” in product title; inspect actual grade stamp |
| Simpson ML24Z angle | 24 | 1 angle × $2.99 | $71.76 | [Fasteners Plus, ML24Z](https://www.fastenersplus.com/products/simpson-ml24z-2-x-4-medium-l-angle-zmax-finish) |
| Simpson SDS25112, 1/4 × 1-1/2 in | 144 | 25 screws × $8.49 | $50.94 | Six [SDS25112-R25 packs](https://www.fastenersplus.com/products/1-4-x-1-1-2-strong-tie-sds-heavy-duty-connector-screw-double-barrier-coating-pkg-25), 150 screws purchased, six spare |
| Conquest A307 Grade A plain bolt, 3/8-16 × 3-3/4 in | 8 | 1 bolt × $0.52 | $4.16 | [HBA-38X334](https://www.fastenersplus.com/products/3-8-16-x-3-3-4-conquest-a307-grade-a-hex-bolt-plain); current catalog price, not older cached $0.35 listing |
| Conquest Grade 2 plain hex nut, 3/8-16 | 8 | 1 nut × $0.06 | $0.48 | [HNG2-38](https://www.fastenersplus.com/products/3-8-16-grade-2-hex-nut-plain-finish); dimensional-family price, not a new connection approval |
| Conquest plain USS washer, 3/8 in | 16 | 1 washer × $0.12 | $1.92 | [ABW38](https://www.fastenersplus.com/products/3-8-flat-washer-plain-finish); **two washers per bolt**, one under the head and one under the nut |
| **Priced portion** | | | **$260.41** | Excludes the unresolved items below |

The eight modeled leg bolts are 95.25 mm under-head length in the [current connection schedule](../exports/round-bore-service-development/connections.csv). The round-service candidate retains those lengths and complete stacks, with nuts on the inside; verify the supplied product dimensions before ordering. Nut/washer fit, thread engagement, corrosion compatibility and connection resistance remain separate checks.

Fence and Lumber lists stores in [Oregon and Idaho](https://fenceandlumber.com/pages/contact-us); Supply On Time markets the cited product for the Los Angeles area. These are regional comparison prices, not confirmed Denver stock or freight. Retail catalog availability does not establish delivery eligibility. Obtain a local quote for the same dry species/grade and dimensions before treating the lumber subtotal as purchasable.

Most prices were read from each retailer's current product JSON endpoint, because rendered pages or search caches sometimes showed older amounts. The ledger records the exact endpoint, retrieval time, variant, availability and response hash. It preserves the observed figures; it does not promise that a future page fetch will return the same price.

## Panel screw scenarios

The model identifies **SPAX XFT08P-2000, #8 × 2 inches**. No verified mapping from that reference designation to a currently priced retail SKU has been established here. Its selected-product purchase cost therefore remains **unpriced**. A further September 11 check of the [manufacturer product page](https://spax.us/products/t-star-plus-flat-head-yellow-zinc), [designation report](https://www.drjcertification.org/report/download/1936) and [retail T-Star Plus partial-thread listing, SKU 4191020400506](https://www.homedepot.com/p/202040969) did not establish an explicit SKU cross-reference. Similar name, diameter and length alone have not been treated as that confirmation.

For a transparent package comparison only, Home Depot lists [SPAX 211-4191020400504, #8 × 2 in star-drive flat-head yellow-zinc screws, 161 per box](https://www.homedepot.com/p/308308848), at **$12.63 per box**. This is not a substituted product selection and is excluded from the $260.41 subtotal.

| Scenario | Installed panel/kicker screws | Comparison boxes | Comparison purchase cost | Unused screws |
| --- | ---: | ---: | ---: | ---: |
| Historical grooved baseline | 87 | 1 × 161 | $12.63 | 74 |
| Historical reduced comparison | 75 | 1 × 161 | $12.63 | 86 |
| Current round development pattern, including eight kicker screws | 56 | 1 × 161 | $12.63 | 105 |

Both reduced patterns save **$0 in this package scenario**. They reduce installed hardware, not the number of boxes purchased. The [screw-necessity review](panel-screw-necessity.md) governs why the candidates are being examined; package arithmetic does not establish that screws can be removed. None of these counts is a qualified final construction schedule. Recalculate against the actual approved SKU and package size once selected.

## Unpriced materials and measured inputs

| Item | Quantity basis | What is missing |
| --- | --- | --- |
| Any additional plywood after checking owned Roseburg stock | Additional sheet quantity unknown; the existing four-sheet allocation is a cutting concept, not four new purchases | Inventory purchased sheets and sound usable dimensions, thickness and stamp. The listing’s 47.436-inch width conflicts with nominal 48 inches; actual measurement determines whether fixed-grid squares and kicker offcuts fit. Do not assume either a shortage or zero further need. |
| Selected SPAX panel/kicker screws | 56 in the current round development pattern | Exact purchasable product mapping, package price and installation requirements |
| Hold T-nuts and retention screws | 142 positions: 132 main plus 10 kicker | Count owned Escape three-hole 3/8-16 T-nuts; obtain the actual retention-screw specification/count. Do not budget zero simply because ownership is uncertain. |
| Hold bolts and anti-rotation screws | Per actual installed hold and recess | Owned-kit inventory, individual bolt lengths, thread system, engagement and rear clearance |
| Consumables and any finishing materials | No adopted quantity | Cutting/drilling consumables, sanding/finish choices and actual owned stock |
| Freight, sales tax and local delivery | Destination and chosen retailer | Local availability, freight terms and actual tax; excluded from all subtotals |

No dollar allowances have been invented for these lines. The complete additional-spend total is **not yet known**. The full installed-material value is also unknown because historical purchase costs are not recorded. The sheet allocation deliberately does not assume that two exact 48-inch squares can be separated from an exact 96-inch sheet with nonzero saw kerf. Also measure usable lumber lengths: the two 12-foot center-principal allocations retain only about 13.8 mm beyond the draft's kerf/end-trim assumptions. An extra or longer board needed for defects or trimming would add cost.

An **optional replacement-stock comparison**, excluded from the base budget, is four sheets of APA PS 1 Structural I, 23/32 Performance Category, 48/24, square-edge Exposure 1 or Exterior plywood. No matching verified primary retail quote was found. This alternative does not establish that the owned Roseburg lot is Structural I, require replacing it, or justify repurchasing four sheets. Generic CDX, OSB and T&G listings are not equivalent quotes. Retain the existing face-panel purchase while verifying its actual material properties and geometry.

## Already owned, optional and separate budgets

The Roseburg face plywood, V5 MoonBoard LED kit, original controller, supply and included cables are already owned and excluded from repurchasing by default. Record their quantities and any missing or unusable component after inspection; no replacement quantity or cost is assumed. The owned Mini hold bundle is also separate sunk inventory, while missing hold hardware remains unresolved above. Historical plywood and kit spending is not included in the remaining-material subtotal and cannot be reconstructed without receipts.

Threaded inserts and machine screws remain a removable-panel development option and a possible later worn-hole repair, not installed hardware in this candidate. No speculative insert purchase is included. Temporary supports, tools and labor have no material allowance here; inventory the separate [tools and equipment list](round-service-build-plan.md#tools-and-equipment) first. Repair suitability, safe disassembly support and structural review are not purchased or established by this cost page.

## Reproduce the arithmetic

Run without network access or CAD generation:

```sh
python3 docs/check_material_costs.py
```

The check reads `material-costs.json`, rounds every required quantity up to full packages, verifies the two-washers-per-bolt count, recomputes both partial subtotals and compares the 87/75/56 screw scenarios. Prices and quantities can be reviewed independently. No order, retailer contact or purchase has been made.
