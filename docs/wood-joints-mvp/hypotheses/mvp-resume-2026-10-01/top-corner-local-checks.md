# Top outer corner local checks under six static cases

This extends the [complete corner action accounting](top-corner-checks.md)
with finished bore shear-plane areas, same-state parallel tear-out component
references, end/group-factor scenarios and washer wood-pressure references.
The reviewed geometry, 92 candidate axes, selected baseline and physical
release flags are unchanged. No native solver or agent review was used.

## Finished parallel tear-out paths

[top_corner_local.py](top_corner_local.py) reads the pinned finished STEP
cleats and their already mapped 7.5 mm bores. For each of eight bolt axes,
it queries two bore-tangent planes in each grain direction. Each interval
ends at the timber end or the next bolt in that same grain row. All 32
planar wood-area queries retain the neighboring orthogonal bores.

The component reference uses the triangular-stress/two-shear-line method in
[NDS-2024 Appendix E](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf),
§E.3, printed pp.174–175: `n Fv min(one-plane area)`. Taking the smaller
of the two queried plane areas is the declared conservative area scenario.
The reference uses the existing dry DF-L No. 2 `Fv=180 psi` input, with no
duration or size increase. The PDF and STEP sources are hash-checked.

| Declared one-plane path | Gross area | Finished area | Change from neighboring bores |
| --- | ---: | ---: | ---: |
| Side bolt to grain end, 59.85 mm interval | 5,320.665 mm² | 5,276.486 mm² | One 7.5 mm circular opening, 44.179 mm² |
| Rail bolt to next grain-row bolt, 33 mm interval | 2,933.700 mm² | 2,845.343 mm² | Two circular openings, 88.357 mm² |
| Rail bolt to nearest grain end, 43.35 mm interval | 3,853.815 mm² | 3,853.815 mm² | No finite-area opening on these planes |

The side pairs are two separate grain rows. Their opposing signed parallel
components are checked individually, toward their respective ends. The rail
pair is one two-bolt grain row; its same-state parallel components have the
same sign. Both individual path references and the complete two-bolt row
reference are retained, without assuming equal sharing.

Across 48 individual bolt states, the largest parallel component/reference
is **0.1954**, right `side_2`, K12-rear: 1,279.3 N over 6,548.4 N.
Across twelve rail-row states, the largest row component/reference is
**0.1518**, right rail pair, K12-rear: 1,072.2 N over 7,062.5 N.

These calculations resolve the arithmetic for the declared finished paths.
They do not qualify every possible crack path, cross-grain splitting,
combined loading or the shared two-face cleat as a complete joint.

## Geometry and group-factor scenarios

The current side-pair outer-face geometry meets the deliberately strict
pure-direction comparators: 7D grain ends and 4D loaded edges at quarter-inch
diameter. Its cleat grain ends are 59.85 mm and its closest transverse
external edge is 27.95 mm.

The rail cleat ends are **43.35 mm**, slightly below the **44.45 mm**
7D softwood parallel-tension comparator. They exceed its 22.225 mm minimum.
The §12.5.1.2(a) pure-direction end scenario gives
`Cdelta = 43.35/44.45 = 0.975253` for the rail pair. A reduced end factor
does not require lengthening the block when the resulting reference suffices.
This remains a named direction scenario rather than an invented interpolation
for every oblique action. Source:
[NDS-2024 Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf),
§12.5.1.2 and Tables 12.5.1A–C, printed pp.98–99.

For the rail pair's pure N load component, the cleat grain is parallel and
the rail grain perpendicular. Applying Eq.11.3-1 with the single-row area
definition in §11.3.6.3 gives `Cg=0.992743` using the minimum parallel-grain
spacing, 3D=19.05 mm, as the rail's equivalent group width. The alternative
full-Cdelta 4D-width scenario gives `Cg=0.994720`. The actual 33 mm rail-pair
pitch is across the rail grain and is not substituted for that width.
The source is [NDS-2024 Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf),
§§11.3.6.1–.3, printed p.74.

The rail pair's other transverse component and the side-pair singleton rows
retain separate `Cg=1` scenarios. These component scenarios supply no
combination rule for the full oblique couple. As an illustrative arithmetic
screen only, applying the smaller component Cg and conservative end factor
to the full individual-bolt reference produces:

| Interface | Largest illustrative lateral ratio with 106 ksi hypothesis | Case / bolt |
| --- | ---: | --- |
| Left rail | 0.678 | A12-rear / `rail_2` |
| Left side | 1.191 | A12-left / `side_2` |
| Right rail | 0.767 | K12-rear / `rail_2` |
| Right side | 1.384 | K12-rear / `side_2` |

The 106 ksi value remains the existing unadopted bending-yield estimate.
These are scenario references, not adopted oblique-group capacities.

## Washer wood pressure and direct bolt stresses

The existing upper-seat report supplies sixteen fully supported nominal
washer seats for these eight axes. The producer joins those unchanged
geometry records to all six current axial tie states. Under the minimum
catalog-annulus area of 213.628 mm², the maximum ideal wood pressure is
**2.539 MPa**, right `rail_1`, K12-rear at 542.4 N. This is **0.5892**
of the existing 625 psi Fc-perpendicular reference. It assumes uniform
pressure over that annulus and no preload or bearing-area increase.

Direct axial/thread-area and lateral/shank-area stress proxies are also
retained per state. Their largest combined von Mises proxy is 73.10 MPa,
right `side_2`, K12-rear. This proxy uses the nominal tensile-stress and
smooth-shank areas; it does not establish co-located bolt bending, thread
geometry, steel design resistance or complete bolt acceptance.

Washer metal bending, actual head/nut footprint, prying and partial contact
remain separate from the ideal wood-pressure result. The ordinary washer's
numeric yield is not inferred from hardness or the bolt grade. Existing
washer method work is preserved without launching its detailed mesh work
as part of this calculation.

## Next decision

The declared parallel paths, pure-direction adjustment scenarios and ideal
washer wood pressure do not displace the top side-bolt concern. Prepare a
local correction that carries the actual six-case force couple and meets
edge, spacing, stock and hardware/access constraints. Preserve the current
N envelope where possible; do not enlarge members merely to eliminate a
small permissible Cdelta reduction. Carry splitting and washer-transfer
limits through that correction and recalculate affected sharing.

All 47 formal criterion dispositions remain pending. The existing upper-left
service-joint owner retains that separate joint. No recurring agent review
round is scheduled.

The next [isolated correction proposal](top-corner-correction.md) uses two
full 4×6 cleats and four 5/16-inch side bolts. Its calculation preserves the
existing six-case lateral wrenches, checks the half-row-spacing edge and 5D
row-spacing comparators, and recalculates diameter-dependent wood bearing.
It does not alter or accept the reviewed model.

## Reproduction

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /usr/bin/timeout --signal=KILL 60s \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top_corner_local.py
```

[top-corner-local-references.json](top-corner-local-references.json) retains
every queried plane, source hash, signed component and factor scenario.
[top-corner-local-summary.csv](top-corner-local-summary.csv) contains the 48
same-state bolt records. The calculation and scoped Ruff pass; no software
test suite or independent review was run for this addition.
