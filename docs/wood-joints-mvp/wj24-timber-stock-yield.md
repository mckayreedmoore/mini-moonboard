# WJ24 timber stock and yield screen

**Status: developmental stock-planning screen, 2026-09-24.** This records the
wood blanks represented by the unaccepted WJ24 integrated hypothesis and
tests a few bounded crosscut-yield assumptions. It is not a lumber order, cut
list, fabrication release, fit confirmation, or structural acceptance.

The source inventory counts 28 connector blanks for 24 target duties. The
dimensions below come from
[`inventory.json`](hypotheses/wj24-hardware-inventory/inventory.json); the
integrated host and receiver changes come from
[`composition.json`](hypotheses/wj24-integrated-static/composition.json).
The separate
[part-count review](hypotheses/part-count-and-merge-review.md) describes the
28-piece full-layout projection and its remaining development gates.

## Modeled blank schedule

Dimensions are in millimetres. For each row, the listed grain axis follows the
long dimension of the stock blank. A grain-axis label retains the source
coordinate system used by the inventory. The angled cuts, bevels, counterbores,
bores, and receiver cuts are model operations only.

| Quantity | Connector family | Stock blank dimensions | Grain axis and modeled operations |
| ---: | --- | --- | --- |
| 16 | Bottom, outer, left-service, top, WJ04, and WJ06 cleats | 88.9 × 88.9 × 119.7 | Source-local N. One WJ04 blank carries a modeled G7 crosscut to 86.9 mm grain length. |
| 2 | WJ05 center-post cleats | 88.9 × 88.9 × 128.9 | Global Z; crosscut blank and through-bolt bores. |
| 2 | WJ05 center-principal cleats | 88.9 × 88.9 × 156.596 | Source-local T, parallel to the center principal. Modeled angled ends leave 82 mm finished grain length, with an open wire-relief cut and through-bolt bores. |
| 2 | WJ05 inner-kicker backers | 88.9 × 88.9 × 238.9 | Global Z; modeled through-bolt paths, bottom counterbores, and two redirected fixed panel-screw receiver cuts per backer. |
| 2 | WJ03 rear bridges | 383.2 × 38.1 × 88.9 | Global X; crosscut blank and rear bevel. The 383.2 mm axis is the stock/grain length. |
| 2 | WJ03 under-header links | 185.2 × 88.9 × 88.9 | Global X; crosscut to the modeled blank length. |
| 2 | WJ03 spines | 88.9 × 139.7 × 269.95 | Global Z; crosscut blank and rear bevel. The 269.95 mm axis is the stock/grain length. |
| **28** | **Total** |  | **24 nominal 4×4 blanks, two nominal 2×4 blanks, and two nominal 4×6 blanks.** |

The 24 full-section 4×4 blanks comprise 16 × 119.7 mm, two × 128.9 mm,
two × 156.595957 mm, two × 238.9 mm, and two × 185.2 mm. Their combined
crosscut length is 3,334.391914 mm. This groups the 185.2 mm WJ03 links with
the other full-section 4×4 stock; it does not splice or laminate members.

## Bounded crosscut scenarios

These are arithmetic scenarios, not statements about stocked retail lengths.
For a stick holding `n` blanks, the screen uses:

`blank lengths + (one 3.175 mm kerf per blank) + end trim allowance`

The base case assumes 3.175 mm (1/8 in) saw kerf, one 25.4 mm (1 in) end trim
per purchased stick, and one crosscut per blank. It does not include a defect
allowance, planing, section cleanup, or fit tolerance. A two-end-trim
sensitivity adds another 25.4 mm per stick.

