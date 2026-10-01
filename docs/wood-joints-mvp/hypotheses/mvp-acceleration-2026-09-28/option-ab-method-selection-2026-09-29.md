# Option A/B feasibility comparison

Date: September 29, 2026  
Lane: `compact-floor-flush-wood-joints-development`  
Reviewed geometry: `led-clearance-2x6-runner-seated-blocks-v1`  
Scope: read-only feasibility comparison; no source, model, deck, or geometry
changes and no solver run.

Independent Luna Max cold review: passed September 29, 2026; no blocking
corrections. Parent independently verified the local links and cited c11,
gravity-source, and load-input hashes.

## Recommendation

Keep **whole-frame static demands followed by applicable code/product checks**
as the route to MVP, with targeted local models only for unresolved mechanisms.
Advance Option B only as a read-only demand-coverage and load-path preflight.
Today’s evidence contains no accepted member-force or joint-demand subset for
design checks: the six-case load wrenches, geometry and exception screens are
usable inputs, while c11’s one-case force recovery is conditional on a failed
contact branch. If the next preflight finds no subassembly with a closed,
supported path, stop numerical response work and report the missing facts.

Do not start Option A implementation now. It is a new conditional-stick
formulation, and neither a bounded solution method nor branch uniqueness has
been demonstrated. More contact coupons will not settle the constitutive
gap: the existing CalculiX 2.23 coupon already validates normal contact and
`CF`/`CFN`/`CFS` output, while 2.23's friction law requires an unsupported
positive coefficient. The [feasibility plan](next-gate-feasibility-plan-2026-09-29.md)
contains the exact hand-solvable fixture to use if a parent later scopes that
new method.

This preserves the original route-to-MVP decision. The failed c11 branch is a
stop for that branch and for transfer of its response quantities; it is not
evidence that the conventional whole-frame demand/code-check architecture is
inherently unusable.

## Option A: coupled conditional-stick complementarity

The concrete law would keep unilateral normal contact,
`N_i = k_i max(0, -g_i)`, and enforce both tangential relative translations
`Δu_t = 0` only while the same cell bears (`N_i > 0`). An open cell must have
zero tangent reaction. The current finite paired floor `SPRING2` tangents
must be replaced; their stiffness and reactions are not the ideal constraint.
That choice follows the owner's conditional no-slip analytical assumption,
not a measured floor property.

The update must solve normal and tangent states together because changing
tangent constraints changes the global displacement field and which normal
cells bear. It is path-dependent unless the method defines its state history.
At minimum, freeze the initial loading sequence, the reference displacement
when a cell first bears, and the reset rule at each re-engagement. A proposed
rule—record relative tangent position at first bearing, hold it while bearing,
release on opening, and record a fresh reference on re-engagement—still needs
parent review and a coupled fixture. The feasibility plan's prescribed-state
oracle checks signs, reactions, release and reset arithmetic; it does not by
itself prove an algorithm selects the coupled state correctly.

Current reduced response has 1,122 unilateral normal cells; c11 has 317 active
normal cells. The existing branch-transition tooling checks that a candidate
active set has not appeared in earlier consumed runs, but it supplies no
practical iteration cap or uniqueness argument. Finite enumeration has an
unusable worst case, and a deterministic active-set or semismooth method would
need a proved stop/fail policy, cycle handling, and a small coupled known-answer
fixture before any full-frame attempt. The current six c11 sign failures (four
internal cells and two floor cells) also show that force balance and successful
postprocessing alone do not establish complementarity.

**Transfer boundary:** c11 used finite tangent springs. Its floor tangent
reactions and all c11 response quantities—including support reactions,
displacements, member stresses, contact forces and joint forces—are
branch-conditional and do not transfer to Option A. The exact response was
for one A12-rear zero-gap diagnostic, not six cases. c11's
independent audit passed response accounting, while numerical checks and
mechanical acceptance remain false.

## Option B: conventional frame demands and code checks

The current inputs support a useful preflight: six frozen applied-load cases,
300 body external-wrench rows, source geometry and receiver identifiers,
contact-patch inventory, and six outward panel-normal load resultants. These
are load inputs and path evidence, not computed member actions. No accepted
`N/V/M` table or joint-demand table is present. A global equilibrium or
tipping screen is necessary only and cannot recover member bending or
connector forces.

c11 recovered 1,566 physical connector-force records, global and 50-body
equilibrium, and its modeled axial ties for one branch. Those remain
conditional diagnostics only: six contact signs fail, the 66 Hillman axial
ties use a non-qualifying stiffness ratio of 1.0, and neither tie force proves
capacity or physical sharing. Do not use c11 outputs as Option B design
demands. The failed branch also cannot produce six-case code checks.

The shortest defensible next task is a read-only demand-coverage register for
the same six cases. For each member and joint, identify the source load,
receiver path, support law, and response quantity needed; then mark it as
source input, recoverable with a specified closed model, or blocked. Advance a
partial numerical demand only for a subset whose full load path and support
conditions are represented and whose response is independently equilibrium-
checked. The current record has not yet established such a subset.

## Four integration gates that remain separate

