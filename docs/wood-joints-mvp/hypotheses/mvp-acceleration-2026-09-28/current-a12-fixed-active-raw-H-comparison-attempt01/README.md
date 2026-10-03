# A12 raw-H fixed-branch comparison, attempt 01

This packet prepares one parent-owned comparison against the same full-load
A12 episode, exact source inputs, 734 estimated nonfloor unilateral bound
rows, and original attempt01 force, projected-`q`, coordinate, equilibrium,
spring-law and floor gates. It changes only the operator used in the fixed
branch equations: the bordered row block uses `H_raw_active` instead of the
symmetric energy block. It does not change the load, `D`, `e`, inverse
stiffness, floor mask, active rows, thresholds, or source intervals.

For the source equations

```text
q = D*a + e - H_raw*f
D.T*f = W
```

free spring rows satisfy `f_i/k_i = q_i`; the 50 conditional held-tangent
rows have `k_i=0` in the stored compliance convention and retain their
existing zero reference; 734 selected lower-bound rows have `f_i=0`. With
`lambda=-a`, the single bordered linear system is

```text
[[ H_raw_active + diag(1/k),  D_active,  G.T ],
 [ D_active.T,                0,          0   ],
 [ G,                         0,          0   ]] * [f, lambda, mu]
    = [e_active, W_total, 0]
```

The original inverse-stiffness row scaling is retained exactly (`1/k` for
positive stiffness and zero for the 50 held tangents). `G` selects the exact
734 fixed rows in the preflight's local order. At a bound row, the first block
equation gives `mu=q_raw` because `f=0`; the multiplier is therefore reported
alongside the raw gap. These are multipliers of the fixed linear border, not
energy-QP multipliers for a nonsymmetric objective. The matrix is checked at
the unchanged `1e-12` singular-value cutoff and passed once to
`scipy.linalg.solve(..., assume_a="gen")`. A warning, rank failure, residual
failure, or source/physical gate miss stops the attempt. There is no retry,
regularization, factorization fallback, mask change or threshold search.

The tiny known-answer raw-H fixture passed before this packet was prepared. A
noncontiguous synthetic-bound assembly check verifies the exact `G.T`/`G`
border placement without constructing the A12 bordered matrix. Readiness also
checks that the prior source matrix equals `sym(H_raw_active)+diag(1/k)` to
`1.2e-17`, that the saved objective right-hand side remains exactly
`-e_active`, that held references remain zero, and that active row positions
match the pinned 1840-row identity inventory. Textual row labels can repeat,
so source position, group, and element remain attached to each recorded row.

`prepare_raw.py --verify-ready` is read-only with respect to the packet and
does not assemble the actual bordered matrix, factor, or solve. Its pins
preserve the entire source map from parent attempt01 and add the current raw-H
tiny oracle. The exact parent execution entry is:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-active-raw-H-comparison-attempt01/parent_run.py \
  --parent-one-shot
```

That entry is not executed in this preparation. If the parent chooses to run
it, it rechecks all pins, requires an idle shared run ledger, freezes sources,
and applies the prior 180 s wall/CPU, 6 GiB memory and one-thread caps. It
writes the full `f_active`, `a`, `lambda`, 734 `mu`, full 1840-row force and
raw/symmetric `q` vectors to `response.npz`. `assessment.json` records the
unchanged physical/source gates and every force, projected-`q`, or coordinate
DAT interval failure with its source position/identity, center, radius,
roundoff guard, difference and ratio. The parent attempt01 failure summary
is retained as a comparison baseline; its complete vectors were not saved.

The only purpose of the parent run is to see whether the raw-H fixed branch
reproduces the original source intervals that the symmetric attempt missed.
It does not select a staged contact state, establish that the 734-row estimate
is correct beyond its existing gates, or constitute a physical response,
acceptance, or design release. A failure remains a stop.
