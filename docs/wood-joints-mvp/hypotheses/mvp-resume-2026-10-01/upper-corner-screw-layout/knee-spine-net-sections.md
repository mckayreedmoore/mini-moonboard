# Two outer knee spine nominal opening sections

**Parent attempt02 is complete.** All **600 evaluated opening-section trace
limits** have reported nominal reference indices below 1.0 under the stated
hypotheses. The global normal reference sum is **0.09634385826188308** and the
global same-state combined shear bound/Fv is **0.38257055105473975**, both at
`knee_outer_right_spine` in `k12-right`. These are finite nominal comparisons,
not member or complete-joint acceptance.

The [frozen producer](knee-spine-net-sections.py) covers the two bodies excluded
from [remaining-net-sections](remaining-net-sections.md): `knee_outer_left_spine`
and `knee_outer_right_spine`. This closes their finite nominal opening-section
comparison gap. The tables below are copied from the saved parent results;
this annotation performs no replay or mechanical arithmetic.

The source is the six original simultaneous states at **250 lb × 2 plus
300 N horizontal force and a 100 mm hold lever**: `a12-rear`, `a12-forward`,
`a12-left`, `k12-right`, `k12-rear` and `a1-rear`. The calculator authenticates
their saved load identities and retains the recorded dead-load factor and
source force-state limits. Later hold-lever, duration and gravity sensitivities
are separate inputs. This producer applies none of those sensitivities.

## Saved geometry and finite coverage

Both saved rectangular blanks are **38.1 × 139.7 × 276.3 mm**, with grain
along global Z, section u along global X and section v along global Y. Each
finished record contains six bounding planes and four complete transverse
cylinders of radius 3.75 mm through the 38.1 mm width. The following coordinates
are copied from the saved cylinder/interval records and apply to both bodies.

| Feature suffix | Saved grain center station (mm) | Saved grain opening interval (mm) | Global Y center (mm) |
| --- | ---: | --- | ---: |
| `facet008` | 31.75 | 28.0 to 35.5 | -137.6 |
| `facet009` | 73.80000000000001 | 70.05000000000001 to 77.55000000000001 | -137.6 |
| `facet007` | 191.61555301851 | 187.86555301851 to 195.36555301851 | -106.2280866515 |
| `facet006` | 226.08755295886 | 222.33755295886 to 229.83755295886002 | -77.30264421564 |

The 7.5 mm bore diameter is the saved geometric envelope, not a drilling or
purchased-hardware instruction. Neither STEP file is imported into CAD.
Delivered STEP bytes are authenticated against explicit pins, the member
geometry binding and the finished-feature register binding.

The completed parent calculation passed the retained geometry gates for both
assigned records: the frame, plane positions and trim areas, transverse axes,
full-width cylinder intervals, disjoint grain opening bands and
rectangle-minus-cylinder volume. No unsupported geometry was reported in
attempt02. An unsupported feature still stops the frozen producer with
`UNSUPPORTED_GEOMETRY`, the exact body and feature or station; it is not
replaced with an assumed rectangle.

The producer reuses `section(geom, station)` from the existing authenticated
[corner-timber-sections.py](corner-timber-sections.py). A cylinder removes its
actual chord interval from v across the full u width. Each active opening
therefore leaves two actual retained rectangles; an exact tangency can retain
one. Section bounds are in the saved grain/u/v frame, including the asymmetric
net centroid. No square-block section or gross-section resistance is substituted.

Only existing saved stations touching a bore or its tangency are compared,
with both before/after limits and all six cases. Both bodies have 58 saved
stations and signed arrays of shape `(116, 6)` per half and case. The output
records the exact selected station and trace indices and verifies coverage
of all four openings. Each body has 25 recorded opening/tangency stations,
300 evaluated trace limits, minimum evaluated net area
5036.819999999989 mm² and at most two material regions. The total is the
reported 600 limits. There is no added station search or continuous-station
maximum certificate.

