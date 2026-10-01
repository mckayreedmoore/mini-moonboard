# Shared-edge penalty contact with full-cap motion: numeric-format correction

Status: **static preparation complete; parent review and freeze pending**.
This separate packet corrects only numeric serialization after
[attempt01](../contact-penalty-shared-edge-motion-known-answer-attempt01/RESULTS.md)
failed native input reading. Its geometry, equations, loads, analytical values
and tolerances are unchanged. `lexical-audit.json` checks exact numeric-value
equality and the pinned 20-character floating-field limit.
No native solver was run for this packet. The fixture is a method check, not a
current-joint analysis or acceptance result.

## Question and scope

This fixture combines two ingredients that were qualified separately: a
penalty contact law with shared-edge contact roles, and six-component
work-dual motion maps on a full quadratic cap. It runs two role patterns over
the same three 2 mm cubes:

| Case | Pair 1 | Pair 2 |
| --- | --- | --- |
| `shared_slave_motion` | `Z_CENTRAL` slave / `Z_LOWER` master | `X_CENTRAL` slave / `X_LEFT` master |
| `cross_role_motion` | `Z_CENTRAL` slave / `Z_LOWER` master | `X_LEFT` slave / `X_CENTRAL` master |

The central body meets the lower body on the 4 mm² z-plane and the left body
on the 4 mm² x-plane. Both interfaces have matching quadratic triangle meshes.
The contact law remains frictionless linear pressure-overclosure with
`K=100000 N/mm³`; all three bodies retain `E=100000 N/mm²`, `nu=0`, the prior
remote-plane supports and the single out-of-plane gauge. The flat interface
geometry, pair-role patterns and affine endpoint come from the frozen penalty
shared-edge fixture. The mesh alone is refined to 2×2×2 cells per cube, with
the same six-tetrahedron Freudenthal split per cell, yielding 144 C3D10
elements total.

The coarse fixture's three admissible off-contact carrier nodes per cap lie
on a line. Their 6×9 work-dual projection submatrices have exact rank 5, with
rotation about the carrier line unobservable. `expected.json` records the
coarse matrices and candidate DOFs. The single authorized regular refinement
provides enough off-contact, off-other-cap midside nodes for six independent
physical pivots per port. Each cap's six dependent physical DOFs avoid every
contact, support and gauge node; the two dependent sets are disjoint and no
dependent DOF appears in the other cap's equations. The contact nodes remain
independent terms in the maps. No support or oracle was added or changed to
obtain rank.

For each port, the serialized map implements
`q = (Aᵀ W A)⁻¹ Aᵀ W u`, with the exact face centroid, integrated quadratic
shape-function weights, and translation/rotation coordinates. `prepare.py`
re-parses the generated `*EQUATION` cards and checks the affine field residual,
the projection identities, arbitrary-state q reconstruction and virtual
work. The exact pressure dual is checked against the consistent quadratic
face traction vector. The two prescribed endpoint vectors are:

| Port | Centroid | `(tx, ty, tz, rx, ry, rz)` |
| --- | --- | --- |
| `PORT_TOP` | `(1,1,2) mm` | `(-4e-5, 0, -5e-5, 0, 0, 0)` |
| `PORT_RIGHT` | `(2,1,1) mm` | `(-5e-5, 0, -4e-5, 0, 0, 0)` |

The independent physical-node oracle remains the original affine field. Its
central body is `Ux=-3e-5-1e-5*x`, `Uy=0`, `Uz=-3e-5-1e-5*z`; the lower body's
only motion is `Uz=-1e-5*(z+2)` and the left body's is `Ux=-1e-5*(x+2)`.
The expected force is 4 N per interface. Series compliance is
`(2 mm/E + 2 mm/E + 1/K) = 5e-5 mm³/N`, approach is `5e-5 mm`, and penalty overclosure
is `1e-5 mm`.

## Pair output and energy oracle

At the compressed endpoint, the pinned 2.23 `printoutcontact.f` contract
prints CF/CFN/CFS resultants by exact slave/master pair. CFN is a summed force
vector, not an integrated positive pressure magnitude. The expected
tension-positive projection along the printed mean normal is `-4 N` for each
compressed pair. Frictionless loading gives zero CFS. The force and origin
moment oracles below use `r × F` and are explicit in `expected.json`:

