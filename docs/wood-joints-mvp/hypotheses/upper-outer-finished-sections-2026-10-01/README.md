# Upper outer finished-section geometry

For `compact-floor-flush-wood-joints-development`, reviewed revision
`led-clearance-2x6-runner-seated-blocks-v1`, the exact saved finished solids
produce 20 section planes for the eight upper outer bolt axes and the eight
existing before/after host brackets. Twelve bore-centered cuts contain two or
three separate positive-area planar regions. The eight bracket cuts each have
one region. These results describe geometry; they do not establish stress,
resistance, splitting, compatible strain between regions, or joint acceptance.

The five imported BReps each contain one solid. Multiple regions in a planar
cut do not mean the three-dimensional timber is split or disconnected.
Geometric integration across all regions supplies an area and central moment
tensor, but does not authorize a common-strain strength calculation. Complete
load transfer around the bores and its applicable resistance method remain
required.

## Source coverage and results

The packet preserves eight bolt identities, sixteen host/cleat receiver
memberships and their uniquely matched cylinder patches, eight source host
application points, and eight bracket-plane identities. Twenty-four requested
records reduce to twenty planes: the two rail bolts at each corner share a
grain station, as do the two side bolts in each cleat. Grouping uses `1e-6 mm`
station tolerance, records the spread, and retains every source identity.
Each saved solid is imported once. The recursive source closure contains 97
unique SHA-256 and byte-size pins, including the independent polygon test.

Stations below are analytical distances along the recorded member grain
frame. Display rounding is not a shop dimension or permission to cut. Left
and right values agree at the shown precision; the local evidence retains
each individual plane, centroid, tensor, component and source record.

| Saved member | Grain station (mm) | Area (mm²) | Planar regions | Source |
| --- | ---: | ---: | ---: | --- |
| `base_rail_top` | 0.000 | 5322.570 | 1 | left before, terminal |
| `base_rail_top` | 45.450 | 4751.070 | 3 | both left rail bores |
| `base_rail_top` | 89.900 | 5322.570 | 1 | left after |
| `base_rail_top` | 2167.525 | 5322.570 | 1 | right before |
| `base_rail_top` | 2211.975 | 4751.070 | 3 | both right rail bores |
| `base_rail_top` | 2257.425 | 5322.570 | 1 | right after, terminal |
| each `base_side_left/right` | 2411.768 | 12419.330 | 1 | before |
| each `base_side_left/right` | 2440.768 | 11752.580 | 2 | side bore 1 |
| each `base_side_left/right` | 2473.768 | 11752.580 | 2 | side bore 2 |
| each `base_side_left/right` | 2502.668 | 12419.330 | 1 | after |
| each `top_outer_left/right_cleat` | 43.350 | 7236.460 | 2 | rail bore 1 |
| each `top_outer_left/right_cleat` | 59.850 | 6569.710 | 3 | both side bores |
| each `top_outer_left/right_cleat` | 76.350 | 7236.460 | 2 | rail bore 2 |

Independent rectangle-minus-slot area checks agree with the saved-solid cuts:
the rail is `38.1 × 139.7 − 2 × 38.1 × 7.5 = 4751.07 mm²`, a bored side
is `88.9 × 139.7 − 88.9 × 7.5 = 11752.58 mm²`, and a cleat cut is
`88.9² − n × 88.9 × 7.5`, for one or two slots. These are checks of the
reported planar geometry, not drilled-hole sizes or strength formulas.

## Reproduction and validation

From the repository root, with its locked environment installed:

```sh
.venv/bin/pytest -q docs/wood-joints-mvp/hypotheses/upper-outer-finished-sections-2026-10-01
.venv/bin/ruff check --no-cache docs/wood-joints-mvp/hypotheses/upper-outer-finished-sections-2026-10-01
.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-outer-finished-sections-2026-10-01/produce.py --plan-only
.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-outer-finished-sections-2026-10-01/produce.py --verify
```

The 20 synthetic/source-contract tests require no frozen raw evidence. Tests
cover rectangles, off-center holes, unequal disconnected strips, rotations,
adjacent terminal face patches, end faces, outside planes, invalid frames, ambiguous memberships, coincident
plane grouping, candidate identity and changed recursive pins. An independent
polygon-clipping and shoelace integration test checks a diagonal cylindrical
slot, including nonzero product moment, before and after an arbitrary
rotation and translation. Its expected area is `1847.1724394270311 mm²`,
centroid `(−0.12745042915924518, 2.2293604067598096) mm`, and central
`(uu, uv, vv)` integrals
`(248874.15120160574, −67430.05995042094, 602694.0319065998) mm⁴`.
The expected integration does not call the BRep mass-property routine.

`--plan-only`, `--write` and `--verify` require the locally retained upstream
reports and saved STEP files. `--write` creates ignored `sections.json` and
`source-pins.json`; `--verify` compares their exact bytes without writing.
A public checkout can run the synthetic tests and lint; missing private raw
evidence does not become a new engineering or fabrication prerequisite.
The existing CI packet gates include these synthetic tests. Full local source
replay remains a separate gate. No native structural solve, model regeneration
or reviewed-geometry change is part of this work.

The kernel used CadQuery 2.8.0 and OCP 7.9.3.1.1. Its bounded planar Boolean,
topological component grouping and BRep surface integration are described in
[section-geometry.md](section-geometry.md); source joining and frame semantics
are in [section-plan.md](section-plan.md). Numerical tolerances are recorded,
but no certified integration error bound is claimed. Component joining follows
shared positive-length topological edges, with no geometric welding of nearby
edges. The source application points stay distinct from saved bore centroids.

## Evidence identity

Producer, verification-code and local-result SHA-256 identities:
Raw results remain local; published code, this summary and
[review.md](review.md) retain the method and validation record.

| Artifact | SHA-256 |
| --- | --- |
| `section_geometry.py` | `8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3` |
| `test_section_geometry.py` | `4888d83218c5278e022bd53cb103d1eb1356ec98f8f8f3523e86ef5b9e466198` |
| `test_polygon_oracle.py` | `b6c044d45bb29e106779006a7a3a6b12dd626d946653a11be7d51be326ed8f66` |
| `produce.py` | `e5803f153c55ff622789cb24b4aed99cb9b70c5a593b63c0b14d129b7250b566` |
| `test_source_plan.py` | `3bd4c3ac9c76e1bb85695302a918467282c925c9d81641d4be2b29b4ea29fa4c` |
| `sections.json` | `292ff14f7b72db872312389eb123bc054021197e9af507f6a80b3c712ca3f0f7` |
| `source-pins.json` | `54ea0890403fc69b374ed873f1e2b619fb238de8aa74d56a307fecb9ba1097c6` |

Use these properties with the signed, simultaneous source actions in
[the upper outer load-path packet](../upper-outer-load-path-2026-10-01/)
only through an explicitly applicable section/load-transfer method. Point
resultants and external nodal-transfer sums are not integrated traction in
these bored sections. This packet closes a geometry-information gap and
does not close any complete-joint or formal MVP criterion.
