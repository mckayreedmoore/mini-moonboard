# Working-profile numerical followup

The final `profile-enriched01` packet records twelve accepted fields and all
fourteen dispositions. The three states lost by the initial wider-washer
sweep have passed actual strict retries. The remaining `a12-left_zero` and
`k12-right_zero` dispositions retain their original exhaustive floor-search
stops; those searches do not prove physical nonexistence.

The [followup controller](joint-frame-profile-followup.py) preserves the actual
`profile-frame01` sweep and the frozen v3
[replacement adapter](joint-frame-member-replacement.py). That first sweep
records nine accepted fields and five complete floor-search traces. The final
aggregate retains those nine fields exactly and adds the three actual retry
fields. Geometry, loads, connection laws and physical tolerances are unchanged.

## Source-mask question

Each stopped trace includes all 256 distinct floor masks. That is a complete
execution of the recorded search procedure, not proof that no physical
equilibrium exists. The source-only audit identifies the original accepted
`frame-attempt08` mask in each new trace:

| State | Original accepted bearing footprints | New profile trial at that mask |
| --- | --- | --- |
| `a12-left_gap` | 1, 2, 3, 4, 6, 7 | `AlmostSolved`; dual residual 1.17e-10 |
| `k12-rear_zero` | 0, 2, 3, 4, 6, 7 | `Solved`; ordinary physical gates pass, panel residual 0.00532984 N |
| `a1-rear_gap` | All eight | `Solved`; ordinary physical gates pass, panel residual 0.000168829 N |

The panel gate remains **less than 1e-4 N**. The controller freezes one
existing `fixed_floor_branch` call per state using the original
`REFINEMENT_SETTINGS`; it does not rerun the 256-mask search or accept
`AlmostSolved`. Original masks provide the trial branch, not transferred
forces. Each retry must pass all original body, shaft, washer, floor,
compatibility, spring and panel-screw checks, plus recovered continuous-shaft
nodal balance. The maximum is three new global equilibrium calls.
Failed iterates stay unaccepted and cannot become exported force fields.

The actual `retry01` receipt is
`49e7ddde970b3f6ebcb8f45c052a737ab71d6c72ae2feb359c727ca1704b6ee1`.
`k12-rear_zero` and `a1-rear_gap` passed with panel residuals
6.86656e-6 N and 3.89089e-6 N. The left-gap trial passed all seventeen
physical/panel gates, including a panel residual of 7.37670e-6 N, but remains
unaccepted: the selected `faer` backend returned `AlmostSolved` with primal
and dual residuals 1.77462e-10 and 1.10209e-10 against `tol_feas=1e-10`.
Its saved trial is diagnosis evidence and supplies no exported forces.

The three retries are a numerical repair question. An unresolved easy
numerical defect must not be renamed a completed method limitation.
`aggregate` therefore requires all three actual retry fields to pass before
producing the final enriched packet. The original five exhaustive traces and
their source receipt remain unchanged and recoverable.

## Source-only final aggregate

After successful retries, the aggregate owns its `response.npz`,
`comparison.json`, `inputs.json`, applied `joint-update.json`, updated
spring-law array and producer snapshot. It combines the nine actual profile
fields with the three new audited retries, preserving the complete fourteen
dispositions. The two remaining stopped states retain direct trace evidence
from the original profile packet; no stopped state receives forces.

The aggregate preserves the exact working-profile contract, four axial spring
updates, external coefficients, energy constant token and
`working_washer_profile_with_explicit_member_replacements` branch identity.
It adds the exporter metadata
`permanent_only_load_columns = {"gravity": 0, "live": null}` and each state's
live/permanent `load_scope`.

