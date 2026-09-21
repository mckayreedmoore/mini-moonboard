# V4 PB02 center + eight PB04 rail stations: partial hardware and stock cost

Status: **development-only cost decision**, checked online 2026-09-21. Scope is the
current PB02 center and eight PB04 service-rail corner blocks, **not** a full-frame
estimate or a purchase, drill, or structural release. Retail prices are visible US
online prices before tax and delivery; no store/ZIP stock or exact delivered parts
were checked. No seller was contacted and nothing was bought.

## Current count and nominal length leads

The [PB02 current BOM](simple-center-pb02-current-bom.md) has ten 1/4-20 bolts:
three 5-in, three 6-in, four 8-in; ten nuts and twenty washers. PB04 has eight
blocks with four bolts each: sixteen 5-in rail-stack leads and sixteen 8-in
upright-stack leads, with 32 nuts and 64 washers. Of the sixteen upright stacks,
**twelve outer stacks require pockets** for the nominal 8-in trial; the four
center stacks have the shorter inherited grip. The source for PB04 geometry is
[`simple_pb03_lower_center_pair.py`](../../scripts/simple_pb03_lower_center_pair.py)
and the [installed-stack screen](../../scripts/simple_pb04_installed_stack.py).

| Nominal 1/4-20 bolt | PB02 | PB04 | Combined | Online single lead |
| --- | ---: | ---: | ---: | ---: |
| [3 in, Everbilt 800636](https://www.homedepot.com/p/204633286) | 0 | 0 | 0 | $0.38 |
| [5 in, Everbilt 800676](https://www.homedepot.com/p/204633308) | 3 | 16 | 19 | $0.62 |
| [6 in, Everbilt 800686](https://www.homedepot.com/p/204633312) | 3 | 0 | 3 | $0.71 |
| [8 in, Everbilt 800696](https://www.homedepot.com/p/204281626) | 4 | 16 | 20 | $0.94 |
| **Total** | **10** | **32** | **42** | |

The 3-in SKU is an inventory check, **not** a current V4 need. Nominal lengths
are price leads, not verified installed stacks. PB02's limiting 5-in trial has
only **0.17 mm** minimum tip margin under its invented dimensional interval
([stack screen](simple-center-pb02-integrated-stack-screen.md)). The twelve PB04
outer 8-in stacks need nominal **36.9824 mm** pockets: the installed screen
returns **REVISE**, with zero extra dimensional reserve beyond two projected
threads. A [detached 37.9824-mm trial](../../scripts/simple_pb04_pocket_reserve_trial.py)
adds 1 mm nominal margin and leaves 101.7176 mm X-direction wood, but is not
an adopted tolerance or a checked net-section detail. Exact under-head length,
usable threads/runout, shank/root location, nut and washer dimensions and
strength, pocket floor, and access remain unverified. Deeper pockets do not
change the listed bolt quantity or nominal length, and no supported dollar
increment per pocket exists.

## Hardware cash versus consumption

Illustrative mixed-store basket: the linked Home Depot single bolts above;
[Lowe's Hillman 490622 nuts](https://www.lowes.com/pd/Hillman-1-4-in-x-20-Zinc-Plated-Steel-Hex-Nut/1001265718)
at **$1.98/12** and
[Hillman 490687 washers](https://www.lowes.com/pd/Hillman-1-4-in-Zinc-plated-Standard-Flat-Washer-16-Count/3035987)
at **$1.98/16**. The washer page's title and quantity selector say 16, while
one overview sentence says 160; confirm the selling unit before using this
as a cart price. Its listed 5/8-in OD is also below PB04's modeled 0.734-in
washer OD. None of these listings proves a suitable structural stack.

| Scope | Bolts used | Nuts / washers used | Consumed allocation | Initial hardware checkout |
| --- | ---: | ---: | ---: | ---: |
| PB02 | $7.75 | 10 / 20 | $11.88 | $13.69: 1 nut + 2 washer packs |
| PB04 | $24.96 | 32 / 64 | $38.16 | $38.82: 3 nut + 4 washer packs |
| **Together** | **$32.71** | **42 / 84** | **$50.04** | **$52.51: 4 nut + 6 washer packs** |

Combined exact allocation is `$32.71 + 42×$1.98/12 + 84×$1.98/16
= $50.035`, rounded once. Checkout is `$32.71 + 4×$1.98 + 6×$1.98
= $52.51`, leaving six nuts and twelve washers. It is a price illustration,
not a buy-ready BOM. A different compatible washer/bolt or pack can change
both totals. Owner-held bolts, nuts, washers, and tools are **sunk inventory**
only if their exact quantities and suitability are confirmed; their historical
cost does not belong in new cash checkout.

## Blocks and tools

The eight current PB04 blocks are 139.7 × 57.15 × **300 mm**. A representative
**152.4 mm** length-only block passed a bounded geometry screen at one lower
center and one upper outer station; that does **not** establish eight shorter
acceptable blocks or changed strength. The [short-stock calculator](../../scripts/simple_pb01_short_stock_cost.py)
assumes an 8 ft = 2438.4 mm 4×6 stick, a 3.2 mm crosscut kerf per blank,
zero trim and defects, and a depth rip to 57.15 mm:

| Eight PB04 blanks from one 4×6×8 | Length + kerfs used | Remainder | Clean-blanks ceiling |
| --- | ---: | ---: | ---: |
| 300 mm | 2425.6 mm | 12.8 mm | 8 per stick |
| 152.4 mm, conditional | 1244.8 mm | 1193.6 mm | 15 per stick |

The 15-blank ceiling is **not** eight free blocks plus seven saleable parts.
With only eight used, the remainder stays charged to the board. PB02 also
needs **390.3 mm** of 4×6 length including its two example kerfs. Thus current
300-mm PB04 plus PB02 totals **2815.9 mm**, requiring at least two 8-ft 4×6
sticks on this isolated cut-length basis. The conditional 152.4-mm PB04 plus
PB02 totals **1635.1 mm**, fitting one stick by length with **803.3 mm** left.
This possible one-stick reduction is subject to section, separate ripping,
end trim, defects, grain, grading and all eight block checks. A
[Lowe's #2 & Better Douglas-fir 4×6×8 lead](https://www.lowes.com/pd/4-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-8-ft-Actual/1000028917)
lists 3.562 × 5.625 in actual section but says “Get Pricing & Availability.”
The [Home Depot 4×6×8 lead](https://www.homedepot.com/p/202084523) also
exposes no verified local board price. Let `P46` be a suitable whole-board
price: new-stock 4×6 checkout is conditionally `2P46` versus `P46`, **not**
a 49.2% cash saving. PB02 additionally needs one 4×4 and one 2×4 stick by
its example yield; their prices and any owner stock are unknown. If suitable
wood is already owned, show it separately as sunk stock and recalculate new
cash only after counting its usable lengths.

PB04's pocket tool has an online lead:
[Diablo FB-007 1-in Forstner bit](https://www.homedepot.com/p/100098841),
**$13.97 for one**. A
[Drill America 9/32-in × 12-in extension bit](https://www.homedepot.com/p/305284242)
is **$6.23 for one**; its 7.14-mm diameter is not the modeled 7.5-mm bore,
so it is only a reach/price lead and is **excluded** from the tool subtotal.
If the Forstner bit were newly needed, its conditional first-tool cash is
$13.97, with no justified per-joint consumption charge.
Bit reach, bore size, drill, socket/extension, wrench, saw/rip setup, clamps,
wear, labor and safe pocket workholding remain open. The 1-mm deeper trial
uses the same nominal 1-in pocket tool; extra labor/wear has no sourced price.

**Decision boundary:** the only numerically supported fresh-cash subtotal is
**$52.51 hardware**, or **$66.48 including the example Forstner bit** if needed.
Add whole-board prices (`2P46` now, conditionally `P46` for shorter blocks),
PB02 4×4/2×4 stock, any other needed tools/consumables, tax and delivery.
No exact local stock, tax, delivery, or complete partial-assembly total is
available. Do not buy from this nominal basket until the actual stacks,
washer bearing, all eight blocks and pocketed wood are resolved.