## Nominal method and unchanged references

The calculator reuses `nominal_section(wrench, regions, refs)` and
`rectangular_known_answer(refs)` from the authenticated
[corner worksheet](corner-net-section.md). The parent completed the existing
translated-rectangle coupon once as part of attempt02. Importing the
producer runs neither the coupon nor a section calculation.

Each comparison retains the complete saved negative-grain-half internal cut
`[N, Vu, Vv, T, Mu, Mv]` in N and N·mm, with positive N in tension. The saved
opposed positive-half vector is retained in the output and compared for closure;
it is not another reversed tension/compression state. The source before/after
limits preserve concentrated actions and free couples already in the saved
cut. Nothing is reallocated to individual fasteners or omitted from torque.

The existing nominal hypotheses remain explicit:

1. A common longitudinal strain plane spans the retained rectangles; continuous
   grain-end bridges are assumed to maintain it.
2. Transverse forces share in proportion to retained area, with every regional
   centroid-offset moment retained.
3. Equal longitudinal shear moduli across regions and in both transverse
   directions, common twist and nominal free warping give regional torque
   proportional to each rectangle's Saint-Venant J.
4. In each region and the same signed state, the nominal shear bound is
   `1.5 × hypot(Vu_j, Vv_j) / A_j + tau_T_j`, compared with the unchanged Fv.

The helper translates the entire wrench to the actual net centroid, fits the
normal stress plane from the full retained-area second-moment matrix, and
reconstructs all six original components from regional forces, moments and
offsets. Its existing closure bounds remain 1e-7 N and 1e-6 N·mm. The saved
opposed-half comparison retains the source's 0.1 N and 2 N·mm bounds. These
are arithmetic accounting bounds, not strength criteria. No balancing free
couple is introduced. Rectangle torsion uses the same fixed 200 odd terms and
authenticated `torsion_faces` definition from `member_stability.py`.

The following values are copied unchanged from each spine's saved conditional
material binding. These bodies use the **nominal 2×6** scenario; its CF values
happen to equal the corner helper's nominal 4×6 values. The producer authenticates
the 2×6 membership and CF-only arithmetic against the existing material packet.

| Existing conditional DF-L No. 2 CF-only reference | MPa |
| --- | ---: |
| Ft parallel | 5.15383107664335 |
| Fb | 8.066866033006981 |
| Fc parallel | 10.238714580355017 |
| Fv parallel | 1.241056312770305 |

The recorded scenario remains normal duration, dry service, unincised stock,
normal temperature and Cfu = Cr = 1, without calculated or credited CL/CP.
No regional size factor, duration correction or new torsion allowable is added.
The normal diagnostic sums mean axial stress/Ft or Fc with the actual bending
stress/Fb at the same rectangle corner. Separate total tension, compression
and absolute bending comparisons are also retained. The compression diagnostic
is not NDS 3.9-3 and supplies no new interaction law.

Every peak selects an existing complete comparison and its region/corner
witness. Separate transverse and torsional peaks remain separate diagnostics;
they are never summed across cuts, regions or cases. The combined shear witness
retains its own two contributions.

## Completed finite peaks

All values below are copied from the saved `per_block.peaks` records. The
right-body value is also the global peak over both bodies for each listed
comparison. No independent peak values are summed.

| Nominal comparison | `knee_outer_left_spine` peak | `knee_outer_right_spine` / global peak | Saved limit, trace index and region |
| --- | ---: | ---: | --- |
| Axial-plus-bending reference sum | 0.09618748067541498 | 0.09634385826188308 | after / 77 / region 1 |
| Total tension / Ft | 0.1281898157874449 | 0.12902640019327621 | after / 77 / region 0 |
| Total compression / Fc | 0.07709830357930347 | 0.07718668710695667 | after / 77 / region 1 |
| Absolute bending / Fb | 0.08999183488166848 | 0.09031237830179582 | after / 77 / region 1 |
| Same-state combined shear bound / Fv | 0.3738444971110511 | 0.38257055105473975 | before / 76 / region 0 |
| Separate transverse shear / Fv | 0.11610216970426661 | 0.11653491979981757 | after / 77 / region 0 |
| Separate torsional shear / Fv | 0.2673621150627805 | 0.27314422345697353 | before / 76 / region 0 |

