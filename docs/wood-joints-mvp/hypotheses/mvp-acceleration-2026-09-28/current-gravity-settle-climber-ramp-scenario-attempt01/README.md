# Gravity-settle then climber-ramp scenario proposal — attempt01

## Result and scope

This input-only packet decomposes the six registered source load cases into
the full gravity source map and the one source-bound climber patch map. It
recomposes each case against its registered physical nodal map and first
moment, and replays the two-cell/reset and coupled contact-state fixtures.
It defines a candidate loading/history contract for a later parent review.

No frame deck was prepared, frozen, or run. No contact state or force from a
rejected frame response is adopted. This proposal changes no geometry,
stiffness, source law, material, existing accepted scenario, native criteria,
or capacity. It does not establish that any whole-frame history has one
admissible state or converges.

## Source decomposition

The six case IDs and exact input hashes are in [source-pins.json](source-pins.json).
Their current all-bearing source input models retain each case's complete
`physical_external_loads` map and its single normalized
`uniform_square_patch_wrench` row. For each case the verifier forms

```text
F_climber = normalized physical nodal map for that case's climbing patch
F_gravity = registered full physical nodal map - F_climber
F_total   = F_gravity + F_climber
```

This is a nodal-vector decomposition, not a centroid substitute. The verifier
checks exact nodal recomposition, the six registered map hashes, source
gravity totals and first moments, every one of the 50 physical body gravity
wrenches against the source wrench ledger, and each climber patch force and
first moment against its case source. The common gravity resultant is
`(0, 0, -2200.816009515055) N` with moment about the global origin
`(-1535856.136567969, -3619.323688877, 0) N·mm`; each decomposed nodal gravity
map agrees across cases within `4.55e-13 N` per component. Exact nodal
recomposition error is zero for each case. The source gravity inventory is
778 mass entities (50 physical member/panel solids, 142 T-nuts, and 586
mapped hardware entities: 460 current candidate, 60 retained frame, and 66
panel-screw proxy components) expanded into 952 receiver-wrench ledger rows.
All 50 body maps remain present; none is omitted from the staged load.

The existing input models are used only as source-load records. Their floor
mask, normal response, tangent response, and any rejected-response force are
not transferred into this proposal.

The reproducible result is [decomposition.json](decomposition.json). Run:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-gravity-settle-climber-ramp-scenario-attempt01/verify_decomposition.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-gravity-settle-climber-ramp-scenario-attempt01/verify_decomposition.py --verify
```

The first command recomputes only a summary from pinned JSON inputs; it does
not rebuild geometry, write a deck, or invoke a solver. The second compares
the summary byte-for-byte.

## Fixture replay

The requested prior method checks were replayed before drafting this loading
contract:

- `conditional-floor-two-cell-coupled-stick-fixture-attempt01/verify_fixture.py --verify` passes all 8 stages, each with one normal active set, zero open-contact tangent force, and force/moment/stick residuals within its recorded `1e-9` check.
- `conditional-floor-structural-coupling-fixture-attempt01/verify_fixture.py --verify` passes 4 stages with all 4 masks enumerated per stage; its maximum selected balance residual is `3.553e-15 N`.
- The independent `parent_check.py` reproduces all 4 selected states and checks all 16 masks. `parent_reference_counterexample.py` separately reproduces no admissible fixed-reference state for one load and two mirrored admissible branches for another.

Reproduce those checks from the repository root with:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-two-cell-coupled-stick-fixture-attempt01/verify_fixture.py --verify
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-structural-coupling-fixture-attempt01/verify_fixture.py --verify
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-structural-coupling-fixture-attempt01/parent_check.py
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-structural-coupling-fixture-attempt01/parent_reference_counterexample.py
```

These are small analytical fixtures. They establish the tested local reset,
opening, coupled equilibrium and bounded mask-enumeration behavior only. They
do not demonstrate full-frame existence, uniqueness, event convergence,
three-dimensional native mapping, or solver termination.

## Proposed path contract

For every source case `c`, use its own source-bound maps and preserve the
original physical point loads and moments:

```text
gravity settle:  F_c(beta) = beta * F_gravity,      beta from 0 to 1
climber ramp:    F_c(alpha) = F_gravity + alpha * F_climber,c,
                 alpha from 0 to 1
```

At `beta=1, alpha=1`, nodal loads and first moments must reproduce that case's
current source load register. The gravity phase includes every gravity
source row: all 50 distributed member/panel solid self-weights, all 142
T-nuts, and all 586 mapped hardware entities with their recorded receiver
shares and source couples. The source rows are one complete dead-load table,
not extra loads to add to already assembled carrier wrenches.

