# BG003 anisotropic circular-clearance point law — attempt01

## Bounded result

This packet tests one candidate point law that combines the earlier rotated
anisotropic foundation and radial-clearance diagnostics. The law is a
**constitutive hypothesis**, not a measured or calibrated BG003 contact law:

```text
U(delta) = min over |v| <= g of 0.5 (delta-v)^T K (delta-v)
```

Here `delta` is relative bolt-to-receiver displacement, `v` is displacement
absorbed within a circular free-clearance disk, and point stiffness `K` is
symmetric positive definite in receiver grain axes. For `|delta| <= g`, the
minimizer is `v=delta` and force is zero. Outside the disk, the KKT equations
give

```text
(K + lambda I) v = K delta,  |v| = g,  lambda > 0
p = K (delta-v) = lambda v
```

The scalar equation for `lambda` is monotone and has one positive solution.
The returned point force is one coupled Y/Z resultant; the two axes are not
separate capacities.

## Tangent and known answers

Set `M=(K+lambda I)^-1`. Differentiating the boundary condition
`v^T v=g^2` gives
`d lambda = (v^T M K d delta)/(v^T M v)`. With `b=K M v` and `p=lambda v`,
the outside-gap tangent is

```text
T = dp/d(delta) = lambda K M + b b^T / (v^T M v)
```

Because `K` and `M` commute, this matrix is symmetric positive semidefinite.
The fixture verifies its gradient and tangent by central finite differences.
The potential is convex: it is the infimal convolution of a positive
quadratic with the indicator of a convex disk. The force is continuous at
first engagement, while its tangent has a branch jump there; exact boundary
points use the zero-force inside branch.

The main anisotropic oracle uses
`K=[[300,150],[150,100]] N/mm`, `g=0.575 mm`, and target `p=(3,4) N`. It
constructs `v=g p/|p|` and `delta=v+K^-1 p`; the solver recovers the target
force, `v=(0.345,0.460) mm`, and `lambda=8.695652174 N/mm`. The constructed
`delta` is not collinear with `p`, so the fixture exercises mixed anisotropic
response. The isotropic special case also replays the previous radial point
oracle exactly: `K=100 I N/mm`, `g=0.575 mm`, `p=(3,4) N`, and
`delta=(0.375,0.500) mm`. Other checks show that:

- `K=k I` gives the prior radial law `p=k max(|delta|-g,0) delta/|delta|`.
- `g=0` gives the rotated linear law `p=K delta`, energy
  `0.5 delta^T K delta`, and tangent `K`.
- An interior point has zero force, energy, and tangent.
- Simultaneously rotating `delta` and `K` rotates `v`, `p`, and `T` while
  preserving energy.

The maximum finite-difference errors are `1.8e-10 N` for the energy gradient
and `6.5e-9 N/mm` for the tangent. The outside tangent is symmetric with a
positive minimum eigenvalue in the mixed-force oracle. Exact values and
residuals are in [point-law-fixture.json](point-law-fixture.json).

## Applicability and finite-proxy recipe

The recipe is limited to the existing `a12-rear` BG003 bolt
`knee_outer_left_side_1`, full-load source increment, with the existing
38.1/88.9/88.9 mm receiver intervals and source member wrenches applied once
to the three rigid receiver degrees of freedom. No finite beam calculation
was run here. The next finite proxy, if separately ready, should use these
eight sensitivity combinations:

```text
density: 350 or 550 kg/m^3 (illustrative, non-adopted)
mesh:    16 or 32 divisions per receiver
gap:     0 or 0.575 mm (modeled hole-minus-axis radial gap)
```

The already reviewed Gikonyo et al. Eq. 4(c-d) regressions give
`k_f,parallel=0.1374 rho-12.9` and
`k_f,perpendicular=0.0922 rho-18.20 N/mm^3`. They yield:

| Illustrative density | `k_f,parallel` | `k_f,perpendicular` | `K_line,parallel = d k_f` | `K_line,perpendicular = d k_f` |
| ---: | ---: | ---: | ---: | ---: |
| 350 kg/m³ | 35.19 N/mm³ | 14.07 N/mm³ | 223.4565 N/mm² | 89.3445 N/mm² |
| 550 kg/m³ | 62.67 N/mm³ | 32.51 N/mm³ | 397.9545 N/mm² | 206.4385 N/mm² |

The units matter. The regression is a stress/displacement foundation modulus
`k_f [N/mm^3]`; multiply by the modeled shaft diameter `d=6.35 mm` to obtain
line stiffness `K_line [N/mm^2]`. At each 4-point Gauss integration point,
multiply again by that quadrature weight `w [mm]`:

```text
K_line,j = R_j diag(d*k_f,perpendicular, d*k_f,parallel) R_j^T
K_point,j = w K_line,j                 [N/mm]
U_point = min_|v|<=g 0.5 (delta-v)^T K_point,j (delta-v)   [N*mm]
```

For the outer spine and inner-frame block, proposed grain is global +Z. The
middle receiver grain is the modeled 40° direction from +Z toward +Y. Preserve
the off-diagonal middle `Y/Z` terms and evaluate the vector law jointly. The
radial diagnostic's mesh has four Gauss points per element and 16 or 32
elements per receiver (192 or 384 integration points for this one bolt).
The JSON records each receiver's element length, quadrature weights, rotated
line matrices, and the resulting point-stiffness eigenvalue envelopes. For
example, the 16-division quadrature weights span 0.4142–1.8117 mm; the
32-division weights span 0.2071–0.9059 mm. Density and mesh combinations are
sensitivities, not actual wood-property bounds.

Use the radial diagnostic's relative-displacement sign
`delta=w_bolt-u_receiver` and its established residual assembly. If evaluating
the point law with `K_point=w*K_line`, its returned energy, force, and tangent
already include the quadrature weight and go directly into the assembled
energy, residual, and tangent; do not multiply them by `w` again. The
equivalent per-length evaluation uses `K_line`, then multiplies its energy,
force, and tangent by `w` exactly once. Keep the exact A12 bolt1 receiver load
mapping and gauge checks; do not add source interface forces to the bolt beam
or add capacities across planes. The parent owns readiness and any finite
execution.

The reference point-law oracle uses a scalar bisection for `lambda` (53 steps
for the mixed-force answer). A finite proxy has hundreds of integration
points and repeated nonlinear evaluations, so an optimized batched or
eigenbasis 2×2 implementation and an explicit runtime budget are needed before
any finite execution. No such performance claim is made here.

The Gikonyo primary study supplies separate parallel/perpendicular elastic
regressions and its validation scope does not establish the proposed 40°
mixed-axis law. It also does not identify actual BG003 density, moisture,
initial stiffness, contact history, or hole fit. The circular clearance
minimization is a new path-independent assumption. It has no damage,
hysteresis, or measured engagement law. This result does not calculate
strength, splitting, group action, shared two-bolt timber compatibility,
steel yield, axial tie/washer interaction, a conservative demand bound, or
joint acceptance.

The exact method inputs and prior diagnostics are SHA-256 pinned in the result
packet. The primary source already recorded in the input packet is Gikonyo,
Schweigler, and Bader (2024), [“Beam-on-foundation modelling of dowel-type
single fastener connections in cross laminated timber”](https://www.diva-portal.org/smash/get/diva2%3A1829333/FULLTEXT02.pdf),
Eqs. 4(c-d). Its orthogonal regressions are reused as illustrative sensitivity
inputs only.

Replay from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-anisotropic-clearance-point-law-fixture-attempt01/verify_point_law.py --verify
```

No finite BG003 response, native solve, geometry change, capacity, or
acceptance is included.