| Gate | What is established | What still prevents complete design demands |
|---|---|---|
| **Floor support** | The owner permits an explicitly conditional no-slip-while-bearing analytical assumption. The pinned 2.23 manual screens out frictionless contact, finite-`μ` Coulomb friction, and tensile `TIED`/`*TIE` as exact substitutes. | Floor law remains an unverified assumption. Do not invent `μ`, infer an anchor, or transfer c11 finite-tangent reactions. |
| **Panel withdrawal** | The six outward resultants before gravity are A12 rear **1,659.44 N**, A12 forward **1,199.82 N**, A12 left **1,429.63 N**, K12 right **1,429.63 N**, K12 rear **1,659.44 N**, and A1 rear **1,659.44 N**. | Those are global panel inputs, not screw-group/per-screw demands. Hillman 42605 withdrawal stiffness and resistance, head/panel limit, group sharing, and complete tension path are unsupported. |
| **Receiver/hardware path** | Current c11 source code maps the 586 non-member hardware gravity rows into 760 receiver-body point-wrench contributions; force and first moment are preserved, and all-to-each-receiver extremes are available. This is an explicit load-assignment model. | It does not prove mechanical carrier stiffness, connection action, real force split, or receiver-to-frame transfer. Six opposed-patch pairs remain zero-area/unresolved; the center-kicker receiver paths remain open. |
| **Self-weight in frame response** | The c11 solid builder applies the 50 member/panel self-weight rows as distributed consistent body gravity, separately maps 142 T-nuts, and accounts for all 778 source mass rows in its frozen one-case assembly. | A beam/frame Option B model must distribute member weights along its members to recover bending. The solid C3D20 load mapping or a centroid resultant is not a substitute for beam line loads and section-force recovery. |

These four gates are not exhaustive of all connector, material, stability and
resistance checks. A new model can only reduce uncertainty for the assumptions
it actually represents.

## Decision and handoff

Recommendation: **Option B, preflight only**. The next safe Luna Max
coordinator task is the read-only demand-coverage register described above.
Its output should identify any path-complete partial subset, list the exact
load/response fields and equilibrium checks needed to calculate it, or conclude
that no subset is currently defensible. Do not start a response implementation
or solver run from that register alone.

Parent retains any new analysis formulation or candidate revision, input and
method freeze, solver choice and run budget, native execution, and final
validation. Any implementation or run requires a separate parent-owned plan
and explicit authorization. No c12, radial fixture, source-clearance pilot,
or joint acceptance follows from this comparison. This artifact does not
authorize a future run.

## Evidence anchors

| Evidence | SHA-256 and relevance |
|---|---|
| [c11 freeze](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/freeze.json) and frozen [`wood_joint_reduced_case.py`](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/sources/fea/wood_joint_reduced_case.py) | Freeze `1633e79900afd194ece79c7463a7b383a11bb96920e7449e6a25c528e933b8e2`; frozen case builder `9b442e85221c383f1ad013dd493d87c9d4a303b6e36f58b2733f5de00316e192`. This is the exact c11 source pin. |
| [c11 response](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/response.json) and [independent audit](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1-postrun-review/independent-postrun-review.json) | Response `b8558fbaa986ff251008da629c21d8d9a56e16c965ce09476e94a688f0a9f878`; audit `0c6c7b8601a8b15cd46901c912934483b5da14babb84380a9301c0730cdb18ed`. Six contact signs fail; mechanical acceptance false. |
| Frozen [body gravity source](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/sources/fea/wood_joint_reduced_gravity.py) and [case assembly source](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/sources/fea/wood_joint_reduced_case.py) | Gravity source `e41c09282d59fa41d452ec88031fc59213863fd6edf65b1335dc8de92b7d3c45`; case builder `9b442e85221c383f1ad013dd493d87c9d4a303b6e36f58b2733f5de00316e192`. Builder lines 301–336 distribute 50 body self-weights; lines 387–430 apply hardware source wrenches; lines 458–519 close body and global load wrenches. These establish the c11 load-application method, not mechanical validation. |
| [attempt01 case-assembly audit](reduced-static-attempt01/case-assembly-check.json) | `55f94ae42ed7b2efc1e2a70157b24881c6f35cb3fd0d531cd5de71ee9e2600a0`; it pins the earlier case-builder SHA `1bd3e38bf13b83532166c1292018eccf5caf5102febf33332eaac6e35e9187ce`. Treat it as earlier packet evidence; do not attribute that audit to c11's 9b source. |
| [six-case load inputs](reduced-static-attempt01/model-inputs.json) and [external body wrenches](reduced-static-attempt01/body-external-wrenches.csv) | `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9`; `6c823add8e29fc2089bff460ce7fa59c300794511214890b638b6c1a6c77a33f`. They specify external loads; not internal actions. |
| [panel withdrawal preflight](panel-withdrawal-preflight.md) and [coordinator review](COORDINATOR-HANDOFF-REVIEW.md) | `22e4b14d270a1d7ba8a247562b901ef4998483ca7d70feed6646560a29c6d18f`; `e6caddbb975411ab2bfe6c79dae0f955f1f03860ded1ba2fcf3558e681bdd79c`. These bound panel loads and unresolved geometry/path concerns. The coordinator review's older “586 hardware gravity rows still need carriers” language means no proven mechanical carrier/path; later c11 code maps/applies their source wrenches but does not validate mechanics. |
| [c11 method/model reassessment](c11-method-model-reassessment-2026-09-29.md) and [feasibility plan/oracle](next-gate-feasibility-plan-2026-09-29.md) | Reassessment `e80e41c061a37da01b11f34cb00c1a6aefb8b6b6d545956cc4257e44da732a0a`; feasibility plan `1d0162a17071db7e029dc8d893dc41ce3f55ef4991e91f8596923c86d2503812`. The reassessment supersedes the initial native-contact-coupon recommendation; the plan records the 2.23 manual evidence and exact normal/tangent fixture. |
