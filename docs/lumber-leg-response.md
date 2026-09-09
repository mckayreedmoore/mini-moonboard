# Straight-leg coupled-frame comparison

This analysis replaces the current paired-plywood legs with the separately
modeled [straight-lumber variants](leg-stock-comparison.md). The frame and its
existing gusset releases remain unchanged. Native comparisons for all four
lumber sizes, a 300 mm extended 2×8 footprint and a finer-leg mesh comparison
are recorded below. Preparation alone is not a result.

## Native results: unchanged foot-centre position

The native archives for [2×6](../fea/results/lumber-leg-response/2x6-e0-m40-E7000.tar.gz),
[2×8](../fea/results/lumber-leg-response/2x8-e0-m40-E7000.tar.gz) and
[2×10](../fea/results/lumber-leg-response/2x10-e0-m40-E7000.tar.gz) and
[2×12](../fea/results/lumber-leg-response/2x12-e0-m40-E7000.tar.gz)
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
| New 2×12 / 100 | 6.126 | 303.7 | 8.3 |
| Current bonded plywood / 1000 | 3.137 | 592.2 | 40.8 |
| New 2×6 / 1000 | 2.930 | 602.4 | 91.9 |
| New 2×8 / 1000 | 2.869 | 603.9 | 70.5 |
| New 2×10 / 1000 | 2.816 | 598.6 | 52.7 |
| New 2×12 / 1000 | 2.768 | 593.2 | 39.5 |
| Current bonded plywood / 10000 | 2.369 | 770.9 | 85.6 |
| New 2×6 / 10000 | 2.120 | 857.3 | 250.2 |
| New 2×8 / 10000 | 2.064 | 910.5 | 209.8 |
| New 2×10 / 10000 | 2.024 | 910.8 | 167.8 |
| New 2×12 / 10000 | 1.994 | 937.0 | 135.6 |

This is a whole-assembly comparison including the **changed bolt layout**, not
an isolated material substitution. The new geometry is less flexible at the
loaded hold in this trial, but its compact bolt group develops greater lateral
and axial peaks at the stiffest assumed connection. Do not choose it on
displacement alone. Connection qualification and combined member checks
remain open; the recommendation below is for further development, not release.
None of the spring values is a measured joint
property or a guaranteed bound on the real joint.

`fea.lumber_leg_summary` also reports 150, 200 and 300 lb cases, with the
governing bolt, load case and signed simultaneous components for each peak.
The current reference is
[`coupled-leg-release.tar.gz`](../fea/results/coupled-leg-release.tar.gz).

## Longer 2×8 comparison

The [2×8 with 300 mm additional foot-centre extension](../fea/results/lumber-leg-response/2x8-e300-m40-E7000.tar.gz)
also passes all 27 native numerical checks and 648 scenario replays. At 250 lb,
its separate peak values are:

| Spring stiffness, N/mm | Loaded-hold displacement, mm | Single-bolt lateral force, N | Single-bolt axial force, N |
| --- | ---: | ---: | ---: |
| 100 | 6.112 | 312.6 | 10.9 |
| 1000 | 2.664 | 567.2 | 58.8 |
| 10000 | 1.980 | 857.9 | 169.1 |

The whole-frame response improves in several respects despite the longer
individual leg: the changed angle and support leverage matter as well as member
length. Do not substitute an isolated length-cubed strip comparison for this
assembly result. The extra 300 mm (11.81 in) of footprint adds about 0.86 kg
under the shared density assumption. It does not fix the joint on its own:
the maximum direction-dependent lateral demand/reference ratio at 250 lb is
still 1.090 in this trial, before axial/group checks.

