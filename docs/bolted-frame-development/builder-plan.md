# Current compact bolted-frame builder plan

Use this maintained guide with the [revision index](development-revisions.json)
and issued [current shop packet][shop]. It consolidates the existing plan for
**`eoere-raised-kicker-screws-v1`** with
**`eoere-selected-purchase-hardware-v1`**, **extra grid off**.
The [viewer][viewer] shows that combination. The selected screw-and-bracket
baseline and earlier wood-block plans have separate instructions.

The nominal part geometry, cut records, 120 receiver occurrences, selected
hardware and supported assembly order are documented. Six matching
first-order load cases and bounded component comparisons are complete.
The packet remains conditional: complete joint/member resistance and physical
stiffness/restraint are unqualified. Actual stock, tooling, support arrangements
and hardware have not been inspected. This guide supplies no fabrication or
climbing release and leaves every issued observation cell blank.

## Use these revisions together

| Operation | Controlling records | Earlier instruction superseded |
| --- | --- | --- |
| Timber blanks, angled ends, rear recesses and stock nesting | [Current profiles][profiles], [end datums][ends], [raw projections][projections], [rear recess][recess] and [nesting][nesting] | These unchanged records are deliberately reused; the current packet composes them. |
| Through-bolt receivers | [Per-member layout](builder-layout.md), derived from [120 receiver rows][holes] | Old adjusted-base v1/v2 and aligned-wire-only drill layouts precede the current axes. |
| Wiring cuts and panel holes | [Current channel drawing][channels], [32 route/receiver rows][channel-datums], [340 panel datums][panels] and [panel plates][panel-plate] | Use smaller channels, omit eleven filled principal arcs, and raise the two named kicker screws to Z212 mm. |
| Bolt lengths and spacers | [100 selected stacks][hardware] and [stack drawing][stacks] | Old `bolt-stacks.csv` modeled lengths and earlier viewer lengths are not purchase instructions. The current hardware viewer applies the selection. |
| Wrench, socket and removal access | Later [installation study][installation] and [200-side method table][access] | The shop packet's coarse 160-side unresolved screen has been refined. Nominal box-wrench access clears 200 sides; actual tools/supports remain unqualified. |
| Current loads and resistance status | [Six current cases][forces] and [qualification ledger][qualification] | Earlier packet statements that matching response is missing describe their issue date. Earlier passes and proposals keep their own scope. |

The optional expanded grid and Z180 lower-corner proposal remain separate.
Neither changes this guide's holes, services or assembly sequence.

## Parts and stock

The fixed inventory is **22 timbers, six panels, 22 Eoere angles, 100 bolts,
100 nuts, 200 washers, eight spacers and 66 Hillman 42605 screws**. Hold
hardware, LEDs and cables retain their separate component specifications.

The following are **raw blank dimensions**, in millimetres. Angled ends can
produce a shorter finished L extent. Use the source member identities and
[per-member face/end coordinates](builder-layout.md), rather than treating
every blank length as a square-ended final cut.

| Member IDs / group | Quantity | Raw length × depth × thickness |
| --- | ---: | ---: |
| `base_floor_left/right` runners | 2 | 1815.646483 × 139.7 × 38.1 |
| `base_header` | 1 | 2435.225 × 139.7 × 38.1 |
| `base_post_center_left/right`, `base_post_outer_left/right` | 4 | 238.9 × 139.7 × 38.1 |
| `base_principal_center_left/right` | 2 | 2532.626012 × 139.7 × 38.1 |
| Left bottom/lower-service/upper-service rails | 3 | 1041.25 × 139.7 × 38.1 |
| Right bottom/lower-service/upper-service rails | 3 | 1077.275 × 139.7 × 38.1 |
| `base_rail_top` | 1 | 2257.425 × 139.7 × 38.1 |
| `base_side_left/right` sloping sides | 2 | 2570.726012 × 139.7 × 88.9 |
| `eoere_cleat_left/right` | 2 | 361.186083 × 139.7 × 38.1 |
| `lumber_leg_left/right` | 2 | 2028.462988 × 139.7 × 88.9 |
| Four main panels | 4 | 1217.6125 width × 1219.2 height × 18.25625 |
| Two whole kickers | 2 | 1217.6125 width × 277 height × 18.25625; retain the miter profile |

