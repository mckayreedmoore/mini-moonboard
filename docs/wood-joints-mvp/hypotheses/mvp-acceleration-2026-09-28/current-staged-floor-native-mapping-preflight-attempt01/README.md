# Staged floor reference mapping preflight — attempt01

## Finding

The pinned CalculiX 2.23 input rules support the proposed *kinematic mapping*
for episode references without deleting or changing the source equations:

```text
physical pivot + weighted other physical DOFs - scalar reference = 0
```

Put the physical pivot first in each `*EQUATION` so it is the eliminated
dependent DOF; keep its scalar reference as an independent master. While a
contact is bearing, prescribe the scalar to the captured event coordinate.
While it is open, leave that scalar DOF unconstrained. Then the persistent
equation merely defines the pivot from the free scalar and other physical
coordinates; it does not tie the physical row to ground. The scalar must have
no separate element, load, or SPC while open. Do not prescribe an equation's
dependent DOF.

For a source row `h·u=0`, the episode form is `h·u-r=0`, with a distinct
reference scalar `r` per independent tangent row. The native normal springs
remain at every source cell and choose their own unilateral force state. A
separate driver must read all normal and displacement outputs together, solve
the coupled state, and update the scalar-SPC set together. The input deck does
not make `*BOUNDARY` conditional on normal force or gap.

The exact pinned 2.23 manual establishes:

- `*BOUNDARY,OP=MOD` keeps existing prescribed displacements and replaces a
  value for the same DOF; `OP=NEW` removes previous prescribed displacements.
  `*BOUNDARY` amplitudes scale prescribed values. A step-local constant-one
  amplitude therefore applies a newly captured reference from the first
  increment instead of ramping it from zero. Static loads can remain on their
  default ramp while only the reference card uses that amplitude.
- `*EQUATION` is a model-definition keyword; only `*EQUATION,REMOVE` is
  allowed inside a step. Its first term is dependent and cannot also be an SPC.
  Keep the `h·u-r=0` equations for the whole run and change only scalar SPCs.
- `*RESTART,WRITE,FREQUENCY=1` can save each step. A subsequent job starts
  with `*RESTART,READ,STEP=n`; its step cards can continue the same model and
  update boundaries/loads. The model/equation set must stay fixed.
- `*STATIC` steps ramp loads by default. A changed load at an existing
  node/DOF replaces its prior value; unchanged loads remain active.

To release selected references, `*BOUNDARY,OP=NEW` is the available direct
operation. It resets the boundary-condition set, so the new step must restate
all permanent SPCs and all references that remain active, omitting only the
released scalar DOFs. `OP=MOD` is suitable for adding a captured scalar or
changing its value, but it does not remove a stale scalar SPC.

The official current upstream driver source also rematches changed SPCs and
comments that removed SPCs no longer have numerical values. That source is
not pinned to the installed 2.23 executable, so it is corroboration only. The
new coupon includes a nonzero-reaction release probe to test the actual pinned
solver: a held state with `T=+1 N`, `N=0` is released at unchanged load and
must resolve to the open state with `T=N=0`. An endpoint-only position check
cannot substitute for that check.

## Small known-answer proposal

`prepare.py` exposes `build_fixture()` returning
`(Structure, record, metadata, deck)`, and generates three inspectable decks:

- [coupon-staged.inp](coupon-staged.inp) schedules the exact synthetic two-
  coordinate contact path and both episode-reference captures.
- [coupon-nonzero-release-probe.inp](coupon-nonzero-release-probe.inp) tests
  release of a nonzero tangent reaction with unchanged external loads.
- [coupon-restart-continuation.inp](coupon-restart-continuation.inp) shows a
  continuation from the first event checkpoint, beginning with the required
  `*RESTART,READ,STEP=2` line.

