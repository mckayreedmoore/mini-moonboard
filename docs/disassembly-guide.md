# Round-service disassembly and maintenance draft

For the newer insert candidate, use the [matching build and removal
draft](round-insert-build-plan.md). Its machine screws and receiver inserts
must not be confused with the wood screws described below. The temporary
support and stage-stability requirements remain unresolved for both candidates.

This guide covers `round-bore-service-development`. It separates panel
maintenance from full frame teardown. The sequence was reviewed against the
connection topology; **physical disassembly and temporary support stability
have not been tested**. No lifting points or temporary brace capacities are
specified by the current design.

## Before any structural fastener is loosened

Close the climbing area, remove people and loose equipment, disconnect the
lighting supply from mains, and identify every part and connection from the
current schedule. Photograph wiring, bracket orientation, outside bolt heads
and inside nuts. Label hardware containers by connection, keeping each bolt,
nut and two washers together.

**Stop before removing a panel screw, bracket screw or leg bolt.** The frame
needs an independently verified temporary support arrangement that carries the
parts being removed and prevents the remaining structure translating, tipping
or racking at every intermediate stage. Panels may contribute rigidity; the
remaining screwed frame has no demonstrated standalone erection stability.
Floor friction, a person holding the frame, and unverified straps attached to
brackets or hold holes are not substitutes. The current package does not supply
that support design. Until it exists, limit work to nonstructural inspection
and de-energized lighting service that leaves the panels and frame attached.

## Panel-only maintenance, after the support arrangement is verified

1. Support the panel independently and positively restrain the remaining frame
   as specified by the temporary support plan. Clear its work area and identify
   all panel attachments; do not assume the screws visible from one angle are
   the entire set. Holds and their bolts add handling weight and rear obstacles.
2. Map each factory LED string crossing the panel and adjacent timber passages.
   Label the A1 input, joins at E2/E3 and I4/I5, and the power boost at I4.
   Photograph the unused tail. Unplug the supply and factory connectors by their
   housings; do not pull wires or cut a strand.
3. Gently unseat affected bulbs from the front-flush position toward the rear.
   Withdraw the necessary intact factory strands through the enclosed passages
   in reverse installation order, feeding components through rather than pulling
   on bulbs. A shared strand can require unseating lights on adjacent panels.
   Stop if a connector or bulb cannot pass freely; the modeled diameter check
   has not demonstrated real bend clearance or a successful withdrawal trial.
4. Confirm that no cable or hold bolt still connects, crosses or traps the panel
   being removed. With its weight already carried by the verified support,
   remove only its scheduled attachment screws. Leave all leg bolts, commercial
   brackets and neighboring panel attachments in place. Prevent the panel moving
   when its final attachment is removed; then transfer it using the planned
   handling method. No fixed universal last-screw location is specified.
5. Inspect screw holes, plywood edges, receiver timber and cable passages. A
   stripped hole, split timber or crushed plywood is not restored by simply
   tightening harder or automatically fitting an insert. Record the damage and
   assess the repair or replacement before reassembly.
6. Reinstall the panel and verified attachments before routing and seating the
   intact strands. Check wiring and all affected connections. Remove temporary
   supports only in the approved reverse sequence. Returning the assembly to
   its original geometry does not resolve the outstanding construction gates.

## Full teardown, after a stage-specific support plan is verified

First complete lighting removal and separately supported panel removal as above.
Do not infer a safe bare-frame state from a completed panel-removal step.
The support plan must carry each timber member before its last retaining
connection is released and restrain the remaining frame throughout.

The following are connection dependencies for planning, **not an approved order
for an unsupported frame**:

- Service rails and top/bottom rails attach to outer rims and center principals;
  retain those supports until each rail is separately carried and detached.
- Each center principal depends on its post/header bearing and retaining
  brackets; preserve that load path until the principal is independently carried.
- The outer rim/leg assemblies and header connections control overall geometry.
  Do not release leg bolts or base angles merely because panels are gone.
- Before any leg bolt is withdrawn, positively support both connected members
  and remove load from the bolt. The nut is inside, head outside; capture both
  washers. Binding is a reason to reassess support, not drive a loaded bolt out.
- Header and posts remain supported until all members depending on them have
  been detached or independently restrained. Do not lift from an unqualified
  bracket, hold attachment or partially fastened rail.

Store labeled timber flat and protected. Keep wiring without sharp folds and
protect factory connectors. Inspect screws, bolts, nuts and washers for damaged
threads, bending and corrosion; follow applicable manufacturer reuse limits.
Replacement quantities and any consumable fasteners must be established from
condition and product instructions, not assumed from the original purchase count.

## Connection review and limits

The current round layout has twelve screws on each of the four main panels
and four on each kicker: 56 panel/kicker screws in total. Each main panel
connects its outer rim, center principal and edge/service rails; each kicker
connects center and outer posts. Leg bolts face outward, with nuts inside.
These connections explain why panel removal changes several load paths at once.
The preceding 87- and 75-screw layouts do not describe this attachment pattern.
Recheck the inventory against the matching exported schedule before planning
maintenance; the count does not qualify the attachments or temporary supports.

Repeat the topology inventory without CAD using the final exported CSV:

```python
import csv
from pathlib import Path

path = Path("exports/round-bore-service-development/connections.csv")
rows = list(csv.DictReader(path.open()))
for panel in ("main_lower_left", "main_lower_right", "main_upper_left",
              "main_upper_right", "kicker_left", "kicker_right"):
    attached = [r for r in rows if panel in r["members"].split(" + ")]
    receivers = sorted({m for r in attached
                        for m in r["members"].split(" + ") if m != panel})
    print(panel, len(attached), receivers)
```

This inventories fastener dependencies only. It does not test temporary support
capacity, load transfer, physical access, component handling or stability.
No graph-connectivity result should be reported as a successful teardown test.
