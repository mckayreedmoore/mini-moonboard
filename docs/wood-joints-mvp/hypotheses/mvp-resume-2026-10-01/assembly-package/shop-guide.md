# Conditional shop and assembly guide

This guide describes handling and assembly for the current bolted wood-block lane. It is an
operations aid for recorded geometry, not a fabrication release, product selection, inspected build,
or climbing release. Use it with the [assembly and procurement reconciliation](README.md), the
[hardware engagement worksheet](hardware-engagement.md), the [longer-bolt added-occupancy
screen](hardware-length-fit.md), and the current [top-corner fit
worksheet](../top-corner-hardware/assembly-fit.md).

Read panel stations with the [four-upper-screw coordinate
overlay](../upper-corner-screw-layout/shop-addendum.md). It records the current analytical
layout; its stations are conditional and are not instructions to drill the preserved source solids.

## Parts and current layout

| Item | Quantity | Identity |
| --- | ---: | --- |
| Frame timber bodies | 20 | Separate members. |
| Connector blocks | 24 | Separate blocks; preserve names and orientation. |
| Timber blanks | 44 | 18 nominal 2×6, 10 nominal 4×6, 16 nominal 4×4. |
| Top outer cleats | 2 of the 24 blocks | Solid 4×6, each with 119.7 mm grain length. |
| Plywood bodies | 6 | Four main panels and two whole kickers. |
| Structural stacks | 104 | 92 candidate plus 12 retained frame stacks. |
| Nuts | 104 | One per structural bolt. |
| Separate washers | 208 | One under each bolt head and nut. |
| Panel/kicker screws | 66 | Hillman 42605: 48 main-panel, nine per kicker. |

The 44 blank identities include the two top cleats changed from 4×4 to 4×6. Four prepared section
rips remain in the 4×6 source class. Transport means individual bodies, not subassemblies. The six
panels are not six purchased sheets. Finished envelopes and planning masses are in the [assembly
package](README.md).

The former 144 Simpson SDS25112 screws and 24 ML24Z angles are absent from this lane. Do not add
them to this bill of materials or substitute them for the 66 Hillman screws. Hold T-nuts, mounted
holds, lights, and wires are separate from structural fastener counts.

Use the [preserved 66-axis receiver
inventory](../../current-panel-receiver-transfer-2026-10-01/inventory.md) for panel screw IDs and
its previous receiver assignments. That inventory records 58 retained and eight moved stations
relative to its source. The current [four-upper-screw overlay](../upper-corner-screw-layout/shop-addendum.md)
then retains 62 of those 66 stations and moves four upper screws upward; the two moved center
stations enter `base_rail_top`. These are successive comparisons with different reference layouts,
not competing totals. Four previously moved center-kicker axes still enter the center posts.
Do not use historical `inner_kicker_backer` names as current receivers. Use the [current
hardware coverage](../../../current-hardware-coverage.md) for frame axis IDs, and the [top-corner
correction summary](../top-corner-correction.md) for the eight proposed top axes. Modeled dimensions
are not bit instructions.

## Stock and conditional purchase list

Stock quantities reuse the replacement-aware nesting in the [assembly reconciliation](README.md):
3.2 mm timber kerf and 0, 10, or 20 mm end trim per stick. These are first-fit scenarios, not
optimized orders or stock-grade selections.

| Stock option | 2×6 sticks | 4×6 sticks | 4×4 sticks | Blanks placed |
| --- | ---: | ---: | ---: | ---: |
| 8 ft only | 6 | 3 | 1 | 39 of 44 |
| 10 ft only | 8 | 4 | 1 | 44 of 44 |
| 12 ft only | 6 | 4 | 1 | 44 of 44 |
| 16 ft only | 5 | 3 | 1 | 44 of 44 |
| Mixed 8, 10, 12, 16 ft | 9 | 4 | 1 | 44 of 44 |

The 8 ft scenario leaves five identified members unplaced. Larger and mixed scenarios place all
current blanks under the recorded method. Four 4×6 source blanks are section-ripped; do not count
them again as 4×4 stock.

For the six panel envelopes, geometry-only layouts require three 1219.2 × 2438.4 mm sheets or five
1219.2 × 1219.2 mm sheets. These counts identify no compatible purchased panel product, layup, or
released cutting plan. Two main-panel widths plus 3.175 mm kerf exactly use the 4×8 sheet length,
leaving no margin; 3.2 mm kerf does not fit that envelope.

