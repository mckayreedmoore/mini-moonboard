# c11 method/model reassessment

Date: September 29, 2026  
Lane: `compact-floor-flush-wood-joints-development`  
Reviewed model: `led-clearance-2x6-runner-seated-blocks-v1`  
Scope: read-only reassessment of c11 r1; no model, geometry, deck, response,
or native-run ledger changes were made.

## Finding

c11 is an internally equilibrated solution of one frozen, linear contact
branch. It is not a complementarity-consistent response of the compression-only
contact model. The saved independent postrun audit passes 15/15 evidence
checks and reproduces all 21 response fields, but numerical checks and
mechanical acceptance remain false.

The evidence does not identify a sign error in the branch selector. The
selector uses the expected local zero-gap rule: retain an active normal when
its opening is at most `1e-7 mm`, and activate an inactive normal when its
penetration is more than `1e-7 mm`. The c10-to-c11 transition used DAT
displacement intervals, had no rounding-ambiguous decisions, and was
independently reproduced. c11 nevertheless has four active contacts opening
with tensile normal force and two inactive contacts penetrating. Each failure
is outside the saved displacement-rounding interval and the branch tolerance.

This sequence establishes nonconvergence of the consumed branch history, not
that a physically consistent contact solution is impossible. Exceptions fell
from 501 in c00 to 3 in c10, then increased to 6 in c11. The active-set
history checker prevents an exact repeated active set; it does not establish a
convergence bound or guarantee a fixed point. Do not continue with c12 under
the spent c11 run budget.

## Exact c11 exceptions

`opening_mm` is positive for separation and negative for penetration.
`compression_force_n` is the signed force under the compression-only
convention; a negative force on an active spring means that the linear branch
is pulling in tension.

| Contact | Frozen state | Interface | Opening (mm) | Signed normal force (N) | `|opening| / 1e-7 mm` |
|---|---|---|---:|---:|---:|
| `contact_8_1` | Active | `base_header` / `base_post_center_left` | +0.000029450 | −3.918742 | 294.5 |
| `contact_29_4` | Active | `base_post_center_right` / `kicker_right` | +0.000014235 | −2.149889 | 142.35 |
| `contact_41_2` | Inactive | `base_principal_center_left` / `left_service_inner_upper_cleat` | −0.000069100 | 0 | 691 |
| `contact_89_1` | Active | `base_side_left` / `knee_outer_left_inner_frame_block` | +0.000006000 | −2.741521 | 60 |
| `floor_base_floor_left_0` | Inactive | `base_floor_left` / floor | −0.001364782 | 0 | 13,647.82 |
| `floor_base_floor_left_5` | Active | `base_floor_left` / floor | +0.001641732 | −298.864916 | 16,417.32 |

For the four active failures, the independent force-recovery audit confirms
endpoint RF action/reaction and agreement with the `k*deltaU` force intervals.
For the two inactive failures, the spring force is zero while the recovered
relative motion is penetration. The transition’s zero DAT interval ambiguity
and these response checks rule out printed-displacement rounding and force
postprocessing as explanations for these six signs.

Raw and rounding-interval global equilibrium pass. All 50 body raw and interval
balances, MPC checks, 170/170 tie checks, and spring-force recovery pass. Those
checks verify the selected linear branch and accounting; they do not override
the six invalid contact states.

## Floor support consequence

The c11 floor cells are especially important because the development model
assumes no slip only while an individual floor cell bears. In c11,
`floor_base_floor_left_5` is active with a tensile normal force of
`−298.8649 N`, yet its paired active no-slip tangent springs carry
`[6.62113, 328.4595, 0] N`, or `328.5262 N` transverse shear. The paired
`floor_base_floor_left_0` normal cell is inactive while penetrating; its
tangent springs are off. Thus this c11 branch carries substantial conditional
no-slip reaction at a cell that fails the assumed bearing condition, while
another floor cell penetrates without support.

This is not isolated to c11. In c09, active `floor_base_floor_left_11` carried
`−272.9226 N` normal tension and `494.8446 N` tangent shear. In c10, active
floor-left cells 7 and 9 carried `−27.9051 N` and `−235.2607 N` normal
tension, with `66.5752 N` and `402.6181 N` tangent shear. The changed branches
move the failed floor state between cells; they do not establish a stable
conditional stick response. Do not use these floor tangent reactions as
accepted support demands.

## Method diagnosis

The c11 deck is a `*STATIC` linear branch made from `SPRING2`/`*SPRING`
connectors. It contains no native `*CONTACT PAIR` or `*SURFACE INTERACTION`
cards. A contact-cell stiffness is currently assigned as
`100 N/mm^3 * cell_area`; the value is a numerical scenario parameter, not a
measured timber or floor stiffness. Contact springs are active or omitted in
each frozen deck, then their status is selected externally from the previous
branch’s displacement. A spring in an active branch can therefore carry
tension until another branch is assembled and solved.