The separate [rigid-floor comparison](leg-stock-comparison.md#rigid-floor-comparison-results)
improves from 678 to 696 feasible cases out of 1296 at assumed μ=0.1; both cover
all cases at μ=0.2. A longer footprint cannot overcome insufficient friction.
For example, the 150 lb, one-times-weight, 80%-mass, 300 N horizontal case
requires μ≥0.1342 for the extended 2×8 from net-force balance alone. This is a
necessary condition, not a sufficient friction specification. An independent
test verifies an analogous bound above 0.1 for every variant, including plywood;
this particular low-friction failure is not merely an inscribed-cone artifact.

## Leg-mesh sensitivity

A [30 mm target leg mesh](../fea/results/lumber-leg-response/2x8-e0-m30-E7000.tar.gz)
repeats the 2×8/e0 trial with the rest of the frame unchanged. All native checks
and scenario replays pass. For 250 lb, its separate peak values are:

| Spring stiffness, N/mm | Loaded-hold displacement, mm | Single-bolt lateral force, N | Single-bolt axial force, N |
| --- | ---: | ---: | ---: |
| 100 | 6.479 | 305.0 | 11.0 |
| 1000 | 2.870 | 602.4 | 70.4 |
| 10000 | 2.065 | 891.9 | 208.4 |

Compared with the 40 mm leg mesh, the listed displacement maxima change by less
than 0.055%, lateral maxima by at most 2.05%, and axial maxima by less than 0.69%.
The refined maximum directional lateral ratio remains 1.129 at 250 lb. This
does not reverse the joint-development conclusion. It is a two-resolution
**leg-mesh sensitivity check**, not convergence of the entire frame, local
bolt-bearing stresses, contact behavior or orthotropic wood response.

## Working recommendation

Advance **2×8 straight legs with the +300 mm footprint** to the next joint
experiment below. It uses ordinary straight stock and simple end cuts, avoids
relying on a glued pair of leg plies, provides more side-edge room than 2×6,
and reduces several of the present joint demands relative to 2×8/e0. The longer
footprint is an explicit tradeoff, not a universal requirement.

Keep 2×6 as a lighter alternative if the revised connection, lateral restraint
and combined member checks support it. There is no present justification for
choosing 2×10 or 2×12 solely from loaded-hold displacement: larger stock has not
removed the joint concern. **Do not purchase or drill from this recommendation
as though the new joint were validated.** The default/current construction
candidate is unchanged, and no variant is approved for climbing.

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

The report also evaluates direction-dependent bearing for every bolt/case using
[NDS Appendix J, Eq. J-2](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf)
and the actual YZ lateral-force vector, not the axial X component. For the
2×8/e0 peak lateral case, the rim and leg angles are 81.190° and 26.110°.
Using 5600/3650 psi parallel/perpendicular references gives a refined lateral
reference of **790.011 N** (yield mode IV), versus the same 910.531 N demand.
The ratio remains 1.153 before the unresolved axial/group checks. Thus the
conservative perpendicular-only shortcut does not by itself explain away this
case. This case's simultaneous axial magnitude is 209.846 N, not an additional
lateral force. Other cases retain their own directional ratios in the report;
maximum force and maximum demand/reference ratio need not be the same case.

```sh
uv run python -m fea.lumber_leg_resistance fea/results/lumber-leg-response/2x8-e0-m40-E7000.tar.gz
uv run pytest -q tests/test_lumber_leg_resistance.py
```

### Next joint experiment: isolated geometry, not yet solved

The present model uses a 50×50 mm parallelogram bolt group and a square top
120 mm beyond its centre. A preliminary geometry check suggests extending the
top by 30 mm and testing **100 mm along-leg × 50 mm along-rim pitch**. At zero
extra footprint, this would leave 85.689 mm to the leg top and 51.078 mm to the
rim side edge. Even 2×6 would retain 49.351 mm to its side edge. These exceed the
same nominal 7D/4D comparisons used above; they do not establish resistance.

`mini_moonboard.lumber_leg_spread_frame` now implements this separate geometry.
The extended wood, new bores and complete assembly have been regenerated for
2×8/+300 mm and the 2×6/e0 alternative. Their new-bolt/wood/hardware, extended-leg/
other-wood and extended-leg/retained-hardware checks found no overlaps above
0.01 mm³. All twelve stock/extension combinations pass the nominal spacing,
square-top and full-level-foot checks; full assembly collision checks are
limited to the two specified cases. Obsolete compact-pattern bores are absent,
not plugged, and unrelated frame machining is retained.

This experiment has **not** been natively solved or added to the viewer. The
viewer and native archives still represent the original 50×50 mm group.
The larger lever arm is not a drilling instruction or a demonstrated structural
improvement. Increasing lumber width alone has not resolved the current
conditional bolt demand concern.

```sh
uv run pytest -q tests/test_lumber_leg_spread_frame.py
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
