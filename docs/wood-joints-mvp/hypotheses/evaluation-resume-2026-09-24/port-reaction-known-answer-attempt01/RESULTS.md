# Known-answer results and disposition

Date: 2026-09-27. All four frozen jobs finished normally in under one second
each. Inputs and native outputs are preserved with hashes and terminal
container states in their execution records. The README is the unchanged
pre-run contract; this report records the resulting failed method gate.

| Fixture | Observation | Disposition |
|---|---|---|
| Static direct cap motion | q=.01 mm, force=.01 N, elastic energy=5e-5 N·mm | Matches exact solution |
| Static average-MPC motion | Same uniform physical response; controller RF=0 | Kinematics match; controller RF is not actuator reaction |
| Dynamic direct cap motion | Uniform prescribed motion; independent actuator work equals elastic plus kinetic energy | Kinematics/independent energy match; native RF omits inertia and native external work is zero |
| Dynamic average-MPC motion | Cap motions [.01560773, .008919995, .008919995, .006552276] mm at average .01 mm | Fails symmetric physical response; do not use for the joint |

## Independent diagnosis

`fea/wood_joint_port_coupon_audit.py` independently integrates the C3D8
stiffness and consistent mass using eight Gauss points, including the shear
terms produced by nonuniform axial nodal motion. It implements Newmark
beta=.25, gamma=.5 without calling the native solver. See
`independent-audit.json` and the saved auditor snapshot.

For right-cap motion x=T*y+g*q, with g=[4,0,0,0], the correct reduced equation
contains the prescribed-acceleration contribution Tᵀ*M*g*q̈. The full
equation produces the expected uniform .01 mm cap response. If that one term
is omitted, the independent solution matches all 100 native states to
4.97e-9 mm, consistent with native DAT rounding. The full equation differs
from the native result by .00560773 mm. This is strong evidence of missing
prescribed-motion inertia in this pinned solver's tested generic MPC path.
It does not establish a defect in every MPC or dynamic formulation.

The independent agent checked the integration, coordinate reduction and
Newmark recurrence and agreed with this diagnosis. Local 2.21 source
`calcresidual.c` collects acceleration only for active independent DOFs before
multiplying by the reduced mass matrix; this supports the observed omission.
Source inspection alone was not used to declare the result.

The reported residual reconstructed by repeated differencing of rounded DAT
displacements is less precise; use the independent forward integration
comparison above for the diagnosis. The full-residual work of the failed
MPC solution does not close energy, because that solution fails the intended
dynamic equilibrium equation. Static MPC and direct-motion energy results
do not rescue it.

## Decision and next step

The proposed full-joint prescribed-MPC transient is disabled in its producer;
no full joint job was launched using it. Do not change the cleat restraint or
rigidize the caps to obtain a successful response.

A separate [balanced-force fixture](../force-port-known-answer-attempt01/RESULTS.md)
tests the alternative: apply a balanced external load, leave axial rigid
translation free, and measure relative member motion. Both direct nodal loads
and a homogeneous free-controller coordinate pass that known-answer check.
Proceed by freezing a force-driven external-member diagnostic with actual
nodal work, current patch contact accounting and inertia retained. Its result
will be a transient response until rate, timestep, energy and equilibrium
comparisons support a quasi-static interpretation.

Documentation: [CalculiX 2.21 manual](https://dhondt.de/ccx_2.21.pdf), §6.7.2,
Direct integration dynamics, *NODE PRINT and *SECTION PRINT. The manual
permits dummy-node nonhomogeneous linear equations, while *NODE PRINT
explicitly excludes dynamic and MPC-induced force contributions from RF.
The native fixture establishes the additional limitation relevant here.
