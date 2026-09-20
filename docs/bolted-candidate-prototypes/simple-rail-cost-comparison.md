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

The cleat has a **$13.72 known single-item hardware illustration** and a
**$84.06 alternative pack-checkout illustration**; neither includes its
unknown 4×6 purchase. The overlap has no defensible numeric total, and
its separate backer material/attachment and 12-in-class fastener stack are
unpriced. Consequently there is **no cost winner**. For either path,
installed tooling, taxes, shipping, ordinary cuts, discarded or shared
offcuts, stock/fastener quality checks, exact washer bearing, fastener
thread geometry, access, and all joint/frame limit states remain open.
Retail existence and arithmetic are not evidence of structural suitability
or a release to purchase, cut, or drill.
