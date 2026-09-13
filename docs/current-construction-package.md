# Current DIY construction package

This package records the **277 mm, shoe-free `no-shoes-development` candidate**
with single 2×6 support legs. It supplies a current stock schedule, connection
coordinates, panel drilling coordinates, hardware inventory and assembly sequence.
The endpoint is an **engineer-unreviewed DIY design**. Independent engineer review
is not an owner-required completion condition.

The existing four-bolt leg joint remains provisional. Its coordinates below
identify the modeled detail; they are not a recommendation to drill that joint
before its connection decision is resolved. The [completion record](current-diy-completion-record.md)
separates completed documentation from that outstanding design decision. This
package does not establish a safe climber rating.

## Use this revision

- [Current model and selectable components](https://mckayreedmoore.github.io/mini-moonboard/?model=no-shoes-development&view=rear)
- [Current STEP assembly](../site/hybrid/no-shoes-development/assembly.step)
- [Stock blanks, one row per physical member](current-construction/stock.csv)
- [All 218 modeled connection axes](current-construction/connection-axes.csv)
- [All 66 panel and kicker attachment axes](current-construction/panel-attachment-axes.csv)
- [Panel hold and LED hole coordinates](current-construction/panel-hole-axes.csv)
- [Current enclosed timber passages and entry/exit dimensions](current-construction/timber-passages.json)
- [Raw stock profile vertices, including bevels](current-construction/stock-profiles.json)
- [Schedule provenance](current-construction/manifest.json)

The CSV coordinates are in millimeters. Dimensions govern; the viewer is not a
scale drilling template. The schedule generator reads the current standalone
inventory and current coordinate factories, rather than copying a historical
cutlist. Regenerate it from the repository root with:

```sh
uv run python -m scripts.current_construction_schedule
```

The preceding 225 mm kicker drawings, shoe designs and 2×8 comparison are
historical. Do not combine their leg lengths, floor cuts, drilling or hardware
with this package.

## Datums and material

The floor is world **Z = 0**. X spans the wall, with the center at X = 0.
Positive Y points rearward. The main-face datum is Z = **277 mm**, comprising
150 mm of exposed kicker above a nominal 127 mm (5-inch) pad. The 127 mm pad covers the entire lower front section across the full wall
width, leaving 150 mm of kicker exposed. The pad supplies clearance only and
does not support the frame; structural feet bear directly on the floor, not on
the pad. The main face is inclined
40 degrees from vertical. Its panel-local S coordinate runs upward along the
slope from the main-face datum; S is not world Z.

Panel coordinates are viewed from the climbing face. “From left” means the
individual panel's left edge in that view. Main-panel “from bottom” follows S;
kicker “from bottom” is vertical from the floor. Keep left and right panels
labeled so these references are not mirrored during rear-side work.

Retain the owned Roseburg AC exterior PS 1, 23/32-category plywood. The model
uses 18.25625 mm thickness. Use dry, unincised, grade-stamped Douglas Fir–Larch
No. 2 or better for the dimensional lumber assumed in the calculations. Actual
sheet dimensions, stock thickness, grain orientation and defects affect layout;
check them before cutting, without treating this as a new plywood qualification
campaign. The [purchased-material record](purchased-materials.md) identifies the
owned plywood.

## Adapting to a different pad height

To retain the intended exposed kicker height, use:

```text
floor-to-main-face datum = 150 mm + actual selected pad height
change from this package = selected pad height − 127 mm
```

Change both kicker panels and all four posts by that vertical difference. Move
upper-frame, bracket, panel, LED and T-nut datums consistently. Recalculate the
rear-leg lengths and level foot cuts while retaining the selected grain angle;
this moves the rear footprint as well as changing leg length. Regenerate the
cutting/drilling schedules, fit checks and affected structural response for the
changed geometry. These equations describe a coordinated design revision, not
permission to extend only one component or use the present leg length unchanged.

The current generator extends inherited 225 mm geometry using a positive
`HEIGHT_CHANGE_MM`. Arbitrary pad heights are not supported merely by editing
`PAD_HEIGHT_MM`: pad heights at or below 75 mm require explicit zero-extension
or stock-shortening handling before regeneration. The equations above are the
required design relationship, not a claim that this parameter range is already
implemented or checked.

Simply replacing the pad without changing the frame leaves the present 277 mm
face datum fixed. The exposed kicker then becomes **277 mm minus pad height**,
which changes the intended Mini MoonBoard setup. Pad compression is not modeled.

## Cutting schedule

These are finished model blank envelopes, before allowance for saw kerf,
squaring or defective stock. A blank length is not automatically a square-cut
finished length; inclined bearing ends and panel transition profiles must match
the STEP geometry.

| Members | Quantity | Nominal stock | Blank dimensions, mm |
| --- | ---: | --- | --- |
| Main panels | 4 | Owned 23/32-category plywood | 1219.2 × 1219.2 × 18.25625 |
| Kicker panels | 2 | Same plywood | 1219.2 × 277 × 18.25625 |
| Outer inclined rims | 2 | Single 2×6 | 2608.024 × 139.7 × 38.1 |
| Center inclined principals | 2 | Single 2×6 | 2532.626 × 139.7 × 38.1 |
| Top rail | 1 | Single 2×6 | 2362.2 × 139.7 × 38.1 |
| Split bottom and four service rails | 6 | Single 2×6 | 1092.05 × 139.7 × 38.1 |
| Rear support legs | 2 | Single 2×6 | 1861.826 × 139.7 × 38.1 |
| Header | 1 | Single 2×10 | 2438.4 × 234.95 × 38.1 |
| Outer and center posts | 4 | Single 2×10 | 238.9 × 234.95 × 38.1 |

The header is a horizontal 38.1 mm-thick member with its top at Z = 277 mm;
all four 238.9 mm posts bear below it and reach the floor. Keep the center
service corridor open. Adjacent panels remain separate and are not glued or
joined across their seams.

The rear legs have square top cuts and level floor cuts. Their current length
includes the extended floor contact and the long point of the foot bevel. Their
top extends 177.105 mm along grain beyond the current bolt-group centroid.
The historical leg factory used 150 mm beyond its original datum; downstream
drilling moved the current group 27.105 mm downhill along the same leg. Preserve the
actual leg orientation and bevel; a square cut at the listed overall length
would not produce the modeled bearing foot. The two outer rims retain timber
bearing against the header, without the historical 9.525 mm shoe-clearance trim.
Use fresh stock without the omitted shoe holes.

## Hardware inventory

| Item | Quantity | Application |
| --- | ---: | --- |
| SPAX XFT08P-2000 #8 × 2-inch flat countersunk T-STAR Plus screws | 66 | Twelve per main panel and nine per kicker |
| Simpson ML24Z angles | 24 | Current frame, including the two restored outer-rim/header angles |
| Simpson SDS25112 1/4 × 1.5-inch screws | 144 | Six per ML24Z, three in each flange |
| Existing 3/8-16 × 3.75-inch modeled leg bolts | 8 | Four per leg; provisional connection detail |
| Matching nuts | 8 | One per modeled leg bolt |
| Matching washers | 16 | One under each bolt head and nut |
| Owned-type Escape three-hole 3/8-16 T-nuts | 142 | 132 main-face positions and ten kicker positions |
| Custom base shoes, shoe bolts and shoe bearing plates | 0 | Not part of this candidate |
| Panel inserts and machine screws | 0 | Future space reservation only |

Bolt heads face outside and nuts face inside. The existing leg bolt product,
washer geometry and thread location are part of the unresolved connection
assessment; do not substitute the historical smooth-bolt candidate or a larger
bolt merely because it fits the hole.

T-nut retention screws and hold bolts are not included in the modeled inventory.
Use the actual T-nut installation instructions for its retention hardware; the
three modeled holes do not establish a selected retention-screw length. The
[hold-bolt guidance](moonboard-hold-hardware.md) records published kit lengths
separately from per-hold installation. Confirm each hold's seating and thread
engagement with the supplied hold hardware; the display model does not locate
hold recesses or assign bolts to individual plastic holds.

## Drilling and fastener installation

Use the panel-hole CSV for the current fixed grid: hold holes are modeled at
11.1125 mm (7/16 inch), and panel LED holes at 13 mm. Main-panel grid coordinates
are measured along the panel itself. Kicker hold heights already include the
277 mm datum; do not add another 52 mm or 127 mm.

Use the panel-attachment CSV for the SPAX axes. The original four attachments
per kicker are supplemented by five header attachments at local X magnitudes
200, 400, 600, 800 and 1000 mm, at floor height **257.95 mm**. Each independent
kicker therefore has nine screws. Their other attachment rows are at floor
heights 112 and 192 mm.

Use the selected SPAX installation guidance and a controlled-depth countersink
to obtain a flush head without crushing the face veneer. Establish the seat on
an offcut first. The model's screw cylinders depict occupied fastener geometry;
they do not prescribe a pilot diameter or an insert pilot. Keep possible future
insert space intact and undrilled. Use the specified SDS screws in all six
scheduled holes of each ML24Z; do not substitute generic screws or overdrive the
heads.

The connection CSV gives each connection's start point, unit axis, length,
diameter and two members. The start point follows the specific fastener model's
head/under-head convention; it is an assembly coordinate, not a local timber
edge offset. Use panel-local coordinates for panel layout and the commercial
bracket itself as the manufacturer-specified screw-hole pattern. Leg axes remain
provisional, with modeled 11.1125 mm clearance holes for 9.525 mm bolts.

Enclosed timber LED passages are 38.1 mm (1.5 inches) only in nominal 2×6 stock
and 25.4 mm in other members. They are separate from panel LED and hold holes.
Their circular sections must remain enclosed; do not substitute front-open wire
slots. A centered 38.1 mm bore in exactly 139.7 mm stock leaves 50.8 mm on each
side at that section. Real stock and drilling tolerances matter. The timber-passage JSON supplies each current entry/exit point, drilling
direction, through length and offsets from the member edges. Its coordinates
include the 52 mm rise. Use these dimensions with the labeled stock; do not
arbitrarily extend a hole through an additional receiver.

## Assembly sequence

1. Label all members and panels; establish the floor and face datums on a stable
   assembly surface. Check the intended installation against the no-sliding
   assumption recorded in the completion record.
2. Cut the labeled stock and required bearing profiles. Dry-fit the header and
   four posts so the header top is 277 mm above their common floor datum.
3. Lay out the inclined rims, two center principals, top rail, split bottom rails
   and four service rails. Keep the central service corridor open. Verify the
   independent panel edges sit on the intended receivers.
4. Prepare the scheduled panel holes and enclosed wire passages with clamped
   guides and backing to control breakout. Keep front/rear and left/right
   references marked. Do not machine future insert reserves.
5. Fit the 24 commercial angles and 144 specified SDS screws. The two restored
   outer angles connect the outer rims to the header alongside actual timber
   bearing. No base shoes or shoe-clearance gaps are installed.
6. Dry-fit both support legs with temporary support maintained. Complete their
   permanent drilling and hardware only against the resolved leg-connection
   detail. Temporary assembly support is not an installed structural member.
7. Install the T-nuts while rear access is available, following the actual
   product instructions. Fit the panels using their 66 scheduled SPAX screws,
   maintaining the separate seams and flush head seats.
8. Feed the intact factory LED harness through the prepared passages and fit
   lights after the panels. Retain factory connectors, controller, power supply,
   supplemental lead and unused tail. Verify access and slack with the actual
   harness; do not cut or splice it to force a route.
9. Fit holds using their appropriate supplied hardware. Confirm seating and
   usable thread engagement individually; keep electrical wires clear of bolts.
10. Inspect the assembled geometry, bearing contacts, complete bolt stacks,
    bracket screw counts, panel seating and clearance before removing temporary
    support. Record any departure from the package and reconcile it with the
    leg assessment before climbing use.

## Inspection and maintenance

Inspect for loose hardware, wood splitting near the leg joint, crushed washer
seats, opening bearing gaps, panel movement and damaged wiring. Recheck after
initial settling, relocation or disassembly, and after an unusual impact or
visible movement. Follow the hardware manufacturers' tightening instructions;
no unsupported numerical torque or destructive proof-load procedure is assigned
by this package. A damaged hole is a repair decision, not permission to install
a larger screw or bolt without checking the resulting detail.

The [DIY completion record](current-diy-completion-record.md) is the companion
statement of assumptions and remaining limits. Documentation completeness does
not override the outstanding leg-connection result.