| Slave pair surface | Resultant point (mm) | CFN force (N) | CFN moment about origin (Nmm) |
| --- | --- | --- | --- |
| `Z_CENTRAL` | `(1,1,0)` | `(0,0,4)` | `(4,-4,0)` |
| `X_CENTRAL` | `(0,1,1)` | `(4,0,0)` | `(0,4,-4)` |
| `X_LEFT` | `(0,1,1)` | `(-4,0,0)` | `(0,-4,4)` |

The per-pair force gate is `0.041 N = 0.01×4 N + 0.001 N`. The pair moment
gate is `0.041 Nmm = 0.01×4 N×1 mm reference length + 0.001 Nmm`; this keeps
the moment tolerance dimensionally explicit. These gates are inherited from
the frozen shared-edge force fixture. The normal-compliance, profile, force
closure and energy tolerances are unchanged from the frozen penalty and
penalty-energy known-answer packets; no result-dependent tuning is allowed.

The analytic body strain-energy totals are `CENTRAL=8e-5 Nmm`,
`LOWER=4e-5 Nmm`, and `LEFT=4e-5 Nmm`. The penalty contact energy is
`CELS=4e-5 Nmm`, giving `ELSE+CELS=2e-4 Nmm`. Their unchanged gate is
`|observed-reference| <= 0.01×reference + 1e-6 Nmm`. This validates only the
multi-pair endpoint energy channels. It is not external work, does not
validate trapezoidal path quadrature across open-gap closure, and does not
establish a current-joint global energy-defect limit.

Requested outputs include physical-node U/RF in DAT and FRD for every body,
the twelve scalar controller-node U values in DAT, both cap section wrenches,
pair CF/CFN/CFS, CDIS/CSTR, per-body ELSE totals, global CELS, and a complete
accepted-state trace. The verifier reconstructs each six-component cap q from
physical-node U and checks it against the controller DAT values. It does not
require controller FRD rows.

The pinned 2.23 source review corrected two output requests before freeze.
`noelfiles.f` assigns a shared U-field set selector, so a second `NODE FILE`
card for `PORT_CONTROLS` would replace the physical-node U selection; the
single `ALL_PHYSICAL_NODES` request now carries both U and RF, while controller
U remains a separate DAT print. The pinned `printoutface.f` SOF path integrates
extrapolated nodal stress, so `EL FILE S` is requested for the full physical
mesh. The verifier requires finite SOF force and origin-moment reports and
complete physical-node fields. These are output-only changes; the full motion
maps, contact definitions, supports, geometry, and numerical gates are
unchanged. `prefreeze-amendment.md` records the prior deck hashes and exact
output-only diff. The parent runner owns the freeze and serialized native
execution. The static preflight does not establish solver convergence or an
accepted state.

## Applicability limits and source pins

This flat, orthogonal, homogeneous coupon can check shared-slave and
slave/master role interactions under prescribed full-cap motion. It does not
qualify MORTAR, curved bore pressure, cancellation-free local pressure, the
first local bearing point, current-joint onset, current-joint motion-map
applicability, structural resistance, or any adopted criterion. A resolved
nonzero pair resultant can witness some bearing; a zero resultant cannot
establish no bearing. On the current joint, onset still needs the separately
frozen pair-local bore output, a verified near-zero threshold, complete
accepted-state coverage and two accepted states after the first resolved
nonzero bore-pair resultant.

The provenance record binds the pinned CalculiX 2.23 manual
(`fea/generated/ccx_2.23.pdf`), upstream source archive and relevant source
members, base image and unmodified executable, as well as the frozen penalty
and energy source artifacts. The exact hashes are recorded in
`source-snapshot.json`. Source pins support the input/output contract only;
the producer, readiness record and parent review remain separate hashes.

`prepare.py --check` is a read-only regeneration check. Default generation is
exclusive and refuses to overwrite any existing generated packet artifact.
`prefreeze-amendment.md` records the preparation audit changes and both
authorized pre-freeze regenerations. This directory contains no freeze, native
output, solver result, or joint acceptance.
