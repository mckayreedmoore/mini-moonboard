# Dimensional length screen for 24 current WJ24 center and knee axes

**Checked:** 2026-09-25. **Status:** source-bound nominal length classes for
further review; no SKU is selected and no candidate is fit-qualified. This
screen uses the current 92-axis WJ24 geometry and a provisional 1/4-20
washer/nut dimensional basis. It changes no model, stack, or hardware.

## Exact scope and source

The axis source is frozen [grip-screen attempt 02](hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json),
SHA-256 `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`,
rendered in the [current grip-screen report](current-grip-screen.md). These
are the 24 current axes outside the separate 48-axis 152.4 mm / 127 mm-grip
ordinary screen, the 16-axis 203.2 mm / 177.8 mm-grip side screen, and the
four-axis 6.35 mm / 76.2 mm-grip outer-post screen.

| Family and exact axis IDs | Count | Current modeled wood grip / bolt length |
| --- | ---: | ---: |
| `center_post_left_1`, `center_post_left_2`, `center_post_right_1`, `center_post_right_2` | 4 | 127.000 / 139.217 mm |
| `center_principal_left_1`, `center_principal_left_2`, `center_principal_right_1`, `center_principal_right_2` | 4 | 122.000 / 139.217 mm |
| `center_post_header_left_1`, `center_post_header_left_2`, `center_post_header_right_1`, `center_post_header_right_2` | 4 | 167.000 / 179.217 mm |
| `center_principal_header_left_1`, `center_principal_header_left_2`, `center_principal_header_right_1`, `center_principal_header_right_2` | 4 | 172.800 / 190.017 mm |
| `knee_outer_left_inner_header_1`, `knee_outer_left_inner_header_2`, `knee_outer_right_inner_header_1`, `knee_outer_right_inner_header_2` | 4 | 177.100 / 202.500 mm |
| `knee_outer_left_side_1`, `knee_outer_left_side_2`, `knee_outer_right_side_1`, `knee_outer_right_side_2` | 4 | 215.900 / 241.300 mm |
| **Total** | **24** | **Current screen uses 6.35 mm unthreaded shaft occupancy for each.** |

Each current axis has one head-side washer role, one nut-side washer role,
and one nut role. This 24-axis scope therefore represents 24 bolts, 24 nuts,
and 48 separate washers as a piece-count screen. It is not a purchase list.
The 6.35 mm CAD shaft is an occupancy envelope; this axial screen does not
establish radial clearance, actual timber dimensions, actual holes, or a
delivered bolt body.

## Reused hardware dimensional basis

The prior [ordinary-hardware sourcing work](current-side-hardware-option.md)
documents a specific 1/4-20 Grade 5 bolt/nut candidate route for a different
8 in axis group and a 1/4 in Type A Wide washer candidate. This note reuses
only its standard dimensional ranges and source trail; it does not transfer
the 8 in bolt SKU or its supplier price to any of the length classes below.

| Piece | Axial dimension used |
| --- | ---: |
| Each 1/4 in Type A Wide washer | 1.2954–2.032 mm (0.051–0.080 in) |
| Two washers combined | 2.5908–4.064 mm |
| Finished 1/4 in hex nut | 5.3848–5.7404 mm (0.212–0.226 in) |
| Inherited minimum physical bolt-tip projection beyond far nut face | 3.175 mm |

The candidate 1/4-20 hardware is only an axial sizing basis. The washer
candidate is plain/light-oil low-carbon steel, while the prior bolt and nut
examples are zinc plated; the finish choice, washer strength/support, and
thread fit remain open. The current CAD washer thickness on these rows is
1.651 mm, which lies inside the Type A Wide dimensional interval.

For wood grip `G`, the screen uses these worst-case axial targets, with no
additional wood-length allowance:

| Quantity | Formula | Meaning |
| --- | --- | --- |
| Earliest nut bearing plane | `G + 2 × 1.2954` | Both washers at minimum thickness. |
| Latest nut bearing plane | `G + 2 × 2.032` | Both washers at maximum thickness. |
| Latest physical far-nut face | `G + 2 × 2.032 + 5.7404 = G + 9.8044` | Both washers and finished nut at maximum thickness. |
| Minimum physical tip target | `G + 9.8044 + 3.175 = G + 12.9794` | The inherited tip projection is physical bolt length only, not a full-form-thread requirement. |

## Shortest quarter-inch nominal classes in the screen

The length classes below are the shortest quarter-inch nominal increments
whose ASME B18.2.1 minimum overall length reaches the worst-case physical tip
target above. For 1/4 in cap screws through 6 in, the minimum-length
allowance is 0.10 in; above 6 in, it is 0.18 in. The tabulated `LG,max` and
`LB,min` values use ASME B18.2.1-2012 (R2021), Tables 12 and 13.

