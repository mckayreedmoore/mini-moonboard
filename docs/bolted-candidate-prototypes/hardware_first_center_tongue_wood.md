# Center-tongue HL33 nominal wood geometry

Status: **conditional geometry screen only**. The paired JSON records every
center-to-boundary ray for the seven current nominal axes. Regenerate it with
`uv run python -m scripts.hardware_first_center_tongue_wood`. Coordinates
are analysis geometry, never drilling instructions.

The script reconstructs the parent trial's one-piece shaped post and tongue,
raised one-piece header, and both oblique one-piece principal toes from the
kerf-right CAD solids. It uses the parent trial's nominal HL33 axes: one
shared lower post axis, two lower and two upper header axes, and two upper
principal axes. The bolt comparator is D = 12.7 mm; modeled bore diameter is
14.2875 mm. The HL33 horizontal-hole inset remains an undimensioned pose
assumption. Distances are from nominal bolt *centers*, with no bore-radius or
manufacturing allowance.

The [AWC 2024 NDS Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
§12.5.1.2–.3 and Tables 12.5.1A–D are the conditional comparison basis
already used in this repository. The chapter URL was reachable, but direct
table text could not be extracted in this environment; the table markers
below therefore remain **conditional**. Table 12.5.1A's softwood
parallel-tension square-end markers are 3.5D for the reduced geometry factor
and 7D for the full factor. Table 12.5.1B gives 3D minimum and 4D full-factor
spacing for a parallel-to-grain row. Table 12.5.1C distinguishes loaded and
unloaded edges, and Table 12.5.1D addresses spacing between rows. Actual
member load directions, loaded edges, row grouping and geometry factors are
not assigned here. A **reversible 4D = 50.8 mm from both transverse edges**
and **7D = 88.9 mm toward both grain ends** are search filters only. Neither
filter is a formal NDS verdict on the shaped header shoulder or oblique
principal cut.

All values below are mm. For each pair, the first and second numbers are
the negative and positive directions of the stated grain or transverse axis.
Margins are distance minus 7D for grain, distance minus 4D for transverse.
The JSON also gives all centers and grain unit vectors.

| Nominal bolt axis | Grain boundary rays | 7D filter margins | Transverse boundary rays | 4D filter margins |
| --- | ---: | ---: | ---: | ---: |
| Shared post | 183.55 / 50.80 | +94.65 / −38.10 | 31.75 / 58.72 | −19.05 / +7.92 |
| Lower left header | 185.55 / 274.45 | +96.65 / +185.55 | 163.53 / 58.72 | +112.73 / +7.92 |
| Lower right header | 274.45 / 185.55 | +185.55 / +96.65 | 163.53 / 58.72 | +112.73 / +7.92 |
| Upper left header | 64.75 / 395.25 | −24.15 / +306.35 | 190.00 / 32.25 | +139.20 / −18.55 |
| Upper right header | 395.25 / 64.75 | +306.35 / −24.15 | 190.00 / 32.25 | +139.20 / −18.55 |
| Upper left principal | 2354.77 / 66.3147 | +2265.87 / −22.5853 | 53.899 / 85.801 | +3.099 / +35.001 |
| Upper right principal | 2354.77 / 66.3147 | +2265.87 / −22.5853 | 53.899 / 85.801 | +3.099 / +35.001 |

The post's grain is vertical. Its top ray reaches the flat 234.35-mm post
top at the bolt's X station; the thin central tongue is elsewhere along that
through-bolt. The header's grain is along X. Each header bore crosses the
raised part's ±230-mm local profile shoulders near its top; the listed grain
rays are to those **internal profile boundaries**, not to a free timber end.
At the lower section, the full-span header has different X end rays; all four
are recorded separately in JSON. The principals' grain slopes in Y/Z. Their
66.3147-mm near-end rays strike the actual horizontal toe cut at an angle to
grain. These rays do not establish NDS end distance at an oblique cut.

The post's 90.47-mm Y depth cannot place a 12.7-mm bolt at least 4D from
*both* Y edges: the necessary width is 2 × 4 × 12.7 = 101.6 mm, a nominal
11.13-mm deficit independent of bolt position. This is only a useful design
bound if the eventual joint actions make both edges loaded under the
perpendicular-to-grain Table 12.5.1C category; it is not an unconditional
NDS rejection or a requirement to enlarge this post without checking the
load path.

Independent header groups have center pitches of **88.9 mm** (lower pair)
and **330.5 mm** (upper pair). Their conditional 3D/4D parallel-row margins
are +50.8/+38.1 mm and +292.4/+279.7 mm, respectively. Across groups,
the same-side axes differ by X = 120.8 and Y = 26.47 mm, giving a true
center distance of **123.6661 mm** and nominal cylindrical bore surface gap
of **109.3786 mm**. Opposite-side cross-group pairs are 211.3640 mm apart.
The 26.47-mm transverse row offset is measured, but its Table 12.5.1D
category is unresolved. The parent's 120.8-mm figure is the X projection,
not the three-dimensional center distance.

The full lower header bore envelope has **0.0 mm** minimum CAD distance to
its adjacent shaped principal toe on each side: tangency without positive
overlap volume. The corresponding upper header bores have 43.6563 mm to
their adjacent toes. Opposite-side gaps are in JSON. Contact and proximity
need physical tolerance, bolt-stack, and local wood review; absence of
volume overlap does not establish clearance.

The reversible filters have negative margins at the post's top and rear
side, each upper header axis's nearest shoulder and front edge, and both
principal toes' grain rays. These values bound the nominal search; they do
not identify a loaded edge, assign an NDS end category, establish wood or
connector resistance, or approve the joint. Delivered holes, bends,
fastener stacks, cuts, load path, and simultaneous loads remain unresolved.
