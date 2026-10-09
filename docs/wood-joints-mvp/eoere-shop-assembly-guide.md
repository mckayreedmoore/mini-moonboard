# Raised-rail Eoere shop and assembly guide

This is the nominal shop and operation packet for
`compact-floor-flush-eoere-bolted-development`, revision
`eoere-bottom-rail-tnut-clearance-v1`. The owner requests complete reporting
and instructions for the existing model, retaining reference exceedances and
unknown capacities. Physical testing and engineer approval are outside this
completion scope. Actual observations stay blank. This packet does not select
the candidate, establish complete joint strength or release fabrication or
climbing. Start with the [current summary](README.md) and its
[six-case numerical receipt](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/fixed-floor-numerical-mvp-v1.json).

## Packet and identities

The [raised-rail viewer](../../site/index.html?model=eoere-bolted-bottom-rail-development&view=rear)
and [occupied geometry](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-bottom-rail-v1.json)
identify the nominal parts. The shop tables below read those saved inputs;
they do not regenerate the frame or qualify delivered parts.

| Record | Use |
| --- | --- |
| [Members and stock datums](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/cut-datums.md) | Current timber identities, local frames, profiles, end planes, panel and receiver coordinates. |
| [Hardware and receiving](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/hardware.md) | All 100 physical stacks, nominal purchase recipes and dimensional receiving limits. |
| [200 access sides](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/access-sides.csv) | One head and one nut side per shaft; nominal directions and explicit unresolved tool/removal dispositions. |
| [Completion ledger](completion-ledger.md#build-package-completion) | Source hashes, reproduction, independent review, limitations and recovery. |

| Physical item | Count | Counting rule |
| --- | ---: | --- |
| Timber members | 22 | Includes the two exterior 2×6 cleats. |
| Plywood bodies | 6 | Four main panels and two whole kickers; 28 separate wood/panel bodies overall. |
| Eoere angles | 22 installed | Six four-packs supply 24, leaving two spare. |
| Through bolts | 100 | 84 angle shafts, four cleat/post shafts and twelve starting frame shafts. |
| Nuts / separate washers | 100 / 200 | One nut and one washer under each head and nut. |
| Hillman 42605 panel/kicker screws | 66 | Retained purchased screw policy; four lower axes move in this revision. |
| Service bodies | 132 LEDs, 142 T-nuts, 131 wires | Separate from structural fasteners. |

The 22 angles have 88 installed hole attachments. Four physical shafts are
shared by pairs of angles, leaving 84 angle shafts. Count each shared shaft
once. The 24 starting joint duties comprise 22 angle duties and two solid
cleat duties; a duty is not an extra fitting or bolt.

## Stock, panels and layout datums

The declared timber bolt-reference scenario is solid Douglas Fir–Larch
(DF-L) No. 2, specific gravity G=0.50, with the unadjusted CD1 reference.
It is a numerical material basis, not an observed lumber grade or complete
joint resistance. Received species, grade and moisture remain blank inputs.

Use each timber's named local frame rather than dimensions taken from a
perspective viewer. L follows its recorded grain axis; U and V complete the
orthogonal section frame. A point is `origin + L*eL + U*eU + V*eV`. Raw
profile vertices and outward-facing end-plane equations define raw cut
profiles; recesses, bores and service cuts are separate operations. A
normal-to-grain angle is not automatically a saw setting.

The retained rear recess is the source 1:12 taper, with its recorded mirrored
right-side offset. Preserve whole kickers and their seam profiles. The
thirteen-stick, 150-board-foot nesting scenario nominally accommodates the
two 289.7-mm cleats in runner offcuts. It is a stock-length scenario, not an
observed lumber order: its earlier tightest margin is 2.649 mm. Actual usable
length, section, grade, kerf, end trim and defects remain receiving inputs.
Individual transport envelopes are distinct from blank lengths and stock
orders.

| Nominal stock scenario | Length | Sticks |
| --- | ---: | ---: |
| 2×6 | 8 ft / 2438.4 mm | 6 |
| 2×6 | 10 ft / 3048 mm | 3 |
| 4×6 | 8 ft / 2438.4 mm | 2 |
| 4×6 | 10 ft / 3048 mm | 2 |
| Total | 150 nominal board feet | 13 |

This is the unchanged stock scenario in the
[preserved Eoere inventory](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/inventory-v2.json),
with 3.175-mm kerfs and 12.7-mm end allowances. Each nominal runner offcut
is 594.178517 mm before the cleat; one cleat plus its kerf needs 292.875 mm,
leaving 301.303517 mm afterward. The existing
end allowance is already charged, so it is not added again to that offcut.
No added stock purchase is inferred, and usable offcut/grade observations
remain blank. The older three-4×8-sheet scenario does not replace the owner's
already cut squares or establish their dimensions.

The owner reports Group 1 sanded A-C plywood, nominal 3/4 inch, already cut
into squares, with the original sheet's eight-foot direction horizontally
across the board. The saved panel mechanics use CAT 23/32 inch
(18.25625 mm); the separate nominal 3/4-inch check uses 19.05 mm. Neither
value is an observed thickness or actual cut-panel dimension. Keep the
factory direction separate from the panel's geometric upslope coordinate.
Do not substitute the selected baseline's cut sheets or move panel outlines.

Only the two bottom rails are raised: 30.625 mm along the climbing slope,
or world translation `[0, 19.685370547, 23.460111071]` mm. Their nominal
slope interval is 121.425–159.525 mm, giving 6.35 mm above the recorded
first-row T-nut service envelope. Four lower-edge Hillman stations and
sixteen bottom-angle stacks follow that move. Existing wire routes and
front-open cuts stay at their source endpoints. Lay out the revised holes
from raw profiles; translating an already machined member would also move
cuts that must stay fixed.

The cleat/post axes stay at the reviewed Z200 location. The Z180 alternative
is unadopted. The nominal minimum bore/screw gap at Z200 is 0.340625 mm;
this is not a usable fabrication-tolerance allowance. No general cut,
hole-center, angle-datum or accumulated assembly tolerance is established.
The source tables retain these missing tolerances explicitly rather than
borrowing the selected baseline's fixture limits.

## Holes and fasteners

The angle scenario is 88.9-mm legs and width, 6.35-mm working catalog
thickness, 10-mm factory holes and the far transverse pair on each flange.
The transverse pitch is 50.8 mm, axial pitch 41.275 mm and nominal far
station 65.0875 mm. These are catalog/model datums. Minimum metal thickness,
bend radius/thinning, absolute heel offsets and delivered hole tolerances
remain unknown. The inside-radius-equals-thickness scenario is described in
the [separate heel supplement](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/heel-assumptions-v1/nominal-scenario.md).

Receiver rows identify entry/exit coordinates for every saved wood bearing
occurrence. Occupied bore sizes, shaft circles, modeled screw diameters and
nominal shaft lengths are analysis envelopes. They are not a released bit
list, a delivered smooth-shank guarantee or permission to enlarge a factory
hole. Preserve each receiver, flange, head/nut direction and shared-axis
identity. A mismatch is recorded against that axis; forced alignment,
elongation, added spacers or a relocated hole do not preserve this model.

The unchanged purchased panel screw is Hillman 42605, #10 × 2½ inch
(63.5 mm), with a #2 Phillips drive and the owner-selected lead pilot plus
face countersink. The recorded Kobalt #10 tool policy uses a 1/8-inch
(3.175-mm) lead pilot and 3/8-inch (9.525-mm) face countersink. That policy
comes from the [screw purchase record](../current-panel-screw-purchase.md)
and [baseline tool checklist](../floor-flush-shop-checklist.md); their frame
geometry, angle counts and physical-trial requirements do not become this
packet's completion criteria. No screw-shank clearance hole or insert pilot
is adopted. The reported 9-mm head dimension is not a product resistance
rating. Heads, engagement and actual hole execution remain unobserved.

## Hardware receiving and cost

Use the source-bound [100-stack worksheet](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/bolt-stacks.csv)
to match each recipe and both washer roles. The specified Grade 5 reference,
matched nuts and catalog USS washers remain purchase/analysis assumptions;
the installed parts have not been observed. Partially threaded bolts are
the basis, with separately declared body/root reference regions.

For each delivered stack, measure under-head length L, receiver-plus-plate
stack S, both washer thicknesses, nut height and thread pitch. The recorded
minimum projection condition is
`L >= S + w_head + w_nut + h_nut + 2*pitch`. Check smooth body/runout reach,
usable full-form thread through the nut, free nut seating, washer support
and access separately. Nominal length alone satisfies none of those
additional conditions. No tightening torque or preload has been established.

The catalog tolerance box has 24 short comparisons: sixteen 3/8 × 4½-inch,
four 3/8 × 6-inch and four 1/2 × 8-inch stacks. At the maximum recorded
nut/washer stacks, their minimum delivered lengths are 112.268, 150.368 and
199.792492 mm respectively. These are receiving equations, not observed
rejects. Actual grip and hardware dimensions govern each row. Longer bolts
require their own seating and occupancy dispositions; they are not an
automatic substitute.

Planning mass is 218.912854 kg, including the 25-kg accessory allowance and
excluding pads. It uses nominal volumes, densities and drawing masses;
actual carried weights remain blank. The recorded full bolt/nut/washer
basket is $109.93 before freight and tax. Total planning cost is
`$109.93 + 6*C4 + U`, where C4 is the unobserved current four-pack angle
price and U contains unpriced lumber, panels, screws, service parts, pads,
holds and other items as applicable. Purchased panels/screws remain separate
from future spending. The October 8 seller lookup found no featured offer;
no current complete quote or zero-priced missing item follows.

## Nominal assembly order

This order organizes the recorded parts and access dependencies. Temporary
support, actual tools and continuous insertion/removal paths remain
unverified. The final no-slip floor idealization is not an assembly fixture.

1. Identify all 22 timbers, six panels, 22 angles and 100 physical stacks.
   Keep each bolt, nut and two washers with its axis label. Reconcile the
   receiving and datum rows before any operation that depends on them.
2. Support adjoining members independently and position the unloaded base,
   legs, posts and climbing-frame members from their named datums. Place the
   twelve starting frame stacks while both sides remain exposed. Their
   actual installation sequence is a recorded access disposition, not an
   inherited baseline pass.
3. At each lower exterior corner, position its 2×6 cleat above the runner.
   Two dedicated bolts connect cleat to outer post; two retained upper-angle
   side shafts also cross the cleat. Keep these four physical shafts and
   their receiver order distinct. No lower outside angle or alignment block
   is added. Stage cleat and side member before inserting their common
   upper-angle shafts (`eoere_bolt_067/071` left, `070/074` right).
4. Position each of the 22 angles against its named receivers, including the
   staged cleats. Stage both attached angles before inserting a shared
   shaft. Use all four far-pair attachments per angle, while counting shared
   shafts once. Match head and nut sides to the worksheet rather than
   reversing them to gain access.
5. Manage the intact harness through the retained front-open channels before
   panel closure. Switch power off; use only identified existing disconnects.
   No cutting, splicing, connector isolation, bend radius, slack or feed path
   is assumed. Record any obstruction while the panel-facing work is open.
6. Keep panel-facing work exposed until its structural stacks and receiving
   observations are reconciled. Plan kicker placement before the lower main
   panels so their nominal seam can engage; place upper panels afterward.
   Retain all 66 supported Hillman stations, including the four raised lower
   stations. Do not add the old and moved holes together.
7. Reconcile 100 bolts, 100 nuts, 200 washers, 22 angles, two cleats and 66
   panel screws with their axis/body identities. Hand-starting, seating and
   alignment observations stay separate from strength comparisons.

## Nominal dismantling and transport

Support each unloaded part before releasing its connections. This is a
dependency plan; no current swept-tool or continuous extraction pass is
claimed by the 200-side table.

1. Remove external loads and manage holds/hold bolts and services before
   moving panels. Power off and identify the harness staging route and any
   actual connector; the harness does not support a released panel.
2. Release panel screws with the supported upper panels first. The preserved
   thin-v4 method releases the lower-panel/kicker seam by a small upslope
   move before outward withdrawal, then removes the kickers. Use that order
   as a planning dependency; its old 0.5-mm/100-mm swept-corridor checks do
   not qualify the current physical operation. Keep T-nuts with their panels.
3. Lift the harness from its front-open channels before shaft travel where
   needed. Existing wire routes are retained, but actual harness bodies,
   release strokes and staging space are unverified.
4. Work one supported joint at a time. Release each nut and nut washer,
   then plan headward bolt/head-washer withdrawal along that axis. Shared
   shafts release both attached angles; retain support until all of a
   fitting's own shafts are free. The old B103 beam-first dependency and
   block-candidate captured-nut routes are not Eoere instructions.
5. Release the two cleats only after their dedicated and shared-angle shafts
   are free. Release the twelve starting stacks while their two receiver
   members are independently supported. Record unresolved access instead
   of presuming removal by reversing a nominal installed pose.
6. Separate 22 timbers, six panels and 22 angles individually. Keep hardware
   grouped by axis and account for all 100 stacks. No connected transport
   subassembly or actual carried mass is established.

## Blank receiving and operation record

Actual and Disposition cells are intentionally blank. A measured mismatch,
unsupported seat, missed receiver, damaged passage or inaccessible required
operation stops that affected operation; it does not erase the numerical
packet's exceedances or prove a different design. Record departures against
the current part/axis and its source row.

| Required observation or unresolved input | Actual | Disposition |
| --- | --- | --- |
| Lumber identity, usable blank, grade, section, end/profile datums | | |
| Actual panel dimensions, thickness and factory direction | | |
| Angle minimum thickness, inside/outside bend, thinning, heel/hole datums | | |
| Each stack's length, body/runout, full threads, nut and washer dimensions | | |
| Finished receiver centers/diameters and available tolerance clearance | | |
| Full washer support and intended receiver/flange contacts | | |
| Each of 200 head/nut tool sides, counterhold and removal path | | |
| Temporary support and unloaded assembly/removal handling | | |
| Harness staging, connector identity and feed route | | |
| Actual weights, supplier packs, prices, freight and tax | | |

Numerical evaluation remains complete under its recorded loads and fixed
rear-leg no-slip support scenario. Panel/screw exceedances, formed-heel
applicability, complete joint resistance and physical operation remain
explicit limitations. This reporting scope commissions no additional solve,
panel remedy, physical test or external approval.