| Exact family | Grip `G` | Screened nominal length | Minimum overall length | Latest far-nut face | Physical tip target | Min-length margin to tip target | `LG,max` / margin from earliest bearing plane | `LB,min` | Min length minus current modeled endpoint |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `center_post_{left,right}_{1,2}` | 127.000 mm | 5.75 in / 146.05 mm | 143.510 mm | 136.8044 mm | 139.9794 mm | +3.5306 mm | 127.000 / +2.5908 mm | 120.650 mm | +4.293 mm |
| `center_principal_{left,right}_{1,2}` | 122.000 mm | 5.50 in / 139.70 mm | 137.160 mm | 131.8044 mm | 134.9794 mm | +2.1806 mm | 120.650 / +3.9408 mm | 114.300 mm | −2.057 mm |
| `center_post_header_{left,right}_{1,2}` | 167.000 mm | 7.50 in / 190.50 mm | 185.928 mm | 176.8044 mm | 179.9794 mm | +5.9486 mm | 165.100 / +4.4908 mm | 158.750 mm | +6.711 mm |
| `center_principal_header_{left,right}_{1,2}` | 172.800 mm | 7.50 in / 190.50 mm | 185.928 mm | 182.6044 mm | 185.7794 mm | +0.1486 mm | 165.100 / +10.2908 mm | 158.750 mm | −4.089 mm |
| `knee_outer_{left,right}_inner_header_{1,2}` | 177.100 mm | 7.75 in / 196.85 mm | 192.278 mm | 186.9044 mm | 190.0794 mm | +2.1986 mm | 171.450 / +8.2408 mm | 165.100 mm | −10.222 mm |
| `knee_outer_{left,right}_side_{1,2}` | 215.900 mm | 9.25 in / 234.95 mm | 230.378 mm | 225.7044 mm | 228.8794 mm | +1.4986 mm | 209.550 / +8.9408 mm | 203.200 mm | −10.922 mm |

The `LG` margin is `earliest nut bearing plane − LG,max`; all six are
positive in this gage-coordinate screen. `LG` is the distance to the face of
the GO thread ring gage assembled as far as the thread permits; it is not a
delivered first-full-form-thread coordinate. `LB` is a minimum under-head
body length to the last thread scratch (or applicable rolled-thread
extrusion-angle datum), not an actual first-full-thread or runout location.
Neither table value proves full functional thread engagement in the nut.

“Min length minus current modeled endpoint” keeps the nominal CAD cylinder
separate from the physical-tip rule. A positive value means the standard
minimum overall length still extends beyond that modeled endpoint; a negative
value means the standard permits a delivered bolt shorter by that amount.
The minimum length in every row reaches the 3.175 mm physical projection
target, but not every row guarantees the full current CAD endpoint. The
available standard screen does not require full-form thread through the
additional 3.175 mm beyond the nut.

## Separate 8 in candidate route for the four inner-header knee axes

The four `knee_outer_{left,right}_inner_header_{1,2}` axes have a 177.100 mm
wood grip and a current 202.500 mm modeled endpoint. The already reviewed
[Lawson FA21103 / K.L. Jack nut and washer route](current-side-hardware-option.md)
is a conditional exact 1/4-20 × 8 in Grade 5 catalog route for these four
axes as well. This does not select the product or establish a delivered
matched set.

| Check for the four axes | Value | Basis |
| --- | ---: | --- |
| Earliest nut bearing plane | 179.6908 mm | `G + 2 × 1.2954` |
| Latest far-nut face | 186.9044 mm | `G + 9.8044` |
| Required physical tip target | 190.0794 mm | Latest far-nut face + 3.175 mm |
| 8 in standard minimum overall length | 198.628 mm | `8.00 − 0.18 in`, ASME B18.2.1 dimensional screen |
| Minimum-length margin past physical tip target | +8.5486 mm | Standard minimum minus target |
| `LG,max` / margin from earliest nut bearing | 177.800 / +1.8908 mm | ASME gage limit; not an actual first-full-thread coordinate |
| `LB,min` | 171.450 mm | Under-head body length to last thread scratch datum |
| Minimum length minus current modeled endpoint | −3.872 mm | Standard minimum may be shorter than the 202.500 mm CAD cylinder |

