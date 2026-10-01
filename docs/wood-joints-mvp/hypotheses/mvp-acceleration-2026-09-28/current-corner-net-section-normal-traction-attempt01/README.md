# Conditional corner net-section properties and normal traction

This packet supplies section centroids, second moments and signed nominal
normal-traction conversions for the existing spine and inner-block bore
stations. It consumes the three authenticated rear cases and all seven
increments, preserving both one-sided cut actions: 252 conversions. It does
not assign a wood strength or complete-joint resistance.

It also corrects a specific **contextual-area metadata error** in the preserved
[section-action report](../current-corner-conditional-section-demands-attempt01/section-demands.json).
That report assigns the inner block's BG003 center cuts 11,766.458 mm², the
area within the two BG045 holes but away from a BG003 cross-bore. At the
BG003 center cuts, the full-width 7.5 mm strip removes a further 666.75 mm².
The applicable matching-axis geometry entry is therefore **11,099.708 mm²**.
All 84 affected one-sided metadata rows are explicitly identified here. The
earlier signed actions and report hash are preserved; no forces are corrected
or rejected because of this contextual field error.

The geometry hypothesis is the earlier rectangular envelope minus disjoint
modeled bore strips/circles. The normal traction hypothesis is a common affine
strain field: `σ=N/A+a(x-cx)+b(y-cy)`. Moments are transported from the actual
source cut datum to the net centroid before solving the unsymmetric section
equations. The calculation retains each cut's simultaneous signed force and
moment rather than combining independent maxima. At these cuts, the full-width
cross-bore separates the ligaments. Their common affine strain is an
unqualified proxy; this calculation does not prove local transfer around the
hole or establish actual hole-wall stresses.

The following full-load ranges collect the most negative and most positive
nominal values across the screened cuts; each range's endpoints can come from
different cuts.

| Case | Spine nominal normal traction (MPa) | Inner-block nominal normal traction (MPa) |
| --- | ---: | ---: |
| A12 rear | −0.3022 to +0.4277 | −0.04118 to +0.04144 |
| A1 rear | −0.2147 to +0.1558 | −0.04090 to +0.03148 |
| K12 rear | −0.1467 to +0.1226 | −0.01807 to +0.01093 |

Producer replay passes. The independent parent verifier integrates the
reported traction over quadrature domains for the gross rectangle, subtracts
the strips and circular holes, and reconstructs each original datum's
`N/Mx/My` without importing producer functions. Its maximum force discrepancy
is 1.71e−13 N and moment discrepancy 9.10e−12 Nmm. Rectangular bending and an
eccentric net-centroid pure-tension oracle also pass. These are arithmetic
checks, not new tolerances for native acceptance.

Physical gravity distribution, local bearing and hole concentrations,
shear/torsional traction, wood adjustments and stability, splitting/group
methods, BG003 contact/steel behavior and washer/thread/engagement remain
outside this conversion. No wood capacity, DCR, actual-geometry qualification,
native solve or reviewed-axis change is claimed.

Read-only reproduction from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-net-section-normal-traction-attempt01/convert.py --verify
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-net-section-normal-traction-attempt01/parent_verify.py
```
