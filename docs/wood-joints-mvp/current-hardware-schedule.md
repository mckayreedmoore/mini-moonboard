# Current wood-joints hardware schedule and specification gaps

**Prepared:** 2026-09-24. **Status:** source-bound quantity and specification-gap
schedule for the current WJ24 development geometry. It is not a selected-SKU
bill of materials, purchase list, mechanics result, drilling instruction, or
fabrication release. No vendor lookup or purchase was made for this update.

## Geometry and count authority

The current candidate is `led-clearance-2x6-runner-seated-blocks-v1`. The
authoritative candidate-axis source for this schedule is the frozen
[attempt 02 grip-screen JSON](hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json),
SHA-256 `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`.
Its rendered [current grip-screen report](current-grip-screen.md) gives every
axis ID and every receiver interval. The source reports 92 candidate axes,
all with a 6.35 mm unthreaded CAD shaft envelope. Modeled under-head-to-tip
length is an occupancy envelope, not an order length or delivered shank.

The separate [retained frame-bolt review](current-frame-bolt-review.md) and
[retained frame-bolt audit](wj24-retained-frame-bolt-audit.md) reconcile all
12 inherited frame arrangements to the selected candidate's kerf-right
[connection axes](../floor-flush-construction-kerf-right/connection-axes.csv)
and [hardware schedule](../floor-flush-construction-kerf-right/bolt-hardware.csv).
Those are identity and model checks. Their current-candidate rechecks remain
required, and no physical product or delivered part is verified.

| Scope | Axes / assemblies | Bolts | Nuts | Separate washers | Treatment |
| --- | ---: | ---: | ---: | ---: | --- |
| Current WJ24 candidate | 92 | 92 | 92 | 184 | New development quantity screen; one head, shaft, two washer roles, and one nut per axis. |
| Retained starting frame | 12 | 12 | 12 | 24 | Kept as separate starting arrangements; not requalified by identity review. |
| Structural total represented | 104 | 104 | 104 | 208 | Quantity arithmetic only; stock ownership and fit are unknown. |
| Fixed Hillman panel/kicker policy | 66 screw axes | 66 screws | — | — | Separate purchased policy; receipt cost is not recorded. |
| Former ML24Z structural screws | 144 SDS25112 axes | 0 | — | — | Removed from WJ24; do not include in its BOM or cost. |

Each of the 92 latest candidate rows contains exactly one shaft envelope, one
integral head, one head-side washer role, one nut-side washer role, and one
nut envelope. Thus 460 modeled CAD roles correspond to 368 candidate pieces,
not 460 purchases. The earlier [WJ24 inventory](hypotheses/wj24-hardware-inventory/README.md)
and [development cost screen](wj24-development-costs.md) describe a prior
104-axis / 216-washer layout, including four special backer stacks. Those
quantities do not match the frozen 92-axis result and must not be carried
forward. The current 92-axis result has two washer roles per axis; no special
three-washer stack is present in this source.

## Current 92-axis dimensional groups

The identities below partition the 92 axes in the frozen JSON. The existing
partial-thread length comparison matches only 64 axes: 48 modeled at 152.4 mm
(6 in) and 16 at 203.2 mm (8 in). A match means only that the modeled
under-head-to-tip number equals a length class already present in source
records. It does not select that length for purchase or establish the
delivered thread transition. The other 28 axes have no exact existing
dimensional class in the current screen.

