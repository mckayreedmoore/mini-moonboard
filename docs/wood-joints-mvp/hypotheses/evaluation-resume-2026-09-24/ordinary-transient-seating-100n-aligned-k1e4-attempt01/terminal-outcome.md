# K=10000 seating diagnostic: bounded terminal outcome

The native launcher ended with `bounded_timeout`, return code 137 and
elapsed time 2407.138729356 seconds under its 2400-second
bound. This is the planned runtime limit, not a recorded motion-stop event.
The parent verified its terminal session before subsequent native work and
checked all 23 frozen-input and 14 output hashes. This note was added after
the output inventory; the raw execution manifest remains unchanged.

Seventeen increments were accepted through 0.017 s of the requested 0.025 s,
with no rejected attempts. Each advances 0.001 s; the last took seven
iterations. Final q is 0.467034573679 mm, maximum loaded-node displacement
is 0.385607144843 mm, and maximum controller rotation is
0.000644645559208 rad. No sampled motion threshold was reached. These
observations do not establish bounds between output points or bore seating.

All accepted states have complete monitor blocks. The separate
[history audit](../ordinary-transient-history-audit-attempt03/README.md)
reconstructs 2.406094469332 N·mm of discrete applied work, matching the native
2.406095 N·mm within the stated output-rounding bounds at every accepted
state. At the final accepted state, the native summary prints internal energy
0.03229635 N·mm, kinetic energy 2.373521 N·mm, elastic contact energy
0.0001586135 N·mm and relative energy balance 0.027582 percent. The response
is dominated by inertia; this is not a quasistatic stiffness result. The
smaller final printed energy discrepancy does not erase the matched first-knot
penalty sensitivity or establish time accuracy.

The [first-knot motion comparison](../aligned-first-knot-penalty-motion-comparison-attempt01/README.md)
retains its local-field and energy sensitivity flags. The original K=100000
branch has no matching later output knots, so later results are not a paired
penalty comparison. Complete terminal contact coverage and transferred body
forces remain to be audited; q alone does not locate first bore engagement.
Provisional stiff nut coupling remains a physical-model limitation. No
complete-joint response or any of the 47 criteria is accepted.

Execution SHA-256: `6c5eedb7b2b33f9841f50bbfc8d50642459fc4d50e4825771ce73fc3bb2b47c0`.
Frozen input SHA-256: `4f5d892d6f6270ae2d645463255a048b8b719331a0906412c4c4b85fd304f367`.
