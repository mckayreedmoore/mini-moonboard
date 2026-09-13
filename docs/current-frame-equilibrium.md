# Current shoe-free frame: whole-body equilibrium

This calculation uses the actual `no-shoes-development` CAD with the 277 mm
floor-to-main-face datum. It is the first finite stage of the current structural
assessment: it checks whether the complete assembly can balance the stated
loads using compression-only foot reactions. It does not calculate member or
connection strength, frame deflection, or compatible load sharing.

## Method and reproducibility

Run `uv run python -m fea.current_frame_equilibrium`. The
[JSON result](../fea/results/current-frame-equilibrium.json) records source
hashes, each modeled component's mass and centroid, stock blank dimensions,
all six actual timber footprints, the support hull and all 142 hold locations.
Fastener components are fused within each connection before volume integration;
T-nuts and angles are explicitly steel. Declared densities are 600 kg/m³ for
wood/plywood and 7,850 kg/m³ for steel. These are calculation assumptions, not
measurements. Electrical parts, holds and unmodeled installation items are
covered by the separate 25 kg equipment allowance, positioned at the centered
uppermost hold plane. That placement is not the worst position for every edge.

Four posts and two rear feet carry compression. No pad or kicker-edge support
is credited. Omitting kicker bearing reduces the credited support region and
avoids relying on plywood-edge support. Horizontal no-sliding reactions and
floor yaw resistance are assumed available; this does not qualify friction or
an installed anchor. Feet are not clamped against rotation or uplift.

For each loading case, the calculation sums the full three-dimensional force
and moment wrench. Vertical equilibrium determines total normal reaction;
roll/pitch equilibrium determines its required center of pressure. Signed
distance from that point to every convex support-hull edge determines whether
nonnegative vertical reactions can exist. Distance times total reaction gives
raw restoring-moment reserve. No additional overturning factor is applied:
a positive reserve means mathematical equilibrium, not a rated stability margin.

Each of 150 lb and 250 lb is evaluated with static (1×) and separate 2× vertical
sensitivity loads. Horizontal load is zero, ±300 N across the board, or ±300 N
fore/aft, one axis at a time. Each resultant acts at each hold with 0 or 100 mm
outward standoff: 5,680 cases. The 2× multiplier and horizontal forces are
explicit project comparisons, not an exhaustive dynamic spectrum or a climber
rating. Hand/foot couples are not included. The additional envelope below covers all horizontal azimuths.

For the case with least edge reserve in each weight/multiplier/direction family,
linear programming finds the minimum and maximum admissible normal force at
each whole footprint under the same three equilibrium equations. Each extremum
has its own admissible reaction distribution. Extrema for different feet do
not necessarily coexist. These are statics bounds, not predicted pressure.

## Numerical result

All **5,680 sampled cases admit compression-only normal equilibrium** within the
credited timber support polygon. Modeled mass is **171.039 kg**, plus the stated
25 kg equipment allowance. Modeled centroid is approximately
(X, Y, Z) = (−0.17, 619.91, 1,046.46) mm.

| Climber comparison | Vertical multiplier | Least edge distance | Raw restoring reserve |
| --- | --- | --- | --- |
| 150 lb | 1× | 319.73 mm | 828.02 N·m |
| 150 lb | 2× | 242.10 mm | 788.52 N·m |
| 250 lb | 1× | 264.19 mm | 801.69 N·m |
| 250 lb | 2× | 177.46 mm | 735.85 N·m |

Each row's minimum occurs at main hold A12, with 100 mm outward standoff and
300 N rearward force. The small modeled mass asymmetry distinguishes mirrored
edge cases. These distances are reserves to incipient rigid-body overturning,
not frame deflections, prescribed safety factors or climber ratings.

For the 250 lb × 2 governing case, the left rear foot's statically admissible
normal force is **2.482–3.019 kN**, while the right rear foot's is
**0.651–1.188 kN**. The disjoint intervals show that equal left/right support
sharing is incompatible with this edge-load case. They do not establish the
actual split or the leg bolt-group forces. Individual front post ranges include
zero; this permits local uplift and does not require every foot to bear.

## Exact horizontal-azimuth and equipment-placement envelope

A separate analytic envelope evaluates a 300 N horizontal force along each
support-hull edge's outward normal. For any fixed load location, edge moment
is linear in horizontal force; its worst value over the 300 N circle occurs
in that normal direction. Checking all edges therefore covers every horizontal
azimuth for the reported minimum edge reserve without angular sampling.

The baseline keeps the centered 25 kg equipment location. A separate bounded
option places all 25 kg at the hold-front XY position with maximum outward
projection for each edge. This bounds any gravity-only equipment distribution
whose XY centroid lies within the convex hull of current hold-front positions.
It does not cover equipment outside that footprint, additional equipment mass,
or dynamic forces on equipment. Extremal equipment locations differ by edge.

Both envelopes retain positive reserve. Their minimum edge distances and restoring moments equal the corresponding four baseline rows above: rearward loading still governs, including when equipment placement is bounded over the hold footprint. Equipment changes individual reaction ranges even when the governing rear-edge moment stays unchanged.

Both envelopes cover all 142 holds and both standoffs. Their eight governing
records, including normal-reaction bounds, are saved under
`all_horizontal_azimuth_envelope`. An independent diamond-footprint test verifies
that diagonal extrema are captured and outward equipment placement worsens
reserve as expected.

## What this closes and what remains

This establishes a current-geometry mass/load/support calculation and a direct
whole-assembly overturning screen. Independent tests verify analytical centered
loading, a horizontal-load overturning example, unequal reaction sharing and
edge-only compression contact.

Even when the required pressure center is inside the support hull, many reaction
distributions can satisfy equilibrium. Frame/panel deformation and connection
slip determine which distribution occurs. The remaining calculation must map
those compatible reactions and applied loads into the actual leg bolt groups,
base-angle connections, rim/header bearing and other governing members. The
present LP cannot establish their internal moments, racking stiffness or strength.
No larger lumber or additional reinforcement is selected by this screen alone.

See [current design review](current-design-review.md) and
[base connection basis](current-base-connection-basis.md).
