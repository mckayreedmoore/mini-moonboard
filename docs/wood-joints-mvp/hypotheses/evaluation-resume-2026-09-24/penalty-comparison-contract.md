# Matched penalty-sensitivity comparison

Declared September 25, 2026 before interpreting any K=10000 response. The
child had been launched while this note was finalized; neither the parent
nor the threshold proposal used its displacement, force, momentum or energy
results to choose limits. The thresholds below are analyst-set numerical
triage rules, not adopted structural criteria or physical uncertainty bounds.

## Inputs and comparison state

Compare the terminal [K=100000 baseline](ordinary-transient-seating-100n-aligned-attempt01/terminal-outcome.md)
with the [K=10000 child](ordinary-transient-seating-100n-aligned-k1e4-attempt01/native-readiness-review.md).
Their freezes are respectively
`c3349f42bb8aaa3721e90f8f36ffd823c985ba9e0cffc6d8474b8154e1c5e267`
and `4f5d892d6f6270ae2d645463255a048b8b719331a0906412c4c4b85fd304f367`.
The parent checked that the contact penalty is the sole changed native
input scalar. Mesh, 35 pairs, 70 surfaces, material scenarios, forces, ramp,
zero initial state, stiff nut relation and requested output times are fixed.

The only baseline output state available is t=0.001 s. The reference force
is 100 N per opposed side, multiplied by 0.000298 at that knot: 0.0298 N per
side. The 15.625 N value belongs to the requested t=0.025 s endpoint, which
the baseline did not reach. The exact first-segment impulse is 1.49e-5 N·s
per side. Require matching recorded times within 1e-8 s and verify actual
amplitude/load equality; do not compare by iteration number, runtime or
different contact events. No interpolation fills an absent state.

Also compare accepted increment histories through the common knot. If the
child subdivides the baseline's single first increment, observed differences
combine penalty sensitivity and changed time discretization. Equal physical
time and input schedule alone do not isolate those effects. Further time
refinement remains necessary before a quantitative physical conclusion.

## Available-field triage

For each available scalar or vector field X, use
`r = ||X_child − X_base||∞ / max(||X_base||∞, floor)`.
Signed components must be preserved. A vector field comparison uses identical
node/owner IDs and the complete declared field, not just a change in its
maximum magnitude. Report absolute differences alongside normalized values.

| Quantity | Denominator floor | Flag for further numerical investigation |
| --- | ---: | ---: |
| Signed q and complete loaded-node displacement field | 1e-9 mm | r > 5% |
| Complete nut-controller rotation field | 1e-9 rad | r > 10% |
| Each audited owner's mass-weighted momentum vector | 1e-9 N·s | r > 10% |
| Each available pair's CF, CFN and CFS vector, separately | 1e-6 N | r > 10% |
| Global internal and kinetic energy, separately | 1e-12 N·mm | r > 10% |

These limits distinguish visible numerical changes from printed noise; they
do not bound design error or imply a conservative response. A change of
contact/opening state is reported even if force norms are below the floor.
CFN duplicates must not be added to CF. Slave-side subtotals are not complete
body forces, and a zero force vector alone does not establish an open gap.

For contact overlap, first verify a complete CDIS block against the native
contact count. The [CalculiX 2.21 manual](https://www.dhondt.de/ccx_2.21.pdf),
section 7.23, defines positive normal CDIS as overlap at active contact
integration points. Record the global maximum positive overlap. Flag values
above 0.000575 mm, an analyst-set 0.1% of the smallest modeled radial bore
clearance, 0.575 mm. This is a numerical length screen, not a wood-bearing
criterion; global values have no per-pair attribution without verified mapping.
Small global overlap does not establish contact-report coverage or accuracy.

Report elastic penalty energy separately and flag it if its magnitude exceeds
5% of `|internal energy| + |kinetic energy| + |penalty energy|`, using a
1e-12 N·mm denominator floor. Also report that energy against external work;
do not interpret that ratio when external work is at or below the floor.
Do not impose a relative-change limit on overlap or penalty energy: both may
scale approximately as 1/K at unchanged force and area. Their changes alone
do not prove material response changed by the same fraction.

For each branch report native energy discrepancy and its normalization.
The baseline discrepancy is 1.230541%. An increase above 0.5 percentage points
or a discrepancy above 2% is a triage flag; passing this screen does not establish energy or time
accuracy. First-increment discrete work from zero can be reconstructed and
checked against native external work within printed precision. Full-run work
cannot be reconstructed across accepted substeps whose displacement outputs
are absent; retain that result as unavailable.

## Coverage and disposition

The baseline has 33 complete CF/CFN/CFS triplets, partial pair 034 and absent
pair 035. Compare the available records, but keep complete-pair coverage
INCOMPLETE. The existing independent momentum audit covers the cleat, including
its vector and N projection; the other owners require actual vector fields
integrated with the same source-bound mass operator. Do not substitute q,
an equal-node rigid fit or a scalar projection for missing vector evidence.
Unparsed overlap fields and uncomputed owner momenta remain unavailable.

Record coverage and sensitivity separately: missing data must not hide an
observed sensitivity flag, and small observed differences must not turn
missing data into a pass. If complete compared metrics fall within these
limits, the result supports only further numerical refinement under the
declared scenario. It does not select K=10000, validate nut engagement,
establish quasi-static stiffness or bore seating, or close any of the 47
pending criteria. Runtime, iteration counts and memory are operational
observations and are reported separately from response quality.
