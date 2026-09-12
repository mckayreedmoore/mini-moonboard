# Reinforced candidate: completed rigid-floor equilibrium check

The complete stated load envelope has compression-only sliding/yaw equilibrium
at an **assumed coefficient of friction of 0.20 or 0.40**. At 0.10, actual
300 N horizontal loads fail the necessary sliding bound. This closes the
analytical equilibrium calculation under stated installation assumptions;
it does not establish measured friction, floor bearing capacity or flexible
frame response. Physical floor testing is outside the owner's requested scope.

[Saved numerical evidence](../fea/results/reinforced-floor-envelope-v1.json)
records current authenticated mass, centroid, support polygon, witness residuals
and a concrete failing load. [Runner](../fea/reinforced_floor_envelope.py)
reproduces the calculation and rejects stale geometry/mass evidence.

| Assumed friction coefficient | Feasible enclosing vertices | Continuous envelope | Actual load counterexamples |
| --- | ---: | --- | ---: |
| 0.10 | 384 / 768 | Not established; sliding fails | 384 |
| 0.20 | 768 / 768 | Equilibrium established | 0 |
| 0.40 | 768 / 768 | Equilibrium established | 0 |

Maximum verified force residual is 2.3e-12 N and moment residual 5.2e-9 N mm.
No reaction needs tension or exceeds its circular Coulomb friction cone.
The witnesses establish existence, not actual individual foot reactions.

## Explicit installation and load assumptions

- Rigid, level floor under the four posts and two leg feet. Every contact has
  the stated friction coefficient. No anchor, rubber pad, additional ballast
  or kicker contact improves this global calculation.
- Modeled mass 181.2058086 kg, including the 142 T-nuts, with sensitivity down
  to 80% at the unchanged modeled centroid. Wood/plywood density is assumed
  600 kg/m³ and steel 7850 kg/m³. Hold, hold-bolt and electrical mass is omitted.
  These are calculation assumptions, not measured mass bounds.
- One resultant at one hold at a time, covering every one of the 142 locations.
  Downward force ranges from 250 to 600 lbf. This includes the intended
  250 lb × 1/2 project comparisons and the 300 lb × 1/2 sensitivity. The
  multipliers are project assumptions, not a certified impact envelope.
- Horizontal force has any azimuth and magnitude from zero through 300 N.
  Outward hold standoff ranges continuously from zero through 100 mm.
  Independent simultaneous hand/foot couples and top/side-edge use are excluded.
- Floor capacity and friction remain installation assumptions. This calculation
  does not require physical floor measurements or tests, and does not convert
  an assumed coefficient into a measured or manufacturer-rated one.

At 0.10, with 80% modeled mass and 250 lbf downward, total floor compression is
2533.673 N. Available total friction is at most 253.367 N against a 300 N
horizontal load: **46.633 N short**. Redistribution among feet cannot fix that
necessary bound. At 0.20, every vertex passes including yaw and overturning
compatibility, beyond the translation-only bound.

## Why finite checks cover every horizontal direction and hold

The horizontal 300 N disk is enclosed by a regular 16-gon with vertex radius
305.877 N. Main hold locations lie in a rectangle; the kicker holds lie on a
line segment. Six positional vertices therefore cover both families. Test the
Cartesian product of those vertices, both downward-force bounds, both mass
bounds, both standoff bounds, and all 16 horizontal vertices: 768 combinations.

The external wrench is separately affine in each variable. In particular,
position cross horizontal force and standoff cross force are retained. A load
inside the prescribed ranges is a convex combination of these product-vertex
wrenches. The fixed-support contact-force feasible set is convex. Combining
verified vertex witnesses therefore supplies an equilibrium witness for every
interior load. An independent reviewer checked this construction; regression
tests check the interpolation cross terms, all hold positions, and the
horizontal polygon's 300 N apothem.

The contact friction polygon is inscribed in the circular cone, so a successful
witness is conservative. Failure of either an enclosing load vertex or the
inscribed-contact LP alone is inconclusive. The reported actual failures use
300 N loads and the exact necessary circular-friction bound.
