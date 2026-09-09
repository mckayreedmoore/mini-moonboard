# Straight-leg coupled-frame comparison

This analysis replaces the current paired-plywood legs with the separately
modeled [straight-lumber variants](leg-stock-comparison.md). The frame and its
existing gusset releases remain unchanged. Native 2×6, 2×8 and 2×10 comparisons
are recorded below; 2×12 and extension comparisons remain pending. Preparation
alone is not a result.

## Native results: unchanged foot-centre position

The native archives for [2×6](../fea/results/lumber-leg-response/2x6-e0-m40-E7000.tar.gz),
[2×8](../fea/results/lumber-leg-response/2x8-e0-m40-E7000.tar.gz) and
[2×10](../fea/results/lumber-leg-response/2x10-e0-m40-E7000.tar.gz)
each contain 27 solved basis cases (nine per spring stiffness) and 648 linear
load combinations. All equilibrium, interpolation and energy gates pass, and
the archives replay without a native solver. The mesh target is 40 mm and both
materials use the equal-modulus E=7000 MPa comparison assumption.

For the intended 250 lb maximum climber, the following are **separate maxima**
over the established load cases, including two-times-weight plus 300 N horizontal
force. They are not a simultaneous force/displacement vector or a load rating.

| Leg / per-axis spring stiffness, N/mm | Loaded-hold displacement, mm | Single-bolt lateral force, N | Single-bolt axial force, N |
| --- | ---: | ---: | ---: |
| Current bonded plywood / 100 | 6.658 | 310.9 | 8.2 |
| New 2×6 / 100 | 6.626 | 308.2 | 13.5 |
| New 2×8 / 100 | 6.478 | 305.1 | 11.0 |
| New 2×10 / 100 | 6.295 | 302.9 | 9.1 |
| Current bonded plywood / 1000 | 3.137 | 592.2 | 40.8 |
| New 2×6 / 1000 | 2.930 | 602.4 | 91.9 |
| New 2×8 / 1000 | 2.869 | 603.9 | 70.5 |
| New 2×10 / 1000 | 2.816 | 598.6 | 52.7 |
| Current bonded plywood / 10000 | 2.369 | 770.9 | 85.6 |
| New 2×6 / 10000 | 2.120 | 857.3 | 250.2 |
| New 2×8 / 10000 | 2.064 | 910.5 | 209.8 |
| New 2×10 / 10000 | 2.024 | 910.8 | 167.8 |

This is a whole-assembly comparison including the **changed bolt layout**, not
an isolated material substitution. The new geometry is less flexible at the
loaded hold in this trial, but its compact bolt group develops greater lateral
and axial peaks at the stiffest assumed connection. Do not choose it on
displacement alone. Connection resistance, member checks, the remaining stock,
extension sensitivity and mesh sensitivity remain to be completed before a
comparative recommendation. None of the spring values is a measured joint
property or a guaranteed bound on the real joint.

`fea.lumber_leg_summary` also reports 150, 200 and 300 lb cases, with the
governing bolt, load case and signed simultaneous components for each peak.
The current reference is
[`coupled-leg-release.tar.gz`](../fea/results/coupled-leg-release.tar.gz).

## Member and connection demand screen

`fea.lumber_leg_resistance` recovers the simultaneous force/moment wrench for
each leg from its four native connector forces, including the 19.05 mm
interface-to-centroid eccentricity. It reports gross-section biaxial normal
stress, transverse shear and torsional moment at the endpoints of the clear
prismatic interval. That interval starts above the floor bevel and ends below
both the physical hole envelope and the native interpolation-node load spread.
These are section-resultant stresses, not recovered local finite-element stress
peaks; bolt-group, bevel and torsional shear stresses are excluded.

