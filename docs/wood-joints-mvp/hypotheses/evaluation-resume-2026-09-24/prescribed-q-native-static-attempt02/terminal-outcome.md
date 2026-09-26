# Static prescribed-q fixture outcome

Native execution returned zero in 0.264961285 s. The zero-active-equation
warning does not prevent CCX from evaluating this fully prescribed static
state. Printed physical U and RF are both +0.03349590 in mm and N,
respectively; ground RF is -0.03349590 N. The dummy node's U is
0.001 mm and its RF is exactly zero. The imposed mapping
u=33.49590462574 q is reproduced within print precision.

With k=1 N/mm, analytic actuator applied demand is +1.121975626697 N
and structure resisting demand is its negative. Multiplying physical RF by
du/dq reconstructs the applied demand within DAT precision. Dummy RF cannot
be used as that demand. The analytic multiplier in K*u+lambda*c=0 has
the opposite sign to the internal-force scalar described by resultsforc.c;
coefficient-weighted source force and actuator-applied force must remain
separate. The source scalar itself was not printed in this fixture.

This verifies static kinematics and the output distinction only. It does not
validate any joint reaction, stiffness, or capacity. The fixture reproduces
the current actuator's dependent-first ordering and control coefficient;
it uses physical DOF 1 instead of the current actuator's DOF 2.

The parent verified frozen input and all output hashes. Execution SHA-256:
`eb066984768b05bb4c8a623b09d1e8cd3cd7559f43b4361b82612769bd662d01`. Attempt01 preserves the decimal-point
input-parser rejection; attempt02 changed only stiffness token 1 to 1.0.
