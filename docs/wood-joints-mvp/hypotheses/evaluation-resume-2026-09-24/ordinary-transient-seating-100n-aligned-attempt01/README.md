# Ramp-knot-aligned 100 N seating diagnostic

Status: frozen, not executed. This is a separate timing derivative of the
100 N reference-amplitude case. It changes both integration endpoints and
output scheduling: the named `RAMP_KNOTS` sequence makes the implicit CCX
step end at each 0.001 s ramp knot, and every active output request uses that
same sequence. The source review explains the CCX 2.21 behavior and its
limits in [native-ramp-time-points-review.md](../native-ramp-time-points-review.md).

The derivative retains the source case's 0.0025 s initial and maximum
increments, 0.000001 s minimum increment, and 0.025 s step end. The solver clips
the initial increment to the first listed 0.001 s endpoint and preserves
adaptive cutbacks if an increment fails. Endpoint alignment does not establish
time accuracy or a converged time history; it only ensures that the prescribed
piecewise-linear load knots are eligible as integration endpoints. In
particular, knot alignment alone does not remove displacement quadrature error
on the first linear ramp segment. A time-refinement comparison is still needed
before interpreting response magnitude.

The inherited 662 serialized CLOAD terms, original `RAMP_N` amplitude table,
unit-load actuator observation weights, physical inputs, and all other cards
are preserved byte-for-byte or text-identically as appropriate. The existing
100x CLOAD scale means this 0.025 s case reaches 15.625 N on each opposed side;
it is a short reference-amplitude seating diagnostic, not a 100 N service-load
case. The unit-load weights continue to define the reported generalized
observation `q`; calculate actual applied-load work and momentum using the
separately serialized 100x load vectors and the amplitude history.

The 41 node, element, and contact output requests write only at listed times
and at step end, not at every adaptive substep. Stop monitoring therefore sees
only complete requested samples; it does not capture exact threshold-crossing
times. Sparse displacement output also cannot supply a per-substep work
history. Knot-aligned force impulse by itself is not evidence of dynamic
accuracy, equilibrium, physical bolt-thread behavior, resistance, capacity,
or joint acceptance.

`input-freeze.json` binds this deck and its copied inputs. The original
`parent-input-freeze.json` and `scale-producer.py.snapshot` remain byte-for-byte
identical to the 100 N parent. The immediate scaled-parent freeze is preserved
separately as `timing-parent-input-freeze.json`; `timed-producer.py.snapshot`
records the exact derivative producer used. No native solve or geometry change
was made.
