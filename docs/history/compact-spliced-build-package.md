# Compact frame with independent spliced knees: DIY build package

**Status: completed conditional DIY build package with a checked end-trim
revision.** The preserved assembled baseline passes all 21 listed conditional
criteria in six load cases; its worst adopted bolt ratio is **0.674**, against
a limit of 1.0. The current package adds outward bolt ends and exterior timber
trims. Their [installation check](compact-spliced-construction/bolt-installation-check.json)
and [end-detail check](compact-spliced-construction/end-trim-check.json) accompany
the [baseline assessment](compact-splice-study.md).

The trim assessment reuses the six baseline force cases and checks current
receiver fit, end distances, local connections and hardware. It retains the
original connected-section/stability results and approximates the stiffness
and gravity effects of the removed exterior tails; no new assembled native
solve was performed. This is the project's engineer-unreviewed DIY endpoint,
not an unconditional climber weight rating. Construction follows the exact
stock, hardware and installation conditions below.

## Design and package

The frame retains single 4×6 legs and panel-edge-flush outer rims, the compact single
2×6 header/posts and the 277 mm floor-to-main-face datum. Each leg connects
to its rim with two ½-inch bolts at 56 mm pitch. Each diagonal knee comprises
two separate, unnotched single 2×6 pieces: four ⅜-inch bolts connect their
overlap, and two ⅜-inch bolts attach each endpoint to its host member.
There is no assumed composite action between overlapping knee pieces.
The knee tips are cut flush to their adjoining host's exterior depth face.
Rear-leg tops retain **18 mm projection normal to the rim's rear face**;
cutting them completely flush would violate the retained upper-bolt end-distance
reference. Use the individual profiles for these cuts, not an assumed square end.

The [generated packet](compact-spliced-construction/) contains the following:

| File | Use |
| --- | --- |
| `stock.csv` | All 28 timber/panel blanks and their nominal dimensions. |
| `base_side_left-bolt-sheet.svg`, `base_side_right-bolt-sheet.svg` | Full rim side profiles, physical datums and upper/knee bolt ordinates. |
| `lumber_leg_left-bolt-sheet.svg`, `lumber_leg_right-bolt-sheet.svg` | Full leg side profiles, physical datums and upper/knee bolt ordinates. |
| `base_knee_left_rim-bolt-sheet.svg`, `base_knee_left_leg-bolt-sheet.svg`, `base_knee_right_rim-bolt-sheet.svg`, `base_knee_right_leg-bolt-sheet.svg` | Separate knee-piece profiles and endpoint/splice bolt ordinates. |
| `bolt-member-datums.csv` | Exact coordinate source for every sheet's connection IDs and physical corner. |
| `bolt-hardware.csv` | Modeled bolt/washer/nut envelopes and member ownership. |
| `connection-axes.csv` | All 230 connection axes, including panel and commercial-angle screws. |
| `timber-passages.json` | Enclosed LED passage dimensions and coordinates. |
| `panel-attachment-axes.csv`, `panel-hole-axes.csv` | Accepted panel screw, hold and LED layouts. |
| `stock-profiles.json`, `outer-rim-end-trim.svg` | Raw profiles and the retained 7 mm rear-overhang trim detail. |
| `bolt-installation-check.json` | Outward bolt installation, unchanged axes and hardware equivalence evidence. |
| `end-trim-check.json` | Current trim geometry, receiver/local checks using six retained force cases, removed mass and explicit response approximation. |
| `manifest.json` | Source/inventory/generator hashes and generated artifact hashes. |

The eight bolt sheets show profiles, bolt ordinates and the new end-cut
angles/endpoints. They are not a complete
machining definition by themselves. Use the passage and screw-axis schedules
too. Identify datum D on the actual minimum-X side-face profile, then follow
the positive grain and cross-grain arrows. Cross-grain ordinates are signed.
The short H labels map to full connection IDs in each sheet's table and CSV.
Use the stated dimensions, not image scale. Left/right sheets are individual
parts; do not substitute an assumed mirror jig. Use the installation dimensions
and acceptance conditions below; displayed fastener body dimensions are not
screw pilot sizes.