Every left-body peak is in `a12-left` at exact saved station
**191.61555301851246 mm**, station index 38, intersecting
`knee_outer_left_spine/facet007`. Every right-body/global peak is in
`k12-right` at exact saved station **191.61555301851178 mm**, station index 38,
intersecting `knee_outer_right_spine/facet007`. The table's before/after limit
and region apply to each body's own peak record.

The normal-sum, compression and bending corner is
`[19.049999999999955, 69.85000000000001] mm` on the left and
`[-19.049999999999955, 69.85000000000001] mm` on the right, in saved u/v.
The tension corner is `[-19.049999999999955, -69.85000000000001] mm` on the
left and `[19.049999999999955, -69.85000000000001] mm` on the right.

The combined-shear witnesses retain these contributions from their own
before-limit cut and region 0; they do not use the separately governing
after-limit transverse peak:

| Body | Same-state transverse bound (MPa) | Same-state torsional peak (MPa) | Recorded combined bound / Fv |
| --- | ---: | ---: | ---: |
| `knee_outer_left_spine` | 0.13215063243982558 | 0.3318114406942844 | 0.3738444971110511 |
| `knee_outer_right_spine` | 0.13580423464847918 | 0.33898736281801983 | 0.38257055105473975 |

The saved full-wrench accounting reports the following componentwise maximum
absolute errors in `[N, Vu, Vv, T, Mu, Mv]` order, with force entries in N
and moment entries in N·mm:

```text
Opposed half sum:
[3.268496584496461e-13, 6.821573242080035e-13, 4.879652237832488e-12,
 1.5825207810848951e-10, 3.5312952562094324e-09, 1.1141381150991947e-09]

Regional reconstruction:
[5.684341886080802e-14, 5.684341886080802e-14, 5.684341886080802e-14,
 3.637978807091713e-12, 7.275957614183426e-12, 3.637978807091713e-12]
```

Zero balancing free couples were added. The report retains the complete
source and opposed cuts, net-centroid shifts, regional forces/moments and
corner stresses for all 600 limits. Its comparison flag includes the four
normal diagnostics and the same-state combined shear bound; complete-member
and complete-joint acceptance remain false.

## Frozen inputs and producer

All thirteen input pins, including the two delivered STEP files, were
authenticated during source-only preparation. Ruff format/check passed then.
The parent execution receipt records authentication of these inputs and the
producer before and after arithmetic. The current annotation reads the saved
checks and receipt only; it does not execute producer functions.

