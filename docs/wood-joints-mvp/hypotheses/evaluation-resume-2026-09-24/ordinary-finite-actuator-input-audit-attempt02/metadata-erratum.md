# Emitted-coefficient rounding metadata correction

The frozen finite-actuator input contains an incorrect diagnostic value in
`actuator-driving.json`, at
`source_unit_pattern.mpc_coefficient_max_rounding_error`. The producer compared
the source physical weight `w` to the serialized equation coefficient `a`,
although the equation convention is `a = -w`. The reported value therefore
includes a sign mismatch and is not a coefficient-rounding bound.

This defect does not change the emitted equation, spring, prescribed target,
physical inputs or native result. The parent actual-input audit and the
[first-state work audit](../current-finite-actuator-work-audit-attempt01/README.md)
derive the actual weights as `w = -a` directly from the serialized equation.
They do not use the incorrect metadata value to qualify a comparison. The
work audit's exact decimal source-text comparison gives a maximum difference
of `5e-17`; the parent binary64 comparison records approximately
`5.03e-17`, including binary conversion.

Preserve the running case, its input freeze, producer snapshot and captured
outputs unchanged. Correct the metadata calculation for future builds and
verify it against weights independently recovered from the emitted equation.
Do not substitute the erroneous stored value as an error bound in any later
momentum, work or force audit. This correction establishes no joint capacity
or acceptance.
