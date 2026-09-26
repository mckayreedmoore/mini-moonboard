# Finite actuator: dynamic implementation and time refinement

The two-mass fixture retains both physical mass coordinates and uses a
massless dependent proxy for q. A separate spring connects that proxy to a
prescribed, massless target. This formulation reproduces the analytical
inertial motion and provides an observable controller force, unlike the
[earlier directly prescribed physical-MPC fixture](../prescribed-q-native-two-mass-attempt01/pilot.inp).
It does not validate a current joint, contact law or physical thread engagement.

Masses are .001 and .002 N·s²/mm, the inter-mass spring is 1 N/mm,
u1−u2=33.49590462574 q, and actuator stiffness Ka is 100000 N/mm.
Both physical X coordinates are free; only unused transverse coordinates
are constrained. The exact scalar equation is
`Mq*qddot + (Kj+Ka)*q = Ka*qtarget`, with
Mq=0.7479837511 N·s²/mm and Kj=1121.975626697 N/mm.
The prescribed target rises through .0001/.0003 mm then returns to .0002 mm
at .01/.02/.03 s. Actual q is a response and need not equal its target.

The [audit](audit.py) checks frozen native inputs and output hashes, actual
material/MPC/control cards, accepted status rows, complete U/V/RF records,
and the independent discrete Newmark oracle. In both cases the physical
motion, proxy q and target RF match that oracle within native output
precision. RF at the target equals Ka*(qtarget−q); the proxy RF is opposite.
Physical total momentum remains zero within printed-velocity bounds.

The prescribed target velocity is checked separately against the Newmark
recurrence `v_n = 2*(U_n-U_previous)/dt - v_previous`, starting from zero.
It oscillates around the piecewise-linear displacement slope on these
fixtures; it is not that continuous slope. The audit propagates printed
displacement bounds through this recurrence. The target is massless, and
controller work uses target displacement increments, so its reported velocity
is used for neither kinetic energy nor work.

Controller work is reconstructed from target RF against target displacement.
It equals the change in physical kinetic energy plus joint spring energy
plus actuator spring energy within propagated output-rounding bounds at
every accepted state. The actuator energy must remain separate from joint
energy. CCX prints zero point-MASS kinetic energy and zero external work on
these fixtures, so those native summaries are not used for this closure.
The earlier dummy-node RF shortcut remains invalid.

| Check over each case's output times | Coarse .01 s | Refined .0001 s |
| --- | ---: | ---: |
| Accepted states, no rejected attempts | 3 | 300 |
| Maximum q error against exact continuous solution | .0001260628 mm | 4.0626702e-8 mm |
| q error / exact sampled field infinity norm | 43.9564% | .0117100% |
| Maximum controller force error | 12.60628 N | .00405867 N |
| Force error / exact sampled field infinity norm | 314.4101% | .0457937% |
| Reconstructed final controller work | .000792014725 N·mm | .000707928702 N·mm |

The continuous reference is an independent exact piecewise-linear-forcing
oscillator solution, not the discrete oracle. Coarse native convergence and
work balance alone conceal a severe time error. Refinement resolves that
error for this fixture and history; it does not prescribe the timestep or
actuator stiffness for the current joint. No structural threshold is inferred.

DAT precision bounds use decimal rounding. FRD bounds additionally include
the binary32 conversion in CCX 2.21 `frdvector.c` before decimal printing,
source SHA-256 `2dabcb51ae3cbad1bb43353b6db0f9fc36a72f4b30dc9173d872b0c4bff2001c`.
Source archive SHA-256 is
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`.
The independent check does not use an extra mechanics tolerance to hide
rounding mismatches. Ruff and formatting checks pass.

Report SHA-256: `e14b379e64c214e8e09f4aa151151ddf15d1c6f885b0424f130529feeac98b77`.
Audit SHA-256: `08a78823d3be0c875d67795860be21d5027df5982ef66ebf3da33f1325389165`.
The [coarse case](../prescribed-q-native-spring-actuator-attempt03/execution.json)
and [refined case](../prescribed-q-native-spring-actuator-attempt04/execution.json)
retain their separate freezes and native output inventories.
