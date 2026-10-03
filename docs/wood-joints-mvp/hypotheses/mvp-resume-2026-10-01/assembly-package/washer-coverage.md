# Washer evidence coverage: 104 stacks, 208 endpoints

The **eight top-rail washer positions have completed all 48 requested retail
plate/contact states and their bounded nominal installation/removal fit**.
Those results cover four bolts, two washers per bolt and six load cases. They
do not qualify the other 200 washer positions or establish a delivered-product
capacity. The full washer census is complete; the former eight-endpoint
service reference gap is now filled with the specific limits below.

This report reads saved records only. It adds no geometry, mechanics run,
capacity, release gate or physical observation. The completed
[top-washer fit note](top-washer-fit.md) and [current working order](hardware-engagement.md#working-order-export)
bind the eight retail replacements. These replace eight existing washers: the total
remains **208**, not 216. The 66 Hillman panel/kicker screws are separate.

## Frozen inventory and force scope

The [hardware worksheet](hardware-engagement.md)'s saved CSV contains exactly
104 unique axes in fourteen families: eleven candidate families and three
retained families. Its axis set matches the saved working-joint register.
Every stack has one head washer and one nut washer. A continuous three-receiver
knee bolt has no middle washer or separate middle axial tie.

The register retains six cases: `a12-rear`, `a12-forward`, `a12-left`,
`k12-right`, `k12-rear` and `a1-rear`. It uses the frozen current100 frame
comparison `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca`
and response `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7`.
Eight top axes use their first-order allocation, eight bottom axes use their
first-order allocation, four continuous knee axes use contact-entry records,
and 84 axes retain the original integrated allocation. Original forces are
history where a corrected allocation exists. There is no washer-compliance
feedback into the frame or transfer to a different lever case.

In this report, an endpoint is `axis_id/head` or `axis_id/nut`, a reporting
suffix rather than a new source axis. The CSV's
`ordered_members_head_to_nut` identifies the physical receiver: the first
member is the head seat and the last member is the nut seat.

| Exact family ID | Bolts | Washer endpoints | Evidence partition |
| --- | ---: | ---: | --- |
| `candidate_ordinary_48` | 44 | 88 | B: 8; R: 76; V: 4 |
| `candidate_side_16` | 12 | 24 | B: 8; R: 12; V: 4 |
| `candidate_top_rail_quarter_8in_4` | 4 | 8 | T: 8 |
| `candidate_top_side_5_16_4` | 4 | 8 | S: 8 |
| `candidate_outer_post_4` | 4 | 8 | R: 8 |
| `candidate_center_post_4` | 4 | 8 | R: 8 |
| `candidate_center_principal_4` | 4 | 8 | R: 7; C: 1 |
| `candidate_center_post_header_4` | 4 | 8 | R: 8 |
| `candidate_center_principal_header_4` | 4 | 8 | R: 8 |
| `candidate_knee_inner_header_4` | 4 | 8 | R: 8 |
| `candidate_knee_side_4` | 4 | 8 | K: 8 |
| `retained_rail_front_4` | 4 | 8 | F: 8 |
| `retained_rail_rear_4` | 4 | 8 | F: 8 |
| `retained_lumber_leg_4` | 4 | 8 | F: 8 |
| **Total** | **104** | **208** | **T8 + S8 + B16 + K8 + F24 + R135 + V8 + C1** |

The `_48` and `_16` family IDs are preserved source names; their present
counts are 44 and 12 bolts. Across all six cases there are 1,248 endpoint
action records, derived from 624 bolt states. That is not a count of 1,248
washer-metal solutions.

## What the completed evidence establishes

| Class | Endpoints / case-end states | Applicable saved evidence and limit |
| --- | ---: | --- |
| **T: retail top rail** | 8 / 48 | [Retail suite](../upper-corner-screw-layout/retail-washer-suite.md): all 48 ends and one coupon complete, no end failures. Saved nominal exterior lands support the declared concentric annuli. Maximum sampled stress proxy is 207.205343 MPa, index 0.828821 against **assumed** Fy 250 MPa. [Fit](top-washer-fit.md) is complete: 37,352 pairs, zero overlaps or undecided pairs. It establishes nominal enclosure separation, not actual tools, turning, loaded fit or a manufacturer rating. |
| **S: top side** | 8 / 48 | [Current component replay](../upper-corner-screw-layout/corner-first-order-components.md) includes the same-state tension and supported **cleat** mean-seat comparison. Current end contact fields exist in the first-order packet. There is no current end-specific flexible-washer metal result for these eight positions; old integrated-allocation strip results do not supply one. |
| **B: bottom outer** | 16 / 96 | [Current bottom replay](../upper-corner-screw-layout/bottom-corner-components.md) retains per-end supported geometry, the axial-only radial-strip calculation and current mean-seat comparisons; maximum mean index is 0.229340. K20 contact fields remain separate. Required strip stress is a demand, not a product capacity or a solution of end-moment washer flexure. |
| **K: continuous knee outer ends** | 8 / 48 | [Contact-entry suite](../upper-corner-screw-layout/knee-contact-entry.md) completes all 24 three-receiver bolt states with both external annular pressure/moment fields. It supplies no flexible-washer metal resistance. Sampled side-2 pressures exceed the existing **mean** Fc-perpendicular reference while mean indices remain 0.349209/0.361594; no adopted pointwise failure criterion follows from that comparison. |
| **F: retained stacks** | 24 / 144 | [Fresh retained comparisons](../upper-corner-screw-layout/bolted-replay.md#retained-pairs-and-washer-families) and saved nominal support cover every retained seat. Current ideal pressure/reference maxima are 0.208053 for 3/8-inch and 0.264300 for 1/2-inch washers. Geometry probes establish nominal annulus support, not loaded shift/tilt, actual supported pressure, head/nut transfer or washer-metal capacity. |
| **R: other candidate full-annulus references** | 135 / 810 | The current `remaining-attempt02/washer-reference-states.csv` supplies six-case ideal `T/A` references with full-annulus applicability true for these exact ends. Actual supported pressure and washer-metal resistance fields are blank. Header-specific evidence additionally covers twelve of these seats; it is not evidence for both ends of every header bolt. |
| **V: lower-left outer service** | 8 / 48 | The completed [service washer comparison](../upper-corner-screw-layout/lower-service-washers.md) joins all current simultaneous ties to the eight unchanged supported seats. All 48 annular wood-bearing references are applicable; maximum ideal pressure/reference is **0.052459 MPa / 0.012174**, K12-right `lower_rail_1`, simultaneous **11.206614 N** tension. Actual pressure and washer-metal resistance remain null. These axes remain absent from the original remaining CSV; the new leaf fills that exact gap. |
| **C: central partial nut seat** | 1 / 6 | [Central transfer](../upper-corner-screw-layout/central-seat-transfer.md) supplies a completed, signed static trial on the supported 10/8.3058-mm ring, with the unsupported crescent unloaded. Peak demand is 22.952333 N and hypothetical yield threshold 0.942288 MPa. This is a conditional plastic equilibrium route, not an elastic stress result, actual yield guarantee or full-annulus mean comparison. |

The 92-axis remaining washer CSV includes the bottom and continuous knee
source allocations but omits the four V service axes and all eight top axes.
Filtering it to unchanged candidate allocations leaves 68 axes: 135 full
annulus endpoints and the single partial endpoint, each in six cases. Using
the entire CSV as current coverage would both inherit superseded forces and
miss V. The fresh retained packet supplies the appropriate F comparison.

The [header map](../upper-corner-screw-layout/header-traction-map.md) supports
only these twelve `base_header` seats: the four `center_post_header` heads,
four `center_principal_header` nuts, and each side's `inner_header_1` head and
`inner_header_2` nut. It records a uniform concentric annulus hypothesis and
signed boundary balance, not flexible-washer stress or delivered capacity.

## Exact endpoint map, including every end outside the retail suite

Brace notation expands the listed literal alternatives. Except for the C
exception, both `/head` and `/nut` are included for each listed axis.
The following aliases abbreviate existing axis prefixes only:

```text
TL = top_outer/clip_single_top_left_1
TR = top_outer/clip_single_top_right_2
BL = bottom_outer/clip_horizontal_bottom_left_1
BR = bottom_outer/clip_horizontal_bottom_right_2
LS = left_service/left_service_mirrored_inner_outer_hypothesis
G7 = wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis
RO = wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis
```

| Exact axis set | Axes | End class |
| --- | ---: | --- |
| `{TL,TR}/{rail_1,rail_2}` | 4 | T: head on `base_rail_top`, nut on the same-side `top_outer_*_cleat` |
| `{TL,TR}/{side_1,side_2}` | 4 | S: head on same-side `base_side_*`, nut on same-side top cleat |
| `{BL,BR}/{rail_1,rail_2,side_1,side_2}` | 8 | B |
| `bottom_center/clip_horizontal_bottom_left_2/{principal_1,principal_2,rail_1,rail_2}` | 4 | R |
| `bottom_center/clip_horizontal_bottom_right_1/{principal_1,principal_2,rail_1,rail_2}` | 4 | R |
| `LS/clip_horizontal_lower_left_1/{lower_rail_1,lower_rail_2,lower_side_1,lower_side_2}` | 4 | V |
| `LS/clip_horizontal_lower_left_2/{lower_principal_1,lower_principal_2,lower_rail_1,lower_rail_2}` | 4 | R |
| `LS/clip_horizontal_upper_left_1/{upper_rail_1,upper_rail_2,upper_side_1,upper_side_2}` | 4 | R |
| `LS/clip_horizontal_upper_left_2/{upper_principal_1,upper_principal_2,upper_rail_1,upper_rail_2}` | 4 | R |
| `top_center/clip_split_top_center_{left,right}/{principal_1,principal_2,rail_1,rail_2}` | 8 | R |
| `G7/{lower_principal_1,lower_principal_2,lower_rail_1,lower_rail_2,upper_principal_1,upper_principal_2,upper_rail_1,upper_rail_2}` | 8 | R |
| `RO/{lower_rail_1,lower_rail_2,lower_side_1,lower_side_2,upper_rail_1,upper_rail_2,upper_side_1,upper_side_2}` | 8 | R |
| `knee_outer_{left,right}_post_{1,2}` | 4 | R |
| `center_post_{left,right}_{1,2}` | 4 | R |
| `center_principal_{left,right}_{1,2}` | 4 | R for seven ends; C only at `center_principal_right_2/nut` on `base_principal_center_right` |
| `center_post_header_{left,right}_{1,2}` | 4 | R; header-specific support only at the head |
| `center_principal_header_{left,right}_{1,2}` | 4 | R; header-specific support only at the nut |
| `knee_outer_{left,right}_inner_header_{1,2}` | 4 | R; header-specific support at `_1/head` and `_2/nut` |
| `knee_outer_{left,right}_side_{1,2}` | 4 | K: head on outer spine, nut on inner frame block; no middle washer |
| `rail_front_bolt_{left,right}_{1,2}` | 4 | F: head on outer post, nut on floor member |
| `rail_rear_bolt_{left,right}_{1,2}` | 4 | F: head on floor member, nut on leg |
| `lumber_leg_bolt_{left,right}_{1,2}` | 4 | F: head on side member, nut on leg |
| **Total** | **104** | **208 separate endpoints** |

Thus the eight T positions have a current flexible-plate/contact result. The
named S/B/K/F/R/V positions, totalling **199**, lack that result; C has the
different static trial. This is a method applicability boundary, not evidence
that 200 washers failed or a requirement for 200 new models. Mean wood-seat
references, nominal support, washer-metal stress and product resistance are
different evidence and remain separate.

## Product conditions and finite remaining decisions

The [product investigation](../upper-corner-screw-layout/washer-product-basis.md)
and [bearing-face worksheet](bearing-face-basis.md) identify exact limitations.
No bolt grade or nut flats establish a numerical washer yield or the actual
flat pressing footprint. Current conditional order routes are 168 K.L. Jack
`25NWUS`, eight Hillman `885522` top-rail washers, eight `2995` top-side
washers, sixteen `15023` retained 3/8-inch washers and eight `15025` retained
1/2-inch washers. Attempt03 replaces the earlier eight `2994` roles and
retains the original order attempts as history.

For T, the calculation fixes ID 8.3058 mm, OD 25.4 mm, thickness 2.5 mm,
Fy 250 MPa and a concentric 5-mm pressing radius. The retail listing supports
a 2.5-mm nominal thickness but also has conflicting inch thickness fields;
its actual bore, numerical yield and pressing footprint are not guaranteed
by that calculation. Its 0.828821 index is against assumed yield, not a
manufacturer rating or a delivered-product safety factor. No full nut-turning,
tool sequence or body/thread acceptance is transferred from the fit screen.

For C, the supported ring trial needs a centered, flat nut land containing
that ring and a declared ductile yield bound covering its trial stress.
The named nut/washer catalog dimensions do not establish those facts.
The unsupported crescent is already excluded; no automatic bridging-model
prerequisite follows from this saved centered route.

The immediate finite handoff is:

1. Preserve the completed T suite, fit and attempt03 working order. Eight
   replacements keep the total at 208; actual product conformity is open.
2. Preserve the completed V comparison: eight ends in six cases using the
   saved simultaneous service ties and applicable catalog annuli. Parent
   execution and source/output bindings are recorded in its leaf. No new
   force model or product capacity is assigned.
3. Keep the named method/product conditions with their affected endpoints.
   S has current end actions but no current end-specific metal result; B has
   an axial-only strip demand; K has annular contact fields; F/R have nominal
   support or ideal pressure references; C has its static trial. The existing
   evidence does not establish a universal washer-metal pass. Any further
   calculation must answer the parent's concrete criterion for that end,
   rather than repeat force comparisons or require a generic new study.

Actual dimensions, material, seating, offsets and hardware inspection remain
unobserved. This report fills no builder Actual/Disposition cells.

## Engineering appendix: exact saved inputs

Paths are relative to this folder. Hashes bind the read-only census and saved
results, including ignored local evidence. No producer was executed for this
report and no raw output was created.

| Saved artifact | SHA-256 |
| --- | --- |
| `rawlocal/hardware-engagement/hardware-engagement.json` | `93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a` |
| `rawlocal/hardware-engagement/hardware-engagement-axes.csv` | `9fd9f2f70dbaf347bf174925f21cc3d589c2640a7b42501e3b81f4533ab42cac` |
| `../upper-corner-screw-layout/rawlocal/working-joint-register/attempt03/register.json` | `c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c` |
| `../upper-corner-screw-layout/rawlocal/retail-washer-suite/attempt01-fine/checks.json` | `3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74` |
| `rawlocal/top-washer-fit/run-attempt01/result.json` | `bc1bbfd01d6c002ffc7a9da4b14b44e47bb98c4809ef5059c7b3e10bddd1d797` |
| `rawlocal/top-washer-fit/run-attempt01/receipt.json` | `eb40764257349f6d24472c71278e990195d583c4de02e7a10909c184d583de89` |
| `../upper-corner-screw-layout/rawlocal/corner-first-order-components/attempt01/checks.json` | `f220673994b6a6c5b6bc0afd104becd61b5bb68f5e22bc700ed07b901b94525c` |
| `../upper-corner-screw-layout/rawlocal/bottom-corner-components/attempt01/checks.json` | `39e698d7ffec6646e2295f5ce96be0764ea8fbe6654ed3b0e881040b410bcc95` |
| `../upper-corner-screw-layout/rawlocal/knee-contact-entry/suite-attempt01/suite.json` | `b707952e5ad740ad2ebc0306bce17a37e4718e88c1164cba568d9a39a6e8b79a` |
| `../retained-washer-attempt02/checks.json` | `f23e2f0c9c1b32aa37f53416de95f7ed97257e704b638a6f94b1d043aec1420b` |
| `../retained-washer-support-attempt02/support.json` | `72ecad11051f7a72695f83561bb12503bfd79a44d3c3f6eeac2de476e3bc3448` |
| `../upper-corner-screw-layout/bolted-replay-results/remaining-attempt02/washer-reference-states.csv` | `43da5dab2bc0ed8761959767aecec466a645a3832509c7162e494cc4da17f35b` |
| `../service-joint-current-attempt03/four-screw-250-attempt03/result.json` | `850a31de41efc8e710cb45660f9822852469303e0e391fb70ed325977558293c` |
| `../upper-corner-screw-layout/rawlocal/central-seat-transfer/preparation-attempt01/contract.json` | `e430c138f0e1fb4eacda278fa535d3e14400fcff3514f4a81d3a5f7fc3ac6646` |
| `../upper-corner-screw-layout/rawlocal/central-seat-transfer/coupon-attempt01/coupon.json` | `bdc35b60ca03039f6e5acad8c5c81784086368a3472183ae7515f66335fe41bb` |
| `../upper-corner-screw-layout/rawlocal/header-traction-map/attempt01/result.json` | `39d63b41dc495659b02cb4ff4fb638a19a491bc09e6ea3fd76a70314db08a837` |
| `rawlocal/working-order/attempt02/working-order.json` | `3ba75dad67a22e621ce49572cf8fd5b7dfd393c41e13df2f135e3153ba770085` |
| Current `rawlocal/working-order/attempt03/working-order.json` | `6becf19a9b06f625b4292cc8cd60f908fd3bff8d865430e60abcec155af4e9be` |
| `../upper-corner-screw-layout/rawlocal/lower-service-washers/attempt01/result.json` | `cea8ed7447fd3b73a50833bd3cbe67310917e7d37e02b1d1fcb59489997997db` |
| Same service comparison `receipt.json` | `1e9f911f7dc24ea9ffc4257a6ae0756e3fee731bc1eac209a92b1449b9209dd0` |