## Hardware and material basis

| Function | Quantity | Catalog assessment |
| --- | ---: | --- |
| Upper leg/rim bolts, ½-13 × 8 inches | 4 | [Half-inch Grade 5 hardware](compact-half-inch-hardware.md) |
| Brace-to-host bolts, ⅜-16 × 6 inches | 8 | [Splice/endpoint hardware](compact-splice-hardware.md) |
| Knee splice bolts, ⅜-16 × 4 inches | 8 | [Splice/endpoint hardware](compact-splice-hardware.md) |

Use one matching nut and two specified washers per bolt: 20 nuts and 40
washers overall, separated by bolt diameter. The linked catalog assessments
identify concrete products and preserve minimum dimensions, thread/runout,
material-conformity and washer-yield conditions. The CSV describes modeled
envelopes; those nominal envelopes do not supersede catalog tolerances or
the resistance envelope. Existing ML24Z/SDS connections and the accepted 66
panel/kicker screws remain in the connection schedule. No insert pilots or
custom steel fabrication are introduced.

Use the [material basis](leg-material-basis.md) and the
[current design basis](current-design-basis.md) with the final assessment.
The owner accepts the panel/T-nut construction as the basis and excludes
floor-friction qualification. Calculations assume no-slip floor support;
that assumption does not establish measured friction or an installed anchor.
This package adds no panel or floor-friction test prerequisite.

## Drilling and installation

Use fresh, dry stock of the specified grade, with the actual sections in the
stock schedule: 88.9 × 139.7 mm for legs/rims and 38.1 × 139.7 mm for knee
pieces. Do not reuse the abandoned three-bolt holes or substitute smaller
finished sections. Check dimensions before transferring the individual datums.

The nominal end-cut angles measured from square are **36.16° at the rear-leg
top**, **4.27° at the rim-end knee tip**, and **49.57° at the leg-end knee tip**.
The last exceeds a common 45° miter-stop range: use an appropriate saw setup
or a securely clamped cutting jig, following its tool instructions. The
rim-end knee cut retains only **0.361 mm** beyond the adopted end-distance
reference after the existing 3 mm geometric allowance. That reserve is not
extra cutting tolerance; preserve the specified line and verify the finished
bolt-to-end distances before assembly.

Clamp a drill guide and back the exit face. Target each bolt centre within
±0.5 mm of its sheet ordinate, and each cut edge within ±1 mm of its specified
position. These are project fabrication targets: the resistance geometry
already erodes the stock boundary by 3 mm, but the narrowest bolt-spacing
reserve is only 1.9 mm. Check the finished spacing as well as individual marks;
do not consume that reserve by moving adjacent holes toward each other.

The modeled clearance bores are **9/16 inch (14.2875 mm)** for half-inch bolts
and **7/16 inch (11.1125 mm)** for three-eighths bolts. Those are the upper end
of the NDS clearance allowance: actual holes must remain between bolt diameter
plus 1/32 inch and plus 1/16 inch. Align the two members accurately; bolts must
enter without being driven. Do not enlarge a misaligned hole to force assembly.
These requirements follow [NDS §12.1.3](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf).

Install all 20 bolts with heads toward the board center and nuts/threaded
ends outward: toward negative X on the left and positive X on the right.
The installation model reverses the four upper bolts, four rim-end bolts and
eight splice bolts; the four leg-end bolts already face outward. The bolt
reversal leaves hole locations, bolt sizes and counts unchanged; the exterior
wood trims are assessed separately. Fit the scheduled
washer beneath both head and nut, with full, flat wood seating. Confirm full
usable nut engagement and freedom from thread runout before tightening. For the specified nominal-diameter resistance route,
measure from under the head to the first reduced shank/thread transition:
minimum **158.9278 mm for upper bolts**, **120.1166 mm for rim endpoints**,
**107.4166 mm for leg endpoints**, and **69.3166 mm for knee splices**, using
the maximum head-washer thickness and scheduled wood grip. Recalculate these limits for actual grip and washer
dimensions as described in the hardware assessments. Catalog minimum thread
length does not guarantee these shank lengths. Reject unsuitable hardware;
do not silently switch to the root-diameter sensitivity as a build basis.

