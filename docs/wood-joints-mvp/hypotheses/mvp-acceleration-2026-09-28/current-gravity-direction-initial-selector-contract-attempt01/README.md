# Initial gravity-direction selector contract — attempt01

## Decision

The source provides enough information to define one bounded, input-only
first-direction selection for case `a12-rear`. It does not provide the
selected state. Start from the reviewed undeformed geometry with zero connector
force, then solve the right-hand gravity direction at `beta -> 0+`; do not
choose a contact mask. The 100 floor-normal source spans have a maximum
initial residual of `2.4158453e-13 mm`, and all 100 normals point in global
`+Z`. Thus a cell that bears immediately from the initial touching geometry
uses its two source tangent references `r=(0,0) mm`. An initially open cell
has zero normal and tangent force; a later re-engagement needs its own
bracketed event and captured reference. This result defines a bounded next
method step, not readiness to claim a gravity equilibrium.

Scope is candidate `compact-floor-flush-wood-joints-development`, geometry
`led-clearance-2x6-runner-seated-blocks-v1`, case `a12-rear`. No source,
geometry, operator, native input, or previous packet was changed. No solver
was run for this packet.

## Reduced equations and source loads

Use the source-bound operators from
[`current-frame-connector-compliance-attempt04`](../current-frame-connector-compliance-attempt04/README.md):

```text
H: 1840 x 1840 mm/N       D: 1840 x 300, dimensionless
e: 1840 x 12 mm          W: 300 x 12 N
q = D*a + e - H*f         D.T*f = W
```

Here `f` is the 1,840 signed connector-force vector in N; `q` is the
conjugate connector displacement in mm. `a` has 300 body-rigid generalized
coordinates, translations in mm and rotations scaled as `1000 mm * radians`.
The last three entries of `W` are moments divided by `1000 mm`, so every
generalized-force entry is N. Keep `D.T*f=W` as raw force and moment balance;
do not project away a nonzero load to make a gauge solvable.

Columns are six exact case-specific gravity/climber pairs:

| Case | Gravity `e,W` columns | Climber `e,W` columns |
|---|---:|---:|
| `a12-rear` | 0 | 1 |
| `a12-forward` | 2 | 3 |
| `a12-left` | 4 | 5 |
| `k12-right` | 6 | 7 |
| `k12-rear` | 8 | 9 |
| `a1-rear` | 10 | 11 |

For each case `c`, use its own source maps and columns. The proposed path is
`(e,W)=beta*(e_g,c,W_g,c)` for gravity settling, then
`(e,W)=(e_g,c,W_g,c)+alpha*(e_climber,c,W_climber,c)` for the climber ramp.
The gravity map retains all 778 source mass entities and 50 physical-body
wrenches. The recorded gravity resultant is `(0,0,-2200.816009515055) N`;
do not add carrier wrenches a second time or transfer a settled state between
cases. First-direction selection is for `a12-rear` only; it does not run the
later path.

## Right-hand initial direction

At `beta=0`, set `a=0`, all source-law forces `f=0`, and hence `q=0`. This is
the reviewed source geometry and the source laws have zero force at zero
extension; it carries no prestress, dead-load response, or reaction. The
directional problem uses the unit gravity columns `(e_g,a12-rear,
W_g,a12-rear)` directly. It is the exact right-hand branch coefficient, not a
finite guessed load step. The source unilateral tables have a positive-side
linear slope at zero. If a directional solution has coefficient `q'`, its
physical extension is `beta*q'`; the recorded `[-10,+10] mm` table domain
applies to that physical extension, not to the normalized directional
coefficient. Check the domain on every finite continuation state. A strict
one-sided solution has a sufficiently small right neighborhood with the same
branch, but this contract chooses no finite epsilon.

Preserve each row's source orientation and law. There are 348 bilateral
SPRING2 rows, 1,122 compression-oriented and 170 tension-oriented
compression-only-in-their-own-positive-`q`-direction SPRINGA rows, plus 100
floor normals within those 1,292 unilateral rows and 200 conditional floor
tangent rows. All unilateral source rows use the conjugate scalar law
`f_i=k_i*max(q_i,0)`; the 170 tension-only labels reflect their source axis
orientation. Do not flip those rows based only on their physical label.

