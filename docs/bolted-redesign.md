# Bolted-frame redesign: strength and buildability comparison

2026-09-07. **Development candidates, not construction approval.** These changes
respond to the [square-cut structural review](square-cut-structural-review.md).
Small deflections from bonded-joint, fixed-foot FEA did not qualify the original
connections or the freestanding structure. Wider stock and different fasteners
address identifiable weaknesses; they do not turn those results into a safety
rating for the new geometry. The redesigned candidates still require testing.

## Options considered

| Approach | Cutting and assembly | Strength characteristics and limitations | Decision |
| --- | --- | --- | --- |
| Longer flush structural screws in the original ledges | Fewest changes; one driver and no rear nuts | More embedded thread, but does not fix short loaded-edge distances, head pull-through or mixed-load qualification | Reject as a drop-in fix |
| A: wider 4×6 frame, through-bolted ledges, purchased ML24Z clips | Repeated square cuts; front counterbores and long matched holes; clips avoid large block-bolt groups | Through-bolts remove reliance on ledge-screw withdrawal; wider receiving faces improve geometric margins. Clip directional capacity and screw groups remain unqualified | Preferred first candidate for qualification |
| B: the same frame, 4×4 blocks and ¼-in through-bolts | Twelve identical block blanks, but more long holes, loose washers/nuts and wrench operations | Larger blocks improve geometric margins over the failed narrow blocks. Smaller bolts reduce required geometric distances but also reduce steel and wood-bearing resistance | Implemented comparison, not automatically stronger |
| Larger blocks retaining ⅜-in joint bolts | Larger stock or additional stock preparation; bulkier corners and longer holes | Potentially greater bolt resistance, but additional edge/end distances, bolt-group splitting, interference and access must be designed together | Reserve if B's quarter-inch resistance is inadequate; not modeled |

### Why a longer screw alone is insufficient

