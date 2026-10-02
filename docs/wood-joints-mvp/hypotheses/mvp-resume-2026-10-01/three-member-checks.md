# Continuous knee bolts: same-state three-member screen

## Current all-two-receiver clearance replay

The new saved-state replay uses `two-receiver-frame-attempt03/`. The four
continuous knee bolts retain zero modeled lateral clearance while the 88
independent candidate bolts take up their modeled gaps. All six nominal states
have finite fixed-force seating bounds; no unique pose or strict tangent
stability is claimed. Geometry, grain, receiver order and resistance hypotheses
are unchanged.

All 24 bolt cases remain asymmetric. The declared convex-superposition
comparison peaks at **0.919157951** under the conditional 92 ksi scenario,
`knee_outer_left_side_1` in A12-left. The 45 ksi sensitivity is
**1.312488270**, with seven cases above one. Endpoint embedding and convex
complete-assembly admissibility remain unvalidated; this arithmetic supplies
no normative three-member capacity or complete-joint acceptance.

Current local result:
`three-member-screen-attempt01/all-two-receiver/screen.json`, SHA-256
`306aa4a8e4c6113d4a0258d09564292d07095131ef2b4621370d7284e75e0377`.
Its signed plane, receiver, group and contact records remain separate and
source-bound. Use this fresh child and frame path with the replay command
below. The earlier result and producer snapshots remain preserved.

The subsequent [static bearing and bending construction](knee-bearing-checks.md)
now preserves every receiver wrench through an explicit affine bearing field:
24 bolt states, 72 receiver fields and 96 normalized endpoint fields. Peak
nominal bearing and smooth-shank steel indices are 0.359589 and 0.592568.
All endpoint fields fit the declared nominal bearing/plastic-bending bounds;
static embedding is constructed within that model. Displacement/contact
embedding, common-bolt clearance, actual thread sections and the complete
physical convex admissible set remain unvalidated. No normative asymmetric
capacity or complete-joint acceptance follows.

## Preserved six-joint comparison

The following calculation uses the six nominal-gap states from
[all-outer-corner-frame-attempt01](all-outer-corner-frame-attempt01/), including
both top corners, both bottom corners and both left outer service cleats. All
**24 bolt cases are asymmetric**. The declared convex lateral interaction screen
reaches **0.903977959 at conditional Fyb = 92 ksi**, at
`knee_outer_left_side_1` in **a12-left**. The corresponding 45 ksi sensitivity
is **1.289820442**; three bolt cases exceed one at 45 ksi.

These are numerical component comparisons under an unvalidated superposition
assumption. They are not an adopted asymmetric three-member resistance,
adjusted NDS capacity, complete joint qualification or physical release.
The calculation preserves each bolt's simultaneous two-plane vectors, three
receiver wrenches and outer tie, plus the two-bolt group and face-contact
couples. The parent owns the surrounding corner chains and frame integration.

The maintained producer is [three_member_screen.py](three_member_screen.py).
Current ignored results are
[screen.json](three-member-screen-attempt01/all-outer-corners/screen.json),
[bolt-cases.csv](three-member-screen-attempt01/all-outer-corners/bolt-cases.csv),
[plane-states.csv](three-member-screen-attempt01/all-outer-corners/plane-states.csv),
[receiver-wrenches.csv](three-member-screen-attempt01/all-outer-corners/receiver-wrenches.csv),
[group-states.csv](three-member-screen-attempt01/all-outer-corners/group-states.csv),
[contact-states.csv](three-member-screen-attempt01/all-outer-corners/contact-states.csv),
[profile-states.csv](three-member-screen-attempt01/all-outer-corners/profile-states.csv)
and [source-pins.json](three-member-screen-attempt01/all-outer-corners/source-pins.json).
The JSON includes all four-mode/six-mode method boundaries, every endpoint
reference mode, signed action points, separate wrench contributions and exact
remaining gaps. No force is assembled from maxima in different cases.

## Stack, sources and symmetry applicability

| Short name | Physical bolt axis | Group |
| --- | --- | --- |
| L1 | `knee_outer_left_side_1` | BG003 |
| L2 | `knee_outer_left_side_2` | BG003 |
| R1 | `knee_outer_right_side_1` | BG004 |
| R2 | `knee_outer_right_side_2` | BG004 |

