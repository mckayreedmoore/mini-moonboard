# PB01 six-inch block: two-bolt group and spacing applicability

Status: **bounded 2024 NDS applicability screen, not a connection capacity,
utilization, selected bolt schedule, or cut/drill release.** This is the
152.4 mm `quarter_short` block in the kerf-right trial. The upright and rail
are two *serial* wood-to-wood, single-shear interfaces with two nominal
1/4-in bolts each; the four bolts are not one group. The [retained A12-left
and K12-right archives](simple-pb01-short-tension-evidence.md) are accepted
diagnostic solves, but retain 23 legacy connector proxies and do not establish
qualified V4 joint demand. No historical 300 mm block action is transferred.

## Rule and edition boundary

The [AWC 2024 NDS Chapter 11, p. 72, §§11.3.6.1–11.3.6.3][ch11]
applies a group action factor `C_g` to reference *lateral* values for
dowel-type fasteners of `D ≤ 1 in` **in a row**. A dowel row for this
purpose has at least two same-diameter fasteners in single or multiple shear
*aligned with the direction of load*. For `D < 1/4 in`, `C_g = 1`; the
nominal `D = 1/4 in` trial is on the other side of that strict threshold.
The equation uses fastener count, center pitch, main/side member gross areas
and elastic moduli, and a diameter-dependent load/slip modulus. The
[2024 NDS errata, p. 7][errata] corrects its printed `D1.5` to `D^1.5`.
Table 11.3.6A on [Chapter 11, p. 73][ch11] is based on a 1-in bolt,
4-in pitch, and specified reference modulus/areas; its entries cannot be
read directly as this 1/4-in trial's factor.

The [AWC 2024 NDS Chapter 12, p. 81, §§12.1.2–12.1.3][ch12] defines
end distance along grain, edge distance across grain, and spacing between
centers; its row also follows load direction. For `D ≥ 1/4 in`,
[p. 97, §12.5.1.2][ch12] applies the smallest relevant geometry factor
`C_Δ` to all fasteners in a group when end distance or in-row spacing is
below its full-value requirement. [p. 98, Tables 12.5.1A–B][ch12] gives
3D minimum/4D full-value parallel-grain pitch, 3D minimum
perpendicular-grain pitch with full-value spacing governed by the attached
member, and softwood loaded-end 3.5D minimum/7D full-value distance;
other end directions use 2D/4D. [pp. 98–99, §12.5.1.3 and Tables
12.5.1C–D][ch12] separately govern edge distance and spacing between
rows. [p. 100, §§12.6.2–12.6.3][ch12] requires load distribution and
local-stress checks for multiple fasteners. These are 2024 provisions;
no 2018 table or material value is mixed into this screen.

## Actual grain and center layout

The [retained pose](simple_rail_joint_comparison.json) fixes X × T × N
at 139.7 × 57.15 × 152.4 mm for the short trial; the
[short-block screen](simple-pb01-short-block-screen.md) establishes that
only N length changes from the recorded 300 mm pose. Upright host grain is
T, rail host grain is X, and block grain is N. The 7.5 mm diagnostic bores
are not a shop diameter. Distances below are center-to-wood-boundary,
not clear wood or fabrication tolerances.

| Interface | Center line and pitch | Along-grain member | Across-grain member |
| --- | --- | --- | --- |
| Upright u1/u2 | N = 265/310 mm; 45 mm (7.09D) | Block N: front ends 55.159/100.159 mm; rear ends 97.241/52.241 mm | Upright T grain: N edges 55.159/84.541 mm at u1 and 100.159/39.541 mm at u2 |
| Rail r1/r2 | X = 70/110 mm from rail butt; 40 mm (6.30D) | Rail X: butt ends 70/110 mm | Block N grain: X edges 70/69.7 mm at r1 and 110/29.7 mm at r2 |

