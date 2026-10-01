# Six-case demand-coverage register

Date: September 29, 2026  
Lane: `compact-floor-flush-wood-joints-development`  
Geometry revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Status: read-only inventory; no source/model/deck/geometry changes and no
solver run. Review status is recorded separately against the exact artifact
hash.

## Finding

There is no genuinely path-complete member or joint demand subset available
for code checks in the current evidence. The source-bound six-case wrenches,
50-body load assignments, geometric axes and contact-patch inventory are
useful inputs. c11 supplies a detailed response for **one A12-rear, zero-gap
branch**, but six compression-only contact signs fail; its recovered support,
member, contact and connector forces are diagnostics conditional on that
branch. They do not become accepted six-case demands, even for components
whose local response row did not fail.

The immediate full-frame response blocker is therefore broader than Gmsh:
support and connection laws/load paths are not fully established. The parent
reports a working Gmsh 4.12.1 binary and Docker image in its 2026-09-29
environment; this coordinator did not reproduce that runtime (`gmsh` is not
on this shell's `PATH`). The append-only environment record binds that
parent-reported evidence. It makes a bounded 50-body **mesh-only** step
operationally plausible after a separate parent freeze, but a mesh alone
cannot calculate a design demand or clear the remaining constitutive,
material and load-transfer gates.

## Six frozen climber cases

The force vector and source moment below are the exact source-bound panel
wrench from `model-inputs.json`; `M` is reported about its recorded global
wrench reference point (shown as `r`). The 250 lbf force basis and dynamic
factor 2.0 are already reflected in the force; gravity is a separate load.
The outward panel-normal resultants are global resultants before gravity, not
per-screw demands.

| Case | Loaded panel | `F=(Fx,Fy,Fz)` N | `M=(Mx,My,Mz)` N·mm | Reference `r=(x,y,z)` mm | Outward panel component N |
|---|---|---:|---:|---:|---:|
| `a12-rear` | `main_upper_left` | `(0, 300, −2224.110808)` | `(−164885.115, 0, 0)` | `(−1019.2, 1465.956774, 2059.313004)` | 1659.44 |
| `a12-forward` | `main_upper_left` | `(0, −300, −2224.110808)` | `(−206972.839, 0, 0)` | `(−1019.2, 1465.956774, 2059.313004)` | 1199.82 |
| `a12-left` | `main_upper_left` | `(−300, 0, −2224.110808)` | `(−185928.977, 21043.862, 25079.098)` | `(−1019.2, 1465.956774, 2059.313004)` | 1429.63 |
| `k12-right` | `main_upper_right` | `(300, 0, −2224.110808)` | `(−185928.977, −21043.862, −25079.098)` | `(980.8, 1465.956774, 2059.313004)` | 1429.63 |
| `k12-rear` | `main_upper_right` | `(0, 300, −2224.110808)` | `(−164885.115, 0, 0)` | `(980.8, 1465.956774, 2059.313004)` | 1659.44 |
| `a1-rear` | `main_lower_left` | `(0, 300, −2224.110808)` | `(−164885.115, 0, 0)` | `(−1019.2, 38.968280, 358.694340)` | 1659.44 |

Each 20 mm hold-patch/standoff record is preserved in the source input. The
six-case artifact contains 300 body-external-wrench rows (50 bodies × six
cases); these are applied loads, not recovered interface actions.

## Family-by-family coverage

| Member/joint family | Source load and receiver route | Response fields currently available | Governing output needed for checks | Exact missing link; any path-complete subset? |
|---|---|---|---|---|
| **44 timber/block members**: 18 base-frame members, two legs, four knee brace/block pieces, and 20 other candidate cleats/blocks (24 candidate timber pieces total) | Six climber wrenches enter three panels and must pass through panels, block/contact/fastener joints, frame members, and floor. All 50 physical bodies receive source-mapped own-weight/gravity in c11; hardware wrenches are also assigned to receiver bodies. | c11 has 50 body equilibrium rows for `a12-rear`; all close, but they are external-load/reaction accounting. No six-case beam `N,Vy,Vz,T,My,Mz` diagrams, accepted solid stress resultants, or stability result. | Signed member `N/V/M/T` envelopes, service deflection and stability; local bearing/shear/splitting checks at each receiver and section-loss checks at the actual members. | Only one false contact branch; no six-case support/connector response. Need a source-bound whole-frame response with continuous member actions, correct sections/material axes, line-distributed self-weight for beam bending, closed joint paths, and per-case body/global balance. **No demand subset established.** |
| **Four climbing panels and two whole kickers (six panel-kind bodies)** | Source load goes to `main_upper_left` (three A12 cases), `main_upper_right` (two K12 cases), and `main_lower_left` (A1 rear). Panels/kickers transfer to 66 Hillman axes, timber bearing/contact, and frame receivers. | Source panel wrench, 142 T-nut gravity point loads, panel geometry/face map, and c11 `a12-rear` branch forces. Panel layups/properties remain unassigned in the full-frame source audit. | Panel bending/shear/deflection and edge/net-section actions; signed per-axis/group tension and shear; head pull-through, plywood damage, screw-root tension, and simultaneous interaction. | All six outward resultants require tension transfer. Hillman 42605 withdrawal `k_ax`, resistance/product eligibility, penetration `pt`, head/panel limit, group sharing, and complete receiving-member-to-frame path are not established. C11's screw axial field is a non-qualifying ratio-1.0 diagnostic. **No panel/screw demand subset.** |
| **24 bolted solid-wood cleats/blocks replacing former angle duties; 92 candidate bolt axes** (46 geometry groups; four axes lie in two three-member stacks) | Each axis is mapped to its current receiver-member set; four three-receiver axes remain one physical stack apiece. Load reaches these groups through adjacent member bearing/contact and must continue through each receiver. Geometry inventory identifies 96 adjacent raw-wood stations, receiver intervals, axes and spacing. | c11 recovers 96 candidate-bolt lateral-plane force rows and applicable outer-seat axial tie rows for `a12-rear`; these are active-set/connector-law outputs, not accepted forces. | Per physical bolt and group: signed axial tension, two transverse shear components, any bolt/washer bending or seat couple, wood dowel-bearing/edge and end distance actions, splitting/group effects, and block/member net-section actions. Preserve three-member equilibrium as one connector group. | There is no validated connector stiffness/clearance/seat transfer or load-aligned group distribution for design use. Geometry and spacing do not give force split. The source-bound [former-duty reuse map](../../current-joint-family-reuse.md) reports **24/24 duties unresolved or unaccepted**; only its ordinary reference station is an exact whole-patch match. Need accepted duty mapping, connector law, full-frame group wrenches and applicable timber checks. **No demand subset.** |
| **12 retained frame-bolt starting axes** (six two-bolt joints) | Their source axes/receiver memberships are retained as the starting frame layout; they must close loads from blocks/panels and continue into frame members. They are not automatically equivalent to prior angle-frame connections. | c11 has 12 retained-bolt lateral-plane and physical outer-seat response rows for the single branch. | Signed bolt tension/shear, group resultant and eccentric couple, receiver wood bearing/splitting, washer/seat actions, and full member equilibrium. Recheck any changed bolt axis/receiver. | Current geometry inventory flags recheck; no validated current bolt/member force demand or resistance interaction. c11 branch not accepted and only one case. **No demand subset.** |
| **66 Hillman/Fas-n-Tite 42605 panel/kicker screws** | Axes and current panel/backer identities are in source inventory. All six panel loads can require outward tension; current model's lateral-only path is incomplete for that direction. | c11 returns 66 lateral-plane rows and 66 parameterized withdrawal rows, but the withdrawal ratio is explicitly non-qualifying. | Per-axis/group signed lateral and withdrawal forces, load-slip openings, group sharing, and applicable wood-thread/root/head/panel resistances and interaction. | Product axial stiffness/resistance, actual thread penetration/head-seat/panel-limit basis and group rule are unknown. All six outward panel resultants remain without complete tension path. **No demand subset.** |
| **Timber/block/panel face bearings and 117 opposed planar patches across 115 pairs** | Contact geometry yields 1022 internal cells, preserving patch area and first moment. Six pairs are zero-area/unresolved, including both center-principal-cleat/kicker paths. | c11 has 1022 normal-contact rows; three internal contacts fail as active tension/separation (`contact_8_1`, `contact_29_4`, `contact_89_1`) and one as inactive penetration (`contact_41_2`). With the floor rows below, the six total sign failures are four active separation/tension and two inactive penetrations. Cell resultants represent uniform traction, not local peak pressure. | Active/open state and signed pressure resultant by real patch, local maximum/area distribution where capacity requires it, shear transfer, wood compression-perpendicular/grain checks, and a complete alternate fastener path where no area exists. | Contact penalty is a numerical scenario; six c11 signs fail and six geometric pairs have no finite bearing area. Center-kicker paths are open. Need corrected/verified receiver geometry or a separately supported path and a new response. **No demand subset.** |
| **Floor support: 100 normal cells and 100 assumed no-slip tangent rows** | Floor is the explicit, unverified analytical no-slip-while-bearing assumption; reactions support the full frame. | c11 has 100 normal and 100 assumed-tangent force records, with 28 active floor-tangent groups in its branch. Its two floor contact failures are `floor_base_floor_left_5` (active separation/tension) and `floor_base_floor_left_0` (inactive penetration). | Signed vertical reactions/contact state, horizontal floor reaction resultant and moment, uplift/tipping/equilibrium by case; if checking the analytical rule, exact zero tangent slip only while bearing and zero shear when open. | No actual floor verification or anchor is claimed. CalculiX 2.23 cannot represent conditional ideal stick without unsupported positive μ; c11 finite paired springs are different. Need parent-approved new formulation and coupled known-answer method check. **No support-dependent demand subset.** |
| **778 mass sources and gravity transfer (50 member/panel weights, 142 T-nuts, 586 other hardware rows)** | c11 frozen model assigns 50 distributed consistent solid-body weights, 142 T-nut point wrenches to panels, and 586 hardware source rows into 760 receiver-body point-wrench contributions. Source force and first moment are preserved. The source mapping places bolt head/nut masses at outer receivers and shaft/screw mass by modeled receiver interval occupancy, with all-to-each-receiver sensitivity extremes. | c11 model's one-case source assembly audit records all 778 rows once and per-body/global load-wrench closure; c11 response balances close. The older attempt01 `case-assembly-check.json` pins builder `1bd3e38…`, while c11 freeze pins builder `9b442e…`; only the c11 frozen model/source bundle is attributed to c11. | Preserve exact gravity at distributed member line/solid loads and account for every hardware source once. Recover body, member and joint effects with equilibrium; bound uncertain receiver allocation before connection design. | Source assignment is not physical connector stiffness, true sharing, bolt bending, bearing activation, or complete receiver-to-frame mechanics. The c11 solid body map also cannot substitute for line-load bending in a beam model. **No gravity-carrier demand subset.** |

No path-complete member/joint row was found. c11 exposes 1,566 physical force records, grouped as 1,022 timber/panel normal contacts, 100 floor normals, 100 assumed floor tangents, 96 candidate-bolt lateral planes, 12 retained-bolt lateral planes, 66 panel-screw lateral planes, 66 non-qualifying screw-withdrawal ties, and 104 physical-bolt outer-seat ties. Its equilibrium/MPC/tie/RF accounting is useful branch evidence, but the six contact-sign exceptions—four active separation/tension and two inactive penetration across internal and floor contacts—invalidate using those forces as accepted demands. The five cases other than `a12-rear` have no corresponding response.

## Integration gates and next model

| Gate | Required to close demand coverage |
|---|---|
| Conditional floor support | Exact bearing-conditional stick implementation, reference/reset definition, coupled fixture and independent method review—or explicitly keep all floor-dependent actions conditional. No invented friction coefficient. |
| Panel withdrawal | Applicable Hillman product/installation resistance and stiffness or other verified physical tension path; group sharing, panel-head limit and member path; calculate all six signed screw/group actions. |
| Receiver/hardware paths | Validate actual mechanical receiver paths and stiffness/load sharing; resolve six zero-area patch pairs and center-kicker route; source-map conservation alone is insufficient. |
| Self-weight | For beam response, apply distributed member weight and verify internal bending; retain the c11 solid body gravity source audit as source-load evidence only. |

The next bounded **T09** calculation should be a mesh-only preparation of all
50 exact STEP bodies from the source manifest, after parent freezes that
attempt. It must create a one-to-one `member_id → input STEP SHA → imported
solid → mesh body → element/node IDs` register for all 50; verify no missing,
duplicate, or merged identity; record per-body volume/bounds/centroid against
the source STEP; report element type/count and frozen quality metrics (positive
Jacobian, no degenerate elements, and predeclared aspect/quality bounds); and
have an independent source/mesh identity and quality review. The pre-existing
patch mesh covers only three wood members plus 16 local metal bodies; 47 of the
50 current members are absent. This proposed mesh-only task calculates no
response and changes no readiness flag. No materials, contact/attachment
laws, solver DOF/support/load maps, or load-transfer rules are inferred from
mesh success.

After the mesh-only gate and the four input/mechanics gates are resolved or
explicitly scoped, the first Option B response should be a source-bound
whole-frame static beam/member model (with panel representation appropriate to
verified layup) under these six exact patch wrenches and gravity. It must use
distributed member weights, physical connector/support laws, and actual
receiver paths; return per-case signed member `N/V/M/T`, deflections/stability
monitors, contact/support resultants and per-fastener/group forces; and close
whole-frame plus each-body equilibrium. Until those inputs are available, no
defensible response subset exists. Any such model, freeze, or solver run is a
separate parent-owned decision.

## Evidence and provenance pins

| Evidence | SHA-256 / scope |
|---|---|
| [Six-case source load contract](../evaluation-resume-2026-09-24/current-load-cases.json) | `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a` |
| [Reduced-static model inputs](reduced-static-attempt01/model-inputs.json) and [body external-wrench CSV](reduced-static-attempt01/body-external-wrenches.csv) | `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9`; `6c823add8e29fc2089bff460ce7fa59c300794511214890b638b6c1a6c77a33f`. `ready_for_six_case_response=false`; these are source loads and receiver inventory only. |
| [Current geometry manifest](../evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json) | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`; 50 STEP member IDs/hashes, 24 candidate blocks, 92 candidate bolts, 12 retained bolts, 66 screw axes. |
| [Contact geometry](reduced-static-attempt01/contact-geometry.json), [member geometry](reduced-static-attempt01/member-geometry.json), [bolt grouping](bolt-groups/README.md), [panel path screen](reduced-static-attempt01/panel-path-screen.json) | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151`; `121f1940d0180367f953a1f92443964ded901ca775536750a9b028e37d6c8187`; `faa50a5f9ca08ca5c40eaff30950b4ed4a56baf5fe9415517f1be8149266b458`; `80b7df4762981479c7f5c080d6207773cea1a2d6d4310f35280849b96400ec2c`. Geometry does not establish force sharing or capacities. |
| [Current joint-family reuse map](../../current-joint-family-reuse.md) | `961f2365efc3d7d5b81a09a5ac2b7eae015f969b82189ed01276bdba20ddff58`; all 24 former angle duties remain unresolved/unaccepted. |
| c11 [freeze](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/freeze.json), [model](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json), [response](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/response.json), and [independent audit](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1-postrun-review/independent-postrun-review.json) | `1633e79900afd194ece79c7463a7b383a11bb96920e7449e6a25c528e933b8e2`; `d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0`; `b8558fbaa986ff251008da629c21d8d9a56e16c965ce09476e94a688f0a9f878`; `0c6c7b8601a8b15cd46901c912934483b5da14babb84380a9301c0730cdb18ed`. Freeze/source bundle pins c11 case builder `9b442e…`; response is single `a12-rear`, numerical/mechanical false. |
| c11 frozen [case builder](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/sources/fea/wood_joint_reduced_case.py), [gravity mapper](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/sources/fea/wood_joint_reduced_gravity.py), [model/contact builder](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/sources/fea/wood_joint_reduced_model.py) | `9b442e85221c383f1ad013dd493d87c9d4a303b6e36f58b2733f5de00316e192`; `e41c09282d59fa41d452ec88031fc59213863fd6edf65b1335dc8de92b7d3c45`; `f94b1161b984b7599f6c8d4a131ad49a3f12a0033ec6a0b6b5892a5b9d45e2f7`. These are the frozen source code for the c11 body-load assignment and spring/active-set formulation. |
| Earlier [attempt01 assembly audit](reduced-static-attempt01/case-assembly-check.json) | `55f94ae42ed7b2efc1e2a70157b24881c6f35cb3fd0d531cd5de71ee9e2600a0`, pins old builder `1bd3e38bf13b83532166c1292018eccf5caf5102febf33332eaac6e35e9187ce`. Do not attribute it to c11, whose freeze pins `9b442e…`. |
| [Panel withdrawal preflight](panel-withdrawal-preflight.md), [coordinator path review](COORDINATOR-HANDOFF-REVIEW.md), mesh-source audit [README](../evaluation-resume-2026-09-24/current-frame-mesh-source-audit-attempt01/README.md) and [JSON](../evaluation-resume-2026-09-24/current-frame-mesh-source-audit-attempt01/mesh-source-audit.json) | Panel `22e4b14d270a1d7ba8a247562b901ef4998483ca7d70feed6646560a29c6d18f`; path review `e6caddbb975411ab2bfe6c79dae0f955f1f03860ded1ba2fcf3558e681bdd79c`; mesh README `e323692e6a45a5c35a2c11567dd5da1a513bb90599b3df7abdcf1b938aac0410`; mesh JSON `8d3b7ced91d43a0933b815f34433cd7e677fd193d90e44008fa3ea1b7011409c`. |
| [T09 environment attempt02](../evaluation-resume-2026-09-24/current-frame-mesh-preparation-environment-attempt02/README.md) and [observations](../evaluation-resume-2026-09-24/current-frame-mesh-preparation-environment-attempt02/environment-observations.json) | README `477a1c30bdca538ab63aac00d7c635f836cd86afc68b016e1eaf714de580c0ed`; observations `b4c8d6a021010e49b25e4b07e5e43893be6480cc44f4e024002e226ccb7420d1`. Parent-reported 2026-09-29 Gmsh 4.12.1 `-version` success after an extracted `libGLU.so.1` runtime dependency, and Docker server/pinned-image availability. The packet labels these as parent-reported, not reproduced by this register author; no mesh, solver run, or readiness follows. |

## Boundary

This register separates (1) source inputs and load assignment, (2) response
fields conditional on the exact failed c11 branch, and (3) accepted design
demands. Only the first two exist today; the third is empty. The 47 MVP-E
criteria remain pending. Root/parent retains readiness, any new model
formulation/freeze, resource budget, native-run decision, and final validation.
This artifact authorizes no mesh or solver run and no physical work.