For every accepted state, it reconstructs continuous-shaft pose and audits the
saved force/motion/rigid field against the applied profile laws. It then calls
the existing `shaft_diagnostics` with that **same new saved field**, original
continuous-shaft geometry and frozen reference hypotheses. This supplies the
wood-seat resultant/area/pressure diagnostics required by the existing mean
reference consumer. Original frame08 diagnostics are not transferred.
Scalar-shaft own-end moments remain a separate development question.
The aggregate performs no global frame or native solid solve.

Both original and retry receipts, fields and comparisons are directly bound.
The existing action exporter can consume the owned aggregate arrays and
metadata. Its snapshot-only floor parser delegates to the existing pure
helper, authenticated through the same source closure. Absolute frozen
reference paths retain their original hashes.

## Frozen preparation and commands

The parent freezes `joint_frame_profile_followup_request/v1` with the actual
profile receipt, exactly the three target tags, maximum three calls,
`REFINEMENT_SETTINGS` and the source map from `source_bindings()`.
The map authenticates 532 source-only bindings, including profile outputs,
original accepted masks, reference/model helpers, the frozen v3 adapter and
this controller. Preparation saves the exact request, mask audit and producer
snapshot; no project solve occurs.

```bash
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-profile-followup.py prepare --request REQUEST --expected-sha256 SHA --output FRESH_PREPARATION
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-profile-followup.py retry --preparation FROZEN_PREPARATION --output FRESH_RETRY
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-profile-followup.py aggregate --retry-packet COMPLETED_RETRY --output FRESH_AGGREGATE
```

Fresh outputs are immediate children of ignored
`rawlocal/joint-frame-profile-followup`. The parent serializes and validates
the three retry calls. Their existing 60-second per-call solver limit gives
180 seconds of bounded solver allowance plus setup/postprocessing.
Source binding, mask-audit identity, snapshot-only floor delegation and Ruff
checks passed without a project solve during controller preparation.

## One backend qualification and remaining retry