Each ordered modeled stack is exterior `knee_outer_*_spine` →
`base_side_*` → `knee_outer_*_inner_frame_block`. Bearing lengths are
**38.1 / 88.9 / 88.9 mm**, with zero modeled interface gap and **215.9 mm**
wood grip. Shaft occupancy is 241.3 mm, not a purchased length or delivered
shank. Left axes point +X; right axes point −X. Both outer grains are +Z;
the middle member's grain is `(0, 0.642787610, 0.766044443)`.
All bolt axes are perpendicular to these proposed grains. Receiver identity,
intervals, directions, interface points and all six original finished STEP
hashes are bound; no new geometry query or model was made.

This reuses the [old BG003 transfer note](../mvp-acceleration-2026-09-28/current-knee-three-member-transfer-attempt01/README.md),
[modeled stack-order packet](../mvp-acceleration-2026-09-28/bolt-groups/three-member-stack-order-attempt01/README.md),
[remaining-joint producer](remaining_joint_screen.py), and maintained
[multi-member NDS helper](../../../../mini_moonboard/nds_2024_multi_member_bolt_yield.py)
and [double-shear helper](../../../../mini_moonboard/bolted_wood_wood_double_shear.py).
The old note's missing signed actions are now supplied for these six saved
states; its hypothetical symmetric references and historical demands are not
used as current resistances.

Let `P1` and `P2` be the signed plane vectors **on each plane's first body**,
in modeled underhead order. The bolt's outer actions are `V0 = P1` and
`V2 = −P2`; its middle action is `Vm = −V0 − V2`. Symmetric action requires
`V0 = V2` and therefore `Vm = −2V0`. The numerical equality tolerance is
`1e−8 N + 1e−10 × max(|V0|, |V2|)`. The implementation also requires matching
outer load-to-grain angles before calling the double-shear helper.

Positive raw scalar force acts along its recorded direction on the first
body, with the opposite action on the second. Moments are `r × F` about the
listed common datum. Outer tie forces are recorded at modeled head/nut seats;
translating the axial action along the bolt line preserves its wrench.

No state meets that condition. Outer vector separation divided by the larger
outer magnitude ranges **0.579949–1.593025**; their magnitude ratio ranges
**0.060550–0.660625** and their angle ranges **9.244°–171.382°**.
Thus the failure is a real force split and direction difference. Unequal side
thickness is separately addressed by the NDS minimum-side-length input rule;
that rule cannot establish equal signed outer actions. Current direct
double-shear references are **null**.

