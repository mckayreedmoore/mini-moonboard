# BG001 signed end-distance and resultant-direction screen

The accepted `a12-rear` lateral vectors select the previously unresolved
opposed tension branch: both actions on `base_post_outer_left` point toward
its `g+` (+Z) end, while both actions on `knee_outer_left_spine` point toward
its `g−` (−Z) end. The shorter selected ends are the post end at axis 2
(25.40 mm, 4D) and the spine end at axis 1 (31.75 mm, 5D). This resolves the
sign branch for the two BG001 references in this case.

The pinned NDS-2024 method record identifies §12.5.1.2(a), Table 12.5.1A and
Commentary C12.5.1.2. The commentary method record says to interpolate the
tension end-distance requirements for an angle-to-grain load between the
parallel-tension and perpendicular-to-grain values. Using the actual
resultant-to-grain angles gives these conditional member-specific factors:

| Axis | Member | Signed lateral action (Y, Z), N | θ to grain | Loaded end | Distance | `CΔ` |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| `knee_outer_left_post_1` | post | (+151.2499, +260.9994) | 30.0924° | `g+` | 67.45 mm (10.622D) | 1.0000 |
| `knee_outer_left_post_1` | spine | (−151.2499, −260.9994) | 30.0924° | `g−` | 31.75 mm (5.000D) | 0.8338 |
| `knee_outer_left_post_2` | post | (−213.2224, +258.4611) | 39.5216° | `g+` | 25.40 mm (4.000D) | 0.7039 |
| `knee_outer_left_post_2` | spine | (+213.2224, −258.4611) | 39.5216° | `g−` | 73.80 mm (11.622D) | 1.0000 |

The minimum for the group is `CΔ = 0.703901`, controlled by post axis 2. The
NDS group rule applies the smallest applicable geometry factor to every
fastener in the group. The queried cross-grain loaded edges are post axis 1
`e+` = 16D, spine axis 1 `e−` = 7D, post axis 2 `e−` = 6D, and spine axis 2
`e+` = 15D. Their opposite edges are respectively 6D, 15D, 16D, and 7D. All
queried loaded and unloaded edges exceed the cited Table 12.5.1C minima of 4D
and 1.5D. The distances are from the pinned finished STEP query at three
through-thickness stations, not observed stock dimensions.

The direction-specific single-bolt packet reports Mode IV references of
712.070 N and 682.661 N for axes 1 and 2. Applying only the group minimum
angle-interpolated `CΔ` gives conditional references of 501.227 N and 480.526
N, with demand/reference comparisons of 0.60184 and 0.69728. The old pure
parallel-tension branch `CΔ = 4/7` is also retained separately: it scales those
same references to 406.897 N and 390.092 N. That is a more reducing branch on
these inputs, but it is not the exact mixed-direction factor.

The earlier `Cg = 1.0` results do not transfer to these resultants. They used a
unit +Z direction aligned with the row. The reviewed helper returns pending
for a load not aligned with its row: each per-bolt resultant has alignment
sine 0.50140 or 0.63637, and the sum of the two reported main-member actions is
`[approximately 0, −61.9725, 519.4605] N`, with alignment sine 0.11846. This
packet leaves `Cg` unapplied and does not establish a mixed-direction group
factor.

The method references the repository-pinned official [AWC 2024 NDS Chapter 12
PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
SHA-256 `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
The source-bound interpolation note is in
[`ordinary-finished-end-edge-query-attempt01`](../../evaluation-resume-2026-09-24/ordinary-finished-end-edge-query-attempt01/README.md),
and the BG001 square-end / edge geometry is in
[`current-knee-finished-profile-attempt01`](../current-knee-finished-profile-attempt01/README.md).

These are conditional geometry-scaled individual-bolt reference comparisons,
not adjusted resistance, a group capacity, a design DCR, or acceptance. The
load angles, DF-L No. 2 and SG 0.50 wood scenario, proposed grain axes,
full-body quarter-inch shank, 38.1 mm bearing lengths, zero gap and 45,000 psi
bolt bending yield are inherited conditional inputs. This screen does not
evaluate splitting, row shear, tear-out, net section, member shear, bolt or
washer axial resistance, axial tie, contact, or complete load transfer. It
does not qualify physical parts or the twelve retained frame-bolt
arrangements.

From the repository root, reproduce and verify with:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-bg001-signed-end-distance-attempt01/produce.py --verify
```