| Input | SHA-256 |
| --- | --- |
| `../member-screen-attempt02/four-screw-layout01/member-results.json` | `54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5` |
| `../member-screen-attempt02/four-screw-layout01/geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| `../member-screen-attempt02/four-screw-layout01/action-section-arrays.npz` | `ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf` |
| `../../current-finished-feature-register-2026-10-01/surfaces.json` | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |
| `corner-net-section.py` | `8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5` |
| `corner-timber-sections.py` | `d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633` |
| `../member_stability.py` | `eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72` |
| `../../hardware-material-specification-2026-09-30/material-inputs.json` | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |
| `operators-attempt02/model-inputs.json` | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `../../evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_left_spine.step` | `081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0` |
| `../../evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_right_spine.step` | `f70ade3760f1615cc31f687bc4cf4c334d27db3b8b41e35e615e15b92c4e1faa` |

Frozen producer SHA-256:
`3121c3b8d49c6fde81dbb7a8a2700aace62249acbc494f4dfee2d85fc5e96fc6`.
The initial source-only [preparation record](rawlocal/knee-spine-net-sections/preparation.json)
is preserved with its original producer binding
`f1227f7be8ca74dd37895be98353fc4e5b77e9a000e0276e9d9eaee1389e9115`;
it does not bind the corrected producer. It is ignored local evidence.
Preserved preparation SHA-256:
`5dcb226ac2378d880d0596ff21d56fb419b52b2ed5f9f16cbf5017e6cbcf3358`.

## Completed parent execution and retained limits

The parent reported attempt01 stopped before the coupon and nominal section
arithmetic at `UNSUPPORTED_GEOMETRY: knee_outer_left_spine: changed member kind,
replaced bores or recess`. The guard incorrectly compared the member-screen
record's outer `member_kind` with the nested source descriptor's kind. Both
frozen spine records have outer `member_kind = timber` and nested
`geometry.source_descriptor.member_kind = candidate_block`, with no replaced
bore features or recess. The correction binds those two exact schema levels.
The frozen geometry/features and delivered STEP hashes remain unchanged, and
each spine still has the same four cylindrical bore records. All geometry,
cut, full-wrench and volume gates are retained. No nominal comparison result
is claimed from the stopped attempt.

The corrected producer passed Ruff format/check and source/hash inspection.
Attempt01 failure evidence and the initial preparation record are preserved.
The parent completed the following attempt02 command once; no replay is needed:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-spine-net-sections.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-spine-net-sections/attempt02
```

The producer authenticated inputs and its own bytes before and after arithmetic.
It wrote `checks.json`, `producer.py.snapshot` and a hashed `receipt.json`,
including runtime versions, the coupon, all evaluated cuts and opposed halves,
actual section integrals and centroids, regional stresses and torque shares,
full-wrench recovery, finite coverage counts and separately named peak witnesses.
Execution used Python **3.12.3** and NumPy **2.5.2**. The receipt records one
completed rectangle known answer and 600 evaluated limits. The artifact hashes
below were verified when annotating this worksheet; the producer and executed
snapshot remain byte-identical.

| Completed artifact | SHA-256 |
| --- | --- |
| [Attempt02 checks](rawlocal/knee-spine-net-sections/attempt02/checks.json) | `6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85` |
| [Attempt02 execution receipt](rawlocal/knee-spine-net-sections/attempt02/receipt.json) | `81e75fa6105901209321663c81dad521629c463142bca193eda32fbdf7dc52ab` |
| [Attempt02 producer snapshot](rawlocal/knee-spine-net-sections/attempt02/producer.py.snapshot) | `3121c3b8d49c6fde81dbb7a8a2700aace62249acbc494f4dfee2d85fc5e96fc6` |

The original global force scope remains the saved simultaneous force vectors
from `coupled_two_receiver_frame_clearance/v1`. Fixed-force seating freedoms
do not change those vectors. The saved representative position is not a unique
pose or an envelope of all permitted seating positions. The output preserves
`all_source_rank300_gates_met = false` and
`strict_tangent_stability_transferred = false`; the nominal section results
do not repair those source limitations. The unchanged saved dead-load factor
is **1.1111358300342407**, with the recorded 25 kg accessory allowance and
original stiffness/material/contact hypotheses. No local shaft-field result
is transferred into these timber cuts or used to revise the global frame forces.

The finite two-body nominal comparison is complete. The producer, this
worksheet and attempt02 evidence remain active for integration and recovery.
Attempt01 and the initial preparation record remain historical evidence.
No raw evidence is proposed for pruning. Ownership is ready to return to the
parent for its shared summary/index update and commit.

This finite nominal comparison supplies no bore-wall concentration, local notch,
splitting, grain-end bridge strength, opening compatibility solution, common-knee-
bolt clearance solution or new capacity. Source seating/stability and unverified
floor assumptions retain their recorded limits. This packet ran saved-data
arithmetic only; it performed no software tests, agent review, new
frame/native/CAD run or physical work. Complete-member
acceptance, complete-joint acceptance, formal qualification and physical release
remain false.
