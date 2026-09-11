# Round-passage service candidate: purchasing and assembly draft

[Materials and hardware](#package-status-and-purchasing-basis) ·
[Tools and equipment](#tools-and-equipment) ·
[Assembly sequence](#machining-and-assembly-sequence) ·
[Disassembly](disassembly-guide.md)

The `round-bore-service-development` candidate replaces the preceding open-front
wire grooves with 32 enclosed, nominal 25.4 mm timber passages. The owner reports
a maximum harness-component diameter of 12.7 mm and approximately 304.8 mm
between bulb bases. These measurements inform clearance development; they do
not establish bend clearance, installation force or guaranteed usable cable length.
This candidate is **not build-ready**. The earlier grooved-frame FEA does not
qualify the new round-bore geometry.

## Package status and purchasing basis

The generated export package is `exports/round-bore-service-development/`, with
`wood-parts.csv`, `connections.csv`, assembly STEP, wiring/passage schedule and
source manifest. The matching [drilling schedule](round-service-drilling/drilling.json) and
[drilling PDF](round-service-drilling/drilling.pdf) describe this candidate. Do not drill the new passages from the old
grooved-model drawings or use a visualization as a scaled template.

Lumber blanks remain those in the
[preceding stock allocation](horizontal-service-build-plan.md#timber-stock-allocation-from-the-generated-cutlist):
two 2x6 × 12 ft, four 2x6 × 10 ft, two 2x6 × 8 ft and one 2x10 × 12 ft.
That allocation includes 3.2 mm kerf per blank and 12.7 mm total end trim per
board; the two principal/rail combinations require at least 3643.776 mm usable
length. Reconcile every blank against the new export before cutting.

Retain dry, grade-stamped Douglas Fir–Larch No. 2 or better for the remaining
lumber. **Keep the owned Roseburg face plywood**, Lowe’s item 12235 / model
119055, recorded as AC exterior PS 1, 23/32 category in the
[purchased-material record](purchased-materials.md). Verify this lot’s usable
dimensions, thickness, stamp and strength axis; Structural I designation has
not been established. Structural I 48/24 plywood was a provisional research
alternative, not identification of the purchased sheets or an instruction
to replace them. The six modeled panels are four 1219.2 mm squares and
two 1219.2 × 225 mm kickers, with modeled thickness 18.25625 mm. Four sheets,
one main square per sheet and kickers from offcuts, remain a provisional stock
allocation: verify actual usable dimensions, thickness, edge condition and kerf.
Do not resize the panel grid to fit undersized stock.

| Hardware | Current development basis | Purchasing status |
| --- | --- | --- |
| Panel/kicker attachments | 56 SPAX XFT08P-2000 #8 × 2-inch screws: 12 per main panel and four per kicker | Mirrored development pattern; count and connection resistance remain unqualified |
| Commercial brackets | 24 ML24Z angles and 144 SDS25112 screws | Six specified screws per angle; no bracket-to-bolt substitution selected |
| Leg bolts | Eight 3/8-inch × 3¾-inch (95.25 mm) bolts, eight matching nuts and sixteen washers | One washer at each end; head outside and nut toward the frame interior; match the complete connection schedule and supplied dimensions |
| Owned lighting | V5 three-string kit, controller, original power supply and supplied leads | Inventory existing equipment; do not replace the factory harness with cut/spliced sections |
| Hold hardware | 132 main plus ten kicker T-nut positions | Reconcile owned hold/T-nut kit and per-hold bolt lengths; separate from panel attachment screws |
| Removable-panel inserts | Separate development option | None installed by this plan; fit and resistance must support a selected product |

Use the [purchased-material record](purchased-materials.md) for the owned
plywood and remaining lumber specification. The historical horizontal plan’s
Structural I research selection does not override the existing face-panel purchase. Actual delivered material properties remain to be
verified; neither the selected specifications nor prior isotropic FEA establish
connection resistance.

## Tools and equipment

Review the [front-view screw placement diagram](round-panel-screw-layout.svg)
before marking the panels. Blue dots identify attachment screws; gray dots
provide hold-grid context. The diagram shows symmetry, not drilling dimensions;
use the matching PDF coordinates for fabrication.

Inventory owned tools before buying; tool costs are separate from the material
schedule. This list covers the proposed operations, but required reach and
capacity must match the final drawings and workpieces.

| Operation | Required equipment and fit checks |
| --- | --- |
| Measuring and labeling | Metric/imperial tape, steel rule, square, straightedge, bevel gauge or angle finder, pencil, labels; calipers for actual plywood, hardware and harness dimensions |
| Stock cutting | Suitable crosscut/bevel saw; guided circular/track saw for plywood; sharp wood blade with measured kerf; secure clamps, sacrificial backing and supported infeed/outfeed |
| Passage drilling | 25.4 mm (1-inch) wood bit, appropriate drill, guide/jig and depth reference; enough usable bit reach for the longest passage and access to the specified entry face; drill-press support or secured portable jig where applicable |
| Hold and leg bores | 11.1125 mm (7/16-inch) wood bit for current modeled hold-T-nut and structural-bolt bores; hold bore remains subject to the selected Escape product fit, not Moon's generic bore size |
| LED panel bores | 13 mm wood bit for the current LED seating holes, with backing to reduce breakout; verify supplied bulb seating before production drilling |
| Panel screws | T20 driver bit and controllable drill/driver; check reach to every retained screw axis |
| Panel-face countersinking | 90-degree included-angle wood countersink matched to the SPAX head, controllable drill or drill press, depth stop and representative plywood offcut; finished depth requires actual seating setup |
| ML24Z screws | 3/8-inch hex driver for SDS25112, with suitable clearance around the integral screw head; extension or right-angle access only where the physical tool fits the approved axis |
| Leg bolt stacks | Nominal 9/16-inch socket and matching backup wrench for the modeled standard 3/8-inch hex heads/nuts; confirm actual supplied flats; socket depth must clear protruding threads at inside nuts |
| Surface finishing | Deburring tool, sandpaper and sanding block; dust extraction; avoid unreviewed chamfers or enlarged holes |
| Lighting installation | Labels, flashlight and gentle component feeding by hand; no wire cutters, strippers or crimpers are required for the intact factory-connector assembly route |
| Handling and temporary support | Stable work supports, adequate lifting/handling equipment and a verified stage-specific support arrangement; equipment ratings and attachment points require a separate plan, not an assumed bracket lifting point |
| Personal protection | Eye and hearing protection, suitable dust protection and extraction; follow tool instructions for clothing and hand protection around rotating equipment |
| Disassembly | Same drivers and two-ended bolt tools, labeled hardware containers, cable protection and the verified independent supports in the disassembly guide |

The selected bolt model bounds head/nut flats at 14.2748 mm, consistent with a
nominal 9/16-inch tool; this is not a guarantee about substituted heavy-hex or
other supplied hardware. Hold-bolt Allen-key size depends on the actual bolt
head and thread system; verify the owned kit rather than buying a guessed size.
A torque wrench is required only with a supplied installation torque criterion;
this plan does not invent one. Do not improvise countersinks in ML24Z steel.
Prepare panel-face seats as described below only after the actual screw/head
match and controlled-depth setup are established. The CAD head cone is not a
verified cutter profile or depth instruction.

The manufacturer’s [#8 flat-head drawing CP-XF_08](https://dxf82wtg340bb.cloudfront.net/resources/8-Flat-Head-Unidrive-and-T-Star-Plus-2D-11-5-21.pdf)
specifies a 90-degree included head angle and 0.320-inch head diameter. These
dimensions identify the cutter/profile; they do not prescribe a shop recess
depth or permit overdriving.

SPAX TER 2010-02 Table 2 identifies T20 for XFT08P-2000. Sections 9.5–9.6 state
that lead holes are not required for the evaluated screws and call for flush
installation without overdriving; that scope does not qualify this connection's
capacity. [SPAX evaluation report](https://www.drjcertification.org/report/download/1936)
Simpson identifies a 3/8-inch hex drive for SDS25112.
[Manufacturer SDS technical sheet](https://strongtie.com.au/sites/default/files/technical_data/Technical%20Data%20Sheet_SDS.pdf)
That drive-size reference is not permission to transfer regional installation
rules to a different connector application. Confirm the applicable ML24Z/SDS
instructions and any wood predrilling requirement; a nominal screw shaft
subtraction in CAD is not a pilot-drill specification.

Optional insert development/repair needs its selected manufacturer's bore,
installation driver and machine-screw tools, plus separate damaged-wood
assessment. Those tools are not required for the current ordinary-screw build
and no insert drill size is assigned here.

## Machining and assembly sequence

1. Label the header, four retained posts, two outer rims, separated center
   principals, top/bottom rails, four service rails and both legs. Match each
   label to its own new drawing and connection schedule. Preserve the 101.9 mm
   clear center corridor and single-stock members.
2. Lay out and drill the 32 nominal 25.4 mm enclosed passages on the specified
   member faces and axes before assembly. Use their complete entrance/exit
   coordinates and remaining-edge dimensions, not the old groove locations.
   Their diameter exceeds the measured maximum component diameter, but that
   difference alone does not prove an intact strand can negotiate every turn.
   Remove sharp edges without enlarging an unreviewed residual section.
3. Assemble header/posts, rims, center principals and rails. Fit commercial
   brackets using their specified structural screws; do not substitute through
   bolts into the bracket holes. The ordinary panel-screw audit does not remove
   manufacturer-required bracket fasteners.
4. Fit all eight leg bolt stacks with heads on the outside and nuts on the
   inside. Put one washer beneath each head and one beneath each nut. Verify
   access and complete thread engagement against the selected bolt/nut details;
   no torque value is assigned by this geometry draft.
5. Prepare the climbing-face screw seats on both main and kicker panels at
   the finalized attachment axes. Use a 90-degree included-angle countersink matched to the received
   SPAX head profile; establish the shallowest seat that leaves the
   head flush using a representative plywood offcut and a controlled depth
   stop. Deburr without enlarging the seat. Do not drive the head deeply into
   the plywood to create its own oversized recess, and reject a setup that
   tears the face veneer or removes an unreviewed amount of plywood. The CAD
   uses a nominal 90-degree head envelope, 8.128 mm across the head and
   2.921 mm across the shank, giving 2.6035 mm axial head height. That
   idealized envelope is **not a shop countersink depth**. Verify the finished seat and applicable head-bearing
   resistance before repeating it across the panels.
   Install the main and kicker panels using the finalized attachment schedule.
   Hold T-nuts and their retention screws require their own product instructions
   and rear-access sequence. Their bores are not panel-screw pilots. Keep both
   ends of the round service passages and string-join locations accessible.
6. **Install the lights after the frame and panels are assembled.** Identify the
   input end, then feed the intact factory strands through successive passages
   before seating each bulb from rear to front. Follow the manufacturer’s
   A1-to-K12 serpentine order. Do not cut, splice or pull on LED bodies to force
   a route. Check local bends and slack against the shortest actual segment;
   304.8 mm is approximate bulb-base pitch, not extra routing allowance.
7. Connect successive strings at indices 50/51 and 100/101. Route LED1 to A1
   and PWR1 to the supplementary feed at the end of string two. Keep the
   controller switch, connectors and power supply accessible. The
   [electrical topology](horizontal-service-wiring.svg) remains schematic for
   external lead lengths and physical placement.
8. Check flush LED seating and the supplied startup sequence. Demonstrate the
   reverse strand-removal route before treating the panels as removable; closed
   passages can require sequentially withdrawing a strand before separating a
   panel. Protect and retain the unused tail without prescribing a cut.

## Drill diameters and product instructions

The 25.4 mm service passages are proposed timber-routing dimensions. Structural
bolt clearances, hold T-nut bores, LED seating bores and wood-screw pilots are
different operations. CAD subtraction using a screw's nominal diameter does
not specify a drill bit. Source-specific SPAX and Simpson pilot/installation
guidance is being verified alongside the connection audit; do not predrill all
screw axes to the CAD shaft diameter. Final instructions must name the product,
wood/material condition and applicable pilot requirement or permitted omission.
Panel-face countersinking is a separate head-seating operation, not permission
to drill the receiver to the CAD screw diameter. A later insert/machine-screw
repair may need a different head seat; reassess the remaining plywood and new
head profile rather than automatically deepening or reusing the SPAX seat.

For panel maintenance or full teardown, use the separate
[disassembly and temporary-support dependency guide](disassembly-guide.md).
Its stop points apply before any structural attachment is removed.

## Remaining release gates

See the [round-candidate analysis](round-service-analysis.md) for matching
evidence and its limits. The new passage residual sections need matching
structural evidence. Current
panel attachment demand/resistance and screw necessity must be reconciled before
recommending a final screw count. The intact harness must traverse the assembled
passages with measured body/connector geometry, bend clearance and slack.
Leg and bracket resistance, delivered material properties, actual floor behavior
and any selected insert connection remain separate qualification tasks. Passing
a geometry audit or reusing unchanged lumber blanks does not close these gates.
