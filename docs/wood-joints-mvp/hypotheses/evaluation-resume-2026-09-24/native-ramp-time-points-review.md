# Implicit dynamic ramp-knot alignment in CCX 2.21

The current ramp lists force values at 0.001 s intervals. With a 0.0025 s
initial increment, the first increment spans the 0.001 and 0.002 s knots. The
CCX 2.21 implicit nonlinear path can be asked to end increments at those
times by activating a named `*TIME POINTS` schedule through an output request.
The checks below use the official CCX 2.21 source archive, SHA-256
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`.

For a one-step pilot ending at 0.025 s, define the time points before the
first `*STEP`:

```text
*TIME POINTS,NAME=RAMP_KNOTS
0.001,0.002,0.003,0.004,0.005,0.006,0.007,0.008
0.009,0.010,0.011,0.012,0.013,0.014,0.015,0.016
0.017,0.018,0.019,0.020,0.021,0.022,0.023,0.024
0.025
```

Replace `FREQUENCY=1` with `TIME POINTS=RAMP_KNOTS` on each active
`*NODE FILE`, `*NODE PRINT`, `*EL PRINT`, `*CONTACT FILE`, and `*CONTACT
PRINT` request. Keep the existing requested output variables and sets. This
matters because these keyword readers share the active `itpamp`; a later
`FREQUENCY=` option resets it to zero. The present model has one step and both
the amplitude and time-point lists use step time by default. For a
multi-step schedule, explicitly choose step time or total time consistently.

This request constrains integration endpoints, rather than merely asking to
write interpolated results. `nonlingeo.c:866` calls `checktime.f` at the
beginning of the step, where lines 81–102 shorten the initial increment to an
earlier first time point. On a converged increment,
`checkconvergence.c:437–477` clips the proposed next increment to the next
listed time, retaining the solver's adaptive increment proposal between
points. Rejected attempts restore the pending time-point index in
`checkdivergence.c:81–84`.

The schedule therefore turns the 0.0025 s initial increment into a 0.001 s
first increment and lands later increments on listed ramp knots. It does not
fix the increment size between knots or demonstrate time-integration
convergence; compare refined/adaptive runs before interpreting response. The
source applies this endpoint logic only when `idrct==0`; direct solution is
also explicitly rejected with a `TIME POINTS` output request by the print/file
keyword readers. This review is read-only and does not modify the live pilot.

Source archive provenance: [CalculiX 2.21 source archive](http://www.dhondt.de/ccx_2.21.src.tar.bz2), SHA-256 `52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`. The archive and extracted source tree used for this review are not included in this repository.
