# PB01 short corner block: retail stock, yield, and cost sidecar

Status: bounded arithmetic for **one 139.7 × 57.15 × 152.4 mm bolted solid-wood
corner block** versus the historical 139.7 × 57.15 × 300 mm block. The
[short-block geometry screen](simple-pb01-short-block-screen.md) keeps the X/T
section, four bolt centers, wood grips, and hardware count unchanged. Its
49.2% gross-block-volume reduction is **not** a 49.2% purchase saving. This is
not a stock selection, structural acceptance, cut list, or drilling release.
Retail pages were checked online on 2026-09-20; no seller was contacted and
nothing was bought.

## Exact 4×6×8 ft leads and section allowance

| Lead | Page evidence on this check | Implication for 139.7 × 57.15 mm finish |
| --- | --- | --- |
| [Lowe's item 92730 / model 637637](https://www.lowes.com/pd/4-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-8-ft-Actual/1000028917) | #2 & Better Douglas fir, green, S4S; nominal 4 × 6 × 8 ft; listed actual **and industry-standard minimum** 3.562 × 5.625 in × 8 ft. Page says “anti-stain treated” and “Meets AWPA Standards: No.” It displays “Get Pricing & Availability,” with no numeric board price or local stock confirmation. | Listed section converts to **90.4748 × 142.875 mm**. A 3.2 mm example rip through the 90.4748 mm depth leaves 57.15 mm finish plus **30.1248 mm side offcut**. The width has **3.175 mm** excess to face/size; it is less than the example 3.2 mm blade kerf, so a second full-width rip with a separately usable strip is not assumed. |
| [Home Depot internet #202084523 / model 0405438](https://www.homedepot.com/p/202084523) | Current accessible page identifies a nominal 4 × 6 × 8 ft #2 Premium/Prime fir lead, but its rendered product fields did not expose a verifiable current actual/minimum section, species certainty, board price, or local availability. The [prior retail inventory](simple-joint-retail-inputs.md) recorded 3.5 × 5.5 in S4S and Douglas fir. | **Conditional only:** if 3.5 × 5.5 in is delivered, section is 88.9 × 139.7 mm; the same depth rip leaves a **28.55 mm side offcut** after kerf and no nominal width excess. This is not a current dimension guarantee. |

The nominal “4 × 6” is not a 101.6 × 152.4 mm usable section. Both
section examples need a depth rip; the Lowe's example also needs width
sizing. The quoted excess/offcut widths are *geometric* and have **zero
salvage credit**. Machining must leave a sound, correctly graded/species-
identified finished member; a retail grade label does not establish its
post-rip grade, the delivered DF-L design-species group, straightness,
moisture/shrinkage, treatment compatibility, or freedom from defects at the
eventual bolt zones. The Lowe's anti-stain statement makes an untreated-only
assumption uncertain. Neither online listing proves a usable local board.

## One-stick length screen

Assume an 8 ft = **2438.4 mm** stick, grain along its length, one **3.2 mm
crosscut kerf for every separated blank** (including the last separation
from the remainder), and a **3.2 mm depth-rip kerf**. These are example saw
allowances, not tool specifications. The base calculation has **zero end
trim, squaring, defect rejection, or planing loss**. A full-length depth
rip and ripping individual blanks have different workholding requirements;
neither process is selected here. Count is
`floor((2438.4 − end_trim) / (blank_length + 3.2))`.

| Length scenario | Short 152.4 mm | Historical 300 mm |
| --- | ---: | ---: |
| Zero end trim: maximum separated blanks | **15** | **8** |
| Zero end trim: blanks + crosscut kerfs consumed | 2334.0 mm | 2425.6 mm |
| Zero end trim: remaining stick length | 104.4 mm | 12.8 mm |
| 25.4 mm end-trim sensitivity: maximum blanks | **15** | **7** |
| 105 mm end-trim sensitivity: maximum blanks | **14** | **7** |

Thus the nominal short-blank count is 15/8 = **1.875×** the historical
count under the zero-trim assumptions. It is a ceiling for clean blanks,
not a predicted number of acceptable corner blocks. Crosscut kerfs total
48.0 mm short or 25.6 mm historical at those ceilings; the depth rip also
converts wood to sawdust. The remaining 104.4 or 12.8 mm, and the ripped
side material, are charged to the purchased stick until a separately
verified use exists. Defects can reduce either yield, especially when the
remaining grain-end reserve and bolt locations must be checked on each
short block. The [short-block screen](simple-pb01-short-block-screen.md)
records an unresolved rear-end/member check; stock yield does not close it.

## Cost boundary

Let `P_L` be the unknown **whole-board** Lowe's checkout and `P_H` the
unknown whole-board Home Depot checkout, each before tax, transport, cuts,
tools, and quality checks. Neither retailer page supplied a usable local
numeric price here. Let `H` be the **unchanged four-bolt hardware checkout**
for whichever *compatible* stack is later established; this sidecar adds no
bolt, nut, or washer and does not update or adopt the illustrative prices in
the [historical one-joint cost comparison](simple-rail-cost-comparison.md).

| Conditional comparison, one retailer/stock basis at a time | Short | Historical |
| --- | ---: | ---: |
| First isolated block, cash outlay before excluded charges | `P + H` | `P + H` |
| One fully used clean stick, wood allocation per accepted block | `P / 15` | `P / 8` |
| `Q` identical blocks, perfect clean yield, whole-board wood checkout | `ceil(Q / 15) × P` | `ceil(Q / 8) × P` |

`P` means either `P_L` or `P_H` consistently within a comparison. The
allocation line applies **only if all 15 or 8 blanks have a real accepted
use** and the whole stick's price is assigned among them. It is not the
cash cost of one block. For `Q = 8`, both lengths still require one board;
for `Q = 9` through `15`, the ideal historical case requires two boards and
the short case one. Actual rejected blanks, trim, machining, labor,
delivery, hardware pack sizes, and any other demands for the same board can
change this. No offcut is assumed free or deducted from checkout.

**Conclusion:** shorter length creates a credible *conditional* stock-yield
advantage, while a single-block first purchase remains one whole 4×6 board
plus unchanged hardware. A dollar saving, local purchase option, and
acceptable finished part cannot be established from these pages. The
reproducible arithmetic is in
[`scripts/simple_pb01_short_stock_cost.py`](../../scripts/simple_pb01_short_stock_cost.py)
with focused tests; no fabrication dimensions beyond the trial envelope are
released.
