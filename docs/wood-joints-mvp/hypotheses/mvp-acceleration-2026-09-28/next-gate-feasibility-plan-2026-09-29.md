# Next-gate feasibility plan

Date: September 29, 2026  
Lane: `compact-floor-flush-wood-joints-development`  
Reviewed revision: `led-clearance-2x6-runner-seated-blocks-v1`

Status, September 29: the bounded A/B comparison is recorded in
[option-ab-method-selection-2026-09-29.md](option-ab-method-selection-2026-09-29.md).
It recommends Option B preflight only. No current member or joint demand is
accepted. An independent Luna Max cold review found no blocking correction;
parent independently checked its cited hashes and links. This plan authorizes
no implementation or solver run.

## Recommendation

The completed read-only method-selection stage recommends the route-to-MVP
conventional frame-demand/code-check approach, limited to a demand-coverage
preflight because current artifacts contain no accepted member or joint
demand subset. Parent retains exact model readiness, any new plan or run
budget, native execution, and final validation. This handoff authorizes no
solver run or model change.

Option A is a material formulation change: replace the finite, paired floor
`SPRING2` tangents in the current reduced model with ideal tangential
constraints that activate only when the associated normal floor contact bears.
This is the direct mathematical form of the owner's explicit no-slip-while-
bearing assumption; it is not a physical friction law. It requires a new
candidate analysis revision and exact freeze. The initial stick reference and
the reset rule on every re-engagement must be defined and reviewed first.
Proposed rule for the feasibility check: at first bearing, record the current
relative tangent position as the episode reference and hold it fixed while
normal reaction stays positive; release tangent constraints when open, and
record a fresh reference at each re-engagement. Test that reset in the
analytical fixture before considering the full frame.
None of c11's finite-spring floor tangent reactions or demands transfers to
that formulation.

Stop pursuing another CalculiX contact coupon for conditional floor stick. The
pinned CalculiX 2.23 manual says its optional `*FRICTION` law uses a positive
friction coefficient `μ` and a positive stick slope `λ`; it relates shear to
relative tangential movement and caps shear at `μp`. With no friction law,
the pinned source sets the tangential stiffness contribution to zero. The
manual's `PRESSURE-OVERCLOSURE=TIED` instead ties slave faces even across a gap,
allows tension as well as compression in the normal relation, and requires a
stick slope. `*TIE` likewise is not a unilateral, bearing-conditional
constraint. None represents the requested idealized rule—zero tangential
slip only while a floor cell bears—without adding an unsupported friction
assumption or changing the boundary condition.

This is a method stop, not a finding against the physical frame. The existing
[normal-contact coupon](../evaluation-resume-2026-09-24/contact-penalty-touch-work-known-answer-attempt01/RESULTS.md)
already passes open/touch/compress/reopen and pair `CF`/`CFN`/`CFS` checks.
Its verifier hash is `6becb6d9c4cc875bcb06379078e97f86c2108318ef3df76a20f6b3c8be693bcd`.
The c11 branch remains false: its [response](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/response.json)
hash is `b8558fbaa986ff251008da629c21d8d9a56e16c965ce09476e94a688f0a9f878`;
the [independent postrun audit](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1-postrun-review/independent-postrun-review.json)
hash is `0c6c7b8601a8b15cd46901c912934483b5da14babb84380a9301c0730cdb18ed`.
That audit passes evidence accounting, while six contact signs fail and
mechanical acceptance remains false. Do not create c12 or transfer c11 demands.

