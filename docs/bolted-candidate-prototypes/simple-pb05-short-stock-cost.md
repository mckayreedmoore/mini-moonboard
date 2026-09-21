# PB05 300 mm versus detached 152.4 mm: bounded stock and cost

Status: development comparison, online retail check **2026-09-21**. This compares
the existing PB02 center plus the **current PB05** eight 300 mm blocks with the
[detached eight-block 152.4 mm screen](../../scripts/simple_pb05_short_block_screen.py).
The shorter option is a geometry trial, not a selected design, structural result,
cut instruction, purchase list, or complete final BOM. No seller was contacted and
nothing was bought. Prices below are US online leads before tax and delivery; no
store or ZIP was selected, so local price and stock are unknown.

## Actual scoped inventory

The [PB02 current BOM](simple-center-pb02-current-bom.md) specifies 3 × 5 in,
3 × 6 in, and 4 × 8 in 1/4-20 bolts (10 nuts, 20 washers). The
[PB05 source](../../scripts/simple_pb05_native.py) retains two 139.7 × 57.15 ×
300 mm center blocks and changes six outer blocks to 95.25 × 57.15 × 300 mm.
All eight have four bolt axes: two nominal 5 in rail bolts and two nominal
8 in upright bolts per block (32 nuts, 64 washers). The twelve outer upright
bolts use PB05's no-pocket 8 in trial and **24 washers** with a 0.734 in OD
envelope. The 24 outer-rail and 16 center-block washer positions use the
PB03 model's 25.4 mm diameter envelope. These are modeled envelopes, not
approved retail stacks.
The two center uprights are 38.1 mm thick, so their separate modeled grip is
38.1 + 139.7 = **177.8 mm**; the 228.6 mm gross grip in the PB04 pocket study
belongs to the 88.9 mm outer uprights, not these center joints.

