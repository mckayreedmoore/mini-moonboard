# Fixed-active-set KKT refinement fixture, attempt 01

This packet tests an unregularized direct KKT solve on the existing tiny
prescribed-mask dual-QP cases. It does not load `H` or `D` for A12, assemble
an A12 KKT matrix, run a frame solve, launch CalculiX, or change a source
attempt. The result is a numerical-method preflight only.

The A12 input is the historical full-load conditional numerical response
with its recorded zero held-tangent references. Reproducing that fixed
episode does not select or accept a fixed-zero forward state. A future
forward contact analysis still requires the full gravity-settle then climber
ramp, captured event references, coupled state selection, and explicit
no-state, multiple-state, and cycle stops.

Run 01 stopped at its 45-second OSQP time limit after 109,470 iterations
(45.302 s wall, 45.002 s solver), with primal residual `1.17308e-8` and dual
residual `0.00983182`. It produced no candidate. Run 02 solved in 0.6521 s
after 1,250 iterations, with primal residual `4.84666e-8` and dual residual
`8.20485e-9`, but did not pass the required source comparisons. Its minimum
unilateral force was `-1.0458805373e-8 N`, below the unchanged `-1e-8 N` sign
gate. It missed 69 force DAT intervals (maximum difference
`1.0813165e-3 N`, maximum ratio `205.686`) and 30 projected-q intervals
(maximum difference `1.073041e-6 mm`, maximum ratio `39.2148`). All rigid
coordinate intervals passed. The raw-H, body balance, source-law and floor
gates passed; the unilateral nonnegative gate failed. No candidate forces
were adopted.

Run 02 reported `status_polish=-1`. The official OSQP API maps that value to
unsuccessful polishing. OSQP describes polishing as an active-constraint guess
followed by a linear solve; when its guess fails, the solver returns its ADMM
iterate. This is consistent with the saved result being unrefined, but the
status does not identify the cause of the failed guess or prove the A12 KKT
system is nonsingular. See the official [OSQP polishing description](https://osqp.org/docs/solver/)
and [polish status values](https://osqp.org/docs/interfaces/C.html).

Attempt 03 tightened the OSQP criterion to `eps_abs=1e-11`, `eps_rel=0` while
keeping the equations, source arrays, floor mask and caps unchanged. Its tiny
settings preflight reportedly reached maximum iterations; the attempt
directory contains no `assessment.json`, and no frame run occurred. The
reported stop is retained as parent handoff provenance in
`refinement-fixture.json` rather than represented as a local solver output.

For a chosen active lower-bound set `A`, the direct refinement solves

```text
minimize  1/2 x.T P x + c.T x
subject to E x = b,  x[i] >= 0 for declared unilateral rows

KKT(A) = [[P, E.T, I_A.T],
          [E,   0,     0 ],
          [I_A, 0,     0 ]]
KKT(A) [x, lambda, mu] = [-c, b, 0]
```

The active rows impose `x[i]=0`; with this row sign convention their
multipliers must satisfy `mu[i] <= 0`. The physical coordinates use
`a=-lambda`, matching the existing `D.T*f=W` formulation. The code checks the
KKT matrix rank using a relative singular-value cutoff of `1e-12`, then calls
`scipy.linalg.solve(..., assume_a="sym")`. It uses no pseudoinverse,
least-squares fallback, diagonal regularization, force clipping, or tolerance
change. SciPy documents that `solve` raises on singular systems and warns on
ill-conditioned ones; both conditions stop this method.
See [SciPy `linalg.solve`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve.html).

The fixture enumerates active lower-bound subsets for the 24 masks already
recorded in the eight tiny source cases. Every direct result matches the
existing tiny branch output and expected no-state, one-state, multiple-state,
or zero-boundary classification. The existing nonempty-`D`, nonzero-`H`/`e`
sign oracle also returns `f=[0.5, 1.0]`, `a=[0.3]`, and `q=[0.5, 0.5]`. The
rank-stop oracles reject dependent equality rows and an unconstrained flat
mode. Invalid active-set oracles reject an out-of-domain bound index and a
wrong active guess whose multiplier has the wrong sign. Across the tiny
source systems, the smallest observed KKT singular-value ratio is about
`1.53e-3`, above the fixed cutoff.

This shows that direct KKT refinement can reproduce these tiny exact
solutions when the active set is correct and the KKT matrix is nonsingular.
It does not show that the A12 active set can be inferred correctly or that its
KKT matrix has acceptable conditioning or runtime. The saved Run 02 candidate
contains force, coordinate, q and body-wrench arrays, but no inequality-dual
array. Any A12 active set would therefore be a numerical estimate from that
candidate, not an authenticated solver active set. A parent-owned refinement
would have to preserve the exact 25/75 floor mask and rerun every existing raw
`H`, force/moment, spring law, nonnegative sign, strict floor, released-row
and original DAT interval gate. Failure, rank deficiency, uncertain active
set, or any original-gate mismatch remains STOP. This fixture is not a global
selector, frame readiness result, or license to relax the DAT intervals.

Reproduce only this tiny numerical fixture with the repository environment:

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-fixed-active-kkt-refinement-fixture-attempt01/refine.py \
  --verify
```

`--verify` rebuilds the tiny expected result in memory, checks the frozen
source/result pins, and byte-compares it with `refinement-fixture.json`; it
does not write files or invoke a solver. `--write` is reserved for an
intentional regeneration after review.

The producer and result pin the prior tiny source inputs and the read-only
Run 01/02 outputs. No previous attempt is edited.
