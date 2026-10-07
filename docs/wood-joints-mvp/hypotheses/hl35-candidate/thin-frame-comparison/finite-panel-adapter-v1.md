# Finite-panel integration adapter

The [method receipt](finite-panel-adapter-method-v1.json) validates an integration
adapter for the six retained interval-eight panel bases. It reproduces their
saved reference stiffness, all 66 screw port rows, and the corrected reference
load vector. It supplies finite internal energy, load potential, and exact
point/director derivatives for the parent's separate global assembly. It does
not solve that assembly or establish finite-motion applicability, panel
resistance, or any release.

The new [adapter](../../../../../scripts/thin_bolted_finite_panel_adapter.py)
reuses the frozen [objective plate method](finite-plate-method-v4.md), retained
quadrature helpers, and authenticated JSON/NPZ datums. No CAD was rebuilt, no
existing producer was changed, and no response was solved. The previous
finished-floor field provides load metadata only; its first-order coefficients
and screw demands are not used as a finite response.

## Integration contract

`FinitePanelAdapter(panel, global_indices=None, ndof=None, source_sha256=None)`
accepts an existing panel dictionary. `prepare_adapters(panels, panel_offsets,
ndof, source_sha256)` builds six adapters without changing the old offsets.
The optional `ndof` includes appended global coordinates such as shaft gauges.
An evaluator accepts either the local `[u,v,outward_w]` coefficient vector or
the full global vector. When both lengths coincide, the vector is interpreted
as local.

- `response(q, tangent=True)`, also named `internal`, returns `energy_nmm`,
  `gradient_n`, and `hessian_csr` on the supplied global map. Local derivatives
  are also returned as `local_gradient_n` and `local_hessian_csr`.
- `point_port(q, reference_xyz, tangent=True, allow_edge_extension=False)`
  returns `position_xyz_mm`, `reference_position_xyz_mm`, `J_csr`, and the
  three sparse `H_xyz_csr` matrices. The reference point includes its complete
  midsurface offset. Back contact uses `-t/2`; a hold point is supplied at the
  saved front plus 100 mm, so its offset is approximately `t/2+100` once.
- `screw_port(q, source_axis, tangent=True)` retains the source axis ID,
  panel, receiver, midpoint, projected ring dimensions, and finite center/ring
  positions. Its reference Jacobian exactly retains the saved midpoint
  lateral rows and annular axial average.
- Both port functions return the positive outward `normal_xyz`,
  `normal_J_csr`, and three `normal_H_xyz_csr` matrices, including the retained
  left-handed panel embedding. Compact coefficient indices and derivative
  blocks are available for independent virtual-work auditing.
- `prepare_case_load(panel_case, integrated, accessory, body_loads)` returns
  a load object whose `external(q, tangent=True)` has the same potential,
  gradient, and Hessian contract. Use the frozen panel case dictionary and
  source-owned load rows. The object records their canonical hash and source
  pins; assembly provenance and physical action auditing remain parent-owned.

Pass the parent's complete global source-pin set into the constructor,
including `fea/current_response_materials.py` at
`72af0456272d91282928014d8fde557d347e36df6b7bdf23bcc41ef923d0d135`.
Default direct-helper pins alone do not independently authenticate every
transitively imported material file. The saved K reference coupon confirms
the six adopted section targets, while the assembly gate must authenticate
the material source used by its own run.

The cubic basis has at most 16 active nodes at an ordinary quadrature point.
Integration groups points by shared support and assembles local blocks into
sparse matrices. It stores no dense global point Hessians. The energy/residual
path uses a vectorized first-derivative chain rule; full tangents reuse the
frozen analytic metric/normal Hessians. The six reference coupon groups took
about 15.1 seconds in total with one BLAS thread; this is a coupon observation,
not a nonlinear solver performance promise.

## Retained energy measure and objective ports

The rectangle contributes reference area. Full bores subtract that area from
all six energy measures. The explicit 3 mm head-seat scenario and kicker bevel
subtract membrane factors `1-h/t` and bending/twist factors `1-(h/t)^3`
separately. This exactly reproduces the frozen conditional linear plate K;
it does not resolve free hole-edge stresses, actual veneer properties, or
seat pressure. The combined transient point set also supplies the retained
bore/bevel mass measure, normalized to exact source panel mass. Head-seat mass
distribution remains part of the source-centroid/generalized correction
scenario.

The projected-ring finite extension is

`p = r_center + n_center * [n_center · (mean_ring(r) - r_center)]`.

