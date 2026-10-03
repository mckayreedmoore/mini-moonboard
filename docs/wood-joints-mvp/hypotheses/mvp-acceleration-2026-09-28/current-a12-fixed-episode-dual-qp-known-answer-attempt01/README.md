# Parent A12 prescribed-episode dual-QP known-answer run

This is one parent-owned reproduction test against the authenticated full-load
A12-rear conditional numerical response. The exact input episode is in the
[preparation packet](../current-a12-fixed-episode-dual-qp-preparation-attempt01/README.md).
It preserves the recorded 25 closed / 75 open floor cells, zero held tangent
references and combined proportional gravity/climber loads. It selects no
new floor state, supplies no new design demand, and accepts no joint.

The model uses the existing tiny prescribed-mask dual-QP formulation. It
minimizes `0.5*f.T*S*f + c.T*f`, requires raw `D_A.T*f=W`, and constrains
1,217 unilateral forces to be nonnegative. There are 1,615 force variables,
with the 225 released floor rows restored as exact zero after solving. Body
coordinates are the negative first 300 equality multipliers; the original
rigid-coordinate rotation scale is 1,000 mm. Moment residuals are therefore
multiplied by 1,000 to obtain N mm; their gate is **2 N mm**, not 2 N m.

The one-shot settings use OSQP 1.0.4, NumPy 2.2.6 and SciPy 1.15.3. Both
solver tolerances are `1e-10`, rho is fixed at `0.1`, sigma is `1e-6`,
polishing is enabled and warm starts are disabled. Scaling uses ten iterations,
the documented default; termination is checked every 25 iterations. The
solver stops at 45 seconds or 200,000 iterations, within parent 180-second
CPU/wall and 6 GiB caps. No settings are changed after an unsuccessful run.
The settings differ from the tiny fixture only in the declared numerical
scaling, termination interval and runtime cap; they do not change the
physical equations, references or mask. See official OSQP
[settings](https://osqp.org/docs/interfaces/solver_settings.html) and
[status definitions](https://osqp.org/docs/interfaces/status_values.html).
The installed pinned API is checked separately; the documentation does not
prove convergence or source reproduction for this problem.

Only status `solved` / status value 1 proceeds to audits. Inaccurate,
infeasible, iteration or time-limit statuses stop with no adopted forces.
The Hessian's numerical Cholesky factorization must succeed before setup.
After a solved result, independently recover all 1,840 source-row actions
and displacements using the original unsymmetrized H. Check:

- every body's force/moment balance against 0.1 N / 2 N mm;
- original spring laws against 0.1 N, unilateral force signs, and the unchanged
  unilateral table domain;
- raw versus symmetrized displacement compatibility against `2e-8 mm`;
- closed normals above `2e-8 mm` and `1e-8 N`, open normals below `-2e-8 mm`,
  held tangent displacements within `2e-8 mm`, and exact released forces zero;
- force, projected q and rigid-coordinate comparisons against the original
  DAT-derived rounding intervals, separately from all general gates.

The interval comparison adds only a declared floating-point operation guard,
`128*eps*(abs(value)+abs(center)+1)`, as in the source replay. It adds no
physical/model uncertainty. A failed source comparison stops the test even
when general physical residual gates pass. No token-bound widening, arbitrary
anchor, changed support mask or adoption of rejected screen forces is allowed.
The comparison of q recovered with Hsym against the raw-H prediction is
explicitly nonzero when skew matters; computing q_raw by its own definition
is not presented as an independent zero compatibility residual.

Source files, settings, versions and the runner are frozen before numerical
work. The shared execution lock and idle native ledger are required. Running
again in this attempt is refused. The result, when present, is
[assessment.json](assessment.json). A saved diagnostic candidate remains
unadopted even if the known-answer test passes. Source checks alone do not
establish uniqueness, gravity settlement, contact events or the other cases.

The parent command is:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-project \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-episode-dual-qp-known-answer-attempt01/parent_run.py
```

Do not execute until the preparation producer/output is stable and its replay
has passed parent inspection. This authorizes a numerical known-answer test
only; it launches no native solver and changes no reviewed geometry.