That three-sheet scenario places main-panel X along the factory long direction.
If face grain follows that direction, its orientation differs from the analytical model's
assumed strong slope direction. Keep the count conditional; reconcile sheet placement
with the [material/axis note](../upper-corner-screw-layout/panel-material-fidelity.md)
before treating this as a compatible cutting plan.

The routes and dated listing amounts below are conditional, not selected or received products.
Quantities remain subject to each family’s fit requirements in [hardware
engagement](hardware-engagement.md).

| Family / duty | Need and named route | Listing amount or unresolved term |
| --- | --- | --- |
| Ordinary 1/4-20 | 44 K.L. Jack `25C600HCS5Z`; 100-piece box | $82.14; 56 surplus. |
| Shared 8 in 1/4-20 | 20 Lawson `FA21103` (12 side, 4 top rail, 4 inner knee/header); one 25-pack | Unpriced; five surplus. Do not add separate top-rail or knee packs. |
| Corrected top side | Four Bolt Depot `28650`; four `2583` nuts; eight `2995` washers | $12.20 + $0.32 + $0.48. Bolt profile not guaranteed. |
| Corrected top rail | Four bolts from shared Lawson pack; four `2569` nuts; eight `2994` washers | Nuts $0.28, washers $0.48. Motion `11706127` is an alternative. |
| Center principal | Four K.L. Jack `25C550HCS5Z`; 100-piece box | $30.59; 96 surplus. |
| Center post/header | Four conditional HiStrength `104-049`, 7.5 in | Part of eight-bolt $20.32 listing. |
| Center principal/header | Four 7.5 in bodies unresolved; proposed Lawson `FA21103` 8 in alternative | Geometry reconciliation required before alternative; no selection. |
| Remaining 1/4 in nuts/washers | 84 nuts of 100; 168 washers from two 100-piece packs | $4.71 + 2 × $3.47; fit remains conditional. |
| Outer posts | Four K.L. Jack `25C400HCS5Z`; listed pack of 100 | Reliable price absent; 96 surplus. |
| Center posts | Four 6 in options, including HiStrength `104-044` / `25C600HCS5P` | $1.23 displayed per item; payable pack basis unresolved. |
| Continuous knee side | Four Ro-Brand HC5127, 1/4-20 × 9.5 in lead | Profile, package quantity, and price unresolved. |
| Retained stacks | Eight 3/8 in and four 1/2 in bolts, 12 nuts, 24 washers | Dated [catalog increment](catalog-costs.md): $31.12 at displayed piece prices; profiles remain conditional. |
| Panel/kicker screws | 66 purchased Hillman 42605 | Purchase retained; current cost not assigned. |

The recorded earlier hypothetical recipe has a **$158.46 partial priced subtotal**, including eight
7.5 in center-header bolts. The center post/header four have a conditional 7.5 in route; the four
principal/header 7.5 in bodies remain unresolved. If those four later use Lawson 8 in bolts, the
shared pack grows from 20 to 24 of the same 25-pack, leaving one spare. That alternative is not in
the subtotal, and its complete-order price is not established. Lawson, outer-post, center-post,
knee-side, and retained hardware, lumber, eligible plywood, pads, holds, lighting/service parts,
freight, and tax remain unpriced or unresolved. No missing price is zero.

The October 2 [catalog update](catalog-costs.md) records the separate $31.12 retained-hardware
increment; the $158.46 historical subtotal above is preserved. Combining that increment once
gives $189.58 of priced terms before freight/tax, still an incomplete order. The same update
records a conditional quantity pool: if four center-post 6 in bolts use the exact ordinary
`25C600HCS5Z` SKU and meet the worksheet profile, the existing 100-piece box supplies 48 total
and leaves 52 spare. This quantity scenario selects no product and adds no second bolt box.

## Fastener counts and top corners

| Stack family | Bolts | Nuts | Washers | Duty |
| --- | ---: | ---: | ---: | --- |
| Candidate 1/4 in | 88 | 88 | 176 | Includes four corrected top-rail axes. |
| Candidate 5/16 in | 4 | 4 | 8 | Four corrected top-side axes. |
| Retained 3/8 in | 8 | 8 | 16 | Four front and four rear stacks. |
| Retained 1/2 in | 4 | 4 | 8 | Four leg stacks. |
| **Total** | **104** | **104** | **208** | One head washer and one nut washer per stack. |

At each proposed top corner, use two side stacks and two rail stacks. Side receiver order is 88.9 +
88.9 mm; rail order is 38.1 + 139.7 mm. Both grips are 177.8 mm. Side axes use 5/16-18 bolts; rail
axes use 1/4-20 bolts. Four side and four rail bolts across both corners are already included above.

