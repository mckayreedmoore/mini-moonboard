# WJ-04 ordinary joint feasibility screen

**Historical early feasibility screen; superseded as the current configuration
reference.** The failed 139.7 × 57.15 × 139.7 mm service-clashing pose and
its full-section-overlap comparison remain diagnostic history only. The
current ordinary-joint geometry trial is the
[WJ-04 workhorse probe](wj04-workhorse-probe.md) and its
[machine-readable configuration](wj04-probe.json); both remain diagnostic,
with provisional hardware and no acceptance, strength result, cut, or drill
instruction. This note does not define active ordinary hardware.

Status: **Historical diagnostic only; no joint selected or accepted** (2026-09-23).

The first workhorse station is `clip_horizontal_lower_right_1`. Its source
principal ends at X = 89.05 mm and its service rail starts there. Both have
38.1 × 139.7 mm sections; the available rear face of each is 38.1 mm wide.
The fixed panel screw at X = 70 mm is 19.05 mm from the butt. The nearby
upper service rail has a 105.95 mm tangent gap. These are source layout
constraints, not a new cut or fastening instruction.

The historical grain-N solid cleat trial in
`scripts/simple_rail_joint_comparison.py` uses a 139.7 × 57.15 × 139.7 mm
body and four provisional 1/4-inch bolts. Its local bore and timber checks
are useful leads, but its protected-service screen reports positive-volume
hits: `light_G7` 1520.122437 mm³, `wire_078_G6_G7` 1088.220130 mm³, and
`wire_079_G7_G8` 239.270692 mm³. That pose cannot be copied as the WJ-04
joint. A historical full-section overlap also lost two fixed screw receivers
and hit the lower panel, so it is not a viable shortcut.

The later workhorse probe supersedes this early pose search as the current
ordinary-joint geometry trial. Its checks for bolt groups, seats, removal,
services, screw receivers, local-N envelope, stock/cut method, and mechanics
remain open as recorded in the linked probe files. The historical diagnostics
establish no capacity, current-configuration identity, or WJ-04 clearance
pass.
