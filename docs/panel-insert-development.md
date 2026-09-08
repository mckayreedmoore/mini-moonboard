# Removable-panel connection candidate

This revision preserves the timber frame, its through-bolts/nuts, and all 96
manufacturer-specified ML24Z screws. It replaces the 48 face-panel and eight
kicker-panel wood screws with machine screws and flush receiver inserts.
**Geometry candidate only; not build-ready or structurally qualified.**

## Inspection package

- [Interactive model](https://mckayreedmoore.github.io/mini-moonboard/?model=panel-insert-development)
- [Assembly STEP](../exports/panel-insert-development/panel-insert-development.step)
- [Metric/imperial parts](../exports/panel-insert-development/panel-insert-development_parts.csv)
- [Connection positions and hardware](../exports/panel-insert-development/panel-insert-development_connections.csv)
- [Separate panel/pilot drilling reservations](../exports/panel-insert-development/panel-insert-development_panel_drilling.csv)
- [Supplier dimensions and limits](panel-insert-selection.md)

The published candidate has 275 selectable entries: 43 inherited wood/angle
bodies, 56 inserts and 176 connection assemblies. Inserts and angles are gray;
machine screws and bracket screws blue; through-bolts red. Threads and drives
are simplified envelopes, not detailed manufactured surfaces.

## Hardware delta

| Change | Quantity | Selected geometry candidate |
| --- | ---: | --- |
| Remove panel wood screws | 56 | Previous SPAX #8 × 2 in |
| Add receiver inserts | 56 | E-Z LOK 801420-13, flush zinc, ¼-20 |
| Add panel machine screws | 56 | L.H. Dottie FMDD14114, ¼-20 × 1¼ in, flat head |
| Keep commercial-angle screws | 96 | Simpson SDS25112, separately purchased |
| Keep through-bolt connections | 24 | Existing leg, ply-stitch, base and backing selections |

No reserve/spares quantity or purchase order is implied. The underlying timber
cuts and 56 attachment axes are unchanged. The existing lower-backing bolt
edge-distance issue is not resolved by this panel revision. The researched
[small-angle alternative](backing-angle-selection.md) is not installed because
its available rating/installation conditions do not qualify this application.

## Drilling and model interpretation

Inserts sit flush with the **receiver**, behind the removable panel. The panel
receives a provisional 7 mm (0.276 in) machine-screw clearance hole. The insert
manufacturer lists a 23/64 in (9.128 mm) pilot, separately from its 11.506 mm
nominal external thread diameter. Do not drill the receiver to the external
diameter shown in the CAD model: that cut represents occupied insert space.

The model reserves 17 mm (0.669 in) depth for pilot/tip clearance. It is not a
confirmed straight-flute drilling depth or a supplied installation instruction.
Allowances for the actual drill point, product length tolerance, wood condition
and required thread engagement still need resolution.

The modeled screw head uses a conservative 80-degree/max-diameter envelope.
The supplier gives an 80–82-degree head range; the provisional countersink
selection is 82 degrees. Actual seating/profile and a flush climbing surface
must be confirmed together before machining. CAD-envelope depth is not a
machining instruction. The screw's quoted length includes the flat head.

At nominal panel thickness, screw reach behind the panel is 11.970–13.494 mm
over the published screw length tolerance. **This is not effective engagement:**
insert hex recess, full internal thread length and screw runout are unknown.
No installation torque, withdrawal or lateral resistance is assigned.

## Assembly and disassembly intent

1. Complete the structural frame and retain access behind the removable panels.
   Resolve the qualification items below before using these as workshop plans.
2. Transfer the matched panel/receiver axes using the drilling schedule; keep
   panel-clearance drilling separate from insert installation pilots.
3. Install each insert flush with its receiver using the selected manufacturer's
   tool/method. Do not infer a tightening torque from the machine-screw catalog.
4. Offer up panels without forcing alignment. Install machine screws from the
   climbing side; verify seating, no bottoming and no service obstruction.
5. For removal, support each panel and remove its 12 screws (four per kicker
   half). Inserts stay in the frame. Structural brackets and transport bolts
   remain independent of routine panel removal.

Panel removal exposes the recessed backing-bolt heads. Bracket screws are not
intended for repeated removal simply because the panels are now removable.

## Qualification ledger

Geometry checks cover receiver containment, service reservations, nominal head
and shaft collisions, hardware pairs, body validity and published source/units.
They do not qualify wood-thread anchorage, panel pull-through, cyclic loosening,
splitting, clamping force, real tolerances or structural load sharing.

Before construction/climbing approval, resolve:

- actual usable engagement, screw/insert seating and allowable installation torque;
- panel attachment resistance in the actual Douglas-fir stock and face plywood;
- lower-backing bolt edge distance and complete base/leg connection resistance;
- conditional asymmetric FE demands versus actual unanchored floor reactions;
- actual material condition, flat-floor support, friction and a reviewed physical
  validation procedure. The crash pad remains a separate excluded element.

The predecessor's ideal-bonded FEA does not validate the changed fasteners or
larger receiver holes. No structural approval transfers to this candidate.
