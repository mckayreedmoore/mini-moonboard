# Bottom-outer finished bolt placement and interface actions

This packet joins the reviewed bottom-left four-bolt layout to its finished
timber solids and all 21 existing A1/A12/K12 states. It resolves a bounded
edge-distance input and retains the cuts and neighboring bores needed for
local member checks. It does not adopt a resistance, NDS row/group, geometry
factor, criterion pass or complete joint. The selected angle-frame baseline
and reviewed wood-joint geometry are unchanged; no native solve was run.

The [method review](method-review.md) gives the exact 2024 NDS edge categories.
The [finished-edge review](finished-edge-review.md) independently checks the
current STEP faces and cut identities. Separate [source/code review](source-code-review.md)
and [calculation review](independent-calculation-review.md) check the implementation
and source reconstruction. The existing
[bottom joint packet](../bottom-outer-joint-disposition-2026-10-01/README.md)
retains the full cleat balance and the three distinct contact paths.

## Finished geometry result

Each source axis is independently reconciled into the proposed stock frame
and its matched 7.5-mm modeled bore. The code checks the three finished STEP
hashes, valid single solids and current face counts. At 0.01 mm inside each
end of every finite bore patch and at its midpoint, it queries both grain
directions and both transverse directions in the plane perpendicular to the
bolt. The 96 exact solid intersections preserve initial bore voids and all
subsequent gaps, and identify the finite planar terminal faces. Three depth
samples do not prove continuous through-thickness extrema or a load-bearing
ligament.

All 48 cross-grain rays reach the proposed stock edges at these depths.
The minimum is **27.9 mm**, at `side_2` on `bottom_outer_left_cleat`, rather
than a rounded 28 mm. The following distances are center-to-edge values, not
clear wood beyond the bore surface or drill instructions.

| Axis suffix | Receiver | Two cross-grain stock edge distances, mm | Minimum sampled finished end distance along grain, mm |
| --- | --- | ---: | ---: |
| `rail_1` | `base_rail_bottom_left` | 86.35 / 53.35 | 45.45 |
| `rail_2` | `base_rail_bottom_left` | 53.35 / 86.35 | 45.45 |
| `rail_1` | `bottom_outer_left_cleat` | 45.45 / 43.45 | 43.35 |
| `rail_2` | `bottom_outer_left_cleat` | 45.45 / 43.45 | 43.35 |
| `side_1` | `base_side_left` | 69.85 / 69.85 | 256.714903 |
| `side_2` | `base_side_left` | 69.85 / 69.85 | 289.714903 |
| `side_1` | `bottom_outer_left_cleat` | 28.00 / 60.90 | 59.85 |
| `side_2` | `bottom_outer_left_cleat` | 61.00 / 27.90 | 59.85 |

The twelve base-side grain rays terminate at finished cut planes before the
stock-envelope ends. For `side_1`, the actual sampled terminal distances are
256.714903 and 2255.400000 mm, compared with stock-coordinate distances
284.367606 and 2286.358406 mm. `side_2` gives 289.714903 and 2222.400000 mm,
compared with 317.367606 and 2253.358406 mm. The raw report explicitly marks
these stock/finished end mismatches. It never substitutes the longer blank
dimensions for the finished ray result.

For nominal `D=6.35 mm`, the lesser bearing-length ratio is 14 on each side
plane and 6 on each rail plane. The worst listed loaded/unloaded edge
constant is `4D=25.4 mm`; the parallel-loading branch at a ratio above six
also includes `S/2`. Within an interface explicitly limited to its two
33-mm-spaced axes, any between-row projection is at most 33 mm, so
`S/2≤16.5 mm`. Thus 25.4 mm is a conservative pair-only edge envelope, and
the sampled minimum has a 2.5-mm margin. This is a sufficient geometric
screen under that scope condition. It does not select the NDS load category,
establish the complete joint's fastener group, exclude other axes or adopt
a Table 12.5.1C pass. A larger group needs its own row-spacing bound.

The rail-cleat's 43.35-mm grain-end distance remains below the softwood
parallel-tension full-value threshold `7D=44.45 mm`, while exceeding the
minimum `3.5D=22.225 mm`. Its conditional end-factor sensitivity is about
0.975253 if that category governs. The side planes do not inherit this
factor. Other end categories, within/between-row spacing, the angled-axis
equivalent shear area and complete geometry adjustment remain separate.

## Neighboring bores and local sections

