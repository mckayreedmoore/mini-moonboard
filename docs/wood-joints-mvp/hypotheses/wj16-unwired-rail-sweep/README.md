# Continuous rail enclosure before wiring

Status: nominal motion diagnostic, 2026-09-24. Parent ran the
[producer](producer.py.snapshot) against retained
[WJ16 geometry](../wj16-integrated-static/README.md) in 3.60 seconds.
The [report](sweep.json) finds no positive-volume intersection for the full
0–200 mm +N translation of the upper-right rail subassembly. Five zero-gap
timber contacts remain, so its clearance and release flags are false.

The moving subassembly comprises the rail, its inner and outer cleats, and
four installed rail bolt stacks: 23 shapes. Four upright bolt stacks and two
named upper-right panel screw axes are absent in this operation. All 66
canonical panel screw records remain unchanged. The complete lighting harness
is assumed not yet installed: exactly 132 lights and 131 wire shapes are
omitted. This follows the initial frame-before-wiring order; it supplies no
method for removing an installed harness.

All six panels remain conservative obstacles, together with the other
finished timber, hardware, fixed axes, frame bolts, holds, and retained legacy
connections. The stationary scene contains 839 shapes. For each moving solid,
the producer bounds the rigidly transformed solid in X/T/N, extends that prism
200 mm in +N, and verifies start/end containment. Convexity of the prism then
covers every intermediate translation. Of 19,297 possible pairs, bounding-box
pruning leaves 91 exact Boolean checks. None has positive overlap volume.

The five zero-gap enclosure contacts are the rail with the right principal,
side, and upper-right panel, and each cleat with its upright receiver. Their
presence prevents a positive-clearance or tolerance claim. This result does
not prove support, handling, tools, installation order, or individual-member
transport. It also does not supersede the
[wired WJ12 motion result](../wj12-right-rail-motion/README.md), which intersects
five modeled wires at intermediate positions. Recheck any accepted operation
against the eventual complete layout.

[Execution bindings](execution.json) and [SHA-256 values](sha256.json)
authenticate the inputs, report, producer, and focused tests. The live entry
point is `build_wj16_unwired_rail_sweep_report(g16)` in
`scripts/wood_joint_wj16_unwired_rail_sweep.py`.
