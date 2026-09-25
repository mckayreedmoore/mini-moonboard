# Current corner-block fastener geometry screen

Status: source-bound geometry and conditional NDS detailing screen for
`led-clearance-2x6-runner-seated-blocks-v1`, 2026-09-24. No signed fresh
member actions, material receipt, resistance, joint acceptance, fabrication
release, or physical inspection is established here.

## Binding and method

This screen uses the parent-exported
[`geometry-snapshot.json`](hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json),
which binds the current viewer/report to repository revision `b1e8707d` and
records hashes for both source JSON files. In that snapshot,
`site/owner-wood-joints-wj24-scene.json` is
`74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf` and
`site/owner-wood-joints-review-report.json` is
`148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695`.
The frozen revision is the geometry source; the separate selected baseline
and preserved historical mechanics are not evidence for this screen.

The current outer-spine grain is screened conditionally along global `+Z`,
consistent with the long dimension of the proposed 2×6 blank and the earlier
WJ-03 spine basis. The [current stock review](corner-block-stock-review-2026-09-24.md)
does not approve the delivered grain or stock. For the trimmed central blocks,
the owner-directed vertical stock-length proposal is explicitly screened as
grain `+Z`; it is still a proposal, not observed material. Bolts and wood
remain candidate geometry: snapshot shaft diameter is nominally 6.35 mm,
outer bore diameter 7.5 mm, and tall-block bore diameter 7.3 mm.

The outer-post receiver rows below are also screened with grain `+Z`, carried
from the earlier source-post grain map in the [wood-limit-state basis](wood-limit-state-basis.md);
that does not prove the current post material or grain.

The [directional geometry helper](../../mini_moonboard/wood_joint_directional_geometry.py)
requires the signed force **on one identified wood member** and a grain vector
perpendicular to the bolt axis. No current signed per-member actions were
provided here, so I did not supply assumed loads to it. All “positive” and
“negative” cases below are conditional direction screens. A force on the
other member must be classified independently with that member's geometry.
The sign cases refer to lateral fastener load in the member plane; force along
the bolt axis belongs to separate bolt, washer and wood-bearing checks.

