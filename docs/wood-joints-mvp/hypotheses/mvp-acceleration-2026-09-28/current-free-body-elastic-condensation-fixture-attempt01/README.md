# Free-body elastic condensation known-answer fixture

This fixture checks a small condensation method against the authenticated free
C3D20 stiffness export. It reuses the completed CalculiX 2.23 run in
[`current-free-c3d20-matrix-export-native-attempt01`](../current-free-c3d20-matrix-export-native-attempt01/).
The fixture starts by replaying that attempt's frozen sources, execution record,
output hashes, and analytical matrix assessment. It does not run CalculiX or
change the upstream packet.

The cube has side 1 mm, volume 1 mm³, `E = 1 N/mm²`, and `nu = 0.25`. Six
rigid modes are built from translations and rotations about the cube centroid.
If `Q` is an orthonormal basis perpendicular to those modes, the elastic
inverse is

```text
K+ = Q (Qᵀ K Q)⁻¹ Qᵀ
```

This gives the minimum-gauge elastic response only for equilibrated loads. The
fixture checks `RᵀF` before using the inverse. For a body with source rows
selected by `B`, `F` denotes other loads applied to the body and `f` denotes
the force exerted by the body on the connected interface. The force on the
body is therefore `-Bᵀf`, and its source-row displacement is

```text
q = B R a + B K+ (F - Bᵀ f)
```

The body must satisfy `Rᵀ(F - Bᵀf) = 0` in all six rigid modes. The connected
global problem must enforce those six equilibrium equations. The rigid-mode
gauge only chooses a displacement representative; it cannot supply a support
reaction.

For the known answer, the fixture applies uniform analytic traction
`sigma n` to all six cube faces for six independent constant-strain fields.
Each quadratic face uses consistent shape-function integrals of `-1/12` for
each corner and `+1/3` for each edge midpoint, times the 1 mm² face area. These
loads come from continuum stress and face integration, never from `K u`. The
resulting nodal loads have zero net force and moment. Their inverse responses
match the centered affine displacement fields after removing rigid motion,
and all 36 cross-work terms match `volume * epsilon_i : sigma_j`.

The two-row illustration selects DOFs `1.1` and `2.1`. Its equal-and-opposite
source forces are self-equilibrated, and the reported 2×2 projected compliance
is symmetric and positive. Each individual row force is unbalanced; its wrench
is reported, and that row cannot be treated as an independently admissible
free-body load. A separate `+1 N` point load at node `1`, X returns the wrench
`[1, 0, 0 N; 0, -0.5, 0.5 N·mm]`. The fixture rejects it before applying
`K+`; the balancing wrench remains explicit and is not labeled as a physical
support or hidden in a gauge multiplier.

Reproduce and replay the saved result from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-free-body-elastic-condensation-fixture-attempt01/verify_condensation.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-free-body-elastic-condensation-fixture-attempt01/verify_condensation.py --verify
```

The detailed checks and upstream freeze, execution, matrix, and map hashes are
in [`assessment.json`](assessment.json). The native evidence is limited to one
free isotropic C3D20 cube. The source-row demonstration is two rows only; it
does not assemble a frame controller or the 50-body system, check current-frame
gravity/contact, or establish joint acceptance, construction readiness, or a
climbing release.
