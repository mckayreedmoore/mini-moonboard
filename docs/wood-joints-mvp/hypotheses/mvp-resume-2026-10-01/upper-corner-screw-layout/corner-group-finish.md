# Finite corner-group working assessment

## Question and scope

Complete the simplest supported static assessment of the four current corner
cleats under all six saved climbing cases. Preserve the current 100 mm hold
lever, K20 frame response, first-order bolt model, smooth-shank hypothesis,
washer/contact actions and original mapped body weight. No loads, geometry,
hardware or material references change.

This leaf adds one static postprocessor to the completed transfer and finished
geometry evidence. It does not add a local mechanics model. Completion means a
conditional working assessment of the stated nominal timber and longitudinal
tear-out hypotheses; it does not establish complete crossed-group fracture
resistance or formal joint qualification.

## Frozen sources

| Input | SHA-256 |
| --- | --- |
| Top first-order transfer, 12 states | `b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe` |
| Bottom first-order transfer, 12 states | `4d255ba5ebd8f1f93fb41ef90511eb3da49906f4729f33f5f63766e0a0bd78ed` |
| Corrected top timber geometry and references, attempt02 | `8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813` |
| Top finished longitudinal paths | `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6` |
| Bottom finished longitudinal paths | `ec421ee35b9477842660faa6d2528bd957f8a06620f7d84c46d9654e40ce146a` |
| Bottom CF-only material references | `54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5` |

Top cleats use the corrected 88.9 × 139.7 mm section. Bottom cleats use the
saved 88.9 × 88.9 mm section. All four are approximately 119.7 mm along grain.
Each has two rail bores and two perpendicular side bores. The producer checks
right-handed frames, stock margins and pairwise cylinder separation before
using disjoint-void area integrals. It does not reinterpret the old top
88.9 × 88.9 mm descriptor as the corrected geometry.

## One finite method

1. Recover every saved applied action and body weight once. Check the full
   signed force and moment against the saved physical residual.
2. Reuse the supported, nonnegative half-cosine bore-wall pressure mapping.
   Preserve each original axial quadrature measure. Its analytical angular
   integrals reproduce the original force and moment; no balancing couple is
   added. Washer and face actions retain their saved quadrature locations.
3. Take finite planes normal to grain and both transverse section directions
   at recorded action coordinates, bore centers/tangencies, wall radial
   extents, the stock midpoint and two interior edge stations. Retain both
   limits at point actions. Retain all six internal force/moment components
   and check the opposite half using the complete physical residual.
4. Integrate exact plane area, first moments and second moments for the
   rectangle minus disjoint through strips or circles. Solve the explicit
   affine normal-traction hypothesis from axial force and both signed bending
   moments. For grain-normal planes reuse the existing retained-rectangle
   nominal normal, transverse shear and torsion sharing calculation. This
   preserves torque and regional force offsets; it is not a 3D elastic stress
   recovery or a proved maximum over continuous stations.
5. On transverse planes report the nominal opening stress and whether the
   whole affine normal field is compressive. Perpendicular tension and
   transverse shear/torsion capacities remain null. Compression-only normal
   traction would not itself establish fracture resistance or shear transfer.

The analytical coupon combines the existing translated rectangular full-wrench
coupon with a rectangle containing one circular void. For the latter,
`sigma = 2 + 0.5 p - 0.25 q` MPa on `[2,6] × [-4,2]` mm minus a unit-radius
circle at `(4,-1)` mm must be recovered exactly, including the translated
moments; the corner range is 2.5–6 MPa. A separate angular half-pressure
known answer checks force `[5, -10/pi, 0]` N. Parent executes these in the one
postprocessor run. They are analytical method checks, not software tests or
new mechanics solves.

## Applicable resistance comparisons and limits

[NDS 2024 Appendix E](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf)
provides local longitudinal multiple-fastener checks. Equation E.3 is
`Z'RT,i = n_i Fv' Acritical / 2`; with two equal shear lines this becomes
`n_i Fv' × one-plane area`. Use the saved minimum finished one-plane area;
do not multiply by two again.

The producer integrates positive and negative grain components separately
over each distributed wall pressure. These are conservative longitudinal
channel bounds, not a replacement for the full wrench. It compares each
single channel and the actual two-bolt rail grain row with E.3 references.
The side bolts are separate rows. Four orthogonal bolts are not treated as a
single four-bolt row. Neither these comparisons nor the inherited individual
spacing checks establish E.4 group tear-out resistance, perpendicular splitting
or eccentric interaction for the whole crossed group.

