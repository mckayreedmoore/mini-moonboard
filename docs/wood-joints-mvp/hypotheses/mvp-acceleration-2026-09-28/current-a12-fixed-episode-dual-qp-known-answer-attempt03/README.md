# A12 known-answer QP with absolute precision criterion

The [adaptive-rho run](../current-a12-fixed-episode-dual-qp-known-answer-attempt02/assessment.json)
reached OSQP status `solved` in 0.652 s / 1,250 iterations after documented residual
balancing replaced fixed rho. Its general body, law, raw-H, floor reference
and strict closed/open gates passed. It did not pass reproduction: 69 force
and 30 projected q comparisons exceeded their original DAT intervals, and one
unilateral force was −1.04588e-8 N against the declared −1e-8 N numerical sign
gate. It remains rejected and no candidate forces are adopted.

The reported dual residual was 8.20485e-9, despite eps_abs 1e-10, because OSQP's
relative stopping term also scales with its problem vectors. The official
[convergence equations](https://osqp.org/docs/solver/index.html) define these
absolute-plus-relative limits. This attempt makes one bounded precision
change: eps_abs=1e-11 and eps_rel=0, requiring absolute residual convergence.
The source comparisons, physical sign/force/moment gates and all floor
conditions stay unchanged. No force is clipped or reclassified to pass.

Everything else reuses [attempt02](../current-a12-fixed-episode-dual-qp-known-answer-attempt02/README.md):
the same source NPZ, equations, mask, references, adaptive-rho interval 50,
45-second solver/180-second parent cap, settings stack and no warm start.
No additional iteration/time budget, anchor, load change or source-interval
widening is introduced. Source and candidate comparison failures are still
separate from solver status. If this sharper criterion cannot reproduce the
source, record the failed rows and numerical dependency rather than starting
an open-ended tolerance/settings campaign.

The same `verify_settings.py` producer must pass the unchanged tiny force,
multiplier and all prescribed-mask oracles with the new settings before root
executes `parent_run.py`. The freeze binds both preceding result assessments,
this test and all original source evidence. Shared-lock and one-shot controls
are unchanged. A passing reproduction would validate only the fixed episode;
this is no gravity-settle/ramp, new floor-state selection or joint acceptance.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-project \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-episode-dual-qp-known-answer-attempt03/verify_settings.py
```

After that passes, root may use the same command with `parent_run.py`.