| Nominal bolt length | PB02 | PB05 | Together | Online single-bolt lead |
| --- | ---: | ---: | ---: | ---: |
| [5 in Everbilt 800676](https://www.homedepot.com/p/204633308) | 3 | 16 | 19 | $0.62 |
| [6 in Everbilt 800686](https://www.homedepot.com/p/204633312) | 3 | 0 | 3 | $0.71 |
| [8 in Everbilt 800696](https://www.homedepot.com/p/204281626) | 4 | 16 | 20 | $0.94 |
| **Totals** | **10** | **32** | **42** | **$32.71** |

Both lengths retain **42 bolts, 42 nuts, and 84 washers**. The bolt arithmetic
is `19×0.62 + 3×0.71 + 20×0.94 = $32.71`. The nominal lengths remain price
leads: actual under-head length, usable threads, washer bearing, nut engagement,
wood grip and tools still need selection/measurement. In particular, the
[PB05 no-pocket tolerance review](simple-pb05-no-pocket-hardware-tolerances.md)
does not accept a delivered 8 in stack.

## Whole-board stock, including PB02

Use the same isolated-stock convention as the
[earlier V4 partial cost](simple-v4-partial-cost.md): one 8 ft = 2438.4 mm
4×6 stick, grain along its length, **3.2 mm crosscut kerf for every separated
blank**, and zero end trim or defect loss. PB02's two 4×6 pieces consume
`238.9 + 145 + 2×3.2 = 390.3 mm` under its example cut list. A 4×6 section
must also finish to 57.15 mm depth and to 139.7 mm for center blocks or
95.25 mm for outer blocks; the additional depth/width rips and their offcuts
get no saleable credit. These are length feasibility figures, not an optimized
shop layout.

| Isolated 4×6 requirement | Current 300 mm | Detached 152.4 mm |
| --- | ---: | ---: |
| Eight PB05 blanks plus eight kerfs | `8×303.2 = 2425.6 mm` | `8×155.6 = 1244.8 mm` |
| Add PB02's two 4×6 pieces/kerfs | **2815.9 mm** | **1635.1 mm** |
| Minimum whole 8 ft sticks by length | **2** | **1** |
| Example placement | 8 PB05 on stick 1; PB02 on stick 2 | all ten blanks on one stick |
| Total remaining length after these cuts | **2060.9 mm** across two sticks | **803.3 mm** on one stick |

One stick gives at most eight 300 mm or fifteen 152.4 mm separate PB05 blanks
under this zero-trim convention. With PB02 on the same stick, the short case
still has room for the eight required blocks. The current case misses one-stick
fit by **377.5 mm** even before trim; the short case has **803.3 mm** nominal
trim/defect/other-cut headroom. The short case removes 1180.8 mm of finished
PB05 block length, but the checkout change is **one whole board** only if
acceptable stock and cuts really yield the ten scoped pieces. The current
12.8 mm remainder beside eight 300 mm blocks cannot fit a PB02 piece.

[Lowe's 4×6×8 #2 & Better Douglas-fir lead](https://www.lowes.com/pd/4-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-8-ft-Actual/1000028917)
lists 3.562 × 5.625 in actual section, but currently asks for a ZIP to show
“Pricing & Availability.” The [Home Depot 4×6×8 lead](https://www.homedepot.com/p/202084523)
also exposed no numeric board price or verified local stock. The Lowe's section
is 90.4748 × 142.875 mm: nominally enough for both PB05 widths and the
57.15 mm depth after machining, but not proof of finished grade, dimensional
tolerance, defects, treatment suitability, or a usable delivered board.
Let `P46` be the local price of **one verified suitable 4×6×8 stick**. The
scoped new-stock checkout is conditionally `2P46` current versus `P46`
short, a `P46` difference, with **no supported dollar figure**. PB02's
example also uses one 4×4 and one 2×4 stick; their prices are unverified and
identical in both columns. Already-owned usable stock changes new cash, not
the required length; count and check it before treating its cash cost as zero.

## Hardware checkout versus pieces consumed

For both lengths, the direct retail leads above give $32.71 for individual
bolts. [Lowe's Hillman 490622](https://www.lowes.com/pd/Hillman-1-4-in-x-20-Zinc-Plated-Steel-Hex-Nut/1001265718)
shows **$1.98 per 12 nuts**: 42 nuts allocate `$6.93` at pack unit price,
but require **four packs = $7.92** at checkout, leaving six nuts.

For the **24 PB05 outer-upright washer positions only**, [Home Depot Everbilt 807210](https://www.homedepot.com/p/204284538)
is a 100-pack lead listed at 0.734 in OD and 0.065 in thickness in the
[retail size filter](https://www.homedepot.com/b/Hardware-Fasteners-Washers-Flat-Washers/1-4-inch/0734-in/0065-in/N-5yc1vZc2ckZ1z1bszxZ1z23290).
Its direct product page displayed **$11.70**, while Home Depot category
results displayed **$15.75** for the same model during this check. Treat
that as an unresolved online price range, not a guaranteed quote.

| Identically required in either length option | Consumed-price allocation | New-stock checkout |
| --- | ---: | ---: |
| 42 individual bolts | $32.71 | $32.71 |
| 42 nuts, 12-pack lead | $6.93 | $7.92 (4 packs) |
| 24 PB05 outer-upright washers, 100-pack lead | $2.81–$3.78 | $11.70–$15.75 (1 pack) |
| **Priced subset** | **$42.45–$43.42** | **$52.33–$56.38** |

The allocation divides pack prices by pieces used; it is **not cash saved**
on leftovers. One washer box leaves 76 washers of this size. **60 other washer
positions** (20 PB02, 24 PB05 outer-rail, 16 PB05 centers) have no compatible
selected retail item or honest checkout subtotal here. The previous V4 note's
$1.98/16 Hillman washer example has 5/8 in OD and cannot be carried over as
the PB05 outer model's
0.734 in washer or the center model's 25.4 mm washer. The nut and bolt leads
likewise do not prove strength or installed compatibility. Thus even the
hardware subtotal above is deliberately incomplete.

PB05 has **zero counterbore pockets** in both columns, so the prior V4
$13.97 Forstner-bit lead and any per-pocket charge are removed. The modeled
tool paths still require real drilling, saw/rip setup, socket/wrench access,
clamping and workholding; no new-tool price or labor allowance is supported.
Tax, delivery, machining, waste, PB02 4×4/2×4, the remaining washers and all
other frame/panel materials are outside this comparison.

**Decision boundary:** the shorter detached option offers a conditional
**two-to-one 4×6 stick reduction for PB02 + PB05** on the stated cut-length
assumptions, while nominal PB02/PB05 bolt, nut and washer counts do not change.
No numeric local board saving or complete cash total is established. The
short screen is geometry-only; strength, thread/washer fit, delivered wood,
and structural/fabrication approval remain open.
