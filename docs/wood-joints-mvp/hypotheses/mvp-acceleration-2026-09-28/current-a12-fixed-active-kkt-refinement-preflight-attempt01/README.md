# A12 fixed-active-set KKT refinement preflight, attempt 01

This packet prepares one direct unregularized refinement of the existing
full-load A12 conditional numerical response. It does not choose a new floor
mask or state, run a native solver, assemble the frame operator, or execute
the KKT solve. The CLI only verifies the exact source pins and the one
provisional bound-set estimate. A parent-owned frozen wrapper may call
`one_shot_refine()` after reviewing this code and accepting its own serialized
run conditions.

Attempt 02 solved its QP but failed 69 original force-token intervals and 30
projected-q intervals; its minimum unilateral force was
`-1.0458805373e-8 N`, just below the existing `-1e-8 N` sign gate. The 300
rigid-coordinate token intervals passed. Its physical/source failures remain
stops, and the saved forces were not adopted. The candidate has no inequality
dual array, so its active set is only a provisional numerical estimate.

The single declared estimate uses `abs(f_candidate) <= 1e-4 N` among the
1,192 **nonfloor** unilateral variables. It marks 734 rows as fixed at zero
and leaves 458 nonfloor unilateral rows free. In the pinned attempt-02
candidate, the largest absolute force among the 734 estimated bounds is
`4.84666e-8 N`; the smallest free force is `0.00363391 N`, 36.34 times the
declared threshold. Each estimated bound row has a native force center of
zero and a strictly negative native q interval; the least negative interval
upper endpoint is `-2.22668e-6 mm`. Each estimated free row has a strictly
positive native force interval; the smallest lower endpoint is
`0.00363382 N`. The selected 25 floor normals are excluded from this estimate
and remain free; their smallest saved force is `1.00736 N`. These margins
support one guess but do not authenticate it. No adjacent threshold or
alternate active-set search is allowed.

For that fixed guess, the direct system is

```text
minimize  1/2 f.T S f + c.T f
subject to D_active.T f = W_total
           f_i >= 0 for all 1,217 unilateral variables

K = [[S, E.T, G.T],
     [E,   0,   0 ],
     [G,   0,   0 ]],   E = D_active.T
K [f, lambda, mu] = [-c, W_total, 0]
a = -lambda
```

`G` selects the 734 estimated active lower bounds; its rows are exactly
`f_i=0`. The full KKT matrix is order 2,649 (1,615 variables, 300 equilibrium
equalities and 734 active rows). The proposed one-shot method computes its
singular values, stops unless the matrix is full rank at the recorded
`1e-12` relative cutoff, then calls the unregularized
`scipy.linalg.solve(..., assume_a="sym")`. It has no clipping, diagonal
regularization, pseudoinverse, least-squares fallback, active-set reselection
or threshold search. It stops on a solve warning/error, nonfinite output,
relative KKT residual above `2e-10`, active force error above `2e-9 N`, an
active multiplier not strictly below `-2e-9 mm`, or a free nonfloor
unilateral force at or below `1e-4 N`. The last two conditions expose a
wrong or boundary-ambiguous guess rather than changing it.

After a successful KKT solve, the code independently rebuilds full forces,
recovers all 300 coordinates with `a=-lambda`, and evaluates the exact
attempt-02 audits with the original `H_raw`, source stiffnesses, and native
token intervals. It preserves their `0.1 N` force-balance, `2 N mm`
moment-balance, `2e-8 mm` raw-H compatibility, `0.1 N` source-law,
`-1e-8 N` unilateral-sign, `10 mm` table-domain, strict floor, released-row,
and unchanged force/q/coordinate interval gates. Rotational equilibrium
residuals are multiplied by 1,000 before the moment comparison. It reports
physical checks and each DAT comparison separately. Any miss remains a stop;
the output is only reproduction of the old prescribed episode, never
mechanical acceptance or a new physical state.

The pinned repository environment used for the input replay is NumPy 2.5.2
and SciPy 1.18.1 with `OPENBLAS_NUM_THREADS=1`. Parent execution should keep
the declared 180-second wall/CPU and 6-GiB memory caps and one BLAS thread. The
attempt-02 parent runner is hash-pinned so its original gates can be compared
verbatim. The tested tiny direct-KKT fixture is also hash-pinned; that result
does not establish A12 conditioning or accuracy.

Verify only the frozen inputs and active-set proposal:

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-active-kkt-refinement-preflight-attempt01/prepare.py \
  --verify-inputs
```

This prints `PASS_A12_FIXED_ACTIVE_KKT_INPUTS` and assembles or solves no KKT
matrix. Source pins, exact row identities, and the proposal are in
[`readiness.json`](readiness.json). The helper's `one_shot_refine()` is an
unexecuted parent-callable function; this packet supplies no runner or lock.
