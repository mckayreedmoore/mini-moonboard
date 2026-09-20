# PB-02/PB-04 connected center and lower-right rail geometry probe

Status: **one combined kerf-right frame, two alternative grain-N cleat solids**.
This is a nominal CAD diagnostic, not a connected joint design, bolt layout,
strength result, shop dimension, or drilling release. Reproduce with
`python -m scripts.simple_connected_base_probe`; the focused test is
`tests/test_simple_connected_base_probe.py`. Neither source trial script nor
the fixed connection-axis CSV is modified.

## Combined assembly

The [probe](../../scripts/simple_connected_base_probe.py) starts from all 26
uncut kerf-right frame and panel solids. It moves only
`base_post_center_right` 37.8 mm outward in X and adds the existing
139.7 × 88.9 × 238.9 mm solid 4×6 center backer at X −50.95…88.75,
Y −124.9…−36, Z 0…238.9 mm, matching the
[center trial](../../scripts/simple_center_support_offset.py). It then places
either the 139.7 × 57.15 × 200 mm grain-N lower-right cleat or its
139.7 × 57.15 × 300 mm group-length alternative in that **same** modified
frame, matching the wood-solid poses in the
[rail trial](../../scripts/simple_rail_joint_comparison.py). The two cleats
are alternatives, never simultaneous parts. The rail, principal, panels,
header, other frame solids, and all 66 fixed axes retain their inputs.

## Results of the combined solid screen

The baseline raw frame already has positive-volume `lumber_leg_left` /
`base_floor_left` and right-side counterpart overlaps of **765,784.421 mm³
each**. Those exact pre-existing overlaps remain in the combined results;
their acceptability is outside this probe. No **new** positive-volume
wood/wood, wood/panel, or panel/panel overlap appears from the shifted post,
backer, or either cleat. The cleat and center backer have zero intersection;
their bounding boxes are separated vertically by **933.111 mm**. The
cleat/shifted-post intersection is also zero.

A 0.1-mm perturbation of nominally touching faces measures backer contact
areas of **21,238.21 mm²** against each center post and **12,419.33 mm²**
against the header. Each cleat alternative measures **7,983.855 mm²**
against the principal and **19,516.09 mm²** against the rail. These are
geometric face-contact diagnostics, not bearing pressure, installed fit,
contact stiffness, or a demonstrated load path. The backer and cleat are
separated; their actions can connect only through the rest of the frame.

The fixed-axis CSV contains **48 main-panel** and **18 kicker/header** screw
axes. All 48 main receiver intersections are numerically unchanged from
the raw frame, and their modeled full 63.5-mm receiver paths remain inside
wood under both the historical-diameter and nominal-head-width proxies.
Both interior kerf-right kicker edges, at X = −1.5875 mm,
sample over the backer at Z = 120 mm and over the header at Z = 257.95 mm.
All 18 kicker/header purchased screw paths use the full **63.5-mm overall
length**; the portion behind the panel back is **45.24375 mm** and lies
completely in its assigned wood receiver. The two right-center kicker
screws now enter the backer. This result holds both for the historical
4.1402-mm modeled occupied diameter and for a deliberately over-width
full-length cylinder at the retailer's nominal **9.017-mm head diameter**.
Neither proxy is a controlled delivered shaft/head shape, installation
tolerance, verified tip datum, or proof of full-edge backing between the
sampled stations. The cleat solids have no intersection with any of those
66 full-length nominal-head-width proxy cylinders in the combined frame.

## Limits before a connected design

This probe adds **wood solids only**. It does not combine bores, bolt heads,
washers, sockets, installation sequence, actual delivered screw envelopes,
or cut tolerances. It does not select 3/8-in or 1/4-in bolts or verify end,
edge, group, splitting, cleat bending/shear, backer/header transfer, or
simultaneous six-case actions. The prior rail access and placement conflicts
remain open. No old angle/SDS resistance or case pass transfers to this
assembly, and the fixed 66 panel/kicker axes are not permission to drill.