| Modeled under-head to tip | Modeled wood grip | Axis IDs / family pattern | Length-class status and purchase length |
| ---: | ---: | --- | --- |
| 101.600 mm | 76.200 mm × 4 | `knee_outer_{left,right}_post_{1,2}` | No exact comparator; purchase length unassigned. |
| 139.217 mm | 127 mm × 4; 122 mm × 4 | `center_post_{left,right}_{1,2}` (127); `center_principal_{left,right}_{1,2}` (122) | No exact comparator; purchase length unassigned. |
| 152.400 mm | 127 mm × 48 | `bottom_center` (8); `bottom_outer` rail axes (4); `left_service` lower-left rail (2), lower-left principal/rail (4), upper-left rail (2), upper-left principal/rail (4); `top_center` (8); `top_outer` rail axes (4); `wj04_g7` lower/upper principal/rail axes (8); `wj06_outer_pair` lower/upper rail axes (4). Full IDs are in the per-axis report. | Exact nominal 6 in dimensional comparator for 48 only; [Bolt Depot #10](https://boltdepot.com/Product-Details?product=10) is a dated low-carbon price comparison, not a selected product. |
| 179.217 mm | 167 mm × 4 | `center_post_header_{left,right}_{1,2}` | No exact comparator; purchase length unassigned. |
| 190.017 mm | 172.8 mm × 4 | `center_principal_header_{left,right}_{1,2}` | No exact comparator; purchase length unassigned. |
| 202.500 mm | 177.1 mm × 4 | `knee_outer_{left,right}_inner_header_{1,2}` | No exact comparator; purchase length unassigned. |
| 203.200 mm | 177.8 mm × 16 | `bottom_outer` side axes (4); `left_service` lower-left and upper-left side axes (4); `top_outer` side axes (4); `wj06_outer_pair` lower/upper side axes (4). Full IDs are in the per-axis report. | Exact nominal 8 in dimensional comparator for 16 only; [Bolt Depot #14](https://boltdepot.com/Product-Details?product=14) is a dated low-carbon price comparison, not a selected product. |
| 241.300 mm | 215.9 mm × 4 | `knee_outer_{left,right}_side_{1,2}` | No exact comparator; purchase length unassigned. |
| **92 total** |  |  | **64 exact nominal length comparators; 28 without an exact comparator. No candidate purchase length or SKU is selected.** |

The current geometry supersedes the earlier center-axis length assignments in
the [WJ24 length screen](wj24-bolt-length-screen.md) for any purchase decision:
the current report now shows 172.8 mm grip / 190.017 mm model length on the
four `center_principal_header` axes, and its 28 unmatched axes include all 16
current center axes. The prior 4.75-, 5.75-, and 7.5-inch assignments were
screened against a different inventory hash and must be recalculated against
this revision before reuse.

## Fastener facts and open specifications

For the current 92-axis group, the model supplies only a cylindrical 6.35 mm
shaft envelope and axial extents of the modeled hardware roles. It does not
contain thread geometry. The screen names a 1/4-20 thread only as a
dimensional comparator where an existing exact class applies; it does not
make 1/4-20 universal hardware selection. No exact bolt SKU, supplier, grade,
finish, thread class, delivered length, actual shank length, first full-form
thread, last thread scratch, thread end, nut fit, or resistance basis is
accepted for any of the 92 axes.

One nut and two washers per current axis is a provisional piece-count screen.
The current grip report is axial and does not certify actual nut across-flats,
thread class, grade, washer ID/OD, thickness, material, bearing support, or
washer steel capacity. A 1/4-20 Grade 5 hex nut and a 1/4-inch USS washer
appear in earlier price comparisons; those examples do not close the current
size, grade, fit, thread-engagement, or washer-support gates. In particular,
do not assign a single washer SKU or capacity across all 184 washer roles from
the price reference alone.

### Retained 12-axis schedule

These arrangements preserve their source ID, receiver pair, modeled nominal
diameter/length/grip, and starting stack geometry. The listed catalog parts
are references from the selected-baseline hardware research, not WJ24
purchase selections or inspected stock. The construction CSV leaves each
`shop_purchased_length_mm` blank and marks the entries provisional.

| Retained axis IDs | Count | Receivers | Modeled D × L / grip | Modeled washer pair and nut envelope | Dated catalog references | Unresolved for WJ24 |
| --- | ---: | --- | --- | --- | --- | --- |
| `lumber_leg_bolt_{left,right}_{1,2}` | 4 | `base_side` + `lumber_leg` | 12.7 × 203.2 / 177.8 mm | 2 × 34.925 mm OD, 3.175 mm washer thickness; 11.5316 mm nut height | [Bolt Depot #407](https://boltdepot.com/Product-Details?product=407), 1/2-13 × 8 in Grade 5; [#2573 nut](https://boltdepot.com/Product-Details?product=2573); [#15025 USS washers](https://boltdepot.com/Product-Details?product=15025). Source research dated 2026-09-13. | Delivered identity/ownership, grade evidence, actual shank/thread transition, dimensions, engagement, washer support, and fresh signed actions/capacity. The prior product screen notes the #2573 maximum nut height (11.3792 mm) is 0.1524 mm below the 11.5316 mm CAD nut envelope; recheck the actual stack. |
| `rail_front_bolt_{left,right}_{1,2}` | 4 | `base_post_outer` + `base_floor` | 9.525 × 101.6 / 76.2 mm | 2 × 25.4 mm OD, 2.032 mm washer thickness; 8.5598 mm nut height | [Bolt Depot #367](https://boltdepot.com/Product-Details?product=367), 3/8-16 × 4 in Grade 5; [#2571 nuts](https://boltdepot.com/Product-Details?product=2571); [#15023 USS washers](https://boltdepot.com/Product-Details?product=15023). Source research dated 2026-09-14. | Delivered identity/ownership, actual thread transition, wood/bolt fit, nut engagement, washer support, and fresh signed actions/capacity. |
| `rail_rear_bolt_{left,right}_{1,2}` | 4 | `base_floor` + `lumber_leg` | 9.525 × 114.3 / 88.9 mm | 2 × 25.4 mm OD, 2.032 mm washer thickness; 8.5598 mm nut height | [Bolt Depot #368](https://boltdepot.com/Product-Details?product=368), 3/8-16 × 4-1/2 in Grade 5; [#2571 nuts](https://boltdepot.com/Product-Details?product=2571); [#15023 USS washers](https://boltdepot.com/Product-Details?product=15023). Source research dated 2026-09-14. | In addition to the above: verify 50.8 mm remaining leg section at the actual station and actual delivered fit. |

The selected-baseline sources give these products as ordinary catalog
candidates and detailed dimensional studies; they do not establish that the
owner has the 12 parts, that the delivered lots match, or that they satisfy
the changed WJ24 load path. The [current frame review](current-frame-bolt-review.md)
records every retained axis as requiring a new structural recheck.

## Price-source coverage, not a current estimate

This schedule reuses only the dates and applicability stated in prior source
notes. The WJ-03 procurement pages were recorded on 2026-09-23; the
[WJ24 cost screen](wj24-development-costs.md) and
[2026-09-24 hardware budget](hardware-budget-2026-09-24.md) recorded retailer
prices on 2026-09-24. No availability, stock quantity, shipping, tax, or
present-day price was verified for this schedule.

| Current line | Price-source coverage | Quantity-priced comparison | Extended price reference | Limit |
| --- | --- | ---: | ---: | --- |
| Candidate bolts, 152.4 mm model length | [Bolt Depot #10](https://boltdepot.com/Product-Details?product=10), 1/4-20 × 6 in zinc-plated low-carbon Grade 2/A307A, $0.39 each on 2026-09-23 | 48 | $18.72 | Nominal length and price scale only; the cited listing's minimum thread length does not establish thread-start or maximum-thread location. Material class and delivered fit remain unresolved. |
| Candidate bolts, 203.2 mm model length | [Bolt Depot #14](https://boltdepot.com/Product-Details?product=14), 1/4-20 × 8 in zinc-plated low-carbon Grade 2/A307A, $0.90 each on 2026-09-23 | 16 | $14.40 | Nominal length and price scale only; the cited listing's minimum thread length does not establish thread-start or maximum-thread location. Not an accepted Grade 5 product. |
| Candidate bolts at the other six model lengths | No exact existing partial-thread dimensional class/product price assigned | 28 | — | No SKU, compatible length, or price inferred. |
| Candidate nuts | [Bolt Depot #2569](https://boltdepot.com/Product-Details?product=2569), 1/4-20 zinc-plated Grade 5, $0.07 each on 2026-09-24 | 92 | $6.44 | Price comparator only; thread fit and product selection unresolved. |
| Candidate washers | [Bolt Depot #15021](https://boltdepot.com/Product-Details?product=15021), 1/4-in zinc-plated Grade 5 USS washer, $0.09 each on 2026-09-24 | 184 | $16.56 at that unit rate | Arithmetic only; the modeled washer roles are not all dimensionally validated against this product. Do not treat the extension as a matched quantity or fit claim. |
| Retained 12 frame assemblies | Bolt/nut/washer comparators from 2026-09-24 hardware budget | 12 bolts + 12 nuts + 24 washers | $31.12 | Product references only; physical stock/ownership and suitability remain unknown. |
| Hillman 42605 screws | Purchase record identifies the chosen product for all 66 axes; receipt amount is absent | 66 already-purchased screws | — | No historic cost or replacement cost invented. |
| 144 SDS25112 screws | Removed from the WJ24 candidate | 0 WJ24 | — | Kept separate from the 66 Hillman policy. |

The dated line extensions are not a WJ24 subtotal. Combining price references
would imply fit and grade choices that this schedule does not make. The
earlier [development-cost screen](wj24-development-costs.md) subtotal of
$71.72 describes its 104-bolt / 216-washer inventory and is stale for this
frozen 92-axis layout. The earlier broad hardware allowance likewise uses a
predecessor length distribution (including four 292.1 mm envelopes); its
$130.64–178 range is not a current estimate. Timber, frame stock, machining,
tools, freight, tax, and received-part fit remain outside these references.

## Fixed panel/kicker and removed angle hardware policy

Keep the owner's 66 separate panel/kicker axes and purchased
[Hillman 42605 policy](../current-panel-screw-purchase.md): Lowe's item 755741,
#10 × 2-1/2 in (63.5 mm), ceramic-coated deck screw, with the recorded owner
lead-hole pilot plus panel-face countersink. The purchase record does not
contain its receipt cost or publish structural capacities; do not transfer
SPAX resistance, stiffness, or installation rules to Hillman. No axis change
or quantity change is authorized by this schedule.

The prior 24 ML24Z / 144 SDS25112 attachments were replaced in the WJ24 lane.
The 144 screws are not current candidate fasteners, do not count toward the
92 or 12 bolt stacks, and do not receive a cost allocation here. The 66
Hillman panel/kicker screws remain separate from both structural bolt groups.

## Open receiving and mechanics fields

Before any physical WJ24 hardware conclusion, populate only from applicable
product evidence and delivered measurements: SKU and thread designation;
bolt grade, finish, and material traceability; actual under-head length and
thread transition/usable thread bounds; nut size, grade, and functional
engagement; washer ID/OD/thickness/material and supported footprint; actual
wood grip and finished receiver; and each axis's signed demand and supported
resistance check. The 92-axis geometry screen and the retained-frame identity
audit supply no capacity or acceptance. No purchase length should be taken
from the modeled cylinder length.
