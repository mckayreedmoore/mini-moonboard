# Independent-ply leg comparison: geometry and bounded next experiment

This is a separately named analysis path, `foot100-independent-plies`, not a
replacement for the original bonded leg or a construction release. Retain the
current 2×8-foot100 development baseline while evaluating whether its requested
two-sheet construction needs a different connection or member design.

**Completed evidence:** the [actual profile comparison](../fea/results/independent_leg_response/README.md)
passes its global, energy and two-mesh diagnostics. Even sharing gives 3.9223×
out-of-plane compliance versus the bonded reference and less than 0.04% change
in-plane. The predeclared experiment below is retained; its results do not
validate actual panel properties, glue, stitches, contact or stability.

## Geometry preflight

Use `footprint_frame.parts(100, drilled=True)`, not the historical leg coupon.
The current member has a continuous cut profile, a rounded knee, four bolt
bores, and a floor-clipped lower end. Split along **global X**, the thickness
direction, into two nominal 19.05 mm (3/4 in) plies. The right leg extends from
X = 1257.30 to 1295.40 mm and splits at 1276.35 mm; the left is mirrored.

`uv run pytest tests/test_independent_leg_geometry.py` checks both legs:

- Each ply is a valid single solid with half the original volume; their union
  reconstructs the original drilled leg without lost or overlapping volume.
- Each has a planar, finite-area floor face at Z = 0, with the area and centroid
  predicted by the actual lower-member angle. This checks nominal CAD seating,
  not floor levelness or simultaneous contact after deformation.
- Each of the four 10 mm bores crosses both plies inside surrounding wood.
  The nominal 9.525 mm bolt leaves 0.475 mm diametral clearance; the test does
  not assign contact engagement or bolt-bearing capacity.
- The rim is adjacent to the inner ply only. The outer ply is one ply thickness
  away from the rim; a through-bolt does not by itself enforce equal sharing.

No stitches or interface ties are added by this preflight. The source geometry,
viewer, original solid model and prior results remain unchanged.

## Predeclared next numerical comparison

First qualify a conditional **linear stiffness/load-sharing** comparison, not
a nonlinear capacity calculation. Use the same current full profile and holes
for all cases, retaining the generic equal-property material solely to isolate
the construction assumption. Do not call this a model of identified plywood.

1. Original homogeneous 38.10 mm reference.
2. Two uncoupled 19.05 mm plies with half the total applied resultant on each.
3. Two uncoupled plies with the full resultant on the inner ply; repeat on the
   outer ply if the chosen fixtures are not mirror-equivalent.

Apply in-plane and out-of-plane unit loading separately. Use documented
identical idealized fixtures at the four actual bolt-hole locations and
distributed loads on the floor-bearing faces. These reversed, restrained
fixtures isolate compliance; they do **not** represent unilateral floor contact
or actual loose-bolt engagement. Do not couple the two plies at their interface,
share mesh nodes, or silently introduce a common rigid foot plate.

For the actual profile, resolve loading into separate global X, Y and Z unit
force cases: X is out of the plywood plane; Y and Z span its plane. Record the
actual traction centroid and all three applied moment components. Moving the
full force from the full-width floor face onto the inner ply changes that
centroid by half a ply thickness (9.525 mm). For Y or Z loading it consequently
changes an applied moment by 9.525 Nmm per 1 N force; X loading has no moment
change from that X shift. This is a combined **sharing/eccentricity** sensitivity,
not identical six-component loading. Do not conceal it with a rigid coupling or
an undocumented correcting couple.

An uncoupled, no-contact ply model may permit separation or interpenetration
under unequal loading. It is a mathematical stiffness comparison only, not an
admissible simulation of the complete physical assembly. A subsequent assembly
model must address contact and actual connectors explicitly.

Before the profile runs, verify the fixture/load implementation on a homogeneous
straight-strip control: the section-property model predicts equal in-plane
aggregate bending rigidity and one-quarter out-of-plane aggregate rigidity for
independent plies versus the composite reference, under the required symmetric
loading and support assumptions. The bent, drilled leg need not exhibit those
exact displacement ratios. See the derivation and real-plywood limitations in
[the material recommendation](material-selection-recommendation.md).

Record all applied/support resultants, per-ply displacement and strain energy,
and load-sharing sensitivity at two mesh levels. Predeclare numerical tolerances
and the compared output locations in the executable experiment before launch;
do not choose tolerances after seeing its results. Keep fixture singularities
out of any proposed member-demand extraction and qualify that extraction
separately. A failed control or balance check stops interpretation of the
profile comparison.

## What the result can decide

### Executable profile experiment, declared before launch

The straight-strip [control now passes](../fea/results/independent_ply_control/README.md).
The actual [matched right-leg meshes](../fea/results/independent_leg_mesh/README.md)
retain the same quadratic elements for the bonded and independent cases;
only interface node connectivity changes. Mesh sizes are 40 and 25 mm, with
additional curvature-driven refinement around the bores. Before launch, the
response runner authenticates the full bore/floor selections against the
verified mesh archive, not just a connectivity checksum.

`fea/independent_leg_response.py` implements the three unit force directions
above, with generic E = 7000 MPa and ν = 0.3. Each job has a 120-second solver
cap and two OpenMP threads. The frozen numerical gates are 0.001 N and
0.01 Nmm per residual component, 1e−9 mm for fixed/unloaded displacement,
0.1% for native-energy versus half-work comparisons, 1e−10 Nmm for unloaded
energy, and 5% for the two-mesh change in work-conjugate compliance. These are
experiment diagnostics, not allowable deformations or structural capacities.

Native `ELSE` output is requested separately for each ply's element set. For
independent plies it is compared with each ply's half external work; for the
bonded reference only the **sum** is compared with total half external work,
because an individual bonded ply also exchanges interface work. The exact
CalculiX 2.21 manual identifies `ELSE` as whole-element internal energy and
requires its output request to trigger calculation; the parser follows that
version's `printout.f` total-energy format.
[CalculiX 2.21 manual](https://www.dhondt.de/ccx_2.21.htm.tar.bz2).

The current mesh is not exactly mirror-symmetric in its discretization, so all
three directions also run with the entire unit force on the **outer** ply.
That avoids attributing discretization differences to physical sidedness.
No profile result is claimed by this predeclared section.

This experiment can identify whether independent-ply compliance or unequal
sharing is consequential enough to prioritize leg redesign. It cannot select
stitch spacing, establish real load sharing, prove buckling resistance, assign
panel strength, or qualify the workshop adhesive. Its next physical model must
replace imposed sharing with actual connector engagement/slip and allow
independent-ply motion under justified restraints.

If this mechanism governs, changing 2×8 rims to 2×10 or 2×12 is not the targeted
remedy. Develop either a documented structural lamination, a verified
mechanically connected two-ply assembly with no adhesive credit, or a separately
checked engineered-member geometry. Material identity and connection evidence
remain prerequisites for comparing demands with resistance, not reasons to
invent capacities for the present C-3 plywood reference.