The recorded stock scenario uses **13 sticks / 150 nominal board feet**:
six 2×6×8-ft, three 2×6×10-ft, two 4×6×8-ft and two 4×6×10-ft.
Nesting reserves 3.175 mm kerf per output and 12.7 mm trim at each stock end.
This is a nominal allocation, without an observed defect or usable-stock survey.
The model's 47 15/16-in panel width is not proof of the owned panels' cut size.

The [dated hardware basket][shop] is $148.51 before angles, tax and shipping.
The complete scenario is `$148.51 + 6*C4 + U`: C4 is one Eoere four-pack,
and U includes unpriced wood, services and tools. It is not a live quote.
Six four-packs provide 22 installed angles and two spares; pack spares do
not increase the installed counts above.

## 1. Label faces and lay out the cuts

Label every member and each matched left/right set before transferring marks.
The [layout appendix](builder-layout.md) preserves source **L/U/V** coordinates.
L follows grain. Most timbers use U across thickness and V across depth;
**the header instead uses U across its 139.7-mm depth and V across its
38.1-mm thickness**. Its U=0 reference is the narrow edge, and its receivers
run along V. Each member has its own world datum and positive-axis directions.
Negative V values elsewhere are intentional.
Mark the **U=0 reference face** and the named L=0 profile corner; an angled
end does not provide a square fence across the whole depth.

Use the indexed raw end/profile marks beside the [dimensioned projections][projections]
and exact [end datums][ends]. The projections are not scale marking templates
and omit finished bores, service cuts and rear recesses. Keep the right
principal's recorded 39.2-mm shift and the three longer right rails; do not
mirror the left lengths onto them. Listed decimal places preserve geometry,
not an adopted machining tolerance or saw setting.

Support both sides of each cut and clamp the work independently. The recorded
method uses a supported circular saw and a pull saw, with adequate free blade
depth and clamp clearance; the solid 88.9-mm 4×6 cuts use the pull-saw route.
Register angled cut planes with a rigid fence and mark both broad and thickness
faces from the same datum. Actual saw depth and cut accuracy remain unobserved.

For each rear leg, use the [recess section and definitions][recess]:

| Recess feature | Nominal source dimension |
| --- | ---: |
| Maximum removed thickness | 38.1 mm |
| Retained thickness at full depth | 50.8 mm |
| Full-depth interval ends | L180.342661 mm |
| 1:12 return ends | L637.542661 mm |
| Return length | 457.2 mm |

The circular-saw shoe requires coplanar support rails and an independently
clamped leg. Controlled relief cuts stay on the waste side, leave finishing
stock, and finish with a chisel/rasp. The rough depth must stay shallower than
the finished depth law across the entire kerf footprint. A centered 1/8-in kerf
alone consumes 0.132292 mm of taper allowance. The 2-mm nominal pad clearance
does not supply a fabrication tolerance. No relief-cut house is added.

## 2. Register and drill the through-bolt receivers

The [layout appendix](builder-layout.md) groups all **120 receiver occurrences**
by the 22 timbers and joins each to its selected bolt, bit and spacer. Entry
and exit are the source's increasing shaft-axis direction; they are not a
mandatory drill approach. At the rear-runner bolts, the
**left leg enters at U=50.8 and exits at U=0**; the
**right leg enters at U=38.1 and exits at U=88.9**. Both entries are on
the finished recess, whose raw inner face has a different U coordinate
on each side. Preserve each member's source frame and matched-set label.

Locate mating receivers at their intended seats with positive stops and
separate clamps. Preserve one registered setup for a paired pattern, using
an independent compatible guide, a backer and controlled breakthrough.
Factory angle holes are not qualified drill bushings. Independently marked
opposite-face holes and a short bit do not establish a common shaft path.
Use the bit maker's chip-clearing procedure without moving the registered parts.

| Shaft | Nominal starting wood bit | Recorded wood-hole range |
| --- | --- | --- |
| 3/8 in | 13/32 in | 13/32–7/16 in |
| 1/2 in | 17/32 in | 17/32–9/16 in |

