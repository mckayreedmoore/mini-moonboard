# Compact frame with independent spliced knees: DIY build package

**Status: completed conditional DIY build package.** The selected
`compact-spliced-knee-development` passes all 21 listed conditional criteria
in all six current assembled load cases. The worst adopted bolt ratio is
**0.674**, against a limit of 1.0. See the [complete assessment](compact-splice-study.md)
for the finite load set, numerical checks and remaining analytical limits.
This is the project's engineer-unreviewed DIY endpoint; it does not establish
an unconditional climber weight rating. Construction follows the exact stock,
hardware and installation conditions below.

## Design and package

The frame retains flush single 4×6 legs and outer rims, the compact single
2×6 header/posts and the 277 mm floor-to-main-face datum. Each leg connects
to its rim with two ½-inch bolts at 56 mm pitch. Each diagonal knee comprises
two separate, unnotched single 2×6 pieces: four ⅜-inch bolts connect their
overlap, and two ⅜-inch bolts attach each endpoint to its host member.
There is no assumed composite action between overlapping knee pieces.

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
| `manifest.json` | Source/inventory/generator hashes and generated artifact hashes. |

The eight bolt sheets show nominal profiles and dimensions, not a complete
machining definition by themselves. Use the passage and screw-axis schedules
too. Identify datum D on the actual minimum-X side-face profile, then follow
the positive grain and cross-grain arrows. Cross-grain ordinates are signed.
The short H labels map to full connection IDs in each sheet's table and CSV.
Use the stated dimensions, not image scale. Left/right sheets are individual
parts; do not substitute an assumed mirror jig. Use the installation dimensions and acceptance conditions below; displayed
fastener body dimensions are not screw pilot sizes.

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

Fit the scheduled washer beneath both head and nut, with full, flat wood
seating. Confirm full usable nut engagement and freedom from thread runout
before tightening. For the specified nominal-diameter resistance route,
measure from under the head to the first reduced shank/thread transition:
minimum **158.9278 mm for upper bolts**, **107.4166 mm for knee endpoints**,
and **69.3166 mm for knee splices**, using the maximum head-washer thickness
and scheduled wood grip. Recalculate these limits for actual grip and washer
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
   header depth and 7 mm rear projection; keep all four knee pieces unnotched.
   Lay out bolt holes from each member's own datum, and complete the scheduled
   LED passages and screw operations using the final installation details.
3. Assemble each leg/rim side pair with its two upper bolts while supported
   in its required geometry. Position its two knee pieces on their specified
   opposite faces. Fit their endpoint and four overlap bolts with complete
   washer/nut stacks. Keep the overlap pieces independent; add no adhesive
   or unscheduled fastening to imply composite action.
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