The projected ring uses the retained 9 mm owner head and conditional 5 mm bore.
At the reference configuration this gives point lateral displacement and the
saved ring average of outward displacement. The finite expression transforms
under common rigid motion and has analytic first/second derivatives. It is
an explicit screw-port scenario, without a manufacturer seating law, axial
stiffness bound, or physical screw moment capacity.

For the original accessory in the center gap, the accepted finite extension
is `r_edge + delta_x*r_x + delta_y*r_y + z*n_edge`. Only a stated gap offset
within 2 mm is admitted; ordinary outside-panel queries fail. The saved
1.5875/1.6125 mm edge gaps retain their exact reference wrench and an objective
finite extension. This is not a physical accessory attachment qualification.

## Constant world loads and explicit generalized corrections

Gravity remains constant in world coordinates. A source point load has
potential `-F·(p(q)-p(0))`, gradient `-J(q).T·F`, and full Hessian
`-sum(F_i*H_i)`. Uniform net panel/proportional accessory mass uses the
retained midsurface mass quadrature. Point metal shares retain their source
offsets. The original upper accessory and climber keep their saved world
points and the full front/back lever convention.

The old least-norm rigid-wrench RHS correction is unchanged. The adapter also
names a separate fixed `reference_port_alignment_correction`: source-world
ports and the old explicitly nominal offsets differ by about `1e-7` mm because
the recorded axes are orthogonal only to tolerance. Its largest coefficient
force is `4.024e-7` N. This term reconciles the reference vector exactly without
moving any world datum.

Each correction contributes `-delta_f·q` and zero Hessian. `external()` exports
their individual potentials, generalized vectors, and current rigid-generator
wrenches, plus their combined contribution. They have no assigned physical
traction or point-force interpretation. A global wrench audit must include
these contributions or reject the resulting state; a physical-force table
alone is incomplete. The current generator uses the deformed coefficient
positions, so the correction's moment can vary with q.

## Observed coupons and limits

Twelve focused tests pass, covering aperture/bevel reference stiffness, sparse
embedding, nonlinear derivatives, frozen point jets, annular screw rows,
20° rigid motion, nonzero-warp objectivity, spatial force/director duals,
constant-force potential, named reference alignment, and rejected inputs.
Ruff passes on all three new Python files.

| Saved-panel check | Largest observed difference |
| --- | ---: |
| Reference H versus saved K, relative Frobenius norm | `5.668e-16` |
| All 66 reference screw Jacobians, maximum coefficient | `3.497e-15` |
| Corrected reference RHS | `0` N |
| Retained mass/case load versus saved NPZ | `1.421e-14` N |
| External gradient central directional coupon | `2.805e-7` N |
| External Hessian central directional coupon | `2.058e-10` N/mm |

Exact orthogonal synthetic embeddings preserve rigid-motion energy/ports to
roundoff. The four retained main-panel frames have
`||A.T*A-I||F = 4.477e-10`. Their 20° world-rotation coupons therefore report
small coordinate-precision differences rather than replacing the source axes:
maximum internal energy `8.739e-12` Nmm, gravity work difference
`5.740e-4` Nmm, and physical-plus-generalized wrench bookkeeping differences
`7.919e-7` N / `0.001149` Nmm. The receipt records its metric-defect-scaled
work allowance explicitly. Exact kicker axes close gravity work within
`7.276e-12` Nmm. These numerical allowances are not strength or displacement
limits.

Reference agreement supplies method readiness only. Signed hole subtraction
does not establish local hole/hold-footprint capacity or integration
convergence of a finite response. The conditional APA zero-Poisson section
proxy is not a qualified ply laminate; Hillman properties, actual seats,
contact/support movement, global equilibrium, and response convergence remain
separate evidence. Every release flag remains false.

Reproduce with:

```sh
UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache OPENBLAS_NUM_THREADS=1 uv run --offline pytest -q tests/test_thin_bolted_finite_panel_adapter.py
UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache uv run --offline ruff check scripts/thin_bolted_finite_panel_adapter.py scripts/check_thin_bolted_finite_panel_adapter.py tests/test_thin_bolted_finite_panel_adapter.py
UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache OPENBLAS_NUM_THREADS=1 uv run --offline python -m scripts.check_thin_bolted_finite_panel_adapter --out /tmp/finite-panel-adapter-reproduced.json
```

Wall-clock fields can vary. Source pins, numerical checks, and evaluator
semantics define the reproducible method; output filename reuse is rejected.