| Stock section and allocation | Blank length total | Base-case consumed length | Example nominal stock scenario | Arithmetic residual |
| --- | ---: | ---: | --- | ---: |
| 4×4: all 24 blanks | 3,334.392 mm | 3,435.992 mm | One 12 ft (3,657.6 mm) stick | 221.608 mm |
| 4×4: all 24 blanks | 3,334.392 mm | 3,435.992 mm | One 10 ft (3,048 mm) stick | Short by 387.992 mm |
| 4×4: all 24 blanks | 3,334.392 mm | 3,461.392 mm with trim at both ends | One 12 ft (3,657.6 mm) stick | 196.208 mm |
| 2×4: two 383.2 mm blanks | 766.400 mm | 798.150 mm | One 8 ft (2,438.4 mm) stick | 1,640.250 mm |
| 4×6: two 269.95 mm blanks | 539.900 mm | 571.650 mm | One 8 ft (2,438.4 mm) stick | 1,866.750 mm |

The 4×4 case shows one possible way to avoid buying two short sticks: all 24
modeled blanks fit the arithmetic length of one 12 ft stick under both stated
trim cases. A 10 ft stick does not fit the complete 4×4 set. As a two-stick
8 ft alternative, one theoretical partition puts eight 119.7 mm cleats, both
128.9 mm center-post cleats, both 238.9 mm backers, one 185.2 mm link, and one
156.595957 mm principal cleat on the first stick. Those 14 blanks consume
2,104.846 mm with the base kerf and trim assumptions. The other ten blanks
consume 1,356.546 mm on the second stick. The combined arithmetic remnant is
1,415.408 mm; the first stick has about 333.554 mm remaining and the second
about 1,081.854 mm. This is only an arithmetic packing check; it does not
account for defects, actual stock length, or shop handling.

The scenarios treat modeled grain length as stock length and preserve each
full-section stock class. They do not authorize ripping, laminating, splicing,
or selecting a substitute section. The inventory labels the WJ03 cutoff models
as nominal solid-sawn DF-L No. 2; for the cleat and backer groups it calls
delivered grade unverified. No delivered stock, actual dimensions, grade,
grain, moisture, defect condition, usable yield, or vendor availability has
been observed. None of the residuals is an approved usable offcut.

## Existing member changes represented by WJ24

The integrated composition rebuilds 16 source host members around the
candidate connector and bolt geometry: `base_header`; `base_post_center_left`
and `base_post_center_right`; `base_post_outer_left` and `base_post_outer_right`;
`base_principal_center_left` and `base_principal_center_right`;
`base_rail_bottom_left` and `base_rail_bottom_right`;
`base_rail_service_lower_left` and `base_rail_service_lower_right`;
`base_rail_service_upper_left` and `base_rail_service_upper_right`;
`base_rail_top`; and `base_side_left` and `base_side_right`.

In the source geometry, the 24 legacy angle duties carry 144 SDS-axis cutter
operations. WJ24 removes those modeled cutters and replaces the 24 duties with
28 solid-stock pieces and 104 candidate through-bolt axes. The 104-axis count
is a geometry/hardware screen; it is not a drilling schedule, selected bolt
length list, capacity result, or proof of complete-joint behavior. Existing
frame-bolt arrangements (12) and the fixed panel/kicker screw axes (66) remain
separate obligations in the composition.

Four of the fixed panel/kicker receiver cuts are assigned to the two new WJ05
backers, two per backer. The corresponding receiver cuts are removed from the
center posts in the modeled composition. Five formerly separate receiver
overlays are integrated into host solids: `base_rail_bottom_left`,
`base_rail_bottom_right`, `base_rail_service_lower_left`,
`base_rail_service_upper_left`, and `base_rail_top`. These are source-bound
geometry changes only; they do not establish field modification instructions
or authorize cutting.

The composition remains an unaccepted integrated hypothesis. Its recorded
gates leave complete static-scene diagnosis, clearance/access, complete-joint
acceptance, capacity, installation, fabrication, and structural release
unestablished. Stock selection, grades, actual host dimensions, final bore
maps, service/tool access, and all physical cuts remain unverified. Do not use
this screen to purchase lumber, drill, cut, or transfer acceptance from the
selected angle-frame candidate.
