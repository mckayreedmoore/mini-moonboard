# BG003 rotated-foundation diagnostic, attempt 01

This isolated calculation tests whether a rotated anisotropic linear
foundation changes signed middle-cut actions for the two BG003 bolts. It uses
the authenticated full-load source wrenches from the three pinned conditional
corner reports and the same continuous `38.1 / 88.9 / 88.9 mm` receiver stack
as the owner's [continuous-beam diagnostic](../../support-corner-review-2026-09-30/README.md).
The exact loads, source guards and owner comparison rows are in
[`diagnostics.json`](diagnostics.json); its `source_sha256` pins the input
packet, owner diagnostic, source reports and geometry/method records.

The vector beam operator first passes an infinite-beam point-load fixture with
`EI=1 N·mm²` and
`K_line=[[2.5,1.5],[1.5,2.5]] N/mm²`. On a 160-element, 40 mm free-ended
truncation, center displacement is `(0.2392749604, -0.1142769925) mm`; the
eigenmode infinite-beam oracle is `(0.2392766953, -0.1142766953) mm`, a maximum
relative difference of `7.3e-6`. The nonzero Z displacement checks that the
off-diagonal foundation term is active.

The implementation then reproduces the owner's isotropic signed middle-cut
results at `β=100` to maximum relative error `1.23e-10` across six bolt/case
combinations. It also matches the owner's `β=10,000` rows to that tolerance.
This checks the vector assembly and force/moment signs against the established
scalar implementation.

For the anisotropic comparison, `β = k_perpendicular L⁴/EI` uses the smaller
foundation eigenvalue. The synthetic ratio is `k_parallel/k_perpendicular=2`:
outer member grain is global Z; middle grain is modeled 40° from Z toward +Y.
Thus the dimensionless outer matrix in (Y,Z) is `β·diag(1,2)` and the middle
matrix is `β(e_perp e_perpᵀ + 2e_parallel e_parallelᵀ)`. These two beta values,
one ratio and one orientation are mathematical scenarios only; there is no
literature calibration or physical stiffness bound.

| β from `k_perpendicular` | Six scenarios | Largest 16/32 signed shear difference fraction | Largest 16/32 signed couple difference fraction | Largest 16/32 sampled peak moment difference | Largest signed middle-cut change vs isotropic |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 6 | `9.1e-10` | `1.1e-9` | `0.62%` | shear `0.088%`; couple `0.458%` |
| 10,000 | 6 | `1.7e-6` | `4.9e-6` | `0.32%` | shear `7.79%`; couple `22.96%` |

The signed difference fractions compare Euclidean vector differences, with a
1 N or 1 N·mm denominator floor. Every rotated case closes its integrated
receiver force/first-moment wrenches, free-end force/moment, and pinned common
translation/slope gauges; the largest recorded receiver force/normalized
first-moment residual is `4.1e-9` in the normalized generalized-load units
(N-equivalent), free-end force residual is `5.0e-9 N`, free-end couple residual
is `6.8e-7 N·mm`, and gauge reaction is `4.1e-8` in the normalized
generalized-load units. The source lateral Y/Z forces and bending
couples are applied once at the three rigid receiver bodies. They are not
also loaded onto the beam. The middle receiver has no seam or hinge, and the
physical bolt ends are free.

Under this declared elastic assumption, rotating the synthetic foundation
has a small effect at `β=100` and a material effect at the stiff `β=10,000`
fixture point. That demonstrates sensitivity to off-diagonal Y/Z coupling in
this finite proxy only. It does not establish the applicable wood stiffness,
load sharing, or a conservative demand bound.

The actual `0.575 mm` clearance and material/contact law remain unmodeled.
The foundations here are bilateral and continuous; there is no seating or
first-contact transition. The source axial X tie, preload, washer/end-seat
compliance, receiver flexibility/shared-timber compatibility, steel yield,
wood bearing resistance, splitting, group behavior and capacities are outside
scope. This is not a native solve, joint acceptance, or frame qualification.

Reproduce from the repository root:

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-rotated-foundation-diagnostic-attempt01/run_diagnostic.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-rotated-foundation-diagnostic-attempt01/run_diagnostic.py --verify
```

The first command writes only this folder's `diagnostics.json`; the second
checks byte-identical output without writing. [`SHA256SUMS`](SHA256SUMS) pins
the new producer, report and README.