For each unilateral row, a borrowed indicator model may represent both
branches without finite big-M bounds. On the initial directional coefficient
solve, use the zero-extension tangent law and do not apply the finite table
domain to the normalized coefficient:

```text
active=1: q >= 0, f = k*q
active=0: q <= 0, f = 0
```

The 348 bilateral rows use `f=k*q`. Each floor-normal binary also controls
both of that cell's tangent rows: immediately bearing means `q_t1=q_t2=0`
using the initial references `(0,0) mm`, with signed, unbounded tangent
multipliers; open means both tangent multipliers are exactly zero. The model
must retain all 300 `a`, all 1,840 `q` and `f`, every load column, and the raw
body equilibrium equations. The 1,192 nonfloor unilateral indicators follow
their row laws too. PySCIPOpt/SCIP indicator mechanics have only tiny-fixture
evidence; a 1,292-binary solve has no established runtime or scalability.

The initial directional branch must be strict at the floor: an immediately
bearing cell has positive directional normal force, and an open cell has
negative directional gap. A floor cell left at `q_n=N=0` is an unresolved
boundary; do not count its open/closed binary variants as a unique branch.
For ordinary unilateral rows, two indicator assignments with the same
`(q,f)=(0,0)` are the same physical state and do not make a second floor
episode branch. Compare physical states and the 100 floor episodes, not raw
1,292-bit masks.

## Gauge and branch uniqueness

The existing rank packet is a rigid-body kinematic screen, not the actual
directional tangent. Its all-open bilateral branch has nullity 80 at the
`1e-10` cutoff: six common rigid modes plus 74 additional relative-body
mechanisms. The optimistic all-1,292-normal-active envelope has nullity 3
(global `Tx`, `Ty`, `Rz`) at that cutoff, but is not a selected state. The
all-bearing tangent envelope is conditional and cannot be used at zero load.

Therefore the selector must not install a presumed six-mode or three-mode
anchor. Determine the nullspace of the actual strict directional branch,
check `Z.T*W_g=0` on each candidate reaction-free gauge mode before removing
it, and leave all physical body force/moment balance intact. Remove only
verified common rigid modes; any remaining relative mechanism, incompatible
load projection, or gauge reaction leaves the result unresolved. An arbitrary
support node or a projected-away gravity wrench is not a gauge.

Treat the physical floor-episode branch as unique only if the bounded search
proves no second strict, admissible 100-cell floor branch. A second branch is
`MULTIPLE_PHYSICAL_FLOOR_EPISODE_BRANCHES`; a zero-gap/zero-force boundary is
`AMBIGUOUS_ZERO_BOUNDARY`; unproven solver status or exhausted limits is
`BUDGET_OR_SOLVER_STOP`. Do not choose the branch with lower energy or a more
favorable force. If a fixed floor mask is solved as a convex subproblem, its
state must still pass the original raw equations and row laws.

## Fixed-floor-mask convex subproblem: scope of validity

For an already prescribed floor mask and its already captured held references
`r_j`, the borrowed energy formulation is mathematically correct if `H` is
reciprocal symmetric positive definite and all `k_i>0`:

```text
J(f) = 1/2 f.T*H*f + sum_springs(f_i^2/(2*k_i))
       - e.T*f + sum_held_floor_tangents(r_j*f_j)
subject to D.T*f = W
```

Bilateral `f` is free, unilateral spring `f>=0`, held tangent multipliers are
free, and open floor tangent forces are fixed to zero. An open floor normal
has `f_n=0` and must also satisfy the explicit affine inequality `q_n<=0`;
fixing `f_n=0` as an equality alone would not impose that KKT condition. A
held floor normal remains a unilateral variable `f_n>=0`, and its solved
state is postchecked for strict positive bearing. With Lagrangian
`J - a.T*(D.T*f-W)`, stationarity gives `q=f/k` on an active spring and
`q_t=r` on a held tangent. A lower-bound multiplier gives `q<=0` for
unilateral spring rows that are not fixed by an equality. This includes the
1,192 nonfloor unilateral laws without binary variables for that prescribed
floor state.

