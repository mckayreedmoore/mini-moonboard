# Transformed floor reaction known-answer fixture

This is a small, unfrozen input fixture for checking the nonidentity
row/pivot transformation used by the current exact-floor adapter. It has two
physical x-z points, two source floor-stick rows, two independent load cases,
and compression-only normal springs. It does not model a frame or joint.

The source tangential constraint matrix uses original row order and physical
column order `[A, B]`:

```text
A = [[3/4, 1/4],
     [1/4, 3/4]]
```

The physical points lie at `y=[0,100] mm`; the source floor points lie at
`y=[25,75] mm` and use the unit-X tangent. Each row is ordinary linear
interpolation. Its row sum is one, and the interpolation transfers the first
moment in Y exactly. Thus source reactions and their `Mz=-y*Fx` resultant can
be compared with the equivalent generalized forces at A and B.

The fixture reverses the source rows and physical pivot columns:
`selected_rows=[1,0]`, `pivots=[B,A]`. In selected-row order,

```text
A_selected = [[1/4, 3/4],
              [3/4, 1/4]]
S = A_selected[:, [B,A]] = [[3/4, 1/4],
                            [1/4, 3/4]]
S^-1 = [[3/2, -1/2],
        [-1/2, 3/2]]
H = S^-1 A_selected = [[0,1],
                       [1,0]]  # columns remain in [A,B] order
```

The generated equations are therefore `u_Bx - 1.5*r1 + 0.5*r0 = 0` and
`u_Ax + 0.5*r1 - 1.5*r0 = 0`. Each source reference node is fixed in original
source-row order; the physical B and A x DOFs are unique dependent pivots.
Every unused projection, anchor, and physical DOF is fixed or explicitly
constrained.

For each physical point, isolated spring projections realize the known
structural matrix `[[20,5],[5,100]] N/mm`: a spring of `20 N/mm` on
`s=x+0.25*z`, plus `98.75 N/mm` on `z`. The normal coordinate is `q=-z`; the
100 mm `SPRINGA` has force law `100*max(q,0) N` and a 100 N/mm right-hand
tangent at zero. Both prescribed cases close on the positive-compression
branch. Real-valued spring data include explicit decimal points for the pinned
2.23 parser.

## Reaction map and hand answers

For pivot loads ordered `[B,A]`, the source correction in selected equation
order is

```text
correction_selected = (S^-1)^T * F_pivot
```

The assessor writes each selected correction back to original source row
`selected_rows[j]`, then evaluates
`R_source[i] = RF(reference_i,1) - correction_original[i]`. This convention
comes from the fixed normalized equation coefficients and the pinned
`*NODE PRINT,RF` external-force output; it is not selected by fitting the
hand answers. The assessor also checks the raw reference output against the
independently calculated transformed structural force, before the known
pivot-load correction is applied.

The per-body spring force components below are endpoint internal outputs. The
physical support vector is `A^T * R_source = g_x - F_x`; vertical balance is
`F_z - g_z + N = 0` for each body.

| Step | Loads `(A_x,A_z; B_x,B_z)` N | Displacements `(A_z,B_z)` mm | Raw reference RF `(r0,r1)` N | Source correction `(r0,r1)` N | Floor reactions `(r0,r1)` N | Equivalent body X support `(A,B)` N | Source/body `Mz` N·mm |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `(6,-20; -4,-40)` | `(-0.1,-0.2)` | `(-0.25,-1.25)` | `(11,-9)` | `(-11.25,7.75)` | `(-6.5,3)` | `-300` |
| 2 | `(-3,-30; 5,-10)` | `(-0.15,-0.05)` | `(-1,0)` | `(-7,9)` | `(6,-9)` | `(2.25,-5.25)` | `525` |

These answers are derived with exact rational arithmetic in `prepare.py` and
stored in `model.json`. The assessor requires the same fixed transform and row
mapping to reproduce both cases, close both physical bodies, reproduce the
source-point force resultant, and preserve the source/physical yaw moment.
Any output-order or force-transfer discrepancy stops assessment.

The model uses `*STEP,NLGEOM,NLGEOM=NO,INC=40` in each step. The pinned 2.23
manual documents `SPRINGA` in §6.2.42, equations in §7.56, `SPRING` in §7.122,
and `NODE PRINT` in §7.99. The pinned source archive's `steps.f` sequentially
parses the combined step option as Newton iterations on and geometric effects
off; `ident.f` selects the right table interval at a zero knot. Parent review
and any native run must still check the frozen deck and stdout evidence.

The parent owns readiness review, input freeze, and any native execution. This
packet contains no freeze and no solver output. It establishes no floor
friction, support capacity, floor history, compatibility for a larger set of
constraints, frame response, complete-joint behavior, or design acceptance.


## Observed native result

The single parent-frozen/approved stock 2.23 launch returned zero in
0.3402 s. `assess.py` reports
`PASS_NATIVE_TRANSFORMED_FLOOR_REACTION_KNOWN_ANSWER`. Both predicted
source-row reactions, both physical body balances and source/physical yaw
moments pass. The force map subtracts the transformed source CLOAD and
restores the original row permutation; it does not fit residuals.

Parent independently checked all twelve printed increments in
`parent_check.py`: maximum RF and body residual 5e-6 N; source/physical and
global yaw residual <=5.69e-13 Nmm. Frozen input digest is
`5e1ebad5da91caa904ed9534bc7869400d06dbf4acdf0091458bde7221765438`.
Numerical SPRINGA grounds remain excluded as extra physical supports.
This method result supplies no frame forces, support qualification, complete
corner acceptance or new frame launch authority.
