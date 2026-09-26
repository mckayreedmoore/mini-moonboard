# Half-timestep early-prefix comparison

This bounded postprocess compares the complete common accepted states at
`0.001` and `0.002 s` from the frozen 1 ms and 0.5 ms force-driven prefixes.
The coarse case is the 20-state
[force-driven work audit](../force-every-increment-seating-work-audit-attempt01/README.md);
the half-step snapshot has four accepted states through `0.002 s`. Both source
snapshots are non-atomic live-output captures, not terminal runs. The producer
verifies every pinned snapshot output and source input, then excludes any
half-step DAT/log rows later than its captured `.sta` prefix.

Both cases use image
`sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0`
and `/usr/bin/ccx` SHA-256
`6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b`. The
main deck differs only in the first and fourth values of its `*DYNAMIC` tuple:
`0.001, 0.025, 1e-6, 0.001` versus
`0.0005, 0.025, 1e-6, 0.0005`. Of the 27 artifact names shared by the two
freezes, 26 hashes are unchanged; the sole changed shared artifact is
`pilot.inp`. The half-step freeze's `parent-pilot.inp` preserves the original
coarse `pilot.inp` exactly (both have SHA-256
`a9f891c92fed7eaa7e3b78f0656c5829d330a28a3df450ea7128b9ea52eb49c4`). The
half-step freeze adds seven derivative-provenance artifacts. Both retain
the same 662 CLOAD terms, 101-point `RAMP_N`, 35 contact pairs, meshes,
materials, stops and per-accepted-increment outputs.

| Time | q (coarse → half, mm) | Loaded-node max displacement (mm) | Reconstructed cumulative work (N·mm) | Native kinetic energy (N·mm) | Elastic contact energy (N·mm) |
|---:|---:|---:|---:|---:|---:|
| 0.001 s | `2.4127149e-5` → `1.9921449e-5` (−17.43%) | `1.9889680e-5` → `1.7064337e-5` (−14.21%) | `3.5949452e-7` → `3.8915475e-7` (+8.25%) | `3.082268e-7` → `3.269033e-7` (+6.06%) | `1.357480e-8` → `1.020145e-10` (−99.25%) |
| 0.002 s | `1.7898901e-4` → `1.6261584e-4` (−9.15%) | `1.4499062e-4` → `1.3305011e-4` (−8.24%) | `1.1834759e-5` → `1.2138344e-5` (+2.57%) | `1.043535e-5` → `1.058669e-5` (+1.45%) | `1.568612e-8` → `2.630004e-9` (−83.23%) |

At the common times, the serialized amplitude factors are `0.000298` and
`0.001184`; multiplied by the 100 N reference-pattern coefficient, they give
scalar pattern coefficients of `0.0298 N` and `0.1184 N`. The pattern is
self-equilibrated, so these coefficients are not net resultant forces. The
reconstructed work matches each case's native external-work print within the
reported output-rounding bound at both times.

The values above show the absolute scale as well as relative differences: q
is below `0.0002 mm` at these times. Differences are observations at common
accepted times after a single timestep-control change. They do not establish
time accuracy or convergence, and this comparison does not identify a cause.
Native energy lines are recorded as printed; no contact-equilibrium,
material-response, quasi-static, capacity or joint-acceptance conclusion is
made. `mechanical_acceptance` remains `false`.

The full machine-readable comparison is [comparison.json](comparison.json).
Recreate it from the frozen snapshots and pinned coarse audit with:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/halfdt-early-comparison-attempt01/compare.py
```

The source manifests are the
[coarse prefix](../force-every-increment-seating-prefix-attempt01/snapshot.json)
(`001cefdb37a52bdf6bc6d1d590310c93d91d7f5b2f7cf0a35ad2e10c097e0d8a`) and
[half-step prefix](../halfdt-early-prefix-attempt01/snapshot.json)
(`07566ead8aa5e7c9b48d0bbd1a026240c507cd2da805d5dc9a256eccb21c1483`).
