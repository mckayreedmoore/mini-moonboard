# Terminal K=10000 accepted-history audit

The [JSON report](aligned-k1e4-terminal-audit.json) binds the terminal
execution, all 23 frozen inputs, native status/DAT/log output, and the
previously validated history implementation. Parent verification checked all
23 input and 14 output hashes after the launcher became terminal.

All 17 accepted times from 0.001 through 0.017 s have complete displacement
monitors and native external-work reports. There are no rejected attempts or
missing intermediate accepted states. Unlike the earlier K=100000 baseline,
this recorded history permits work reconstruction without bridging gaps.
Each accepted interval ends at a sampled ramp knot.

The signed complete-field q projection gives cumulative discrete work
2.40609446933193 N·mm, compared with native printed 2.406095 N·mm. All 17
cumulative comparisons lie within their combined printed-displacement,
timestamp/amplitude, and native-work rounding bounds. The parent independently
recomputed the trapezoidal sum from execution observations and the actual
ramp table. These rounding bounds do not bound time-integration error.

The [terminal outcome](../ordinary-transient-seating-100n-aligned-k1e4-attempt01/terminal-outcome.md)
records the runtime limit and remaining mechanical scope. Complete accounting
for this recorded interval is not completion of the requested 0.025 s run,
a contact-pair coverage finding, or acceptance of a physical joint law.

Execution SHA-256: `6c5eedb7b2b33f9841f50bbfc8d50642459fc4d50e4825771ce73fc3bb2b47c0`.
Audit SHA-256: `e12c2d0a653f49f9cdf13735542ed565a2723b60313f5fc0eb90bd79c62a794f`.
