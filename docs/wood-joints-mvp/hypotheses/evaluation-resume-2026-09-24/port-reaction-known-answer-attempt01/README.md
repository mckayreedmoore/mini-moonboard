# Port reaction and imposed-work known-answer check

Date: 2026-09-27. This is a native output-method check for the WJ24 study,
not a connection model or joint acceptance result.

## Decision, observation, next step

**Decision:** Compare direct prescribed motion with a generic linear equation
that prescribes only the average motion of a deformable end face. Use a unit
cube with an exact uniaxial solution and the pinned CalculiX 2.21 binary.

**Observation:** The manual's *NODE PRINT/RF caveats and local
`resultsforc.c` show that generic *EQUATION controller RF cannot be presumed
to report actuator force. The source subtracts and restores MPC forces.
The native dynamic external-work accumulator also needs an observed check
for imposed motion. These unresolved interpretations would invalidate work
balance in the expensive joint transient.

**Next step:** Freeze and run four small fixtures serially: static direct,
static average-equation, dynamic direct and dynamic average-equation. Observe
all physical/controller U and RF, dynamic V, end-section SOF, native energy
and printed external work. Compare to the independently derived axial stiffness
and consistent endpoint mass. Bound each run to 60 seconds and preserve its
exact inputs, pinned executable, output hashes and terminal container state.

## Analytical contract and limits

A 1 mm cube with E=1 N/mm², Poisson ratio zero and density 3e-9 tonne/mm³ has
K=EA/L=1 N/mm and effective endpoint mass rho*A*L/3=1e-9 tonne for the affine
uniaxial displacement field. Lateral translations are held at zero and the
left face has zero axial motion. The right face's average displacement is q.
Its exact static resultant is K*q and elastic energy is K*q²/2. The average
equation is `u2 + u3 + u6 + u7 - 4*q9 = 0`; node 2 axial motion is dependent.
Consequently the actuator's generalized dynamic force is four times the full
dynamic residual at node 2. By symmetry it is `K*q + m_eff*a`.

The dynamic fixtures prescribe q=0.01*(t/0.0001)^3 mm at 101 table knots,
with 100 fixed equal increments, alpha=0, zero initial velocity/acceleration
and no contact or damping. Native interpolation is piecewise linear. Compare
to the discrete Newmark kinematics from the exact knot displacements, not
to an assumed continuous cubic acceleration. Expected kinetic energy is
m_eff*v²/2. Trapezoidal total actuator work should equal elastic plus kinetic
energy to a relative tolerance of 1e-4 (absolute 1e-10 N·mm); force and motion
checks use the same relative tolerance with 1e-10 absolute floors.

These fixtures validate output interpretation for this simple element and
equation pattern. They do not validate C3D10 mass integration, arbitrary cap
warping, nonlinear contact, timber properties, or the complete joint.

## Documentation

[CalculiX 2.21 manual](https://dhondt.de/ccx_2.21.pdf): *EQUATION,
*NODE PRINT, *SECTION PRINT, *EL PRINT and Direct integration dynamics.
The zero-dissipation setting here isolates the energy identity for a linear
known-answer fixture; it is not a general prescription for contact analysis.
The [practice review](../ordinary-solver-practice-review-2026-09-27.md)
records the wider method decision.