The separate [backend controller](joint-frame-profile-backend-retry.py)
preserves both frozen producers and the actual `retry01` packet. The pinned
[Clarabel 0.11.1 settings source](https://raw.githubusercontent.com/oxfordcontrol/Clarabel.rs/v0.11.1/src/solver/implementations/default/settings.rs)
explicitly accepts `qdldl` as a direct solver. The backend coupon reuses the
existing `refinement_known_answer()` circular-clearance and near-open
unilateral fixtures. It requires `Solved`, actual `linear_solver=qdldl`, the
unchanged known answers and exactly the strict refinement settings with only
`direct_solve_method` changed. A backend name accepted by the settings object
alone is insufficient qualification.

Only after that frozen coupon passes can the parent prepare and run one
left-gap call at the same original accepted floor mask. The existing
60-second solver allowance, all strict feasibility/gap/refinement tolerances,
`Solved` requirement and seventeen physical/panel gates remain unchanged.
The two actual successful refinement fields and original nine accepted
profile fields are retained. A failed backend iterate remains unaccepted;
no aggregation occurs while numerical qualification is open.

The parent request uses `joint_frame_profile_backend_retry_request/v1`,
the one target tag, maximum one call, exact backend settings, actual retry
receipt, passed coupon directory/receipt and `source_bindings(coupon)`.
The source-only closure contains 544 bindings before coupon outputs are added.

```bash
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-profile-backend-retry.py coupon --output FRESH_COUPON
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-profile-backend-retry.py prepare --request REQUEST --expected-sha256 SHA --coupon-packet PASSED_COUPON --output FRESH_BACKEND_PREPARATION
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-profile-backend-retry.py retry --preparation FROZEN_BACKEND_PREPARATION --output FRESH_BACKEND_RETRY
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-profile-backend-retry.py join --backend-packet PASSED_BACKEND_RETRY --output FRESH_COMBINED_RETRY
```

`join` performs zero frame solves and preserves the two actual prior successes
and the single actual backend success as owned arrays with direct source
records. The unchanged followup controller then consumes this completed
three-state packet with its existing `aggregate` command. Both earlier
unaccepted trials and all original exhaustive traces remain pinned source
evidence. The `backend-coupon01` fixtures passed, but actual `backend-retry01`
remains unaccepted: `qdldl` returned `AlmostSolved` after 29 iterations,
with primal/dual residuals 3.73768e-11/1.47959e-10 and an objective gap
1.274e-8. All seventeen physical/panel checks still pass. The actual receipt
is `0aa57f222483ee6d1641ba900fda06ac31a5629dd7c2c98ff0eefbedcdd5f36a`;
its trial remains source evidence and supplies no accepted forces.

The ignored `rawlocal/joint-frame-profile-followup/precision-adapter.py`
imports the frozen backend controller and authenticates the actual failed
receipt. It freezes three ordered numerical configurations:

| Configuration | Direct solver | Static constant | Dynamic threshold | Dynamic shift |
| --- | --- | --- | --- | --- |
| `qdldl-static-1e10` | qdldl | 1e-10 | Unchanged 1e-13 | Unchanged 2e-7 |
| `qdldl-small-regularization` | qdldl | 1e-12 | 1e-15 | 2e-9 |
| `faer-small-regularization` | faer | 1e-12 | 1e-15 | 2e-9 |

The installed 0.11.1 static default is 1e-8. The pinned
[direct KKT implementation](https://raw.githubusercontent.com/oxfordcontrol/Clarabel.rs/v0.11.1/src/solver/core/kktsolvers/direct/quasidef/directldlkktsolver.rs)
shifts the factorization diagonal, then restores its internal matrix for
iterative refinement against the unshifted equations. Smaller regularization
is therefore a numerical precision hypothesis to qualify; it changes no
physical spring or body stiffness. The pinned
[QDLDL implementation](https://raw.githubusercontent.com/oxfordcontrol/Clarabel.rs/v0.11.1/src/solver/core/kktsolvers/direct/quasidef/ldlsolvers/qdldl.rs)
uses the dynamic threshold/shift directly and enables that regularization
internally, so changing only an enable flag would not test the intended effect.
Equilibration remains enabled with its original ten iterations and scaling
bounds 1e-4 to 1e4. Force scaling, floor mask, strict feasibility/gap/refinement
tolerances, `Solved` requirement and all physical/panel gates remain unchanged.

For each named configuration, the parent first runs the same two strict known
answers, freezes `request(configuration, passed_coupon)`, then permits at most
one project call. The ordered sequence stops at the first actual `Solved`
field passing all gates. This is bounded to three named calls and is not a
mechanical parameter study. `coupon`, `prepare`, `retry` and `join` use the
same arguments above plus `--configuration CONFIGURATION`. The closure has
557 source bindings before the new coupon outputs. Original controllers,
successful fields, failed trials and traces remain unchanged. All three tiny
fixture pairs passed, but none of the three project configurations produced
an accepted field: static-only `qdldl` returned `NumericalError` at iteration
13, and both smaller static/dynamic configurations returned `NumericalError`
at iteration 1. Their actual receipts are preserved in `precision-retry01`,
`precision-retry02` and `precision-retry03`; numerical qualification remains
open for left nominal clearance.

The ignored `rawlocal/joint-frame-profile-followup/termination-diagnostic.py`
prepares one instrumented original strict solve with default regularization
and explicit `faer`, full verbose file output and callbacks that always return
false. It sets only `reduced_tol_feas=0` to prevent a failed underlying status
from later being relabeled `AlmostSolved`; full `Solved` criteria and all
physical/panel gates remain unchanged. The same two known answers first
qualify this instrumentation. The source closure binds all three failed
precision receipts, original producers and actual fields (594 bindings before
new diagnostic coupon outputs).

The pinned [solver loop](https://raw.githubusercontent.com/oxfordcontrol/Clarabel.rs/v0.11.1/src/solver/core/solver.rs)
and [status checks](https://raw.githubusercontent.com/oxfordcontrol/Clarabel.rs/v0.11.1/src/solver/implementations/default/info.rs)
show that `AlmostSolved` can hide several earlier failure triggers. Recorded
raw status, callback iterations and final iterations distinguish an undersized
combined step from a residual-deterioration guard, and a failed KKT update/solve
from cone-scaling failure. Minimum-step settings remain unchanged until that
actual evidence identifies the trigger. The parent freezes `request(coupon)`
and runs at most one diagnostic call; no broader precision sequence is opened.
An unaccepted iterate remains diagnosis evidence and supplies no force fields.

The actual instrumented `termination-retry01` returned an underlying
`CONE_SCALING_FAILURE` at iteration 29, matching its last callback iteration;
the last accepted step was 0.68553. This rules out the minimum-step trigger.
All physical/panel gates still pass, but the original strict residual/gap
criteria remain unmet. The actual receipt is
`eeef38c65f57b0a3daa9fca9aae88dba46b694b51218078c31eb7c2c84375975`.
The pinned [SOC implementation](https://raw.githubusercontent.com/oxfordcontrol/Clarabel.rs/v0.11.1/src/solver/core/cones/socone.rs)
can reject scaling when the slack, dual or normalized scaling vector loses
its positive Lorentz interior determinant. Minimum-step settings stay fixed.

The ignored `rawlocal/joint-frame-profile-followup/lorentz-adapter.py` freezes
one exact cone-coordinate remedy. It aligns each selected cone's spatial
coordinates to its receipt-bound trial force direction, then applies a fixed
binary Lorentz boost `a=1/16`. This improves the relative interior margin of
the aligned opposing primal/dual rays by a factor of 256. Direction selection
uses the original `retry01` trial motion exceeding its original clearance by
1e-8: 58 cones are transformed, 318 retain identity, and all 376 constraints
remain present. The trial supplies coordinates and no transferred forces.

For `J=diag(1,-1,-1)`, each saved map satisfies `M.T J M=J` within a propagated
floating-point bound. Only its SOC row block changes to `M A`; original
objective coefficients, force coordinates, equilibrium rows, loads and laws
remain unchanged. Recovery uses `s_original=M_inverse s_transformed` and
`z_original=M.T z_transformed`, leaving equilibrium dual/rigid coordinates
unchanged. Four tiny calls qualify aligned circular/near-open laws, an
off-axis body/equality coupon with nonzero H/e and nonunit D, and an
inside-clearance apex before one parent-owned project call.

Every result saves full original/transformed x/s/z, cone margins and callback
history. Acceptance additionally recomputes the **original canonical** primal
and dual residuals and objective gap after backmapping, with the pinned
normalizations and unchanged strict thresholds. Native `Solved` and all
seventeen original physical/panel gates are still required. No physical
acceptance criterion is replaced by a transformed residual. The parent
freezes `request(passed_coupon)` and uses the existing `prepare`, `retry` and
`join` arguments. The source-only closure contains 612 bindings before new
coupon outputs. The first coupon stopped at the added off-axis motion
assertion before any project call. Native `Solved` and original canonical
checks passed; its force error was below 2.5e-12 N, but motion error was
5.10351e-7 mm against the added 1e-8 assertion. These failed-coupon bytes and
the 71f5 producer snapshot remain preserved in `lorentz-coupon01`.

The ignored `rawlocal/joint-frame-profile-followup/lorentz-dual-oracle.py`
corrects only that new auxiliary assertion. For original cone slack
`s=(t,w)` and dual `z=(alpha,-v)`, define `r=norm(w)`, `n=w/r` and cone work
`C=s dot z`. Feasibility gives
`norm(v-alpha*n)^2 <= 2*alpha*C/r`. The certificate propagates recorded cone
feasibility/work roundoff, original stationarity residual, axial spring error,
and source/reference direction difference to bound motion error. It then
uses the exact nonunit D/body H relation to bound rigid-coordinate error.

Source-only evaluation of the preserved failed coupon gives a motion bound
5.01376e-6 mm and rigid bound 1.00275e-5, encompassing observed errors
5.10351e-7 mm and 6.45525e-7. The auxiliary bound must also remain below
1e-5 mm, force error remains below 1e-8 N, and the original spring law plus
a stricter 1e-4 N auxiliary spring guard must pass. Observed spring-law
residual is 3.52906e-6 N. This records the angular accuracy implied by the
cone certificate and makes no 1e-8 off-axis motion claim.

Original aligned/near-open fixture gates, core method gates, all project
physical gates, Lorentz maps, solver settings and original canonical strict
criteria are unchanged. The correction imports the frozen method rather
than copying its solver. It binds all failed-coupon files without inventing
a completion receipt, and saves the fresh certificate as an owned coupon
output. Its source closure contains 624 bindings before fresh coupon outputs.
The actual `lorentz-coupon02` receipt is
`4291158508cc8f3d95db370c57839fd5b003f990d03c25984e5ac481056efdb8`.
All four tiny fixtures passed, including the original circular and near-open
gates, the off-axis body/equality certificate and the inside-clearance apex.
The packet authenticates 624 sources and owns sixteen outputs. The parent
then froze the qualified request before the single project call.

## Actual strict result and final aggregate

The actual `lorentz-retry01` receipt is
`dbce731c0922de869914dcd78ee1014e08a7365eae225ea910ba8dd0b4f476f8`.
The required `a12-left_gap` state returned native `Solved` in thirty iterations
and passed all seventeen original physical and panel gates. Independently
rebuilding the original canonical matrices, while intercepting construction
before any native factor or solve, gives:

| Original-coordinate check | Observed result | Unchanged strict criterion |
| --- | --- | --- |
| Primal residual | 8.60843e-13 | Less than 1e-10 |
| Dual residual | 4.10501e-13 | Less than 1e-10 |
| Absolute objective gap | 1.77533e-9 N mm | Absolute gap less than 1e-9 **or** relative gap less than 1e-13 |
| Relative objective gap | 7.14951e-14 | Same disjunction |

The relative-gap clause passes. Original force, rigid and relative-motion
fields reconstructed from the saved canonical solution exactly match the
exported response arrays. The 58 transformed and 318 identity cone blocks
remain present. Independently checked maximum Lorentz metric and inverse
errors are 1.90958e-14 and 1.62093e-14; the original/transformed cone-work
difference is 1.07025e-13. No status, load, law or acceptance gate was relaxed.

The final `profile-enriched01` receipt is
`317f8800d0f1ad947778d4f553a46403b50fbb9d921d0b70f8854928f9994455`;
its comparison hash is
`0a262d5933367be8a6ba98efde200048af67e6005dc6134ffbccb3332d0be34a`.
Independent read-only checks authenticate all 659 sources and six outputs,
and verify all sixty response arrays against their actual source fields:
nine from `profile-frame01`, two from `retry01`, and one from
`lorentz-retry01`. All five original exhaustive trace hashes remain bound.
The aggregate itself performs zero global solves.

Every accepted field passes both its original audit and the same-field
postprocessing audit. Each state owns the new continuous-shaft diagnostics
required by the mean-reference consumer and the exact live/permanent load
metadata required by the action exporter. The applied washer update and
joint-update bytes are preserved. Independent assembly-energy arithmetic for
all twelve fields agrees with the saved components within 2.91038e-11 N mm.
The energy remains explicitly defined up to the common unchanged body-load
constant; this gross-source frame packet supplies no absolute full-body energy
claim. The two remaining stops supply no accepted force arrays.

This follows the conditional first-order elastic/contact model. Numerical
equilibrium and diagnostic enrichment do not establish strength, active-state
stability, inspected hardware/floor, fabrication or climbing acceptance.
All physical release flags remain false.
