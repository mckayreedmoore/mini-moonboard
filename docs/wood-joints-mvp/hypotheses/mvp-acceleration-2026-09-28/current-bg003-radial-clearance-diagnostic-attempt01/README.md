# BG003 radial-clearance diagnostic, attempt 01

This packet tests the modeled 0.575 mm radial clearance in one bounded
elastic scenario: A12-rear, BG003 bolt `knee_outer_left_side_1`, full-load
increment only. It reuses the pinned source wrench register and the owner's
continuous three-receiver beam formulation. The full source and solver checks
are recorded in [`diagnostics.json`](diagnostics.json).

The modeled axis is 6.35 mm and the hole is 7.5 mm, giving
`g=(7.5−6.35)/2=0.575 mm`. For this diagnostic only, steel modulus is set to
`E=190,000 MPa = 190,000 N/mm²`, so a circular axis has
`I=79.811376 mm⁴` and `EI=15,164,161.49 N·mm²`. The three continuous receiver
lengths are `38.1 / 88.9 / 88.9 mm`; each is a free rigid body with its own
transverse translation and rotation, and the beam ends are physically free.

The hypothetical isotropic line-foundation potential is

```text
U = ∫ 1/2 k max(||w(s)−u(s)||−g, 0)² ds
```

with line stiffness `k=100` or `1,000 N/mm²`. Its vector force per length is
`k max(ρ−g,0)(w−u)/ρ` when `ρ>g`, and zero otherwise. It is a radial gap law
with one coupled Y/Z resultant. It does not add separate plane capacities or
contact springs. The values of `E` and `k` are fixture assumptions without
physical calibration or bounds.

The radial spring passes the point-spring solution
`u=(g+||P||/k)P/||P||`: for `P=(3,4) N`, point-spring stiffness
`k=100 N/mm`, and this gap, displacement is `(0.375,0.500) mm` and recovered
force is `(3,4) N`. This point stiffness is distinct from the distributed
line-foundation `k` values below. Rotation
covariance passes. Finite differences check energy gradient and tangent with
maximum errors below `3.0e-10`; at `g=0` the radial law reduces to the ordinary
linear isotropic spring. At model level, all four `g=0` stiffness/mesh results
match the owner's pinned elastic solver at the corresponding
`β=kL⁴/EI` (`14,328.22` for `k=100`, `143,282.18` for `k=1,000`) within
`1.10e-9` relative error.

The 32-division-per-receiver signed middle-cut results are:

| `k` (N/mm²) | `g` (mm) | Middle-cut shear on left Y/Z (N) | Middle-cut couple on left My/Mz (N·mm) | Shear magnitude (N) | Couple magnitude (N·mm) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0 | `(63.242, −68.924)` | `(2,469.114, 1,594.100)` | 93.542 | 2,938.993 |
| 100 | 0.575 | `(30.312, −41.670)` | `(1,932.730, 1,247.664)` | 51.528 | 2,300.459 |
| 1,000 | 0 | `(21.581, −23.520)` | `(127.014, 82.002)` | 31.920 | 151.185 |
| 1,000 | 0.575 | `(14.032, −17.942)` | `(878.821, 599.001)` | 22.777 | 1,063.546 |

Within this assumed law, the 0.575 mm gap reduces the cut shear magnitude at
both `k` values. It reduces the couple magnitude by `21.7%` at `k=100`, but
increases it by `603.5%` at `k=1,000`. This is a marked stiffness/contact-law
sensitivity in the finite proxy, not a physical BG003 demand range or a
conservative bound.

All eight requested `k/gap/mesh` solves converged. Positive-gap solves start
from the exact `g=0` linear solution and use gap continuation only as a
numerical homotopy; it is not a physical loading or contact history. The
continuation allows at most 80 accepted steps and 160 attempts, with at most
20 Newton iterations per step and 12 line-search halvings. A singular or
indefinite tangent, scaled pivot ratio at or below `1e-12`, failed line
search, or exhausted Newton step rejects that increment and halves the gap
step. The calculation stops if the failure persists at the minimum increment
or if either continuation budget is exhausted. The minimum allowed gap increment is
`0.575/2¹⁶ = 8.77e-6 mm`. Actual accepted-step counts were 11/12 at `k=100`
and 70/54 at `k=1,000` for the 16/32 meshes; the smallest accepted increments
were respectively `0.01797 / 0.00898 mm` and `0.00225 / 0.00112 mm`. No
stabilizing spring, anchor or regularization was added.

Signed 16/32 differences are below `0.12%` for cut shear, `0.15%` for cut
couple and `0.08%` for sampled peak couple. The largest receiver force and
normalized-first-moment closure error is `6.9e-6` in normalized generalized
load units; the maximum free-end closure residuals are `1.7e-7 N` and
`1.6e-5 N·mm`. The largest gauge reactions are `4.0e-8 N` in translation and
`5.7e-6 N·mm` in rotation. The source lateral member wrenches are applied once
to receiver degrees of freedom and not again to the bolt beam. The axial X
tie is outside this lateral model.

The radial engaged-length fractions are outputs of this ideal quadrature
law, not observed contact. The actual material/contact law, initial contact
history, axial tie/preload, washer/end-seat compliance, timber deformation
shared between two bolts, strength, splitting, group interaction and joint
acceptance remain unmodeled. No geometry, CAD, native model, or physical
configuration changed; no capacity or full-frame claim follows.

Reproduce from the repository root:

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-radial-clearance-diagnostic-attempt01/run_diagnostic.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-radial-clearance-diagnostic-attempt01/run_diagnostic.py --verify
```

The first command writes only this folder's `diagnostics.json`; `--verify`
replays the bounded calculations and checks byte-identical output without
writing. [`SHA256SUMS`](SHA256SUMS) pins this packet's producer, report and
README.
