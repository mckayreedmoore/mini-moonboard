# Integrated barrel frame: complete-cost ledger, incomplete prices

Checked 22 September 2026 (USD, public US retailer pages, no store selected).
This ledger covers the **46-pair kerf-right integrated-center-post candidate**,
the owner's selected barrel approach for development, not the selected
angle-frame shop packet. The
[source-built integrated assembly](../../scripts/export_owner_barrel_scene.py)
and [published scene](../../site/owner-barrel-layout-scene.json) show 24 former
angle duties, 46 new bolt/barrel pairs, 46 head-side washer positions, two
88.9 × 139.7 × 238.9 mm center posts, **no separate kicker backers**, 66 fixed
panel/kicker screw axes, and 12 retained frame-bolt axes. The nominal bolt mix
is **4 × 4 in, 30 × 5 in, 12 × 6 in**. This is a material/cash ledger, not a
compatible order, joint rating, or drilling release.

## New barrel hardware: observable catalog arithmetic

| Trial item | Needed | Exact public listing and displayed price | Extended |
| --- | ---: | --- | ---: |
| 1/4-20 × 4 in bolt | 4 | [Home Depot Everbilt 800656](https://www.homedepot.com/p/204633305), $0.52 each | $2.08 |
| 1/4-20 × 5 in bolt | 30 | [Home Depot Everbilt 800676](https://www.homedepot.com/p/204633308), $0.62 each | $18.60 |
| 1/4-20 × 6 in bolt | 12 | [Home Depot Everbilt 800686](https://www.homedepot.com/p/204633312), $0.71 each | $8.52 |
| Provisional 1/4-20 barrel | 46 | [Lowe's Hillman 880543](https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559), $1.48 each | $68.08 |
| **Bolts + barrels only** | **46 pairs** | **4×0.52 + 30×0.62 + 12×0.71 + 46×1.48** | **$97.28** |

The $97.28 is a **size-only catalog subset**, not a fillable or qualified
46-pair order. The Hillman page showed 36 available for shipping and 21 for
delivery in its default context, with pickup unavailable; those channel
quantities cannot be added. Its title says “plain steel” while its overview
says zinc-plated, so even the finish should be checked on the delivered part.
The [Home Depot Everbilt 801914 four-pack](https://www.homedepot.com/p/204276112)
is $5.98: 12 packs supply 48 barrels for $71.76, **$3.68 more** than 46
Hillman singles. Its controlled diameter, thread-axis location, usable thread,
and resistance have not been shown interchangeable with the modeled Hillman
body. No price here proves bolt thread engagement, tip clearance, barrel
strength, wood bearing, or a complete structural joint. The
[installed-stack audit](owner-barrel-integrated-stack-audit.md) and
[owner review](owner-barrel-integrated-owner-review.md) identify unresolved
reach, service, and load-path conditions. The earlier two 4½ in trial bolts
and their barrels/washers are **absent** from this 46-pair scene.

All **46 head-side washers** are required but a compatible SKU is unselected.
Two center seats model a 19.05 mm (3/4 in) OD envelope; this is a nominal
geometry input, not a fit tolerance or bearing approval. Catalog-only
comparisons are:

| Unqualified comparison | Package arithmetic | Catalog hardware total | Limitation |
| --- | ---: | ---: | --- |
| [Home Depot Everbilt 800452 1/4-in washer, 100-pack](https://www.homedepot.com/p/204276405), $7.97 | One pack; 54 surplus | **$105.25** | Listing does not establish controlled OD, thickness, bore tolerance, seat or bearing at all 46 heads. |
| [Lowe's Hillman 811070 1/4-in washer](https://www.lowes.com/pd/Hillman-1-4-in-Hot-Dipped-Galvanized-Standard-SAE-Flat-Washer/3037537), $0.26 each, with Everbilt barrel packs | 46 washers = $11.96; 12 barrel packs = $71.76; bolts = $29.20 | **$112.92** | Listed 3/4-in OD and 1/16-in thickness only nominally match the two center OD envelopes; tolerance, bearing, other seats, and hot-dip/zinc finish pairing remain open. |

These are **alternative shopping illustrations**, not lower/upper bounds for
compatible hardware or project cost. A cross-dowel uses its internal thread:
do not add 46 separate hex nuts. The 12 retained through-bolt stacks below
**do** require nuts and two washers each.

## Required material versus verified ownership

The [owner inputs](../bolted-candidate-owner-inputs.json) report structural
stock uncut and undrilled and select a two-4×8-sheet kerf-right width. They do
not record a counted, measured stock inventory. The
[purchased-material record](../purchased-materials.md) identifies the Roseburg
face plywood but does not record receipt quantity or price. Historical spend
and replacement value are separate from **new cash**; neither can be inferred
from the catalog subset.

| Material required by integrated assembly | Working quantity / source | Owned versus new-cash disposition |
| --- | --- | --- |
| Solid 4×6 frame stock | 2 × 10 ft side-rim sticks and 2 × 8 ft rear-leg sticks; see [kerf-right stock schedule](../floor-flush-construction-kerf-right/stock.csv) | Count and qualify actual owner-reported uncut stock first. Any shortage is new cash, **unpriced**. Two 238.9 mm center posts may each come from one 8-ft leg-stick offcut; this is conditional yield, not free stock. |
| 2×6 frame stock | 3 × 10 ft (two principals and header) and 6 × 8 ft (top rail, six half-rails, two runners and two outer posts) | Same physical-inventory gate; **unpriced** shortfall. A 2435.225 mm header blank leaves only 3.175 mm on an exact 8-ft stick before trim/kerf, so the 10-ft allowance is intentional. |
| Center posts | 2 × 88.9 × 139.7 × 238.9 mm, replacing the two original 2×6 posts and two historical separate backers | One per leg-stick offcut is possible in length: 2438.4 − 2028.463 = 409.937 mm before kerf/trim/defects. Check section, moisture, stamp, defects and allocations; if either fails, suitable extra 4×6 stock is **unpriced**. See [stock-lead screen](owner-barrel-center-post-retail.md). |
| Main and kicker plywood | 4 main blanks, each 47.9375 × 48 in, plus 2 kicker blanks, each 47.9375 in wide × 277 mm high, from the [kerf-right schedule](../floor-flush-construction-kerf-right/stock.csv) | Roseburg product is owner-purchased; **two usable sheets are an unverified working assumption**. Any extra matching sheet/offcut and the value of owned sheets are unpriced. Measure both dimensions and prove profile nesting before assigning purchase quantity. |
| Retained Grade 5 frame stacks | 4 × 1/2-13 × 8 in, 4 × 3/8-16 × 4 in, 4 × 3/8-16 × 4½ in partially threaded bolts; 12 matching nuts; 24 matching USS washers | Axes/counts come from the [assembly guide](../floor-flush-assembly-guide.md), but usable on-hand quantities, delivered shanks, fit in changed timber and current exact-stack prices are unknown. Do not price these as zero. |
| Panel/kicker screws | 66 Fas-n-Tite/Hillman 42605 #10 × 2½ in screws | [Purchase recorded](../current-panel-screw-purchase.md); count usable screws. If fewer than 66 are on hand, the [Lowe's 50-count box](https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-50-Count/999995042) is $7.98. At that unchanged price, new cash is $7.98 × ceiling((66 − usable on hand)/50); buying all 66 afresh takes two boxes, **$15.96**. |
| Hold, T-nut, LED and pad systems | 142 modeled T-nut positions; owner hold/hold-bolt kit, 132 modeled LED positions, two 48 × 72 × 5 in pads | Existing kit/material records are in the [assembly guide](../floor-flush-assembly-guide.md) and [pad record](../current-crash-pad-construction.md). Count usable parts and identify any hold-bolt, retention, wiring, cover or pad-supply shortfall; new cash **unpriced**. |
| Tools, finish, consumables, transport and labor | No selected quantities | Inventory owned tools and supplies; price only actual shortfalls. Delivery, tax and labor are excluded from catalog comparisons, **not** assumed free. |

The 24 ML24Z angles and 144 SDS25112 screws are displaced in this *candidate*
inventory. Their possible sunk purchase is not a credit against the new barrel
hardware. The 66 panel screws and 12 frame-bolt axes remain required, but
retaining an axis does not qualify the changed joint.

The public [Lowe's 4×6×10 lead](https://www.lowes.com/pd/4-in-x-6-in-x-10-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-10-ft-Actual/1000028921)
and [2×6×10 lead](https://www.lowes.com/pd/2-in-x-6-in-x-10-ft-Douglas-Fir-Kiln-dried-Lumber/1000571227)
request a location for price/availability. The 4×6 lead is green and lists a
3.562 × 5.625 in actual section, larger than the modeled 3.5 × 5.5 in; it is
not an identified dry, grade-stamped delivered lot. No exact qualified
13-stick timber basket or local price has been established. An alternate
species/grade/condition price would not close that gap.

The [Roseburg listing](https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973)
requests location for price and reports actual **47.436 × 95.868 in**.
The main-blank rectangle needs 48 in in one direction; two 47.9375-in widths
plus a 1/8-in kerf need exactly 96 in in the other. If those listed actual
dimensions apply to the owned sheets, the rectangular two-sheet main-blank
plan fails before kicker allocation. A third sheet reserved for kickers alone
would not fix it. The listing also gives inconsistent minimum dimensions;
it is not a measurement of the owner's sheets. Preserve fixed panel geometry
and verify measured sheets and an actual profile layout.

## Cost result and closure rule

**Known public-price subset: $97.28 bolts/barrels.** One unqualified washer
comparison makes $105.25, or $121.21 if all 66 panel screws also need two new
boxes. The Everbilt-barrel/Lowe's-washer comparison is $112.92 before any
panel-screw replacement. None is a complete project total, compatible-order
floor, or cost ceiling; the Hillman 46-piece supply and every trial stack
remain unverified.

For a later *additional-cash* total, use: qualified 46-pair bolt/barrel/washer
checkout **+** shortages in the 12 retained bolt/nut/washer stacks **+** any
panel-screw boxes **+** verified shortage against the four 4×6 and nine 2×6
stick allowance (including center-post yield) **+** verified plywood shortage
**+** hold/LED/pad and finish/tool/consumable shortfalls **+** delivery, tax and
any chosen labor. Keep receipts for owned material in a separate installed
value column. Exact store/lot prices, on-hand counts, dimensional fit and
material qualification must be known before a defensible complete low/high
range exists. This cost screen authorizes no purchase, drilling, fabrication,
load-test proof or climbing.
