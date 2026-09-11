# Round-passage frame with removable-panel inserts: build draft

[Materials and hardware](#materials-and-hardware) ·
[Tools and equipment](#tools-and-equipment) ·
[Proposed assembly sequence](#proposed-assembly-sequence) ·
[Receiving and qualification checks](#receiving-and-qualification-checks)

**Development candidate `round-insert-development`: not released for machining,
construction or climbing.** This fresh-stock model contains 56 E-Z LOK inserts
and matching machine screws: twelve connections per main panel and four per
kicker. It preserves the round lighting passages, horizontal rails, split center
service corridor, commercial bracket screws and complete leg bolt stacks.
It is not a demonstrated repair of previously drilled or worn timber.

Use this candidate's [wood schedule](../exports/round-insert-development/wood-parts.csv),
[connection schedule](../exports/round-insert-development/connections.csv),
[STEP assembly](../exports/round-insert-development/round-insert-development.step)
and [drilling-reference PDF](round-insert-drilling/drilling.pdf) together.
Drawings are dimensioned development references, not full-size templates or
permission to drill the depicted insert body clearances into real receivers.

## Materials and hardware

Keep the **already purchased Roseburg AC exterior PS 1, 23/32-category plywood**,
Lowe’s item 12235 / model 119055. Inventory the actual sheets and verify thickness,
usable dimensions, stamp, condition and strength-axis orientation. Structural I
remains an optional reference alternative; it is not an instruction to replace
the owned plywood. The modeled main panels are four 1219.2 mm squares and the
two kickers are 1219.2 × 225 mm, all 18.25625 mm thick. Verify usable stock and
saw kerf before accepting the provisional four-sheet/offcut allocation. Keep the
fixed hold grid; do not shrink it to fit undersized sheets. The
[material/LED verification](round-material-led-verification.md) identifies the
owned AC fir product, and the [APA plywood bounds](round-ac-plywood-bounds.md)
keep species-group, layup and directional capacity assumptions explicit.

The proposed remaining lumber is dry, grade-stamped Douglas Fir–Larch No. 2 or
better. The retained stock-allocation draft uses two 2×6×12 ft, four 2×6×10 ft,
two 2×6×8 ft and one 2×10×12 ft board. Reconcile actual blank lengths, kerf,
end trim and defects against this candidate's schedule before cutting. These
quantities are purchasing geometry, not member-strength approval.

| Hardware | Current model quantity | Identification and limits |
| --- | ---: | --- |
| Removable-panel inserts | 56 | E-Z LOK **801420-13**, die-cast zinc, flush hex-drive, 1/4-20, nominal 13.0048 mm length and 11.5062 mm outside diameter; installation and connection resistance remain unqualified |
| Panel/kicker machine screws | 56 | L.H. Dottie **FMDD14114**, zinc-plated carbon steel, 1/4-20 × 1¼ in flat head; full usable thread engagement and plywood head bearing remain unresolved |
| Commercial angles | 24 | Simpson **ML24Z**; retain the specified connector arrangement |
| Angle screws | 144 | Simpson **SDS25112**, 1/4 × 1½ in; retain the manufacturer-specified bracket screws, not panel machine screws or insert substitutions |
| Leg bolt stacks | Eight | Each stack has one 3/8-16 × 3¾ in bolt, one nut and two washers, with head outside and nut inside; verify supplied properties and schedule |
| Hold hardware | 142 positions | 132 main and ten kicker T-nut locations; reconcile the owned Escape kit, retention screws and each hold's bolt length separately |
| Lighting | Owned V5 kit | Keep the controller, original supply and intact factory leads/strands; no cut-and-splice substitution |

SPAX ordinary panel screws belong to the preceding round-bore candidate and are
**not the selected panel attachments here**. Bracket SDS screws and leg bolts
remain. The [dated materials ledger](material-costs.md) prices a partial remaining-
material scenario; do not treat its historical panel-screw comparison as the
price or complete purchasing total for these inserts and machine screws.

## Tools and equipment

Inventory owned equipment before purchasing. Tool capacity, reach and access
must suit the actual workpieces and the final reviewed machining details.

| Operation | Tools and fit checks |
| --- | --- |
| Measuring and labeling | Tape, steel rule, square, straightedge, angle finder, pencil and part labels; calipers for plywood, insert/screw dimensions and harness components |
| Cutting lumber and plywood | Appropriate crosscut/bevel saw and guided circular or track saw, sharp blades with measured kerf, clamps, sacrificial backing and supported work surfaces |
| Round timber passages | 25.4 mm (1 in) wood bit, suitable drill, secured guide and controlled depth/reach; verify access to the scheduled entry face and protect the exit from breakout |
| Hold/leg bores | 11.1125 mm (7/16 in) bit is the modeled clearance diameter; confirm the selected hold T-nut fit and actual structural-bolt detail before production drilling |
| LED panel holes | 13 mm wood bit with backing; verify the supplied bulb's seating fit first |
| Insert pilot development | Manufacturer lists **23/64 in (9.128125 mm)** for 801420-13; drill, guide and depth control must be chosen with the actual point shape, recess and required bottom clearance. This identifies the product recommendation, not an approved drilling schedule for this frame |
| Insert installation | E-Z LOK lists a **6 mm hex** and installation tool **9000**; verify the selected tool's access and product instructions. No installation torque is assigned |
| Panel machine screws | Product sheet identifies **#3 Phillips/square** drive; use the matching received-head driver with controlled tightening and verify reach at all axes |
| Machine-screw head seats | Controlled-depth countersink matched to the received **80–82°** head, test offcut and depth stop. The old SPAX 90° countersink is not the selected profile for this head |
| Panel clearance development | Drill/guide selected only after final shank clearance and head-bearing review; the CAD's **7 mm** clearance is a reservation, not an approved bit instruction |
| ML24Z/SDS screws | **3/8 in hex driver** for SDS25112; extensions only where access and approved axes permit |
| Leg bolts | Nominal **9/16 in socket and backup wrench** for the modeled standard hex bolt/nut; confirm actual flats and socket depth with protruding threads |
| Deburring and cleaning | Deburring tool, sanding block/paper and dust extraction; avoid unreviewed enlarged holes or chamfers |
| Lighting | Labels, flashlight and gentle hand feeding; factory connectors are retained, so wire cutters, strippers and crimpers are not part of this route |
| Handling and support | Stable work supports, clamps and independently verified stage-specific restraint/lifting equipment; no assumed lifting point on a bracket or hold hole |
| Protection | Eye/hearing protection and suitable dust protection; follow each tool's instructions for rotating equipment |

The [recorded insert/screw references](panel-insert-reference.json) link the
[E-Z LOK product](https://www.ezlok.com/ezhex-insert-801420-13),
[installation guidance](https://www.ezlok.com/e-z-hex-drive-insert-installation)
and [Dottie product/technical sheet](https://lhdottie.com/14-20-flat-head-squarephillips/fmdd14114).
Bracket drive identification is in the [SDS technical sheet](https://strongtie.com.au/sites/default/files/technical_data/Technical%20Data%20Sheet_SDS.pdf);
applicable connector installation rules still require the correct regional
product instructions. Do not infer a pilot from a modeled screw shaft.
Hold-bolt Allen-key size depends on the owned kit; it has not been guessed here.
A torque wrench is useful only with a specified installation criterion; this
plan assigns no insert, machine-screw, SDS or leg-bolt torque.

## Why the insert machining dimensions are not shop instructions

The model uses a provisional **0.25 mm below-surface insert recess**, a **7 mm
panel clearance** and **17 mm receiver reserve**. Its receiver subtraction also
clears a maximum-size insert body. That subtraction is an occupied-envelope
check; drilling the receiver to the insert's outside diameter would discard the
wood needed for its external threads. Follow the selected product's reviewed
pilot detail instead, once the complete connection is established.

The manufacturer calls for below-surface installation but the selected recess
has not been established. With an idealized 118° drill point, the recommended
pilot adds about 2.742 mm of tip depth. Maximum insert length, the provisional
0.25 mm recess and that point leave only about **0.368 mm** inside the 17 mm
reserve for any extra bottom clearance. The actual bit and installation
requirements can invalidate that arrangement.

At nominal panel thickness and the modeled recess, nominal gross screw reach
from the insert front is **13.24375 mm**; the minimum-length screw gives
**11.71975 mm**. These are not effective engagement: subtract unthreaded head
transition/runout, insert drive recess and internal thread runout, and check
bottoming and actual panel thickness. No longer replacement screw is selected
by this draft. The Dottie head is larger and has a different angle from SPAX;
its seat, remaining veneer and bearing resistance require their own review.

## Proposed assembly sequence

This describes dependencies for a future reviewed build. Stop before production
machining until the receiving, geometry and resistance checks below are closed.

1. Inventory and label actual stock, panels and every connection. Confirm the
   fixed panel grid, separate members, 101.9 mm center corridor and final
   schedule. Establish independently verified support for each erection stage.
2. Lay out the round passages from the matching drawing's member faces and
   axes. Make only the reviewed cuts and bores. Keep their entry/exit faces
   accessible and remove sharp edges without enlarging residual sections.
3. Develop insert pilot and panel head-seat settings on representative sound
   offcuts using the received products. Resolve recess, bottom clearance,
   usable thread overlap and seat depth before repeating any setting. An
   offcut fit demonstration does not establish structural resistance.
4. Assemble posts, header, rims, principals and rails with their specified
   brackets and SDS screws. Install complete leg bolts with outside heads,
   inside nuts and one washer under each. Maintain the temporary supports.
5. Install inserts in sound receivers to the reviewed detail, keeping each
   axis aligned with its panel clearance. Install the main/kicker panels with
   the 56 machine screws. Verify seating without bottoming or crushing the
   plywood. Hold T-nuts and retention screws need their separate rear-access
   installation sequence and product instructions.
6. **Install the lights after frame and panels are assembled.** Feed intact
   factory strands through successive enclosed passages before seating bulbs
   from the rear. Preserve the A1–K12 route and accessible joins at 50/51 and
   100/101, with the supplementary feed at the end of string two. Do not force
   connectors through, pull on LED bodies, cut strands or invent extra length.
   The CAD represents 132 active bulbs and 131 links only. The unused factory
   tail, A1 input lead, supplementary power branch, extensions, controller and
   supply still need physical routing; the displayed connector cylinders do
   not establish complete kit fit. Retain all factory components.
7. Demonstrate the reverse strand-removal route and inspect actual slack,
   bends and connector access. Verify electrical startup using the supplied
   product instructions. Complete reviewed assembly inspection before any
   temporary-support removal or change of use.

## Removal, maintenance and repairs

Machine screws make repeated panel attachment the intended mechanism; they do
not make a loaded panel safe to remove. Follow the support and wiring dependency
principles in the [disassembly guide](disassembly-guide.md), while using this
candidate's machine-screw schedule in place of the older ordinary-screw list.
Unplug power, independently support the panel and restrain the frame before
loosening a structural attachment. Closed passages may require withdrawing a
shared strand before panel separation. Leave structural brackets and leg bolts
in place during panel-only work.

During normal panel removal, the inserts remain in the receivers. Inspect for
rotation, pullout, damaged threads, splitting and plywood seat damage before
reassembly. Do not assume repeated tightening restores a loose insert or
repeated removal is qualified. The [worn-hole repair guide](threaded-insert-repair-guide.md)
addresses a different situation: damage in previously screw-fastened receivers.
This fresh-stock insert model does not establish that repair's suitability.

## Receiving and qualification checks

Record the received insert/screw dimensions, complete male/female usable thread
intervals, actual plywood thickness and head seat, timber species/grade and
moisture/condition. Establish permitted recess and installation controls with
applicable product guidance. Assess withdrawal, lateral loading, splitting,
head bearing and repeated assembly for this actual connection; neither metal
strength nor a nominal reserve establishes wood connection capacity.

The [floor and harness verification notes](round-floor-harness-verification.md)
identify concrete measurements still needed: actual foot/floor contact and
friction basis, mass/CG, shortest harness interval, rigid connector/strain-relief
length, rear bulb projection, cable diameter and bend limit. The owner-reported
12.7 mm maximum diameter and approximate 304.8 mm pitch remain useful inputs,
not proof of intact feeding or dynamic floor stability.

Fresh insert-candidate geometry, mass/floor and connection/panel evidence is
summarized in the [current analysis](round-insert-analysis.md). The
[surface study](round-floor-surface-assumptions.md) compares assumed horse-stall
mats, hardwood and carpet, including degraded friction and rear-foot contact
loss. These are simulated scenarios, not measured surface ratings. Only reports naming `round-insert-development` with matching
sources apply; predecessor ordinary-screw results remain historical. Physical
feeding/removal, delivered-material behavior, temporary support and complete
frame/connection/floor qualification remain separate release gates. A passed
software test or CAD check does not release this plan for building or climbing.
