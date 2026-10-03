# Exact rejected panel chunk: parent diagnostic

The saved case preserves the first reduction's rejected `main_lower_left`
chunk: 6,567 physical degrees of freedom and 16 source interface columns.
`case.json` pins its original stiffness, rigid basis, raw source wrenches,
projected right-hand sides, and source identities.

Evaluating the original float64 solution in extended precision reduced its
reported residual from 7.2326e-10 to 3.0092e-10; it still failed the 1e-10
gate. After the separate small-model refinement fixtures passed, the parent
ran one bounded correction diagnostic using the same factor and operator.
One correction passed: force residual 3.8855e-11, gauge displacement
1.1390e-16 mm, and multiplier 1.0742e-10 N. No threshold changed.

This is one elastic basis chunk, not a physical response, bearing law,
contact selection, complete compliance operator, or strength result.
`refinement-result.json` records the numerical history and producer hashes.
The subsequent full reduction has a separate attempt directory and stopped
at a different body; this local result is not a global pass.

Operational correction: `test_refinement.py` uses a private `.json.lock`
filename rather than the shared ledger `.lock`. Preserve that producer and
result as recorded; future parent executions must hold the actual shared
ledger lock externally. The subsequent attempt 02 uses the correct lock.
The diagnostic performed no native launch.
