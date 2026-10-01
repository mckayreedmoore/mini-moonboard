# Upper-block local-stress method and section boundary

The parent authenticated the current
[AWC 2024 NDS appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf),
SHA-256 `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31`.
Appendix E is on PDF pages 9–16, printed pages 174–181. Its parallel-grain
local-stress method is optional; the obligation to check applicable member
stresses remains separate. This resolves the former source gap for the
equations, without establishing their applicability to a complete upper joint.

## Existing helper audit

The parent compared the equations directly and visually against
`mini_moonboard/bolted_timber_checks.py`. For declared dry DF-L No. 2 base
properties, its three arithmetic expressions match the source:

| Helper | Source method | Applicability still needed |
| --- | --- | --- |
| Net parallel tension | E.2-1: `Ft' × A_net` | Governing finished cut, adjusted property, parallel-tension section action and stress distribution |
| Parallel row tear-out | E.3-2: `n × Fv' × t × min(end, pitch)` | Actual row and critical shear paths, parallel-grain loading, adjusted property and all neighboring cuts |
| Parallel group tear-out | E.4-1: half of each bounding row value plus `Ft' × A_group-net` | Actual bounding rows, every critical group for unequal row spacing, and group action assignment |

The helpers fix `Ft=575 psi` and `Fv=180 psi`; they do not apply every
adjustment. They therefore produce base references rather than adjusted
upper-joint capacities. The row expression's apparent lack of a factor of
two is correct: the source's triangular shear-stress assumption halves each
of the two shear-line contributions. Do not add another factor of two.

The full upper bolt resultants are oblique to grain. Splitting, perpendicular
grain tension, moments and coupled receiver forces do not become covered
checks by feeding only a parallel force component to these helpers. A
component calculation needs its own justified action and failure-path model;
the remaining components and interactions still require evaluation.

## Exact sampled block cuts

The [geometry calculation](geometry.md) samples each of the eight saved
block solids at its three distinct along-grain bolt stations and at the two
interstation midplanes. These are forty exact planar BREP intersections,
including the modeled bores. The result is a geometric input, not a stress
field or proof that the sample finds every critical cut.

The repeated section families have the following area/property products. For
this illustration only, specify full-section nominal 4×4 DF-L No. 2, dry
service, normal temperature, `CD=1`, and the documented `CF=1.5` tension
factor. Then `Ft'=862.5 psi`. These are conditional uniform parallel-tension
references for the sampled area; they are not adopted resistance or a demand
comparison.

| Sampled cut | Combined wood area (mm²) | Separate face regions | `862.5 psi × area` (kN) |
| --- | ---: | ---: | ---: |
| Interstation plane | 7,903.21 | 1 | 46.998 |
| Single-bore station | 7,236.46 | 2 | 43.033 |
| Two-bore station | 6,569.71 | 3 | 39.068 |

The areas are rounded for this table; use the geometry output for full
precision. Conditional grade and grain are specifications for the study,
not observations or transferred grades from unidentified stock. The
shortened G7 block retains the sampled section families; that does not
restore its shorter end distances.

Separate regions on a cut do not mean the whole three-dimensional block is
disconnected. They do mean that force and moment balance over the total area
alone cannot establish the stress or load share in each region. A uniform
stress field over the summed area would be a new assumption, especially
where two receivers act on different sides of a bore. The current block
balance records authenticate whole-body equilibrium but do not provide the
traction on these cut faces.

## Actionable closure

Bind section and tear-out demands to the same source increment, receiver,
bolt, contact-force locations and gravity loads. Identify the material
regions and cut paths receiving those actions; retain section moments and
shear as applicable. Establish the applicable adjusted properties and check
the nonparallel failure modes independently. Reuse these exact geometry
inputs and the authenticated source method instead of regenerating the
frame or importing a historical pass. The missing three load cases remain
the coordinator's separate envelope dependency.

This note changes no geometry, adopts no capacity, and releases no physical
work. The source PDF is cached locally and excluded from Git; the public
packet preserves its URL, edition, page locations and hash.