The contact geometry discretizes each exact opposed face into area cells and
uses each cell’s centroid movement to preserve uniform-traction resultants.
It does not resolve local pressure peaks. Consequently, a successful branch
would still need local bearing and resistance screens before it could support
joint acceptance.

The c11 evidence is consistent with an incomplete fixed-point iteration over
these externally selected linear branches. It cannot distinguish that
nonconvergence from inadequate stiffness/engagement assumptions or actual
separation of a modeled interface. It does show that equilibrium, an exit-0
solver status, or the passing evidence audit is insufficient for interpreting
the six-case joint demands.

## Initial recommendation (superseded) and current next gate

**Supersession note, September 29, 2026:** The initial recommendation below
to evaluate native CalculiX 2.23 as the first contact-method candidate is
superseded by the pinned-manual/source review. Stock 2.23 has no frictionless
tangential reaction; `*FRICTION` requires positive `μ` and stick slope, while
`PRESSURE-OVERCLOSURE=TIED` ties across gaps and carries tensile normal action.
These do not implement the owner's conditional no-slip-while-bearing floor
assumption. The existing known-answer coupon already validates normal contact
and `CF`/`CFN`/`CFS` output, so no new CCX contact coupon is planned. The current
task is the read-only Option A/Option B comparison in the
[next-gate feasibility plan](next-gate-feasibility-plan-2026-09-29.md).
Option A replaces c11's finite paired floor `SPRING2` tangents with ideal
conditional tangential constraints; this is a new formulation requiring a
new analysis revision and exact freeze, explicit initial/re-engagement
tangent references, and no transfer of c11 floor tangent reactions or
demands.

The original proposal below is retained as history only; it is not the next
work order.

Do not derive another c12 branch. Before any new frame run, review a single
known-answer test of a method that solves normal contact and the conditional
floor stick state together. The test should exercise open, engage, release,
and opposite-side selection, recover the expected normal reaction and gap,
and verify that no tangential floor reaction remains when its normal contact is
open. Keep the floor no-slip condition explicitly conditional; do not add a
friction coefficient, floor test, or anchor claim that the evidence does not
support.

The original low-port-cost candidate proposal was native CalculiX 2.23 contact
on source-mapped face surfaces, because c11 already uses that solver but never
invokes its native contact formulation. As recorded in the supersession note,
this remains only a normal-contact capability reference, not a proposed
conditional floor-stick solution. The pinned [CalculiX 2.23 user
manual](https://www.dhondt.de/ccx_2.23.pdf) documents node-to-surface,
surface-to-surface, and mortar contact; it also says contact pairs in one deck
must use a consistent method and recommends face-to-face or mortar over
node-to-face for contact between faces. This is a candidate for a known-answer
test, not a selected production method. The test must establish the
appropriate surface method for this mesh, force/gap extraction, and the
conditional no-slip coupling before a new full-frame plan is considered.

If native contact cannot represent the specified conditional floor stick
without an unsupported finite friction assumption, the next candidate should
be a reviewed complementarity formulation for the existing reduced spring
system. Code_Aster remains a possible comparison solver, but its current
curved-contact work has unresolved local pressure/residual extraction and is
not a drop-in answer for this model.

Any future native run requires a separate bounded plan and one-run budget,
parent-owned exact freeze/readiness, independent pre-run review, and explicit
parent authorization. It must preserve the c11 false result and all earlier
candidate evidence. Do not release the radial fixture, source-clearance pilot,
or six-case work until the new method passes its fixture and the coupled
contact state is independently verified.

## Evidence bindings

| c11 record | SHA-256 |
|---|---|
| Freeze | `1633e79900afd194ece79c7463a7b383a11bb96920e7449e6a25c528e933b8e2` |
| Model | `d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0` |
| Deck | `42a2527eda91c1c56933c00b8429dc37e3d02dba842798fc1eb616b299027ef1` |
| Response | `b8558fbaa986ff251008da629c21d8d9a56e16c965ce09476e94a688f0a9f878` |
| Independent postrun audit, 15/15 | `0c6c7b8601a8b15cd46901c912934483b5da14babb84380a9301c0730cdb18ed` |
| c10 response | `923c753cb6a32e84f40150b65e178ced70d4c104bea3a350f7cc30cabb389137` |
| c10 independent postrun audit | `ee520a5eafc737a54530e13c1348fd2abacadb9a724e91ff7e4b92094ea69566` |
| c09 response | `caa2f520636a0a227c425416ca88fc503f7d4f1fc8b06e2fafac832bac9aaf90` |
| c09 saved postrun audit | `7e3581c01e71981a27782fb6b4bc4279f41e51933063db3af49c6db5ac7cb061` |

Supporting code: [`wood_joint_reduced_trial_review.py`](../../../../fea/wood_joint_reduced_trial_review.py),
[`wood_joint_reduced_model.py`](../../../../fea/wood_joint_reduced_model.py),
[`wood_joint_reduced_connections.py`](../../../../fea/wood_joint_reduced_connections.py),
and [`horizontal_panel_frame.py`](../../../../fea/horizontal_panel_frame.py).
