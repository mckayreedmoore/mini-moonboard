# Additional kicker header row: conditional equilibrium revision

The development candidate adds five SPAX XFT08P-2000 screws to each independent
kicker, retaining the existing four. New axes are at **z = 205.95 mm** and
**|X| = 200, 400, 600, 800 and 1000 mm**, into the existing full-width header.
The calculator reads these axes from the
[candidate module](../mini_moonboard/kicker_header_reinforcement.py).
It does not propose a new receiver or replace the selected screw product.

The [saved calculation](../fea/results/round-structural-kicker-revision-v2.json)
finds restricted three-dimensional equilibrium witnesses for **all 450 cases**:
45 previously saved downward/board-normal load combinations at each of ten
kicker holds. The greatest optimized individual tension is **272.880 N**,
89.726% of the provisional 304.125 N head reference. That is an existence
result for independently assignable reactions, **not an actual screw-force
prediction, equal-sharing rule, head-applicability decision or strength pass**.

## Why five additions

For the largest saved downward load, 300 lb ×2 = 2668.933 N, 100 mm front-face
standoff and 300 N outward force at z = 150 mm, the floor-midplane pitch demand
is approximately 336.26 kN·mm. A backing resultant at z = 25 mm requires
approximately 328.76 kN·mm of screw moment measured about that backing height.
The four existing screws contribute at most approximately 91.24 kN·mm using
the provisional head reference. Each proposed upper screw adds approximately
55.03 kN·mm under the same reference. Four additions are insufficient for these
particular contact assumptions; five exceed this necessary pitch requirement.
This is not proof that five is the minimum under every admissible contact model:
a backing reaction nearer the floor changes the available lever arm.

The full calculation then tests force and moment equilibrium, including
horizontal position of every hold, rather than treating a pitch inequality as
a sufficient condition. The LP minimizes the largest individual tensile force
relative to the smaller supplied head/withdrawal reference. Each screw remains
an independent variable. Equal optimized values in some cases are mathematical
witnesses; the model does not establish physical redistribution or compatibility.

## Explicit reaction model

- All nine screw reactions are axial tension at their actual proposed axes;
  vertical and transverse screw shear are zero in this restricted witness.
- Backing reactions act outward only at post column centers, at z = 25 mm
  into the posts or z = 200 mm into the header.
- Floor reactions act upward only at the two bottom-edge ends of each panel,
  at mid-thickness. No floor friction or arbitrary support couple is available.
- Every applied and reaction point contributes its actual vector cross product
  to all six force/moment equations. Reported residuals are checked explicitly.
- The saved horizontal load subset is board-normal inward/outward force only.
  It does not include sideways force, general horizontal azimuths or hold torque.

The force points represent aggregate resultants, not proven contact areas or
pressure distributions. Panel bending must transfer each hold load to those
points. Point-supported equilibrium does not establish panel, floor, timber or
connection resistance.

The report exports equal-and-opposite simultaneous wrenches delivered to the
header, each post and the floor, about the shared origin at the kicker backplane,
X = 0, Z = 0. For one worst-case witness the five added screws pull the header
outward by approximately **1364.4 N**, with a **281.0 N·m pitch moment** about
that origin. This load does not disappear because the floor carries the vertical
force. Header and downstream connection assessment must include these reactions
simultaneously; the model does not establish their resistance.

## Evidence limits

The [calculator](../fea/round_structural_kicker_revision.py) authenticates its
predecessor evidence and candidate-axis source before solving, then verifies
those hashes again. Version 2 uses the revised drilled kicker panel and its five modeled T-nut
envelopes from the authenticated
[combined mass report](round-reinforcement-review/review.json). Their total is
**3.052452 kg per panel**, giving **29.934325 N** dead load. Their mass-weighted
centroid is used in all six equilibrium equations. The left assembly centroid
is approximately X = −609.797 mm, Y = 9.003 mm from the backplane and
Z = 113.082 mm. The T-nut mass acts behind the floor-midplane reaction, so its
pitch contribution is stabilizing under these specific contact assumptions.

Whole attachment screws span the panel and its receiver; their mass is excluded
from this isolated-panel dead-load model. Unmodeled holds and electrical hardware
are also excluded. Those omissions are explicit and are not claimed to be
conservative. Density and hardware envelopes remain modeled assumptions, not
measured material masses. The [version 1 result](../fea/results/round-structural-kicker-revision-v1.json)
is preserved as historical predecessor-panel-only mass evidence; its original
calculator hash is retained and is not represented as the current producer.

Reproduce the current evidence with:

```sh
python -m fea.round_structural_kicker_revision \
  --mass-report docs/round-reinforcement-review/review.json \
  --output /tmp/kicker-revision.json
```

The provisional head reference retains its
[unresolved countersunk-head applicability](round-structural-head-calculation.md).
The test suite verifies individual head and wood-interaction ratios, unilateral
reactions, all six equilibrium residuals and receiver action/reaction. It does
not resolve applicable resistance adjustments, splitting, group action, panel
bending, installed seating or actual floor pressure.

**Not released for construction or climbing.** This geometry removes the earlier
conditional kicker equilibrium obstruction in a specified reaction model. It
supplies a concrete receiver load case for subsequent checks, not approval of
the complete assembly.
