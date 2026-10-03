# Twelve remaining block net-section references

The parent completed the finite saved-data calculation once. All **2,304
evaluated opening-section traces** of the twelve assigned low-load blocks have
normal reference sums and same-state combined shear bounds below 1.0. The
largest normal reference sum is **0.0017979156913967664**; the largest combined
shear bound/Fv is **0.03220185062683178**, both at `top_center_right_cleat` in
`k12-rear`.

The source remains the frozen six-case, 250 lb dynamic envelope with a
**100 mm hold lever**. This result does not inherit a later 50 mm sensitivity
or change the frame response. The finite nominal comparisons for these twelve
blocks are complete under the hypotheses below; these blocks do not govern
the evaluated nominal section references.

This is a nominal section/reference comparison under stated MVP hypotheses.
Complete-joint acceptance, formal qualification and physical release remain
false. These arithmetic comparisons supply no local bore-wall concentration,
notch, splitting, endbridge strength or continuous-station maximum certificate.

## Scope and geometry

The four outer corners, six header duties and two outer knee spines belong to
other owners and are excluded. The assigned set is:

| Group | Block identities | Grain length |
| --- | --- | ---: |
| Center | `bottom_center_left_cleat`, `bottom_center_right_cleat`, `top_center_left_cleat`, `top_center_right_cleat` | 119.7 mm each |
| Left service | `left_service_inner_lower_cleat`, `left_service_inner_upper_cleat`, `left_service_outer_lower_cleat`, `left_service_outer_upper_cleat` | 119.7 mm each |
| Right service | `wj04_lower_full_stock_cleat`, `wj06_outer_lower_right_cleat`, `wj06_outer_upper_right_cleat` | 119.7 mm each |
| Right upper crosscut | `wj04_upper_g7_crosscut_full_stock_cleat` | 86.9 mm |

Each saved finished block has six bounding planes, an 88.9 × 88.9 mm section
and four complete transverse cylindrical bores of radius 3.75 mm. Their saved
trim intervals reach both stock faces. No matching saved BRep section exists
for these twelve blocks. The calculator instead reuses the existing analytic
rectangle-minus-through-cylinder interpretation, authenticated against the
saved planes, full cylinder patches, STEP binding and finished volume. It does
not read geometry into a CAD kernel or regenerate a solid.

For the eleven standard blocks, bore center stations are 43.35, 59.85 and
76.35 mm from the source grain start; two bores share the central station.
The crosscut block uses 26.95, 43.45 and 59.95 mm. Single slots leave two
retained rectangles; paired slots leave three. Adjacent opening bands have
9 mm of intact grain length between them. That geometry identifies the
bridges; it does not establish their strength or compatibility.

## Explicit MVP section hypotheses

The calculator reuses `corner-net-section.py` rather than defining another
regional stress method. A common longitudinal strain plane spans the retained
regions. Continuous grain-end bridges are assumed to maintain that plane.
Transverse forces share in proportion to retained area. Torque shares in
proportion to each rectangle's Saint-Venant torsional constant under common
twist, equal longitudinal shear moduli in both transverse directions and across
regions, and nominal free warping. These are declared section hypotheses,
not measured timber behavior or a coupled opening solution.

Each complete saved cut retains `[N, Vu, Vv, T, Mu, Mv]` in N and N·mm. The
negative-grain-half internal trace uses positive N in tension. Its opposite
half is checked for equilibrium, not treated as a second reversed
tension/compression state. Saved before/after limits retain concentrated
actions and free couples already present in the source producer.

The section calculation shifts the complete wrench to the actual net centroid,
fits the normal stress plane using the retained area's full second-moment
matrix, and restores every regional centroid-offset moment. The six recovered
components must reproduce the source cut without balancing free couples.
The normal reference sum combines mean axial stress/Ft or Fc with bending
stress/Fb at retained rectangle corners. Separate total tension and compression
comparisons are also recorded; no new normal/shear strength interaction is used.

