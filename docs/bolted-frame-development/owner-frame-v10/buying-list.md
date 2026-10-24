# V10 catalog buying list

Checked October 24, 2026. This list follows the latest owner-directed
**standard 4×6 top-rail planning geometry**, revision
`v10-standard-top-4x6-stock-proposal-v2`: **116 bolts, 116 nuts, 232 washers,
44 spacer pieces, 24 Eoere angles and 66 purchased Hillman screws**.
The current viewer still retains Candidate 13, its intermediate 50.8 mm top
and 60 spacers. Its [frozen BOM](candidate13/packet-13-complete/hardware-bom.csv)
remains historical source evidence; it is not the basket below. The
[owner's stock instruction](top-rail-standard-stock-owner-constraint-v1.txt)
supersedes that intermediate top as a purchase design.

Use the [full 34-line CSV](buying-list.csv) for quantities, package allowances,
inventory status and part links. The [catalog check](catalog-check.json)
binds the geometry, recipe, per-axis checks, stock allocation and observed
supplier facts. Catalog sourcing does not clear the existing structural or
physical-operation holds. No order or supplier contact was made; Actual and
Disposition remain blank. The separate selected screw-and-bracket baseline
retains its own authority.

Prices below are observed USD catalog offers, before owned-inventory credit,
tax and freight. **ZIP 84601 stock, pickup, delivery and checkout prices are
unverified.** Whole-project cost remains incomplete where a line is unpriced.

## Bolts, nuts, washers and factory spacers

The package column includes economical bag allowances. Required quantities
are installed model pieces; package surpluses are inventory, not extra joints.
Each nut, washer and spacer now links to its own product page.

| Part | Required | Planning basket | Observed subtotal |
| --- | ---: | --- | ---: |
| 3/8-16 × 2½ in Grade 5 hex, [Bolt Depot 363](https://boltdepot.com/Product-Details?product=363) | 48 | One 50-piece bag; 2 spare | $18.52 |
| 3/8-16 × 3½ in Grade 5 hex, [366](https://boltdepot.com/Product-Details?product=366) | 12 | 12 singles | $8.64 |
| 3/8-16 × 4¾ in Grade 5 hex, [Zoro G0341148](https://www.zoro.com/zoro-select-grade-5-38-16-hex-head-cap-screw-zinc-plated-steel-4-34-in-l-10-pk-n012000370475/i/G0341148/) | 28 | Three 10-piece packs; 2 spare | $27.45 |
| 3/8-16 × 6 in ASTM A574 socket cap, [8092](https://boltdepot.com/Product-Details?product=8092) | 4 | 4 singles | $12.84 |
| 3/8-16 × 7½ in ASTM A574 socket cap, [8095](https://boltdepot.com/Product-Details?product=8095) | 14 | 14 singles | $100.80 |
| 3/8-16 × 8 in ASTM A574 socket cap, [8096](https://boltdepot.com/Product-Details?product=8096) | 4 | 4 singles | $40.56 |
| 1/2-13 × 4½ in Grade 5 hex, [400](https://boltdepot.com/Product-Details?product=400) | 2 | 2 singles | $3.48 |
| 1/2-13 × 8½ in Grade 5 hex, [Zoro G0340956](https://www.zoro.com/zoro-select-grade-5-12-13-hex-head-cap-screw-zinc-plated-steel-8-12-in-l-5-pk-n012000500850/i/G0340956/) | 4 | One 5-piece pack; 1 spare | $15.15 |
| 3/8-16 Grade 5 nuts, [2571](https://boltdepot.com/Product-Details?product=2571) | 88 | One 100-piece bag; 12 spare | $7.53 |
| 3/8-16 Grade 8 nuts for A574 bolts, [2584](https://boltdepot.com/Product-Details?product=2584) | 22 | 22 singles | $1.98 |
| 1/2-13 Grade 5 nuts, [2573](https://boltdepot.com/Product-Details?product=2573) | 6 | 6 singles | $1.80 |
| 3/8 in USS Grade 5 washers, [15023](https://boltdepot.com/Product-Details?product=15023) | 220 | Two 100-piece bags + 20 singles | $29.36 |
| 1/2 in USS Grade 5 washers, [15025](https://boltdepot.com/Product-Details?product=15025) | 12 | 12 singles | $4.32 |
| ½ in long factory spacers, [13731](https://boltdepot.com/Product-Details?product=13731) | 20 | Two 10-piece bags | $36.08 |
| 1 in long factory spacers, [13733](https://boltdepot.com/Product-Details?product=13733) | 24 | Two 10-piece bags + 4 singles | $51.34 |
| **Priced fastener/spacer subtotal** | | **15 SKU categories** | **$359.85** |

Both spacer products have nominal 13/32 in ID and ¾ in OD. Eight header
entries lacked an explicit spacer SKU; the buying translation assigns 13731
to their recorded 12.7 mm pieces in the retained family. Frozen geometry and
recipes are unchanged. Spacer tolerances and compression resistance remain
unpublished. The change from Candidate 13 is exactly sixteen 4-inch bolts
replaced by sixteen 4¾-inch bolts and sixteen 1-inch spacers removed; all
other fastener SKU counts are retained.

## Catalog fit findings

These are differences between catalog limits and recorded model envelopes,
not observations of delivered parts or demonstrated physical collisions.
The catalog check retains every affected axis ID.

| Item | Catalog finding | Effect on planning |
| --- | --- | --- |
| 60 hex bolts: 363 and 366 | Published head maximum 6.1722 mm; recorded scenario height 6.0 mm | The nominal clearance result does not establish clearance for these maximum heads. |
| Twelve ½-inch washers: 15025 | OD maximum 35.052 mm versus recorded 34.925; thickness maximum 3.3528 versus 3.175 mm | Recheck washer seats, stack length and occupied clearance using applicable bounds. |
| Eight front washers: 15023 | Four `rail_front_bolt_{left,right}_{1,2}` stacks retain OD 25.4 / thickness 2.032 mm; catalog maxima are 26.162 / 2.6416 mm | These front washer envelopes also need reconciliation. Other 15023 stacks already record those maxima. |
| Four front 6-inch A574 bolts: 8092 | Published minimum smooth body is 106.426 mm; current last wood face is 129.6416 mm with the catalog maximum head washer | The minimum guaranteed body ends 23.2156 mm before that face. Retain threaded wood-bearing treatment; full smooth-body coverage is not established. |
| Sixteen changed top-beam stacks: G0341148 | Recorded analytical transition leaves 4.1656 mm of wood and 6.35 mm of steel in threaded bearing | Catalog minimum thread length does not guarantee that body transition. Matched root/body assessment and delivered fit remain separate. |
| Long A574 8096 and Zoro bolts | Product pages do not publish a minimum full smooth-body guarantee | Retain each specified body/runout requirement; nominal length and “partially threaded” do not establish it. |

Product 8095 publishes a 144.526 mm minimum body; its retained 144.272 mm
analysis floor is slightly smaller. Product 8092 similarly publishes
106.426 mm versus the retained 106.172 mm floor. Those comparisons establish
the specific published floors, not full coverage of every receiver.
The per-axis replay uses current product lengths and published bounds where
available. Source fields named `minimum_length_mm` have different producer
meanings, including stack-required lengths; they are not uniformly catalog
minimum delivered lengths. No cached value is relabeled as a supplier guarantee.

## Solid timber

Retain **dry, untreated, solid-sawn DF-L No. 2 or better**, with actual material
and finished-member grade confirmed. The allocation below covers all 22 sawn
members using 13 boards, approximately **175⅓ nominal board feet**. It allows
25.4 mm at each board end and 3.175 mm per member for kerf. It is a sourcing
allowance, not an issued cutting sequence or a guarantee of clear grade yield.

| Stock | Boards | Assigned members | Catalog lead and remaining check |
| --- | ---: | --- | --- |
| 2×6 × 8 ft | 5 | Two runners plus center posts; three paired cross-rail boards | [Lowe's 187153 / STDFL20692](https://www.lowes.com/pd/Top-Choice-2-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-1-5-in-x-5-5-in-x-8-ft-Actual/1000902078): #2 & Better, kiln-dried, listed 38.1 × 139.7 mm. Confirm stamp and usable length. |
| 2×6 × 10 ft | 3 | Header and two center principals | [Lowe's 130751 / 720966-10](https://www.lowes.com/pd/2-in-x-6-in-x-10-ft-Douglas-Fir-Kiln-dried-Lumber/1000571227): #2 Prime, kiln-dried, listed 38.1 × 139.7 mm. Replaces the old no-longer-sold link. |
| 4×6 × 8 ft | 2 | Rear legs, with an outer post from each remaining length | **Dry-stock quote still needed.** [Lowe's 92730 / 637637](https://www.lowes.com/pd/4-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-8-ft-Actual/1000028917) is green and does not match the dry-stock basis. Finished section is 88.9 × 139.7 mm. |
| 4×6 × 10 ft | 1 | Standard top rail and two packers | [Home Depot 603783](https://www.homedepot.com/p/202094390) lists the correct 88.9 × 139.7 mm section and No. 2-or-better grade, but only “fir” species and no supported dry designation. Obtain the matching dry DF-L specification. |
| 4×8 × 10 ft starting stock | 2 | Two 88.9 × 152.4 mm sloping sides | [Lowe's 100565 / 151980](https://www.lowes.com/pd/Georgia-Pacific-4-in-x-8-in-x-10-ft-Douglas-Fir-Lumber-Common-3-562-in-x-7-5-in-x-10-ft-Actual/1000464221): #2 & Better Douglas fir, kiln-dried, listed 90.4748 × 190.5 mm. Provides a dimensional machining allowance; confirm finished grade after remanufacture. |

The two packers require 177.8 × 139.6 × 50.8 mm bounding blanks and are
allocated from the top-rail board's remainder. The side blanks are about
2,539.8 mm long; an 8-foot board is too short. The header is about 2,435.2 mm
before trim allowance, so its purchase allocation also remains 10 feet.
Local prices for these five stock lines remain unverified.

## Plywood, angles, screws and adhesive

| Item | Full requirement / purchase allowance | Source and disposition |
| --- | --- | --- |
| Cleat plywood | Four 410.3 × 215.9 mm nominal half-inch leaves; **two 2×2 project panels**, two leaf blanks per panel | [Home Depot 300888 / model 00114](https://www.homedepot.com/p/205764080) lists 12.7 × 603.25 × 603.25 mm Douglas-fir BC sanded Exterior plywood. Observed category price $11.48 each, $22.96 for two. This is a dimensional lead: PS 1 APA Group 1 Other, strength-axis orientation and actual minimum 11.9 mm per leaf remain unverified. A suitably documented 2×4 panel is an alternative quote, not an extra purchase. |
| Face plywood | Three nominal 4×8 sheets as a replacement-layout allowance for four main panels and two kickers; credit purchased material first | Retain [Roseburg / Lowe's 12235, model 119055](https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973). Listing width 3.953 ft conflicts with the modeled 1,217.6125 × 1,219.2 mm main blanks. Actual usable sheet dimensions and the additional quantity remain unobserved. |
| Eoere angles | **24 angles = six four-packs**, before inventory credit | [ZX128-B-T4 / B0C7V7VS89](https://www.amazon.com/dp/B0C7V7VS89). Exact model and four-pack confirmed; usable price/stock not established. Listing “¼ in (6 mm)” does not guarantee the modeled 6.35 mm thickness or full bend/hole tolerances. Its advertised load is not a complete-joint resistance. |
| Hillman panel/kicker screws | **66 installed; zero new boxes scheduled** | Purchased [42605 / Lowe's 755741](https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-50-Count/999995042). Replacement-only observation: $7.98 per 50, so two boxes give 100 for $15.96. Retain the purchased policy and its unresolved resistance/stiffness. |
| Cleat adhesive | Standard tan **Loctite PL Premium 1390595**, 10 fl oz; tube count unresolved | [Home Depot 223222](https://www.homedepot.com/p/202020473), observed $7.48 per tube. Retains the conditional planning product. [Henkel's TDS](https://datasheets.tdx.henkel.com/LOCTITE-PL-Premium-Construction-Adhesive-en_US.pdf) gives bead yield, not a qualified full-face plywood-leaf spread or required tube count. Bond stiffness, resistance and process remain open. |

## Holds, lighting, pads and tools

These remain separate from the 116 structural bolt stacks. Inventory credit
is necessary wherever the owned quantity is not recorded.

| Item | Full allowance | Purchasing treatment |
| --- | --- | --- |
| Escape zinc three-hole screw-in T-nuts | **142 locations**; one 200-count pack if starting without usable inventory | [Selected product](https://escapeclimbing.com/products/hd3hnut). A received sample identifies the part, not the owned count. A 200-pack leaves 58 spare locations. Exact variant price/availability is unresolved. |
| T-nut retention screws | **426 screw roles** if all three holes are used at 142 locations | Included screws are stated on the Escape listing. This is a count inference; confirm supplied quantity and length. Separate from the 66 Hillman screws. |
| Wood-hold bolts | **Two [60-202-WO-USA kits](https://us.moonclimbing.com/products/moonboard-wood-hold-bolts)**, before inventory credit | $35 each, $70 total; 64 flat-head 3/8-16 × 3½ in kit bolts. Uses a ¼-inch hex key. |
| Plastic-hold bolts | **Two [60-202-USA kits](https://us.moonclimbing.com/products/universal-bolt-kit)**, before inventory credit | $35 each, $70 total; kit contents total 64 cap-head × 2½ in and 40 × 3½ in, all 3/8-16. Uses a 5/16-inch hex key. Kit contents do not establish the installed per-hold length schedule. |
| Hold anti-rotation / screw-on fasteners | Exact type, length and quantity remain unresolved | Reconcile the hold-specific instructions and inventory; no automatic screw count or structural Hillman credit is assigned. |
| Mini 2025 hold bundle | **Owned: one 138-hold bundle** | [Current catalog identity](https://us.moonclimbing.com/products/mini-moonboard-2025-hold-set) confirmed; no replacement bundle scheduled. |
| LED kit, controller and power supply | **Owned: one kit, 132 modeled light positions** | Retain the [owned-kit routing record](../../led-wiring-reference.md). The [current 60-201-V5 page](https://us.moonclimbing.com/products/moonboard-led-kit) now describes 200 bulbs, unlike the retained three 50-light strings. No new kit or routing change is scheduled. |
| Landing pads | **Owned: two 48 × 72 × 5-inch pads** | Retain the [owner-reported pad construction](../../current-crash-pad-construction.md); no replacement foam or pads scheduled. |
| Tools and consumables | Inventory first | Check keys, 9/16- and ¾-inch wrench/socket families, drilling/gaging tools, saw/guide, clamps, caulk gun and consumables. Retain the [selected Kobalt 80277 panel-screw tool](../../current-panel-screw-purchase.md). Tool quantities and current offers were not fully priced; this list adds no drilling instructions. |

The **$359.85** subtotal covers the fifteen fastener/spacer lines only.
The cleat-plywood dimensional lead adds $22.96 and four hold-bolt kits add
$140 before inventory credit, if those conditional lines are used. Timber,
angles, T-nuts, qualified adhesive quantity, missing tools, tax and freight
still prevent a supported full-project total. Face plywood, Hillman screws,
holds, LEDs and finished pads are retained as reported owned material.

Current and historical evidence remain active in their existing packets.
The small catalog replay and stock allocation remain under
`fea/generated/v10-catalog-buying-list-v1/`; no native solve, CAD rebuild,
geometry change, archive, pruning, staging, commit or purchase occurred here.