Use the existing unilateral normal law and geometry. For each floor cell,
solve its normal state together with the two tangential states and all other
cells. A positive normal reaction enables the owner's ideal no-slip condition
for that contact episode; an open cell has zero normal and exactly zero
tangent reaction. On opening, remove both tangent constraints. At first
bearing and every re-engagement, record the relative tangent coordinate at
the contact event as the episode reference. Hold that reference only while
the normal state remains bearing. Do not preserve tangent reaction through
an open interval.

Locate opening/re-engagement by bracketing the sign/event between load
increments and refining the event. Record the event coordinate and verify its
stability under refinement using source-output rounding intervals. A last
finite open increment is not itself the event reference. No posterior offset
chosen from a desired final equilibrium is allowed. The fixture replay tests
reset after a recorded open stage; it does not supply a full-frame event
locator or numeric refinement tolerance.

At zero load, all global external force and moment are zero. Six common
rigid-body coordinate modes are guaranteed; a later implementation must run
a tangent-rank check rather than assume they are the only zero modes.
Additional internal zero modes from inactive or unengaged carriers stop the
method pending separate treatment. Remove only demonstrated null modes with
a reaction-free gauge/nullspace projection, verify zero generalized gauge
reactions, and retain the source geometry as the initial configuration. Do
not clamp a floor node, add an anchor, or report gauge multipliers as physical
support reactions. If gravity increases from zero without an admissible
bearing state, stop; do not use the gauge to balance a nonzero external load.

Advance `beta` monotonically to the gravity-settled equilibrium. Then hold
gravity fixed and advance `alpha` monotonically. Carry only an accepted state
and its episode references into the next increment. A bounded active-set
algorithm may update normal and tangent states together inside this one
load-path solve, using complementarity and recorded event history. This is
different from relaunching fixed-mask frame runs until one looks favorable.
Every candidate must satisfy the original carrier laws, source/MPC checks,
open-tangent zero-action rule, individual body balance and global balance.

Stop unresolved if an increment has no admissible state, multiple distinct
admissible states remain after the recorded loading history, an active-set
cycle recurs, an event cannot be bracketed/refined, a balance/sign gate fails,
or the declared iteration/event budget expires. Do not select a branch from
the rejected response, prefer a branch because it carries a favorable force,
or resume blind cross-run mask retries. The active-set updates needed inside
one bounded coupled solve remain part of the proposed method.

## Native mapping dependencies for parent review

No current frozen frame input implements this path. A future implementation
must separately prove, before any frame deck is prepared:

1. The two staged nodal load maps can be emitted as distinct gravity and
   climber load blocks at original physical nodes without changing the
   source geometry, source force shares, source couples, CLOAD normalization,
   or the registered final resultant.
2. The native/control path can add and remove the 200 exact-stick tangent
   rows during nonlinear continuation, preserve each event reference, and
   solve all 100 unilateral normals and tangent states as one coupled active
   set. Fixed-mask steps do not implement re-engagement reset.
3. The initial zero-load six-mode gauge is reaction-free and has no physical
   floor restraint; it cannot be used to balance nonzero loads.
4. Opening/re-engagement event localization and output-precision intervals
   are implemented and independently checked on a known-answer, coupled
   event fixture before a full-frame input is considered.
5. Per-increment audits continue to cover every original MPC, all source
   carrier laws, all 50 physical bodies, every open tangential reaction,
   source first moments, and full global force/moment closure.

The parent has completed a separate source-independent exact event oracle at
[current-coupled-contact-event-reference-fixture-attempt01](../current-coupled-contact-event-reference-fixture-attempt01/README.md).
It passes 19 states and 10 event brackets, with an independent exact-fraction
balance/law/event check. For its synthetic one-contact example, the
gravity-like load is `(-4,-3)`, then `F(alpha)=(-4,-3+2 alpha)`; the open
branch event is `alpha=0.5`, `t_ref=-2`, and the ramp ends at `(-4,-1)`. The
fixture also checks a subsequent opening/re-engagement with a new reference
of `-1`. At odd subdivision counts `n=3,7,15,31,63`, last-open-coordinate
errors decay as `1/(3n)` or `2/(3n)`, showing why the event coordinate must
be localized instead of copied from the last open increment.

That analytic oracle addresses the reference-event rule only; it is not a
native solver test and provides no full-frame gauge or response result. The
coupled fixtures test small state enumeration, but full-frame readiness still
requires a separate tangent-rank/gauge audit, a mapping for all 100 normals
and 200 event-driven tangent rows, and a bounded coupled solver with
source-output interval checks. These fixtures do not establish those
full-frame properties or native load/control mapping.

The fixture passes are method evidence only. This packet is a proposed
scenario decomposition and event contract, not native-method readiness,
whole-frame feasibility, an accepted response, or design acceptance. Parent
owns any readiness review, freeze, native run and final validation.
