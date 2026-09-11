# Worn panel-screw holes: insert repair assessment

**Current recommendation: assess the damaged receiver before choosing a repair.
Do not convert a loose panel screw into an insert and resume climbing on the
basis of nominal fit.** The insert/machine-screw pair below is a concrete
dimensional-development candidate. The current round model has 56 ordinary panel/kicker screws. No insert is installed,
and no worn-wood repair capacity or physical repair test has been established.

This guide concerns the ordinary face/kicker wood screws only. Retain commercial
bracket SDS screws, structural through-bolts, nuts and washers, and climbing-hold
T-nuts. A panel screw transfers structural load; it is not merely a cover fixing.

## Candidate and why it remains conditional

E-Z LOK **801420-13** is a zinc, flush-style 1/4-20 insert for softwood. Its
matching pilot recommendation is **23/64 in (9.128125 mm)**, not a bolt clearance
bore. The drawing gives 13.0048 mm nominal length and 11.5062 mm outside diameter,
with a general ±0.635 mm tolerance. Its softwood/repeated-assembly purpose makes
it a reasonable candidate to investigate; that description does not rate a
Douglas-fir climbing-panel repair.
[Product](https://www.ezlok.com/ezhex-insert-801420-13),
[manufacturer drawing](https://www.ezlok.com/assets/documents/dimensional_drawings/Dimensional%20Dwg%20-%20HexDriveFlush.pdf).

The paired **L.H. Dottie FMDD14114** is a 1/4-20 × 1¼ in flat-head machine screw,
with a published 11.2268–12.1158 mm head diameter. Retain it for dimensional
evaluation rather than silently selecting a longer screw to compensate for
unknown engagement. Full thread intervals and recess must first be resolved.
[Dottie product and technical sheet](https://lhdottie.com/14-20-flat-head-squarephillips/fmdd14114),
[recorded dimensions and unknowns](panel-insert-reference.json).

The insert manufacturer describes this flush style as recessed below the wood
surface but does not specify the recess here. It also does not supply Hex Drive
test results because installation variables matter. Consequently this guide
assigns no withdrawal, lateral or cyclic allowable load, tightening torque, or
approved minimum engagement. Metal strength and other insert-family pullout
tests cannot fill that gap.
[Installation guidance](https://www.ezlok.com/e-z-hex-drive-insert-installation),
[testing policy](https://www.ezlok.com/testing).

## What has been tested

Eleven automated arithmetic/rejection tests cover drill-point depth, gross
screw reach, and damaged-hole rejection for splitting, uncertain measurement,
oversize holes and eccentricity. These are software tests, not experiments in
damaged wood. Reproduce with:

```sh
uv run pytest -q tests/test_round_insert_repair_assessment.py
```

The earlier [horizontal-frame insert fit](horizontal-insert-fit.md) passed 87
nominal reserves. It is historical evidence for the grooved model and must not
be treated as a result for the new round passages. The
[current round-frame report](../fea/results/round-insert-repair-v1/report.json)
and [location schedule](../fea/results/round-insert-repair-v1/schedule.csv)
pass all 56 tested nominal reserves and prospective head-clearance checks.
No damaged wood or physical repair was tested. The evaluator checks all
current panel/kicker locations against the actual round-bore receiver solids,
existing fastener envelopes and neighboring future screw-head obstructions:

```sh
uv run python -m fea.round_insert_repair_assessment \
  --output fea/generated/round-insert-repair-next
```

The new report must pass at the particular repair location with matching source
hashes before its geometry can support a mockup. It still models nominal wood,
not measured wear. Its head check excludes the screw's own plywood and receiver;
it does not approve countersink seating, panel bearing or driver access.

## Measurements that determine the next step

First follow the [disassembly guide](disassembly-guide.md). Unload the board and
establish independently verified support for the frame and affected panel
before removing any supporting fastener. Protect and withdraw the wiring as
required by that guide. Do not use a loosened panel as a temporary support.

Record the connection identity, receiver, wood condition, actual panel thickness,
hole position, and the damaged envelope over the whole proposed insert depth.
Measure crushed fibers and ovality, not just the visible entrance diameter.
Check behind that depth too: the old 2 in screw reaches about 32.54 mm beyond
the nominal plywood, while the proposed reserve is only 17 mm deep.

For a verified circular envelope, a **necessary cleanup condition** is:

`damage radius + axis offset + measurement uncertainty < 9.128125 / 2 mm`

For example, a 6 mm damage envelope offset 1 mm with 0.1 mm uncertainty leaves
0.464 mm radial cleanup margin; changing the offset to 1.5 mm fails. This
arithmetic only asks whether the proposed pilot encloses the damaged zone.
It neither proves sound wood outside it nor establishes repair resistance.
A screw's original 4.1402 mm diameter is not a measurement of its worn hole.

Reject this insert route when there is splitting, decay, crushed wood beyond a
verified envelope, an oversized/oval/off-center hole failing that condition,
unmeasurable hidden damage, or interference with wiring, another fastener or
the receiver boundary. Do not enlarge the pilot to make an oversized hole fit
the selected insert. Damage in the plywood or its existing countersink is a
separate panel repair problem; an insert behind it does not restore head bearing.

## Depth, edges and the panel head

Our **12.1412 mm diameter × 17 mm full-solid reserve is not a drilling schedule**.
For an idealized 118° twist-drill point, a 9.128125 mm pilot adds about 2.742 mm
beyond its full-diameter depth. Maximum insert length 13.6398 mm plus that tip
already uses about 16.382 mm. Only about **0.618 mm remains for recess and any
additional bottom clearance**. The actual drill, required recess and insertion
clearance must be specified together; blindly setting a depth stop to 17 mm
does not solve this.

At the nominal 18.25625 mm plywood thickness, gross screw reach is 13.49375 mm,
or 11.96975 mm at the recorded minimum screw length, before subtracting insert
recess. Complete male/female thread overlap must exclude the drive recess and
both runouts. Neither value is effective engagement or permission to tighten.

A centered maximum-diameter insert on a 38.1 mm face leaves 12.9794 mm of wood
on each side geometrically. Actual locations, edge/end loading and round wiring
bores need their own checks; this is not an approved splitting distance.
The larger flat head needs its own verified plywood seat. The provisional
7 mm panel clearance hole and 82° countersink concept are not an approved
machining change; damaged veneer, countersink depth, head pull-through, clamp
force and repeat assembly remain unresolved.

## Recommended outcome

If damage or geometry fails, favor **replacement of the affected receiver with
sound stock to a reviewed connection detail**. A relocated fastener is another
option only after checking sound wood, old-hole separation, edge/end distances,
wiring, panel support and the redistributed connection load. Neither option
means simply adding a screw beside the failed one; the current frame itself
still has unresolved strength checks.

If nominal geometry and measured damage bounds pass, the insert option advances
only to a separately planned manufacturer/reviewer assessment or non-load-bearing
mockup. Any physical application evaluation must address the actual species,
damage condition, edge distances, engagement, combined loading and repeated
removal before a design resistance can be assigned. No hanging-person proof
test or numeric DIY acceptance load is supplied here. Release for climbing
requires the repair detail and the complete frame to be qualified.
