# Current shoe-free frame: whole-body equilibrium

This calculation uses the actual `no-shoes-development` CAD with the 277 mm
floor-to-main-face datum. It is the first finite stage of the current structural
assessment: it checks whether the complete assembly can balance the stated loads
using compression-only foot reactions. It does not calculate member or
connection strength, frame deflection, or compatible load sharing.

## Method and reproducibility

Run `uv run python -m fea.current_frame_equilibrium`. The [JSON
result](../fea/results/current-frame-equilibrium.json) records source hashes,
each modeled component's mass and centroid, stock blank dimensions, all six
actual timber footprints, the support hull and all 142 hold locations. Fastener
components are fused within each connection before volume integration; T-nuts
and angles are explicitly steel. Declared densities are 600 kg/m³ for wood and
plywood and 7,850 kg/m³ for steel. These are calculation assumptions, not
measurements. Electrical parts, holds and unmodeled installation items are
covered by the separate 25 kg equipment allowance, positioned at the centered
uppermost hold plane. That placement is not the worst position for every edge.

Four posts and two rear feet carry compression. No pad or kicker-edge support is
credited. Omitting kicker bearing reduces the credited support region and avoids
relying on plywood-edge support. The calculation assumes that the floor can
resist horizontal sliding and rotation about the vertical axis. This assumption
does not establish available friction or represent an installed anchor. Feet are
not clamped against rotation or uplift.

For each loading case, the calculation sums all three-dimensional forces and
moments. Vertical equilibrium determines total normal reaction; equilibrium
about the two horizontal axes determines its required center of pressure. Signed
distance from that point to every convex support-hull edge determines whether
nonnegative vertical reactions can exist. Multiplying that distance by the total
normal reaction gives the restoring-moment reserve. No additional overturning
factor is applied: a positive reserve means mathematical equilibrium, not a
rated stability margin.

The calculation evaluates climber weights of 150 lb and 250 lb under static (1×)
vertical loading and a separate sensitivity case with 2× vertical loading.
Horizontal load is zero, ±300 N across the board, or ±300 N from front to rear,
with one horizontal axis loaded at a time. Each resultant acts at each hold with
an outward standoff of either 0 or 100 mm, giving 5,680 cases. The 2× multiplier
and horizontal forces are explicit project comparisons, not an exhaustive
dynamic spectrum or a climber rating. Force couples between hands and feet are
not included. The additional envelope below covers all horizontal force
directions.

For the case with the least edge reserve in each combination of climber weight,
vertical multiplier and horizontal direction, linear programming finds the
minimum and maximum admissible normal force at each whole footprint under the
same three equilibrium equations. Each extremum has its own admissible reaction
distribution. Extrema for different feet do not necessarily coexist. These
bounds describe reaction forces that satisfy equilibrium; they do not predict
the actual pressure distribution.

## Numerical result

All **5,680 sampled cases admit compression-only normal equilibrium** within the
credited timber support polygon. Modeled mass is **171.039 kg**, plus the stated
25 kg equipment allowance. Modeled centroid is approximately (X, Y, Z) = (−0.17,
619.91, 1,046.46) mm.

| Climber comparison | Vertical multiplier | Least edge distance | Raw restoring reserve |
| --- | --- | --- | --- |
| 150 lb | 1× | 319.73 mm | 828.02 N·m |
| 150 lb | 2× | 242.10 mm | 788.52 N·m |
| 250 lb | 1× | 264.19 mm | 801.69 N·m |
| 250 lb | 2× | 177.46 mm | 735.85 N·m |

Each row's minimum occurs at main hold A12, with 100 mm outward standoff and 300
N rearward force. The small modeled mass asymmetry distinguishes mirrored edge
cases. These distances are reserves to incipient rigid-body overturning, not
frame deflections, prescribed safety factors or climber ratings.

For the 250 lb × 2 governing case, the left rear foot's statically admissible
normal force is **2.482–3.019 kN**, while the right rear foot's is **0.651–1.188
kN**. The disjoint intervals show that equal support sharing between the left
and right sides is incompatible with this edge-load case. They do not establish
the actual split or the leg bolt-group forces. Individual front post ranges
include zero; this permits local uplift and does not require every foot to bear.

## Exact horizontal-azimuth and equipment-placement envelope

A separate analytic envelope evaluates a 300 N horizontal force along each
support-hull edge's outward normal. For any fixed load location, edge moment is
linear in horizontal force; its worst value over the 300 N circle occurs in that
normal direction. Checking all edges therefore covers every horizontal azimuth
for the reported minimum edge reserve without angular sampling.

The baseline keeps the centered 25 kg equipment location. A separate bounded
option places all 25 kg at the hold-front XY position with maximum outward
projection for each edge. This bounds any gravity-only equipment distribution
whose XY centroid lies within the convex hull of current hold-front positions.
It does not cover equipment outside that footprint, additional equipment mass,
or dynamic forces on equipment. Extremal equipment locations differ by edge.

Both envelopes retain a positive reserve. Their minimum edge distances and
restoring moments equal those in the corresponding four baseline rows above.
Rearward loading still governs when the equipment placement is bounded over the
hold footprint. Equipment placement changes the individual reaction ranges even
when the governing moment about the rear edge remains unchanged.

Both envelopes cover all 142 holds and both standoffs. Their eight governing
records, including normal-reaction bounds, are saved under
`all_horizontal_azimuth_envelope`. An independent diamond-footprint test
verifies that diagonal extrema are captured and outward equipment placement
worsens reserve as expected.

## What this closes and what remains

This calculation establishes the mass, applied loads and support geometry of the
current design and checks the whole assembly for rigid-body overturning.
Independent tests verify analytical centered loading, a horizontal-load
overturning example, unequal reaction sharing and edge-only compression contact.

Even when the required pressure center is inside the support hull, many reaction
distributions can satisfy equilibrium. Deformation of the frame and panels,
together with connection slip, determines which distribution occurs. The
remaining calculation must map those compatible reactions and applied loads into
the actual leg bolt groups, base-angle connections, bearing between the rims and
header and other governing members. The present linear-programming calculation
cannot establish their internal moments, racking stiffness or strength. No
larger lumber or additional reinforcement is selected by this screen alone.

See [current design review](current-design-review.md) and [base connection
basis](current-base-connection-basis.md).
