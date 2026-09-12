# Structural-screw frame: build draft

The current `round-structural-development` candidate uses structural wood screws
for the panels now and reserves space for a possible later insert conversion.
**It is not released for construction or climbing.** Centered-passage routing
passes the current geometry audit and has matching drawings. The existing screw
coordinates and selected hardware are retained; structural release tasks remain open.

[Materials and hardware](#materials-and-hardware) · [Tools and equipment](#tools-and-equipment) ·
[Assembly](#assembly) · [Removal and maintenance](#removal-maintenance-and-repairs)

Use the matching [cutlist](../exports/round-structural-development/wood-parts.csv),
[connections](../exports/round-structural-development/connections.csv),
[drilling PDF](round-structural-drilling/drilling.pdf),
[drilling datums](round-structural-drilling/drilling.json) and
[STEP](../exports/round-structural-development/round-structural-development.step).
The [screw diagram](round-structural-screw-layout.svg) shows the current axes.

## Materials and hardware

Keep the owned Roseburg AC exterior PS 1, 23/32-category plywood, Lowe's item
12235/model 119055. The modeled thickness is 18.25625 mm. Retain the fixed hold
grid and verify sheet dimensions, strength-axis orientation and usable stock.
The remaining lumber specification is dry, grade-stamped Douglas Fir–Larch
No. 2 or better. Reconcile cutlist lengths, actual dimensions, kerf and defects
before cutting; historical stock allocation is not a new purchase instruction.

| Connection | Selected hardware |
| --- | --- |
| Four main panels and two kickers | 56 SPAX XFT08P-2000 #8 x 2-inch T-STAR Plus flat countersunk screws; twelve per main panel, four per kicker |
| Commercial angles | 24 ML24Z with 144 SDS25112 1/4 x 1.5-inch screws; retain the specified six screws per angle |
| Leg connections | Eight 3/8-inch x 3.75-inch bolt stacks, each with nut and two washers; heads outside, nuts inside |
| Holds | 142 T-nut locations; match owned hold hardware and each hold's bolt length separately |
| Future panel inserts | None installed or purchased by this schedule; reserve space only |

The [SPAX product reference](round-panel-countersink-reference.json) identifies
the head and length. These are evaluated construction screws, not generic deck
or drywall substitutions. Manufacturer capacity data still needs matching loads,
wood and installation conditions. A screw-tip clearance pass establishes fit,
not withdrawal or joint resistance.

## Tools and equipment

- Tape, rule, square, straightedge, angle finder, calipers and labels.
- Guided plywood saw and suitable lumber saw; clamps and supported work surfaces.
- **1.5-inch (38.1 mm) wood bit for LED passages in nominal 2x6 members**;
  **1-inch (25.4 mm) bit for passages in other stock**, as individually scheduled.
  Use a secured drilling jig and backing. Locate each axis from the measured
  timber depth, with entry/exit references and tool reach checked. The proposed
  2x6 route centers on local N = 69.85 mm in nominal 139.7 mm depth; the
  passage runs through the narrow stock thickness, not front-to-back along N.
  Do not enlarge hold or panel LED holes.
- Hold/leg clearance and panel LED bits matched to their separate schedules;
  the modeled values are 7/16 inch and 13 mm respectively.
- **T20** SPAX T-STAR Plus driver bit and controlled-depth 90-degree countersink;
  use a plywood offcut to establish a flush seat without crushing the veneer.
- 3/8-inch hex driver for SDS25112; matching sockets and backup wrench for leg bolts.
- Dust extraction, eye/hearing protection, deburring tools and temporary supports.

No insert-sized pilot, 7 mm insert-machine-screw clearance, 80–82 degree Dottie
head seat or insert installation tool is required for this screw-first build.
The screw CAD cut is not a pilot-bit instruction. Follow each selected product's
installation guidance, including any applicable pilot requirement.

## Assembly

1. Label stock and establish suitable temporary support for each assembly stage.
2. Cut members and drill the scheduled routing passages. Preserve entry/exit
   access and avoid breakout. Wait for the matching centered-passage drawings
   and geometry audit before using their dimensions. A 38.1 mm hole centered
   in exact 139.7 mm (5.5-inch) stock leaves 50.8 mm (2 inches) each side, with
   **zero nominal edge-clearance tolerance margin**. Undersized stock, oversize
   boring or centering error reduces one ligament; this is not automatic
   structural acceptance.
3. Assemble the frame with the scheduled brackets/SDS screws and complete leg
   bolt stacks. Do not substitute longer screws or overdrive bracket heads.
4. Install hold T-nuts while rear access is available. Establish shallow, flush
   SPAX head seats on an offcut, then attach panels using the current axes.
5. Feed the intact factory LED strands through the passages before seating bulbs.
   Retain connectors, supplementary power lead, controller, supply and unused
   tail. Verify fit/slack with the real harness; do not cut/splice to force a route.
6. Complete assembly inspection before removing temporary support or using the wall.

## Future insert conversion

The current audit reserves a **12.1412 mm diameter by 17 mm deep** envelope
into the timber at each panel-screw axis without machining it. This space
corresponds to the previous E-Z LOK **801420-13, 1/4-20** candidate, including
its outer-diameter allowance; it is not a pilot-hole specification. The larger future head and receiver envelope must stay clear of
holds, passages and other hardware. A later conversion needs a selected insert,
applicable resistance, a pilot appropriate to previously screw-drilled timber,
usable thread engagement and a suitable panel head seat. Existing 90-degree
SPAX seats are not automatically compatible with the earlier Dottie head.
Do not enlarge screw holes to an insert's outside diameter now.

## Removal, maintenance and repairs

Support the panel and restrain the frame before removing panel screws; unplug
and withdraw any shared LED strand as required. Leave brackets and leg bolts
installed during panel-only work. Inspect for stripped wood, splitting and
head-seat damage. Repeated wood-screw removal is not the same as a qualified
machine-screw/insert joint. Use the [disassembly guide](disassembly-guide.md)
and treat [worn-hole repair](threaded-insert-repair-guide.md) as a separate decision.

## Receiving and qualification checks

Confirm actual stock and received hardware match the schedule. Check screw tips
against the candidate's [geometry audit](../fea/results/round-structural-audit-v1.json),
including its limits for length tolerances, seating and wood dimensions.
Nominal minimum tip-to-first-exit margins are 107.156 mm for panel/kicker SPAX
screws and 2.555 mm for bracket SDS screws; do not substitute longer screws
or overdrive to consume that clearance.
The completed focused reviews identify the finite release work:

- [Panel fasteners](round-structural-fastener-review.md): establish current
  signed axial/lateral demands, applicable adjusted resistance and combined
  action, including kicker attachments and plywood head bearing.
- [Base and legs](round-structural-base-review.md): resolve the actual ML24Z
  mounting/load-direction applicability or calculate a specific replacement
  detail, then check base/leg transfer under matching simultaneous demands.
- [Timber and passages](round-structural-timber-review.md): adopt dimensional
  acceptance for centered holes and check global net-section/member behavior,
  bearing and concentrated fastener zones against current demands.

The source-matched native runner is available but has not supplied current
accepted demands here. Historical demand numbers do not close these tasks.

Physical floor measurement/testing is outside the owner's requested scope.
Document the selected floor/pad arrangement and use explicit conservative
stability assumptions; no measured friction or proven multi-surface rating is
claimed. Historical floor and load studies do not qualify this revised candidate.
See the [current analysis and simplification scope](round-structural-analysis.md).
