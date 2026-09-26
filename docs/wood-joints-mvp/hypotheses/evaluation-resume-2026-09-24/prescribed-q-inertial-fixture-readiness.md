# Prescribed-q inertial fixture readiness

The direct prescribed-MPC fixture does not establish inertial loading of a
free physical coordinate. Its dependent-node velocities are reconstructed
correctly, but a later two-mass version left the independent mass stationary
when the other, mass-bearing node was driven through the inhomogeneous MPC.
Treat that boundary pattern as unvalidated for dynamic joint work. CCX 2.21
`dynresults.f` reconstructs dependent velocity from independent velocity and
prescribed boundary history; `resultsini.c` similarly updates dependent
velocity and acceleration with the Newmark parameters. Those output/state
updates do not prove that an affine dependent-mass acceleration contributes to
the reduced active equation.

The finite-actuator [attempt 03](prescribed-q-native-spring-actuator-attempt03/)
provides a defensible scalar dynamic benchmark. Its two mass-bearing physical
x coordinates remain independent. A massless proxy obeys
`q_proxy = (u1-u2)/s`; a separate massless target node has the prescribed
history and is connected to the proxy by a real linear actuator spring. This
leaves the common translation free, adds no ground restraint, and drives the
physical pair through equal-and-opposite spring forces. It is a finite-stiffness
actuator test, not exact prescribed joint motion: report both `q_target` and
`q_actual=(u1-u2)/s`, and include actuator compliance in every interpretation.

For masses `m1=0.001`, `m2=0.002 N·s²/mm`, physical joint spring `k=1 N/mm`,
scale `s=33.49590462574`, and actuator stiffness `Ka=100000 N/mm`, the oracle is

`Mq*q_actual'' + (Kq+Ka)*q_actual = Ka*q_target`,

where `Mq=(m1*m2/(m1+m2))*s²=0.747983751 N·s²/mm` and
`Kq=k*s²=1121.975627 N/mm`. The target force is
`Ft=Ka*(q_target-q_actual)`. Its sign and scale match the printed reaction at
the target spring node in all three accepted states. The physical displacements
and velocities also obey zero total momentum and the expected mass ratio.
The solver outputs match the discrete alpha-zero Newmark recurrence at the
frozen 0.01 s knots. This confirms active-coordinate inertial coupling and
target-reaction mapping for this fixture; it does not validate a wood joint.

The 0.01 s attempt 03 steps are far too coarse for continuous force or work
accuracy. The actuator system's natural period is about 0.01709 s, so that run
has fewer than two increments per period. Against the independently propagated
continuous piecewise-linear target history, the discrete first-knot
`q_actual` error is −32%, and target-force sign is reversed at knots 1 and 3;
cumulative target work differs by −16%, +41%, and +12% at the three knots.

The refined [attempt 04](prescribed-q-native-spring-actuator-attempt04/) uses
0.0001 s steps and 300 accepted states. Its complete U/V and target-reaction
histories match the discrete Newmark oracle within output precision; momentum
and independently reconstructed controller-work/energy close at every state
within propagated print bounds. Against the continuous solution, maximum
`q_actual` error is `4.06e-8 mm` (0.01171% of the sampled response infinity
norm), and maximum target-force error is `0.00406 N` (0.04579%). The final
controller work is `0.000707928702 N·mm`. The [independent audit](spring-actuator-validation-attempt01/README.md)
records the exact comparison. This resolves the scalar fixture's active
inertia, force-sign, and work-accounting method. Choose actuator stiffness and
step size together for any separate joint case, keep target knots exact, and
re-establish response and work accuracy for that case.

Do not use the native `KE` or external-work totals from these point-mass runs
as the audit. The run prints both as zero. In the official CCX 2.21 source,
`calcenergy.f` accumulates energy for supported element integration points and
skips unrecognized element types such as `MASS`; compute physical kinetic
energy from the pinned masses and FRD `V`. Integrate target reaction against
target motion and reconcile it with physical kinetic energy, joint-spring
energy, and actuator-spring energy. In this benchmark the discrete trapezoidal
controller work closes the Newmark energy balance; that closure must be
rechecked after time refinement. The target node is an actual spring endpoint,
so its reaction is the actuator force; do not substitute the proxy's MPC
reaction or the direct-MPC dummy-node `RF`.

Disposition: the scalar finite-actuator path is validated as a bounded
numerical diagnostic. A separate current-joint run can use it if its freeze
preserves the physical mass degrees of freedom and explicitly binds actuator
stiffness, actual `q`, target `q`, and time resolution. Recheck force/work on
the joint model. The scalar result does not establish an intrinsic joint
stiffness, service response, or capacity. Source reference: [official CCX 2.21
source archive](https://www.dhondt.de/ccx_2.21.src.tar.bz2), SHA-256
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`.
