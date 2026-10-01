# Generic annular plate response helper — attempt 01

**Date:** 2026-09-28  
**Benchmark:** attempt02 MIT OCW uniformly pressured, clamped annulus; independently reviewed.  
**Disposition:** generic response helper implemented and locally verified; candidate `washer_bending` method gap remains open.

## Implemented behavior

[`mini_moonboard/washer_plate_response.py`](../../../../../mini_moonboard/washer_plate_response.py)
provides `uniform_pressure_clamped_annulus(...)`. It evaluates the classical
axisymmetric thin-plate solution for a homogeneous isotropic plate with
constant thickness, uniform transverse pressure over the full annular area,
and perfect clamping at both inner and outer radii. At a requested radial
station it returns deflection and radial slope.

Use consistent units: radii and deflection in one length unit, pressure in
force/length², and flexural rigidity `D = E h³/[12(1 - nu²)]` in
force·length. Positive pressure gives positive deflection in the same
transverse direction; the returned slope is `dw/dr`. The function validates
finite numeric inputs, positive radii/rigidity, outer radius greater than
inner radius, and a station within the closed annulus. It also fails closed
when `outer_radius / inner_radius < 1.02`; this is a double-precision numerical
limit, not a physical plate limit. Invalid numeric values raise `ValueError`;
nonnumeric inputs raise `TypeError`.

For the source's `a=1`, `b=10`, `D=1`, `P=1` case, the implementation returns
`w(r=5)=17.55185416356538`, corresponding to reviewed dimensionless
`W(5)=D w/(P a⁴)=17.551854163565369158...`. It also returns zero deflection and
radial slope at both clamped edges within floating-point tolerance. The
equation, primary-source locator, and independent high-precision known answer
are pinned to the producer and review packets listed in
[`source-pins.json`](source-pins.json).

The width-ratio floor addresses cancellation observed in the direct
double-precision coefficient solve. At `b/a=1.0001`, the pre-guard helper
returned `6.938893903907228e-18` at mid-radius, while an 80-digit Decimal
solution gives about `2.60416666688e-19`; at `b/a=1.000001`, it returned zero
while the reference is about `2.60416667e-27`. At the accepted lower bound
`b/a=1.02`, the helper returns `4.166680334094508e-10`, compared with an
80-digit Decimal reference `4.1666802816718521666...e-10` (relative difference
`1.26e-8`). The lower-bound test accepts a relative tolerance of `2e-8`.
Accuracy was not exhaustively mapped over all ratios above 1.02, so the
cutoff is a tested lower numerical boundary, not a global error guarantee.

## TDD and verification

The known-answer test first failed during collection because the new module did
not exist; after the implementation was added it passed. A separate
nonnumeric-input contract test first failed because the helper raised
`ValueError`; the focused change to raise `TypeError` made it pass. Boundary,
pressure/rigidity scaling, geometric scaling, and invalid numeric-input tests
were then run as the complete test module. The thin-annulus guard test first
failed because the helper returned an inaccurate finite value. The helper was
then changed to reject `b/a < 1.02`. A second red test found that zero pressure
bypassed this numerical guard; validation was moved before the zero-load
return.

From the repository root:

```sh
.venv/bin/pytest -q tests/test_washer_plate_response.py
.venv/bin/ruff check mini_moonboard/washer_plate_response.py tests/test_washer_plate_response.py
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-washer-plate-response-helper-attempt01-2026-09-28/verify_packet.py
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-washer-plate-response-helper-attempt01-2026-09-28 && sha256sum -c SHA256SUMS)
```

Recorded results: 15 tests passed; Ruff reported “All checks passed”; the
packet verifier reports `OK`; every entry in this packet's `SHA256SUMS`
passes. This helper is the only existing test target for this new module; no
repository-wide suite, candidate evaluation, CAD operation, or native solver
run was performed.

## Scope limits

This is a generic elastic response helper, not a washer qualification or
assembly check. It does not model ring or concentrated loading, finite
bolt-head/nut contact footprints, partial or unilateral timber support,
timber-seat compliance or crushing, local shear, plasticity, yield, strength,
resistance, capacity, demand/capacity ratio, or any WJ24 response. No washer
product, grade, lot, stiffness, or candidate input was selected or assigned.
It does not close or disposition the candidate `washer_bending` criterion,
change geometry, or establish design acceptance or release. A
candidate-specific model still needs supported load and support conditions,
contact/load distribution, product geometry and properties, and a matching
validated method.

MIT's remote PDF bytes were not stored or hashed in the reviewed source
packet. The local source and review packet files, plus this implementation and
test, are hashed in `source-pins.json`; local packet files are checksum-verified
by `verify_packet.py` and `SHA256SUMS`.
