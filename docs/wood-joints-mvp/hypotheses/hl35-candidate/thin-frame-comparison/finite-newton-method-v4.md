# Generic finite-potential Newton continuation

The new [numerical helper](../../../../../scripts/thin_bolted_finite_newton.py)
evaluates the original finite potential, physical gradient and physical tangent
through the frozen [finite-frame API](finite-frame-method-v4.json). Its
[small-system receipt](finite-newton-method-v4.json) records nineteen focused
fixtures and Ruff. The source remains separate from the frozen first-order
contact continuation: its fixed material matrix and exact quadratic increment
formula are not a finite nonlinear evaluator. This packet executes no candidate
assembly or case and establishes no stability, resistance or release.

The public interface is

```
solve_finite_potential(response, q0, *, quotient=None,
    support_feedback=None, initial_disabled_support_ids=(),
    options=NewtonOptions(), progress=None)
```

`response(q, tangent=True, recover_actions=False,
disabled_floor_support_ids=())` supplies `energy_nmm`, the complete
`gradient_n`, and `hessian_csr`. It is compatible with
`FiniteFramePotential.response`. The initial full state is numerical
initialization only; the solver neither reads a saved case nor transfers
physical acceptance from one. The caller owns model preparation, source-bound
load identity, execution readiness and writing the result. The progress
callback receives evaluation, iteration, trial, gradient-work and recovery
events so the caller can provide regular updates.

Scaled Levenberg steps reuse the frozen `numerical_step.numerical_solve` sparse
backend. With P formed from the reciprocal square roots of the absolute current
reduced Hessian diagonal, the numerical step solves
`(P H P + mu I) z = -P g`, then lifts `P z`. The largest full scaled-coordinate
increment is limited to 100 mm by default. Backtracking uses the original
potential and slope. The physical Hessian supplies the model prediction used
to adapt mu; mu is never added to a physical potential, force, reaction or
resistance. Options and maximum attempted regularization are recorded.

Convergence requires the infinity norm of the complete original generalized
gradient to be strictly below **1e-5 N**. This includes the omitted circular
chart dual and all retained coordinates; a reduced-gradient pass alone cannot
accept a state. No relative force criterion or energy tolerance replaces it.
An unloaded null mode remains free. A stationary nonconvex state may satisfy
equilibrium, so convergence is not a positive-stiffness or stability proof.

Ordinary Armijo tests subtract the published physical energies. If either the
observed difference or predicted decrease cannot be resolved at 32 times the
estimated subtraction scale `4 eps (|E_old|+|E_trial|)`, the comparison uses

```
E(q+delta)-E(q) = integral_0^1 gradient(q+t delta) dot delta dt.
```

The equality is the fundamental theorem for the unchanged conservative
potential along the coordinate segment. The support pattern remains fixed
throughout the integral. The implementation uses
[SciPy QUADPACK integration](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.quad.html),
with absolute tolerance `max(1e-30 N mm, 1e-10 |g dot delta|)`, relative
tolerance 1e-8 and at most fifty adaptive subintervals. QUADPACK's error is an
estimate, not a rigorous bound. A warning or unmet budget rejects the trial.
Armijo compares the increment plus its estimated error with the original
negative slope; no additive energy acceptance allowance is introduced.
The published scalar potential remains unchanged. This integration does not
repair an inconsistent caller-supplied gradient, and it is not invoked when
ordinary subtraction resolves the decrease.

The cancellation fixture publishes 1e20 N mm before and after a near-equilibrium
step. Gradient work resolves an increment -9.999999999988e-7 N mm with error
estimate 1.110e-20 N mm using twenty-one gradient evaluations. The final
physical residual is 2.000e-9 N. Three unilateral activation/deactivation
segments recover known increments 0.75, -0.48 and 0.27 N mm; their largest
error against the known answer is 2.22e-16 N mm. An intentionally unresolved
integration rejects the step and exports no force field.

`CornerSupportFeedback.from_finite_frame(potential)` binds each existing
corner support ID to its own normal contact ID. After a fixed-pattern
equilibrium, the next disabled XY set contains precisely the corners with
normal reaction at or below **1e-7 N**. It does not disable every corner on the
same body, change the floor normal law or qualify no slip. A changed set is
resolved using the same physical potential API and new explicit disabled set.
Repeated patterns, including a return to the initial pattern, fail. The
default limit is ten patterns. The two-corner coupon lifts corner A and retains
corner B on the same body, converging in two patterns with residual
3.125e-7 N. The deliberate two-pattern cycle returns diagnostic state only
and never requests action recovery.

`CircularShaftQuotient(potential.shaft_replacement)` reuses the frozen
[isotropic shaft symmetry and minimal director utility](isotropic-shaft-method-v4.md).
It first removes a common RIGHT material roll at every node of each shaft,
choosing the proved local first-node `theta_x=0` representative. The retained
coordinates parameterize that slice; their full-state embedding is linear,
so its gradient and Hessian are principal restrictions of the original full
physical derivatives. No world rotation component is simply deleted, and no
physical torque support is added. The full dual remains available for force
and moment work and for the original residual test.

The quotient exposes the existing compensated world rigid generators, which
include the common roll needed to remain in the minimal local chart. Its bent
two-element coupon checks the restricted Hessian by differentiation and
reproduces world spatial force/moment work using exact point Jacobians.
The axial solve recovers extension 1.989434799219e-5 mm versus the known
1.989436788649e-5 mm, within the original residual criterion. Its full residual
is 2.000e-6 N; no twist support is present. Material-roll work is monitored at
each evaluated Newton state against an absolute 1e-6 N mm/rad budget or the
larger 128-eps summation scale. A real 5 mm off-axis load breaking that symmetry
fails explicitly. This monitor does not prove gauge compatibility for a new
physical potential: the previously source-checked axial ports/directors and
350 unprojected load-centroid precision bounds remain prerequisites for the
candidate's use of this chart.

The convex two-coordinate coupon recovers (0.05,-0.1) mm to maximum error
1.304e-7 mm, within the 2.609e-7 mm displacement bound implied by the unchanged
force criterion. An unloaded coordinate remains at its arbitrary initial
7 mm value. A double-well coupon starting at 0.1 reaches the positive minimum
1.000000153 with monotonically decreasing physical energy and residual
1.221e-6 N; step regularization reaches 10 without entering its physical
derivatives. These are numerical known answers, not candidate behavior.

Only a stable support pattern and complete force-criterion pass permit final
action recovery. Recovery is checked against the same physical gradient and
published potential. Failures contain `diagnostic_last_q`, residual, scalar
energy and numerical history; they omit accepted `q` and `physical_fields`.
The iteration-cutoff coupon has actual residual 3000 N and exports neither
accepted state nor forces. Invalid initial charts and invalid physical trials
are classified separately; unsupported trials can backtrack, while an
unsupported starting chart fails.

The reproducible producer and commands are pinned in the receipt, which is
created only at a new unused path. Frozen wood, fitting, shaft, finite-frame
and historical continuation bytes are preserved. Independent method review
is required before candidate execution; parent readiness and case provenance
remain separate from these fixtures. This helper, its tests and receipt remain
active numerical integration inputs. Nothing is pruned or archived here.
