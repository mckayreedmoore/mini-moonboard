# Balanced-force native method check

## Decision, observation, next step — 2026-09-27

**Decision:** Check force-controlled external loading on the free axial unit
cube, both directly at physical cap nodes and through an unprescribed generic
average-motion controller. The latter is a homogeneous coordinate change.

**Observation:** The preceding prescribed-MPC dynamic coupon fails the exact
symmetric solution. Independent integration reproduces its response when the
prescribed-motion inertia term is omitted. The proposed full-joint prescribed
MPC transient is therefore unsuitable for execution. Static results remain
valid within their coupon scope.

**Next step:** Run two serialized, 60-second-bounded native fixtures with the
same pinned CalculiX 2.21 executable. No axial displacement is prescribed.
Apply equal and opposite total end forces Q=.01*(t/1e-4)^3 N at 101 knots,
100 fixed increments, alpha=0. Observe U, V, RF, section forces and energies.

## Frozen analytical comparison

The same unit cube has E=1, nu=0, density=3e-9 tonne/mm³. Transverse DOFs
remain zero; whole-body axial translation is free. By symmetry the left and
right displacements are -q/2 and +q/2. The relative stiffness is 1 N/mm and
consistent relative mass is rho*A*L/12=2.5e-10 tonne. Independently integrate
this scalar equation using Newmark beta=.25, gamma=.5 and the exact force
knots. Compare all 100 native physical displacements and velocities, zero
mass-center motion, elastic and kinetic energies, and trapezoidal applied
work. Relative tolerance is 1e-4 with absolute 1e-10 force/energy/motion floors.

The controller variant imposes only u2+u3+u6+u7-4*q9=0, leaves q9 free and
loads q9 with Q. This is work-equivalent to Q/4 on each right-face node.
The left load remains -Q/4 per node. No controller reaction is used.

These checks concern input/output mechanics and homogeneous equation
handling. They do not validate C3D10/contact, a joint capacity, or quasi-static
behavior. The full-joint alternative must preserve complete applied wrench
balance and compare inertia, energy and loading rate before interpretation.

Documentation: [CalculiX 2.21 manual](https://dhondt.de/ccx_2.21.pdf), sections
6.7.2 and direct integration dynamics, *EQUATION, *CLOAD and *NODE PRINT.