[NDS 2024 Chapter 3, §3.8.2](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
and [Chapter 11, §§11.1.2–11.1.3](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf)
do not supply a general sawn-lumber perpendicular tensile resistance for this
crossed, eccentric connection. No `Ft_perp` or empirical crossed-group
capacity is invented.

The [JRC connection guidance](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_5_Leijten.pdf),
slides 63–70, presents EC5 §8.1.4 beam splitting:
`F90,Rk = 14 b w sqrt(he / (1 - he/h))`, with demand defined from the beam
shears on either side of the connection. The present crossed groups,
washer/seat actions and signed end couples do not establish that single
connection/loaded-edge topology. Shortness alone is not the exclusion.
Summing absolute wall forces does not supply the missing applicability.
No EC5 capacity or cross-code design conversion is adopted.

Existing inward washer forces are included once. No additional preload,
friction, tie force or bolt-as-splitting-reinforcement capacity is credited.
Local cracking remains the precise unsupported working assumption.

## Parent execution

Executed producer SHA-256:
`182523c1be28071f74097eed9f36e39978a519b8f6efd6d8447f86e922debd19`.
The parent executed the coupon and all mechanical arithmetic. The worker
authenticated sources and outputs and annotated this worksheet.

From the repository root, the parent executed:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-group-finish.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/corner-group-finish/attempt03
```

`build(output)` is the same bounded API. Any replay requires a fresh owned
child. The completed output includes `checks.json`, ignored compressed cut
records, the frozen producer snapshot and a source/output hash receipt.
Sources were authenticated before and after calculation.

Attempt01 stopped at a helper-output key binding; attempt02 completed the
arithmetic but stopped when serializing an external cached-PDF path. Both are
preserved. The parent corrected the three nested comparison-key bindings and
allowed absolute paths for external frozen inputs. The final attempt uses the
same equations, loads, geometry, references and tolerances. These were producer
defects, not changes to the engineering hypothesis.

## Result

**The finite conditional static assessment is complete.** All four blocks and
24 case/block states are present. The analytical coupons passed. The saved
inventory contains 101,276 cut limits, including 51,312 transverse limits.
All longitudinal reference comparisons reported in the summary are below one.

| Nominal comparison | Maximum reference utilization | Deciding block/case |
| --- | ---: | --- |
| Grain tension | 7.81% | Top right, K12 rear |
| Grain compression | 2.86% | Top right, K12 rear |
| Grain bending | 4.30% | Top right, K12 rear |
| Existing axial-plus-bending reference sum | 5.37% | Top right, K12 rear |
| Regional grain shear plus torsion | 33.49% | Top right, K12 right |
| Single longitudinal wall-pressure channel / E.3 reference | 16.98% | Top right side bolt 2, K12 rear, negative grain direction |
| Two-bolt rail-row longitudinal channel / E.3 reference | 9.91% | Top right, K12 rear, positive grain direction |

These are separate reference comparisons with their own simultaneous force
and moment witnesses, not a new combined failure criterion. For the deciding
regional shear/torsion cut at grain station 75.537504553 mm, before the event,
the signed `[N, Vu, Vv, T, Mu, Mv]` is approximately
`[552.3403, -996.9831, -347.3327, -34512.7714, -33310.2701, -28421.4997]`
in N and N·mm. Torque was retained.

The parent extracted the existing stored `axial_plus_bending_reference_sum`
over 326,848 longitudinal corners. Its maximum is 0.05373012958451201 at the
top-right K12-rear grain-normal cut, station 59.850000000419755 mm, before the
event, region 2, corner `(u,v) = (-44.45,69.85)` mm. The same-state signed cut
is approximately
`[596.4668, -371.1151, -673.1028, -17629.3784, -28258.7565, -38400.3953]`
in N and N·mm. This existing sum uses mean axial stress and bending with their
respective references. The grain-tension row uses total normal stress. The
extraction reuses saved comparisons and adds no model or interaction equation.

The maximum nominal transverse opening stress is **0.169987975 MPa**, at the
top-right K12-right transverse-v cut, station −69.8499 mm, before the event.
Positive nominal opening occurs at 22,334 transverse limits. This is an affine
traction diagnostic, not a recovered physical crack stress or failure verdict.
No perpendicular tension resistance or combined crossed-group capacity has
been assigned. A fully compression-only affine normal route therefore does
not close this entire set of modeled cuts.

The disjoint-cylinder certificates pass for all four blocks. Minimum crossed
bore wall separation is approximately 8.25 mm at the top and 9.00 mm at the
bottom. Maximum opposite-half disagreements are 0.000132633 N in force and
0.013532640 N·mm in moment. The complete source residual is preserved rather
than canceled with an added force or couple.

**Disposition:** the current timber plus bolt/seat approach has favorable
results under the explicit nominal sharing hypotheses. The remaining local
cracking assumption is still unqualified. The result records
`conditional_static_assessment_complete = true`, while
`complete_joint_acceptance`, `formal_criterion_acceptance`,
`fabrication_release` and `physical_release` remain false. It supports the
conditional working route, not a claim that every corner failure mode has
been checked.

### Authentication

The worker independently authenticated all **53 source files and four output
files** against the final receipt. The frozen snapshot matches the executed
producer.

| Final artifact | SHA-256 |
| --- | --- |
| [Checks](rawlocal/corner-group-finish/attempt03/checks.json) | `2ae3a84f273823dc6ca751e6fdddab8e0d70425ee7b34e1e38ebc79d5b672f23` |
| [Compressed signed cut inventory](rawlocal/corner-group-finish/attempt03/cuts.jsonl.gz) | `a60131eaeff3e5bb46579156d31fbfe3423de2848ac2bbb202901013697a5627` |
| [Producer snapshot](rawlocal/corner-group-finish/attempt03/producer.py.snapshot) | `182523c1be28071f74097eed9f36e39978a519b8f6efd6d8447f86e922debd19` |
| [Receipt](rawlocal/corner-group-finish/attempt03/receipt.json) | `f1d8ad0f204be457f5b8eba2e8185828456251ae7fb67aa945bb7477bacd2f62` |
| [Existing normal-sum extraction](rawlocal/corner-group-finish/attempt03/normal-sum.json) | `93f7a4ebd714927fa4614adde78d2e4252abe57cf24130106681ab063c475425` |

The additional normal-sum extraction binds its source to the authenticated
compressed inventory hash `a60131ea…`. The worker authenticated this added
artifact separately; the original four-output receipt is preserved.

The compressed 32.22 MB inventory is ignored raw evidence. No native, frame,
CAD or new local mechanics model was run for this leaf. No software tests,
geometry changes, hardware changes or worker staging/commits occurred.
