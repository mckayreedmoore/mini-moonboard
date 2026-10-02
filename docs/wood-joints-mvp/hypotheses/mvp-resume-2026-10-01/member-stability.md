# Timber torsion and member stability from saved six-case responses

## Two-receiver replay: current force source

The replay of all 88 independent two-receiver clearances is complete in
[member-stability-attempt01/all-two-receiver/checks.json](member-stability-attempt01/all-two-receiver/checks.json).
It uses the parent's completed `member-screen-attempt02/all-two-receiver-clearance01`
arrays and unchanged finished geometry/materials. The current source has a
**top-rail intact-prism face exceedance of 1.039209**, replacing the old
**1.043029** as the result for this force source. It does **not** clear the
declared 180 psi longitudinal shear allowance. Both frozen results remain
available; they are separate same-state calculations.

| Result | Preserved all-outer | Current all-two-receiver |
|---|---:|---:|
| Compatible face shear/torsion ratio | 1.043029 | **1.039209** |
| Same-cut component rectangle upper bound | 1.199096 | 1.202715 |
| Coefficient-5 isotropic sensitivity | 1.339431 | 1.337436 |
| Fixed-action R/T-swapped face ratio | 1.015177 | 1.011546 |
| Maximum normal interaction with declared timber restraints | 0.578574 | **0.614384** |
| Full unsupported normal interaction, including cuts outside column domain | 0.639415 | 0.691259 |

The current replay again covers **20 frame members, 24 blocks, 264 balances,
54,888 signed cuts and 34,632 applicable rectangular traces**. All applicable
normal/stability checks remain below 1.0 inside the declared timber restraint
scenario. The four long 2×6s still require weak effective column lengths
≤1,905 mm; their geometry, brace stations, end duties, and resistance
assumptions were unchanged. Eighteen blocks have applicable rectangular cuts;
their maximum normal interaction is 0.088055 and shear/torsion component bound
is 0.355591, both in `knee_outer_right_spine`. The same six blocks retain their
local nonrectangular-section duties.

The new source's six nominal cases have **bounded fixed-force seating
freedoms**. `frame_state_contract.force_state_scope` permits these saved
simultaneous force vectors, but records that a representative position is not
a unique seated pose or a motion envelope. Its `all_source_rank300_gates_met`
and `strict_tangent_stability_transferred` flags are false. Therefore the
numerical member checks retain their declared restraint conditions and do not
establish strict tangent stability of the assembled frame. No frame, joint or
physical acceptance is transferred.

### Current governing cut and exact remaining strength exception

The current maximum is still `base_rail_top`, `k12-rear`, station
**2116.3359375 mm**, index **407**, **after**, negative-grain half, in the
source-bound 38.1×139.7 mm intact rectangle. These are its simultaneous signed
actions:

| Action | Current demand |
|---|---:|
| N, tension-positive | −1217.023062 N |
| Vu | −272.986628 N |
| Vv | +1048.893119 N |
| T about grain | −54931.265544 N mm |
| Mu | −142674.011671 N mm |
| Mv | −17534.015354 N mm |

At u=−19.05 mm, v=0, the compatible torsional v shear is **0.994120 MPa**
and same-state transverse v shear is **0.295598 MPa**. Their signed sum is
**1.289717 MPa**, versus the unchanged **1.241056 MPa** allowance. This cut's
simultaneous braced normal interaction is **0.227692** and NDS stability
interaction is **0.052658**. The maximum normal interaction, **0.614384**,
occurs at 1963.3039 mm, before, index 374; its six signed actions remain in
the current CSV and machine report.

There are again **66 actual face-exceedance traces**, 33 each in `k12-right`
and `k12-rear`, between 1967.4461 and 2179.6375 mm. A further **81** top-rail
traces exceed only the conservative component bound. Other applicable member
cuts have component bounds below 1.0. The face exceedance remains distinct
from a failed conservative upper bound.

