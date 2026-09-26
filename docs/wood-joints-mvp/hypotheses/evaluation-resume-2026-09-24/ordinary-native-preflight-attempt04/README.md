# Current ordinary joint: native reference-tangent preflight

The parent ran this zero-load case with the pinned CalculiX 2.21 executable.
It completed in 38.126 seconds and exported 334,908 equations and 13,520,701
coordinate records per stiffness/mass matrix. It uses the current three-timber,
four-bolt ordinary joint. This is not a loaded response, accepted stiffness,
strength result, or fabrication release.

The [matrix witness](../ordinary-matrix-witness-attempt01/audit.json) tests a
unit translation of all 9,369 bottom-center cleat nodes along local N, with
every other body and control zero in the probe vector. The maximum nodal
residual is 2.578e-6 N for this 1 mm displacement probe. Its scaled residual
is 1.375e-12, below the declared 1e-8 numerical threshold. A normalized
affine-strain comparison has positive quadratic form. This supports one
specific free-motion direction at the reference tangent; it does not establish
total nullity or every contact's active state or zero pressure. The initial
force-controlled stiffness sweep remains stopped pending a separately bounded
clearance-seating response.

The [mass audit](../ordinary-native-mass-audit-attempt02/audit.json) checks two
free timber translations and four bolt-plus-rigid-nut translations against
frozen integrated volumes and declared densities. All six agree within 2.2e-9
relative error. The bolt-plus-nut checks agree with bolt-only mass, confirming
that the boreless nut display volumes add no artificial mass. These are
assembled scenario masses, not measurements of delivered materials.

The [input freeze](input-freeze.json) and [execution record](execution.json)
bind the unchanged 57,643-element C3D10 mesh, transverse-material scenario A,
35 frictionless compression-only contact pairs, a remote six-scalar gauge,
and assumed six-DOF stiff nut engagement. Timber density is nominally
600 kg/m³; deformable metal density is 7,850 kg/m³. Four rigid seat carriers
have zero density and no nut-bore contact. Actual thread fit, nut compliance,
preload, and delivered material properties remain unresolved.

The [gauge](../ordinary-gauge-parent-attempt01/gauge.json) uses nodes 33824,
43470 and 33822, outside every emitted contact and load patch. The literal
contract corners overlapped contact surfaces, so this is an explicitly revised
remote triad. Source-local T is 2415.403793 mm; global T projection is
2600.924134 mm because the source frame has an offset origin.

The step is `*STEP,PERTURBATION` and `*FREQUENCY,SOLVER=MATRIXSTORAGE`.
The pinned 2.21 source initializes reference-state contact in this first-step
path and exports matrices without an inverse eigensolve. A plain frequency
step without perturbation would omit contact initialization. The independent
source audit used the official 2.21 source archive with SHA-256
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`.
The executable hash is recorded in execution.json and was checked before launch.

Attempt 01 rejected duplicate input headings. Attempt 02 rejected nut equation
coefficients wider than the native reader's 20-character fields. Attempt 03
parsed but exhausted its 10 GiB container limit after 120 seconds; its
[Docker events](../ordinary-native-preflight-attempt03/docker-events.jsonl)
confirm the out-of-memory termination. These attempts are preserved.

The [independently reviewed pivot change](../ordinary-nut-coupling-pivot-attempt01/independent-review.md)
eliminates six shaft DOFs per nut instead of the six nut controls. It preserves
the complete equality row space and original fit while avoiding expansion of
the dense fit into every rigid seat node. No support, stiffness, fit sample,
or physical restraint was added. Attempt 04 completed under the same memory cap.

The frozen pivot report used here has one stale ancillary `artifacts` hash;
its direct `include_file_sha256` and native input agree. The
[corrected report](../ordinary-nut-coupling-pivot-attempt02/nut-coupling.json)
fixes that metadata with identical native card bytes. No native rerun is needed
for that metadata correction.

Raw `.sti`, `.mas`, and `.dof` files are local outputs bound by execution.json.
Their publication packaging remains separate from the completed preflight.