The midpoint grain rays through each cleat side bore cross a neighboring
rail-bore chord at about 12.885792 to 20.114208 mm from the side-bore center.
The end-depth samples miss that chord. The exact four rail/side cylindrical
face distances are approximately **9.0 mm**, confirmed by direct finite-face
distance queries on `facet009/010` versus `facet006/007`; the independent
geometry review records the distinction from a larger fixed-slice distance.
These thin wood ligaments are retained as local net-section and stress
dependencies. No minimum ligament rule, splitting resistance or traction
distribution is supplied by the exterior edge-distance screen.

The rail's cross-grain rays also pass through its paired bolt bore: the
33-mm center spacing leaves 25.5 mm between the two 7.5-mm bore surfaces.
Long grain rays retain distant service passages instead of restoring solid
wood. Passing the proposed exterior-edge envelope does not erase these
internal voids or qualify the gross native timber mesh as a bored-section
resistance model.

## Same-state complete interface actions

The 168 member/bolt states retain the signed lateral plane, separate outer
axial tie, their native rounding radii, local force projections and a
component-based candidate edge direction. Grain direction, bolt-axis angle
and transverse edge direction remain distinct. An interval straddling zero
does not select an edge. The candidate edge label is a component diagnostic,
not an adopted NDS direction for an oblique load.

For each interface and receiver, the code sums exactly eight named source
actions: two lateral planes, two outer-seat ties and four contact cells.
It transports their moments about an explicit midpoint of the two axis
datums, keeping different first/second tie endpoints. All 84 such complete
interface force vectors are oblique to their pair line beyond the source
rounding bounds. Full-load angles to the line are:

| Case | Rail interface | Side interface |
| --- | ---: | ---: |
| A1 rear | 23.221108° | 80.279624° |
| A12 rear | 67.771060° | 47.570232° |
| K12 rear | 69.466933° | 70.459323° |

These differ from the earlier bolt-plane-only sums because axial ties and
contact are now included. They are interface actions, with explicit moments,
not the full host member boundary or whole-cleat connection group. Other
interfaces and body loads remain outside each eight-action sum. Therefore
the code records no automatic two-bolt NDS row, numeric `Cg` or adopted
`CΔ`. Complete local/group mechanics must account for the oblique force and
couple instead of assuming uniform parallel-row loading.

The unchanged A1 `side_1` lateral action is 661.948743 N, with a separate
197.1248-N tie. Its raw demand/reference quotient remains 1.0945088665
under the unadopted quarter-inch, 45-ksi bending-yield scenario. The current
edge result does not reduce that demand, supply a supported hardware value,
resolve the axial/washer interaction or accept the joint.

## Reproduction and source boundaries

Use the repository virtual environment from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/bottom-outer-bolt-placement-2026-10-01/produce.py --joint-report /tmp/mini-moonboard-bottom-outer-joint-2026-10-01.json > /tmp/mini-moonboard-bottom-outer-placement-2026-10-01.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/bottom-outer-bolt-placement-2026-10-01/parent_verify.py
.venv/bin/python -m unittest discover -s docs/wood-joints-mvp/hypotheses/bottom-outer-bolt-placement-2026-10-01 -p 'test_*.py' -v
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/bottom-outer-bolt-placement-2026-10-01
```

The eleven tests include analytic bored-box intersections, a finished end
cut, changed axis datum/direction/diameter/frame, ambiguous bore rejection,
frozen-input corruption, uncertain signs and distinct axial endpoints. The
CAD tests use synthetic solids; they do not alter candidate geometry.
All eleven tests and Ruff pass. The independent reviewer reconstructed the
168 member/bolt states and 84 interface wrenches from frozen response actions,
and its full producer replay is byte-identical. Parent separately ran the
numeric verifier successfully and checked the four finite bore-face distances.
The method, code and finished-edge reviews have no unresolved material finding
within this packet's stated scope.

Producer SHA-256:
`75e7eed05e9f24c1a04b35a8faeb03e4f284259ae2af54abd45c611bb2e0684f`.
Local raw report SHA-256:
`21c2eba56b80efa174cdb5ecdb206468a6b15882732c6edd548d2027063f58c3`.
The inputs are the prior bottom joint report
`fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029`
and current finished-feature register
`bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19`.
Upstream case/source files and pinned producer, interval helper and NDS
Chapter 12 bytes are checked before calculation. Raw JSON and STEP remain
local; publication contains code and summaries only. No delivered stock,
hardware, cuts, holes or floor were inspected.