The source basis is the exact pinned [2.23 PDF](../../../../fea/generated/ccx_2.23.pdf)
(also published [upstream](https://www.dhondt.de/ccx_2.23.pdf), SHA-256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`),
manual entries `*FRICTION` and `*SURFACE BEHAVIOR`, and the official 2.23
source archive pinned at
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
The source members `frictions.f` and `getcontactparams.f` have SHA-256
`ec7b3b2e2cd8f7168d891ce1e05342eed7ca515316cd433f0ca1bf27322eee2a` and
`03384b3d55deb22010f19a4521f3b10380caaf16441d270bf35f886ec0aadbaa`.
The local contact-method screen and source lock are in
[`contact-formulation-method-screen.md`](../evaluation-resume-2026-09-24/ordinary-external-force-transient-attempt04-diagnostic/contact-formulation-method-screen.md)
and its adjacent `diagnostic-lock.json`.

## Completed comparison and next parent gate

The [comparison artifact](option-ab-method-selection-2026-09-29.md) and its
independent cold review are complete. The next safe work, if parent assigns it,
is a read-only six-case demand-coverage register identifying any
path-complete, equilibrium-checkable member/joint subset. Do not edit source,
deck, geometry, or saved results; do not invoke CalculiX or Code_Aster.

The comparison must answer these two options against the same reviewed
six-case loads and geometry:

| Option | Required assessment | Decision use |
|---|---|---|
| **A. New coupled complementarity formulation** | Replace, rather than inherit, the current finite paired floor `SPRING2` tangents with an ideal `Δu_t = 0` constraint while normal reaction is positive; release it on opening and require zero tangent reaction. Keep the existing normal penalty scenario. Define initial and re-engagement tangent references; assess branch uniqueness and a bounded solve guarantee. | If feasible, propose a new analysis revision, exact freeze, one analytical known-answer fixture and a separate parent-reviewed implementation plan. No c11 branch iteration or reaction transfer. |
| **B. Conventional whole-frame static demands plus code checks** | Identify frame and joint demands available from beams/frame elements, source geometry, and the six existing cases. The c11 solid builder source-maps/distributes self-weight, but a beam model still needs member line loads and section-force recovery. Distinguish source-mapped hardware wrenches from proven mechanical transfer. Keep floor support and panel withdrawal paths explicit. | Advance only a path-complete, equilibrium-checked subset. Current artifacts contain load inputs and path screens, not accepted member/joint actions. Do not report complete six-case demands until the chosen frame model represents support, member-weight distribution, panel withdrawal, receiver paths, and other governing actions. |

For Option A, the read-only comparison must include this hand-solvable fixture
oracle before any full-frame/native run. Use N and mm; `g_n > 0` means open,
`N = k_n max(0, -g_n)`, and each normal cell has area `1 mm²`, hence
`k_n = 100 N/mm`. This is the current numerical penalty scenario, not measured
floor stiffness. Use the global floor plane `Z=0`, with normal/upward `+Z`;
apply the positive-magnitude downward load `P` in `−Z` at the fixture origin
so `P` adds no moment. In the normal-only subfixture, place cells at
`r_L = (−100,0,0) mm` and
`r_R = (+100,0,0) mm`. Let `M_ext,y` be the applied right-hand-rule couple
about global `+Y`. Report the following exact states; the listed external
load and couple close the contact reactions for each prescribed-gap state:

| State | `g_L`, `g_R` (mm) | `N_L`, `N_R` (N) | Downward load `P` (N) | Applied couple `M_ext,y` (N·mm) |
|---|---:|---:|---:|---:|
| Open | `+0.10`, `+0.10` | `0`, `0` | `0` | `0` |
| Both bearing | `−0.05`, `−0.15` | `5`, `15` | `20` | `+1000` |
| Released | `+0.03`, `+0.02` | `0`, `0` | `0` | `0` |
| Left only | `−0.05`, `+0.02` | `5`, `0` | `5` | `−500` |
| Mirrored, right only | `+0.02`, `−0.05` | `0`, `5` | `5` | `+500` |

Use upward-positive reactions and define force closure as
`P − N_L − N_R = 0`. The contact reaction moment about `+Y` is
`100(N_L − N_R) N·mm`, so moment closure is
`M_ext,y + 100(N_L − N_R) = 0`. These rows check opening, engagement,
release, and mirrored unilateral support selection without treating contact
cells as qualified floor stiffness.

For the tangential subfixture, use a single floor cell at the global fixture
origin `r = (0,0,0) mm`, with normal `+Z` and orthogonal tangent axes `+X` and
`+Y`. Apply the normal load, both tangent loads, reference-spring reactions,
and contact reactions at this same origin. Use a linear reference spring of
`20 N/mm` on each tangent axis and a tangential contact reaction only while
`N > 0`. These reference springs are fixture devices for a hand-solvable load
path, not floor stiffness or candidate model parameters. Record the episode
reference at first bearing and reset it at re-engagement. The expected values
are:

| Stage | `g_n` (mm), `N` (N) | Applied `(H_x,H_y)` (N) | Reference / displacement `(u_x,u_y)` (mm) | Contact `(T_x,T_y)` (N) |
|---|---|---:|---:|---:|
| First bearing, zero tangent load | `−0.05`, `5` | `(0,0)` | ref `(0,0)`; `u=(0,0)` | `(0,0)` |
| Stick under load | `−0.05`, `5` | `(5,3)` | ref `(0,0)`; `u=(0,0)` | `(−5,−3)` |
| Open / tangent release | `+0.03`, `0` | `(5,3)` | ref `(0,0)`; `u=(0.25,0.15)` | `(0,0)` |
| Re-engage / reset reference | `−0.02`, `2` | `(7,1)` | ref `(0.25,0.15)`; `u=(0.25,0.15)` | `(−2,+2)` |
| Open again | `+0.03`, `0` | `(7,1)` | ref `(0.25,0.15)`; `u=(0.35,0.05)` | `(0,0)` |

On each axis the reference spring reaction is `S = −20u`; verify
`H + S + T = 0`. Thus the rows have zero tangent slip while bearing, free
motion of `(0.25,0.15) mm` while open, zero incremental motion immediately
after re-engagement, then free motion of `(+0.10,−0.10) mm` after reopening.
Because every force in this subfixture acts at `r=(0,0,0)`, its moment about
that origin is zero; match normal `P=N` with no applied couple. An inactive
normal contact must carry zero tangent reaction. The fixture is a design/review
artifact now, not an authorization to run it.

The comparison recommends Option B preflight only; it does not report a
path-complete demand subset. Do not hide an unsupported law inside a stiffness
value, friction coefficient, high-`μ` approximation, permanent tie, or
arbitrary restraint.

These are separate integration blockers, not one generic floor-contact issue:

| Blocker | Current evidence and limit |
|---|---|
| Conditional no-slip floor support | CalculiX 2.23 cannot supply ideal bearing-conditional stick without unsupported positive `μ`; Option A is a new mathematical formulation. Keep floor-dependent reactions unresolved until it is verified. |
| Panel outward tension | The six frozen cases have outward panel-normal resultants before gravity of A12 rear 1,659.44 N; A12 forward 1,199.82 N; A12 left 1,429.63 N; K12 right 1,429.63 N; K12 rear 1,659.44 N; and A1 rear 1,659.44 N. The 66 Hillman 42605 axes currently carry lateral resistance only; withdrawal stiffness and resistance are unsupported. See [panel-withdrawal-preflight.md](panel-withdrawal-preflight.md). |
| Receiver-to-frame path | The independent [coordinator handoff review](COORDINATOR-HANDOFF-REVIEW.md) found 117 opposed planar patches across 115 pairs, six zero-area or unresolved pairs, and open center-kicker receiver paths. The frozen c11 builder maps the 586 non-member hardware gravity sources into 760 receiver-body wrenches, preserving source force and first moment. That assignment does not validate carrier stiffness, real force sharing, or complete receiver-to-frame mechanics. |
| Self-weight for internal bending | The frozen c11 solid builder distributes the 50 member/panel self-weight sources as consistent body gravity and closes its one-case load accounting. A conventional beam model still must apply member weight along its beam representation and verify section-force recovery. A centroid resultant or source mass inventory alone cannot establish beam bending demand. |

The findings describe current model omissions, not proof of physical failure.

Decision tree:

1. If Option A has a bounded, independently checkable solve and its analytical
   fixture passes review, ask parent to scope the new analysis revision, exact
   freeze, and implementation. Define and verify the initial/re-engagement
   tangent reference before any six-case run.
2. If Option A fails but Option B can produce closed, defensible demands for
   a subset of member/joint checks, advance only that subset. The completed
   comparison finds that current artifacts do not yet show such a response
   subset; begin with a read-only demand-coverage register. Keep conditional
   floor support, beam self-weight distribution, panel withdrawal, receiver
   paths, and other exceptions separately marked; none is the only blocker.
3. If neither option yields defensible loads, stop both and report each exact
   support/load-path fact preventing the MVP demand table. Do not switch to a
   new contact solver or resume c11 iteration by default.

## Pass, fail, and stop gates

**Pass the planning gate** only when an independent reviewer confirms that the
[comparison](option-ab-method-selection-2026-09-29.md) preserves reviewed
geometry and loads, identifies Option A as a new formulation, defines its
initial and re-engagement tangent references, states both support laws without
conflation, records all four named blocker groups and other readiness
exceptions, and verifies the analytical fixture oracle above. Parent then
decides whether to make a new candidate revision and bounded plan.

**Fail Option A early** if the reduced system cannot enforce normal opening /
bearing and conditional ideal stick together, if active-set cycling or
non-uniqueness has no bounded resolution, or if the fixture cannot distinguish
open, engaged, and released states. Do not tune penalty stiffness to force a
pass. **Fail Option B for floor-dependent acceptance** if it needs reactions
at open floor patches, omits a load path, or assumes a restraint not in the
reviewed boundary condition. These failures preserve useful conditional
results but do not produce accepted demands. Option B cannot pass the complete
six-case gate while the floor support, panel withdrawal, receiver-to-frame
paths, or the chosen frame model's member-weight response remain unresolved.
The c11 solid weight map does not discharge a beam model's line-load and
section-force requirement.

**Hard stop:** no c12, radial fixture, source-clearance pilot, six-case native
run, or solver substitution follows automatically. Any implementation or
native run needs a separate parent-owned scope, frozen inputs and method,
independent review, fresh budget, and explicit parent authorization. If both
options fail, return a concise unresolved-method decision to parent; do not
restart generic contact iteration. Preserve the 66 Hillman axes, 92 candidate
bolt axes, twelve starting frame bolts, all prior evidence, and the MVP-E
criteria as pending.

## MVP route and current boundary

The agreed acceleration route remains a whole-frame static demand model under
the six specified cases, followed by applicable NDS / product-based
connection checks and targeted local models only for unresolved mechanisms.
It may produce partial results, but not complete six-case joint demands until
conditional floor support, panel withdrawal, receiver-to-frame paths, and the
chosen frame model's member-weight distribution are represented. The c11
solid source map is not beam bending recovery. The Hillman 42605 resistance and axial load-slip stiffness are
not established by its purchase record or by NDS reference arithmetic alone.
The existing [MVP reassessment](README.md#decision) and c11
[method/model reassessment](c11-method-model-reassessment-2026-09-29.md)
define that route and the current failure boundary. A frame demand model may
advance only as far as its support and joint load paths are defensible. The
c11 equilibrium, ties, and force recovery do not supply an accepted frame or
joint response; its six contact failures block that branch, not the broader
static-demand/code-check architecture.

Read [`AGENTS.md`](../../../../AGENTS.md) and the
[coordinator plan](NEXT-COORDINATOR-PLAN.md) as authority. This artifact is a
planning handoff only; root/parent owns the next decision and any execution.
