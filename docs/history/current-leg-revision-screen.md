# Current leg connection revision screen

> Follow-up: the [assembled MVP study](current-leg-mvp-study.md) found ratios
> 1.535 and 1.606 for the larger full-sole and relieved-sole candidates. The
> fixed-resultant passing screen below does not select a replacement.

A nine-bolt connection in single 2×10 legs and single 2×10 outer rims is an **exploratory candidate that passes this bounded screen**. Its fixed-resultant lateral ratio is **0.847** across the saved current-frame cases, including the 250 lb doubled-downward-load comparison. This is not a selected detail or a construction release. Widening the rims also changes their base bearing footprint; the header relationship must be resolved before treating the option as a complete frame revision.

The accepted panels, T-nuts and no-slip floor assumption remain the project basis. This investigation concerns the leg connection. No custom steel fabrication or doubled vertical stock is proposed.

## What was calculated

The script reads both legs' actual mechanical connection forces and coordinates from all nine cases in `current-frame-response.json`. It sums each group's force and moment, translates the moment to each proposed centroid, and redistributes the in-plane force and turning moment through identical elastic bolts. The saved current bolt pattern is **70 mm along the leg by 50 mm along the rim**.

The search covers 6-, 8- and 9-bolt parallelogram grids, 3/8-, 1/2- and 5/8-inch diameters, pitches in 5 mm increments, and centroid shifts in 10 mm increments. All stock remains 38.1 mm thick. The rim's climbing-side face stays fixed: added depth grows rearward. The leg retains its original centerline. Bounds are derived from the current stock-profile vertices: the rim edges lie at ±69.85 mm relative to the saved group, and the existing leg top is 177.105 mm beyond that group. The search permits a square top extension up to 250 mm beyond the saved group.

| Single leg / outer rim | Screened arrangement | 150 lb comparison ratio | All saved cases ratio |
|---|---|---:|---:|
| 2×6 / 2×6 | No geometrically passing 6/8/9-bolt grid in this search | — | — |
| 2×6 / 2×8 | Six 3/8-inch bolts | 1.263 | 1.757 |
| 2×8 / 2×8 | Nine 3/8-inch bolts | 0.820 | 1.141 |
| 2×8 / 2×10 | Six 1/2-inch bolts | 0.893 | 1.241 |
| 2×8 / 2×10 | Nine 3/8-inch bolts | 0.721 | 1.002 |
| 2×10 / 2×10 | Six 1/2-inch bolts, three leg stations × two rim stations | 0.769 | 1.070 |
| 2×10 / 2×10 | Six 1/2-inch bolts, two leg stations × three rim stations | 0.747 | 1.039 |
| 2×10 / 2×10 | Nine 1/2-inch bolts | **0.609** | **0.847** |

A ratio below one passes this lateral screen only. The 150 lb column excludes the 250 lb case but retains the saved horizontal-load, hold-position and stiffness sensitivities. These are the indicated layouts' results, not independent searches for an optimal 150 lb design and not climber weight ratings. The small search does not rule out other connections or smaller-stock arrangements.

## Concrete nine-bolt option

The exploratory option has nine nominal 1/2-inch smooth-shank bolts per leg in a three-by-three parallelogram:

- Adjacent pitch along the leg: **65 mm**.
- Adjacent pitch along the rim grain direction: **75 mm**.
- New group centroid: saved current centroid plus **50 mm along the leg**.
- Leg square top: **250 mm beyond the saved current centroid**, replacing 177.105 mm. The calculated minimum is 248.833 mm, including the screen's 2 mm margin.
- Single leg and rim sections: **38.1 × 234.95 mm**.

The saved left centroid is approximately `(−1219.2, 984.612524, 1608.537416)` mm. Unit grain vectors are `LEG=(0,−0.260157458,0.965566205)` and `RIM=(0,0.642787610,0.766044443)`. Each bolt center is `saved centroid + 50 LEG + s LEG + t RIM`, with `s=−65,0,65` mm and `t=−75,0,75` mm. Mirror the lateral coordinate for the right side. Exact coordinates are in the result JSON.

