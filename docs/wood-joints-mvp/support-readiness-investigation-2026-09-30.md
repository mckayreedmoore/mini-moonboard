# Gravity-start readiness investigation — September 30, 2026

Docker access is available. The present support blocker is compatible initial
gravity equilibrium and a state-dependent gauge. The reviewed native mapping
coupons are complete. They prescribe contact events; the full-frame driver
still needs to discover the coupled states and events. This investigation
reads the existing model and rank audit without altering either or launching
a native solve. The FEA coordinator retains implementation adoption, frozen
inputs, serialized execution and final mechanics validation.

## What prevents a simple startup

The [current rigid-body readiness audit](hypotheses/mvp-acceleration-2026-09-28/current-frame-gravity-rank-readiness-attempt01/README.md)
maps 50 bodies into 300 rigid coordinates. At its declared `1e-10` rank
cutoff, the bilateral-only, all-contact-open branch has nullity 80, including
six common rigid modes and 74 relative-body mechanisms. Six gauge constraints
cannot remove those relative mechanisms. Conversely, its optimistic branch
with every unilateral normal active has three remaining common modes. Neither
branch selects the actual gravity state: the normal laws have zero force at
zero extension and different one-sided tangents.

The [passing ten-stage native coupon](hypotheses/mvp-acceleration-2026-09-28/current-floor-staged-reference-native-attempt01/README.md)
validates the recorded capture/release/re-engagement mapping. Its prescribed
events do not locate frame events or prove compatibility of 100 floor cells.
The gravity-start audit also does not assemble the orientation-aware C3D20
elastic tangent. These are separate missing requirements; passing one does
not close the others.

## Parent's independent numerical cross-check

I reconstructed each rigid spring row directly from its source physical
receiver, application point and scalar direction. For outer-seat ties, the
two distinct seat points were retained. For fixed-floor receivers, the floor
displacement was zero. This reconstruction was compared to the existing
MPC-expanded rows after verifying the audit's 15 source/context pins. No
spring stiffness, coordinate, law, load or stored source result was changed.

The maximum row-coefficient difference was `3.8979930394589246e-13`.
The source model SHA-256 was
`61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8`;
the rank-audit script SHA-256 was
`8034554eaee03b9884bbc9cd9f6a6da51392beac2182d38339a787dfb30c2d90`.
Using the audit's same row/column normalization and cutoff sweep, the
physical-owner all-normal envelope retained rank 297/nullity 3 at all four
cutoffs (`1e-8`, `1e-10`, `1e-12`, `1e-14`). The source-MPC envelope instead
reported rank 300 at `1e-14`. Thus the tightest cutoff can count tiny mapping
residuals as restraints and erase the expected common null modes. It is not
evidence of a physically fully restrained open-tangent frame.

The independently reconstructed bilateral-only branch still has rank
220/nullity 80 at `1e-8` and `1e-10`. Its tighter-cutoff ranks also vary.
This confirms that the practical startup concern is not cured by changing a
numerical cutoff. This is an independent kinematic cross-check, not a new
elastic-rank certificate, gravity solution or accepted gauge.

I also checked the source mesh connectivity: all 50 body inventories are
connected through element adjacencies sharing at least three non-collinear
nodes. All 1,903 physical elements are C3D20. The source coordinates are not
uniformly affine bricks, however; the largest discrepancy from a corner-based
affine 20-node reconstruction is 16.7048 mm. Therefore a regular-cube check
cannot by itself certify every current element's geometry or elastic rank.
This screen does not establish positive Jacobians at integration points,
finished-CAD agreement or complete-frame stiffness.

## Source-backed elastic-operator route

Section 7.63 of the [official CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf)
describes `*FREQUENCY,SOLVER=MATRIXSTORAGE,GLOBAL=YES`: it exports sparse
stiffness and mass triplets with a node/DOF map, then stops. The pinned local
manual's SHA-256 is
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.
This is a possible way to obtain the solid elastic operator from the existing
solver, rather than implementing another C3D20 element kernel.

I inspected the installed image read-only. Its ID matches the existing
[2.23 profile](hypotheses/evaluation-resume-2026-09-24/calculix-2.23-upgrade-attempt01/solver-profile.json).
The upstream `arpack.c` and `matrixstorage.c` hashes match that build's
manifest, and its recorded Makefile enables `MATRIXSTORAGE`. In the source's
global output branch, diagonals are written once and only one symmetric
off-diagonal triangle is emitted. A reader must reconstruct symmetry without
doubling diagonals and must use the emitted DOF map.

The bounded implementation task is an input-only method packet with one free,
rotated orthotropic C3D20 unit cube and an independent affine-energy oracle.
The native exit gate is six rigid modes, positive non-rigid stiffness,
correct DOF mapping and agreement with the known affine strain energies and
cross energies. Preparing or passing synthetic reader tests is not that
native gate. The existing FEA coordinator owns adoption, exact freeze,
serialized native execution and final validation of this proposal.

The [method packet](hypotheses/elastic-matrix-export-method-2026-09-30/README.md)
is now implemented and independently reviewed. Parent reproduced its tests:
15 invalid parser fixtures and three corrupted operators are rejected, while
the algebraic 60-DOF oracle passes all six affine modes. Independent tensor
rotation agrees within `2.3e-13`. Review corrected a native connectivity-line
error and documentation provenance; the generator now preserves the required
16-plus-5 entry split. These are code and proposal checks. The native cube
gate remains pending, with no full-frame case or strength acceptance gained.

If that gate passes, a separately frozen pure-solid export could preserve
the current frame's exact physical geometry, orientations and material
definitions, supplying its elastic matrix while keeping source carrier-law
and floor-state assembly explicit. This is a proposed implementation route,
not proof of native export behavior, source-equation reduction, a compatible
gravity state or accepted frame response. Do not infer a unilateral tangent
at zero extension from a frequency export of nonlinear springs.

## Concrete implementation consequence

The next support implementation must resolve the gravity branch and its
normal signs together, then demonstrate the nullspace and reaction-free
gauge of that actual state. It must preserve the existing gravity nodal
forces and first moments, the source unilateral laws and all-body/global
balance checks. Any relative mechanism in the actual branch stops readiness;
it cannot be removed as a common-coordinate gauge.

Once the gravity branch is established, the driver must localize opening
and re-engagement events, release tangents at opening, and capture their
measured reference coordinates at bearing events. No-state, incompatible
multiple-state, cycle and exhausted-budget outcomes remain explicit stops.
The [mapping preflight](hypotheses/mvp-acceleration-2026-09-28/current-staged-floor-native-mapping-preflight-attempt01/README.md)
already records these requirements; another prescribed-event coupon would
not by itself implement them.

Disposition: the investigation identifies a startup and rank-interpretation
issue. It authorizes no extra floor restraint, revised geometry or native
launch, and adds no blanket external sign-off or physical floor test. Usable
conditional responses remain the three rear cases; complete joint acceptance
and the full six-case requirement remain open.