With current Vu/Vv held fixed, necessary face clearance requires
**|T|≤52,242.441 N mm**, and the sufficient component bound requires
**|T|≤43,394.933 N mm** at this cut. With all current actions fixed, the face
requires at least **187.058 psi** compatible longitudinal shear allowance;
the sufficient bound requires **216.489 psi**. These are demand thresholds,
not adopted new allowables or a torque-only model modification. The current
saved state remains above the 180 psi screen. A future changed response or
supported strength scenario must be bound and evaluated simultaneously; no
restraint or hardware change was made to clear the reference result.

### Current source bindings and replay command

| Current input | SHA-256 |
|---|---|
| `two-receiver-frame-attempt03/comparison.json` | `0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5` |
| same packet `response.npz` | `774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52` |
| `member-screen-attempt02/all-two-receiver-clearance01/member-results.json` | `8828f6d258a770136deb6af7dca1b443ebd0459faaa6e71d111f4f7b9e1b3507` |
| same member packet `geometry.json` | `ecfeee2627fc67d91ce89acd5253bf99a4d79b06451c94ced6b915a664009f9d` |
| same member packet `action-section-arrays.npz` | `3f89ad4290e93a2fed4a2526ae2cafa143ac64f3bac7bf40d46c71cd646b23e9` |
| `frame_state_contract.py` | `22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5` |

The parent's member packet records 160 matching saved sections and 131
changed-STEP section exclusions. The replay retains this bound geometry;
saved net geometry alone does not supply resistance. It restores actions from
the new member arrays and authenticates them against
the new raw forces through the unchanged physical operator. Maximum whole-body
residuals are 1.28×10⁻¹¹ N and 1.39×10⁻⁸ N mm.

`member_stability.py` now accepts `--clearance` and `--members` with the old
all-outer defaults. Selected comparison/response/member input hashes and new
output hashes are recorded dynamically. Geometry, material, frame operators
and the specified contract-helper hash remain fixed. Incoming geometry is
checked against the preserved all-outer geometry reference and its finished
STEP bindings; in this replay the entire geometry JSON is byte-identical.
The member producer is authenticated through its immutable saved snapshot,
rather than requiring the parent's current producer source to equal an older
packet's source. Status is derived from the selected input's calculated ratios;
the old torsion exception is not copied into the replay status.

Executed command, terminal exit 0:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member_stability.py \
  --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/two-receiver-frame-attempt03 \
  --members docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-screen-attempt02/all-two-receiver-clearance01 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-stability-attempt01/all-two-receiver