For both sides, each `_inner_header_1` axis has a 139 mm far inner-block
receiver and each `_inner_header_2` axis has a 38.1 mm far header receiver.
The far wood face is at most 179.132 mm from the under-head datum. At the
tabulated `LB,min`, the thread interval that could occupy the final receiver
is therefore at most 7.682 mm. That is below one-quarter of either receiver
(34.750 mm for the 139 mm block; 9.525 mm for the 38.1 mm header). This is
only the NDS nominal-diameter boundary screen under §12.3.7.2, using the
published minimum `LB`; it assigns no resistance and does not locate the
actual thread transition.

The 8 in standard minimum exceeds the latest far-nut face by 11.7236 mm, so
it clears the 3.175 mm physical tip-projection screen without a proposed
stack shift. It is 3.872 mm shorter than the current modeled endpoint, so
this route does not guarantee the full CAD cylinder length. Reconcile an
actual delivered endpoint with the parent clearance workflow if this
conditional route is carried forward. Full functional engagement through
the matched nut, bolt/nut class fit, seating, actual thread/runout position,
washer support, radial clearance, and finish compatibility remain open.
There is no requirement for full-form thread through the extra physical tip
projection.

For a shared catalog scenario with the 16 side axes in
[the existing 8 in option note](current-side-hardware-option.md), these four
axes would bring the piece counts to 20 bolts, 20 nuts, and 40 washers. One
25-piece Lawson bolt pack and one 100-piece box each of the cited K.L. Jack
nuts and washers would cover that combined count, leaving 5 bolts, 80 nuts,
and 60 washers. The nut and washer pages displayed $4.71 and $3.47 per
100-piece box respectively on 2026-09-25; the exact Lawson bolt price is not
publicly available in the cited source. This is package context for a
conditional 20-axis scenario, not a purchase or complete cost estimate.

These are length classes, not fit-qualified supplier products. A bounded
K.L. Jack catalog listing checked 2026-09-25 showed a lead for the 5.50 in
`center_principal` class: 1/4-20 × 5-1/2 in Grade 5 hex-head cap screw,
SKU `25C550HCS5Z`, displayed at $30.59 per box of 100. Four pieces would
leave 96 from that displayed package quantity; price is listing context,
not an estimate of landed cost or a purchase recommendation. The listing
does not establish availability, thread class, `LG`/`LB`, actual transition,
or functional engagement with a matched nut. The product-detail page could
not be retrieved during this check, so no more specific product dimensions
are claimed. No exact SKU, 1/4-20 Grade 5/2A source, availability, package
size, or price was verified in this bounded screen for 5.75, 7.50, 7.75, or
9.25 in. The [8 in Lawson FA21103 / K.L. Jack nut and washer route](current-side-hardware-option.md)
is a separate option for the four 177.1 mm axes above; it does not make any
shortest class in this table a sourced product. Do not infer availability
from standard nominal increments.

## Body-boundary check by nut-side receiver

