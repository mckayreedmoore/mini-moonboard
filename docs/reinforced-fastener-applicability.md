# Reinforced candidate: fastener applicability decisions

**The selected SPAX screw has a directly applicable 120 lbf (533.787 N)
plywood head pull-through reference.** The previous generic 304.125 N equation
candidate and its head-shape dispute need not govern this assembly. The
reinforced frame retains 22 ML24Z angles; their exact force-axis inventory is
recorded in the [lookup](reinforced-fastener-applicability.json).

## Panel-screw head resistance: resolved product basis

[SPAX TER 2010-02, Table 6](https://www.drjcertification.org/report/download/1936#page=13)
lists carbon-steel #8 flat heads at 120 lbf for 19/32-inch plywood, G=0.39.
Footnote 1 makes thickness a minimum. Footnote 3 directs intermediate G values
between 0.39 and 0.50 to the 0.39 values. The owned 23/32-category panel,
assigned G=0.42, meets both conditions. This is a lower published column
selection, not interpolation of the 212 lbf/G=0.50 column. Section 9.6 requires
flush installation without overdriving. The actual selected flat-head product
is covered; no Simpson head-shape multiplier or generic NDS extrapolation is
needed. Table 6 and its footnotes were visually checked in the downloaded PDF.

Use intact plywood at least **15.08125 mm thick**, the selected screw and a
flush undamaged seat. The reference does not cover deeper counterboring or
damaged seats. It applies to both face and kicker panel head resistance; receiver
withdrawal and demand are separate checks. No hardware change is needed to
close this product-reference question.

## Adopted adjustment basis

[NDS 2018 Tables 11.3.1, 11.3.3 and 11.3.4](https://plib.org/wp-content/uploads/2020/09/AWC-NDS2018.pdf#page=78)
give the head pull-through ASD adjustments: load duration, wet service and
temperature. Adopt **CD=1.0, CM=1.0, Ct=1.0** for the project's normal-duration
load envelope, continuously dry installation/use and temperature no greater
than 100°F. The resulting assumed-condition allowable is **533.787 N per
head**. This is a declared installation basis, not a claim of measured moisture.
Use CD=0.9 for a permanent-load-only check. Do not take an impact-duration
increase. Wet-service CM=0.7 and elevated-temperature reductions apply if those
conditions replace the stated basis.

The head equation edition issue is bypassed by the product table. The adjustment
tables above were inspected in 2018. The publisher's 2024 view-only resource
did not provide inspectable chapter content during this check; no complete
2018/2024 equivalence claim is made. A project requiring 2024 exclusively must
confirm those adjustment provisions, not reopen the resolved SPAX head shape
or plywood-column selection. Compare each current axial demand to this head
allowable, then complete receiver wood interaction and steel checks separately.

## All 22 retained ML24Z locations

CAD station tuples define orthogonal flange axes `u`, `v` and bend axis
`w = u cross v`. The first member receives screws perpendicular to `v`; the
second receives screws perpendicular to `u`. Board slope tangent is
`S=(0,0.642788,0.766044)`; board normal is perpendicular to S in the Y/Z plane.

| Family | Exact station names/pattern | Count | Force directions |
| --- | --- | ---: | --- |
| Top rail | `clip_single_top_left_1`, `clip_single_top_right_2`, `clip_split_top_center_left/right` | 4 | F1 along ±N; rail withdrawal F2 along ±X; F3/F4 along S |
| Bottom rail | `clip_horizontal_bottom_left/right_1/2` | 4 | Same axes; `v=+S` |
| Lower service rails | `clip_horizontal_lower_left/right_1/2` | 4 | Same axes; `v=-S` |
| Upper service rails | `clip_horizontal_upper_left/right_1/2` | 4 | Same axes; `v=+S` |
| Header/post | `clip_timber_header_outer_left/right`, `clip_split_header_center_left/right` | 4 | Bearing analogy: F1 along ±Y; separation F2 along −Z; F3/F4 along X |
| Center principal/header | `clip_split_base_center_left/right` | 2 | Bearing analogy: F1 along ±Y; separation F2 along +Z; F3/F4 along X |

Every station's origin and direction vectors are in the lookup. The top/lower
versus bottom/upper flip matters; do not reuse one global sign convention.
Removing the two outer rim angles did not remove the two center-principal base
angles or the four header/post angles.

## Published force capacities and exact unresolved duties

[L-C-MLZ25](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
provides, for one ML24Z and six SDS25112 screws in DF/SP, single/end allowables
F1/F2/F3/F4 of **595/450/450/750 lbf**. Bearing installation gives
**595/unlisted/450/750 lbf**. No ML24Z duration increase applies. The letter's
second page was visually inspected for member orientation. It requires
consideration of reinforcement for unavoidable cross-grain tension/bending.

The sixteen rail-end joints geometrically follow single/end arrangements.
Their F1 reference is 2646.692 N, F2 is 2001.700 N, and a conservative
sign-independent F3/F4 reference is 2001.700 N. These are useful force screens
without assigning the stronger F4 sign incorrectly. They do not supply an
independent moment rating. Nonzero torsion or bending couple from the structural
model must be resolved through a supported force application point/load path,
or explicitly designed steel/screw-group resistance; do not set it to zero.

For the remaining six joints, the bearing analogy leaves the stated separation
direction unlisted. Their grain/member conditions also differ from the letter's
drawn bearing member: posts have Z grain, center principals have S grain, while
the illustrated bearing beam runs along the bend. A 450 lbf single/end F2
number cannot simply be reassigned. Neither a compressive bearing contact nor
the new outer steel shoes proves that separation demand at these six is zero.
The necessary model output is each joint's simultaneous force and moment on
the identified loaded member, including any contact bypass.

The [2026 catalog's simultaneous-load rule, page 289](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog),
as recorded in the [prior primary-source review](round-structural-base-review.md),
requires compatible directional allowables for simultaneous loading. A unity
check on rated force components cannot create a missing separation or couple
rating. Signed F3/F4 allocation and the applied-force point remain explicit
inputs if the larger 750 lbf value is used.

## Least-change closure

Retain SPAX hardware and adopt the 120 lbf head basis above. Retain the sixteen
rail-end ML24Z angles for their published force directions, subject to current
joint demands and actual grain/fastener-zone checks. For the six bearing-like
joints, first determine whether compression/contact carries the relevant duty;
if separation is required, a separately rated axial tie can carry that duty
while the angle carries only its rated shear components. Such a tie requires
actual placement and its own rated wood/grain installation; the previously
studied H3 does not automatically fit the sloped center principal. No inspected
catalog detail establishes all six joints' complete six-component resistance
without that layout and force-path work.

Exact manufacturer/designer question, not sent: For the four downward-pointing
header/post and two upward-pointing sloped-center-principal connections in the
attached station table, which published installation applies with the recorded
member grain and screw planes? Identify separation resistance, compatible
simultaneous-load rule and permissible applied-force point/couple. If none
applies, specify one axial tie in its rated mounting and the required bearing
or rotational-release detail. Supply current simultaneous demands with the
request; historical insert/outer-angle demands are not substitutes.
