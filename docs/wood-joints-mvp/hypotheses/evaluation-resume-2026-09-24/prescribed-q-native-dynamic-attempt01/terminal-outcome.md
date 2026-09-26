# Implicit dynamic prescribed-q fixture outcome

Native execution returned zero in 0.365365710 s with three accepted .01 s
steps. The parent verified the frozen input and every recorded output hash.
Only the two documented input-syntax corrections separate this deck from its
captured prepared source: decimal spring stiffness and removal of EXPLICIT=0.
The latter token would select explicit mode in CCX 2.21 despite its value.

Printed physical displacement follows 33.49590462574*q at all three states.
Physical FRD velocities are +0.669918, +0.669918 and -1.33984 mm/s,
consistent with the zero-initial-state alpha = 0 Newmark recurrence and the
prescribed q sequence .0001, .0003, .0002 mm. RF at the dummy node is zero;
physical RF is the elastic spring force k*u, without the analytical inertia
contribution required for the full actuator demand.

Native external work and kinetic energy are both printed as zero. The final
native internal energy is 2.243951e-5 N·mm and its printed relative energy
balance is 85.714286 percent. In contrast, the mass and verified velocity
imply nonzero kinetic energy. Thus native energy/work reporting on this
SPRING2 and MASS fixture has not validated generalized force/work recovery. The
nonzero observed velocities rule out interpreting zero reported kinetic energy as zero physical-node
motion. Source review must distinguish MASS energy-reporting scope and the
zero-active-equation path before transferring an inference to a full patch.

This supports the imposed U/V kinematics and confirms that raw dummy RF is
not actuator demand. It does not yet exercise inertial equilibrium on a free
physical coordinate or validate the current-joint prescribed-q route. A
meaningful dynamic check remains open; no large derivative is authorized by
this result alone. The fixture uses a scalar DOF 1 stand-in for original DOF 2.

Execution SHA-256: `ba91b392bea1098bdb5dfd4f4916e8847f7de15f1c2afb3bc07250e6509f947e`.
