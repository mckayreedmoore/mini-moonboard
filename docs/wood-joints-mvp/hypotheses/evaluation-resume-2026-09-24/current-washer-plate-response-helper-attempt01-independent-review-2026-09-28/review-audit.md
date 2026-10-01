# Independent helper and evidence audit

## Method mapping and dimensional behavior

The source packet pins the independently reviewed MIT OCW uniformly pressured,
fully clamped annulus. For `xi=r/a`, `k=b/a`, and
`W=Dw/(P a^4)`, the source solution is

```text
W(xi) = A ln(xi) + B xi^2 + C xi^2 ln(xi) + F + xi^4/64
```

The helper's coefficient system imposes `W(1)=W'(1)=W(k)=W'(k)=0`:

```text
[ 0       1        0            1 ] [A B C F]^T = [ -1/64 ]
[ 1       2        1            0 ]                  [ -1/16 ]
[ ln(k)   k^2      k^2 ln(k)    1 ]                  [ -k^4/64 ]
[ 1/k     2k       k(2ln(k)+1)  0 ]                  [ -k^3/16 ]
```

Each row is the source particular solution's edge value or derivative moved
to the right-hand side. The code's radial derivative
`A/xi + 2B xi + C xi(2 ln(xi)+1) + xi^3/16` is the analytic derivative of
that expression. The source's `+P r^4/(64D)` particular solution supports the
chosen sign: positive pressure yields positive deflection in the same
transverse direction. A manual negative-pressure check reverses both
mid-radius deflection and slope.

The dimensional factors are correct: `w=(P a^4/D)W` has length units, and
`dw/dr=(P a^3/D)W'` is dimensionless. `D` is documented as force·length and
computed elsewhere from `E h^3/[12(1-nu^2)]`; pressure is force/length². The
code uses `inner_radius` as `a`, `outer_radius/inner_radius` as `k`, and
`radius/inner_radius` as `xi`, so geometric rescaling at fixed pressure and
rigidity has the expected fourth-power deflection and third-power radial-slope
scaling.

For the pinned benchmark (`a=1`, `b=10`, `D=P=1`, `r=5`), the independent
high-precision source solve gives `W=17.551854163565369158...`; the helper
returns `17.55185416356538`. The independent normalized radial slope is
`0.295343239872811760...`; the helper returns `0.2953432398728069`. Both match
to floating-point precision. Endpoint tests cover zero displacement and slope
at both clamped edges.

## Inputs, cutoff, and numerical range

The implementation rejects booleans/nonnumeric values with `TypeError`; NaN,
infinity, nonpositive inner radius or rigidity, non-increasing radii, and an
out-of-annulus station with `ValueError`. Pressure is intentionally signed:
positive and negative pressure produce sign-reversed outputs. A valid zero
load returns exact zero response, but only after radius-ratio validation.
Overflow/nonfinite intermediate or final response is rejected with `ValueError`.
These paths agree with the source model and the stated API contract.

The `k < 1.02` guard executes before the zero-pressure return. I confirmed a
ratio of `1.019` raises at both zero and nonzero pressure, while exactly
`1.02` is accepted. Independent 100-digit Decimal evaluation at the lower
boundary and midpoint (`xi=1.01`) gives:

```text
W reference       = 4.1666802816718521666418741964590284800842863080e-10
W helper          = 4.166680334094508e-10
relative W error  = 1.2581396289e-8
W' reference      = -1.65018080773472539408450665571463659962595e-10
W' helper         = -1.650175412981625e-10
absolute W' error = 5.3947531004e-16
relative W' error = 3.27e-6
```

The slope's relative error is amplified by its small magnitude. The absolute
error is about `1.30e-8` of the characteristic midpoint slope scale
`W(midpoint)/(half annulus width) ~= 4.17e-8`. Thus the lower-bound result is
not a gross derivative failure, but the packet's lower-bound accuracy check
covers only deflection. If lower-bound slope accuracy is an intended claim,
record this diagnostic and test it with a justified absolute tolerance (for
example `1e-15` in the stated unit case), rather than a tight relative
comparison.

The packet's high-precision references at ratios `1.0001`, `1.000001`, `1.02`,
and `1.03` are consistent with independent Decimal calculations. In particular,
the unguarded response at `1.0001` is about `2.60417e-19`, versus the packet's
reported historical old-helper magnitude `6.94e-18`; at `1.000001` the exact
response is about `2.60417e-27`. These comparisons support a conservative
fail-closed thin-annulus cutoff. The exact pre-guard float outputs are not
replayable from this packet: its pins contain only the frozen guarded helper,
and a straightforward unguarded replay of the current pivoted solver has
roundoff values with different signs/magnitudes. The packet accurately labels
them as historical parent spot checks; treat them as evidence of instability,
not frozen golden outputs. The author also states that no global error envelope
above `k=1.02` is claimed. Independent spot checks at `k=1.03`, `1.1`, `2`,
`10`, and `100` were accurate, but are not exhaustive.

One untested binary64 edge remains: very small but finite nonzero inputs can
produce a mathematically nonzero response below the representable range and
silently round to zero. For example, with `k=1.02`, midpoint station, `D=1`,
and pressure `5e-324`, the helper returns zero deflection and slope. This is
far below any candidate-derived load scale and does not affect the reviewed
benchmark, but `isfinite` checks do not detect underflow. Either document this
as an IEEE-754 input-range limit or add a fail-closed underflow check if this
generic API is intended for arbitrary finite scales.

## Tests and packet integrity

I ran from the repository root:

```text
.venv/bin/pytest -q tests/test_washer_plate_response.py
15 passed
.venv/bin/ruff check mini_moonboard/washer_plate_response.py tests/test_washer_plate_response.py
All checks passed!
python3 .../current-washer-plate-response-helper-attempt01-2026-09-28/verify_packet.py
OK: helper packet checksums and source/code pins match
```

`sha256sum -c SHA256SUMS` also passed for all four producer-packet files when
run from that packet directory. Its verifier checks the local packet sums and
source/code pin list, including the reviewed MIT benchmark packet and its
independent review, the maintained helper, and the 15-test module. It does not
hash mutable remote MIT bytes. No source pin, code, test, candidate criteria or
inputs, queue/status/manifest, CAD, or native solver data was changed by this
review.

The test suite covers the benchmark deflection, both clamped boundaries,
pressure/rigidity scaling, geometric scaling, invalid numeric inputs, a string
type error, the thin-annulus rejection, the accepted `k=1.02` deflection, and
rejection of a thin annulus at zero load. It does not directly assert the
interior known-answer slope or the lower-bound slope; their values above were
checked independently during this review.

## Candidate boundary

The method models only linear isotropic classical thin-plate response for
constant thickness, axisymmetry, uniform pressure over the entire annulus, and
perfect clamping at both radial edges. It is distinct from the earlier Heap
concentric ring-load example and does not represent finite washer/head/nut
footprints, partial or unilateral timber support, timber-seat compliance or
crushing, local shear, plasticity, or strength. This generic helper establishes
no WJ24/candidate washer response or capacity, no demand/capacity ratio, and no
criterion disposition. Candidate-specific washer behavior remains unproven.
