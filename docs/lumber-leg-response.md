# Straight-leg coupled-frame comparison

This analysis replaces the current paired-plywood legs with the separately
modeled [straight-lumber variants](leg-stock-comparison.md). The frame and its
existing gusset releases remain unchanged. Native solve results will be recorded
after the preparation and output checks pass; preparation alone is not a result.

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
```

The runner refuses to overwrite existing evidence, preserves failed native
work in `fea/generated`, and records source identities, full prepared inputs,
decks, native outputs and case vectors. Passing numerical gates is not a member
strength, buckling, joint-resistance or unanchored-contact approval.
