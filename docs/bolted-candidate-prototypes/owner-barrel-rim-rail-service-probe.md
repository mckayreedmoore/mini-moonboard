# Rim-on service screen: six rail-to-side-rim stations

This is a bounded current-viewer diagnostic, not a tool plan, drilling release,
or confirmation that the side rims can be removed safely. It uses
`scripts.export_owner_barrel_scene.build_viewer_assembly()` and the exact
nominal access, bolt, barrel, and bore envelopes in that assembly. It does not
alter the viewer or any wood.

## Scope and sequence assumption

The only stations screened are `bottom_outer`, `lower_outer`, and
`upper_outer`, mirrored left and right (six stations, two bolt/barrel rows
each). The six panel shapes remain in place. On the active side, the eight
fixed-axis panel screws received by that side rim are allowed to be
temporarily removed; the other 58 panel screws, all 12 original frame bolts,
and neighboring candidate hardware remain in the collision inventory. The
fixed axis locations are not changed. A matching bolt/thread overlap is
treated as intentional: the bolt would be unscrewed. Both station bolts are
assumed removed before either barrel is extracted. No removal of the other
rim-touching stations is assumed.

For each row the probe checks the existing 20 mm diameter × 40 mm nominal
bolt-driver and barrel-entry envelopes, then a straight axial withdrawal
envelope. The bolt withdrawal travels nominal bolt length plus 10 mm. The
barrel withdrawal travels its modeled recess plus body length plus 10 mm.
Only the receiving timbers are virtually relieved by their matching proposed
bores during the withdrawal check. This is an analytical subtraction, not a
cut, bit size, or proof that a bore can be made.

## Current result

| Station family | Sides | Rows | Nominal access/withdrawal result |
| --- | --- | ---: | --- |
| Bottom outer | Left, right | 4 | No modeled blocker in any of four operations per row |
| Lower outer | Left, right | 4 | No modeled blocker in any of four operations per row |
| Upper outer | Left, right | 4 | No modeled blocker in any of four operations per row |

Thus the 12 bolt rows and 12 barrel rows are **clear in this finite nominal
screen only**. No other modeled frame wood, neighboring trial shaft/barrel
solid, retained protected screw/bolt, hold/T-nut or 50.8 mm trial projection,
light, or wire envelope intersected the four service paths above the 1 mm³
reporting threshold. The screen identifies no current geometry blocker for
undoing these six stations while the rim is still installed.

## What remains open

- The producer's rail stacks model shafts only. Delivered heads, washers,
  cross-dowel slots, grip, and actual extraction method are not represented.
  The barrels are recessed about 11.049 mm; a clear 20 mm cylinder does not
  prove a person can turn or pull one out.
- The cylindrical access paths and axial envelopes do not prove a continuous
  real driver/tool/hand sweep or clearances at tolerances. The projection
  envelope is a trial, not a measured hold-bolt length.
- The side rim still has two original frame bolts and two other candidate
  barrel stations (`top_outer` and `base_outer_side`) per side. This probe
  does not verify their removal, a continuous rim withdrawal, supported
  panels during disassembly, or repeated reassembly.
- Neither this screen nor an empty collision list establishes thread fit,
  wood/fastener resistance, whole-frame load path, or safe climbing use.

Run the focused check with:

```sh
.venv/bin/pytest -q tests/test_owner_barrel_rim_rail_service_probe.py
```
