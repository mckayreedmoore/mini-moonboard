# Explicit raw-equilibrium strengthening fixture, attempt 01

This isolated fixture adds a signed `g` variable to the frozen tiny
floor-binary convex-energy adapter, imposes `y = L.T*g`, and adds raw
`D.T*g = W` as explicit linear source-equilibrium rows. It does not use
stationarity with respect to `g` as a substitute for those rows. The pinned
compatibility equation and independent raw-H, spring-law, and floor-law audits
remain unchanged.

The fixture solves each of the existing 24 prescribed floor masks separately
and compares its polished admissible masks and classification with the frozen
adapter result. It does not compare energy across masks or claim a global
physical winner or uniqueness. Those 24 fixtures have zero generalized rigid
coordinates, so their explicit equilibrium row set is empty; a separate
two-carrier oracle exercises nonempty equilibrium and reproduces the known
`a`, `g`, and `q` answer.

Two exact algebraic toys check the gauge cases. A full-D null direction with
zero raw work remains feasible and flat after adding equilibrium; perturbing
work along that direction makes the exact equality infeasible. A separate
open-floor-tangent toy has `D_energy*v = 0`, `D*v != 0`, and `W.T*v = 1`.
Equilibrium alone admits an open witness with `g_T = 1`, while the unchanged
open source law requires `g_T = 0`; adding that law makes the branch
infeasible. A closed-held-reference control passes the same source audits.
Thus raw equilibrium does not replace the released-tangent law.
In the release ray, `a` and its parameter `t` are in mm, `W.T*v` is a
generalized force in N, and the objective change is `-t*(W.T*v)` in N·mm.

The report pins the frozen adapter and the corrected A12 root-relaxation
diagnosis. It uses only tiny analytic matrices and the pinned PySCIPOpt 6.2.0 /
SCIP 10.0.2, NumPy 2.5.2, OSQP 1.0.4, and SciPy 1.18.1 stack. It loads no frame
operator, performs no frame solve or native run, and makes no claim that the
constraint improves the actual selector's root bound.

From the repository root, replay with:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-project \
  --with pyscipopt==6.2.0 --with numpy==2.5.2 \
  --with osqp==1.0.4 --with scipy==1.18.1 \
  python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-energy-equilibrium-strengthening-fixture-attempt01/verify_equilibrium.py --verify
```

The machine-readable known-answer results and source pins are in
[assessment.json](assessment.json).
