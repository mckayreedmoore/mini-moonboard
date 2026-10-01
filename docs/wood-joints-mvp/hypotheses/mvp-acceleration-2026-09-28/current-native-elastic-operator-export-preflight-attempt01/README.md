# Native elastic operator export preflight

Status: source-supported input proposal only. This attempt is not frozen and
has not been run. It does not establish a full-frame rank, gravity/contact
continuation, or joint result.

## Proposed export path

Use a dedicated `*FREQUENCY,SOLVER=MATRIXSTORAGE` step as the last step in a
small export job. CalculiX assembles its frequency-procedure matrices and emits
`job.sti`, `job.mas`, and `job.dof`, then stops. The `.sti` and `.mas` files
contain one-based row, column, value records for sparse entries; some emitted
values may be zero, and unlisted entries are zero. The matching line in
`.dof` maps each equation index to `node.direction`. The source writes the
diagonal plus one triangular half of each symmetric sparse matrix. The parser
mirrors off-diagonal entries when reconstructing a dense symmetric matrix and
rejects duplicate coordinate pairs.

In the pinned 2.23 manual, PDF pages 517–518 describe these three files, the
terminal stop, `GLOBAL=YES` with MPCs, `GLOBAL=NO` without SPCs/MPCs, and the
zeroing of SPC values at the beginning of a frequency calculation. The local
PDF SHA256 is recorded in `source-pins.json`. The exact 2.23 source archive
confirms that `SOLVER=MATRIXSTORAGE` selects `isolver=6`; the frequency parser
does not read an eigenvalue-count data line for this choice. The ARPACK path
calls the matrix writer and stops before its eigenvalue iteration. The build
still needs the `ARPACK` and `MATRIXSTORAGE` compile features. The target pinned
binary has not been run with this option yet.

The export is an assembled frequency-procedure operator in CalculiX's active
equation coordinates. It is not an element-by-element matrix dump and it is
not automatically a full unconstrained node-space matrix. With the default
`GLOBAL=YES`, SPC/MPC handling is allowed; SPC rows and MPC-dependent DOFs are
handled by the active equation mapping, and `.dof` labels the exported
equation rows. Preserve the exact permanent constraints and map when using a
constrained export. If an unconstrained full node-space operator is required,
export a model with no SPCs or MPCs and apply those constraints separately.
`GLOBAL=NO` uses local directions and the 2.23 writer rejects SPCs/MPCs in
that transformed-coordinate path.

The export writes stiffness and mass matrices, not the applied load vector.
Gravity, concentrated loads, and other right-hand-side terms must be assembled
or derived separately in the same equation map. A uniform acceleration load
can be formed as `M*g` when the exported mass, density, units, and directions
match the intended model; that load mapping still needs its own check. Any
nonzero imposed-reference offset must also be kept separately: frequency
analysis sets SPC values to zero for the perturbation calculation.

For a baseline elastic operator used by the later continuation, retain the
permanent MPCs and numerical linear grounds that belong to that operator.
Leave state-dependent `SPRINGA` contact tangents and the conditional floor
stick contribution out of this baseline. A frequency export assembles the
state represented by its input/base model; it does not choose gravity contact
states or run an external active-set controller. The `q=0` right-side normal
tangent and any contact history remain outside this export proposal.

## Small known-answer input

`coupon-free-c3d20-matrixstorage.inp` is one free, unit-side C3D20 with positive
linear elastic material and nonzero density. It has 60 unconstrained equations,
six rigid-body modes, and no contact, loads, SPCs, MPCs, restart, or frame.
Because MATRIXSTORAGE stops before eigenvalue iteration, the six rigid modes
do not require CalculiX to solve a singular eigenproblem. The separate oracle
script uses NumPy only to parse the native matrices and check their invariants;
it does not implement finite elements or run a solver.

For `E=1 N/mm^2`, `nu=0.25`, side `1 mm`, and simple shear
`u_x=gamma*y`, `gamma=0.01`, the analytical elastic energy is
`0.5 * (E/(2*(1+nu))) * gamma^2 * V = 2.0e-5 N*mm`. With density `1` in the
same consistent unit system, the mass quadratic form for unit translation in
one direction is `rho*V = 1`. These checks verify matrix indexing and scaling;
the six rigid modes and energy are still unobserved until the parent authorizes
a later bounded native run.

## Scope boundary

This attempt proposes an engine-backed elastic assembly route instead of a
custom C3D20 stiffness implementation. It does not select the floor active
set, supply the controller, validate constrained equation expansion, verify
gravity load mapping for the frame, establish contact tangents at `q=0`, or
qualify any complete-frame result. The free-body coupon also does not verify
SPC/MPC projection; source behavior is recorded, while a constrained mapping
coupon remains a separate future gate if needed.
