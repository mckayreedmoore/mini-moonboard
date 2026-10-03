# Primal energy condensation fixture — attempt01

## Bounded result

For an exactly symmetric positive-definite carrier compliance `H`, the
generalized-force potential

```text
q = D*a + e - H*g
J = 1/2*g.T*H*g - W.T*a
    + bilateral sum(1/2*k*q^2)
    + unilateral sum(1/2*k*s^2),  s >= q, s >= 0
```

has KKT equations `g=f`, `D.T*g=W`, and the original compatibility relation.
The epigraph hinge gives ordinary unilateral springs `f=k*max(q,0)` without
contact binaries. A pinned one-DOF/two-carrier QP returns the exact known
answer `a=0.3`, `g=(0.5,1)`, `q=(0.5,0.5)` and zero stored-precision residuals
for compatibility, equilibrium, both spring laws, and epigraph stationarity.

The three pinned one-cell source examples reproduce their branch classes:

| Source toy | Replayed branch result | Key output |
| --- | --- | --- |
| Event at zero force | `AMBIGUOUS_ZERO_BOUNDARY_MASKS` | Both masks give `q=(-2,0) mm`, `g=(0,0) N`; both remain valid |
| Fixed-reference counterexample | `NO_ADMISSIBLE_STATE` | Open has positive normal extension `+0.005063291 mm`; constrained closed minimizer lands at `q_n=0` with extra normal multiplier `0.5 N` and `g_n=-0.5 N` |
| Mirrored fixed-reference load | `MULTIPLE_ADMISSIBLE_MASKS` | Open and closed masks both pass; closed gives `q=(0,0.0025) mm`, `g=(3.9875,0.25) N` |

The normal-bound multiplier is a key branch check. For an open floor branch,
the `q_n <= 0` constraint multiplier can supply an apparent reaction at
`q_n=0`, although the source open law requires `g_n=0`. For a closed branch,
the `q_n >= 0` multiplier shifts the source force to `g_n=k*q_n-mu`.
Therefore the multiplier must be zero before a constrained energy minimizer
can count as a source-law state. At a zero-force event, two masks may still
represent the same valid zero-force state; the fixture preserves that
ambiguity.

## KKT and applicability

With compatibility constraint `q-D*a-e+H*g=0`, use multiplier `lambda` and
define `f=-lambda`. Stationarity with respect to `a` gives `D.T*f=W`.
Stationarity with respect to `g` gives `H*g-H.T*f=0`, hence `g=f` when `H`
is symmetric. For an ordinary unilateral epigraph, multipliers `alpha,beta`
for `q-s<=0` and `-s<=0` satisfy `f=alpha`, `alpha+beta=k*s`; at `q=0`,
`s=0` forces both multipliers and the normal force to zero. A held tangent
constraint `q_t=r` contributes its signed equality multiplier as tangent
force. Open floor tangents still carry zero force; held floor tangents use the
prescribed reference.

This proves a conditional algebraic route to replace binaries for ordinary
unilateral springs while retaining the discrete coupled floor branches. The
toy branch solves condense the pinned two-coordinate source carriers to `H`
and `e`; they are not a frame operator or a frame solve. No actual body matrix
was factored or inverted, and no floor masks were selected for the frame.

The actual frame `H` is only numerically reciprocal. Using
`H_sym=(H+H.T)/2` in a later convex energy is a declared numerical
approximation: the resulting solution must be checked against the original
raw-`H` compatibility relation, source force balance, and every retained
branch law. This fixture does not establish conditioning, runtime, scale for
1,192 ordinary unilateral contacts, floor-history validity, contact
compatibility, or physical acceptance.

The result JSON pins the prior selector inputs, source fixture files and this
producer by SHA-256. OSQP 1.0.4, NumPy 2.2.6, and SciPy 1.15.3 are used in an
ephemeral environment. Only OSQP status `solved` is accepted. See the official
[OSQP Python interface](https://osqp.org/docs/interfaces/python.html),
[solver description](https://osqp.org/docs/solver/), [settings](https://osqp.org/docs/interfaces/solver_settings.html),
and [status values](https://osqp.org/docs/interfaces/status_values.html).

From the repository root, replay with:

```sh
uv run --no-project --with osqp==1.0.4 --with numpy==2.2.6 --with scipy==1.15.3 \
  python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-primal-energy-condensation-fixture-attempt01/verify_energy.py --verify
```

No native run, current-frame matrix inversion, frame MIQP, floor mask
selection, panel analysis, geometry change, or joint acceptance is included.
