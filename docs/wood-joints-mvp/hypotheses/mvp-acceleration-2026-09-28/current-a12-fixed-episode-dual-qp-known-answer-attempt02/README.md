# A12 known-answer QP with documented residual balancing

The preceding [fixed-rho run](../current-a12-fixed-episode-dual-qp-known-answer-attempt01/assessment.json)
stopped at its 45-second budget after 109,470 iterations. Its primal residual
was 1.1731e-8 while its dual residual remained 0.0098318. It did not reach
`solved`, produce a candidate force file or pass a source comparison. This
result motivates one specific numerical change, not a physical input change
or a larger budget.

This attempt preserves the exact equations, prepared source arrays, floor
mask, references, 45-second solver / 180-second parent caps, tolerances and
all [original audit gates](../current-a12-fixed-episode-dual-qp-known-answer-attempt01/README.md).
The numerical change is `adaptive_rho=True` with an explicit update interval
of 50 iterations. Initial rho remains 0.1. The official
[OSQP algorithm documentation](https://osqp.org/docs/solver/index.html)
describes residual balancing as its convergence method, and its
[settings documentation](https://osqp.org/docs/interfaces/solver_settings.html)
identifies adaptive rho as enabled by default. The fixed iteration interval
avoids the default runtime-derived update interval. These are algorithmic
choices only; they do not change geometry, loads, support restraints or source
precision. No guarantee of convergence follows.

`verify_settings.py` uses the same pinned prescribed-mask tiny QP producer
with this attempt's declared settings. Its expected force/multiplier and
source-branch oracles must pass before the one-shot parent run. It writes
`numerical-settings-fixture.json` separately; no frozen method source or
old output is changed. The parent freezes that replay evidence, the previous
STOP assessment and all original inputs before the solve. Only status exactly
`solved` proceeds; inaccurate or budget statuses stop. A converged candidate
must still pass every physical/source/DAT gate without bound widening.

Commands, with one BLAS/OMP thread and the pinned NumPy 2.2.6, SciPy 1.15.3,
OSQP 1.0.4 environment:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-project \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-episode-dual-qp-known-answer-attempt02/verify_settings.py
```

After the tiny checks pass and inputs are ready, root alone may invoke the
same command with `parent_run.py`. Shared execution lock, idle native ledger,
one-shot freeze and unchanged-source audit are retained. No native solve,
floor-state selection, new design demand or joint acceptance is authorized
by a passing numerical fixture or known-answer reproduction.