The structural reference is [ANSI/AWC NDS-2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
particularly §§12.1.2–12.1.3 and 12.5.1, Tables 12.5.1A–D; the
[AWC 2024 NDS page](https://awc.org/resources/2024-nds/) identifies this as
the current ANSI-approved edition. For a conditional nominal `D = 6.35 mm`
bolt screen, `4D = 25.40 mm`, `7D = 44.45 mm`, and `3.5D = 22.225 mm`.
For a softwood bolt group with pure tension parallel to grain, Table 12.5.1A
uses 7D for `CΔ = 1.0` and 3.5D for `CΔ = 0.5`; when a member's loaded end
lies between these, the conditional screen is `CΔ = end distance / 7D` and
the group minimum governs. Compression uses 4D / 2D. Table 12.5.1C uses 4D
at a loaded edge for pure perpendicular-to-grain loading and 1.5D at the
unloaded edge. These table conditions are not inferred for oblique loading.
They are not adopted capacities, and a conditional factor below 1.0 is not
by itself a joint failure. See the existing
[WJ-04 directional audit](representative-directional-end-edge-audit.md)
for the project's table interpretation and limits.

## Exterior 2×6 spine and post receivers

Each finished spine has global bounds `X = 38.1 mm`, `Y = 139.7 mm`,
`Z = 139.7–416.0 mm` on the left and the mirrored X bounds on the right.
Its four X-axis bolt centers are identical in Y/Z on the two mirrored
members. The two `post` axes have `y = −137.6 mm` and `z = 171.45,
213.50 mm`; the `side` axes are at `(-106.2281, 331.3156)` and
`(-77.3026, 365.7876) mm` in `(Y,Z)`. The post pair pitch is 42.05 mm. The
side pair has `(ΔY, ΔZ) = (28.9254, 34.4720) mm` and center distance
45.00 mm; it is diagonal to the assumed Z grain, so the two projected
components should be retained rather than called a grain-parallel pitch.

End and edge distances below are center-to-outer-boundary values. End pairs
are lower-Z / upper-Z; edge pairs are lower-Y / upper-Y. The post group also
passes through a distinct vertical receiver, so its distances must not be
copied from one member to the other.
For a signed `+Z` lateral component, the upper-Z end is loaded and lower-Z is
unloaded; a `−Z` component swaps them. A signed `+Y` component loads the
upper-Y edge and leaves the lower-Y edge unloaded; `−Y` swaps them. The
tables retain both sides so the action sign, once available, selects which
Table 12.5.1A or 12.5.1C condition applies.

| Receiver and axis | Z ends (mm) | Y edges (mm) |
|---|---:|---:|
| Left/right 2×6 spine, post 1 (`z=171.45`) | 31.75 / 244.55 | 44.45 / 95.25 |
| Left/right 2×6 spine, post 2 (`z=213.50`) | 73.80 / 202.50 | 44.45 / 95.25 |
| Left/right outer post, post 1 (`z=171.45`) | 171.45 / 67.45 | 38.10 / 101.60 |
| Left/right outer post, post 2 (`z=213.50`) | 213.50 / 25.40 | 38.10 / 101.60 |
| Left/right 2×6 spine, side 1 (`Y,Z = −106.2281,331.3156`) | 191.62 / 84.68 | 75.82 / 63.88 |
| Left/right 2×6 spine, side 2 (`Y,Z = −77.3026,365.7876`) | 226.09 / 50.21 | 104.75 / 34.95 |

For a pure lateral tension component parallel to the assumed `+Z` grain, the
spine post group's nearest upper end is 202.50 mm, so its end screen is
7D-clear. For tension toward `−Z`, the spine post group's minimum is 31.75 mm at post 1,
`CΔ = 31.75 / 44.45 = 0.714`; this remains above the 3.5D geometry-factor
floor by 9.53 mm. On the separate outer-post receiver, tension toward `+Z`
has only 25.40 mm at post 2, `CΔ = 25.40 / 44.45 = 0.571`; tension toward
`−Z` has 171.45 mm minimum. Thus the same bolt group gives different
conditional end factors in its two wood members and opposite signs. No sign
is selected without a fresh action for that member.

For the spine side pair, the nearest `+Z` end is 50.21 mm at side 2 (5.76 mm
above 7D); the nearest `−Z` end is 191.62 mm. The nearest `+Y` edge is
34.95 mm at side 2 (9.55 mm above the 4D loaded-edge reference); the nearest
`−Y` edge is 75.82 mm. For the spine post pair, the smaller Y edge distance
is 44.45 mm. For the outer-post receiver, the smaller Y edge distance is
38.10 mm. These are outer-box pure-direction screens only. The side-pair
centerline distance of 45.00 mm has 28.93 mm Y and 34.47 mm Z components;
no Table 12.5.1B–D spacing pass is claimed from its scalar length.

The outer modeled washer has nominal circular-envelope dimensions
18.6436 mm OD and 8.0 mm ID (the latter follows from its modeled volume and
thickness). Its ideal annulus area is 222.73 mm². The
published washer comparison in the [fastener-resistance basis](representative-fastener-resistance-method.md)
has OD 18.4658–19.0246 mm and ID 7.7978–8.3058 mm; taking minimum OD and
maximum ID gives 213.63 mm² of ideal annulus. The 7.5 mm modeled wood bore
is smaller than that maximum washer ID. At the closest side-2 Y edge,
34.95 mm center distance minus half the comparison's maximum OD leaves
25.44 mm from the washer perimeter to that block boundary. This describes
envelope fit and a circular-area calculation only; full wood support,
contact pressure, washer bending and resistance are unresolved. The catalog
comparison is not a received-product selection.

The exact snapshot solids are rectangular bounds with four 7.5 mm X-axis
bores: the spine AABB volume is 1,470,626.091 mm³ and finished volume is
1,463,893.265 mm³. Their 6,732.826 mm³ difference equals four modeled
`Ø7.5 × 38.1 mm` bores to rounding; the snapshot therefore supports this
modeled section arithmetic. Gross Z-normal area is `38.1 × 139.7 =
5,322.57 mm²`. Any Z-normal section through one bore station removes one
`38.1 × 7.5 = 285.75 mm²` strip, leaving **5,036.82 mm²** (94.63% of
gross). Bore stations are separated by more than their diameter, so no such
section intersects two of these holes. This is a geometric normal-section
area, not a design tensile resistance, row-tear-out check, splitting check,
or joint capacity.

## Trimmed central blocks: proposed grain `+Z`

Each handed block is a finished `83.9 × 139.7 × 134.7 mm` rectangular
envelope, with bounds `Z = 277.0–411.7 mm`. The 5 mm outer-X and top trim
was made without moving the bore axes. With proposed grain `+Z`, the two
principal axes (`±X`) have:

| Axis | Center `(Y,Z)` (mm) | Z ends (lower / upper, mm) | Y edges (lower / upper, mm) |
|---|---:|---:|---:|
| principal 1 | `(−124.3776, 326.4099)` | 49.41 / 85.29 | 51.32 / 88.38 |
| principal 2 | `(−90.3098, 367.0102)` | 90.01 / 44.69 | 85.39 / 54.31 |

The center-to-center principal pitch is 53.00 mm, with `ΔZ = 40.60 mm`
along the proposed grain and `ΔY = 34.07 mm` cross-grain. For common-sign
pure lateral `+Z` tension, the closest loaded end is the upper end of axis 2 at
44.69 mm: only 0.24 mm above 7D in nominal geometry. For `−Z` tension, the
nearest loaded end is 49.41 mm. Pure `+Z` compression has at least 44.69 mm
to the loaded end, above 4D by 19.29 mm. The pure cross-grain Y edge minima
are 54.31 mm for `+Y` and 51.32 mm for `−Y`, both above 4D. These are
conditional on the proposed grain vector and exact nominal model dimensions;
the 0.24 mm positive-end margin has no allowance for actual part or bore
tolerance. The oblique principal row projections are reported above, but
their spacing-table applicability is not decided here.

The two header axes are at `X = ±116 mm`, `Y = −140` and `−75 mm`,
`Z = 318.3423 mm`, with 65.00 mm center spacing in Y. Under this proposal
their bolt axes are parallel to grain (`±Z`), violating the directional
helper's side-grain prerequisite. Raw block-end projections are 41.34 mm
lower and 93.36 mm upper for each axis; raw Y edge distances are 35.70 /
104.00 mm at `Y=−140` and 100.70 / 39.00 mm at `Y=−75`. These dimensions
do not classify an NDS loaded end/edge or establish applicability for a
bolt placed parallel to grain. That connection requires an explicit method
and signed demand before resistance can be assessed.

The modeled principal washer envelope is 16.256 mm OD; its CAD ring volume
and 1.651 mm thickness imply a 6.35 mm inside diameter. The wood bore is
7.3 mm, so the ideal annulus area outside the bore is
`π/4 × (16.256² − 7.3²) = 165.69 mm²`. On a principal side face, the closest
Y boundary is at least 51.32 mm from an axis and the closest Z end is
44.69 mm; subtracting the 8.128 mm washer radius leaves 43.19 mm and
36.56 mm, respectively. For the top-face washer on a header axis, the
nearest X boundary is 26.95 mm from center, leaving 18.82 mm beyond its
radius. These are modeled annulus and footprint measurements only; washer
seat/contact adequacy and resistance remain open.

For the proposed Z-normal grain section through either principal bore, the
cross-section is `83.9 × 139.7 = 11,720.83 mm²` gross. The X-axis bore
removes an `83.9 × 7.3 = 612.47 mm²` strip; both Z-axis header bores remove
`2 × π × 7.3² / 4 = 83.71 mm²`. Those areas do not overlap at that section,
leaving **11,024.65 mm²** (94.06% of gross). The snapshot finished volume
matches the full rectangular envelope less these four modeled bores to
rounding. This is a modeled geometric net-section quantity, not a tension
capacity or splitting result. Other sections and failure paths still require
their own method and signed actions.

## Evaluation boundary

This bounded screen finds no end-distance shortfall below the cited NDS
`CΔ=0.5` floor or pure-direction loaded-edge 4D reference in the listed
outer-box quantities. It does identify sign-sensitive reductions on the
outer post/spine pair and a near-zero nominal 7D excess for the trimmed
principal group under the proposed `+Z` grain scenario. Neither establishes
failure or acceptance: the current action sign, member-specific demand,
material species/grade/moisture, as-built grain and dimensions, delivered
fastener properties, washer support, local connection checks and applicable
resistance methods are not supplied. `base_side_*` host end/edge checks and
all member-level reactions are separate from these block-only values.

Do not turn the displayed sections or annulus areas into capacities by
assigning generic lumber or steel strengths. Net-section force paths,
parallel-row tearout and cross-grain splitting still need the actual signed
member actions and complete candidate-specific resistance methods described
in the [wood-limit-state basis](wood-limit-state-basis.md) and
[representative-fastener method](representative-fastener-resistance-method.md).