The governing source is [AWC's NDS-2024](https://awc.org/resources/2024-nds/),
with the [pinned official Chapter 12 PDF](../hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf)
and [March 2026 errata](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf):

- §12.3.1 and Tables 12.3.1A/B, printed pp.91–92: single shear and symmetric
  double shear, contacting faces, transverse loading and §12.5 detailing.
- §§12.3.3–12.3.5, pp.92–95: direction-specific bearing, bearing length and
  the shorter unequal side length for double shear (§12.3.5.4).
- §§12.3.6.2 and 12.3.7.1–.2, p.95: Fyb test basis and diameter/thread rules.
- §12.3.8, pp.95–96: four-or-more-member procedures; neither a three-member
  multiplier nor a solution for these unequal outer vectors.
- §12.3.2, p.92, and §12.5: adjustments and detailing remain separate.

The maintained API has no supported route for these actual asymmetric vectors.
[AWC TR12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf)
Table 1-1 supplies the reused single-shear equations; its double-shear
derivation does not supply this independent vector split. The sum below is
an explicitly declared engineering hypothesis, not another NDS provision.

## Declared conservative screen and its precise limits

For each bolt and case, calculate separate two-member endpoint references
`Z1` and `Z2` in the actual plane directions, then:

```text
u1 = |V0| / Z1
u2 = |V2| / Z2
Ulat = u1 + u2
```

The endpoint at plane 1 uses spine/middle lengths 38.1/88.9 mm. The endpoint
at plane 2 uses middle/inner-block lengths 88.9/88.9 mm. Both use conditional
DF-L `G = 0.50`, 6.35 mm smooth body, zero thread bearing, zero face gap,
Fe parallel/perpendicular **5600/4450 psi**, direction-specific Hankinson
bearing and the six existing yield modes with their reduction terms.
[Current material inputs](../hardware-material-specification-2026-09-30/materials.md)
and [fastener inputs](../hardware-material-specification-2026-09-30/fasteners.md)
remain the scenario sources. Each plane's six values are reproduced through
the maintained NDS mode helper using identical inputs.

The conservative interpretation requires **both** of the following:

1. Each normalized two-member endpoint, lifted to this same complete
   three-member assembly with the other plane unloaded, is admissible with
   its full receiver wrench, shared middle member and continuous bolt.
2. The complete assembly's lateral admissible set contains zero and is convex
   for those full signed endpoint wrenches.

Under those assumptions, the actual lateral wrench is
`u1 × W1 + u2 × W2 + (1−Ulat) × 0`; `Ulat ≤ 1` is a sufficient convex
combination condition. This accounts for both planes using one shared budget.
It does **not** add capacities, multiply by two planes, or grant a separate
capacity to the middle member. Reusing the 88.9 mm middle interval in distinct
endpoint hypotheses is not proof that both endpoint bearing distributions
can coexist. Endpoint embedding and convexity are **not validated here**.
`Ulat > 1` lies outside this sufficient screen; it alone does not prove that
the actual joint fails.

This lateral construction includes the recorded lateral transfer moments in
its hypothesized endpoint wrenches. It supplies no recovered bolt moment,
axial/lateral interaction surface, washer resistance or wood splitting limit.
The simultaneous outer tie and normal contact wrenches are preserved as
additional demands; they are not included in `Ulat`.

**92 ksi** is the pinned conditional SAE J429 Grade 5 minimum tensile-yield
scenario under the existing ASTM F606 interpretation; exact product conformity
and the applicable Fyb basis remain unverified. **45 ksi** is an unadopted
quarter-inch sensitivity, not a guaranteed quarter-inch product value.
The references are unadjusted `Z`, and no `Z′`, Cg or Cdelta is adopted.

## All 24 current simultaneous bolt cases

`|V0|` and `|V2|` are the complete signed outer-vector magnitudes. The angle
is between those actual outer vectors. `T` is the same bolt's signed outer
tie. `|Mm|` is the middle receiver's **lateral transfer moment** about the
midpoint of that bolt's two interface points, in N·m; it is not steel bending
stress or a bolt bending capacity comparison. Full XYZ forces, moments,
application points, raw rows, scalar signs and endpoint modes remain in the
linked CSVs and JSON.

| Case | Bolt | \|V0\|, N | \|V2\|, N | Outer angle, ° | T, N | \|Mm\|, N·m | U45 | U92 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| a12-rear | L1 | 455.838 | 72.804 | 35.88 | 83.273 | 17.742 | 0.855039 | 0.597996 |
| a12-rear | L2 | 223.051 | 95.368 | 118.52 | 40.117 | 12.506 | 0.519793 | 0.372023 |
| a12-rear | R1 | 58.349 | 10.947 | 11.83 | 100.743 | 2.120 | 0.117780 | 0.083389 |
| a12-rear | R2 | 38.505 | 11.985 | 167.19 | 80.185 | 2.234 | 0.083934 | 0.058702 |
| a12-forward | L1 | 630.174 | 63.101 | 99.08 | 158.748 | 28.589 | 1.179048 | 0.824988 |
| a12-forward | L2 | 394.492 | 89.983 | 136.84 | 18.691 | 20.635 | 0.808917 | 0.565739 |
| a12-forward | R1 | 45.167 | 15.265 | 33.36 | 62.415 | 1.488 | 0.086406 | 0.060430 |
| a12-forward | R2 | 53.363 | 13.710 | 47.30 | 86.262 | 2.009 | 0.095430 | 0.066742 |
| a12-left | L1 | 684.435 | 82.024 | 76.68 | 192.286 | 29.795 | 1.289820 | 0.903978 |
| a12-left | L2 | 437.266 | 119.095 | 140.88 | 47.321 | 23.779 | 0.921714 | 0.644627 |
| a12-left | R1 | 166.728 | 49.765 | 10.27 | 34.219 | 5.249 | 0.337260 | 0.241665 |
| a12-left | R2 | 238.095 | 98.975 | 10.34 | 58.874 | 6.305 | 0.508376 | 0.355547 |
| k12-right | L1 | 163.835 | 47.040 | 9.24 | 19.512 | 5.229 | 0.332871 | 0.239031 |
| k12-right | L2 | 232.137 | 101.635 | 12.36 | 57.312 | 5.984 | 0.506519 | 0.354249 |
| k12-right | R1 | 671.353 | 76.595 | 82.33 | 173.416 | 29.580 | 1.263746 | 0.884425 |
| k12-right | R2 | 419.143 | 115.096 | 139.62 | 71.328 | 22.770 | 0.889365 | 0.622003 |
| k12-rear | L1 | 53.356 | 26.909 | 54.09 | 87.564 | 1.931 | 0.133730 | 0.095857 |
| k12-rear | L2 | 50.529 | 24.324 | 171.38 | 50.392 | 3.319 | 0.115701 | 0.080919 |
| k12-rear | R1 | 448.363 | 60.453 | 40.84 | 91.831 | 17.983 | 0.821440 | 0.574497 |
| k12-rear | R2 | 216.960 | 90.035 | 118.52 | 59.183 | 12.078 | 0.503800 | 0.361019 |
| a1-rear | L1 | 192.601 | 98.896 | 119.38 | 166.653 | 11.382 | 0.467280 | 0.326806 |
| a1-rear | L2 | 8.561 | 141.380 | 168.91 | 75.583 | 6.658 | 0.225255 | 0.157538 |
| a1-rear | R1 | 23.152 | 7.221 | 84.19 | 60.986 | 1.047 | 0.049331 | 0.034826 |
| a1-rear | R2 | 14.126 | 9.332 | 146.46 | 29.637 | 1.000 | 0.036979 | 0.025862 |

For governing L1/a12-left, `V0 = (0, −532.720916, +429.720654) N`,
`V2 = (0, +35.399229, +73.991593) N`, and
`Vm = (0, +497.321688, −503.712247) N`. At the common bolt datum,
the corresponding moments are:

| Receiver | Lateral moment XYZ, N·mm | Simultaneous axial action XYZ, N |
| --- | --- | --- |
| Exterior spine | `(0, +19101.083056, +23679.444730)` | `(+192.285968, 0, 0)` |
| Middle side member | `(0, −15812.156742, −25252.940438)` | `(0, 0, 0)` |
| Inner frame block | `(0, −3288.926315, +1573.495708)` | `(−192.285968, 0, 0)` |

That datum is `(-1174.750000, -106.228087, 331.315553) mm`.
Plane 1 has Z45/Z92 **581.144065 / 829.025949 N**, governing IV/IIIm;
plane 2 has **731.810522 / 1046.372474 N**, governing IV/IV.
Thus U92 is **0.825589485 + 0.078388473**, and U45 is
**1.177737412 + 0.112083030**. Neither middle-resultant cancellation nor a
symmetric double-shear reference replaces those two signed actions.

## Two-bolt group and couple transfer

Both groups have 45.0 mm center spacing with pitch
`(0, 28.925442, 34.472000) mm`. In the middle member that pitch is along
proposed grain; in each outer block it has grain/cross-grain components
34.472000/28.925442 mm in magnitude. The actual two bolt vectors frequently
oppose. Group references therefore cannot be obtained from a count times a
single-bolt value or from the norm of a canceled resultant.

Each group datum is the mean of both bolts' two interface points:
BG003 `(-1174.750000, -91.765365, 348.551553) mm`; BG004
`(+1171.575000, -91.765365, 348.551553) mm`. The table gives the
**middle receiver's total local wrench**, including these two bolts and the
eight adjacent face-contact rows. `C0/C2` are the headward/nutward interface
compression sums; ties act directly on the two outer receivers. Contact is
kept at its actual recorded point and is not apportioned to a bolt. External
post/header/panel actions are outside this local table.

| Case | Group | Middle force XYZ, N | Middle moment XYZ, N·m | C0 / C2, N | Sum ties, N |
| --- | --- | --- | --- | ---: | ---: |
| a12-rear | BG003 | `(81.214, 80.377, -476.739)` | `(13.815, -3.740, -3.113)` | 89.514 / 8.300 | 123.390 |
| a12-rear | BG004 | `(-90.955, 44.874, -13.386)` | `(2.112, 9.687, 1.754)` | 206.736 / 115.782 | 180.927 |
| a12-forward | BG003 | `(9.699, 145.991, -277.260)` | `(21.377, 6.122, -16.130)` | 114.990 / 105.290 | 177.440 |
| a12-forward | BG004 | `(-40.277, -53.123, -107.199)` | `(-0.547, 11.213, 2.782)` | 142.393 / 102.116 | 148.677 |
| a12-left | BG003 | `(95.873, 194.036, -323.170)` | `(23.695, 6.609, -15.356)` | 162.553 / 66.681 | 239.607 |
| a12-left | BG004 | `(-0.391, -110.949, -427.412)` | `(-7.920, 8.202, -2.100)` | 49.939 / 49.548 | 93.093 |
| k12-right | BG003 | `(-3.117, -103.740, -407.647)` | `(-8.181, -7.473, 4.835)` | 28.292 / 31.409 | 76.823 |
| k12-right | BG004 | `(-93.262, 175.239, -333.428)` | `(22.830, -2.083, 15.903)` | 178.434 / 85.171 | 244.744 |
| k12-rear | BG003 | `(86.541, 61.043, -4.851)` | `(2.036, -3.459, -0.823)` | 152.243 / 65.702 | 137.956 |
| k12-rear | BG004 | `(-76.944, 71.233, -463.791)` | `(13.201, 5.499, 4.423)` | 117.657 / 40.713 | 151.014 |
| a1-rear | BG003 | `(132.279, -138.955, -101.147)` | `(-5.612, 23.445, 21.031)` | 286.455 / 154.176 | 242.236 |
| a1-rear | BG004 | `(-51.162, 8.402, -17.005)` | `(0.718, 4.247, 1.092)` | 101.088 / 49.926 | 90.623 |

In BG003/a12-left, the spine/middle interface transmits
`(0, −213.217638, +131.192620) N` to the spine and **−25221.393923 N·mm
about X** at the two-bolt interface center. The middle/inner-block interface
transmits `(0, −19.181355, −191.977221) N` to the middle and
**−1525.945839 N·mm about X**. These group couples survive the large
cancellation between L1 and L2 and are retained in the JSON.
The middle's lateral wrench alone is
`F = (0, +194.036284, −323.169842) N`,
`M = (+23695.448084, +2701.875523, −10330.135255) N·mm`;
normal contact adds `F = (+95.872621, 0, 0) N`,
`M = (0, +3907.227822, −5025.657972) N·mm`.

Across the 24 bolt and twelve group records, action/reaction accounting closes
within **6.6e−14 N / 3.5e−12 N·mm**. This is closure of extracted local
connector actions, not independent verification of frame equilibrium,
continuous bolt bending or member resistance.

## Finished profiles and formal work remaining

BG003 reuses the [72-ray finished-profile query](../mvp-acceleration-2026-09-28/current-knee-three-member-profile-attempt01/README.md)
unchanged. The source grains and receiver intervals match the current knee
register. The new 36-row profile CSV joins each left bolt/receiver's resultant
grain and cross-grain signs to the appropriate existing g±/e± rays, retaining
all three sampled thickness stations and internal void intervals. It performs
no new CAD work and grants no end/edge acceptance. Resultant signs do not
replace checking each signed plane action and its transfer moment.

The smallest source terminal grain distance is **50.212447 mm** and smallest
cross-grain distance **34.952644 mm**, at the second bolt's square block
profiles. The middle side member retains its oblique g− end and the first
bolt's e+ corner intersection. Its second bore is an internal void; the inner
block has separate header bores, including an e+ void starting only
11.202645 mm from bolt 2 at middepth. Terminal distances alone do not establish
net ligaments, splitting or tear-out. BG004's own finished STEP identities
and grip are bound, but no corresponding right-side profile query is consumed;
left measurements are not transferred to it.

| Remaining formal gap | Exact unresolved input or calculation |
| --- | --- |
| Convex endpoint admissibility | Establish both endpoint embeddings and convexity for the complete shared-bolt assembly and its full lateral receiver wrenches, or replace this conditional construction with an applicable validated asymmetric route. |
| Continuous bolt mechanics | Resolve compatible bearing and rotations through the 38.1/88.9/88.9 mm stack and actual steel bending under both simultaneous vector planes. The reported r×F moments are receiver transfer demands. |
| Axial and washer transfer | Resolve same-state tie tension together with bolt lateral/bending actions and supported head/nut/washer metal and wood transfer. Contact patches remain group actions, not per-bolt resistance credits. |
| NDS adjustment and group behavior | Bind Z′, Cg/Cdelta applicability, the oblique two-bolt distribution and both interface couples without multiplying independent plane or bolt references. |
| Finished wood failure modes | Complete signed end/edge/spacing, splitting, net-section and tear-out treatment with the BG003 oblique end/internal bores and BG004's own finished-profile evidence. |
| Hardware and stock | Bind the declared Fyb/product and species/grade/grain assumptions, actual face contact, body/root diameter, thread exposure and nut engagement. For the nominal-D thread allowance, quarter-bearing thresholds are 9.525 / 22.225 / 22.225 mm; actual exposure remains unknown. |
| Parent corner/frame integration | Reconcile these demands with post/spine and inner-block/header connections, member sections and the saved frame's floor, Hillman spring, contact, material and clearance assumptions. No historical case pass transfers. |

## Frozen results, command and retention

The original task source,
[top-and-service-frame-attempt02](top-and-service-frame-attempt02/), was calculated
first. Its [root attempt01 result](three-member-screen-attempt01/screen.json),
CSVs, source receipt and producer snapshot remain immutable. After the parent's
additional bottom clearances, the maintained producer gained `--clearance`
and wrote a separate child. The old and current governing states are both
L1/a12-left:

| Saved source | Maximum U45 | Maximum U92 | States above one, 45 / 92 ksi |
| --- | ---: | ---: | ---: |
| Top plus left services, preserved root | 1.287889099 | 0.902708405 | 3 / 0 |
| All outer corners plus left services, current child | 1.289820442 | 0.903977959 | 3 / 0 |

The redistribution is not uniformly small: L1/a1-rear's simultaneous outer
tie changes from **23.643218 N** to **166.652696 N**. Use the whole selected
source state, including contact and moments, when integrating a joint.

| Binding | SHA-256 |
| --- | --- |
| Current `all-outer-corner-frame-attempt01/comparison.json` | `ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3` |
| Current `response.npz` | `aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901` |
| Current child `screen.json` | `34f2e7a1c362277e8e2640e04a0ac6c23827814f696d55af059ac558d08c3141` |
| Current producer / child snapshot | `9487cc1c3f6442e418adb8a4cb51d825901dc6f40e32fcf615d6d40d7a9cb507` |
| Preserved root `screen.json` | `bd10dbddbf756ec70064fd70ba8a2245cf3ce7b486c97b8455f554adbea736ca` |
| Preserved root producer snapshot | `8398ce11e6d709987aba8e289092070d1bd81d9f8259e8e7a34d5a1618880954` |
| Unchanged `corner-frame-attempt01/model.json` | `d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e` |
| Unchanged `corner-frame-attempt01/row-identities.json` | `bec1feb75be61b321220a047a652cc42f09c4c11d1d3c66377c4035bde4826d5` |
| Reused `remaining_joint_screen.py` | `4e2704590dc009194953425c594a38f288c9b47de4385dd3542b18ad76b217c1` |

Each completed calculation binds 146 files before and after arithmetic,
including the clearance source's 122 pins, raw force NPZ, corrected frame
operators/rows/model, producer snapshots, current materials, helpers, stack,
profile and STEP sources. It requires all twelve zero/nominal-gap source
states and consumes only the six `case_id + '_gap_raw_force_n'` arrays.
Python 3.12.3 and NumPy 2.5.2 were used. Ruff format/check pass. No tests,
native/frame solves, new beam/contact/CAD models, review agents, staging or
commits ran for this task.

The completed current invocation was:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/three_member_screen.py --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/all-outer-corner-frame-attempt01 --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/three-member-screen-attempt01/all-outer-corners
```

For parent replay, choose a fresh output child, for example
`--output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/three-member-screen-attempt01/parent-all-outer-replay`.
`--clearance` accepts a saved directory or its `comparison.json`; the two
named frozen sources above retain explicit pins. Other sources must preserve
one of the supported schemas, complete state census and unchanged baseline
bindings. Existing output paths are refused. The default source remains the
original top/service packet, so select all-outer explicitly for current work.

The all-outer child is active; the root retains the earlier clearance
sensitivity. Both numerical packets and their snapshots remain ignored
(about 1.1 MB combined). Only this document and the maintained producer are
new permanent artifacts. No old snapshot, source authority or shared summary
was changed. No archive or prune was performed; parent owns integration,
shared summaries and commits.
