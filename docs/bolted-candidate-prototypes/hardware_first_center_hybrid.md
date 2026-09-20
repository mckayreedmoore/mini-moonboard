# Hybrid HL35 center diagnostic — rejected

This is one bounded kerf-right installed-geometry trial, not a fabrication or
drilling plan. Regenerate the paired JSON with `uv run python -m
scripts.hardware_first_center_hybrid --output
docs/bolted-candidate-prototypes/hardware_first_center_hybrid.json`.

The lower joint uses one ideal rear Y-face HL35 on a front-aligned, solid
common post. Its X span is −92.075..92.075 mm, covering the kerf-right kicker
seam at X = −1.5875 mm. The header is a single shaped solid: the original
full-span base beam with one central raised and rearward projection. Its
bounding span is X = −1219.2..1216.025, Y = −258.25..−36, Z = 238.9..327.8
mm. Two upper principals stay on their original X centerlines, ±70 mm, and
widen symmetrically to 88.9 mm. Their upper HL35 vertical legs are on the
*outer X faces*; no upper rear Y-face bracket or upper/lower shared bolt is
assumed. Wood contacts the header at a butt; there is no lap or custom steel.

The fused CAD volumes each form one connected solid. Their unions describe
one-piece machined timber shapes, **not** assembled overlapping plies or a
permitted joinery seam. Minimum sampled one-piece blank envelopes, in mm:

| Part | Minimum envelope | Method |
| --- | --- | --- |
| Common post | 184.15 × 139.7 × 238.9 | Axis-aligned |
| Shaped header | 2435.225 × 222.25 × 88.9 | Axis-aligned |
| Each widened principal | 88.9 × 139.7 × 2466.3113 | Y/Z rotation sampled at 0.1° |

These are geometric lower bounds without machining allowance, defects, or
shop tolerances. Example dressed stock envelopes (6×8 post, 4×10×10-ft
header, 6×6×10-ft principals) contain those sampled dimensions; this is only
a dimensional comparison. The [Home Depot 4×10×8-ft lead](https://www.homedepot.com/p/306316788)
and [Lowe's 4×10×8-ft lead](https://www.lowes.com/pd/Common-4-in-x-10-in-x-8-ft-Actual-3-5-in-x-9-5-in-x-8-ft-Doug-Fir-Lumber/1000075217)
identify potential solid stock. At the Lowe's stated actual
88.9 × 241.3 × 2438.4 mm, however, the modeled header leaves just
**3.175 mm total length**. That is not a production-feasible cutting allowance
for end trim, kerf, defects, or delivered-length variation. The
[4×10×10-ft fir lead](https://www.lowes.com/pd/4-in-x-10-in-x-10-ft-Douglas-Fir-S4S-Green-Lumber/5014282465)
states 3.5 × 9.5 in actual cross section and offers length margin, but
availability is unverified. [Another 10-ft lead](https://www.lowes.com/pd/4-in-x-10-in-x-10-ft-Douglas-Fir-Lumber-Common-3-562-in-x-9-5-in-x-10-ft-Actual/1000028857)
has a different listed thickness; it likewise needs a current local check.
A [6×6×10-ft fir listing](https://www.homedepot.com/p/6-in-x-6-in-x-10-ft-1-Premium-Grade-Fir-Dimensional-Lumber-744799/202534027)
states 5.5 × 5.5 × 120 in actual. No delivered one-piece blanks, matching
DF-L No. 2 grade, cut yield, or local availability are verified. An online
listing is not local stock. Each principal needs at least 2466.3113 mm along
its sampled blank, exceeding 8 ft by 27.9113 mm; a longer blank such as 10 ft
is required before any cutting allowance. If an
ordinary retail blank cannot contain any part as one piece, reject the
concept. Each blank must also clear its listed length and be transportable,
supported, and machinable at full length. Do not splice or laminate it.

All 66 protected panel/kicker axes remain fixed. The four center kicker
occupied cylinders each intersect the common post by 438.127 mm³, and no
protected screw loses modeled receiving wood. The lower bores remain within
their intended wood. No independent upper/lower bore cylinders intersect.
No ideal plate meets a panel, and no frozen occupied panel screw cylinder
meets a plate or bore. None of the 12 original frame-bolt cylinders meets
the new ideal hardware. These zero intersections do **not** establish
delivered fit, screw embedment, edge capacity, or access.

The trial still fails. Each first upper principal bore leaves its sloped toe
by 12,022.236 mm³. Each widened principal intersects the unchanged bottom
rail (133,291.013 mm³) and two service rails (135,193.278 mm³ each); the
original narrow principals had zero intersection with those rails. Each
upper vertical plate intersects an unchanged bottom rail by 8,218.758 mm³.
Those are installed wood/steel clashes, even though the bore directions no
longer duplicate. The 63.5-mm *overall* purchased screw length is only a
conditional envelope here, not verified occupied shaft length.

**Disposition: reject this pose.** The screen assumes ideal 4.55-mm plate
rectangles, a symmetric but undimensioned horizontal hole offset, and
14.2875-mm diagnostic bores. Delivered HL35 holes and bends, heads, washers,
nuts, tool and withdrawal paths, wood edge/end distances, connector
resistance, and the force path remain unresolved. No drilling coordinates,
capacity claim, cutting instruction, or procurement approval follows.
