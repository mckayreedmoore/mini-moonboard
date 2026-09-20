# PB-01 purchase-cost boundary: one lower-right service-rail joint

Status: diagnostic estimate only, checked 2026-09-20. This is **one**
`clip_horizontal_lower_right_1` joint, not a board-wide bill of materials or
a structurally suitable detail. No purchase, contact, or drilling is authorized.
The [geometry record](simple_rail_joint_comparison.json),
[joint comparison](simple-rail-joint-comparison.md), and
[retail source inventory](simple-joint-retail-inputs.md) define the scope.
Prices are US dollars, before tax, shipping, cuts, tools, and quality checks;
retailer/ZIP availability and prices can change.

## Four-bolt, one-block 4×6 cleat diagnostic

The current *trial*, not a qualified bolt schedule, has two upright-to-cleat
and two rail-to-cleat through-bolts. Its cut block is 139.7 mm across X,
57.15 mm tangent, and 300 mm along panel-normal grain. The wood-only
grips are **177.8 mm** at each upright bolt and **95.25 mm** at each rail bolt.
The CAD's 182.8/100.25-mm trial cylinders each include 2.5 mm of exterior
envelope at both ends; that 5 mm is not wood. Thus 8 in (203.2 mm) and
5 in (127 mm) leave only 25.4 and 31.75 mm beyond the wood,
respectively, before two washers, a nut, thread engagement/projection,
thread runout, and tolerance. The retail inventory's earlier 177.8-mm
4×6 grip also applies to the upright wood here; the bolt count changes.

This table deliberately uses **one consistent single-item Lowe's price
scenario** rather than treating a 100-pack's unit share as cash outlay.
The linked listings displayed these prices on the 2026-09-20 check; the
8-in bolt lists A307, while the 5-in bolt lists “all-purpose” (and says
Grade 1 in its overview). That is not a verified matching bolt specification.