Occupied CAD diameters are analysis envelopes. The proposed fixture uses a
19.05-mm guide plus 6.35-mm backer travel. The [axis-specific reach table][drilling]
requires:

| Wood path | Minimum usable bit projection below chuck |
| ---: | ---: |
| 38.1 mm | 63.5 mm / 2.5 in |
| 76.2 mm | 101.6 mm / 4 in |
| 88.9 mm | 114.3 mm / 4.5 in |
| 127 mm | 152.4 mm / 6 in |
| 177.8 mm | 203.2 mm / 8 in |

Additional guide flanges, pads or chip gaps increase reach and clamp opening
one for one. A 1/2-in chuck needs the specified reduced 1/2-in shank for the
long 17/32-in bit. Overall bit length alone does not prove usable projection.

The later [fixture worksheet][fixtures] finds nominal guide support and two
separate clamp-pad lands at all 120 receivers. Use its per-receiver pad
coordinates; the initial symmetric pad pair only fits 108. Actual guide
rigidity/play, clamp bodies and retention, drill/chuck approach and support
stability remain unqualified. Even the assumed 0.02-mm diametral guide play
leaves only **0.011771 mm** worst-case alignment reserve. A drilled wood
guide does not establish that precision. Those unresolved inputs hold the
affected operation; this continuation performs no actual-fit work.

## 3. Support and assemble the open frame

Follow the issued order while each member and subassembly has independent
support: runners, legs, sloping sides and posts; then header, principals and
rails; then seated exterior cleats and their angles. The cleats seat at
world Z139.7 mm. Their two top-edge heights above the seat are 194.698106 and
361.186083 mm; use the [cleat drawing][cleats] to identify the faces.

The assembly sequence specifies when support is required, but it does not
qualify a trestle, lifting method, clamp capacity or an unsupported partial
frame. Twelve tool/removal sides extend below Z0, by up to **93.221730 mm**.
Those operations require a raised or reoriented, independently supported
setup with the per-side clearance in the [access table][access]. The saved
floor assumption does not establish temporary-support stability.

Keep panels and wiring off while accessing structural bolts. Stage all shared
fittings before inserting their shaft; a shared shaft restrains both angles.
Hand-start each nut and counterhold the opposite side. Do not draw a mismatched
recess or misaligned holes into place by tightening. No installation torque,
preload, friction or locking capacity is assigned.

## 4. Use the selected stacks and access method

Use SAE J429 Grade 5 zinc-plated **full-body, partially threaded** hex cap
screws and matching specified nuts/USS washers. Each of the 100 stacks gets
one head washer and one nut washer. [Per-axis assignments][hardware] control
product identity, minimum body/grip requirements and the recipe.

| Bolt diameter / thread × underhead length | Installed |
| --- | ---: |
| 3/8-16 × 2.5 in | 60 |
| 3/8-16 × 3.5 in | 4 |
| 3/8-16 × 4 in | 4 |
| 3/8-16 × 4.5 in | 8 |
| 3/8-16 × 4.75 in | 16 |
| 3/8-16 × 6.5 in | 4 |
| 1/2-13 × 8.5 in | 4 |

Only `eoere_bolt_065`, `_066`, `_079`, `_080` and the four
`cleat_post_bolt_left/right_1/2` stacks receive the factory spacer:
**12.7 mm long × 19.05 mm OD × 10.31875 mm ID, after the nut washer and
before the nut**. Do not substitute washer packing. Nominal two-tip-pitch,
body and seating comparisons pass, but delivered shank/runout and actual
contact remain unknown. The other 92 rows do not establish smooth body
through every far wood surface; full-thread-root sensitivity is not adopted.

The [installation study][installation] refines access to all 200 sides using
nominal 9/16- and 3/4-in box wrenches: axial insertion, a continuous 60°
handle sweep, counterhold and complete removal. The modeled handle is
152.4 × 19.05 mm, at most 6.35 mm thick. Use the table's different working
and counterhold orientations. A 50.8-mm-long socket conflicts at 24 nut
sides; 25.4-mm socket seating clears all sides but does not qualify its
approach or driver. These are modeled tool envelopes, with actual tools
and receiving observations still blank.

## 5. Route services, then fit kickers and panels