```

For another reproduction, select a fresh owned child directory. All 16 reported
Ruff issues were fixed: imports, equivalent unlimited cache syntax, unused
unpacked variables, dictionary item iteration, adjacent-pair iteration and
explicit default binding of the existing immediately used per-member closure.
These fixes change no numerical model or engineering reference. Targeted Ruff
lint reports zero issues. The replay's producer, saved snapshot and source
hash are identical. No tests, review agents, native/frame/CAD runs, staging or
commit were performed. Parent retains integration and heavy work ownership.

## Preserved all-outer finite result

The saved-response screen is complete for the **20 frame timbers and 24
blocks**. It covers 54,888 signed cut traces, including 34,632 bore-free
rectangular traces, and restores all 264 member/case action balances.

The governing intact-section result is **top rail combined longitudinal shear
and torsion, 1.043029** against the explicitly assumed **180 psi parallel-grain
shear allowance**, normal duration. This is an exceedance at an actual face of
the assumed compatible prismatic stress field. The larger component bounds
1.199096 and 1.339431 are conservative sensitivities. Their maxima need not
occur together at one point. The face result establishes that the present
conditional strength screen cannot be cleared just by removing conservatism
from those bounds.

For axial/biaxial bending and stability, **all screened rectangular cuts are
below 1.0 when the declared existing timber restraints are effective**. The
governing normal interaction is **0.578574**, also in `base_rail_top`. Four long
2×6 members exceed the NDS column slenderness domain when treated as entirely
unsupported between their ends. Each needs **weak-direction effective column
length ≤1,905 mm**. Existing timber bolt/bearing stations offer maximum weak
bays of 860–981 mm in those four members. Actual restoring restraint through
those receivers is an explicit condition, not a result proved by the saved
first-order response.

These are usable conditional engineering results with one identified intact
prism strength exception and specified restraint duties. They do not replace
the selected baseline or establish local hole resistance, formal torsion
qualification, physical inspection, or fabrication release.

## Preserved all-outer inputs and reproduction

Only `member_stability.py`, this document, and ignored
`member-stability-attempt01/` were owned. The completed header packet was
preserved. Model, CAD, operators, authority and other agents' documents were
not edited. No native/frame solve, CAD evaluation, tests, review agents,
staging or commit were performed. Parent retains panel/contact sharing scope.

| Consumed input | SHA-256 |
|---|---|
| `all-outer-corner-frame-attempt01/comparison.json` | `ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3` |
| `all-outer-corner-frame-attempt01/response.npz` | `aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901` |
| `member-screen-attempt02/all-outer-clearance01/member-results.json` | `7f120364d2fc027bee85d7516581a130e7a05728fb9d7de2460978ddea451e01` |
| same member packet `geometry.json` | `ecfeee2627fc67d91ce89acd5253bf99a4d79b06451c94ced6b915a664009f9d` |
| same member packet `action-section-arrays.npz` | `20298c4191d579a06577f877411287febbec60c56d21ba0d31a1e2511f01fd02` |
| `hardware-material-specification-2026-09-30/material-inputs.json` | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |

The [machine report](member-stability-attempt01/checks.json) additionally binds
the unchanged `corner-frame-attempt01/model.json`, row identities and physical
operator, all 44 current finished STEP hashes, the frame material map, and
consumed helpers. Nominal raw force keys are exclusively
`case_id + '_gap_raw_force_n'` for `a12-rear`, `a12-forward`, `a12-left`,
`k12-right`, `k12-rear`, and `a1-rear`. No earlier native forces or source
acceptance were transferred.

Reproduce from the repository root using the shared environment, Python
3.12.3 / NumPy 2.5.2:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member_stability.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-stability-attempt01/reproduce
```

Use a new child directory; existing evidence is preserved. Current results
are the files at the attempt root. `preliminary-bilateral-only/` retains the
first arithmetic packet, which deliberately credited only bilateral lateral
rows and therefore found no weak-axis brace stations. The current packet adds
the explicitly conditional tension-tie/compression-face path. Both packets use
identical frozen demands. The output manifest lists exact paths and hashes.

## Same-cut method and declared engineering assumptions

`bottom_corner_checks.saved_actions` restores the existing point forces and
free couples; `top_corner_actions.wrench` checks them against each raw response
row through the frozen physical operator. Whole-member maximum residuals are
below 1.2×10⁻¹¹ N and 6.9×10⁻⁹ N mm. The saved opposite cut sides agree. Every
calculation retains **N, Vu, Vv, T, Mu and Mv from one case, station, cut side
and before/after trace**. Negative-half N is tension-positive. At retained
profile sections moments are translated to the actual saved centroid with
`M_centroid = M_datum − offset × force`; torsion receives that translation too.

The saved finite-plane rectangles, station array and strength classification
come from `member_screen`. Source DF-L No. 2 references and existing CF
scenarios are retained: normal duration, dry, unincised, normal temperature;
no flat-use or repetitive-member increase. Emin is 580,000 psi. Four ripped
blocks retain their recorded hypothetical final-product CF=1 scenario;
grading of their original stock is not transferred to a ripped product.

### Beam and column stability

The existing `fea.reinforced_timber_resistance` kernel supplies CP, CL, FcE,
FbE and effective beam length. Strong/weak dimensions are selected from the
actual u/v rectangle, not a global vertical convention. Full-span strong
column and beam lengths are retained; weak column length alone changes with
the proposed restraint stations. The source-bound 1:12 rear recess is screened
conservatively as its minimum intact 50.8×139.7 mm rectangle extended along
the entire leg for buckling. Actual retained dimensions and centroid are used
for each cut stress.

Two explicit support scenarios are reported:

1. **End support only:** translation restrained in both section directions,
   no sway, column K=1, and rotation about grain restrained at end bearing.
   Full start-to-end length conservatively replaces the support span.