This QP cannot discover the floor masks, initial direction, captured
references, or load history. Solving several masks and preferring the lowest
energy does not implement the path rule. Further, serialized `H` has measured
relative reciprocity error `9.3832183e-11`, rather than exact stored
symmetry. The QP derivation assumes the exact reciprocal operator; any
numerical symmetrization must be explicit, bounded by the pinned reciprocity
check, and separately checked against the original unsymmetrized `q` equation.
The exact source-law indicator system is the direct first-direction method
candidate; the QP is a fixed-mask verification/reduction option, not a state
selector.

## Applicability replays

I replayed the borrowed reduced indicator method's known-answer suite and the
two existing native coupon output assessors. All passed. The coupon assessors
read the already frozen `model.dat` files; no native solver was launched.

| Replay | Observed result and pinned output | What it supports |
|---|---|---|
| `current-reduced-coupled-indicator-method-attempt01/verify_method.py --verify` | `PASS_REPLAY_REDUCED_COUPLED_INDICATOR_KNOWN_ANSWERS`; eight existing coupled state oracles plus two signed raw `D.T*f=W` checks; PySCIPOpt 6.2.0 / SCIP 10.0.2 | Indicator equations, explicit zero-boundary/no-state/multiple-state stops, and retaining raw body wrench equilibrium on the tiny fixtures |
| `parent_release_check.py current-floor-nonzero-reference-release-native-attempt01` | `PASS_PARENT_NONZERO_RELEASE_ALL_INCREMENTS`; 12 printed increments, `model.dat` SHA-256 `20c5395b0d256b7090126adc8b7b8bf2a97ee0f13b1f920ce6470cdf68977487` | The native coupon maps `T=Ft-RF(T_REFERENCE,1)`, normal force, equilibrium, and zero tangent force on immediate open release |
| `parent_staged_check.py current-floor-staged-reference-native-attempt01` | `PASS_PARENT_STAGED_COUPON_ALL_INCREMENTS`; 60 increments, all ten stages, `model.dat` SHA-256 `b6d77329091d3302450a768bda39864b048fcc0cb0f4ef0ab516098206b8ec0e` | Capture on the first increment of stages 3 and 9; zero tangent on open stages 1, 2, 6, 7, 8; stage 7 stays open while both external components change |