For each region in the same state, the nominal shear bound adds
`1.5 × hypot(Vu, Vv) / A` and the rectangular torsional peak. Dividing by the
unchanged Fv gives the comparison index. The torsion series is the existing
200-odd-term rectangle helper. Equal shear moduli are the stated local MVP
approximation; this calculation does not change the source model's R/T axes.

Only existing saved bore/tangency stations and both limits are evaluated.
Reported peaks are maxima over that finite recorded set. The point-action
cut convention remains the source convention; no new physical wall-traction
distribution is asserted inside an opening.

## Completed comparisons

Each block contributes 16 recorded opening/tangency stations, two limits per
station and six cases: **192 traces per block**. The minimum evaluated retained
area is 6,569.710 mm², with up to three material regions. All displayed indices
below are copied from the completed output. Peak stations are displayed to
0.01 mm; the output retains the exact source station and trace index.

| Block | Peak normal reference sum | Governing normal case / station / limit | Peak same-state shear bound/Fv | Governing shear case / station / limit |
| --- | ---: | --- | ---: | --- |
| `bottom_center_left_cleat` | 0.00047239801972544 | `a1-rear` / 59.85 mm / before | 0.0036212512974902384 | `a12-left` / 59.85 mm / before |
| `bottom_center_right_cleat` | 0.00044069488644381 | `k12-right` / 59.85 mm / after | 0.0037396556183029533 | `k12-right` / 59.85 mm / before |
| `top_center_left_cleat` | 0.0012878565162332545 | `a12-left` / 59.85 mm / after | 0.011020547756070984 | `a12-left` / 76.35 mm / after |
| `top_center_right_cleat` | 0.0017979156913967664 | `k12-rear` / 59.85 mm / before | 0.03220185062683178 | `k12-rear` / 59.85 mm / after |
| `left_service_inner_lower_cleat` | 0.0004140264190149238 | `a1-rear` / 59.85 mm / before | 0.004956449928150458 | `a1-rear` / 59.85 mm / before |
| `left_service_inner_upper_cleat` | 0.00048514167445201927 | `a12-left` / 59.85 mm / before | 0.004614126293866521 | `a12-left` / 76.35 mm / after |
| `left_service_outer_lower_cleat` | 0.0003817654355547149 | `k12-right` / 59.85 mm / after | 0.005901735222754546 | `a1-rear` / 59.85 mm / after |
| `left_service_outer_upper_cleat` | 0.0004891807701579732 | `k12-right` / 59.85 mm / before | 0.0036301337257242535 | `a12-left` / 59.85 mm / before |
| `wj04_lower_full_stock_cleat` | 0.0003168344099769291 | `a12-left` / 59.85 mm / after | 0.004006857648377656 | `a12-left` / 59.85 mm / after |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 0.0002891017769585345 | `k12-right` / 43.45 mm / after | 0.004980133627207524 | `k12-right` / 43.45 mm / before |
| `wj06_outer_lower_right_cleat` | 0.0003839372580106402 | `a12-left` / 59.85 mm / after | 0.004240947354532426 | `a12-left` / 59.85 mm / before |
| `wj06_outer_upper_right_cleat` | 0.000493346458709994 | `a12-left` / 59.85 mm / after | 0.0037679611524272013 | `k12-right` / 59.85 mm / after |

The separate transverse and torsional peaks below are diagnostic maxima.
They can occur in different cases, cuts or regions and must not be added to
form a fabricated combined state. The preceding table uses the actual
same-state regional sum.

