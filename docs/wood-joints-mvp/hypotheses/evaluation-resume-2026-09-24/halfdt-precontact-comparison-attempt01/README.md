# Half-timestep precontact-prefix comparison

This bounded comparison uses the 13 shared accepted times from `0.001` to
`0.013 s` in the frozen coarse 1 ms and half-step 0.5 ms force-driven runs.
The coarse snapshot has 20 accepted states through `0.020 s`; the half-step
snapshot has 26 through `0.013 s`, with no rejected attempts in either
captured `.sta` prefix. All 13 paired DAT monitor states and native work/energy
log summaries are complete. The comparison includes q, maximum loaded-node
displacement U, reconstructed discrete cumulative work, native external
work, internal/kinetic/contact/total energy, and absolute and relative energy
balance values. `comparison.json` reports each absolute coarse/half pair,
absolute difference, and coarse-relative percentage at every common time.

The original half-step capture is
[halfdt-precontact-work-prefix-attempt01](../halfdt-precontact-work-prefix-attempt01/README.md),
snapshot SHA-256
`cc48eff42c5ef23eaa88d3511a55d024d54adba8373b642fa20a74e0782c2fee`.
Its original `pilot.log` remains preserved. The captured log stopped during
the `.013 s` increment, so the parent captured a separate immutable
[log-completion snapshot](../halfdt-precontact-log-completion-attempt01/snapshot.json)
with SHA-256
`b874bcb1323d492e45d6e12248a53c23e21e5dd2d6991c3a2d419668b1134d97`. Its
126,061-byte log (`9deb8ddf7ecdd471b99d2d850b45e23f297a163330f723519d90fe2fd9a40a6b`)
is a strict byte-prefix extension of the original 112,751-byte log
(`c8bd1af8f48c027a11b8d0d2c2085ccc477e7317f62f9c8bd61395452bd0f9f6`). The
producer uses only its complete summaries at the original 26 accepted times
through `0.013 s`; later states are excluded. The original `.sta`, `.dat`,
input freeze and snapshot remain unchanged. FRD and CEL were omitted, so this
comparison supplies no velocity or momentum result.

Both cases use solver image
`sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0`
and `/usr/bin/ccx` SHA-256
`6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b`. Their
main decks differ only in the first and fourth values of `*DYNAMIC`:
`0.001, 0.025, 1e-6, 0.001` versus
`0.0005, 0.025, 1e-6, 0.0005`. Of 27 shared input artifact names, 26 hashes
are unchanged and `pilot.inp` is the sole changed shared artifact; normalizing
that time-control row makes the main decks byte-identical. The half-step
freeze's `parent-pilot.inp` preserves the coarse `pilot.inp` exactly (SHA-256
`a9f891c92fed7eaa7e3b78f0656c5829d330a28a3df450ea7128b9ea52eb49c4`). All 34
half-step input artifact hashes, snapshot output hashes, and supplemental
log pins are checked by the producer.

The 662 CLOAD terms still use the same 101-point piecewise-linear `RAMP_N`
and the 100 N scalar reference-pattern scale. For example, the serialized
amplitude factor at `.001 s` is `0.000298` (pattern coefficient `0.0298 N`);
at `.013 s` it is `0.046306` (coefficient `4.6306 N`). These coefficients
multiply a self-equilibrated nodal pattern; they are not net resultant forces.
Both cases' discrete work reconstructions match native external-work prints
within their output-rounding bounds at all 13 common times.

Across the paired times, q differences narrow from `−17.43%` at `.001 s` to
`−0.416%` at `.013 s`; maximum loaded-node U differences narrow from
`−14.21%` to `−0.414%`. Reconstructed cumulative work changes from `+8.25%`
to `−0.0119%`. These are observations at common accepted times after a single
timestep-control change; they do not establish time accuracy, convergence or
a cause. The folder name means only that these times precede the coarse run's
reported bolt-hole contact onset; it does not assert zero active contact or
qualify the half-step contact history. No contact, capacity, or mechanical
acceptance conclusion is made (`mechanical_acceptance` is `false`).

The detailed absolute/relative time series is in
[comparison.json](comparison.json). It also reports the signed difference in
the printed absolute energy-balance residual and the percentage-point
difference in the printed relative energy balance. The following table gives
the paired coarse-relative changes; for the final two balance columns, the
entries are half-step minus coarse rather than relative-percent changes.

| Time (s) | q Δ% | max U Δ% | work Δ% | internal E Δ% | kinetic E Δ% | contact E Δ% | total E Δ% | Δ absolute balance (N·mm) | Δ relative balance (pp) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.001 | −17.431 | −14.205 | +8.251 | +21.370 | +6.059 | −99.249 | +4.304 | −1.363e−08 | −3.300834 |
| 0.002 | −9.148 | −8.235 | +2.565 | +11.287 | +1.450 | −83.234 | +2.484 | −9.797e−09 | +0.315452 |
| 0.003 | −5.438 | −5.408 | +0.754 | +2.021 | +0.630 | −27.601 | +0.749 | −6.120e−09 | +0.108755 |
| 0.004 | −3.432 | −3.477 | +0.404 | +0.419 | +0.405 | −25.612 | +0.399 | −3.151e−08 | +0.078258 |
| 0.005 | −2.256 | −2.308 | +0.345 | +2.040 | +0.228 | −2.457 | +0.344 | −1.532e−08 | +0.040751 |
| 0.006 | −1.596 | −1.647 | +0.249 | +2.613 | +0.098 | +0.582 | +0.248 | −3.888e−08 | +0.028661 |
| 0.007 | −1.218 | −1.261 | +0.141 | +2.086 | +0.028 | −0.474 | +0.141 | −1.326e−08 | +0.018640 |
| 0.008 | −0.966 | −0.995 | +0.077 | +1.576 | −0.002 | −1.408 | +0.077 | −8.823e−09 | +0.013378 |
| 0.009 | −0.787 | −0.801 | +0.039 | +1.116 | −0.010 | −0.563 | +0.039 | −6.390e−08 | +0.010535 |
| 0.010 | −0.662 | −0.668 | +0.007 | +0.394 | −0.008 | −0.242 | +0.007 | −9.046e−08 | +0.008212 |
| 0.011 | −0.565 | −0.565 | −0.011 | −0.236 | −0.003 | −0.456 | −0.011 | −1.739e−07 | +0.006719 |
| 0.012 | −0.484 | −0.482 | −0.015 | −0.577 | +0.001 | −0.924 | −0.015 | −4.260e−07 | +0.005872 |
| 0.013 | −0.416 | −0.414 | −0.012 | −0.672 | +0.003 | −1.040 | −0.012 | −7.263e−07 | +0.005138 |

Recreate the report from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/halfdt-precontact-comparison-attempt01/compare.py
```
