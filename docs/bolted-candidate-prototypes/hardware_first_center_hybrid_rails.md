# Hybrid HL35 center: bounded six-rail resection screen

**Result: local rail geometry is feasible; the installed hybrid pose remains
rejected.** This is a CAD occupancy comparison for the kerf-right raw panel
solids and the 66 fixed Hillman panel/kicker axes. It is not a cutting,
drilling, connection, or capacity approval. The paired JSON can be regenerated
with `uv run python -m scripts.hardware_first_center_hybrid_rails --output
docs/bolted-candidate-prototypes/hardware_first_center_hybrid_rails.json`.

The original six rails (bottom, lower service, upper service on each side)
begin at X = ±89.05 mm and overlap the widened principals. This trial keeps
their outer ends and original sections, and makes one planar inner-end cut on
each rail at X = ±120 mm. Each remains one connected, unspliced timber solid;
there is no lap joint or custom steel. The cut clears the outer upper vertical
plate envelope by a nominal 1 mm and leaves a 5.55-mm gap to the principal.
Neither clearance is a shop tolerance or an attachment design.

| Each side | Original principal overlap | Original plate overlap | After cut |
| --- | ---: | ---: | --- |
| Bottom rail | 133,291.013 mm³ | 8,218.758 mm³ | Neither |
| Lower service rail | 135,193.278 mm³ | 0 | Neither |
| Upper service rail | 135,193.278 mm³ | 0 | Neither |

All six changed rails clear the raw main/kicker panel solids, the widened
principals, and the ideal plate rectangles. All 66 original occupied screw
axes were checked against their assigned receiving wood. No modeled receiving
volume is lost, and no receiver is missing. Each of the twelve axes assigned
to the changed rails still intersects 438.127 mm³ of its intended rail, the
same as before the cut. This is preservation of the original CAD receiving
envelope, not proof of screw embedment, edge distance, or resistance. The
original twelve frame-bolt axes also have no intersection with the changed
rails.

The minimum sampled one-piece blank envelopes (X length × cross section) are
**1010.3 × 38.1 × 139.7 mm** for each left rail and
**1007.125 × 38.1 × 139.7 mm** for each right rail. The Y/Z orientation was
sampled every 0.1°. These are geometric lower bounds, with no allowance for
trim, kerf, defects, delivered size, or machining. A nominal dressed 2×6
section is a dimensional comparator only; no delivered blank is verified.

This cut leaves the center attachment and load path unresolved. A compatible
prefabricated rail-to-center bracket would need its own geometry and hardware
check. The parent hybrid also still has upper principal toe bores exiting
wood, among its unresolved installed-hardware checks. **Do not advance this
pose to fabrication on this rail result.** The occupied cylinders and ideal
plate envelopes are analysis geometry, never drilling coordinates; no
connection capacity is claimed.