Use snug, fully seated assemblies without crushing wood beneath washers;
no steel-joint torque value is assigned to these timber joints. Follow the
supplied hardware instructions and recheck after initial wood settling.
Use all six specified SDS screws in each scheduled ML24Z, without generic
screw substitution or overdriving. Install the selected SPAX screws with a
controlled flush head seat; establish the countersink on an offcut without
crushing face veneer. Screw occupied diameters are not pilot instructions.
Retain the factory LED harness and connectors; keep wiring clear of bolts.

Keep all nine kicker screws per half. The four lower post screws are at Z60 mm
from the floor, lowered 52 mm from the preceding installation. Maintain at least
44.45 mm from the actual post bottom. The upper post row is nominally 46.9 mm
below the post top, with only 2.45 mm reserve above the 44.45 mm loaded-end
reference. Mark from the actual post top and verify that minimum before driving;
do not round the row upward. The header row remains centered at Z257.95 mm.
See the [kicker placement review](kicker-screw-placement-review.md) for receiver,
embedment, hardware-clearance and pad-access checks.

Inspect the completed member datums, floor and header bearing contacts,
washer seats, hardware counts, panel seating and service clearance. Loose
hardware, splitting, crushed seats or changed bearing gaps require correction
before use. Repeat this inspection after relocation, disassembly or an unusual
impact. These are ordinary fabrication and assembly checks, not an added floor
friction or destructive proof-test requirement.

## Assembly sequence

1. Identify the exact candidate and matching packet manifest. Sort and mark
   every timber blank with its full member name, grain direction and datum D.
   Confirm actual stock and hardware against the final specification before
   laying out holes.
2. Cut the raw member lengths and end profiles. Preserve the specified
   header depth and 7 mm rear projection. Apply the drawn knee tip cuts and
   retain the 18 mm rear-leg top projection; add no notches to the knee pieces.
   Lay out bolt holes from each member's own datum, and complete the scheduled
   LED passages and screw operations using the final installation details.
3. Assemble each leg/rim side pair with its two upper bolts while supported
   in its required geometry. Position its two knee pieces on their specified
   opposite faces. Fit their endpoint and four overlap bolts with complete
   washer/nut stacks, heads inward and nuts/threaded ends outward. Keep the
   overlap pieces independent; add no adhesive or unscheduled fastening to
   imply composite action.
4. With temporary support maintaining alignment, assemble the header, posts,
   principals and shortened rails using the scheduled commercial angles and
   screws. Check floor contact, member positions, trim bearing and service
   access before closing the frame with panels.
5. Route wiring through the scheduled passages, then install the accepted
   panels and kicker using their separate attachment layouts. Preserve open
   service access and the pad allowance; the pad is not a structural support.
6. Complete the final specified hardware installation and dimensional checks,
   including washer seating, usable nut threads, intended gaps and brace
   placement. Do not infer a bolt torque or pilot diameter from the rendering.
   Remove temporary support only after the specified assembly requirements
   are satisfied.

## Regeneration

```sh
uv run python -m scripts.compact_spliced_exports
uv run python -m scripts.compact_spliced_construction
```

The exporter produces the complete candidate viewer/STEP bundle. The schedule
generator refuses a stale export manifest and creates the CSV, profile and
SVG files from matching model data. Generated dimensions apply to this selected revision and its stated
material, hardware, load and installation conditions.

## Lower kicker screw update

The current `compact_spliced_kicker` adapter moves four lower kicker screws from
Z112 to Z60 mm. Horizontal positions, the Z192 upper row, the Z257.95 header
row, screw product and count remain unchanged. Fresh-stock geometry closes the
old bores and represents the new bores and head seats. This is not an instruction
to repair already-drilled stock.

The existing accepted panel-construction scope is retained. Local placement and
receiver checks support this installation change; the six archived native solves
still contain the preceding screw axes. Do not describe those archives as six
fresh solves of this screw relocation or as a new panel-resistance qualification.