If a later NDS lateral-yield calculation uses nominal bolt diameter under
NDS-2024 §12.3.7.2, the current local
[bolt-resistance basis](bolt-resistance-basis.md#nds-full-body-or-thread-root-diameter)
requires thread bearing in each member to occupy no more than one-quarter of
that member's bearing length; otherwise it uses measured thread-root
diameter (or a more detailed method). The following is only the worst
thread-in-nut-side-member interval allowed by `LB,min`, using the current
CAD receiver lengths and maximum head-washer thickness. It is not a capacity
check and does not assert where a particular bolt's transition will fall.

| Axes / nut-side receiver | `LB,min` | Far wood face max | Max thread length in final receiver from `LB,min` | One-quarter of final receiver | Conditional nominal-`D` boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| `center_post_{left,right}_{1,2}` / 38.1 mm base-post member | 120.650 mm | 129.032 mm | 8.382 mm | 9.525 mm | Inside by 1.143 mm. |
| `center_principal_{left,right}_{1,2}` / 38.1 mm base-principal member | 114.300 mm | 124.032 mm | 9.732 mm | 9.525 mm | Exceeds by 0.207 mm; to meet this screen, actual `LB` would need to be at least 114.507 mm. |
| `center_post_header_{left,right}_{1,2}` / 128.9 mm cleat | 158.750 mm | 169.032 mm | 10.282 mm | 32.225 mm | Inside by 21.943 mm. |
| `center_principal_header_{left,right}_{1,2}` / 38.1 mm header | 158.750 mm | 174.832 mm | 16.082 mm | 9.525 mm | Exceeds by 6.557 mm; to meet this screen, actual `LB` would need to be at least 165.307 mm. |
| `knee_outer_{left,right}_inner_header_1` / 139 mm inner block | 165.100 mm | 179.132 mm | 14.032 mm | 34.750 mm | Inside by 20.718 mm. |
| `knee_outer_{left,right}_inner_header_2` / 38.1 mm header | 165.100 mm | 179.132 mm | 14.032 mm | 9.525 mm | Exceeds by 4.507 mm; to meet this screen, actual `LB` would need to be at least 169.607 mm. |
| `knee_outer_{left,right}_side_{1,2}` / 88.9 mm inner block | 203.200 mm | 217.932 mm | 14.732 mm | 22.225 mm | Inside by 7.493 mm. |

For the `knee_outer_*_inner_header_1` axes, the far member is the 139 mm
inner block; for `_2`, it is the 38.1 mm `base_header`. These pairs have the
same grip and length target but different nut-side receiver lengths, so their
conditional `LB` screens differ. In the three rows that exceed one-quarter,
the table does not establish that delivered hardware fails: actual `LB` may
exceed the tabular minimum. It identifies the measurement needed if the
nominal-diameter exception is later used. No root diameter, thread location,
or material resistance is inferred here.

For the `center_principal_header` row, the required `LB` of 165.307 mm is
0.207 mm greater than the screened 7.50 in class's `LG,max` of 165.100 mm.
The tabulated limits alone do not establish the actual part-specific
relationship or satisfy the nominal-diameter exception for this row. If
that NDS check is needed, establish the thread-bearing interval from a
part-specific drawing or measurement; otherwise use measured thread-root
diameter `Dr` or a detailed threaded-section method under the cited basis.

## Open fit, stack, and cost fields

- Verify the actual matched bolt/nut pair provides full functional internal
  nut engagement and seats without unthreaded shank, incomplete thread,
  point, or runout interference. Exclude nut entry/exit chamfers using
  source-bound part dimensions or measurement. A `1 in` catalog thread
  length or `LT` reference alone is not an axial thread-transition drawing.
- Measure actual bolt length and body/last-scratch position against the
  relevant row. If the physical 3.175 mm tail is required, no extra
  full-form-thread length beyond the nut is included.
- Reconcile any actual bolt endpoint shorter or longer than the current CAD
  cylinder with the parent geometry/clearance workflow. The table does not
  authorize an endpoint or stack change.
- Measure washer dimensions and verify bearing support and strength at each
  wood face; verify nut/head access and radial shaft clearance. The 6.35 mm
  model envelope has no documented radial tolerance in this note.
- Treat any outward nut/washer shift as a new geometry proposal requiring
  its own length, access, and overlap screen. This arithmetic does not require
  such a shift to meet the 3.175 mm minimum tip-projection target, and does
  not prove full nut engagement without one.
- If a common 1/4-20 layout were later retained for these 24 axes, the
  provisional count is 24 bolts, 24 nuts, and 48 washers. Supplier packages,
  prices, availability, receipt, capacity, and total cost remain unknown for
  the length classes screened here.

## Source trail

- Frozen [attempt 02 grip-screen JSON](hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json)
  and [rendered report](current-grip-screen.md), input hash above.
- ASME [B18.2.1-2012 (R2021) standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws),
  Tables 12–13; [partial-thread table reproduction](https://www.nickel-systems.com/products/bolts-screws/hex-head-cap/)
  and [table PDF](https://www.nickel-systems.com/wp-content/uploads/2025/01/Hex-Head-Cap-Screws-Partially-Threaded-Minimum-Body-Maximum-Grip-Gaging-Lengths-1.pdf).
  The linked reproduction has a visibly transposed 6 in / 1/4 in cell;
  the 8 in limits used above and in the separate 8 in option were rechecked
  against ASME's table as recorded in the
  [source-attribution correction](bolt-dimension-source-correction.md).
- ASME [B18.2.2 finished-hex standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts)
  and [dimension table](https://www.nickel-systems.com/products/nuts/finished-hex/).
- K.L. Jack [25NWUS washer listing](https://www.kljack.com/products/25nwus/)
  and [Fastenal Type A Wide washer dimension sheet](https://www.fastenal.com/content/product_specifications/FW.LC.USS.A.P.00.pdf).
- K.L. Jack catalog listing for Grade 5 1/4-20 × 5-1/2 in cap screw
  [`25C550HCS5Z`](https://www.kljack.com/products/25c550hcs5z/), observed
  2026-09-25; the linked product-detail page timed out, so the listed price
  and package are used only as bounded catalog context above.
- Current [hardware schedule](current-hardware-schedule.md),
  [8 in side-axis candidate route](current-side-hardware-option.md), and
  [bolt resistance basis](bolt-resistance-basis.md#nds-full-body-or-thread-root-diameter).
