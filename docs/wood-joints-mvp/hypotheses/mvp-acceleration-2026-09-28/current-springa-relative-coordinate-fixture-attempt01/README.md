# Two-body relative-coordinate SPRINGA known-answer fixture

This input-only fixture checks whether a nonlinear SPRINGA force on a relative
coordinate transfers as equal and opposite actions to two moving body DOFs
through the nested MPC pattern intended for the adapter. Each body has an
independent linear SPRING2 support to a separate fixed endpoint. The SPRINGA
endpoint at a 100 mm initial X span is a numerical carrier; its grounded
endpoint is not a floor or physical support.

The kinematic chain is explicit:

| Slave coordinate | Equation |
| --- | --- |
| Support A endpoint `SA` | `u_SA = u_A` |
| Projection A `PA` | `u_PA = u_A` |
| Support B endpoint `SB` | `u_SB = u_B` |
| Projection B `PB` | `u_PB = u_B` |
| Relative SPRINGA endpoint `Q` | `u_Q = u_PB - u_PA` |

Every slave uses X DOF as the first term of its own homogeneous `*EQUATION`.
The support spring endpoints are distinct from the projection ghosts, and no
spring endpoint DOF is shared by another element. All Y/Z displacements are
fixed. `Q` begins at X=100 mm, its grounded endpoint `GQ` at X=0; therefore
`length - initial_length = u_Q = u_B-u_A` while the span stays positive.

The supports have `k_A=100 N/mm` and `k_B=200 N/mm`. The SPRINGA table encodes
`f=50 max(q,0) N`, with `q=u_B-u_A` in mm. Its table covers elongations from
-10 to +10 mm; the expected range is only -9/20 to +9/35 mm. At an exact
zero table knot, pinned CalculiX 2.23 selects the right-hand interval, so this
sign convention gives the closed-side tangent of +50 N/mm at the contact
kink. It needs no preload or stiffness regularization. The numerical
100 mm carrier span does not represent a timber, bolt, screw, or floor
dimension.

This sign choice follows the pinned 2.23 `ident.f` interval rule: at a table
knot it selects the interval beginning at that knot. The nonlinear force and
tangent implementation comes from the unmodified upstream source recorded in
the [2.23 build manifest](../../evaluation-resume-2026-09-24/calculix-2.23-upgrade-attempt01/build_manifest.json).

Each step uses the exact option line `*STEP,NLGEOM,NLGEOM=NO,INC=40`. In the
pinned 2.23 `steps.f` parser, the flag first selects iterative Newton solving;
the following `NLGEOM=NO` option then turns geometric effects off, leaving
material nonlinearity and the spring-law iteration active. This is a source-
based expectation for the unusual combined syntax, not an observed result in
this input-only packet. The pinned `steps.f:156-185` processes the two options
sequentially, while `calinput.f:1815-1822` emits the final Newton/geometric
status messages. `assess.py` requires the run to report Newton-Raphson
active, report geometric effects off in all three steps, and never report
nonlinear geometric effects active before treating this option check as
passed.

The hand equations use native generalized internal spring forces
`s_A=100 u_A`, `s_B=200 u_B`, and `f=50 max(q,0)`. Since `q=u_B-u_A`, the
relative law contributes `-f` to A and `+f` to B in the internal force
equations. Its physical actions on the bodies are `+f` on A and `-f` on B.
For the closing load pair `(-30,+30) N`, solving
`-30=100u_A-f`, `+30=200u_B+f`, and `q=u_B-u_A>0` gives:

| State | Applied loads `(A,B)` N | `u_A` mm | `u_B` mm | `q` mm | SPRINGA internal `f` N | Physical joint action `(A,B)` N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Closed, step 1 | `(-30,+30)` | `-6/35` | `3/35` | `9/35` | `90/7` | `(+90/7,-90/7)` |
| Open, step 2 | `(+30,-30)` | `3/10` | `-3/20` | `-9/20` | `0` | `(0,0)` |
| Closed, step 3 | `(-30,+30)` | `-6/35` | `3/35` | `9/35` | `90/7` | `(+90/7,-90/7)` |

The support generalized endpoint forces are `(-120/7,+120/7) N` in the
closed steps and `(+30,-30) N` in the open step. The assessor checks their
native SPRING2 endpoint RF pairs, the SPRINGA endpoint RF pair against the
signed table law, every displacement/MPC answer, and separate force closure
for bodies A and B using recovered physical support and joint actions. It does
not treat the `GQ` reaction as a physical floor reaction.

`prepare.py` writes the un-frozen `model.inp` and `model.json` in this packet
root. They remain inspectable inputs; this packet currently has no `native/`
freeze or execution output. The pinned CalculiX 2.23 manual is
[`fea/generated/ccx_2.23.pdf`](../../../../../fea/generated/ccx_2.23.pdf),
SHA-256 `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.
Relevant sections are 6.2.42 SPRINGA, 7.122 SPRING, and 7.56 *EQUATION
(pp. 504-505).

This is a method coupon only. It does not model a frame, joint geometry,
floor-stick rule, connection stiffness or capacity, or design acceptance.
Parent owns exact freezing, preflight/readiness, serialized launch, and result
review under the one-launch/60-second budget.


## Parent native result

The separately scoped, frozen single launch returned 0 and is terminal.
Freeze SHA `846eace6101106839b4382568afb4df4a1f0da5301ed18e049adb78333ca4231`.
`assess.py` passes all three known answers, native endpoint force laws,
physical A/B force closure and nested projection/relative constraints.
The runtime reports Newton active with geometric effects off for all three
steps, substantiating the pinned-source step-option interpretation.

Independent `parent_check.py` checks every one of the 18 printed converged
increments against the closed-form 2x2 solution or open supports: maximum
body force residual 4.01e-6 N; physical global balance residual zero. The
numerical SPRINGA grounded endpoint is excluded from physical external
reaction accounting. It has a nonzero RF on the closed steps and would
produce a spurious global force if counted as a real support.

This verifies scalar nested-MPC carrier transfer for the intended native
method. Frame geometry, normal bearing, exact floor reactions and current
corner capacity remain unverified by this fixture.
