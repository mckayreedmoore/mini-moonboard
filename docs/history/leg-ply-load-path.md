# Individual leg-ply load path

The current mesh can represent the two leg plies independently without a new
whole-frame mesh. This geometry audit is preparation for a no-composite-credit
connection trial, not a solved load-sharing result or approval.

## Verified ownership

Each whole-leg element was classified against the CAD-derived ply boundary.
No element crosses it. Every selected node lies inside its intended CAD ply;
individual mesh volumes and centroids agree with CAD within the predeclared
0.1% volume and 1 mm centroid gates. Both plies have their own floor nodes.

| Side | Inner-ply elements | Outer-ply elements | Shared interface nodes | Matched interface faces |
| --- | ---: | ---: | ---: | ---: |
| Left | 1,982 | 1,972 | 1,197 | 544 |
| Right | 1,980 | 1,973 | 1,189 | 540 |

Every interply face has exactly one inner and one outer owner, and the faces
cover every shared node. The six actual stitch-bolt axes map onto this surface
using the existing quadratic interpolation. Nearest face nodes are approximately
4.77, 7.92 and 9.60 mm from the three axes on each side; the coupling points
retain the actual axes rather than snapping to those nodes.

The [source-bound map](../fea/results/leg-ply-map.json) records each ply's
elements, nodes, floor nodes, CAD/mesh moments, shared faces and stitch-point
weights. No coordinates, connectivity, CAD, hardware or drilling schedule have
changed. No released-ply FE solve has yet been performed.

## Requirements for the next connection trial

A [three-member lateral connector coupon](three-member-connector-coupon.md)
now establishes a continuous-bolt linear formulation with independent region
motions and limiting-case tests. It is not calibrated or integrated into the
frame; the requirements below remain open.

1. Duplicate shared ply nodes while preserving element coordinates and correct
   separate floor support membership. Keep the previous rim/panel and gusset
   releases; do not accidentally restore their bonded paths.
2. Represent the six stitch-bolt transfers at their actual axes, with equal and
   opposite actions on the plies. A no-glue-credit model must not retain bonded
   interply nodes or silently substitute full-surface shear ties.
3. Resolve each rim bolt's three bearing members explicitly. Two independent
   rim-to-ply springs do not automatically represent the bending and bearing of
   one physical bolt. Establish the connector formulation and its limiting-case
   checks before using its forces for resistance decisions.
4. Treat interply bearing/contact separately from glue, friction or clamp credit.
   Separate bodies alone do not establish realistic contact. Preserve signed
   per-ply floor, rim-bolt and stitch forces and moments and check equilibrium
   for each ply, not merely the combined leg.
5. Compare same-case actions to applicable resistance, retaining material,
   thread, group, washer, splitting and unanchored-floor limitations. The
   [bonded-laminate reference](leg-bolt-resistance.md) is not the resistance of
   this no-credit arrangement.

```sh
uv run pytest -q tests/test_leg_ply_map.py tests/test_leg_bolt_reference.py
```

Verification: 27 focused map, thread-bearing, yield and connection-reference
tests passed. Ruff and whitespace checks passed. Independent correctness,
testing and architecture/package reviews found no substantial issues. These
reviews do not establish structural adequacy.
