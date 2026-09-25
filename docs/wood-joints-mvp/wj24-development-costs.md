# WJ24 preliminary development cost screen

**Prepared:** 2026-09-24. **Status:** quantity-based development estimate;
not a purchase list, selected-SKU bill of materials, cutting release, or build
release.

This screen prices comparison items against the source-bound WJ24 quantities.
The [Bolt Depot product pages](https://boltdepot.com/) were read on
2026-09-24; the four ordinary-item prices match the 2026-09-23 snapshot in
the repository's [WJ-03 procurement note](wj03-hardware-procurement.md).
Posted prices do not confirm stock, shipping, tax, or a tailored quote. A
priced comparison item does not establish fit, grade, resistance, capacity,
or acceptance for WJ24.

## Quantity basis

The [WJ24 hardware inventory](hypotheses/wj24-hardware-inventory/README.md)
and its [machine-readable inventory](hypotheses/wj24-hardware-inventory/inventory.json)
screen 104 proposed bolts, 104 nuts, 216 physical washer equivalents, and 28
connector blanks. They are provisional quantities for one modeled layout.

| New development item | Quantity | Basis |
| --- | ---: | --- |
| Proposed bolts | 104 | One per candidate bore axis: 60 model axes at 152.4 mm nominal length / 127 mm grip; 24 at 203.2 / 177.8 mm; 4 at 304.8 / 270 mm; 16 center axes with no nominal length assigned. |
| Proposed nuts | 104 | One per proposed bolt axis. |
| Proposed washers | 216 | 100 ordinary two-washer stacks = 200; four backer stacks with one bottom and three top washer equivalents = 16. |
| Connector blanks | 28 | Modeled timber blank count; stock yield scenario below. |

The WJ24 inventory separately records 12 retained starting frame-bolt
assemblies and 66 fixed Hillman panel/kicker screw axes. Neither is included
in the new-hardware subtotal. The 144 former SDS axes were removed from this
candidate inventory; they are not costed as WJ24 items.

## Priced comparison items

The price inputs below come from the [WJ-03 through-bolt procurement note](wj03-hardware-procurement.md),
which records a 2026-09-23 price snapshot. Its 6-inch and 8-inch bolts are
low-carbon zinc-plated products identified by the supplier as Grade 2 or
A307A. They are used here only to expose a price scale for matching nominal
model-length groups. They are not the WJ24-selected product or evidence of a
WJ24 material specification.

| WJ24 quantity line | Price comparison and direct source | Required | Each | Bag of 100 | Bulk of 1,000 | Extension at each price |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 6-in nominal bolt group | [Bolt Depot #10, 1/4-20 × 6-in zinc-plated hex bolt](https://boltdepot.com/Product-Details?product=10) | 60 | $0.39 | $26.12 | $209.00 | $23.40 |
| 8-in nominal bolt group | [Bolt Depot #14, 1/4-20 × 8-in zinc-plated hex bolt](https://boltdepot.com/Product-Details?product=14) | 24 | $0.90 | $59.92 | $479.00 | $21.60 |
| Nuts | [Bolt Depot #2569, 1/4-20 zinc-plated Grade 5 hex nut](https://boltdepot.com/Product-Details?product=2569) | 104 | $0.07 | $4.86 | $38.80 | $7.28 |
| Washers | [Bolt Depot #15021, 1/4-in zinc-plated Grade 5 USS washer](https://boltdepot.com/Product-Details?product=15021) | 216 | $0.09 | $6.19 | $54.40 | $19.44 |
| 12-in modeled backer bolts | No accepted or receiving-qualified WJ24 SKU; see price lead below | 4 | — | — | — | — |
| Center-node bolts with unassigned inventory length | No selected or priced SKU; tentative length screen below | 16 | — | — | — | — |

The per-piece extensions for the four priced comparison rows total **$71.72**.
That subtotal covers 84 of the 104 proposed bolts and all proposed nuts and
washers; it excludes 20 bolt costs and all timber costs. It is not a complete
WJ24 cost or a lower bound on the eventual accepted hardware.

The listed bag prices support a separate purchase-quantity illustration. If
the vendor allows bag quantities to be combined with loose units at the
listed each prices, the priced portion would be:

| Purchase illustration | Arithmetic | Amount | Surplus |
| --- | --- | ---: | ---: |
| 6-in bolts | 60 × $0.39 | $23.40 | 0 |
| 8-in bolts | 24 × $0.90 | $21.60 | 0 |
| Nuts | One 100-count lot at $4.86 + 4 × $0.07 | $5.14 | 0 |
| Washers | Two 100-count lots at $6.19 + 16 × $0.09 | $13.82 | 0 |
| **Priced portion under this illustration** |  | **$63.96** |  |

This illustration assumes the listed bag prices can be combined with loose
units at the listed each prices, and that the products remain available on
those terms. It is not a purchase quote. Freight and tax are excluded. If
only loose-item prices apply, use the $71.72 extension above.

If only whole bags are available for nuts and washers, two nut bags would
cost $9.72 for 200 pieces (96 extra) and three washer bags would cost $18.57
for 300 pieces (84 extra). The 6-in and 8-in bolt each prices remain cheaper
for the modeled quantities than their respective bags of 100.

### Unpriced bolt lines

The 4 backer axes have 304.8 mm model envelopes and 270 mm modeled wood grip.
The [Bolt Depot #5238 12-in stainless 18-8 example](https://boltdepot.com/Product-Details?product=5238)
lists $7.04 each, a $146.63 bag of 25, and $1,290.00 bulk for 250 on
2026-09-24. These figures are price context only and are omitted from the
WJ24 subtotal: the [WJ-05 backer screen](wj05-center-backer-transfer.md)
records the delivered thread-transition and full nut-engagement condition as
unverified, and does not select that stainless product for WJ24.

The 16 center-node axes have grip screens of 100.915644, 127, or 167 mm, but
the WJ24 inventory assigns no nominal bolt length or SKU. The separate
[bolt-length screen](wj24-bolt-length-screen.md) tentatively identifies 4 ×
4.75-in, 8 × 5.75-in, and 4 × 7.5-in nominal candidates; it does not select a
bolt family or supplier SKU, and 7.5-in availability remains unverified. No
price is assigned until an exact orderable product is identified.

The WJ24 inventory also says the 6-in K.L. Jack `25C600HCS5Z` dimensional
basis applies to some WJ04/WJ06 model groups, not as a universal WJ24
selection, and the 8-in Forces `F086013` is only an unselected lead for some
WJ06-derived groups. Neither is used to price all WJ24 axes. See the
[ordinary hardware basis](ordinary-hardware-basis.md) and
[current hardware schedule audit](hypotheses/current-hardware-schedule-audit.md).

## Timber blank scenario

The current [WJ24 stock-yield screen](wj24-timber-stock-yield.md) groups the
28 modeled blanks as follows. It provides a planning scenario for whole stock
lengths, not a supplier selection or price.

| Modeled stock group | Blank quantity and dimensions | Planning stock-length scenario | Price status |
| --- | --- | --- | --- |
| Full-section 4×4 | 16 × 88.9 × 88.9 × 119.7 mm; 2 × 88.9 × 88.9 × 128.9 mm; 2 × 88.9 × 88.9 × 156.596 mm angled; 2 × 88.9 × 88.9 × 238.9 mm; 2 × 185.2 × 88.9 × 88.9 mm links. **24 blanks total.** | One nominal 12-ft stick under the documented kerf and trim scenario. | Unknown; no stock SKU, grade evidence, local availability, or price selected. |
| Nominal 2×4 | 2 × 383.2 mm blanks | One nominal 8-ft stick in the planning scenario. | Unknown. |
| Nominal 4×6 | 2 × 269.95 mm blanks | One nominal 8-ft stick in the planning scenario. | Unknown. |

The 4×4 base scenario uses one 3.175 mm kerf per blank (24 cuts) and 25.4 mm
end trim; the modeled blanks total 3,334.392 mm, consume 3,435.992 mm, and
leave 221.608 mm in a nominal 12-ft stick before defect, grade, dimensional,
moisture, and receiving losses. The 2×4 and 4×6 scenarios use the same
one-kerf-per-blank rule. These planning quantities do not establish delivered
stock. The stock screen leaves all prices null, so this report assigns **no
cost** to any of the 28 blanks. Full-frame member lumber is outside this
connector-only quantity screen.

## Scope and open costs

No complete WJ24 total can be stated while 20 bolt prices, all 28 timber
blank costs, exact supplier SKUs, and received-product fit remain unresolved.
The comparison items also do not establish the eventual bolt grade, thread
transition, nut engagement, washer dimensions or bearing, or vendor stock.
There are no accepted WJ24 hardware selections or unit prices in the source
inventory.

This estimate excludes the 12 retained frame-bolt assemblies, 66 retained
Hillman panel/kicker screws, removed SDS hardware, the main frame stock,
cutting and drilling labor, finishing, tools and consumables, shipping, and
tax. Retained hardware is not claimed to have been inspected. WJ24 hardware
selection, physical stock, dimensional fit, assembly sequence, complete
mechanics, cutting, drilling, and fabrication release gates remain open.