2. **Existing timber weak restraints:** the same end duties, plus restoring
   weak-direction support at the listed existing timber bolt stations. Each
   receiver must itself be laterally restrained. A source tension-only axial
   tie needs its corresponding timber compression face for the other
   displacement sense, with opening slack taken up. Panel attachment and
   compression-only contact alone receive no restraint credit. Strong-column
   and beam spans remain full length. This condition does not assume an axial
   tension spring is bilateral.

Applied provisions are NDS 3.3.3 / Table 3.3.3 footnote 1, 3.6.3, 3.7.1 and
3.9.1–3.9.2. The column domain is le/d≤50; construction's higher limit is not
used. Beam RB≤50; its maximum here is 21.0663. CP uses c=0.8. Compression
checks retain both Euler denominators and the biaxial interaction. Tension
uses the linear tension/bending check plus an independent bending check with
CL and no beneficial tension relief. Normal interaction and shear/torsion are
separate limits evaluated with the same signed cut. Their ratios are not
summed into an invented failure law. [2024 NDS, Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).

The locally available official Chapter 3 PDF was read and hash-bound:
`205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644`.

### Practical torsion screen

The FPL Wood Handbook gives rectangular torsion stress coefficients and a
longitudinal shear-modulus approximation. Its section equations are mechanics,
not a timber torsion allowable. The adopted engineering screen assumes free
warping in an intact prism, adds the signed transverse shear field, and compares
both longitudinal shear components with the unchanged Fv=180 psi; no torsional
strength enhancement is credited. [FPL Wood Handbook, Chapter 9, equations
9–9, 9–11 and 9–24 / Figure 9–6](https://research.fs.usda.gov/download/treesearch/37423.pdf).

Retrieved primary PDF SHA-256:
`84829761afb977291236c85bd51fdb00a3a56109625b0c09e7a0915ae684a9b4`.

For rectangles whose u/v axes align with source R/T, the local closed
Saint-Venant rectangle series retains the source longitudinal shear ratio
GLR/GLT=0.064/0.078. Absolute elastic modulus cancels out of the stress
coefficients. Both consumed timber elastic categories have this ratio.
The arithmetic transform is:

```text
Phi_uu / G_Lv + Phi_vv / G_Lu = -2 theta
s = sqrt(G_Lu / G_Lv), v' = s v
tau_Lu = Phi_v, tau_Lv = -Phi_u, T = 2 integral(Phi dA)
```

This is local section arithmetic, using 200 fixed odd series terms. It adds
no beam model and changes no response or elastic binding. Dimensions are
rounded only to 10⁻⁹ mm for coefficient caching. A fixed-action R/T swap is
also reported; it is a section-stress sensitivity, not a second frame response.

Transverse shear uses the elementary fields
`tau_Lu = 1.5 Vu/A (1 − 4u²/width²)` and
`tau_Lv = 1.5 Vv/A (1 − 4v²/depth²)`.
At u=±width/2, v=0, the u shear vanishes and one opposing face adds torsion
to the actual signed v shear. Similarly for the v faces. A face ratio above
1.0 therefore exceeds the allowance in the declared field. The sufficient
all-section comparison is the norm of the two component maxima after adding
their respective transverse maxima. Exceeding that upper bound alone is
recorded as a conservative sensitivity.

`scripts.floor_taper_checks.rectangular_shear` is reused for the separate
coefficient-5 isotropic comparison. The header's grain is X, u is Y=139.7 mm
and v is Z=38.1 mm; its frozen R axis lies 50° from u. That member uses the
explicit equal-longitudinal-shear-modulus FPL stress approximation, giving a
component bound of 0.774330. It does not relabel Y/Z as measured R/T or alter
the frozen off-axis elastic frame. Gradually reduced recess sections similarly
use a local rectangular approximation; notch and opening concentrations remain
with their existing local-section duties.

## Preserved all-outer frame results

N ratios below use the declared timber restraint scenario. S is the sufficient
same-cut component bound for shear plus torsion. S≤1 clears this rectangular
engineering comparison; S>1 requires the face distinction above. Every listed
member has signed compression somewhere in the six-case traces.

| Frame member | Full length mm | Proposed maximum weak bay mm | Peak N interaction | Peak S bound |
|---|---:|---:|---:|---:|
| `base_floor_left` | 1815.646 | 1594.597 | 0.119792 | 0.203692 |
| `base_floor_right` | 1815.646 | 1594.597 | 0.107488 | 0.172963 |
| `base_header` | 2435.225 | 860.140 | 0.167313 | 0.774330 |
| `base_post_center_left` | 238.900 | 145.000 | 0.037045 | 0.184623 |
| `base_post_center_right` | 238.900 | 145.000 | 0.045553 | 0.133979 |
| `base_post_outer_left` | 238.900 | 73.347 | 0.141008 | 0.408835 |
| `base_post_outer_right` | 238.900 | 73.347 | 0.136864 | 0.418733 |
| `base_principal_center_left` | 2506.167 | 981.100 | 0.118845 | 0.177322 |
| `base_principal_center_right` | 2506.167 | 981.100 | 0.079658 | 0.160389 |
| `base_rail_bottom_left` | 1041.250 | 952.350 | 0.137955 | 0.350459 |
| `base_rail_bottom_right` | 1038.075 | 949.175 | 0.021270 | 0.041455 |
| `base_rail_service_lower_left` | 1041.250 | 950.350 | 0.029556 | 0.072275 |
| `base_rail_service_lower_right` | 1038.075 | 947.175 | 0.021522 | 0.053533 |
| `base_rail_service_upper_left` | 1041.250 | 950.350 | 0.018741 | 0.048305 |
| `base_rail_service_upper_right` | 1038.075 | 947.175 | 0.022131 | 0.063691 |
| `base_rail_top` | 2257.425 | 952.350 | **0.578574** | **1.199096** |
| `base_side_left` | 2539.768 | 838.150 | 0.375292 | 0.481216 |
| `base_side_right` | 2539.768 | 838.150 | 0.361041 | 0.454834 |
| `lumber_leg_left` | 1989.026 | 1683.660 | 0.147544 | 0.183768 |
| `lumber_leg_right` | 1989.026 | 1683.660 | 0.156605 | 0.178963 |

The full unsupported-column scenario has maximum normal ratio 0.639415. That
number is outside the column slenderness domain for its compressed top-rail
cut; it is a sensitivity, not an accepted NDS column result. No normal stress
ratio exceeds 1.0. The following four support requirements arise from the
50×38.1 mm slenderness limit, not a failed normal-strength ratio:

| Member | Weak translation direction | Full le/38.1 | Existing brace stations, mm from source start | Required effective weak length |
|---|---|---:|---|---:|
| Header | global Z | 63.917 | 133.350; 993.490; 1103.200; 1335.200; 1443.550; 2301.875 | ≤1905 mm |
| Left principal center | global X | 65.779 | 75.339; 128.339; 288.867; 321.867; 1160.017; 1193.017; 1431.167; 1464.167; 2445.267; 2478.267 | ≤1905 mm |
| Right principal center | global X | 65.779 | same station values, right-side receivers in machine report | ≤1905 mm |
| Top rail | u=[0, 0.642788, 0.766044] | 59.250 | 45.450; 997.800; 1262.800; 2211.975 | ≤1905 mm |

The table uses K=1. For a different effective-length coefficient, the permitted
physical unsupported distance is `1905/K` mm. The exact remaining restraint
fact is whether these named bolt/face interfaces, through their receivers,
provide restoring weak-direction support with slack taken up, and whether the
end bearing joints restrain roll. The frozen source's tension-only axial rows
and compression-only faces have not been silently converted to bilateral
springs. No panel stiffness or screw restraint was assumed to establish this
fact. Confirmation may use the existing joint/load-path evidence and parent's
assembly sensitivity work; this screen introduces no new general solve.

## Preserved all-outer governing cut and limits

The maximum face ratio is at `k12-rear`, station **2116.3359375 mm**, array
index **407**, **after** trace, negative-grain half. The intact source section
is **38.1 u × 139.7 v mm**, grain global X. The critical face is
u=−19.05 mm, v=0, approximately global
`[986.0359375, 1457.5860952, 2172.2053683]` mm.

| Simultaneous signed action | Demand |
|---|---:|
| N, tension-positive | −1173.672310 N |
| Vu | −195.385199 N |
| Vv | +1041.606383 N |
| T about grain | −55306.691536 N mm |
| Mu | −139991.850040 N mm |
| Mv | −21352.474744 N mm |

At the critical u face the aligned source-R/T torsional v shear is
**1.000914 MPa** and simultaneous transverse v shear is **0.293544 MPa**.
Their actual signed sum is **1.294458 MPa**, giving 1.043029 against
1.241056 MPa. The simultaneous braced normal interaction on this same cut is
**0.239076** and its NDS stability interaction is **0.050768**. The maximum
normal interaction, 0.578574, is another same-case cut: 1963.3039 mm, before,
with complete simultaneous actions retained in the CSV.

There are **66 face-exceedance traces**, 33 each in `k12-right` and `k12-rear`,
between stations 1967.4461 and 2179.6375 mm. Another 62 top-rail traces only
exceed the conservative component bound. All other applicable member cuts
have component bounds below 1.0. At the governing cut:

| Fixed-action section comparison | Ratio |
|---|---:|
| Frozen aligned R/T face | **1.043029** |
| R/T swapped, same actions | **1.015177** |
| Equal shear moduli, compatible face | 1.028562 |
| Aligned orthotropic component upper bound | 1.199096 |
| Reused coefficient-5 isotropic sensitivity | 1.339431 |

Under unchanged Vu/Vv and the declared stress assumptions, necessary face
clearance requires **|T|≤52,355.912 N mm**. A sufficient all-section component
bound requires **|T|≤43,964.639 N mm** at this cut. Alternatively, with all
actions fixed, the face alone requires at least **187.745 psi** compatible
longitudinal shear allowance; **215.837 psi** clears the sufficient component
bound here. These are demand thresholds, not new wood allowables, grades,
duration factors or a global remedy. Any changed sharing result must repeat
the simultaneous section checks; changing torque alone is only arithmetic.

The present Fv=180 psi scenario thus has a finite top-rail strength exception.
Shorter unbraced length cannot clear it. The next usable input is parent's
candidate-specific revised panel/contact sharing response, or an explicitly
supported alternative shear-strength scenario. No member enlargement or axis
movement is proposed or performed in this bounded screen. Formal torsion
qualification and physical flags remain false.

## Preserved all-outer blocks and local-section boundaries

Eighteen blocks have applicable intact rectangular traces. Their maximum
normal interaction is **0.054439** and maximum combined shear/torsion component
bound is **0.257494**, both in `knee_outer_left_spine`. Source orientations and
material scenarios are retained individually in the machine report. Their
short stock lengths do not create a new column slenderness failure.

Six blocks have no bore-free rectangular trace. Their nominal dimensions and
complete signed demands are retained; rectangular torsion resistance is not
assigned through longitudinal bolt holes or passages. Separate maxima in this
table are demand inventory only; they are not combined into a synthetic state.

| Block | Length / minimum stock dimension mm | Minimum signed N, N | Maximum absolute T, N mm |
|---|---:|---:|---:|
| `center_post_cleat_left` | 128.9 / 88.9 | −11.250 | 4906.497 |
| `center_post_cleat_right` | 128.9 / 88.9 | −10.811 | 4412.813 |
| `center_principal_cleat_left` | 134.7 / 83.9 | −322.880 | 9021.035 |
| `center_principal_cleat_right` | 134.7 / 83.9 | −287.444 | 8114.656 |
| `knee_outer_left_inner_frame_block` | 139.0 / 88.9 | −54.761 | 3719.831 |
| `knee_outer_right_inner_frame_block` | 139.0 / 88.9 | −52.517 | 4609.542 |

At K=1 their nominal le/d≤1.606. That identifies no gross-stock column-domain
issue; it supplies no net-section or splitting acceptance. Their missing local
fact is a resistance treatment of the actual remaining section around the
already-bound holes/passages, with the same complete signed cut demand. These
duties stay with the existing [header joint packet](header-joint-checks.md),
member section evidence and joint register. Their absence is distinct from the
identified top-rail intact-prism exceedance.

Across all members, excluded traces comprise 19,080 bore/passage traces, 1,056
clipped end profiles and 120 incomplete/terminal profiles. The 1,224 accepted
recess-profile traces retain their actual centroid and dimensions. No gross
rectangle ratio is reported as a local hole qualification.

## Active evidence and retention

Current replay artifacts are
[all-two-receiver/checks.json](member-stability-attempt01/all-two-receiver/checks.json),
[same-cut-states.csv](member-stability-attempt01/all-two-receiver/same-cut-states.csv),
[body-balances.json](member-stability-attempt01/all-two-receiver/body-balances.json),
the producer snapshot and
[SHA256SUMS](member-stability-attempt01/all-two-receiver/SHA256SUMS).
Preserved all-outer artifacts are [checks.json](member-stability-attempt01/checks.json),
[same-cut-states.csv](member-stability-attempt01/same-cut-states.csv),
[body-balances.json](member-stability-attempt01/body-balances.json), and the
producer snapshot. [SHA256SUMS](member-stability-attempt01/SHA256SUMS) lists the
original paths and source hashes; its original producer snapshot remains
unchanged. The original report source is also preserved byte-for-byte in
`replay-source-preparation/prior-member-stability.md.snapshot` inside the
ignored attempt. Current tracked sources have their hashes in the replay
manifest. Both frozen source response/member packets and prior header evidence
remain active for parent reconciliation. The preliminary
bilateral-only arithmetic is retained inside this ignored packet as a method
diagnostic; no source, historical run, or other agent's output was pruned.
Parent owns reconciliation and any archive decision. This file is the only
new tracked report for the bounded task.

## Appendix: governing-cut location and fixed-action dimension sensitivity

This appendix uses only the completed all-two-receiver saved arrays and the
frozen producer `b9968e028eaa03e759c06db2c0ad4f1ef80ea67dd95fc2da4b0fa80a485b8535`.
`member_stability.py` was not edited after delivery. The delivered report,
before this appendix, is preserved as
`all-two-receiver/face-location-sensitivity/member-stability-before-appendix.md.snapshot`
with SHA-256 `bf8e7760aa232d86748fbb29dc64afd4206190a044ee8eb1a7c122eda11649f6`.
The replay output and its original manifest remain unchanged. Small arithmetic
is retained in [arithmetic.py](member-stability-attempt01/all-two-receiver/face-location-sensitivity/arithmetic.py)
and [arithmetic.json](member-stability-attempt01/all-two-receiver/face-location-sensitivity/arithmetic.json),
with the appendix manifest in that same ignored child.

### Location relative to existing load transfer

The governing cut is the intact rectangle at station **2116.3359375 mm**,
global grain X, `k12-rear`, after trace 407. The current top-rail length is
2257.425 mm. The cut lies outside the outer-right cleat's saved contact
footprint and clear of both the structural bolt bores and the preceding panel
screw bore.

| Existing load station or disturbance boundary | Station mm | Distance from cut mm |
|---|---:|---:|
| First boundary of outer-right cleat contact footprint | 2168.525 | +52.189063 |
| First active outer-right cleat contact cell, row 1873 / cell 21 | 2179.6375 | +63.301562 |
| Both existing outer-right rail bolt axes and their axial ties | 2211.975 | +95.639063 |
| Near boundary of those structural bolt bores | 2208.225 | +91.889063 |
| Preceding loaded panel screw, `round_panel_upper_right_edge_2` | 1965.375 | −150.960938 |
| Far boundary of that panel screw's bore | 1967.4451 | −148.890838 |
| Rail end / active rail-to-side contact stations | 2257.425 | +141.089063 |

The first active cleat cell carries 155.438 N resultant; the saved full cleat
footprint is `[2168.525, 2257.425]` mm. Two potential panel contact stations
coincide with the cut (`contact_83_2` / `_3`, rows 930/931), but both carry
**zero force in this same state**. They are not a concentrated load causing
the displayed exceedance. The loaded panel screw at 1965.375 mm retains its
saved lateral and parametric withdrawal actions; no favorable cancellation or
different-case contact state is substituted.

The after trace coincides with a nodal representation of distributed body
load. The net body load at this station is about 1.586 N and its torque jump
is only 3.050 N mm, compared with the carried torque of 54,931.266 N mm.
The same-cut face proxy before that body-load node is **1.038933**; after it
is **1.039209**. Thus the nominal exceedance exists on both sides of the node.

**Engineering interpretation:** this is an intact, uniform member slice in
the joint neighborhood, appropriate for a nominal ordinary-section screening
comparison. It is not an infinitesimal cut through a bore, a vanishing end
profile, or the loaded cleat face. However, its clearance from the contact
footprint is only **52.189 mm = 0.374 of the 139.7-mm section depth**, or
**1.370 times its 38.1-mm thickness**. The entire uniform run between the
preceding screw-bore edge and the cleat footprint is only **201.080 mm**,
about **1.439 section depths**. Those distances do not establish a fully
developed Saint-Venant pointwise field remote from load introduction.
No calibrated disturbance cutoff is invented. Retain the **3.9209% nominal
face-proxy exceedance** and its actual load-path location; do not recast it as
an established local wood failure or dismiss it as a zero-length-section
artifact. The precise unresolved method fact is the pointwise stress field
in this 201-mm load-transfer run, not an additional generic qualification gate.

### Required allowance with actions unchanged

The signed cut's actions, orientation and section dimensions are those in the
current governing-cut table above. Its compatible face stress is
**1.289717358 MPa**. Therefore:

```text
Fv_at_unity / Fv_original = 1.0392093771253832
Fv_at_unity = 1.289717358 MPa = 187.057687883 psi
Fv_original = 1.241056313 MPa = 180 psi
```

Strict proxy `<1` would require an allowance above the unity threshold.
This is the required fixed-action ratio, **+3.9209377%**; no higher allowance,
load-duration factor, species/grade change, or torsional strength enhancement
is adopted or looked up. The calculation continues to use the original 180 psi
allowance.

### Smallest isolated section-dimension sensitivity

Keep all six signed actions fixed about the same section centroid, retain the
frozen aligned R/T shear ratio, and change one section dimension at a time.
The same rectangular series is recomputed for each counterfactual shape;
its torsion coefficient is not held fixed. The proxy is:

```text
R(w,d) = max(1.5 |Vu|/(w d) + |T| Ku(w,d),
             1.5 |Vv|/(w d) + |T| Kv(w,d)) / Fv_original
```

The root is the infimum for a strict `<1` requirement; any positive increase
beyond it clears this particular proxy. The last columns show rounding upward
to 0.01 mm solely as arithmetic examples.

| Single dimension changed in `base_rail_top` | Other dimension held fixed | Dimension at proxy=1, mm | Increase at unity, mm | Rounded example, mm | Same-action face proxy |
|---|---:|---:|---:|---:|---:|
| u thickness, original 38.1 mm | v=139.7 mm | 39.013136 | +0.913136 | **39.02** (+0.92) | **0.999714761** |
| v depth, original 139.7 mm | u=38.1 mm | 144.478825 | +4.778825 | 144.48 (+4.78) | 0.999990713 |

Among these independent one-dimension increases, the smaller additive change
is **u: 38.1→39.02 mm**, with v unchanged at 139.7 mm. This dimension follows
the source u direction `[0, 0.64278761, 0.76604444]`; it is not a change in
global Z thickness. The 0.01-mm rounding is not a shop tolerance, available
stock size, engineering margin, or cutting instruction.

These are counterfactuals for the identified same-action cut only. No revised
geometry or response was solved, and no other cut, receiver, joint, brace,
bolt stack or panel attachment is accepted by this calculation. An actual
uniform u increase would move the main-member seat faces and change its bolt
grip and contact geometry; effects on forces, selfweight, support and fit were
not computed. Parent owns reporting required geometry changes before any
reviewed-scene alteration. The saved model, material, hardware policy and
producer remain unchanged.
