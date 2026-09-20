# Hardware-first connector screen (conditional scope)

Status: source-verified concept research, not an owner-approved frame change,
connector selection, resistance verdict, purchase list, or drilling release.
The owner's earlier instruction limited movement to the center box supports;
the later Astra handoff reports broader permission. Confirmation of which
scope governs is pending. The selected candidate, 66 panel/kicker screw axes,
panel outlines, and archived evidence have not changed.

## Documented factory-hardware shortlist

The [Simpson C-C-2026 p. 315 HL sheet](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
was inspected as a page image. Its tabulated DF/SP loads have the shown
`160` duration label; they are not adopted board ratings. The
[same C-C-2026 catalog's general instructions](https://www.rbscorp.com/wp-content/uploads/2026/03/C-C-2026.pdf)
(pp. 21–23) define `(160)` as the earthquake/wind/uplift duration basis,
require all specified fasteners, and say that wood shear is not included
unless noted. Do not simply divide a tested/catalog connector value by
1.6 to invent a different-duration capacity: its controlling steel, wood,
fastener, or deflection limit has not been identified. A single connector
is the table basis. Both sides are required for F1 lateral resistance in
both directions; uplift may be doubled for two connectors, but lateral may
not. The angle must be centered on a member face at least as wide as the
angle, and the `3`/`5` series requires a minimum 3.5-in wood thickness.
Structural-quality through bolts must be at least ASTM A307 Grade A.

| Model | Width × leg length | Bolts, total | DF/SP uplift / F1, lb | Retail identity |
| --- | --- | --- | --- | --- |
| HL33 | 3.25 × 2.5 in | 2 × 1/2 in | 740 / 1,040 | [Home Depot HL33-R](https://www.homedepot.com/p/100375377); `-R` equivalence not yet verified |
| HL35 | 3.25 × 5 in | 4 × 1/2 in | 740 / 1,310 | [Home Depot HL35-R](https://www.homedepot.com/p/100374913); Simpson links this retail designation to its HL drawing |
| HL53 | 5.75 × 2.5 in | 4 × 1/2 in | 740 / 1,310 | [Home Depot HL53](https://www.homedepot.com/p/205227146), exact model |

For HL35, D1 = 1.25 in from the end along its 5-in bend length, D2 = 2.5 in
between the two centers along that length, and D3 = 2 in transverse from
the bend on each flange. The nominal two-hole pattern on each flange is
therefore `(1.25, 2)` and `(3.75, 2)` in from the same end/bend datums.
[Simpson's response about the HL35-R hole spacing](https://www.lowes.com/questions/simpson-strong-tie-hl35-r-angles-brackets-and-braces/1002693778/8250e297-9f65-5443-8b75-322144244762)
directs buyers to the HL catalog drawing; a separate
[Simpson retail-suffix explanation](https://www.lowes.com/questions/simpson-strong-tie-bc4z-r-base-and-cap-hardware/1002708600/78d2d639-8e97-5e02-b1d7-aebc98135eb3)
says `-R` denotes retail packaging for another model. This supports a
nominal HL35-R pattern match, not a measured tolerance or receipt check.
Confirm the exact occupied factory pattern and
received variation before any wood drilling. The listed uplift/F1 directions
do not cover arbitrary flange moments, separation, mixed actions, or joint
stiffness; each demands its own applicable route if present.
For simultaneous rated-direction loads, C-C-2026 p. 289 gives a unity
equation using the ratios of design uplift and the two lateral components
to their respective allowable values. Its alternative 75% rule is limited
to certain roof-to-wall products; it does not identify HL angles as eligible.
The HL table publishes uplift and F1 only, so the unity equation cannot
confer an unlisted F2 resistance or moment rating. The actual installed
joint must first resolve its load directions and any load sharing; no
interaction ratio can be evaluated from the current shortlist alone.

For comparison, the [MiTek B-series table](https://www.mitek-us.com/wp-content/uploads/2020/12/B_-BL.pdf)
states a 3-in minimum member thickness, ASTM A307-or-better bolts, and
single-brace F1/F2 values that already include a 60% wind/seismic increase.
It requires braces on both sides for F1 in both directions. B66 uses four
3/8-in bolts, with 710/335 lb F1/F2; B88 uses six 3/8-in bolts, with
620/305 lb. These values are not adopted for the board's load duration.
The [Home Depot UB88 listing](https://www.homedepot.com/p/313507573) and
the existing `mitek-b66-retail.json` record provide a manufacturer/retailer
model cross-reference, but the inspected B88 drawing does not dimension all
hole centers. The previously checked Lowe's B66 listing was no longer sold.

## Smallest-change concept to investigate if broader scope is confirmed

Start with HL35 on solid 4×6 actual 3.5 × 5.5 in receiving stock for
*both sides* of the center principal/header and center post/header duties:
the center principal, header, and center post all require a thick receiving
member under the catalog detail. Keep the current
panel-bearing faces and panel screw axes fixed while allowing extra timber
depth behind them; do not assume the substituted solids fit adjacent members.
HL35 has a narrower face width but a longer leg than an HL53-on-4×8 route,
while offering four
specified bolts and a directly cataloged wood-joint load basis. An opposing
HL35 pair is a *conditional concept* for reversible F1, not a verified joint.
The obvious full-length 4×6 header substitution is **not** a direct drop-in:
raw CAD puts its present top/bottom at Z = 277/238.9 mm. Holding the top
fixed and increasing thickness from 38.1 to 88.9 mm puts the bottom at
Z = 188.1 mm, overlapping the unchanged center post by 50.8 mm. Shortening
that post to meet the new underside leaves its protected upper kerf-right
kicker screw axis at Z = 192 mm, 3.9 mm above the post end and only 3.9 mm
from the new header's bottom edge. This is a nominal centerline screen, not
a bore or screw-body check. The coordinates come from
`uncut_wood_parts()` and the kerf-right `connection-axes.csv`.
Do not convert a projected Y/Z overlap into a screw/bolt clash: in one
principal-side/header-top HL35 trial, the bend is at X = −89.05 mm and its
header flange extends outward. Its 2-in transverse factory-hole offset
then puts header bolt axes at X = −139.85 mm, while the protected kicker
screw is at X = −70 mm. The 69.85-mm X separation rules out an axis
intersection in that particular pose. It does not cure the post/header
solid overlap or establish flange, washer, or tool clearance.
In X, the original left center pieces span −89.05 to −50.95 mm and their
protected main/kicker screw axes use X = −70 mm. A centered 88.9-mm-wide
solid receiver would span −114.45 to −25.55 mm and retain those axis centers
within timber, but this says nothing about the full angled screw bodies,
panel bearing, the right-side mirror, or neighboring connector clearance.
For that one nominal bend pose, centering HL35's 63.5-mm along-bend pitch
in the existing 139.7-mm header depth puts the two Y rows at −137.6 and
−74.1 mm. Each is 38.1 mm from its nearest header Y edge. The original
principal's raw broad-face grain ray from either row at Z = 327.8 mm to
its Z = 277-mm oblique end is 66.315 mm. That exceeds a 3.5D (=44.45 mm)
*ray-only search filter* by 21.865 mm for a half-inch bolt; it is not an
NDS oblique-end classification or a check of a reshaped solid 4×6.
Conversely, a reversible 4D edge search filter in Y would need 50.8 mm
from each loaded edge, 12.7 mm more than the nominal nearest-edge distance.
Which edges are loaded depends on the simultaneous joint actions; neither
the favorable ray nor the failed conservative reversible-edge filter is a
complete wood-connection verdict.
Consequently, a candidate must redesign the local header/post support or
find a different rated flange orientation; merely swapping timber labels
does not preserve the existing kicker fastening.
The center assembly needs its own upper/lower flange orientation, actual
factory-hole layout, bolt stacks, oblique-end/edge distances, support for
the kerf-right kicker edges, and disassembly access. If those fail, compare
one B88-on-solid-thick-member concept; do not default back to BR904 simply
because its earlier prototype is further along.

This screen changes no raw geometry. It does not establish that a 4×6 can
replace both 2×6 pieces without moving other support, that the old twelve
frame bolts remain viable, or that either catalog's isolated load directions
cover the simultaneous joint wrench. No fabrication action follows.

## Receiving and stock-length boundary

The baseline `stock.csv` gives a 2,532.626-mm blank for each center
principal, longer than an 8-ft (2,438.4-mm) stick; a nominal 8-ft 4×6 is
not a sufficient raw replacement. [Lowe's lists 12-ft #2-and-better
Douglas-fir 4×6](https://www.lowes.com/pd/4-in-x-6-in-x-12-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-12-ft-Actual/1000028925)
and separately advertises a 16-ft #2 green 4×6 at 3.562 × 5.625 in actual.
These are retail leads, not received lumber or a claim of local stock. Green
dimensions may change with drying; the HL minimum 3.5-in installed timber
thickness, grade, species, and actual straight usable length must be checked
on the delivered material before applying catalog loads or cutting.
