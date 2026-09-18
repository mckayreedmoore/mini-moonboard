# Compact raw-rim boundary map

`fea.compact_rim_boundary` authenticates the compact 2×6/e0 native archive and
selects each complete raw rim against its CAD solid. It checks whole C3D10
element membership, volume and centroid, then records conforming shared faces,
shared edge/vertex nodes, and the actual quadratic connector interpolation.
It does not modify any archived solver or CAD source.

```sh
uv run python -m fea.compact_rim_boundary
uv run pytest -q tests/test_compact_rim_boundary.py
```

The selected raw rims contain 2,484 left and 2,485 right elements. Each has
217 shared faces and 595 shared nodes with omitted wood. Mesh and raw CAD
volumes agree to better than one part in a billion. The two lower rim-to-gusset
couplings are retained in the map; the four upper leg couplings are separately
marked for replacement by the physical joint. Other gusset couplings do not
belong to these rims.

This is **undrilled parent-mesh ownership**, not equality with the drilled
hardware-trial STEP bodies. Future remeshing must interpolate boundary fields
from this raw parent domain onto the physical local geometry. Shared-face
records identify both parent element/face sides; edge/vertex-only shared nodes
remain explicit rather than silently discarded.

No displacement, load or restraint is assigned. Required remote field nodes
include shared wood nodes and the omitted gusset support nodes for the retained
springs. Their quadratic weights map the remote spring endpoint; do not pin
all six rim support nodes as a substitute for that spring. The source records
also preserve the rim-side interpolation nodes independently.

An accepted complete-WOODN contact endpoint can supply a different parent
field, including gravity and moving feet, only with its own source and endpoint
authentication. Otherwise a fixed-floor parent needs expanded rim displacement
output. Never add the four replaced connector forces to a displacement-driven
local model. This map supplies neither calibrated stiffness nor joint strength.

## Compact leg reach

The zero-extension 2×6 CAD candidate places both legs' furthest world-Y edge
at 1476.339362 mm. The upper climbing panels reach 1549.569606 mm, leaving
73.230244 mm of clearance in the side-view horizontal direction. These bounds
include the entire raw leg solids and their level floor cuts, not just their
foot centerlines. The existing geometry suite reproduces this check with
`test_compact_legs_stay_within_board_top_horizontal_reach`.

This is an undeformed side-view footprint check. It does not assert lateral
containment: each leg lies outside the panel's X edge by its 38.1 mm thickness.
It does not establish stability or a permissible loaded displacement.
