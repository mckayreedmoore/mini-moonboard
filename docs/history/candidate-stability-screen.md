# Screw-spacing candidate: rigid-body moment screen

This calculation compares **drilled screw-spacing-development timber** against
the **original undrilled 2x8-foot100 timber inventory**, both at 600 kg/m³.
These are different inventories and drilling states, not a drilling-only
comparison. Steel angles, generic fasteners, holds, glue, and LEDs are omitted;
overlapping generic hardware adds no mass. No structural acceptance or climber
rating follows from this screen.

| CAD quantity | Original undrilled timber | New drilled timber |
| --- | ---: | ---: |
| Part count | 45 | 47 |
| Volume mm³ | 306605478.648317 | 323500314.924229 |
| Mass kg | 183.963287 | 194.100189 |
| CG X mm | 4.267980 | 6.461180 |
| CG Y mm | 745.153756 | 743.732283 |
| CG Z mm | 1137.150551 | 1144.146945 |

The actual level-floor support hull is unchanged. Counterclockwise XY vertices
in mm are:

```text
(-1295.4, 1307.665366310)
(-1257.3, -159.067084200)
( 1257.3, -159.067084200)
( 1295.4, 1307.665366310)
( 1295.4, 1500.331409594)
(-1295.4, 1500.331409594)
```

All four independent leg plies have their own floor face, each approximately
3670.288125 mm². Together they retain the former two leg solids' contact area.
Other floor-contact timber consists of both kicker panels, the bottom kicker
batten, and both kicker cheeks. This convex hull is not a pressure/contact
distribution solution.

## Existing 96-case envelope

The existing cases and 1.5 moment screening target are unchanged: one climber
at 150/200/250/300 lb; 1×/2× gravity force; 80%/100% timber mass with fixed CG;
0/50/100 mm hold standoff; and 0/300 N horizontal force at the worst azimuth for
each edge. These sensitivities are illustrative, not validated governing loads.
250 lb is the intended maximum under consideration; 300 lb is sensitivity,
not an increased rating.

| Weight lb | Original minimum factor | New minimum factor |
| --- | ---: | ---: |
| 150 | 1.804519 | 1.907537 |
| 200 | 1.773398 | 1.874639 |
| 250 | 1.743331 | 1.842856 |
| 300 | 1.714267 | 1.812133 |

Both inventories return **96/96 MEETS MOMENT SCREEN ONLY**, with no status
changes. Each weight's governing case is A12, 2× force, 80% mass, 100 mm
standoff, and 300 N horizontal force. The worst minimum net restoring moment
increases from 454122.594342 to 516344.376160 N·mm.

## Retained legacy row-12 cases

The six original sagittal force vectors remain separate at full timber mass,
with load point Y=1447.555750085, Z=1971.581330311 mm. ND means no destabilizing
live moment in this two-toe calculation. Reactions are kicker/leg in N.

| Load | Original factor | New factor | New reactions | Status in both |
| --- | ---: | ---: | ---: | --- |
| Downward 1.2 kN | ND | ND | 906.049 / 2197.424 | Meets 2D margin only |
| Downward 2.4 kN | ND | ND | 944.214 / 3359.259 | Meets 2D margin only |
| Downward + outward 0.3 kN | 2.579580 | 2.726845 | 549.610 / 2553.863 | Meets 2D margin only |
| Downward + inward 0.3 kN | ND | ND | 1262.488 / 1840.984 | Meets 2D margin only |
| Outward/downward normal | 0.768984 | 0.812884 | −199.776 / 2874.594 | **UPLIFT** |
| Inward/upward normal | 0.534555 | 0.563124 | 1935.545 / −803.417 | **UPLIFT** |

The exploratory normal vectors are respectively (Fy,Fz)=(919.253332,
−771.345132) N and (−919.253332,771.345132) N. Negative reactions mean uplift,
not tensile restraint from the floor. Their adverse outcomes are retained.

## Reproduction and limits

From the repository root, run:

```sh
.venv/bin/python -B -m fea.candidate_stability_screen
```

The calculator reuses `tied_base.state`, `physical_footprint.evaluate`, and
`tied_base_envelope.case_summary`; rebuilds CAD inventories in memory; checks
the frozen counts, mass, hull equality, four floor plies, envelope outcomes,
and adverse legacy cases; and prints JSON. It creates no CAD exports or solver
jobs. Geometry changes that invalidate its assertions require review and
updated results rather than silently retaining this report.

This is conditional rigid-body assembly equilibrium with unresolved
connections. It establishes no joint capacity, joint slip, floor compliance,
pressure distribution, yaw equilibrium, FEM result, or sliding/friction
acceptance. There is no anchoring, ballast, pad, adhesive, or interface-friction
credit. The increased timber mass and shifted CG improve these calculated
moments; they do not resolve either adverse normal case or establish safety.
