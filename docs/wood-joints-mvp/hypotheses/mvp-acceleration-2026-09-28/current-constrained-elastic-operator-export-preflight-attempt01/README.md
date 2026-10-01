# Constrained elastic-operator export preflight

Status: input-only proposal; not frozen and not run. This bounded coupon adds
one SPC, one permanent interpolation MPC, and one internal linear SPRING2 to
the already checked unit C3D20 material-oracle body. It tests the constrained
equation map before any current-frame export is considered. It does not test
the frame, gravity/contact continuation, state-dependent tangents, or joint
acceptance.

## Deck and expected map

`coupon-constrained-matrixstorage.inp` keeps the orthotropic material, rotated
37 degrees about global Z, and unit cube from the independent [elastic packet]
(../../elastic-matrix-export-method-2026-09-30/). The new elements use
the existing edge midpoint: node 9 is halfway between nodes 1 and 2. The deck
has these permanent relations before the final terminal frequency step:

```text
u(1,1) = 0
u(9,1) = 0.5 u(1,1) + 0.5 u(2,1)
```

The first equation is the single SPC; the second is the first-term-dependent
`*EQUATION` interpolation. The C3D20 interpolation satisfies the same relation
for every affine displacement field because node 9 is the geometric midpoint
of nodes 1 and 2. The SPRING2 connects node 9 direction 1 to node 2 direction
1 with `k = 100 N/mm`.

With `GLOBAL=YES`, no `*TRANSFORM`, and the source's active equation numbering,
`.dof` should contain the 58 independent coordinates: all 60 node translation DOFs
except constrained SPC `(1,1)` and dependent MPC `(9,1)`. The oracle constructs
`u = Bq + c` from those labels. The permanent zero-offset map has `B` rows
equal to identity for active coordinates, zero for the SPC, and coefficient
`0.5` at `(9,1)` for active master `(2,1)`. Master `(1,1)` is the SPC, so it
contributes only to the separate offset vector `c`.

The 2.23 source maps element matrices through SPC/MPC equation status and the
MPC coefficients before assembly. Thus the expected constrained operator is
`K_export = B^T K_physical B`, not a 60-DOF node-space matrix with deleted rows.
For the SPRING2, let `s = e_(2,1) - e_(9,1)`. Its full-space tangent is
`100 s s^T`; `B^T s` has only one nonzero entry, `+0.5` at equation `(2,1)`.
The expected projected spring tangent is therefore `25 N/mm` on that equation.

## Independent oracle and load-work probe

`constrained_matrix_export_oracle.py --check-results JOB.sti JOB.dof` rebuilds
the symmetric matrix and equation-label map from native output. For six
compatible affine strain fields on the unit cube, it compares
`Q^T K_export Q` against the rotated orthotropic continuum cross-energy matrix
from the independent packet, plus `25 N/mm` in the `xx` entry from the
SPRING2. It imports the pinned packet's `global_engineering_stiffness()` rather
than copying its engineering-constant rotation calculation. This checks the
reduced matrix against analytical energies without implementing an element
stiffness kernel.

The separate algebraic probe sets the SPC reference offset to `g=0.2 mm`, the
active value `q(2,1)=0.6 mm`, and a test load `F=8 N` at dependent coordinate
`(9,1)`. The expanded values are `u(1,1)=0.2`, `u(2,1)=0.6`, and
`u(9,1)=0.4 mm`. The spring extension is `0.2 mm`, its physical end-force
magnitude is `20 N`, and its projected generalized force at `(2,1)` is `10 N`.
The test load maps to `B^T f = 4 N` at `(2,1)`, while its physical work is
`f^T(Bq+c) = 3.2 N mm = (B^T f)^T q + f^T c`. These values are analytical
oracle probes, not a load vector read from `.sti`/`.dof`; MATRIXSTORAGE does not
export applied loads.

`c` and its nonzero reference values are kept outside the exported tangent.
The input SPC is zero. The pinned manual says frequency analysis resets SPC
values to zero, so a frequency export cannot be treated as a record of a
nonzero captured displacement or MPC offset. Any current-frame offset must be
provided separately and checked with the work identity above.

Run `uv run --no-sync python constrained_matrix_export_oracle.py --self-test`
for its pure algebraic projection/work checks. That self-test creates no FE
matrix and does not invoke CalculiX. A later native run requires a separate
parent-owned freeze and authorization; the parent runner must authenticate
native execution provenance independently.

## Pinned behavior and scope limits

The pinned CalculiX 2.23 manual is `fea/generated/ccx_2.23.pdf`, SHA-256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`. Relevant
sections are §6.2.41 `SPRING2` (pp. 128–129), §7.56 `*EQUATION` (pp. 504–505),
§7.63 `*FREQUENCY` (pp. 516–519), §7.103 `*ORIENTATION`, and §7.122 `*SPRING`
(pp. 598–599). `GLOBAL=YES`
supports SPC/MPC equations; the frequency procedure writes `.sti`, `.mas`,
and `.dof` and stops, so it remains the final step. The input's zero SPC is
permanent for the model and its MPC is not removed between steps.

Relevant 2.23 source paths, exact archive/member hashes, and line ranges are
recorded in `source-pins.json`. `mastruct.c` numbers active equations after
marking SPCs and MPC-dependent terms; `mafillsm.f` expands element-matrix
terms through MPC coefficients; `springstiff_n2f.f` forms the linear SPRING2
matrix; and `matrixstorage.c` writes the symmetric sparse operator and the
`node.direction` label for each active equation. `arpack.c` writes those files
and terminates before eigensolution for `SOLVER=MATRIXSTORAGE`.

The constrained native outcome remains unknown. In particular, the input
proposal has not demonstrated that the pinned executable accepts this exact
combined deck or that its emitted 58-equation operator meets the oracle. The
reference offset and applied-load vector are deliberately analytical metadata;
the exporter supplies neither. No result here selects gravity contacts or
the `q=0` right-side `SPRINGA` tangent, and no complete-frame rank or contact
claim follows from this coupon.
