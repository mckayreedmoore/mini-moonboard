# Implicit current-map one-axis fixture design

Status: offline prepared; not frozen and not run natively. Parent owns any
readiness decision, freeze, execution, and interpretation.

This fixture isolates the actual six-equation current-map representation on a
single positive-mass A00 bolt-head-plus-shaft body. Three decks separate the
representations: `direct` has the physical body alone; `mapped_no_carrier`
adds the six current-map equations and their free REF/ROT controls; and
`mapped_carrier` adds the source-defined zero-density M03 nut carrier as a
rigid body attached to those same controls. Every case applies the same
physical nodal load vector. The carrier adds no contact, force, mass, or joint
interaction.

The source body is `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` (5,490 C3D10 elements,
11,348 physical nodes). The current map is the first six A00 equations in the
pinned `nut-coupling.inp`: six dependent DOFs, 754 terms per equation, all six
REF/ROT controls referenced, and no boundary conditions. REF and ROT both use
the native A00 pivot `(134.5, 1.178456090256, 410.856889078727) mm`. The
mapped-carrier deck adds the pinned `M03_A00_NUT` mesh (519 C3D10 elements,
1,107 nodes), its original rigid-node NSET, and its original RIGID BODY card.
The full sorted node-ID lists and per-case DAT/FRD membership are in
`expected.json`.

The M00 material uses `E=200000 MPa`, `nu=0.3`, and
`rho=7.85e-9 tonne/mm^3`. M03 keeps the same elastic constants and zero
density. No element, material, map, body identity, or source coordinate value
is selected by this fixture beyond those pinned records.

The 4-point C3D10 integration uses the coordinates and shape functions from
the pinned solver source and the literal `gauss3d5` points and weight
`0.041666666666667` from `gauss.f`. It independently forms the consistent
mass action for a one-axis angular acceleration about global Y,
`f(T) = M * (alpha_y(T) * (e_y cross (x_reference - p)))`. The acceleration
law is `alpha_y(t)=1.2*t rad/s^2`; a linear step-time amplitude scales the
final-time `M*a` physical CLOAD vector from zero to one over `0.01 s`.
The vector has 22,696 nonzero physical component rows (11,348 each in DOF 1
and 3, zero in DOF 2). It is computed from the full consistent C3D10 mass
quadrature, not a lumped nodal mass or an MPC-transformed shortcut. Its
intended full-precision hash and the hash of the values actually read by the
20-character native CLOAD fields are recorded separately in `expected.json`.
Formatting introduces at most `4.95e-14` relative component error; the
resultant drift is below `3.4e-21 N` and moment drift below `2.0e-18 N mm`.

Input width follows the pinned readers: `cloads.f`, `equations.f`, and
`nodes.f` consume 20-character numeric fields. The original map rows are
byte-preserved and checked field-by-field. Eight source coordinate literals
are longer than 20 characters; the decks keep each exact first-20-character
prefix, which is the value the original `nodes.f` reader consumed, and discard
only the ignored suffix. The largest difference between each full source
literal and that parser-visible coordinate is `6.94e-18 mm`. Every generated
comma field is checked to fit its parser width, preventing exponent truncation.

All cases use `*DYNAMIC,DIRECT,ALPHA=0`, `NLGEOM`, fixed `dt=0.001 s`,
`T=0.01 s`, and ten intended increments. No restraint, damping, stabilization,
contact, or mass/stiffness scaling is added. DAT `NODE PRINT` and FRD
`NODE FILE` request U,V at frequency one for all M00 physical nodes. The two
mapped cases also request both controls; controls are unmeshed, so they are
expected in DAT and omitted from FRD. The mapped-carrier case requests U,V for
all M03 nodes as well. `EL PRINT` separately requests ELSE, ELKE, EMAS, and
EVOL totals for M00 in each case and for M03 in mapped-carrier. M03's
quadrature volume reference is `741.7892075330269 mm^3`; its density, mass,
kinetic energy, and elastic energy references are zero. These are output
reference values, not a preselected acceptance gate.

The prospective rigid-mode Newmark reference uses average acceleration
(`beta=1/4`, `gamma=1/2`): `omega_y=c*t^2/2`,
`theta_y=c*(t^3/6+t*dt^2/12)`, and `U=theta_y*(e_y cross (x-p))`,
`V=omega_y*(e_y cross (x-p))`. At the end state this gives
`theta_y=2.01e-7 rad` and `omega_y=6.0e-5 rad/s`. The source's RIGID control
coordinates use a total axis-angle rotation vector, so the Y component is the
small rotation angle. This linearized rigid-mode curve helps assess the
physical-node fields and the six REF/ROT outputs; it does not bound elastic
body, finite-rotation, or solver errors. In mapped-carrier, displacement under
the total axis-angle rotation from measured controls is a separate kinematic
check. The pinned `dynresults.f` dependent-velocity reconstruction and
`nonlinmpc.f` Rodrigues derivatives support using `dR/dw * w_dot * (x-p)`
plus REF velocity for carrier velocity. With a fixed single Y axis this reduces
to `omega_y * e_y cross R_y(theta_y)*(x-p)`. For a changing measured axis, use
the full rotation-vector derivative; do not treat `w_dot` as spatial angular
velocity without that transformation. This source convention is established;
native agreement remains to be tested by this fixture.

The output-size estimate is based on the pinned earlier 10-node, 100-state
DAT/FRD artifacts listed by path and hash in `expected.json`, then scaled by
the actual expected node groups and ten states. Largest requested groups are
12,457 nodes in DAT and 12,455 in FRD. The resulting nodal-row estimates are
about 12.96 MB DAT and 12.21 MB FRD, before roughly 1.4 MiB of mesh and solver
records. A 64 MiB per-case capture cap is therefore a provisional proposal;
parent runner memory, time, and capture limits remain authoritative.

The packet is a small method diagnostic only. It does not represent a
complete joint, contact, bolt preload, thread behavior, capacity, or physical
product. No native execution has been performed by this producer, and no
acceptance tolerances are assigned here.
