# Independent review: force-driven seating prefix work audit

The audit is internally consistent against its pinned immutable 20-state
prefix. I verified the producer (`audit.py`, SHA-256
`5038c690e6b6e523c8d3258e4a6bc57b4ceada634e1c7a92481d121f706c03eb`), the
report (`report.json`, SHA-256
`65078f98f8e71bf8b0e53257bfcc7bc3807bae804c64aa7ae1ca9cffba31c6ce`), the
snapshot manifest (`snapshot.json`, SHA-256
`001cefdb37a52bdf6bc6d1d590310c93d91d7f5b2f7cf0a35ad2e10c097e0d8a`), and
the frozen input manifest (`input-freeze.json`, SHA-256
`f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66`). All
27 pinned source-input artifact hashes match. Following `pilot.inp` and its
includes reaches eight input files. The actual deck contains one `CLOAD`
card: its 662 nonzero node/DOF terms cover 331 nodes and match the frozen
unit-force pattern at a scale of 100. Its tabular `RAMP_N` has 101
piecewise-linear `STEP TIME` points.

The frozen `.sta` prefix contains 20 accepted increments, numbered 1–20 at
1 ms intervals from 0.001 through 0.020 s, with no rejected attempts. A
single streaming pass over the pinned 353,025,378-byte `pilot.dat` matched
its SHA-256 and found 20 complete `PILOT_MONITOR` blocks, each with all 339
expected nodes, at those same times. The complete-field displacement
projection and report rows match. Every accepted endpoint is a ramp knot;
none of the accepted intervals crosses an interior ramp knot. This verifies
the audited prefix only: the ramp extends to 0.100 s, so the remaining knots
are beyond this snapshot.

I independently reconstructed each discrete work increment from the
serialized amplitude, load scale, and complete monitor displacement fields,
then compared it with the pinned native external-work rows. All 20 residuals
are within their reported combined print-rounding bounds. At 0.020 s,
reconstructed work is `5.891621650386964 N·mm`, native external work is
`5.891622 N·mm`, and the residual is `−3.496130362989902e-7 N·mm` against a
reported bound of `1.3231753407044011e-5 N·mm`. The largest absolute residual
over the prefix is `4.143075815754571e-7 N·mm`. The bound arithmetic agrees
with displacement-print precision, ramp-amplitude change from printed-time
precision, and native external-work print precision.

The scalar coefficient multiplying the frozen nodal pattern integrates to
`0.07208 N·s` over 0–0.020 s. The exact piecewise-linear integral and
endpoint-trapezoid sum agree because no ramp knots are skipped. Their
reported cumulative timestamp-rounding bounds reproduce as
`6.474954058301001e-7 N·s` and `6.881570000624676e-7 N·s`, respectively.
This is scalar patterned-force impulse, not a net-resultant vector impulse
or contact-transferred impulse.

This is a complete accounting of a captured, non-atomic live-output prefix,
not a terminal response. The work is discrete applied-work bookkeeping; the
rounding bounds do not include solver integration error or continuous-path
work error. No conclusion transfers to energy balance, contact equilibrium,
material validity, quasi-static behavior, seating, capacity, or mechanical
acceptance. `mechanical_acceptance` remains false. The review read only the
pinned inputs and `.sta`, `.dat`, and `.log` snapshot files; it did not read
live outputs or `pilot.frd`, run CAD or a native solve, or use Git.