Conditional references assume **US Douglas Fir-Larch No. 2, dry and unincised**,
not a generic lumber species or an interchangeable North/South grade. Reference
properties come from [2024 NDS Supplement Table 4A](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf).
The script applies the size factors, but no load-duration, repetitive-member or
flat-use increase. Both-axis K=1 column calculations use
[NDS §3.7](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
and require translation restraint at both ends; the real unanchored feet have
not established that condition. The 2×8/e0 concentric-column reference is
11.955 kN, **not a beam-column resistance or climber rating**.

The two-sawn-member bolt reference is 668.034 N per bolt in lateral shear,
using two 38.1 mm members, conservative 0.298 in thread-root diameter, assumed
45,000 psi bolt bending yield and perpendicular-grain bearing assumptions.
The calculation reuses [AWC TR12 yield equations](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf)
with NDS reduction terms. It does not qualify steel procurement, group action,
splitting, axial bolt/washer resistance or installation tolerances. Do not
multiply this value by four to rate the group.

The 250 lb / stiffest-spring 2×8 lateral demand of 910.5 N exceeds this
conditional single-bolt reference. The excess is enough to reject an immediate
recommendation of the present joint under these assumptions; it is **not proof
of the actual assembly's failure load**. Combined member interaction, lateral
beam stability and torsional strength are not yet evaluated. Separate small
stress or concentric-column demands cannot close those gaps.

```sh
uv run python -m fea.lumber_leg_resistance fea/results/lumber-leg-response/2x8-e0-m40-E7000.tar.gz
uv run pytest -q tests/test_lumber_leg_resistance.py
```

## What the comparison models

- The old leg elements and orphan nodes are removed. Every remaining frame
  element retains its connectivity and coordinates, as do the three load targets.
- Each new undrilled leg is independently meshed into straight-sided quadratic
  tetrahedra. Mesh volume, centroid, full floor face and inner side face are
  checked against its actual CAD solid. No nodes are shared with the frame.
- Eight new rim bolts and eight retained gusset bolts each have three linear
  point springs. Spring stiffness is swept through 100, 1000 and 10000 N/mm per
  axis, as numerical assumptions—not measured properties or physical bounds.
- The two sides of each new bolt use their own six-node quadratic interpolation
  weights at the actual common point. Borrowing weights from the other mesh
  would violate displacement/force consistency and is rejected.
- All floor nodes remain fixed in XYZ. Gravity, unanchored contact, bolt holes,
  washer bearing, splitting, friction and nonlinear material behavior are absent.
  Other frame wood interfaces remain ideally bonded. Consequently these are
  conditional elastic comparisons, not actual joint qualification or approval.
- Frame E is 7000 MPa; leg E is an explicit separate input, initially 7000 MPa
  for the equal-modulus geometry comparison. Both are isotropic with ν=0.3.
  No lumber or plywood strength is assigned by this numerical modulus.

The existing nine X/Y/−Z basis cases at A12, K12 and F6 produce the established
216 signed combinations for 150/200/250 lb and the 300 lb sensitivity, with
one/two-times-weight and horizontal-force cases. These are linear combinations,
not 216 independently solved nonlinear cases. The separate rigid-floor study
has more hold/direction/mass combinations and includes self-weight; do not mix
the two sets as though they were the same physical simulation.

## Acceptance checks established before solving

The inherited global force/moment and gusset checks remain. Additional checks
require each leg's connector forces **plus its native floor reactions** to
balance within 0.02 N and 10 N·mm, and interpolation motion errors below
1e−5 mm. Native wood strain energy plus separately calculated spring energy
must agree with half the external work within 0.1%.

There is no lower-bound comparison against the old bonded-plywood frame's
compliance: changing geometry invalidates that inherited bound. Positive work
and equilibrium/energy checks are retained. Reported loaded-hold displacement
is not the maximum displacement throughout the frame. Each basis also records
maximum displacement over all nodes of each new leg; basis maxima cannot be
linearly combined into a scenario maximum.

## Toolchain and replay

Meshing and solving use the existing pinned Docker image, with no additional
host Gmsh, system library or sudo installation. Host CadQuery exports the solid
and audits the returned mesh. Integration tests explicitly skip if Docker or
the pinned image is unavailable; an archive replay does not require a solver.

```sh
uv run pytest -q tests/test_lumber_leg_mesh.py tests/test_lumber_leg_response.py
uv run python -m fea.lumber_leg_response 2x8 --output /tmp/leg-2x8-native.tar.gz
uv run pytest -q tests/test_lumber_leg_native.py tests/test_lumber_leg_summary.py
uv run python -m fea.lumber_leg_summary fea/results/lumber-leg-response/2x8-e0-m40-E7000.tar.gz
```

The runner refuses to overwrite existing evidence, preserves failed native
work in `fea/generated`, and records source identities, full prepared inputs,
decks, native outputs and case vectors. Passing numerical gates is not a member
strength, buckling, joint-resistance or unanchored-contact approval.