Nominal 8 in length is 203.2 mm, distinct from 177.8 mm wood grip. Use the top-corner fit worksheet
for under-head length, `LB`, and full-form thread requirements; the named catalog lengths alone do
not guarantee delivered body or thread profile. Its three-pitch endpoint is a declared fit scenario,
not a universal shop rule.

The separate longer-bolt screen found no added-occupancy clash for four proposed 6 in center-post
shafts, four proposed 8 in center principal/header shafts, and four proposed 8 in inner knee/header
shafts. Their headward travel references become 150.749 mm, 201.549 mm, and 201.549 mm respectively.
That finite result checks only added tips and the additional headward shaft/head/washer sweep.
It does not select those lengths, verify delivered profiles, or establish full nut, thread,
tool or harness operations. Use its named source-pair results with the existing operation sequence.

Use one compatible washer below each head and nut. Conditional matched nut/washer routes are in the
hardware worksheet. The partial seat at `center_principal_right_2` has idealized bearing arithmetic
only; actual washer/nut footprint contact and metal transfer remain unqualified. Catalog washer
labels do not supply numeric yield minima.

## Forward assembly

Support each member independently while its connections are open. The modeled no-slip floor
condition is not assembly support; no temporary support fixture is specified here.

1. Stage the 20 frame timbers, 24 blocks, six panels, and axis-labeled hardware as separate
   identities. Keep the 66 Hillman screws apart from structural bolts and nuts.
2. Align and support frame members. Install the 12 retained stacks while receiver faces remain
   open. Keep each head washer, nut washer, and nut with its named axis.
3. Place each named block against its receivers. Install 92 candidate stacks before panels close
   access. Hand-start compatible nuts without pulling misaligned wood together; capture one
   completed stack at a time. Use the captured-pair insertion sequence below at the four named
   bottom-block axes where direct nut movement intersects adjacent blocks.
4. At each top corner, install two 5/16 in side bolts from side host into cleat, then two 1/4 in
   rail bolts from rail into cleat. Keep receiver order and thread families distinct. These are
   part of the 92 candidate bolts, not additional stacks.
5. Install panels after frame receivers and panel edge support are reconciled to current design
   records. Use the current receiver inventory for all 66 screw stations, including four
   center-kicker receiver changes.
6. Use purchased Lowe’s 755741 / Fas-n-Tite-Hillman 42605 screws: #10 × 2-1/2 in (63.5 mm), #2
   Phillips. With the owner-selected Kobalt 80277 / Lowe’s 1208451 #10 insert, drill a 1/8 in
   (3.175 mm) lead pilot through plywood into its intended receiver and a 3/8 in (9.525 mm)
   countersink at the plywood face so the flat head seats flush. Keep the screw hole a lead hole;
   do not drill a screw-shank clearance hole or insert pilot.
7. Trial pilot, countersink, and drive on an offcut of matching plywood into scrap DF-L before
   the 66 production holes. The root [shop checklist](../../../../floor-flush-shop-checklist.md)
   is cited here only for this exact Hillman tool policy; its baseline geometry and angle BOM do
   not apply. Do not substitute SDS25112 or size the Hillman pilot from CAD occupancy.
8. Feed the intact harness through recorded passages and seat LEDs after panel placement.
   Preserve source connections and routes. Reconcile 104 stacks, 66 screw stations, and 50
   transport bodies to one revision. No torque or preload is specified here.

The [purchase record](../../../../current-panel-screw-purchase.md) supplies the screw listing and
tool choice, not Hillman head, root, thread, withdrawal, lateral, or plywood pull-through design
values. The existing [panel-attachment worksheet](../panel-attachment/README.md) remains **HOLD**:
saved cases exceed declared unadjusted screw-head references, and no Hillman capacity is
established. This purchase and operation sequence do not establish panel-joint acceptance.

## Removal and member transport

Reverse the connection work while supporting members independently. Sort hardware by axis; do not
hang a released block or panel from a remaining fastener or harness.

1. Manage lights and the continuous harness before moving panels. The named spans
   `wire_010_A10_A11` and `wire_130_K10_K11` intersect modeled retained leg-bolt extraction.
   Stage those spans away before moving the four bolts. Saved checks do not prove physical
   harness staging or re-feeding. Do not cut, splice, or assume a connector isolates a panel.
2. Support panels and release 66 Hillman screws separately from bolts. Keep hold T-nuts with each
   panel. Under the retained sequence, stage each lower panel before its same-side kicker. Keep
   all six plywood bodies separate.
3. At each top corner, remove rail nuts and washers, withdraw both rail bolts headward, then
   release the side stacks. Real tool turning, counterhold, and roughly 0.20 m shaft extraction
   remain unobserved; straight approach is not a full tool-operation check.
