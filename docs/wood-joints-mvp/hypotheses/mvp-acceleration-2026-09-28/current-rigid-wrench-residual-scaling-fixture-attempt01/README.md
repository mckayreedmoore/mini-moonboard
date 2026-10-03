# Rigid-wrench residual scaling fixture, attempt 01

This isolated mathematical fixture checks how the unchanged nodal KKT force
residual gate propagates through the rigid basis. For
`r = K u + R lambda - p`, each generalized coordinate obeys
`|(R.T r)_j| <= sum_i |R[i,j]| * ||r||∞`. Therefore the per-coordinate
numerical allowance is `sum_i |R[i,j]| * 1e-10 * max(1 N, ||p||∞)` when the
nodal residual gate is `1e-10` relative. The equivalent matrix norm is
`||R.T||∞ = max_j sum_i |R[i,j]|`.

From the repository root, run
`.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-rigid-wrench-residual-scaling-fixture-attempt01/verify_scaling.py`
to write the record, then append `--verify` to replay
[assessment.json](assessment.json). The fixture replays the authenticated free
C3D20 operator and six independent analytic face-traction columns. Its
constructed residual reaches 90% of the induced bound: the unchanged nodal
gate passes, the propagated aggregate gate passes, and the previous fixed
`2e-10 N` aggregate-only gate still reports `FAIL`. It separately checks the
contraction-order difference, an elastic force corruption, and a rigid gauge
corruption.

The rigid basis uses the existing 1000 mm rotational coordinate scale. Nodal
residuals and the six scaled generalized residual coordinates are in N;
multiply the three rotational coordinates by 1000 mm to report physical
moments in N mm. The top-equation sign remains `K u + R lambda - p`.

This fixture does not factor an actual frame body or compute `H`. The nodal
force tolerance, gauge tolerance, all 300 raw `D.T @ f = W` coordinates, and
physical `0.1 N` / `2 N mm` checks remain separate and unchanged. It establishes
the numerical scaling relation on the known-answer cube only; it does not
establish a current-frame response or mechanical acceptance.