The block's rail-row N edges are 80.159/72.241 mm after the length-only
shortening; the rail host's N edges are 80.159/59.541 mm. The block's
upright-row T edges are 28.575 mm. Thus a *hypothetical row-aligned*
classification gives both pitches above 4D = 25.4 mm, and the shortest
block N end (52.241 mm) above 7D = 44.45 mm. Those arithmetic margins
do **not** classify the actual oblique loading, establish `C_Δ = 1` for
all members, or clear edge, local splitting, net-section, and interaction
checks. In particular, N distances on the upright are **edges**, and X
distances on the block at the rail are **edges**, not loaded ends.

## Signed actions decide row applicability

The [signed component comparison](simple-pb01-short-tension-component-comparison.md)
reads and verifies both retained archives. The table projects each lateral
force **on its host** onto the geometric pair line and onto the perpendicular
in-plane direction. For upright, row is +N and across row is +T; for rail,
row is +X and across row is +N. Reversing to the block changes all signs,
not the conclusion. Values are N, rounded to 0.001.

| Case | Bolt | Along row | Across row | Lateral magnitude |
| --- | --- | ---: | ---: | ---: |
| A12-left | u1 | −3.164 | +8.857 | 9.405 |
| A12-left | u2 | −3.543 | −16.274 | 16.655 |
| A12-left | r1 | +7.276 | +10.961 | 13.156 |
| A12-left | r2 | +7.289 | −9.901 | 12.295 |
| K12-right | u1 | −5.286 | +16.509 | 17.335 |
| K12-right | u2 | −6.186 | −11.711 | 13.244 |
| K12-right | r1 | +31.662 | +16.534 | 35.719 |
| K12-right | r2 | +31.169 | −10.708 | 32.957 |

Neither pair is aligned with either bolt's complete lateral load vector;
the opposing across-row components also mean a single common row load
direction cannot be inferred from the pair's resultant. The **missing
classification** is a justified direction-of-load/row assignment for each
interface and each member under the simultaneous oblique lateral forces,
including how the perpendicular components and couple distribute, which
edge is loaded, and which end-distance/spacing branch controls. Until
that classification is made, the geometric pairs alone do not justify
inserting `N = 2` into §11.3.6.1 or selecting a numerical `C_g`; nor can
one declare a final `C_Δ`. A conditional row-aligned formula value would
answer a different load case, not these signed archives. Bolt axial tension
at r1 (20.495 N in A12-left, 19.668 N in K12-right), contact compression,
and moments remain separate from this lateral group screen.

## Conservative no-benefit bound, without a resistance claim

For a demand-only envelope, use the triangle inequality: sum the two
individual lateral **magnitudes** at each interface, with no cancellation
of opposing across-row components and no credit for two-bolt capacity.
Against the existing [quarter-inch yield screen's](simple-pb01-quarter-yield-screen.md)
smallest 0°/90° one-bolt reference, 94.1 lbf at its *hypothetical* 0.180-in
root, this gives only the following dimensionless **scale indicators**
(`1 N = 0.224809 lbf`):

| Case / interface | Sum of bolt lateral magnitudes (N) | Sum / 94.1 lbf |
| --- | ---: | ---: |
| A12-left / upright | 26.060 | 0.0623 |
| A12-left / rail | 25.451 | 0.0608 |
| K12-right / upright | 30.579 | 0.0731 |
| K12-right / rail | 68.676 | 0.1641 |

This bounds the *modeled bolt-force resultant* above and gives no sharing
benefit. It is **not** an NDS group check: the denominator is an unadjusted
one-bolt reference with an unverified root, not an established lower bound
on adjusted group resistance. No pass, safety factor, allowable load,
joint capacity, or drilling release follows from ratios below one. The
[quarter member screen](simple-pb01-quarter-member-screen.md) likewise
provides separate conditional Appendix E section components, not a
substitute for group, spacing, combined loading, or local stress checks.

[ch11]: https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf
[ch12]: https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf
[errata]: https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf
