# Corner nominal net-section worksheet

[The frozen producer](corner-net-section.py) completed **one serialized parent
calculation**: one rectangle known answer and the eight frozen cosine-wall cut
limits, each with three actual retained rectangular ligaments. All six signed
components close in the coupon and the eight cuts / 24 regions. Source forces,
loading and lever arms are unchanged. This packet supplies nominal stress comparisons
under the owner's explicit MVP working hypotheses; it assigns no new capacity.

The [wall worksheet](corner-bore-wall.md#parent-execution-receipt-and-frozen-producer)
already records the completed parent wall run, checks SHA256
`b95e7fc3d1d60c94ae449c681d4cec12221345a5ba0eb865f3ca225086350caf`.
Its producer remains `0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185`.

## Fixed inputs and references

The eight cuts are the before/after limits of right K12-rear
s=62.973880402093315 / 59.85000000087682 mm and left A12-left
s=56.39975267961501 / 59.85000000074149 mm. The source is the actual
119.7 mm grain length and 88.9×139.7 mm cleat blank with four cylinders.
Use each saved cut's signed `[N,V_u,V_v,T,M_u,M_v]` and retained bounds directly.
Regions 0/1/2 are named `low_v_outer`, `middle`, `high_v_outer` in the saved
right-handed `[grain,u,v]` frame; the actual left frame is retained.

| Existing conditional CF-only reference | MPa |
| --- | ---: |
| Ft parallel | 5.15383107664335 |
| Fb | 8.066866033006981 |
| Fc parallel | 10.238714580355017 |
| Fv parallel | 1.241056312770305 |

These values come unchanged from the frozen timber packet, checks SHA256
`8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813`.
The producer also binds the existing material JSON and verifies its nominal
4×6 CF-only arithmetic. It adds no regional size factor, load factor,
CL/CP assumption, characteristic-to-design conversion or torsion enhancement.

## Explicit MVP working hypotheses

1. A longitudinal strain plane maintained by the continuous grain-end bridges
   gives `sigma_g=a+b*u+c*v` across all three retained net regions. This is
   longitudinal plane-section compatibility, not a transverse plane-strain
   constraint or a measured local strain field.
2. Each regional transverse force is `V_j=(A_j/A)*V`, in the same state.
3. Equal parallel-grain shear moduli across regions and in both transverse
   directions, common regional twist and nominal free warping give
   `T_j=(J_j/sum J)*T_c`, where `T_c` is the cut torque at the net centroid.
4. Each region's conservative nominal shear bound is
   `1.5*hypot(V_uj,V_vj)/A_j + tau_Tj`, compared with the existing Fv for both
   longitudinal shear components. Both terms belong to that region and cut.

## Exact normal integrals and full-wrench accounting

For each retained rectangle, area, centroid, first moments and second moments
are analytic integrals of its saved bounds. They are summed without sampling
or replacing the section by a gross rectangle. Let net centroid be `(u_c,v_c)`
and central area integrals be `I_uu=integral((u-u_c)^2 dA)`,
`I_uv=integral((u-u_c)(v-v_c) dA)`, `I_vv=integral((v-v_c)^2 dA)`.
Translate the **complete signed wrench** to that centroid:

```text
M_c = M_cut - [0,u_c,v_c] × [N,V_u,V_v]
mean = N/A
[I_uu I_uv; I_uv I_vv] [b;c] = [-M_v,c; M_u,c]
a = mean - b*u_c - c*v_c
```

Positive N is tension. Since the frame is right handed, normal traction has
`M_u=integral(v*sigma_g dA)` and `M_v=-integral(u*sigma_g dA)`.
Each region's normal force and centroid bending moments are integrated from
the same affine field. Four corners give its exact linear stress extrema.

For a regional centroid `r_j=[0,u_j,v_j]`, the producer stores its signed
centroid wrench and the offset `r_j×F_j`. Summing
`[F_j; M_j+r_j×F_j]` reconstructs all six original cut components. Thus
area-shared forces contribute their actual offset torque; J sharing applies
to the remaining centroid torque, not an added balancing couple. All original
nonbore actions and W remain inside the saved cut once.

## Rectangular torsion and nominal comparisons

For rectangle dimensions `long >= short`, use the standard Saint-Venant
constant, distinct from polar area moment:

```text
J = long*short^3/3 * [1 - 192*short/(pi^5*long)
                       * sum_odd(tanh(n*pi*long/(2*short))/n^5)]
tau_Tj = |T_j| * max(rectangle face shear coefficients)
```

The fixed 200 odd terms match the existing scalar `torsion_faces` routine in
[member_stability.py](../member_stability.py#L80), SHA256
`eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72`.
Only that authenticated function is loaded; no mechanics module or solve is
invoked. J's series tail bound is reported. The stress coefficient uses equal
shear moduli. The primary mechanics basis is the [FPL Wood Handbook,
Chapter 9, equations 9–9, 9–11 and 9–24 / Figures 9–3 and
9–6](https://research.fs.usda.gov/download/treesearch/37423.pdf), reusing
`/tmp/wood-handbook-ch9.pdf`, SHA256
`84829761afb977291236c85bd51fdb00a3a56109625b0c09e7a0915ae684a9b4`.

Every corner records total tension/Ft, total compression/Fc, signed-field
bending magnitude/Fb, and an axial-plus-bending reference sum. The latter
uses the same cut's `N/A` with the actual signed combined bending stress at
that corner; it does not add separate case peaks. These are nominal diagnostic
comparisons, including a compression sum that is not NDS 3.9-3. Each ligament
also records its same-state shear bound/Fv. No new normal/shear interaction
law is supplied.

## Rectangle known answer and reusable API

The coupon rectangle is `u=[2,6]`, `v=[-4,2] mm`, with A=24 mm² and centroid
`[4,-1] mm`. Its original-datum cut is
`[102,12,-6,30,-120,-424] N/N·mm`. Analytical results are:

```text
sigma_g = 2 + 0.5*u - 0.25*v MPa
sigma_min/max = [2.5,6] MPa
centroid cut = [102,12,-6,42,-18,-16] N/N·mm
transverse shear bound = 1.5*sqrt(180)/24 MPa
```

The same coupon checks the standard unit-square values J≈0.140577014955 mm⁴
and peak stress coefficient≈4.8 mm⁻³ (the latter is a graph precision check).
The parent run returned these known answers and completed the coupon assertions.

Public API: `area_properties(regions)`, `rectangle_torsion(width,depth)`,
`nominal_section(wrench,regions,refs)`, `rectangular_known_answer(refs)`.
Importing the module executes no coupon or section calculation. The parent
CLI writes all eight cuts / 24 regional comparisons, exact integrals, affine
coefficients, corner stresses, J shares, signed regional forces and moments,
offsets, reconstruction errors, reference ratios and their named witnesses.
The peak witnesses select completed comparisons; demands from different
cuts are never combined.

## Completed parent execution receipt

The completed calculation records all eight cuts and 24 named regional
comparisons under the stated working hypotheses. The following peak ratios
and their exact witnesses are read from that result; each comparison retains
its own complete signed state.

| Nominal comparison | Peak ratio | Actual witness |
| --- | ---: | --- |
| Total tension / Ft | 0.07805318 | Right K12-rear, s=59.85000000087682 mm, before, `low_v_outer`, u=44.45 / v=-69.85 mm |
| Total compression / Fc | 0.02855838 | Right K12-rear, s=59.85000000087682 mm, after, `high_v_outer`, u=-44.45 / v=69.85 mm |
| Absolute bending / Fb | 0.04303309 | Right K12-rear, s=59.85000000087682 mm, before, `high_v_outer`, u=-44.45 / v=69.85 mm |
| Axial-plus-bending diagnostic | 0.05373013 | Right K12-rear, s=59.85000000087682 mm, before, `high_v_outer`, u=-44.45 / v=69.85 mm |
| Same-state shear-plus-torsion bound / Fv | 0.24197697 | Right K12-rear, s=62.973880402093315 mm, after, `middle` |

The deciding shear witness retains transverse bound 0.1141480152947547 MPa
and torsional peak 0.18615903174313722 MPa from that same cut and region.
Zero balancing free couples were added. These are nominal reference
comparisons; no capacity or qualification is assigned.

| Execution artifact | SHA256 |
| --- | --- |
| [Completed checks](rawlocal/corner-net-section/attempt01/checks.json) | `691df118160b4f831df4dd69e989379524d8f1212e1c53a728ed2962a3642d73` |
| [Execution receipt](rawlocal/corner-net-section/attempt01/receipt.json) | `b2fb99a89e1bbb49bf66e840e3cec713d61f28d9d3c04ea7d3d5fa72beb1457b` |
| [Executed producer snapshot](rawlocal/corner-net-section/attempt01/producer.py.snapshot) | `8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5` |

The receipt binds 44 source/producer pins. Execution used Python 3.12.3 and
NumPy 2.5.2. The producer remains byte-identical and its nominal-section API
is reusable by the separate header and remaining-component calculators.

## Frozen producer and recorded parent command

Producer SHA256:
`8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5`.
The [source-only preparation receipt](rawlocal/corner-net-section/preparation.json)
records initial readiness. Ruff format/check and source pins were the only
worker checks; the parent executed the following command once and owns integration:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-net-section.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/corner-net-section/attempt01
```

The CLI authenticated sources before and after arithmetic and wrote
`checks.json`, its producer snapshot and hashed receipt in the owned output child.
This nominal calculation establishes no full 3D compatibility, notch/bore
concentration, group/splitting resistance or elastic qualification. It supplies
no Ft-perpendicular/F90, arbitrary capacity or new qualification workstream.