4. Release the remaining 84 candidate stacks one named joint at a time, supporting adjoining
   members. Remove nuts and nut washers, withdraw bolts headward with their head washers, then
   separate each block. Four bottom-block axes use captured-nut paths instead of the intersecting
   direct nut slides:

| Axis | Captured-pair move in global X | Headward travel |
| --- | ---: | ---: |
| `bottom_center/clip_horizontal_bottom_left_2/rail_2` | −50.9623 mm | 151.368 mm |
| `bottom_center/clip_horizontal_bottom_right_1/rail_2` | +48.9623 mm | 151.368 mm |
| `bottom_outer/clip_horizontal_bottom_left_1/rail_2` | +53.9623 mm | 151.368 mm |
| `bottom_outer/clip_horizontal_bottom_right_2/rail_2` | −55.9623 mm | 151.368 mm |

Keep nut and washer captured at receiver while bolt unthreads and withdraws; move the pair
transversely as listed, then follow with the common 25 mm nutward move `(0, −16.0697, −19.1511) mm`.
Reverse these moves for insertion only under the same thread-compatible capture assumption. They do
not establish physical staging or thread fit.

5. After all 92 candidate stacks are released, support and remove 12 retained stacks. Saved
   headward travel is 99.568 mm for four front bolts, 112.268 mm for four rear bolts, and 200.025
   mm for four leg bolts, with no terminal allowance. Keep the two crossing harness spans clear
   during leg-bolt travel.
6. Separate the 20 frame timbers and 24 blocks individually. Keep each stack’s bolt, nut, two
   washers, and axis identity together. Inventory all 50 bodies and 104 stacks before transport;
   no connected transport subassembly is assumed.

The [operation order](../../../transport-operations.md), [retained access
record](../../../current-retained-access.md), [wire
sequence](../../../current-retained-wire-sequence.md), and [candidate access
screen](../../../current-access-screen.md) retain underlying path assumptions. Modeled sweeps do not
establish wrench reach, complete extraction, or reachable harness staging.

## Field record and limits

Keep Actual and Disposition cells blank until direct observation. Do not fill them from CAD, saved
model results, or catalog nominal dimensions. Record observed results against the affected step.
Stop that operation if a part conflicts with its named layout, a bolt/nut will not mate without
force, or a screw misses its receiver, splits wood, protrudes, or overdrives the face veneer.

| Observation | Actual | Disposition |
| --- | --- | --- |
| Hillman offcut pilot/countersink/drive trial | | |
| Delivered hardware fit or identified mismatch | | |
| Harness staging or observed route | | |

Panel attachment remains on its recorded reference HOLD. Bolt body end, full-form thread position,
matched nut engagement, actual bearing footprints, and supplier profile facts remain conditional.
The central partial washer seat does not demonstrate actual washer transfer. Real wrench access,
counterhold, shaft extraction, and harness staging remain unobserved.

### Engineering source pins

The [current analytical frame and fresh component replays](../README.md#current-analytical-working-model-for-the-mvp-goal)
use the four-upper-screw layout. The comparison retains bounded seating nonuniqueness and
`frame_state_accepted = false`. All six zero-gap states have rank 300; the six gap states have
bounded certificates with rank 296 or 297. The [current joint register](../upper-corner-screw-layout/joint-register.md)
maps all 104 bolts to this force source. Hashes below identify saved evidence; none is a physical observation.
Wood resistance references use conditional DF-L No. 2; stock sizing and nesting do not establish
delivered grade or the grade of prepared section rips. No-slip floor support remains an unverified
analytical assumption.

- `upper-corner-screw-layout/frame-250-attempt02/comparison.json` SHA-256:
  `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca`
- `upper-corner-screw-layout/frame-250-attempt02/response.npz` SHA-256:
  `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7`
- Preserved all-outer hardware comparison SHA-256
  `ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3`; response SHA-256
  `aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901`.
- Top-corner proposal SHA-256 `5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2`;
  catalog inputs SHA-256 `a2110d7580621dee92017403345f21c458729612547ac1f7b2eb8068d0c723c7`.

The [assembly reconciliation](README.md) records transport masses, stock scenarios, quantities, and
price scope. Read the [top-corner correction summary](../top-corner-correction.md) and preserved
[receiver inventory](../../current-panel-receiver-transfer-2026-10-01/inventory.md) with the
[four-axis overlay](../upper-corner-screw-layout/shop-addendum.md). All dimensions here describe saved
records; this guide update performs no new CAD, native solve or physical inspection.
