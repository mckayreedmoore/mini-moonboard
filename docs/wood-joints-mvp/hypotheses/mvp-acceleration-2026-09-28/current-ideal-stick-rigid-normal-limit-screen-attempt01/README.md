# Rigid unilateral normal limit screen for ideal floor stick

This exact-rational screen asks whether replacing the existing one-sided
penalty normal with an ideal rigid unilateral normal resolves the one-cell
release/recontact fixture. It does not change the selected source physics,
loads, criteria, or six-case evidence. It has no native deck and launched no
solve.

The source toy has coordinates `(t1,t2,q)`, stiffness
`K=[[2,0,1],[0,1,0],[1,0,2]] N/mm`, load `(-4,0,-1) N`, and normal spring
`n=k max(q,0)` with `k=2 N/mm`. Equilibrium signs are
`K u + (lambda1,lambda2,n) = f`; positive `q` means compression. Exact
tangential stick imposes `t1=t2=0` only on the active branch. The rigid
scenario uses `q=0,n>=0` when active, and `q<0,n=0` when open.

For the original load, the rigid active solution is `u=(0,0,0)` with tangent
multipliers `(-4,0)` and normal multiplier `n=-1 N`, so it requires tensile
normal support and is inadmissible. The rigid open solution is
`u=(-7/3,0,2/3) mm`, `n=0`; its positive `q=2/3 mm` contradicts the open gap.
The rigid normal constraint therefore supplies no state for this toy's
penalty/stick cycle.

The penalty released-mask branch for the same load has, for general `k`,
`q=2/(2k+3)`, `n=2k/(2k+3)`, and `t1=-2-1/(2k+3)`. As `k` tends to infinity,
`q` tends to `0+`, `n` tends to `1 N`, and `t1` tends to `-2 mm`. The positive
limiting normal reaction would activate the exact no-slip row, but the limit
still has nonzero tangential displacement. Normal stiffening alone does not
resolve the coupled gate. The other fixed mask has `q=-1/2 mm`, `n=0` and is
also inconsistent with its selected stick rows.

Two nearby test loads separate ordinary contact closure from a zero-reaction
boundary convention. With test-only `f=(-4,0,1) N`, the finite penalty active
branch at `k=2` is `q=1/4 mm`, `n=1/2 N`, and `lambda1=-17/4 N`; as `k` tends
to infinity it approaches the rigid active branch `q=0`, `n=1 N`,
`lambda1=-4 N`. This is a valid fixed-branch stiffness-limit sensitivity when
normal reaction stays positive.

With test-only `f=(-4,0,0) N`, the finite penalty strict-positive gate has no
consistent branch: its active branch has `q=0`, which is not strictly
positive, while its released branch has `q=4/7 mm` and `n=8/7 N`. The rigid
scenario as posed with an inclusive `n>=0` active condition does have an
active state `u=(0,0,0)`, `n=0`, and `lambda1=-4 N`. That solution is a
zero-reaction boundary extension of the source's strict-positive gate; if
stick requires `n>0`, it is inadmissible. It also permits an unbounded exact
tangent multiplier at zero normal force. This is a law-boundary convention,
not a numerical tolerance or solver fix.

The ideal rigid normal law is mathematically the infinite-stiffness limit of
the unilateral penalty for a fixed active branch with finite positive normal
reaction: positive compression tends to zero while the spring force tends to
a multiplier. The limit is useful as a separately labeled sensitivity only
where a self-consistent support state exists. It does not establish a
replacement response for the selected finite-penalty model and does not
transfer force demands from another branch. No current frame corner demands
are unlocked by this screen, and it does not prove the full frame has no
alternative support branch.

The pinned CalculiX 2.23 `*EQUATION` / `*NODE PRINT,RF` method has already
verified exact tangential MPC reaction recovery in
[the transformed all-bearing coupon](../current-exact-floor-mpc-fixture-attempt02/README.md):
`RF_REFERENCE - dependent-node CLOAD` was the unique map closing both physical
force balances across twelve printed increments. That coupon did not test
unilateral rigid branch switching or the sign of a normal multiplier. A
minimal future method coupon would reuse this three-DOF SPD system, encode an
active `q=0` row and the two tangent rows through unique physical pivots and
fixed references, release those rows in the open branch, and assess both
known answers and multipliers. It should include the original no-branch load,
the positive-reaction stiffness-limit load, and the zero-reaction boundary
load. A fixed-mask MPC solve can verify reactions; it cannot by itself prove
that CalculiX performs the gated contact update.

`derive.py` reads the earlier fixture's `fixture-spec.json`, recomputes all
branch equilibria with Python `Fraction`, asserts the expected gate outcomes,
and writes `screen.json`:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-ideal-stick-rigid-normal-limit-screen-attempt01/derive.py
```

`source-pins.json` binds the source toy, the earlier native reaction coupon,
the pinned manual, and the generated packet artifacts. This is only an
algebra/method screen. It is not a normal-stiffness study of the six-case
frame, a solver-method validation, a floor qualification, friction evidence,
or an engineering acceptance result.
