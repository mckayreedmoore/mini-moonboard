# A12 fixed-episode dual-QP preparation, attempt 01

This packet prepares one known-answer input from the authenticated full-load
A12-rear native response. It does not solve a QP, launch a native run, select a
new floor mask, or accept the selected frame branch. The frozen response is a
conditional numerical response for a proposed diagnostic mask; its later
response and all-body audits pass, while the earlier mask-screen outputs
remain rejected. This preparation uses the native response force export, not
the rejected screen's force results.

The original conditional episode is fully specified in the frozen run:

- 25 selected floor cells have 50 held tangent rows, each at the recorded
  zero first-bearing reference; 75 cells are open with 150 released tangent
  rows. The model records `first_bearing_reference: zero`, and the reference
  DOFs are fixed to zero in the input deck.
- At the full-load increment (`lambda=1.0`), all 25 selected floor normals
  have strictly positive force and all 75 open normals are strictly
  separated. Across the seven recorded increments the same source mask is
  retained. No mask is inferred from a new calculation.
- Each of the 100 normal rows joins exactly two tangent rows using the pinned
  row-ID cell prefix; the producer checks the paired body and support point.
  The tangent axes are global `[0, 1, 0]` and `[-1, 0, 0]`; its force variable
  is the negative of the recovered physical tangent reaction in the source
  projection sign convention.
- The frozen native deck has one proportional `*CLOAD` step. Its full-load
  vectors are `e_total = e_gravity + e_climber` and
  `W_total = W_gravity + W_climber`. This is the authenticated combined-load
  response, not a gravity-settle/climber-ramp path.

`prepare.py` exposes `prepare()` and the `--write-inputs` /
`--verify-inputs` commands. It recovers the 1,840-row native force vector from
the response records, uses the pinned DAT parser and physical projection to
recover `q_native` and the 300 body coordinates, and writes
[`known-answer.npz`](known-answer.npz). The output includes only active QP
variables plus the full native force/displacement answer and row identities.
Its arrays include `S`, `D_active`, `linear_objective`, `W_total`,
`e_total_full`, active/nonnegative row positions, held/released and open/closed
row positions, row IDs/families, active stiffnesses, full native force
centers/radii, full projected-displacement centers/radii, and the 300 native
rigid-coordinate centers/radii plus the body-name column order. Exact keys
are listed in the producer's `arrays` dictionary. The separately pinned
`current-frame-connector-compliance-attempt04/operators.npz` remains the
authoritative raw `H`, full `D`, and source-column `e`/`W`; it is not duplicated
in this packet. `assessment.json` records its SHA-256 pin and the frozen replay
input inventory.

The authoritative row key is the integer position in the pinned 1,840-row
projection contract: textual `row_id` labels are not globally unique.
`body_names_rigid_column_order` maps each six-value block in `a` to the
authenticated body order. The assessment records Python, NumPy, SciPy, and
`OPENBLAS_NUM_THREADS`; replay with the documented repository environment and
one BLAS thread.

The fixed-mask convex dual QP is prepared as

```text
minimize    1/2 f_A.T S f_A + c_A.T f_A
subject to  D_A.T f_A = W_total
            f_A[i] >= 0 for active unilateral springs

S = Hsym[A,A] + diag(1/k_i for finite springs; 0 for held floor tangents)
c_A = -e_total[A] + r_A,       Hsym = (Hraw + Hraw.T)/2
```

The active set contains 348 bilateral rows, 1,217 unilateral rows (1,192
nonfloor plus 25 closed floor normals), and 50 signed held-tangent rows: 1,615
QP variables. The 75 open floor normals are omitted with exact zero force and
must retain `q_N < 0`; the 150 released tangent rows are omitted with exact
zero force and free displacement. Held tangent rows require `q_T = 0`. The
QP is a prescribed-episode known-answer check, not a floor-state selector.

`S` is formed explicitly from the pinned symmetric part of raw `H` and source
row stiffnesses. The preparation independently evaluates native compatibility
with the original unsymmetrized `Hraw` over all 1,840 rows, and records the
`Hraw`/`Hsym` displacement difference. The parent run must repeat this raw-H
check after solving. It must not substitute `S` or `Hsym` into the raw
compatibility audit.

When the parent QP uses equality `D_A.T*f_A=W_total` with solver multiplier
`lambda_QP`, recover the candidate body coordinates with `a=-lambda_QP` under
the displayed objective/equality sign convention. Check all 300 columns and
raw equilibrium independently. Rotational entries in `D.T*f-W` are
scaled-coordinate residuals; multiply them by `1000 mm` before applying the
physical `2 N mm` moment gate. The separate force gate is `0.1 N`.

The parent-owned run should accept only an exact `solved` status; `solved
inaccurate`, time/budget stops, infeasibility, or any missing row stops the
known-answer check. Report these gates separately:

- raw equilibrium and body force/moment residuals, using the declared
  general gates of `0.1 N` and `2 N mm` (rotational residuals are multiplied
  by `1000 mm` before the moment comparison);
- all-row raw-H compatibility and original source spring laws;
- closed-normal positivity, open-normal strict separation, zero held-reference
  displacement, and exact released-tangent zero force;
- comparison with the original DAT force/U rounding intervals propagated by
  the pinned replay. Do not widen those intervals if QP results fall outside;
  report this as a separate stop even if general residual gates pass.

The preparation records native token radii and DAT-propagated q/a bounds.
The reduction's separate KKT diagnostics are not physical uncertainty bounds.
No uniqueness, recontact, gravity ramp, or general frame acceptance follows
from this one fixed-episode comparison. If the QP encounters a gauge, boundary
or nonunique multiplier state, report it without adding an anchor or changing
the source mask.

Run the deterministic source extraction without a solver:

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-episode-dual-qp-preparation-attempt01/prepare.py \
  --verify-inputs
```

No solve/audit runner is included; the parent owns its frozen inputs, serialized
execution, and result gates.
