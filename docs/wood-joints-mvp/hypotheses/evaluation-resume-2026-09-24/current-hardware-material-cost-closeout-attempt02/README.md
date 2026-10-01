# T08 current hardware and material cost closeout, attempt 02

**Observed:** 2026-09-28. **Disposition:** partial, fail-closed public listing
comparison. This attempt adds current listing evidence and reconciles the
counted axes. It does not select a bolt, nut, washer, spacer, board, plywood
sheet, or supplier offer for the joint candidate.

The source pin set contains 30 local inputs, including the T08 scope, attempt01
axis and cost registers, the reviewed T07/T08 option crosswalk, the current
material/yield and grade records, the attempt05 plywood identity correction,
and the current full-frame manifest. Its queue pin remains
`e624e043f15b3fd361dc99b05be6a37ff625b6bcb0e1da2cccaf3cb557a0a35c`. The
machine-readable IDs and exact counts are in
[axis-count-reconciliation.json](axis-count-reconciliation.json); direct
listing captures and extraction outcomes are in
[public-price-observations.json](public-price-observations.json). The current
source-only material result is in
[material-stock-and-panel-status.json](material-stock-and-panel-status.json).

## Reconciled scopes

| Scope | Count | Interpretation |
| --- | ---: | --- |
| Candidate bolts | 92 axes, 92 nut roles, 184 separate washer roles | Alternatives remain catalog leads; no selected or delivered stack. |
| Retained starting frame bolts | 12 axes, 12 nut roles, 24 separate washer roles | Preserved-baseline catalog references; current candidate fit/mechanics recheck remains open. |
| Hillman 42605 panel/kicker screws | 66 axes: 58 unchanged, 8 previously owner-moved | One owner-purchased screw per axis under the existing Hillman policy. The reported purchased status does not supply the receipt or amount. |
| Former SDS25112 references | 144 axes | Removed from this bolted candidate. They are not new purchases, candidate options, or a source of cost/property transfer to the 66 Hillman screws. |

The T08 register's 92 candidate rows reconcile to nine catalog rows. Alternative
lead coverage can repeat across those rows, so its reference count is not an
SKU order quantity. The 12 retained frame-bolt axes are priced below only as a
current public comparator; the $31.12 reference calculation is excluded from
candidate cost. The Hillman replacement listing is likewise separate from the
owner's historical purchase and receipt. No SDS25112 line was repriced or
added.

## Public fastener prices

Eight candidate bolt-lead pages displayed numeric prices. Their pages show
different nominal lengths, units, volume tiers, and package fields. The rows
below preserve the exact displayed bases; normalized per-bolt values are
arithmetic from each public pack display, not quotes for the 92 axes.

