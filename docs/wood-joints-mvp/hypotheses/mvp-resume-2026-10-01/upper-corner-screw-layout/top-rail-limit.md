# Top-rail shear and torsion isolation

The current `base_rail_top` has a **1.021523661201856** compatible face
shear/torsion reference ratio under the unchanged normal-duration material
scenario. The signed saved state reproduces [member-replay.md](member-replay.md)
and the exact saved member/stability results. This is an exceedance of the
declared intact-prism screen, not observed wood failure, complete joint
resistance, or a climber rating. The current source remains unchanged.

## Governing simultaneous state

The governing state is **K12 rear, nominal gap, station 2116.3359375 mm,
after the station, cut-array index 435, negative-grain half**. Station runs
from `[-1130.3, 1469.831199167, 2186.798514971]` toward +X; the member is
2257.425 mm long. The cut centroid is
`[986.0359375, 1469.8311991671449, 2186.7985149710453]` mm. Its saved finite
profile is `BORE_FREE_FULL_RECTANGLE`, 38.10000000009086 by
139.6999999993129 mm, area 5322.569999986515 mm². The centroid moment shift
from the saved cut datum is included.

| Signed action on the negative half | Value |
| --- | ---: |
| N, tension positive | −1294.9783616768916 N |
| Vu | −334.7392440851142 N |
| Vv | +1040.454937657572 N |
| T | −53849.85035965866 N mm |
| Mu | −144177.8097854061 N mm |
| Mv | −13632.653071273062 N mm |

The basis is L = `[1,0,0]`, u = `[0,0.6427876099290708,0.7660444429154699]`,
v = `[0,-0.76604444291547,0.6427876099290709]`. The frozen elastic orientation
assigns **R to u and T to v**; this is a response scenario, not a growth-ring
observation. Its longitudinal shear-modulus ratio is
`G_Lu/G_Lv = G_LR/G_LT = 0.064/0.078 = 0.8205128205128205`.

The load remains 250 lb with a 2× vertical force, 300 N signed horizontal
force, the original 100 mm front-face lever, gravity, and the separate 25 kg
accessory allowance. The same-state dead-load factor is 1.1111358300342407.
The saved nominal forces have finite bounded seating; they do not establish
a unique pose, a seating-motion envelope, or strict assembled tangent stability.

## Preserved stress method

The adapter calls the existing `member_stability.shear_check` and
`torsion_faces`; it does not replace them with independent action maxima or
an easier scalar sum. The existing aligned orthotropic Saint-Venant stress
function obeys

```text
Phi_uu/G_Lv + Phi_vv/G_Lu = -2*twist
tau_Lu = Phi_v; tau_Lv = -Phi_u; T = 2*integral(Phi)
v' = sqrt(G_Lu/G_Lv)*v
```

The unchanged 200-odd-term rectangle series gives face coefficients
`cu = 1.2278290237034532e-5` and `cv = 1.8097518872110283e-5` mm⁻³. The
same cut's parabolic transverse maxima are 0.0943357938230861 and
0.29321970523456 MPa; its torsional face magnitudes are 0.6611840919367674
and 0.9745486831442373 MPa. Signed superposition places them on compatible
face midpoints, with the other longitudinal shear component zero there:

| Position relative to section centroid, u/v mm | τLu, MPa | τLv, MPa |
| --- | ---: | ---: |
| 0 / −69.85 | −0.7555198857598535 | 0 |
| 0 / +69.85 | +0.5668482981136813 | 0 |
| **−19.05 / 0** | **0** | **+1.2677683883787974** |
| +19.05 / 0 | 0 | −0.6813289779096773 |

The governing shear magnitude is **1.2677683883787974 MPa (183.8742590163
psi)** against **1.241056312770305 MPa (180 psi)**, an excess of
0.0267120756084924 MPa, or **2.1523661201856%**. This is a sampled face
lower bound on the declared field's maximum. The existing conservative
same-cut component rectangle bound is 1.1891650427870186; it retains both
components of this same wrench. Its exceedance alone would not establish a
face exceedance. The coefficient-5 isotropic sensitivity, 1.31802738754122,
is not substituted for the adopted method. The fixed-action R/T swap
sensitivity, 0.9944045731922664, supplies no credit: it changes the frozen
material assignment without recomputing the compatible frame response.