The [GRK R4 customer drawing](https://www.grkfasteners.com/getmedia/d8daea79-f2fb-40e5-9dc4-4efbedbaddf7/GRK-R4-Customer-Drawing-%281%29.pdf)
lists the #10 × 4 nominal screw as 3.94 in (100.076 mm) overall, with 2.60 in
(66.04 mm) thread and .193 in (4.9022 mm) major diameter. Its flush head is
compatible in principle with a panel installed over the ledge. It gives about
61.98 mm gross penetration through a 38.1 mm ledge, versus the old 25.4 mm.

However, the manufacturer's [ESR-3201](https://www.grkfasteners.com/getmedia/302e514d-0dfb-4c6f-b6a9-cd83243f4e46/ESR-3201.pdf)
Table 5 requires 4D for axial edge distance: 19.61 mm, already greater than a
38.1 mm receiver's 19.05 mm half-width. Perpendicular-to-grain loaded-edge
requirements are larger. Minimum embedment is not a complete connection check;
head pull-through, mixed loading, groups and wood splitting also govern. The
retrieved report is the July 2023 edition with July 2025 renewal date, not a
verified current approval. Its tabulated side-member thicknesses must not be
silently transferred to this different connection.

## Common redesigned framing

The climbing faces, official hold/LED layout, box-frame datum and plywood leg
profiles remain. Four nominal 4×6 uprights have actual 88.9 × 139.7 mm
(3½ × 5½ in) sections. The central pair remain full-length; the outer pair have
square lower ends above the retained kicker-splice profiles. Six beam spans are
identical 984.1 mm (38.744 in) long 4×6 blanks. This increases timber bulk and handling
weight compared with the former narrow 2×6 frame; equal section depth does not
mean equal weight or identical structural behavior.

The flat central ledges use standard 2×8 width, 184.15 mm (7¼ in), and the lower
flat rail uses standard 2×10 width, 234.95 mm (9¼ in). The wider lower rail permits
staggered connections around the retained lower profiles. Edge ledges, midpoint
and top ledges remain distinct stock sizes. These are square-ended members,
not a claim that the entire board consists of one repeated blank. Round service
reliefs and bolt holes still require accurate drilling.

Both candidates have 28 front-to-rear ⅜-in ledge bolts and eight lateral rim
bolts. Front ledge bolts use a 28.575 mm (1⅛ in) counterbore, 9.3392 mm deep,
in the **ledge only**, keeping the fastener beneath the climbing panel. That
pocket leaves about 28.76 mm of the 38.1 mm ledge locally. The pocket diameter
reserves clearance around an assumed 25.4 mm socket; actual socket access and
washer-bearing/net-section strength remain separate checks. Do not counterbore
the climbing plywood to accommodate these hidden connections.

The ⅜-in dimensional family follows the existing
[selected bolt specification](selected-bolt-hardware.md): Conquest A307 plain
hex bolts, finished nuts and two specified SAE-pattern washers. The
[supplier's A307 range](https://www.fastenersplus.com/collections/a307-hex-bolts)
includes the selected 7½-in front and 6-in rim lengths. Product availability is
not joint qualification. Maximum washer thickness is used in this candidate's
envelope. Eight leg-attachment bolts are now 7½ in long through the added outer
uprights. Their four-hole pattern moves 4 mm rear-normal for receiver edge
clearance; use the generated connection schedule, not an older drilling template.

## Differences at the beam joints

A retains twelve purchased ML24Z connectors and six SDS25112 screws per
connector, purchased separately. Do not alter factory holes or substitute
ordinary screws. The [2026 Simpson connector catalog](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf)
is the product basis; its tabulated directional arrangement is not an automatic
rating for the board's inclined, mixed-load joints. The modeled bend, factory
hole centers and tool allowances remain inspection proxies.

B replaces those clips and 72 screws with twelve 4×4 offcuts, actual
88.9 × 88.9 × 139.7 mm (3½ × 3½ × 5½ in). Grain follows the 139.7 mm length,
normal to the board. Each block has two lateral bolts to the upright and one
bolt to the beam: 36 quarter-inch assemblies overall. Outer upright bolts also
cross the rim, requiring longer hardware than the inner connections. The
model distinguishes 7½- and 9-in lengths; final grade, thread configuration,
product tolerances and practical sourcing remain unresolved.

Upper and midpoint blocks can provide downhill contact bearing. **Lower blocks
are uphill stops, not gravity seats.** Neither variant credits glue, clamp
friction, or end-grain withdrawal. B must pass both geometric checks and actual
¼-in fastener/wood resistance checks; passing a smaller-diameter edge rule is
not evidence of greater joint capacity.

## Practical assembly approach

1. Sort and label stock by actual section and grain direction. Use stop blocks
   for repeated spans and infills, preserving orientation marks after cutting.
2. Lay out a common board-plane datum on a flat, adequately supported work
   surface. Dry-clamp uprights, spans and ledges; check diagonals and face seating.
3. Establish official service reliefs before final drilling. Clamp mating
   members and use a perpendicular drill guide for long bolt paths. Avoid
   independently marking two ends and expecting the bores to meet.
4. Drill front pockets while ledges remain accessible, using a depth stop.
   Confirm the real socket can engage the head. Assemble hidden bolts and
   inspect rear washer/nut access before installing climbing panels.
5. For A, transfer purchased connector positions from the actual product. For
   B, label the block's grain and three bolt paths; keep outer long-bolt groups
   distinct from inner groups. Inspect for split stock and crossed holes.
6. Fit the retained kicker and legs using the candidate's current schedule.
   Install climbing panels only after hidden work is inspected. Temporary
   lifting/support and erection procedures require their own safe plan.

Bolt holes allow clearance and therefore initial movement; tightening is not
permission to crush the wood or assume a friction joint. No installation
torque is assigned here. Future reinspection must allow access to hidden
connections, normally by removing the climbing panels.

## Inspection files

| Candidate | Inspect and download |
| --- | --- |
| A: purchased clips | [3D viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=bolted-clip-frame) · [STEP](../exports/bolted-clip-frame/bolted-clip-frame.step) · [parts](../exports/bolted-clip-frame/bolted-clip-frame_parts.csv) · [hardware connections](../exports/bolted-clip-frame/bolted-clip-frame_connections.csv) · [grouped blanks](../exports/bolted-clip-frame/bolted-clip-frame_blank_groups.csv) · [hole entries](../exports/bolted-clip-frame/bolted-clip-frame_hole_entries.csv) |
| B: wood blocks | [3D viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=bolted-block-frame) · [STEP](../exports/bolted-block-frame/bolted-block-frame.step) · [parts](../exports/bolted-block-frame/bolted-block-frame_parts.csv) · [hardware connections](../exports/bolted-block-frame/bolted-block-frame_connections.csv) · [grouped blanks](../exports/bolted-block-frame/bolted-block-frame_blank_groups.csv) · [hole entries](../exports/bolted-block-frame/bolted-block-frame_hole_entries.csv) |

Schedules include metric and imperial dimensions. Hole entries refer to raw
member surfaces in board-local X/S/N coordinates, not the recessed bolt-head
plane. They are inspection records, not approved machining templates.

## Current checks and practical cost

The [source-bound screening record](../fea/results/bolted-frame/report.json)
uses the current drilled geometry, assumed wood density of 600 kg/m³ and clip
proxy density of 7,850 kg/m³. Fasteners, holds, LEDs and glue are omitted.

| Candidate | Included mass | Minimum edge-moment factor, 250 lb climber | Minimum factor, 300 lb sensitivity |
| --- | ---: | ---: | ---: |
| A: clips | 280.7 kg / 619 lb | 2.870 | 2.821 |
| B: blocks | 286.0 kg / 631 lb | 2.925 | 2.876 |

All 192 selected cases meet the illustrative 1.5 moment target. These include
150/200/250/300 lb climbers, 1×/2× downward gravity, 0/300 N horizontal forces
over all azimuths, 0/50/100 mm hold standoff and 80%/100% included mass.
They do **not** resolve joint strength, uneven floor contact, yaw/sliding,
dynamic response or the earlier opposite-normal/upward load questions.

**These are heavy designs, not easy-to-lift designs.** A's included mass rises
from the predecessor's approximately 189 kg to 281 kg. The wider receiver
approach reduces joint-layout difficulties at a substantial material and handling
cost. Assemble in manageable stages with a separately reviewed erection plan;
do not plan to lift a completed frame alone. A is preferred between these two
for fewer long-hole and block-bolt operations, not as a weight-optimized answer.

The 4×6 gross section has 2.33× the area and out-of-plane second moment of area
of the former 2×6 section at equal depth; its in-plane second moment is 12.70×.
Those are geometric, equal-modulus ratios—not whole-frame stiffness or capacity
ratios. No new bonded FEA is presented as proof of these changed joints.

Verification: 56 focused CAD, export, screen and historical-evidence tests pass.
They cover body/hardware intersections, receiver engagement and edge/end
distances, paired block-bolt spacing, assumed front socket access, official
service geometry, STEP solids, STL bounds/volume, raw-surface hole entries,
metric/imperial schedules and source hashes. Independent correctness, testing
and dataflow review passes found and corrected raw hole-entry coordinates and
missing receiver, spacing and viewer-volume regression checks. Actual hardware
tool sweeps and structural qualification remain outside those passes.
The local browser check loaded all 259 A and 223 B selectable meshes, selected
a rear upright, displayed metric/imperial dimensions and reported no page or
request errors. Front and selection screenshots were visually inspected.

Reproduce the focused checks with:

```sh
uv run pytest tests/test_bolted_frame.py tests/test_bolted_exports.py tests/test_bolted_screen.py tests/test_easy_structural.py
```

`uv run python -m fea.bolted_screen` regenerates the screen only in a fresh
checkout without the published report; it deliberately refuses to overwrite
existing evidence. The report records its source and export-manifest hashes.

## Remaining qualification gates

- Check all solid intersections, fastener heads, counterbores, crossing axes,
  official service reliefs and actual driver/socket access on the final revision.
- Check wood grade/species, washer bearing and bending, reduced sections,
  splitting, bolt groups, combined loads and connector directionality.
- Reanalyze the changed structure with joint and unanchored-support assumptions
  that represent its actual load path; older bonded FEA cannot approve it.
- Retained shaped plywood legs, independent plies, leg joints and the kicker
  splice remain unresolved strength details. Their reuse is not approval.
- Verify freestanding stability and site contact. The separate crash pad is
  excluded; anchors, hidden ballast and glue/friction capacity are not assumed.

Prefer A for the next qualification step because it avoids B's long quarter-inch
block-bolt groups and their extra assembly work. If its purchased-connector
configuration cannot be qualified, revisit the joint detail rather than treating
either a stiffer FEA plot or a larger block as sufficient evidence.
