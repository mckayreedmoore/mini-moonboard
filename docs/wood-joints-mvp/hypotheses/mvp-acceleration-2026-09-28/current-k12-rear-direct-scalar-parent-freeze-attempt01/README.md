# Parent direct-scalar method preparation

This preparation targets only the SPR489 interpolation exception in the
rejected K12-rear response. It preserves the source coupon deck and verifies
all trace input/output hashes. It parses the serialized 81-term MPC and each
of the three emitted load maps, then independently solves their rank-one
equilibria with 100 N/mm numerical supports and the emitted unilateral joint
table. The resulting master displacements, scalar separation and spring
forces are recorded in `parent-analytic-audit.json`.

All three analytical states pass: tiny compression near a common displacement,
separation and a larger compression control. These are method evidence, not
frame demands, resistance checks or complete joint acceptance.

`prepare.py` refuses to freeze until the separate native-output checker exists.
It records the actual nodes, elements and equation along with the original
coupon metadata and parent oracle. The three step load maps remain explicit
metadata rather than being collapsed into one static `loads` map. Numerical
support grounds remain numerical devices, not physical timber or floor
supports. It snapshots the checker and source artifacts using the existing
parent native executor. It never launches a solver.

Parent readiness and a serialized launch remain separate actions bound to the
exact resulting freeze. A passing coupon alone cannot authorize use of the
rejected K12-rear forces or transfer a historical pass. A production method
change would need its own source-bound input and full response audit.