Minimum directional edge/end margin is 3.167 mm. Minimum center-to-side-edge distances are 55.979 mm in the leg and 57.551 mm in the rim. The plate-fit calculation orients all 50.8 mm square BP1/2 plates with their edges parallel/perpendicular to the rim grain on both wood faces. The minimum separating-axis gap between plates is 2.497 mm: rim-adjacent centers are 75 mm apart, while neighboring leg stations are 53.297 mm apart perpendicular to the rim. The maximum plate half-projection toward a leg edge is 35.367 mm, below the minimum edge distance. Nut, bracket and LED collisions are not established by this check. Catalog bolt length, thread placement and complete washer stacks still require the actual modeled detail.

The eight-bolt 3/8-inch alternative passes the same lateral/spacing screen at 0.863 across all cases and 0.622 for the 150 lb subset, but its smaller-bolt washer and plate assembly was not assessed. No claim is made that nine bolts are the minimum possible connection.

## Wider-rim base bearing consequence

Keeping the rim front face fixed gives the following level-cut geometry against the current header. These are longitudinal dimensions at each outer rim, not bearing areas.

| Rim | Actual header overlap | Rim overhang behind header |
|---|---:|---:|
| 2×6 | 182.365 mm | 0 mm |
| 2×8 | 229.453 mm | 10.938 mm |
| 2×10 | 229.453 mm | 77.253 mm |

The rim front is at y=−41.497 mm and the header spans y=−270.950 to −36.000 mm. A wider header is not automatically required: partial bearing may suffice. The revised model must use only the actual overlap/contact and evaluate its bearing and eccentricity. It must not silently support the overhanging portion.

## Criteria and limitations

The screen uses full-value 4D along-row spacing, thickness-dependent between-row spacing, a 127 mm maximum cross-grain spread, 7D tension-end distance, and force-directed 4D loaded/1.5D unloaded edges. Applying the perpendicular loaded-edge value to this oblique connection is a conservative screen. These rules come from [AWC NDS Chapter 12](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf).

Individual lateral references use the existing TR12 yield equations, diameter-dependent wood bearing, G=0.50, 45 ksi bolt bending yield and adjustment factors of one. Smooth shank across both wood members is assumed. No friction capacity is credited. The equal-stiffness planar group does not establish the exact distribution in flexible timber or the group adjustment for unequal stock widths.

The nine-bolt result leaves about 15.3% reference margin in the all-case comparison. Revised whole-frame stiffness, added wood weight, foot contact and changed base bearing can change demand. This screen holds the original resultants fixed; it cannot qualify those changes. Out-of-plane moment, axial bolt/washer forces and prying, local wood shear/splitting/net sections, fastener collisions and full assembly fit remain outside its result. The catalog plate's local geometric fit is not a plate strength qualification.

Developing this option would require modeling the isolated candidate, resolving its wider-rim/header bearing geometry, and applying the current assembled-response method to its actual connections. This search does not establish that such a large revision is necessary. Keep the selected 2×6 development baseline and its negative connection result intact; no replacement geometry is selected here.

## Reproduction

```sh
uv run python -m fea.current_leg_revision_screen
```

- [Screen implementation](../fea/current_leg_revision_screen.py)
- [Current stock profiles used for member boundaries](current-construction/stock-profiles.json)
- [Exact inputs, coordinates and results](../fea/results/current-leg-revision-screen.json)
- [Current assembled-frame evidence](current-frame-response.md)

The vectorized yield calculation was compared against the repository's separate scalar `dowel_yield.single_shear` implementation for three force directions and three bolt diameters; all nine comparisons agreed to relative tolerance 1e-12. Six focused regression checks also pass, covering the scalar comparison, rejection of invalid native evidence, and trial placement against the actual fixed rim-front plane. This was a lightweight analytical screen; no CAD regeneration, native solver or full test suite was run.
