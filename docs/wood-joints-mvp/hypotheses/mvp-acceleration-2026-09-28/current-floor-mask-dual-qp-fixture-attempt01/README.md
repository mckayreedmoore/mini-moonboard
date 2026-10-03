# Prescribed floor-mask dual-QP fixture

## Bounded result

The convex force-space formulation reproduces the existing one- and two-cell
source branches when each floor mask is supplied. It recovers the exact
one-cell zero-force event ambiguity, a nonzero held-reference state, the
fixed-reference no-state and multiple-state examples, and all four two-cell
stage oracles. It also rejects all 15 prescribed masks that violate the
source branch laws. A separate hand-answer case checks the nonzero `H` and
`e` signs directly. This is a small mathematical fixture only; it does not
select any frame floor mask.

The pinned source branches classify as follows:

| Existing case | QP branch result |
| --- | --- |
| One-cell zero-force event | Open and closed masks both reproduce `u=(-2,0)`, `T=N=0`; ambiguous boundary |
| One-cell held reference `r=-2 mm` | Closed mask reproduces `u=(-2,0.25) mm`, `T=-0.25 N`, `N=0.5 N`; open mask rejected because its normal extension is positive |
| Fixed-reference counterexample | Neither mask is admissible |
| Mirrored fixed-reference example | Both masks are admissible |
| Four two-cell stages | Exactly the existing hand-answer mask is admissible in each |

All 24 prescribed source masks were replayed. Every solver call returned
OSQP `solved`; no inaccurate solver result was accepted. The 15 rejected
masks were rejected by the independently recomputed source displacement,
equilibrium, open-gap, held-reference, normal-spring and KKT checks, rather
than treating a failed solve as an invalid state.

The source-sign check is visible in the two-cell both-open stage: its normal
coordinates are `(-0.03,-0.02) mm` with both normal forces zero. At the
one-cell held bearing state, normal extension is `+0.25 mm` and normal force
is `+0.5 N`.

## Formulation and signs

For carrier forces `f`, prescribed free coordinates `a`, external extension
offset `e`, and symmetric compliance `H`, the fixture uses

```text
q = D*a + e - H*f
D.T*f = W
minimize  1/2*f.T*H*f + sum_i f_i^2/(2*k_i)
          - e.T*f + held_tangent_reference.T*f_t
```

For a QP equality multiplier `lambda` on `D.T*f=W`, set `a=-lambda`. With
OSQP's lower-bound dual `nu_i` on `f_i >= 0`, KKT stationarity gives

```text
free spring or held tangent: q_i = f_i/k_i + reference_i
unilateral spring at f_i=0: q_i - f_i/k_i = nu_i <= 0
unilateral spring at f_i>0: q_i = f_i/k_i > 0
```

For a held tangent, there is no finite tangent spring term (`1/k_t=0`), so
the reference term enforces `q_t = reference` while its multiplier stays
signed. For a prescribed open floor cell, its tangent and normal force
variables are omitted (therefore exactly zero); the recovered displacement
must independently satisfy `q_N <= 0`. A prescribed closed cell keeps its
normal force as a nonnegative QP variable and its tangent multiplier free.
The fixture checks `D.T*f=W`, original source equilibrium, KKT stationarity,
normal lower-bound dual sign/complementarity, and each prescribed branch law.

The direct sign oracle has `H=diag(0.1,0.1)`, nonzero `e`, and exact answer
`a=0.3`, `f=(0.5,1.0)`, `q=(0.5,0.5)`. It confirms that positive normal
extension corresponds to positive compressive force under the stated signs.
The source-derived event/stage fixtures use `H=0`; their SPD source matrices
are exactly factored as tiny bilateral spring banks `K=B.T*B`, with
`D_internal=B`, and source contact rows `D_contact=-diag(contact_basis)`.
This algebraic factorization preserves `K*u - diag(contact_basis)*f = W`
for the oracle comparisons. It is not an FE model or a proposed member
spring decomposition.

The QP Hessian is checked positive semidefinite before each solve. The replay
uses OSQP 1.0.4, NumPy 2.2.6 and SciPy 1.15.3 with pinned tolerances/settings
recorded in the JSON. Only status `solved` is accepted. OSQP documents that
`solved inaccurate` uses tolerances ten times larger than those configured;
that status is rejected here. The code also recomputes the KKT/source-law
residuals from the returned primal and equality/bound duals.

## Sources and replay

The fixture pins the established indicator-selector result and its exact
event, two-cell and parent counterexample sources. Its producer and all input
SHA-256 values are recorded in
[`fixed-mask-dual-qp.json`](fixed-mask-dual-qp.json). No source model or
fixture was edited. Official solver references used for the API, convex-QP
form, settings, residuals and status meanings are the [OSQP Python
interface](https://osqp.org/docs/interfaces/python.html), [solver
description](https://osqp.org/docs/solver/), [solver
settings](https://osqp.org/docs/interfaces/solver_settings.html), and
[status values](https://osqp.org/docs/interfaces/status_values.html).

From the repository root, replay with the pinned environment:

```sh
uv run --no-project --with osqp==1.0.4 --with numpy==2.2.6 --with scipy==1.15.3 \
  python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-mask-dual-qp-fixture-attempt01/solve_fixture.py --verify
```

The engineering implication is limited: after a floor episode mask and
held-tangent references are known, included unilateral spring forces can be
represented by convex nonnegative bounds rather than one binary indicator per
carrier. This fixture neither tests runtime nor proves conditioning,
uniqueness, or scalable behavior for the 1,192 nonfloor unilateral contacts.
No body factorization, current-frame operator, physical mask selection,
gravity path, native solve, panel work, or design conclusion is included.