| Source and exact part | Displayed pack / price | Unit conversion, where pack price was shown | Source and extraction |
| --- | --- | --- | --- |
| HiStrength `104-035` / `25C400HCS5P`, 1/4-20 × 4 in | Each: $0.98 base, $0.59 at 25, $0.39 at 50; Package Qty field 50 | Each prices displayed directly | [Product page](https://histrength.com/104-035), opened 2026-09-28; numeric tiers and page availability text visible. |
| Tanner `25C400HCS5Z`, 1/4-20 × 4 in | $12.85 per 50-piece box (0–9 boxes); $11.57 per 50-piece box (10+) | `$12.85 / 50 = $0.257`; `$11.57 / 50 = $0.2314` per bolt | [Product page](https://www.tannerbolt.com/25c400hcs5z-1-4-20-x-4-grade-5-hex-head-cap-screws-coarse-thread-steel-zinc-plated), opened 2026-09-28; `IN STOCK` page display, not local inventory. |
| HiStrength `104-042` / `25C550HCS5P`, 1/4-20 × 5-1/2 in | Each: $1.25 base, $0.75 at 25, $0.50 at 50; Package Qty field 50 | Each prices displayed directly | [Product page](https://histrength.com/104-042), opened 2026-09-28; numeric tiers and page availability text visible. |
| Tanner `25C550HCS5Z`, 1/4-20 × 5-1/2 in | $32.05 per 50-piece box (0–9 boxes); $28.85 per 50-piece box (10+) | `$32.05 / 50 = $0.641`; `$28.85 / 50 = $0.577` per bolt | [Product page](https://www.tannerbolt.com/25c550hcs5z-1-4-20-x-5-1-2-grade-5-hex-head-cap-screws-coarse-thread-steel-zinc-plated), opened 2026-09-28; `Available to Order` page display, not a stock count. |
| HiStrength `104-044` / `25C600HCS5P`, 1/4-20 × 6 in | Each: $1.23 base, $0.88 at 25, $0.60 at 50; Package Qty field 50 | Each prices displayed directly | [Product page](https://histrength.com/104-044), opened 2026-09-28; numeric tiers and page availability text visible. |
| HiStrength `104-049` / `25C750HCS5P`, 1/4-20 × 7-1/2 in | $2.54 each; Package Qty field 1 | Each price displayed directly | [Product page](https://histrength.com/104-049), opened 2026-09-28; numeric price and page availability text visible. |
| Fastener SuperStore `412254` / Kanebridge `14120CH5O`, 1/4-20 × 7-1/2 in | $382.42, $359.93, or $339.93 per 275-piece carton at 1–2, 3–4, or 5+ cartons | `$382.42 / 275 = $1.390618`; `$359.93 / 275 = $1.308836`; `$339.93 / 275 = $1.236109` per bolt | [Product page](https://www.fastenersuperstore.com/products/412254/hex-cap-screws), opened 2026-09-28; add-to-cart displayed, no stock quantity or delivery date. One carton for eight referenced axes would leave 267 pieces; this surplus is not priced into a candidate scenario. |
| HiStrength `104-051` / `25C800HCS5P`, 1/4-20 × 8 in | $1.36 each; Package Qty field 1 | Each price displayed directly | [Product page](https://histrength.com/104-051), opened 2026-09-28; numeric price and page availability text visible. |

Across those eight pages, the lowest and highest normalized displayed cells are
$0.2314 per bolt and $2.54 per bolt. This is an **observed page-display
envelope only**, across unlike length and quantity tiers. It is not a useful
candidate price bound: it excludes the unpriced/unqualified 9-1/4-in-class
lead, the shared accessories, pack-order rules for several listings, and any
transaction costs. It is not multiplied by 92 and must not be presented as a
candidate total or range.

The other candidate bolt/accessory lead outcomes are explicit gaps:

- K.L. Jack `25C400HCS5Z`, `25C600HCS5Z`, `25CNFH5Z` nut, and `25NWUS`
  washer pages timed out. Prior captures conflict or are stale and are not
  current numeric prices.
- Würth Canada `072.14.6` timed out; its earlier `25.49` display had unclear
  currency and unit, and inventory/pricing was login-gated. No login was used.
- Lawson `FA21103` showed a login/register overlay and a “Check Availability”
  flow, without a public price. No account or login was used.
- Ro-Brand `HC5127` was inaccessible. The old “Call for Pricing” note and
  Grade 5/partial-thread interpretation are not reliable source support for
  the 9-1/4-in-class axes.
- McMaster `91201A029` showed “000000 per pack of 25,” a zero placeholder, not
  a numeric price.

The current shared candidate nut, washer, and conditional spacer prices
therefore remain unknown. Axis-level bolt length is modeled geometry, not
purchase length or delivered shank. None of these pages establishes matched
active-thread engagement, full-thread interval, installed stack fit, owner
stock, receipt, physical identity, or product-specific weight.

## Separate reference arithmetic

The 12 preserved selected-baseline frame-bolt references were rechecked on
Bolt Depot pages. Current displayed by-each prices reproduce:

```text
4*4.03 + 4*0.30 + 8*0.36 + 4*0.81 + 4*0.94 + 8*0.11 + 16*0.19 = $31.12
```

This is not a wood-joints candidate selection, a delivered/purchased total, or
a fit pass. The per-item pack displays and source URLs are in the machine
record. The current candidate still needs all 12 retained stacks rechecked.

The separate Hillman reference is Lowe's item 755741, model 42605, UPC
00038902075949: `$7.98 / 50 screws`. `ceil(66 / 50) * $7.98 = $15.96` is only
a hypothetical full replacement listing calculation. The 66 screws are
already owner-purchased under the repository policy; their receipt amount is
unknown in the available source records, and the comparator is not a new
purchase line. The 144 former SDS25112 references remain excluded from this
candidate and are not transferred to the Hillman policy.

## Lumber and plywood are not bounded

The source schedule has 20 preserved historical frame-source records (four
nominal 4×6 and sixteen nominal 2×6); the current composition rebuilds 16
hosts. The current block pattern proposes 24 blanks: 18 4×4, four 4×6 blanks
to be ripped, and two 2×6. Their recorded proposed blank lengths are 2,140.2
mm, 547.4 mm, and 552.6 mm by those classes. These are linear-length
arithmetic only, not purchasable board counts or a yield plan. No nesting,
defect/trim loss, receiving condition, or delivered board assignment is
observed. Four 4×6 blanks still have no post-rip grade/inspection disposition;
original grade/design values do not transfer across the rips.

On 2026-09-28, public Front Range Lumber size pages showed no item prices.
Lowe's lumber pages required a ZIP/city to display pricing and availability;
Home Depot asked for a store. No ZIP/store was selected. The public numbers
available in the prior local screen for Denver Fence Supply (4×4 “Grade A,”
4×6 WRC, and 2×6 WRC) are not the conditional DF-L No. 2 stock basis and are
excluded. Therefore, no compatible current unit price for the lumber schedule
is established. A stock cost formula would require accepted species/grade,
section, treatment and season/condition SKUs multiplied by a finalized
cut/yield purchase plan; neither side is supplied.

There are six modeled plywood panels. Lowe's item `12235`, model `119055`,
lists 23/32-in × 4-ft × 8-ft Douglas Fir plywood, but its public page did not
show a price without location selection. Roseburg's current manufacturer
card calls a descriptor-matching option “AC Sanded,” 23/32-in and five-ply;
the descriptor overlap does not identify Lowe's exact model, its species, or
its layup. No physical sheet/lot assignment, sheet-to-panel map, price, or
procurement quantity is established. The six modeled panels do not imply six
new sheets must be ordered.

Thus public pages cannot support a material cost bound, and the combined
candidate total or range remains null. The exact unsupported inputs are
recorded in [material-stock-and-panel-status.json](material-stock-and-panel-status.json).

## Claim boundary and verification

These public listing observations are neither quotes nor commitments; a page
availability label is not physical, owner-local, or delivered stock. No
vendor was contacted, no external account was accessed, no store or ZIP was
selected, no cart was used, and no purchase or receipt was made or inferred.
This attempt claims no selected product, fit, receipt amount, received
identity, complete candidate price range/total, material assignment, weight,
or readiness/criterion pass.

Run `python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt02/build_attempt02.py` from the repository root to verify the 30
source pins, reproduce the 92/12/66/144 reconciliations, and regenerate the
machine-readable status files. The source pins include the task queue SHA;
the script writes only this attempt02 folder. The verification result is in
[verification.json](verification.json).