| Diagnostic item | Qty used | Visible retail unit price | Nominal used cost | Minimum listed purchase for this scenario |
| --- | ---: | ---: | ---: | ---: |
| [Hillman galvanized 3/8-16 × 8-in hex bolt](https://www.lowes.com/pd/Hillman-3-8-in-x-8-in-Galvanized-Coarse-Thread-Hex-Bolt/3824905) | 2 | $2.83 each | $5.66 | 2 singles = $5.66 |
| [Hillman galvanized 3/8-16 × 5-in hex bolt](https://www.lowes.com/pd/Hillman-3-8-in-x-5-in-Galvanized-Coarse-Thread-Hex-Bolt/3058911) | 2 | $2.07 each | $4.14 | 2 singles = $4.14 |
| [Hillman galvanized 3/8-16 hex nut](https://www.lowes.com/pd/Hillman-3-8-in-x-16-Galvanized-Steel-Hex-Nut/3037535) | 4 | $0.32 each | $1.28 | 4 singles = $1.28 |
| [Hillman hot-dip galvanized 3/8-in flat washer](https://www.lowes.com/pd/Hillman-1-Count-0-400-in-x-Hot-Dipped-Galvanized-Standard-SAE-Flat-Washer/3037541) | 8 | $0.33 each | $2.64 | 8 singles = $2.64 |
| One cut [#2 & Better Douglas-fir 4×6×8](https://www.lowes.com/pd/4-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-8-ft-Actual/1000028917) block | 1 | Local price unavailable | Unknown | One whole 8-ft board, price unknown |
| **Known hardware subtotal only** | | | **$13.72** | **$13.72** |

Arithmetic: `2×2.83 + 2×2.07 + 4×0.32 + 8×0.33 = $13.72`.
The actual cost to buy this joint's cleat stock is **$13.72 + P₄ₓ₆**, where
`P₄ₓ₆` is the unknown local price of the whole board, *not* a 300-mm
fraction of its shelf price. An offcut could be shared with other joints
only after a complete cut plan; no salvage credit is assumed. The Lowe's
listing gives actual stock 3.562 × 5.625 in, not the CAD's final dressed
block. Rip/cut feasibility, grade after cutting, moisture, and stock quality
remain unverified.

Pack pricing shows why an allocated unit cost and a first-purchase outlay
cannot be conflated. An **alternative, not a compatible selected BOM** uses
Home Depot's [Prime-Line 8-in A307A 10-pack](https://www.homedepot.com/p/310465220)
at $12.56, two [Everbilt galvanized 5-in singles](https://www.homedepot.com/p/204645574)
at $2.21 each, one [Everbilt nut 100-pack](https://www.homedepot.com/p/204274098)
at $33.66, and one [Everbilt washer 100-pack](https://www.homedepot.com/p/204284545)
at $33.42. Its **allocated** four-bolt share is
`2×(12.56/10) + 2×2.21 + 4×(33.66/100) + 8×(33.42/100) = $10.95`
(rounded); its **minimum pack checkout** is
`12.56 + 2×2.21 + 33.66 + 33.42 = $84.06`, before the whole 4×6 board.
The pack leaves 8 long bolts, 96 nuts, and 92 washers unused at this joint.
The Prime-Line listing has conflicting finish fields, and neither this
illustration nor the single-item scenario proves bolt/washer compatibility,
wood bearing, or usable thread length.

## Provisional quarter-inch four-bolt purchase sidecar

This prices the **same 300-mm cleat and four-bolt pose**, with two 1/4-20 ×
8-in upright stacks and two 1/4-20 × 5-in rail stacks, four nuts, and eight
washers. It is a purchasing illustration, not a substitution into the 3/8-in
strength case or an approved fastener schedule. Direct retailer pages were
checked 2026-09-20; the [quarter-inch source screen](quarter-inch-bolt-source-screen.md)
records the separate mechanics and product-evidence gaps. The 177.8-mm and
95.25-mm wood-only grips leave nominally 25.4 mm and 31.75 mm, respectively,
before washers, nut, thread engagement/projection, runout, and tolerances.

| Illustrative zinc hardware | Needed | Listed selling unit | Joint allocation | First listed checkout |
| --- | ---: | ---: | ---: | ---: |
| [Home Depot Everbilt 1/4-20 × 8-in hex bolt, 800696](https://www.homedepot.com/p/204281626) | 2 | $0.94 each | $1.88 | $1.88 |
| [Home Depot Everbilt 1/4-20 × 5-in hex bolt, 800676](https://www.homedepot.com/p/204633308) | 2 | $0.62 each | $1.24 | $1.24 |
| [Home Depot Everbilt 1/4-20 hex nut, 801730](https://www.homedepot.com/p/204274089) | 4 | $6.98 / 100 | $0.2792 | $6.98 |
| [Home Depot Everbilt 1/4-in flat washer, 800452](https://www.homedepot.com/p/204276405) | 8 | $7.97 / 100 | $0.6376 | $7.97 |
| **Known hardware only** | | | **$4.0368 ≈ $4.04** | **$18.07** |

Allocation is `2×0.94 + 2×0.62 + 4×(6.98/100) + 8×(7.97/100)
= $4.0368`; checkout is `2×0.94 + 2×0.62 + 6.98 + 7.97 = $18.07`.
The latter leaves 96 nuts and 92 washers for other work. This same-store
example uses listed online selling units; store/ZIP stock and price are
unconfirmed. The 5-in bolt listing describes a fully threaded bolt, and the
8-in listing gives a 6-in threaded length, but no controlled delivered
shank/thread transition or root diameter. The washer listing does not supply
verified wood-bearing dimensions or capacity. Nominal thread and zinc finish
alone do not qualify the stack.

A **separate, stronger thread-placement lead**, priced from Home Depot's
online pages on 2026-09-20, uses two
[Prime-Line 9058821 A307 Grade A 8-in bolts](https://www.homedepot.com/p/310465152)
from a 10-pack at $16.71, two
[Prime-Line 9058745 A307 Grade A 5-in bolts](https://www.homedepot.com/p/310326760)
from a 25-pack at $14.52, four of the above Everbilt nuts from a $6.98
100-pack, and eight
[Everbilt 807210 wide-pattern washers](https://www.homedepot.com/p/204284538)
from an $11.70 100-pack. Its four-bolt **allocated hardware** is
`2×(16.71/10) + 2×(14.52/25) + 4×(6.98/100) + 8×(11.70/100)
= $5.7188 ≈ $5.72`; the **initial four-pack checkout** is
`16.71 + 14.52 + 6.98 + 11.70 = $49.91`. It leaves eight long bolts,
23 short bolts, 96 nuts, and 92 washers. The [source screen](quarter-inch-bolt-source-screen.md)
explains why the same standard thread-length assumption actually leaves
the 5-in rail nut **0.37 in short of seating** against the outer washer.
The [two-sided stack screen](simple-pb01-thread-stack-screen.md) records
that failure and a fully threaded rail lead. The $49.91 pack checkout is
therefore a priced **incompatible nominal combination**, not a usable or
selected BOM; delivered shank, washer, joint and local stock remain
unverified, and the unknown whole 4×6 purchase is additional.

A second **mixed-retailer pack illustration**, using the same Home Depot
bolts and [Lowe's Hillman 12-nut pack, 490622](https://www.lowes.com/pd/Hillman-1-4-in-x-20-Zinc-Plated-Steel-Hex-Nut/1001265718)
at $1.98 plus [Lowe's Hillman 16-washer pack, 490687](https://www.lowes.com/pd/Hillman-1-4-in-Zinc-plated-Standard-Flat-Washer-16-Count/3035987)
at $1.98, allocates `1.88 + 1.24 + 4×(1.98/12) + 8×(1.98/16)
= $4.77` and has a **$7.08 listed hardware checkout**. It leaves eight
nuts and eight washers, but requires sourcing from two stores; delivery or
travel can overturn the apparent checkout difference. Hillman's washer
listing gives 5/8-in OD and 1/16-in thickness, not an approved bearing plate;
the nut's mechanical grade and stack height remain unverified.

The [Lowe's #2 & Better Douglas-fir 4×6×8 listing](https://www.lowes.com/pd/4-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-8-ft-Actual/1000028917)
still displays **“Get Pricing & Availability”**, so write its whole-board
checkout as `P₄ₓ₆`, unknown. Eight feet is 2438.4 mm: `floor(2438.4/300)
= 8` is only a zero-kerf upper bound on 300-mm blanks. The cut plan must
allow saw kerfs, end trimming, defects, and a rip from the listed 3.562 ×
5.625-in actual section to the modeled 57.15 × 139.7-mm cross-section.
The 300-mm *used-stock allocation* might be `P₄ₓ₆ / usable blanks` only
after that plan and a credible use for every other blank; the first joint
still requires buying the whole board. No offcut credit is assigned.

One verifiable conditional tool lead is Home Depot's [Drill America 9/32-in ×
12-in extension bit, DWDA/CX129/32](https://www.homedepot.com/p/305284242)
at **$6.23 for one bit**. If that exact bit and reach prove suitable and none
is owned, the Home Depot hardware-plus-bit checkout becomes **$24.30 +
P₄ₓ₆** before all other charges. Its full $6.23 is a first-tool purchase,
not an automatic one-joint consumable allocation; bit life and reuse are
unknown. The final hole size, straight reach, power drill, 7/16-in head/nut
tools, clamps, saw/rip setup, blade wear, marking, and any protective finish
are not priced or verified. Do not infer the bit is a drilling instruction.

Work also includes at least one 300-mm crosscut blank and one width rip,
layout/fixturing, four aligned through-bores in the assembled members,
deburring/inspection, and four bolt-stack assemblies. Cutting from an 8-ft
board and transporting the block/rail/upright may add handling or trips;
shop access, labor time, local cutting fees, travel, tax, and delivery are
unknown. A cleat attached to a transport member changes the move plan and
must be checked against actual access. Thus the only numeric comparison here
is **listed hardware**: $4.04 allocated or $18.07 first checkout in the
same-store example, versus $4.77 allocated or $7.08 first checkout in the
mixed-store example. Neither is a completed joint or project total.

## Full-section overlap trial: not a zero-hardware alternative

The tested face-overlap moves the rail **139.7 mm** off its original
panel-support plane. The trial bolt's wood-only grip is **279.4 mm =
11.000 in**; its 284.4-mm CAD cylinder also includes the 5-mm exterior
diagnostic envelope. A nominal 12-in bolt would leave only **25.4 mm** beyond wood
before the same washer/nut/thread/tolerance allowances. No retail 12-in
bolt, bolt count/group, nut or bearing-washer specification has been
selected or priced for this pose. Its trial head/washer/tool conflicts with
the fixed lower panel. Both fixed service-rail panel screws lose their
original rail receiver in the modeled offset. The panel screws and their
axes stay fixed, so the overlap requires a positively attached **front
backer**, not a free or merely adjacent strip.

| Overlap cost line, same single joint | Nominal used cost | Minimum purchase outlay | What is missing |
| --- | ---: | ---: | --- |
| Overlap through-bolts, nuts, bearing washers | Unknown | Unknown | Bolt count, stack, grade/finish, length, unit/pack price |
| **Front backer stock, separately counted** | **Unknown (`B_stock`)** | **Unknown (`P_backer_stock`)** | Sized/graded piece, retail SKU and local board price |
| **Positive backer attachment, separately counted** | **Unknown (`B_attach`)** | **Unknown (`P_backer_attach`)** | Fastener layout, receiver and rating, retail SKU/pack price |
| Cuts, altered rail stock, extra transport/assembly work | Unknown | Unknown | Final geometry, cut list, workflow and prices |

Thus overlap's known priced subtotal is **none**, not `$0`. Its nominal
cost is `overlap bolt stack + B_stock + B_attach + other costs`.
Its cash outlay is `bolt packs + P_backer_stock + P_backer_attach + other purchases`.
The backer gets two explicit lines because its wood alone does
not restore the two screw receivers. The current model does not size it or
its attachment, so assigning either a 2×6 price or a hardware count would
fabricate a comparison. Retaining the original rail stock cost at `$0`
would also require a verified cut plan; no such credit is taken.

## Decision boundary

The 3/8-in cleat has a **$13.72 known single-item hardware illustration** and
an **$84.06 alternative pack-checkout illustration**. The separate 1/4-in
cleat examples above have **$18.07 same-store** or **$7.08 mixed-store**
listed hardware checkouts. None includes its unknown 4×6 purchase or proves
a suitable bolt stack. The separate Prime-Line/wide-washer lead is
$5.72 allocated or $49.91 first checkout, and its nominal rail stack
cannot seat under the assumed thread pattern. The overlap
has no defensible numeric total, and
its separate backer material/attachment and 12-in-class fastener stack are
unpriced. Consequently there is **no cost winner**. For either path,
installed tooling, taxes, shipping, ordinary cuts, discarded or shared
offcuts, stock/fastener quality checks, exact washer bearing, fastener
thread geometry, access, and all joint/frame limit states remain open.
Retail existence and arithmetic are not evidence of structural suitability
or a release to purchase, cut, or drill.
