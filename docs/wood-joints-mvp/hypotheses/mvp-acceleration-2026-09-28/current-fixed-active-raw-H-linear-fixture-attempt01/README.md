# Fixed-active raw-H linear fixture, attempt 01

This isolated numerical preflight tests the linear compatibility/equilibrium
solve for a declared fixed branch. It uses the original unsymmetrized operator
in

```text
q = D a + e - H_raw f
D.T f = W
```

Rows on the fixed branch use either `f_i = k_i q_i + offset` or
`q_i = held_reference`; an open or active lower-bound force row is prescribed
as `f_i = 0`. The producer assembles the resulting square system in
`[a, f_active]` and solves it with `scipy.linalg.solve(..., assume_a="gen")`.
It does not create an energy Hessian, symmetrize `H_raw`, regularize, or use a
pseudoinverse. A general LU solve is appropriate here because compatibility
equations need not be symmetric; this is a fixed-branch linear method, not a
nonsymmetric convex-QP or global contact-state claim.

The producer reads only the pinned tiny `known-answer.json` and
`fixed-mask-dual-qp.json` inputs. It reuses the existing tiny branch assembler,
direct KKT branch oracle, sign oracle, rank-stop oracle, and invalid-active-set
oracle. It deliberately does not call the previous fixture's `produce()` or
`--verify` path because that path also reads a saved frame-run diagnostic
candidate. No A12 frame array/operator, frame solve, or native solver is read
or run here.

The direct raw-operator system reproduces all 24 prescribed-mask branches and
their one-state, no-state, multiple-state, and zero-boundary classifications.
Maximum differences from the prior tiny branch values are `4.45e-16 mm` in
physical coordinates, `3.56e-15 N` in contact force, and `4.45e-16 mm` in
contact `q`. The existing nonzero-`H`/`e` sign answer remains `a=0.3 mm`,
`f=[0.5, 1.0] N`, `q=[0.5, 0.5] mm`. The rank-deficient equality/flat-mode
stops and invalid-active-set/sign stops are replayed unchanged.

The added known-answer case separates the raw and symmetric operators under
high spring stiffness. For `k=1e6 N/mm`, a deliberately nonsymmetric
`H_raw` and a load constructed from the known state give exact recovery of
`f=[1,2] N` with raw-H general LU. The symmetric operator solve is internally
accurate for its own equations but changes the force to approximately
`[1.1667,1.8333] N`; evaluated against the original raw-H law it leaves a
`0.3667 N` residual. This demonstrates why a small energy-KKT residual does
not by itself certify the original nonsymmetric source law when `H` has a
small skew component and stiffness is high. The constructed perturbation is a
method discriminator, not a bound on the A12 operator error or a diagnosis of
all frame force-interval misses.

The parent-reported A12 fixed-active attempt motivates this check: its KKT
residual was about `1.7e-17`, while the raw-law residual was `1.08e-4 N` and
25 nonzero force intervals missed. Those parent-run values are context only;
this fixture does not independently read or recompute them. The exact 734-row
estimate/mask and any actual A12 raw-H comparison remain parent-owned.

Replay the tiny method fixture with:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-fixed-active-raw-H-linear-fixture-attempt01/solve_raw.py \
  --verify
```

`--verify` checks the input, producer, and assessment SHA-256 pins, rebuilds
the tiny results in memory, and byte-compares the result. It does not write
files. The pinned assessment reports the executed known answers, versions,
residuals, and the explicit scope limits.
