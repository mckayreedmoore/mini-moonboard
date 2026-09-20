# Hardware-first connector screen (conditional scope)

Status: source-verified concept research under the owner's 2026-09-20 approval
to change hidden frame members, not a connector selection, resistance verdict,
purchase list, or drilling release. The earlier center-support-only limit no
longer governs this separate bolted candidate. The selected candidate, 66
panel/kicker screw axes, panel outlines, and archived evidence have not changed.

## Documented factory-hardware shortlist

The [Simpson C-C-2026 p. 315 HL sheet](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
was inspected as a page image. Its tabulated DF/SP loads have the shown
`160` duration label; they are not adopted board ratings. The
[same C-C-2026 catalog's general instructions](https://www.rbscorp.com/wp-content/uploads/2026/03/C-C-2026.pdf)
(pp. 21–23) define `(160)` as the earthquake/wind/uplift duration basis,
require all specified fasteners, and say that wood shear is not included
unless noted. Unlike MiTek's B88 report, Simpson's HL catalog says to
**reduce** the wind/earthquake table values where other loads govern. It
does not publish a separate `C_D = 1.0` HL table or an HL-specific conversion.
The arithmetic `740/1.6 = 462.5 lb` uplift and `1310/1.6 = 818.75 lb` F1
per connector is a *conservative screening inference* under the ordinary
wood-duration/unchanged-metal-limit model, not a manufacturer-certified
ordinary-duration rating or an adopted joint capacity. The controlling
steel, wood, fastener, or deflection mode is not identified, and actual load
directions, interaction, and member resistance still need checks. A single
connector is the table basis. Both sides are required for F1 lateral resistance in
both directions; uplift may be doubled for two connectors, but lateral may
not. The angle must be centered on a member face at least as wide as the
angle, and the `3`/`5` series requires a minimum 3.5-in wood thickness.
Structural-quality through bolts must be at least ASTM A307 Grade A.
For that specified **bolt class only**, Home Depot currently lists Prime-Line
1/2-13 ASTM A307 Grade A hex bolts at [6 in (9060913)](https://www.homedepot.com/p/310465135),
[8 in (9060949)](https://www.homedepot.com/p/310465137), and
[12 in (9061025)](https://www.homedepot.com/p/310465147).
These are ordinary-retail leads, not selected stack lengths or proof of
delivered conformity or local stock. Their listings do not resolve usable
smooth-shank length/thread runout, washers, matching nuts, grip, head/nut
access, or the complete wood/steel joint resistance. The listings also use
inconsistent coating descriptions, so coating compatibility requires a
received-item check; no bolt purchase or drilling is released.

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
[MiTek's retail conversion chart](https://images.thdstatic.com/catalog/pdfImages/2f/2f1009db-047c-4da8-a283-bcda2c494ebe.pdf)
establish the UB88/B88 identity. MiTek's public B88 DXF provides six nominal
CAD hole centers, although its PDF does not dimension their offsets and
neither drawing states manufacturing tolerances. See the
[drawing follow-up](mitek-b88-drawing-followup.md). ICC ESR-3455 states its
`C_D = 1.6` B88 loads cannot be applied or adjusted to other durations.
The previously checked Lowe's B66 listing was no longer sold.
The [Home Depot UB66 listing](https://www.homedepot.com/p/313507617)
and the same MiTek conversion chart establish the exact B66 retail identity.
Its [public DXF](https://www.mitek-us.com/wp-content/uploads/files/Drawing%20Library/B66_3view.dxf)
contains four nominal circle centers; see the
[B66 drawing follow-up](mitek-b66-drawing-followup.md). B66 is narrower and
shorter than B88 but still requires the 3-in actual wood receiver and has
the same ESR duration restriction. One bounded *fit* comparison is recorded
below; it is not an accepted replacement for a rejected HL pose.

## First center concepts and their limits

The initial screen used HL35 on solid 4×6 actual 3.5 × 5.5 in receiving stock for
*both sides* of the center principal/header and center post/header duties:
the center principal, header, and center post all require a thick receiving
member under the catalog detail. Keep the current
panel-bearing faces and panel screw axes fixed while allowing extra timber
depth behind them; do not assume the substituted solids fit adjacent members.
HL35 has a narrower face width but a longer leg than an HL53-on-4×8 route,
while offering four
specified bolts and a directly cataloged wood-joint load basis. An opposing
HL35 pair was a *conditional concept* for reversible F1, not a verified joint.
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
header flange extends outward. Assuming the 2-in transverse hole offset
also applies to that flange puts nominal header bolt axes at X = −139.85 mm;
the protected kicker screw is at X = −70 mm. The 69.85-mm X separation rules out an axis
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
the kerf-right kicker edges, and disassembly access. If a viable HL route
does not emerge, compare one B88-on-solid-thick-member concept; do not
default back to BR904 simply because its earlier prototype is further along.

Three specific installed poses have now been **rejected**, not the whole HL
family: [paired X-face HL35 on solid centers](hardware_first_center_hl35.md)
has inner-plate and opposite-timber collisions, overlapping independent
header bores, a kicker screw/bore clash, and incomplete seam backing;
[paired X-face HL53 on wider solids](hardware_first_center_hl53.md) separates
nominal bores but cannot fit inner plates between two posts that each back
their kicker inner edge; and a
[centered common-post Y-face HL35 pose](hardware_first_center_yface.md)
backs both edges but puts its front angle inside the fixed kicker panels.
These CAD screens use idealized factory dimensions and do not establish
resistance. A [rearward structural post with separate kicker backing](hardware_first_center_rearback.md)
was also tried: it clears panels and preserves screw-axis contact, but the
widened header intersects side/principal timbers, front bolts have no head
clearance, and backing connection and upper joint are unresolved. It too is
rejected as an incomplete installed assembly, not a verdict on all HL layouts.
The [rear-only Y-face HL35 pose](hardware_first_center_rear_yface.md)
keeps the front-aligned common post and avoids the panel collision, but its
upper bolts miss the original narrow principals, its independent header
bores overlap, and the enlarged header intersects both side timbers. It is
another rejected pose, not an approved rear-face joint.
A [hybrid rear-Y lower / outward-X upper HL35 pose](hardware_first_center_hybrid.md)
preserves all 66 screw receivers and separates independent upper/lower
bores. It still fails: upper bores leave both sloped principal toes, the
widened principals intersect existing rails, and upper plates hit bottom
rails. The shaped one-piece header has only 3.175 mm total nominal surplus
from an 8-ft 4×10 blank, so that length has no usable trim allowance;
longer stock is a retail lead, not a received blank. This is a bounded
geometry rejection, not a verdict on all factory-bracket architectures.
A [toe/seat shift bound](hardware_first_center_hybrid_toe.md) shows that
sliding those upper HL35s forward cannot contain their first nominal bores
while keeping the complete 127-mm seats on the existing front-limited
header: 12.7 mm is the full-seat limit and both bores still exit wood.
This rules out a simple bracket-row slide within that pose, not a changed
header or a different factory connector.
A [15-mm forward upper-row and 2.3-mm header-extension trial](hardware_first_center_hybrid_forward.md)
contains all nominal bores and resects the same six rails, but the necessary
header extension intersects both fixed kerf-right kicker panels. That
specific extension is rejected while the panel outlines remain fixed; its
nominal bore clearance does not qualify the wood joint or another header
shape.
A [six-rail inner-end resection screen](hardware_first_center_hybrid_rails.md)
shows that the hybrid's widened-principal/upper-plate collisions can be
removed in nominal CAD while all 66 protected screw receivers remain.
However, the changed rails end 5.55 mm short of each principal and leave
only 1 mm ideal plate clearance; their bracketed force path, bolt/tool
access, and tolerances are unsolved. The parent hybrid remains rejected.

A separate [HL33 short-bend center pose](hardware_first_center_hl33.md)
uses a one-piece thicker center header, common post, and widened principals.
It retains all 66 protected screw receivers and contains its six nominal
bores, but the widened principals meet six unchanged rails, the upper
vertical plates meet bottom rails, and the upper principal bores intersect
those rails. This rejects the installed pose, not the HL33 family. Its
single lower HL33 is not established for reversible F1 in this arrangement;
the source does not dimension the assumed horizontal flange-hole offset.

A [lower-only paired outer-X HL35 post pose](hardware_first_center_outer_post.md)
keeps the kerf-right kicker seam and all 66 screw receivers supported. Its
left/right post bolts coincide as two shared through-bolt axes rather than
four independent bolts. The unchanged 38.1-mm header is **below** the HL35
88.9-mm minimum wood receiver thickness, so the pose is catalog-inapplicable
even though its ideal plate and bore solids clear most neighboring geometry.
It leaves the upper joint unmodeled and does not justify shared-bolt capacity;
the separate 63.5-mm overall-screw collision sensitivity is conditional.

One [B88/UB88 center pose](hardware_first_b88_center.md) using the official
nominal DXF centers was screened too. Its four brackets and through-bolts
preserve all 66 protected axes, but four nominal bolt paths intersect
protected kicker screws, four upper paths exit modeled principal wood, and
the enlarged members or one plate collide with adjacent hidden frame parts.
That pose is rejected on installed geometry; it is not a family-wide B88
verdict. Separately, ESR-3455 expressly bars transferring the B88
`C_D = 1.6` ratings to ordinary load duration. Neither the fit study nor
the listed F1/F2 values provide a climbing-board joint rating.

One [B66/UB66 center pose](hardware_first_b66_center.md) was also screened
using its nominal factory DXF centers. The common front-aligned solid post
preserves all 66 historical screw receivers, but lower bolt rows leave only
22.075 mm to an outer post edge under a conservative 4D search filter.
Upper bores leave principal wood; widened members and plates collide with
other hidden members. Its one-piece post and header stock envelopes also
have no verified ordinary untreated DF-L No. 2 big-box source. This rejects
that pose, not every B66 layout. Neither the DXF nor ESR-3455 resolves an
ordinary-duration complete joint resistance or releases drilling.

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

For a *different* short-bend HL33 outer-post trial, [Lowe's 4×8×8-ft
Douglas-fir #2-and-better green lumber](https://www.lowes.com/pd/4-in-x-8-in-x-8-ft-Douglas-Fir-Lumber/1000028833)
lists 3.562 × 7.5 in actual section. That is a dimensional lead for a
roughly 184-mm-wide, 89-mm-deep one-piece common post; it does not establish
delivered size after drying, treatment/service basis, local stock, a fitting
HL33 bolt pattern, or a rated joint. The tested HL33 pose above used the
larger original 139.7-mm post depth and remains rejected.