Reproduction commands from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-project --with pyscipopt==6.2.0 --with numpy==2.5.2 python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-reduced-coupled-indicator-method-attempt01/verify_method.py --verify
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-staged-floor-native-mapping-preflight-attempt01/parent_release_check.py \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-nonzero-reference-release-native-attempt01
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-staged-floor-native-mapping-preflight-attempt01/parent_staged_check.py \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-staged-reference-native-attempt01
```

These checks validate the method signs and output interpretation on isolated
oracles. The native coupons have seven nodes and a single floor cell; they do
not validate the 1,840-row source operator, the 100-cell initial branch, a
reaction-free frame gauge, full-frame uniqueness, or the cost of the
1,292-indicator formulation.

## Events, later continuation, and hard stops

After a unique directional branch, a separate path solver may advance
`beta` from 0 to 1. For each opening or re-engagement, bracket and refine
`q_n=0`; solve simultaneous events together. At an event, compute both new
floor references from the exact joined tangent rows,
`r_episode,j=B_tangent,j*u_physical(event)`. Use `(0,0)` only for first
bearing from the reviewed initial touching configuration. At re-engagement,
replace the old references. On an open interval, remove the two stick rows and
require zero tangent force. Do not use the last-open sample as the event
reference. Then, and only after accepted gravity settlement, continue each
case's own climber map in `alpha`.

Stop unresolved on no admissible state; multiple physical floor branches;
unresolved `q_n=N=0`; an actual-branch mechanism/gauge with nonzero generalized
work; raw balance, source-law, or table-domain failure; an unbracketed or
unrefined event; active-set cycle; or solver/event budget stop. The expected
next result is one bounded `a12-rear` right-hand gravity-direction selection.
If it proves a unique strict branch and a reaction-free actual gauge, that
unlocks a bounded gravity continuation. It does not unlock climber loading,
other case response transfer, a frame run, or a joint acceptance claim.

## Source pins and reproduction boundary

This contract consumes, without editing, these exact outputs:

| Input | SHA-256 |
|---|---|
| `current-frame-connector-compliance-attempt04/assessment.json` | `ae30902f9340875a771d60dab83621ab5e0d6dcadb58c06a35bdb1bc8ac9da6c` |
| `current-frame-connector-compliance-attempt04/operators.npz` | `88a2f2f384edb7be7daa0e20cc87c7b8672ed13e975f8e86afd56d8aeb385b79` |
| `current-frame-connector-compliance-attempt04/row-identities.json` | `768d2afe58b48fa482f118f73bb01b8c911d1f937a5891d5c420a0d821b45037` |
| `current-frame-physical-connector-projection-contract-attempt01/projection-contract.json` | `4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3` |
| `current-floor-normal-tangent-join-contract-attempt01/join-contract.json` | `607ec82a8f830101a5bed07a9d1214aa85ac09179a9091472f7c951671ed8c4e` |
| `current-gravity-settle-climber-ramp-scenario-attempt01/decomposition.json` | `39d1530ee888bb824c2bd1624072890385c19a1448f4d146567a041aff5d14dc` |
| `current-frame-gravity-rank-readiness-attempt01/audit.json` | `a8453f861777a307a386a6398c3dd976965b7c6c6872b149f1826cfec08a5718` |
| `current-coupled-indicator-selector-fixture-attempt01/known-answer.json` | `8b42e4282952d8174f93b5f6138de14d0c88cbb1602d3968665aba5558045e88` |
| `current-coupled-contact-event-reference-fixture-attempt01/fixture.json` | `0e5e5f6953a34be3b2078159cd51eb0f5398cb15ff2f22efd9b1d6e7df75b19e` |
| `current-reduced-coupled-indicator-method-attempt01/assessment.json` | `509509a6da7c34d129e93baffa5eb99d69d7df11b75747a1ca3fccbc4037a7af` |
| `current-reduced-coupled-indicator-method-attempt01/method.py` | `953659834d56c1f1614cdc6359afff4e7eb7ca5df70f32e2ed8b1c03050de04c` |
| `current-reduced-coupled-indicator-method-attempt01/verify_method.py` | `6f4263388e330207387ba97421ebb49c358f24247834c5300b29ec59f115a9e7` |
| `current-staged-floor-native-mapping-preflight-attempt01/parent_release_check.py` | `480bd775efc0bd9e787b2fcd91814ff4c02eba98741bd7d41a4d8dcea38096b1` |
| `current-staged-floor-native-mapping-preflight-attempt01/parent_staged_check.py` | `f933cfb7424e435102f5b1d4f018370da14b471edee17607ee2426a58b6916da` |
| `current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json` | `9cd59d7bbafd65c740d2b0200e3dd88a6a49e6dca0bead0a38bc7826e337548c` |
| `current-floor-nonzero-reference-release-native-attempt01/model.dat` | `20c5395b0d256b7090126adc8b7b8bf2a97ee0f13b1f920ce6470cdf68977487` |
| `current-floor-staged-reference-native-attempt01/model.dat` | `b6d77329091d3302450a768bda39864b048fcc0cb0f4ef0ab516098206b8ec0e` |
| `current-floor-nonzero-reference-release-native-attempt01/freeze.json` | `632885e5e3ac8c47e286f48250d4ed04c087ed39dafe1348af4011515444b73b` |
| `current-floor-staged-reference-native-attempt01/freeze.json` | `02c0ea77685cc8ae40483c931096d2518bf3635929556c8c318745f08bf16c44` |

The parent remains responsible for rechecking source pins and implementing,
freezing, and authorizing any later selector or path computation. Tiny
indicator and event fixtures support method choices only; neither supplies an
actual-frame state.