With power disconnected and the frame open, use the [current channel drawing][channels]
and [receiver coordinates][channel-datums]. The common rounded section has
R6.35 mm, center N8 mm, front opening 20.427677 mm and rear depth N14.35 mm.
Control-route vertices describe a rounded swept envelope, not sharp corners
or a saw path. Support straight relief cuts inside waste and finish turns
and depth by hand. No machining-error budget or qualified jig is adopted.

The right principal retains `wire_072_F1_G1` and its bolt bores. Its eleven
former F-column arcs are filled; do not recreate them. Expanded-grid service
cuts are outside this base-grid plan. Keep the [owned LED system's instructions](../led-wiring-reference.md)
and controller access with its component references.

Fit **whole kickers first, then lower panels, then upper panels**. Use the
[340 current machining datums][panels], current [plate 1][panel-plate] and
unchanged [plate 2][panel-plate-2]. The two moves are
`round_kicker_left_rim_2` and `round_kicker_right_rim_2`: **Z192 → Z212 mm**.
The other 64 screw axes remain fixed. Do not use old Z192 holes.

Retain all **66 purchased Hillman 42605** panel/kicker screws. The owner's
policy is **1/8-in lead pilot, 3/8-in face countersink and #2 Phillips**.
These are owner-selected bit sizes, not Hillman-published values or the
5-mm CAD void. Do not substitute SPAX resistance, install inserts, drill
insert pilots or add panel fasteners. The two raised screws have nominal
backing and 26.9-mm post-top axis distance; end/splitting resistance remains
unqualified. Generic panel/screw reference exceedances stay deferred.

## 6. Unload and support before disassembly

Support each affected part independently. Manage/disconnect the harness and
remove upper panels, lower panels and kickers to recover the modeled tool
access. Remove each nut, its spacer where present, and nut washer before
withdrawing the shaft toward its head. Selected shaft travel is
**63.5–215.9 mm**, plus the head and handling/tool space. A shared shaft
releases both angles. Preserve labels and matched sets; no transport or
lift rating is supplied by the sequence.

## What remains before this is an executable build packet?

The [qualification ledger][qualification] separates completed numerical work
from three remaining engineering limits: complete cleat force/moment
resistance; compatible mixed-joint and finished-member resistance; and
physical stiffness/restraint sufficient to justify demands. Current cleat
normal-force/moment actions require a 295.602493-N necessary tensile
resultant in the governing case. It is a demand bound, without an adopted
transverse-tension resistance. The smaller force-only value is incomplete.

Generic head, withdrawal, panel and t6 heel exceedances are recorded
comparisons under their stated assumptions. The working t6.35/Ri6.35 heel
reference is 0.992604, without controlled product thickness/radius or
manufacturer capacity. None supplies a complete-joint pass. Panel/screw
remedies remain owner-deferred; actual-fit work remains excluded here.

Within the existing plan, affected operations still require compatible
delivered bolt/body/contact dimensions, qualified drill/guide/clamp reach
and alignment, and a stable support arrangement with the recorded access
clearance. Those observations are not replaced by model clearance or this
guide. No floor-friction test, native solve, geometry change or blanket
external sign-off is introduced. See [the document-scope map](../README.md#which-documents-are-current)
before following an older file that calls itself “current.”

[shop]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/README.md
[viewer]: https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-selected-hardware-frame-development&view=rear
[profiles]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/current_profiles.json
[ends]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/member-end-datums.csv
[projections]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/README.md#current-coordinates-and-drawings
[recess]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/rear-recess.svg
[nesting]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/stock-nesting.json
[holes]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/receiver-holes.csv
[channels]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/current-channels.svg
[channel-datums]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/service-channel-datums.csv
[panels]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/panel-machining.csv
[panel-plate]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/panel-layout-1.svg
[panel-plate-2]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/panel-layout-2.svg
[hardware]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/hardware-selection.csv
[stacks]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/hardware-stacks.svg
[installation]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/README.md
[access]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/access-methods.csv
[fixtures]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/drill-fixtures.json
[drilling]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/drilling-requirements.csv
[cleats]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/extended-cleats.svg
[forces]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/current-response-v1/result.json
[qualification]: ../wood-joints-mvp/completion-ledger.md#engineering-closure-beyond-the-assessment
