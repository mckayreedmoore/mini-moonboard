# Compact base angle placement and flush-cut review

The two outer rim-to-header ML24Z angles move 29.15 mm toward the front,
from Y = −135 to −105.85 mm. Their 101.6 mm-wide footprints now lie between
Y = −156.65 and −55.05 mm, centered on the 139.7 mm-deep header. Both front
and rear footprint margins are 19.05 mm. All six specified SDS25112 screws
remain installed in each angle. Fresh stock is rebuilt with the relocated
holes; this is not an instruction to redrill previously bored lumber.

All twelve relocated screw cylinders retain the full 35.54476 mm nominal
penetration beyond the 2.55524 mm angle flange, with no unsupported shaft
volume in the raw receiver. Header screws have 31.75 mm minimum centerline
clearance to either depth edge and at least 124.79 mm to the header end.
The upright screws remain perpendicular to the unchanged 4×6 rim side faces.
Their shortest directional along-grain distance to the rim bearing end is
46.85 mm; minimum cross-grain directional edge distance is 38.15 mm.
The factory hole pattern, screw count, and screw product remain unchanged.
These are actual CAD placement results, not a new connector resistance rating.
Manufacturer reference geometry is retained in `ml24z-reference.json`.

The requested flush rear cut on `base_side_left` was evaluated symmetrically
for both rims. It is not adopted: trimming the remaining 7 mm of rear overhang
reduces the section beyond the retained end-cut depth comparison.

| Rim end geometry | Current 7 mm reserve | Fully flush with header |
|---|---:|---:|
| Full stock depth normal to grain | 139.70 mm | 139.70 mm |
| Retained depth at bearing end | 108.168 mm | 102.805 mm |
| Removed normal depth | 31.532 mm | 36.895 mm |
| One-quarter depth limit | 34.925 mm | 34.925 mm |
| Margin including 3 mm cut/placement allowance | **+0.393 mm** | **−4.970 mm** |

The calculation matches the geometry term used by
`scripts.compact_thick_results.base_comparisons`: retained normal depth equals
actual horizontal bearing-face length multiplied by the rim grain's vertical
component, 0.7660444431. Flush trimming fails even without the 3 mm allowance
(by 1.970 mm). Retaining the small projection preserves the current section
criterion without enlarging the compact 2×6 header. It is not an inference
that a flush member would physically fail; it does not satisfy the selected
conservative comparison.

Implementation: `mini_moonboard/compact_base_finish.py`, wrapping the current
lower-kicker-row revision. Frozen historical native definitions stay unchanged.
New candidate native analyses must import this adapter to include the relocated
base-angle forces and holes. A previous native solve does not become a fresh
solve merely because the displayed clips moved.
