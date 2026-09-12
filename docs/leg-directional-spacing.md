# Directional bolt spacing review

This note applies the 2024 NDS Chapter 12 placement provisions to the proposed
larger-bolt investigation. It is not a connection capacity approval. Both wood
members are 38.1 mm thick and 139.7 mm deep. The grain directions differ by
55 degrees. The fasteners pass perpendicular to the wood faces.

## Placement provisions

NDS 12.5.1 and Tables 12.5.1A–D distinguish the loaded edge from the unloaded
edge. A blanket requirement of four diameters to every edge overstates the
requirement for a unidirectional load. Conversely, a moment group can load both
edges through different bolts or different cases.

Let `D` be nominal bolt diameter and `l` be the smaller of the fastener's length
in the main wood member and total length in the wood side members. Here
`l = 38.1 mm`; `l/D` is 3 for a 1/2-inch bolt and 2.4 for a 5/8-inch bolt.

- For loading parallel to grain, minimum edge distance is `1.5D` for these
  thickness ratios.
- For loading perpendicular to grain, the loaded edge requires `4D`; the
  unloaded edge requires `1.5D`.
- Between rows, parallel-to-grain loading requires `1.5D`. For the present
  thickness ratios, perpendicular-to-grain loading requires `(5l + 10D)/8`.
- In a row, parallel-to-grain full-value spacing is `4D`; the reduced-value
  minimum is `3D`. For perpendicular-to-grain loading the minimum is `3D`,
  while the full-value spacing depends on the attached member's requirements.
- Full-value end distances are `4D` for perpendicular loading or parallel
  loading bearing away from an end, and `7D` for softwood loading bearing
  toward an end. Reduced-value minimums are half those distances.

| Requirement | 1/2-inch bolt | 5/8-inch bolt |
| --- | ---: | ---: |
| Diameter | 12.700 mm | 15.875 mm |
| Loaded perpendicular edge, `4D` | 50.800 mm | 63.500 mm |
| Unloaded/parallel edge, `1.5D` | 19.050 mm | 23.813 mm |
| Between-row perpendicular spacing | 39.688 mm | 43.656 mm |
| Along-row minimum, `3D` | 38.100 mm | 47.625 mm |
| Along-row full value, `4D` | 50.800 mm | 63.500 mm |
| Toward-end softwood full value, `7D` | 88.900 mm | 111.125 mm |

NDS 12.5.1.2 permits `C_delta = actual/full-value minimum` for qualifying
reduced end distances and along-row spacing. The smallest applicable factor
for any fastener applies to the group. It does **not** authorize reductions
below Table C edge distances or Table D between-row distances. Along-row
spacing therefore has a minimum factor of 0.75 for the parallel case; end
spacing can reach 0.5. NDS 12.5.1.2(b)'s separate shear-area provision concerns
loading at an angle to the fastener, not simply the 55-degree angle between
the two wood grain directions.

## Force directions in the existing pattern

Using the existing four centers, axial compression along the leg, and the two
assessment cases `(4153.58 N, -85.07 N m)` and `(4035.68 N, +108.30 N m)`, the
elastic bolt-group allocation gives the following directional result. Define
positive transverse direction in each member as `(0, -grain_z, grain_y)`.
Forces on the leg oppose forces on the rim.

All rim transverse bolt forces are positive: 168–1486 N. Thus the rim has one
consistently loaded edge in these two cases. The leg's transverse bolt forces
have both signs at each of its two rows over the two-case envelope; their
magnitudes reach 722 N. Those components arise from joint moment.

The NDS tables label the direction of loading but do not supply a special
algorithm for a combined axial-force/moment group. Applying loaded-edge rules
to each bolt's force direction is a conservative extension used for this
screen, not an explicit quoted moment-group rule.

For two rows with a single loaded edge, the minimum depth is
`4D + row_spacing + 1.5D`: 109.538 mm for 1/2 inch and 130.969 mm for 5/8 inch.
Both are below 139.7 mm before other geometric requirements.

If both outer edges must accommodate perpendicular loading, the corresponding
two-row depth becomes `8D + row_spacing`: 141.288 mm for 1/2 inch and
170.656 mm for 5/8 inch. Both exceed the available 139.7 mm. Consequently,
shifting the existing two-row topology alone cannot satisfy this conservative
mixed-load placement screen for either larger diameter. Different bolt
positions must have their force signs recomputed; these are not universal
impossibility results for every possible pattern or attachment.

NDS 12.5.1C also refers concentrated loads suspended below the neutral axis to
reinforcement provisions. Passing tabulated edge spacing does not by itself
establish resistance to perpendicular-to-grain splitting.

## Source

[AWC, 2024 NDS Chapter 12, pages 97–99, section 12.5.1 and Tables 12.5.1A–D](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf).
The local downloaded primary document was read through
`/tmp/reinforced-ch12-plain.txt`; formulas should be used with the complete
2024 NDS provisions and same-edition material values.
