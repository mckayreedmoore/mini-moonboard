# Historical outward-post side-rim withdrawal with retained hardware

The [detached probe](../../scripts/owner_barrel_rim_withdrawal_hardware_probe.py)
extends the [rim-first dependency and bare-wood screen](owner-barrel-outer-header-sequence-probe.md)
for the historical 48-pair outward-post composition. It requires the recessed outer-header
forward row at Y = −85 mm and verifies the unchanged 66 panel/kicker screw and
12 frame-bolt source axes. It changes no viewer geometry or fixed axes.

For each side, the screen classifies the five rim-attached barrel stations
(ten trial barrel bodies and ten bolt stacks), eight rim-receiver panel screws,
and two original rim frame bolts as **temporary removal before withdrawal**.
This is a service-sequence assumption, not a change to a bore, screw location,
or other geometry. Both outer-header/post barrel rows and their bolt stacks
remain installed on each side. Every other viewer barrel and represented bolt
stack solid remains in the collision inventory.

The rim is translated along the rearward board normal at 0, 5, …, 160 mm.
At each isolated pose, positive intersections above 1 mm³ are reported by
name and volume against all other outward-post uncut wood, retained barrel
bodies, retained bolt-stack solids, and representable protected envelopes.
The protected inventory includes T-nuts, hold-hole and provisional 50.8 mm
rear-projection envelopes, lights, wires, and the fixed screw/bolt axis solids
that were *not* temporarily removed. The source rim is 139.7 mm deep along
that normal, so the final sample passes its nominal depth.

Both sides have **zero reported positive-volume intersections above 1 mm³**
at all 33 sample poses in all four categories. Per side, the retained screen
contains 27 other uncut wood members, 38 barrel bodies, 114 represented
bolt-stack solids, 58 fixed panel screw envelopes, 10 fixed frame-bolt
envelopes, and 547 other protected envelopes. This measured zero is limited
to those represented solids and discrete poses.

All 48 outward-post rows now include provisional shaft, washer, and head
solids. These envelopes are not delivered hardware or verified seats; actual
projections remain unverified. Neither drill/access paths nor the
space needed to extract removed fasteners are treated as retained physical
hardware.

The result is a **sampled nominal interference screen only**. A zero at these
positions cannot prove a continuous swept path, manufacturing tolerance,
hardware fit, tool access, independent support, safe demounting, reverse
assembly, or repeatability. The viewer still has unqualified and `REVISE`
stations. No drilling, fabrication, or structural approval is issued; all
source release flags remain false. The sampled path is not removal instructions.

Reproduce with
`uv run pytest -q tests/test_owner_barrel_rim_withdrawal_hardware_probe.py`
and `uv run python -m scripts.owner_barrel_rim_withdrawal_hardware_probe`.
