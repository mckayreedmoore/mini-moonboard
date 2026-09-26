# First-transition half-step comparison

This report pairs the force-driven 1 ms and 0.5 ms runs at their exact shared
accepted time of `0.019 s`. It also records the half-step run's `0.0195 s`
work and native-energy accounting as a half-only observation. The frozen
half-step snapshot ends at `0.0195 s`; the coarse run has an accepted `0.020 s`
state, but there is no half-step state at exactly `0.020 s` in this snapshot.
That planned comparison is marked unavailable. No time interpolation is used.

The half-step input and output prefix is
[halfdt-contact-firsttransition-prefix-attempt01](../halfdt-contact-firsttransition-prefix-attempt01/README.md),
snapshot-manifest SHA-256
`d531ba36a8a6387bc6e12f96fa5093edcf9fde6dd20a12a2bb13b6af9ee9430b`,
input-freeze SHA-256
`ea24423f587795743d0c1189c798f77d83159208c76d5d1d3a9fa5554eda4f56`. The
snapshot contains 39 accepted states through `0.0195 s` and no rejected status
rows. Its copied `.sta`, `.dat`, `.log`, `.frd`, `.cvg`, execution record and
34 frozen input artifacts are verified by hash. The producer reads solver
outputs only from this immutable snapshot and reads the source run folder only
to recheck hash-pinned inputs.

The coarse work history comes from
[force-every-increment-seating-prefix-attempt01](../force-every-increment-seating-prefix-attempt01/snapshot.json),
snapshot-manifest SHA-256
`001cefdb37a52bdf6bc6d1d590310c93d91d7f5b2f7cf0a35ad2e10c097e0d8a`,
input-freeze SHA-256
`f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66`. Its
audited work series is
[force-every-increment-seating-work-audit-attempt01/report.json](../force-every-increment-seating-work-audit-attempt01/report.json),
SHA-256
`65078f98f8e71bf8b0e53257bfcc7bc3807bae804c64aa7ae1ca9cffba31c6ce`. Native
energy log summaries are read from the separately frozen
[coarse energy-prefix snapshot](../force-seating-contact-energy-prefix-attempt01/snapshot.json),
manifest SHA-256
`18fac09d22a3b2caab941ad0aa81ff5533d1c60f193a96ae13b39b908407d46e`. Its
`.sta`, `.dat` and `.log` preserve the original coarse snapshot as a strict byte
prefix; the work report remains bound to the earlier momentum snapshot.

Both runs use solver image
`sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0`
and `/usr/bin/ccx` SHA-256
`6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b`.

The 27 shared source artifact names have 26 identical hashes; `pilot.inp` is
the only changed shared input. Normalizing its `*DYNAMIC` row makes the main
decks byte-identical. The coarse row is `0.001,0.025,1e-6,0.001`; the half-step
row is `0.0005,0.025,1e-6,0.0005`. The half-step freeze also contains seven
derivative-parent context and input-pinning artifacts, including a
byte-identical parent pilot. Both cases retain the same 101-point `RAMP_N`, 662 CLOAD terms and 331
nodes in the frozen unit-force pattern. At `0.019 s`, the table factor is
`0.094582`; at `0.0195 s`, it is `0.099291`. With the 100 N scalar reference
scale, these give pattern coefficients of `9.4582 N` and `9.9291 N`. They are
coefficients on a self-equilibrated nodal pattern, not net resultant forces.

At the exact `0.019 s` pair, half-step minus coarse differences are:

| Quantity | Difference | Relative to coarse |
|---|---:|---:|
| q | −0.0013410 mm | −0.1865% |
| Maximum loaded-node U | −0.0011160 mm | −0.1879% |
| Maximum controller rotation | −1.1603e−6 rad | −0.1192% |
| Reconstructed cumulative work | +0.00031820 N·mm | +0.00696% |
| Native external work | +0.00031800 N·mm | +0.00695% |
| Internal energy | +0.00026102 N·mm | +0.5027% |
| Kinetic energy | +0.00004800 N·mm | +0.00106% |
| Elastic contact energy | −0.00025185 N·mm | −50.84% |
| Absolute energy-balance print | −0.00026113 N·mm | — |
| Relative energy-balance print | +0.035517 percentage points | — |

The coarse and half-step reconstructed work residuals are `5.20e−10` and
`1.9762e−7 N·mm`; their respective combined print bounds are `1.0240e−5` and
`1.7042e−5 N·mm`. Both are within those printed-value bounds. At `0.0195 s`,
the half-only observation is q `0.7845223 mm`, maximum loaded-node U
`0.6464461 mm`, maximum controller rotation `7.7124e−4 rad`, reconstructed
work `5.221053225 N·mm`, native external work `5.221053 N·mm`, and work
residual `2.2511e−7 N·mm` against a `1.9409e−5 N·mm` bound. Its log reports
internal energy `0.1341423 N·mm`, kinetic energy `4.475913 N·mm`, elastic
contact energy `0.001169559 N·mm`, total energy `4.611224 N·mm`, absolute
energy balance `−0.6098287 N·mm` and relative balance `71.647365%`.

The paired and standalone values are observations from the coarse and
half-step frozen prefixes.
They establish neither timestep accuracy, convergence nor a cause. This
report makes no contact-count, contact-equilibrium, material-response,
quasi-static, joint-capacity or mechanical-acceptance claim. A separate
contact-storage audit is outside this comparison. The result keeps
`mechanical_acceptance` false.

Recreate the first-transition report from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/halfdt-contact-onset-comparison-attempt01/compare.py \
  --half-prefix halfdt-contact-firsttransition-prefix-attempt01 \
  --half-snapshot-sha256 d531ba36a8a6387bc6e12f96fa5093edcf9fde6dd20a12a2bb13b6af9ee9430b \
  --times 0.019 0.0195 \
  --output docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/halfdt-contact-onset-comparison-attempt01/first-transition-comparison.json
```

The checked producer is `compare.py` (SHA-256
`a16906a20b870fccf5d63bcd8aee18ed6cdb224866e8fe53544f94e5e4483028`). Its
result is
[first-transition-comparison.json](first-transition-comparison.json) (SHA-256
`41bd43ef7984bcc3ed7eeab4a95c8d2418a135eec9fd8ee5c789f4bd96fdd66f`). The
focused checks run with
`python3 -m unittest discover -s docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/halfdt-contact-onset-comparison-attempt01 -p 'test_compare.py'`.
