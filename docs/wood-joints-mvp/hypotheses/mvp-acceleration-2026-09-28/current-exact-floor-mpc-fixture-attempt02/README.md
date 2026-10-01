# Corrected real-field exact floor MPC fixture

This separate attempt preserves the previous fixture physics, source loads,
force tables, hand answers and assessor. Attempt01 failed before mechanics
because a linear spring stiffness was formatted as `20`, which the pinned
SPRING parser interprets as a DOF selector. It remains failed and untouched.
This attempt emits explicit decimal points in real data, including `20.0`.
The correction changes numerical formatting only. It has a fresh single
60-second scoped parent launch budget; no automatic retry or frame authority.

See [the original method description](../current-exact-floor-mpc-fixture-attempt01/README.md).
The same four fixed RF interpretations must yield exactly one consistent
map across both hand cases, closing physical force balance. No native
force convention is assumed accepted before this attempt produces evidence.


## Observed result

Native method check passed both known answers. Parent independently checked all twelve printed increments (RF error <=5e-6 N; body balance <=3.56e-15 N). The uniquely passing reaction rule is `RF_REFERENCE_MINUS_DEPENDENT_CLOAD`; raw reference RF is not the physical reaction. See assessment.json and parent-all-increment-check.json. This verifies a small-model output method, not whole-frame bearing compatibility or corner acceptance.
