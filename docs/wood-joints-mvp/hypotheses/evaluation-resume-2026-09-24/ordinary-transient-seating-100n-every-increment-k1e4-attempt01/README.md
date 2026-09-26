# Every-increment force-driven ordinary-joint diagnostic

This is a fresh diagnostic using the unchanged physical inputs from the
preserved K=10000 force-driven case. Its 662 CLOAD terms and sampled RAMP_N
amplitude are unchanged. The 100 N reference scale gives a 15.625 N per-side
endpoint at 0.025 s; it is not a constant 100 N test.

The adaptive implicit step retains ALPHA=0, uses initial/maximum increments
of 0.001 s and minimum 1e-6 s, and allows 10000 increments. All 41 existing
output cards request FREQUENCY=1. Removing TIME POINTS removes guaranteed
ramp-knot alignment after adaptive cutbacks. Applied-load impulse, work,
contact coverage, momentum and time accuracy require examination of the
actual accepted states.

The input freeze SHA-256 is
`f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66`;
the pilot SHA-256 is
`a9f891c92fed7eaa7e3b78f0656c5829d330a28a3df450ea7128b9ea52eb49c4`.
The parent verified all 27 child artifact pins and all 23 unchanged source
artifact pins. The seven physical include files are byte-identical to the
source case. The only pilot changes are the time controls, increment limit,
and output schedule. The source remains preserved.

The producer is `fea/wood_joint_current_every_increment_transient.py`;
its two focused tests and Ruff checks passed. The producer requires a fresh
destination. This folder already exists and must not be regenerated over.

The parent-owned execution record, when present, governs run status. A
launch or converged increment does not establish joint acceptance. The
K=10000 contact choice, diagnostic rigid nut coupling, physical engagement,
mesh and time sensitivity remain unresolved. No geometry or criterion
status changes follow from preparing this input set.
