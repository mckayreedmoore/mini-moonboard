# Free bolt/washer contact control

Preparation in progress. This tests numerical contact, not a bolt product,
plywood joint capacity or permission to build/climb.

The selected station-1 hardware comes from the actual locked-thread stitch
variant: one fused bolt/head/nut solid and one separate inner annular washer.
The eleven-body mesh completed in 7.05 seconds, with 131,695 nodes and 62,987
C3D10 elements. The two control bodies contain 19,769 nodes and 10,218 elements.
The original fourteen-body evidence remains unchanged. No mesh nodes are
merged across independent bodies. Local coordinates subtract the stitch's
global starting point; this does not move one body relative to the other.

The washer is the slave in both ordinary surface-to-surface penalty pairs:
its cylindrical bore against the exposed shank, and its head-facing annulus
against the head underside. Their nominal radial and axial clearances are zero.
There are no restraints, ties, mortar, gravity, preload, friction or applied
forces. In particular, no artificial pinning is used to suppress free-body
motion. Perfectly fused nut/core retention is a numerical idealization, not a
model of real threads or tightening.

## Frozen proposed numerical settings

| Setting | Value |
| --- | --- |
| Generic elastic steel E / Poisson ratio | 210,000 N/mm² / 0.3 |
| Assumed density | 7.85e−9 tonne/mm³ |
| Linear contact penalty | 100,000 N/mm³ |
| Quiescent initial velocities | Zero for both bodies |
| Moving washer velocity; core velocity | (−100, 100, 0) mm/s; zero |
| Procedure | NLGEOM, implicit DYNAMIC, ALPHA=0; omit EXPLICIT |
| Initial / maximum / minimum increment | 1e−8 / 1e−7 / 1e−11 seconds |
| Initial diagnostic duration | 2e−6 seconds |

These are diagnostic assumptions, not measured material properties. The washer
mass and 183.2133 mm² head bearing area imply an approximate penalty-contact
timescale of 6e−7 seconds; even the selected maximum increment requires a later
refinement check. Initial velocity supplies the moving case's kinetic energy;
there is no load amplitude and no subsequent external work.

## Predeclared interpretation gates

Let `m` be the source-reconstructed native four-point washer mass, with
`P* = m sqrt(100² + 100²)`, `E* = m (100² + 100²)/2`, and `H* = 57.15 P*`.
Record this reference mass and its provenance; do not substitute a fitted scale
after seeing the response. Moments are compared about the fixed initial washer
centre, local (1, 0, 0) mm.

- Quiescent: maximum nodal displacement ≤1e−6 mm; speed ≤0.01 mm/s;
  kinetic/strain/contact energy magnitude sum ≤1e−4 E*; each pair's cumulative
  impulse magnitude ≤1e−4 P*; maximum penetration ≤1e−6 mm.
- Moving: each body's contact-impulse residual ≤1e−3 P* and angular-impulse
  residual ≤1e−3 H*; assembly momentum drift ≤1e−4 of the respective scale;
  total energy drift ≤1% E*. Native mass/kinetic-energy reconstruction retains
  the established 5e−6 comparison limit, with zero-energy comparisons requiring
  an explicitly stated absolute normalization.
- Require each pair's impulse ≥1e−3 P* and core kinetic energy ≥1e−4 E*;
  otherwise the short event is inconclusive, not a successful transfer test.
- Only after the first moving case qualifies, halve its maximum increment;
  endpoint momentum and pair impulse changes must be ≤1% P*.

Every accepted state must have complete nodal and requested contact output.
Trapezoidal impulse integration and its timestep sensitivity must be explicit;
endpoint force times elapsed duration is not an impulse audit. The native pair
`CF` resultants cover washer force and moment because the washer is slave in
both pairs. Do not substitute reported static `RF` for dynamic body balance.
Opposite core force and assembly angular-momentum checks must be verified, not
inferred as proof merely from equal-and-opposite resultants.

`printoutcontact.f` in the retained upstream 2.21 source constructs pair force
and moment about the origin from current slave integration-point positions.
Its empty-contact statistics divide by zero area: primary force/moment may be
zero while ancillary centroid statistics are nonfinite. Any parser exception
for that case must require verified zero area and zero primary resultants;
nonfinite primary forces are never accepted. Contact pressure/sign conventions
must be checked against the actual emitted fields.

The quiescent case must qualify before the moving case is launched. Independently
meshed nominally zero-clearance cylinders can create apparent penetration and
artificial energy. A failed gate stops escalation and remains archived. Solver
completion by itself is not output qualification; none of these controls
releases the complete eleven-body stitch experiment or validates the board.