The free-warping prismatic field has no local concentration factor. The
[FPL Wood Handbook, Chapter 9](https://research.fs.usda.gov/download/treesearch/37423.pdf),
printed pp. 9–4 and 9–7, discusses the limits near concentrated loads and
supports and the rectangular torsion stress equation (9–24). The aligned
orthotropic transformation above is the existing repository method; FPL's
rectangle equation does not itself qualify this complete joint or provide
a torsion allowable.

## Fv and material/duration basis

The pinned [material inputs](../../hardware-material-specification-2026-09-30/material-inputs.json)
use the **2024 NDS Supplement Table 4A, United States Douglas Fir–Larch,
No. 2, 2 in. & wider dimension lumber** conditional row. The top rail is
nominal 2×6, with source dimensions 38.1×139.7 mm. Fv is 180 psi at normal
duration and dry service. The 2×6 CF entries (Fb/Ft/Fc = 1.3/1.3/1.1) do
not adjust Fv. Dry service, normal temperature and unincised material remain
the declared scenario; delivered species, grade, moisture, treatment and
growth rings have not been observed.

The adopted shear comparison uses **CD = 1** and explicitly applies the same
longitudinal Fv to both shear components. No separate NDS torsion resistance,
torsional shape enhancement, or normal/shear interaction resistance is
established. The dynamic 2× force multiplier does not select a load-duration
factor. No impact or short-duration credit is assigned. The cached
[NDS Chapter 2](../../upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf),
§§2.3.2.1–.3 and Table 2.3.2, keeps duration adjustment separate from demand;
its impact factor is excluded for connections. This isolation makes no new
duration selection.

Primary cached sources are the
[official Supplement Chapter 4](../../hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf),
printed pp. 32 and 34, SHA256
`1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b`,
and Chapter 2, SHA256
`6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100`.
The material-input SHA256 is
`0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a`.

## Intact cuts and local exclusions

The top rail has 243 frozen stations, each with before/after traces in six
cases: **2916 signed cuts**, including **2256 bore-free comparisons**.
The saved geometry marks 188 stations as full rectangles and 55 as
non-applicable bore/passage slices. Their ten distinct excluded intervals,
in mm from the member start, are:

```text
41.7000–49.2000       293.1549–297.2951     693.1549–697.2951
994.0500–1001.5500   1058.2299–1062.3701   1198.2299–1202.3701
1259.0500–1266.5500  1563.3049–1567.4451   1963.3049–1967.4451
2208.2250–2215.7250
```

The new 1058.2299–1062.3701 and 1198.2299–1202.3701 slices retain the moved
center-screw shaft envelopes. The earlier saved holes are also retained;
the STEP has not been recut or repaired. These are analysis exclusions,
not pilot or purchased-length instructions. No resistance is assigned to
bore slices, disconnected ligaments, notches, bearing/seats, splitting or
other joint-disturbed stresses.

The governing cut is **52.1890625 mm before** the right outer-cleat contact
footprint, which begins at 2168.525 mm, and **95.6390625 mm before** its
2211.975 mm bolt station. It is only 141.0890625 mm from the right end.
The source records all 24 `contact_83_*` main-upper-right panel contact
footprints crossing the cut, including zero-force rows. Bore-free status
does not prove absence of load-introduction disturbance. The source supplies
point actions and free couples, not integrated local solid tractions; no
new disturbed-region cutoff is invented, and the governing screen is not
discarded to reduce its ratio. Local transfer and concentration behavior
remain outside this intact-prism comparison, as already recorded.

## Exact top-rail receiver roles

The saved census is **146 connector actions plus 200 discrete nodal body
loads per case**. The following are all its direct neighboring bodies;
the complete row identities, roles, footprints and same-state receiver
wrenches are retained in `rawlocal/top-rail-limit/source01/result.json`.

| Neighbor | Existing direct top-rail roles | Connector rows | Footprint station range, mm |
| --- | --- | --- | ---: |
| `top_outer_left_cleat` | Two `rail_{1,2}` bolts: four lateral components, two outer-seat tension ties; 16 contact rows | Lateral 1800–1803; axial 1850–1851; contact 1834–1849 | 0–88.9 |
| `top_outer_right_cleat` | Two `rail_{1,2}` bolts: four lateral components, two outer-seat tension ties; 16 contact rows | Lateral 1808–1811; axial 1886–1887; contact 1870–1885 | 2168.525–2257.425 |
| `top_center_left_cleat` | Two `rail_{1,2}` bolts: four lateral components, two outer-seat tension ties; four contact rows | Lateral 132–135; axial 1566–1567; contact listed in raw receipt | 952.35–1041.25 |
| `top_center_right_cleat` | Two `rail_{1,2}` bolts: four lateral components, two outer-seat tension ties; four contact rows | Lateral 140–143; axial 1570–1571; contact listed in raw receipt | 1219.35–1308.25 |
| `base_principal_center_left` | Four timber contact rows | Listed in raw receipt | 1041.25–1079.35 |
| `base_principal_center_right` | Four timber contact rows | Listed in raw receipt | 1181.25–1219.35 |
| `base_side_left` / `base_side_right` | Four timber contact rows each at their respective end faces | Listed in raw receipt | 0 / 2257.425 |
| `main_upper_left` | Three Hillman screws: six lateral components, three non-qualifying parametric withdrawal rows; 24 panel contacts | Lateral 290–295; withdrawal 1483–1485; contact listed in raw receipt | 0–1128.7125 |
| `main_upper_right` | Three Hillman screws: six lateral components, three non-qualifying parametric withdrawal rows; 24 panel contacts | Lateral 314–319; withdrawal 1495–1497; contact listed in raw receipt | 1128.7125–2257.425 |

The center `principal_{1,2}` bolt receivers and outer `side_{1,2}` receivers
belong to the same blocks' other faces; they are not direct top-rail bolt
rows. The rail's eight cleat bolts remain at 45.45, 997.8, 1262.8 and
2211.975 mm, two axes at each station. The six panel screws are
`round_panel_upper_{left,right}_center_4` and
`round_panel_upper_{left,right}_edge_{1,2}`, at 1060.3/1200.3,
695.225/1565.375 and 295.225/1965.375 mm respectively. They retain the
66-screw candidate policy and purchased Hillman policy; their parametric
laws do not establish product resistance. This packet assigns no new
receiver, hardware or complete-block capacity.

## Targeted adapter and parent command

[top-rail-limit.py](top-rail-limit.py) imports the existing action restoration,
cut partition and compatible stress helpers. Source isolation consumes the
saved top-rail arrays. Future replay reconstructs only this rail's connector
point forces/free couples from the parent's new simultaneous raw force
vectors and the unchanged D; its discrete body loads remain unchanged.
It uses the frozen station/rectangle census and evaluates every applicable
top-rail trace, preserving before/after ordering and same-state centroid
shifts. It performs no CAD, native, frame, stability, or mechanical solve.

For a load-lever-only parent response, the adapter requires explicit hashes,
the original physical model payload and row identities, byte-identical H and D, unchanged gravity
columns, unchanged rail F/W loads, full live-force scales, unchanged
connection-law metadata, and the existing complete six-case zero/nominal
force-state contract. These are input applicability checks for this adapter;
they add no physical acceptance gate. An incompatible input is not a member
failure. The adapter does not calculate or certify the changed load lever;
that preparation and the compatible response belong to the parent. The
parent comparison authenticates the new operator assessment and its model
hash. Only the added `diagnostic_load_scenario` metadata is removed for
comparison with the original physical model; that metadata must itself
match the authenticated preparation. Geometry, material and connection
payloads remain exactly equal.

The source calculation completed once using the existing `.venv`, Python
3.12.3 and NumPy 2.5.2, with input hashes equal before/after.
Maximum top-rail whole-body residuals were 1.09424e-11 N and 7.56700e-10 N mm.
No software tests, geometry change, native or frame solve were performed
by this adapter. The parent subsequently executed the targeted 50 mm replay
below, using the new compatible frame forces.

| Top-rail face peak by case | Station / trace | Ratio |
| --- | --- | ---: |
| A12 rear | 77.7875 / after | 0.9004278919359908 |
| A12 forward | 77.7875 / after | 0.7486245792643700 |
| A12 left | 55.5625 / after | 0.9055710494364231 |
| K12 right | 2186.88046875 / after | **1.0056226011512608** |
| K12 rear | 2116.3359375 / after | **1.0215236612018560** |
| A1 rear | 49.201 / before | 0.0793132619530462 |

Each is a same-case, same-station result. A future smaller face peak does
not by itself establish an all-section pass; the existing same-cut component
bound, bore exclusions and local-joint scope remain visible.

## Completed 50 mm load-lever comparison

The parent replay consumed the completed [load-lever sensitivity](load-lever.md),
with unchanged 250 lb × 2 and signed 300 N forces, gravity, geometry,
connection laws, H and D. It restored this rail's actions from the new
simultaneous force vectors and evaluated the same 2916 signed cuts,
including 2256 bore-free comparisons. The 100 mm source remains the
current analytical basis; 50 mm is not an adopted hold measurement.

| Case | Original 100 mm face ratio | Hypothetical 50 mm face ratio |
| --- | ---: | ---: |
| A12 rear | 0.900428 | 0.849811 |
| A12 forward | 0.748625 | 0.684440 |
| A12 left | 0.905571 | 0.817012 |
| K12 right | 1.005623 | 0.909239 |
| K12 rear | 1.021524 | **0.960773** |
| A1 rear | 0.079313 | 0.078287 |

The governing 50 mm witness remains K12 rear, station 2116.3359375 mm,
after the station. Its signed `[N, Vu, Vv, T, Mu, Mv]` is
`[-1188.799919, -314.314532, 978.507024, -50648.510909, -134664.247249,
-12060.398681]` N / N mm. The same-cut component rectangle upper bound
is **1.118391**. Thus a face value below one does not establish an
all-section pass; interior maximum and local transfer limits remain.
No new duration factor, material allowance or resistance is assigned.

The maintained producer revision adds only the authenticated diagnostic
metadata allowance described above. The original `b6508135…` source is
preserved at `rawlocal/top-rail-limit/original-b6508135.py.snapshot`; its
`source01` result remains unchanged. The executed new producer is also
saved beside `parent-load-lever01/result.json`.

Source isolation reproduction, with a fresh output child:

```sh
packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$packet/top-rail-limit.py" \
  --output "$packet/rawlocal/top-rail-limit/source02"
```

For the parent-produced load-lever frame, set the two directories and three
hashes from its freeze/receipts, then run only this bounded member replay:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$packet/top-rail-limit.py" \
  --frame "$parent_frame" --clearance "$parent_clearance" \
  --operators-sha256 "$parent_operators_sha256" \
  --comparison-sha256 "$parent_comparison_sha256" \
  --response-sha256 "$parent_response_sha256" \
  --output "$packet/rawlocal/top-rail-limit/parent-load-lever01"
```

| Artifact, relative to this packet unless stated | SHA256 |
| --- | --- |
| `top-rail-limit.py` | `12e238bdb0bd0bf9260a94f5c6fc56727d090c87bb84cbe25558defc75fd5509` |
| `rawlocal/top-rail-limit/original-b6508135.py.snapshot` | `b650813514886b36bdbe355105e4b3401ca767d05921b610d482eb2e4cb1c113` |
| `rawlocal/top-rail-limit/parent-load-lever01/result.json` | `a760249a95b7a59a901b79cac1fbf5b89fbf1173dccfa0a4d696342a55a53ee2` |
| Same output `cuts.csv` | `94dccfdf57449dbe884cb37c0af3f280aaa5914a761089951b2a366cea3af69f` |
| `rawlocal/top-rail-limit/source01/result.json` | `e0139a6a89d038d2cea7cd28d4f0b38a67ecc84c79c3da96e5d528c887f08b65` |
| Same output `cuts.csv` | `199f585496fb93df4ff1a0e5d758b7ae5fa2b65b76d6a8a87c6f6ecf16b10288` |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `../member-screen-attempt02/four-screw-layout01/member-results.json` | `54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5` |
| Same member packet `geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Same member packet `action-section-arrays.npz` | `ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf` |
| `../member-stability-attempt01/four-screw-layout01/checks.json` | `aceebc0beaee1cc178450b52b2a16a32924803c3210dc0c115c0fee7a3a7c574` |
| Adopted `../member_stability.py` | `eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72` |
| Adopted `../member_screen.py` | `5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9` |

The raw receipt pins the remaining consumed helpers and exact finished STEP.
`bottom_corner_checks.py` is pinned at its current
`5df7a264…ad19e26` revision for `saved_actions` restoration; this differs
from the earlier stability receipt's whole-file revision. No bottom-member
resistance code is called. The unchanged adopted shear/cut helpers and
saved governing result remain bound separately.

The two owned files and the completed load-lever comparison are returned
to the parent for publication.
The ignored source receipt remains local reproducible evidence; nothing is
pruned or archived by this task. The parent retains current left/right joint
mechanics, heavy execution and comparison ownership; resistance, washer
product and 24-duty work remain with their existing owners.