The coupon uses physical coordinates `t=U(T_BODY,1)` and
`q=-U(Q_BODY,2)`. Three unit `SPRING2` components give the exact structural
matrix `K=[[2,1],[1,2]] N/mm`. A normal `SPRINGA` has a 100 mm initial span and
table `(force,elongation)=(0,-10),(0,0),(20,10)`, so its branch is
`N=2 max(q,0)` over the full answer range. Tangent equation pivots are the
physical `T_BODY,1` DOF; reference node 7, DOF 1 is the independent scalar.
The amplitude `CAPTURE` is 1 over local step time `[0,1]`, so a newly
prescribed scalar takes the captured value at the start of its step.

The expected path is the exact result already recorded by the coupled event
fixture: `(-4,-3)` settles at `(t,q)=(-5/3,-2/3)` open; first bearing is
localized at `(-4,-2)` with `(t,q)=(-2,0)`; the captured `r=-2` branch reaches
`(-4,-1)` at `(t,q,N,T)=(-2,1/4,1/2,-1/4)`. It unloads through the zero-force
opening event at `(-4,-2)`, then releases. A second open ramp reaches
`(-2,-1)` at `(t,q)=(-1,0)`; capturing `r=-1` gives the final state
`(-2,1)` at `(t,q,N,T)=(-1,1/2,1,-1/2)`. Exact rational states are in
[known-answer.json](known-answer.json).

The separate release probe starts at `Ft=-3 N,Fq=-2 N`, holds `r=-2 mm`,
and must recover `(t,q,N,T)=(-2,0,0,+1)`. At identical load after `OP=NEW`
removes the scalar SPC, it must find the open equilibrium
`(t,q,N,T)=(-4/3,-1/3,0,0)`. It will expose a ghost reaction accidentally
carried as an external load.

The new analytical checks and all pre-existing fixture replays can be repeated
with:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-staged-floor-native-mapping-preflight-attempt01/prepare.py
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-staged-floor-native-mapping-preflight-attempt01/verify_proposal.py
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-two-cell-coupled-stick-fixture-attempt01/verify_fixture.py --verify
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-structural-coupling-fixture-attempt01/verify_fixture.py --verify
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-structural-coupling-fixture-attempt01/parent_check.py
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-structural-coupling-fixture-attempt01/parent_reference_counterexample.py
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-coupled-contact-event-reference-fixture-attempt01/verify.py --verify
```

No native run was made. The local mechanics check verifies the exact two-DOF
matrix and rational event answers; it does not verify 2.23's `*BOUNDARY`
removal, amplitude-at-entry, restart continuation, or RF behavior. Those are
the reason for the proposed one-launch known-answer coupon.

## Applicability limits and required stops

This makes the *mapping representable*; it does not create a full-frame
episode solver or make a fixed list of bearing cells valid. A future bounded
driver must in each accepted increment:

1. solve all 100 unilateral normal states jointly with the original source
   loads, material laws, equations and body model;
2. check active normal compression and inactive separation from rounded
   native outputs; release both tangent rows when a cell opens;
3. bracket and refine each opening/re-engagement event, capture its measured
   row coordinate, then restart/continue with all current scalar SPCs updated
   together; and
4. stop on no admissible state, multiple incompatible states without a
   justified loading-history selection, active-set cycles, unrefinable
   events, inconsistent body/global balance, or exhausted budget.

Neither stepwise `*BOUNDARY` nor restart selects contact states, localizes
events, or guarantees a unique path. A frame run would also need a zero-load
nullspace/rank check. Six common rigid modes are expected, but no claim is
made that these are the only modes once contacts/ties are open. Only a
demonstrated reaction-free gauge may remove rigid modes; any internal mechanism
is a stop, not a reason to add floor anchors or guessed constraints.

The repeated fixture replays validate only their recorded analytical/native
method cases. This packet is not frozen or native-ready, does not transfer any
rejected frame force/mask, does not authorize a frame run, and establishes no
floor, friction, anchorage, capacity, or joint acceptance.