| Block | Peak nominal transverse shear/Fv | Peak nominal torsional shear/Fv |
| --- | ---: | ---: |
| `bottom_center_left_cleat` | 0.002345348733395372 | 0.003253851797336523 |
| `bottom_center_right_cleat` | 0.001703298725792136 | 0.002480208374195468 |
| `top_center_left_cleat` | 0.006664198516864376 | 0.0070104447572580265 |
| `top_center_right_cleat` | 0.009924398494950781 | 0.022277452131881002 |
| `left_service_inner_lower_cleat` | 0.0018250078888475817 | 0.003131442039302877 |
| `left_service_inner_upper_cleat` | 0.002776998099908326 | 0.002868903400363168 |
| `left_service_outer_lower_cleat` | 0.0019441217844025954 | 0.004417247595468836 |
| `left_service_outer_upper_cleat` | 0.0023445493246932337 | 0.002886292960761069 |
| `wj04_lower_full_stock_cleat` | 0.0015105998604402955 | 0.0027945018798104567 |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 0.002751050994715327 | 0.003299612362403409 |
| `wj06_outer_lower_right_cleat` | 0.001956549163568432 | 0.004058516580287806 |
| `wj06_outer_upper_right_cleat` | 0.002377088764163692 | 0.0029350744159392372 |

## Engineering appendix

The per-member source binding is conditional DF-L No. 2 with its existing
standard-section CF factors. For these blocks, CF-only references are
Fb = 9.307922346 MPa, Ft = 5.946728165 MPa, Fc = 10.704110698 MPa and
Fv = 1.241056313 MPa. The recorded scenario uses normal duration, dry service,
unincised stock, normal temperature and Cfu = Cr = 1; CL and CP are not
calculated or credited. These are design-reference inputs, not observed
failure loads or qualified properties of delivered stock.

The six case IDs are `a12-rear`, `a12-forward`, `a12-left`, `k12-right`,
`k12-rear` and `a1-rear`. Core input identities are:

| Input | SHA-256 |
| --- | --- |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `operators-attempt02/model-inputs.json` | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| `rawlocal/joint-register/attempt01/register.json` | `79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca` |
| `../member-screen-attempt02/four-screw-layout01/member-results.json` | `54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5` |
| `../member-screen-attempt02/four-screw-layout01/geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| `../member-screen-attempt02/four-screw-layout01/action-section-arrays.npz` | `ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf` |
| `../../current-finished-feature-register-2026-10-01/surfaces.json` | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |
| `corner-net-section.py` | `8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5` |
| `corner-timber-sections.py` | `d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633` |
| `remaining-net-sections.py` | `acd60cee627331fdfeb06eb02321221f09a666bcea7e3997a9e51e616c98c129` |

The parent confirmed all fifteen source pins and twelve finished STEP pins.
The executed producer and saved snapshot are byte-identical to the producer
hash above. Completed output:

`docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/remaining-net-sections/attempt01/checks.json`

SHA-256: `80600628f956f5a957efca382d2c4e2ca9110cefbff8c7aee21a1995a430892f`.

This is ignored local evidence; the numerical tables and scope in this
maintained worksheet remain available in a fresh clone. The output preserves
all finite cut summaries, section regions, per-block metric witnesses and
full regional details for each block's normal and combined-shear peaks.

| Completed accounting comparison | Maximum absolute component error |
| --- | ---: |
| Opposed half force sum | 4.583000645652646e-12 N |
| Opposed half moment sum | 4.066235126387596e-9 N·mm |
| Regional force recovery | 7.105427357601002e-15 N |
| Regional moment recovery | 4.547473508864641e-13 N·mm |

The opposed halves satisfy the existing whole-member closure bounds of 0.1 N
and 2 N·mm. Regional recovery preserves all six source components without
added balancing free couples. Neither accounting comparison supplies a
strength or compatibility result. Complete-joint acceptance, formal
qualification and physical-release flags remain false in the saved output.

Completed parent execution command from repository root, recorded for provenance:

```bash
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/remaining-net-sections.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/remaining-net-sections/attempt01
```

The ignored output contains `checks.json` and the exact executed
`producer.py.snapshot`. Only this producer and maintained worksheet are
publication files. No tests, native runs, frame solves, CAD operations,
supplier searches, shared documentation edits, staging or commits were run
by this worker.
