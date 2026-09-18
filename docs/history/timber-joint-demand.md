# Conditional leg-to-board force recovery

These results recover aggregate forces and moments from the authenticated
40 mm [timber bulk model](timber-structural-results.md). They are **not isolated
rim-bolt demands, actual unanchored reactions or joint resistance checks**.
The panel-insert revision has different receiver holes and is not validated by
this predecessor mesh.

## Important load-path finding

The inset legs touch both the rims and the upper-panel edges. The bulk model's
ideal bonding joins both interfaces, although the physical panel edge is not a
specified glued structural leg connection. Each side has 405 shared nodes:
333 on the rim, 101 on the panel, with 29 common boundary nodes.

Consequently the leg free body transfers load through **rim plus panel edge**.
Assigning its entire resultant to the four rim bolts would misidentify what the
model actually solved. The recovery initially rejected the extra shared nodes;
inspection identified the actual panel-edge contact. The revised check admits
only those two explicit member interfaces and records their node inventories.

The next joint-specific FE model must remove the unintended panel-edge bond or
explicitly qualify a physical contact/connection there, before using isolated
upper-joint demands for design. Do not simply relabel the current result as bolt
force or divide it by four.

## Example result: 2.4 kN downward

Both leg plies form one free body. Axes are world X across the board, S uphill
along the board, and N behind the climbing face. Moments are about the mean of
the four actual bolt axes, projected onto the rim/leg interface. Values below
act **from the leg onto the board**; reverse all signs for board-on-leg actions.

| Component | Left leg | Right leg |
| --- | ---: | ---: |
| X force, N | 17.28 | −16.56 |
| S force, N | 839.66 | 762.52 |
| N force, N | 1,109.91 | 1,008.12 |
| X moment, N·m | −22.15 | −20.20 |
| S moment, N·m | 3.97 | −2.76 |
| N moment, N·m | −6.64 | 5.53 |

The source case shares 2.4 kN among five upper holds. It is not an asymmetric
single-hold result. Unequal left/right results reflect the actual modeled
geometry/load mapping rather than an enforced equal split.

All six original cases and both legs are available in the
[machine-readable report](../fea/results/timber-joint-demand.json). Report
moments are in N·mm, unlike the N·m table above.

## Verification and limitations

The recovery authenticates the original input/output archives, source closure
and whole-frame equilibrium audit. It selects whole ten-node leg elements using
actual CAD bounds/profile, checks all shared interfaces and floor-node ownership,
excludes applied-load nodes, and compares mesh/CAD volume and centroid. Under
these zero-gravity leg load cases, summed floor reactions equal the leg-on-board
wrench. No division among individual bolts, plies or member interfaces is made.

Floors remain fixed in XYZ, timber isotropic, interfaces ideally bonded, and
self-weight absent. Support tension, slip, panel-edge separation and real joint
compliance are not resolved. The free-body arithmetic is valid for that linear
model; this does not make its physical boundary assumptions adequate.

```bash
uv run pytest -q tests/test_timber_joint_demand.py tests/test_timber_joint_evidence.py
# Separate working copy, with the published output absent:
uv run python -m fea.timber_joint_demand
```

The runner refuses to overwrite evidence. Tests replay the published force
results independently; no new finite-element solve is required for recovery.
