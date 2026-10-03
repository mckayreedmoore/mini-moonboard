# Remaining duties for the 24 current connector blocks

This is a consolidation of completed engineering checks and their recorded missing load-transfer/resistance scope. It uses the current six nominal-gap 250 lb cases after the four upper screw moves. It changes no geometry, mechanics, material reference, adopted criterion or release flag.

The new [left common-block result](upper-left-block.md) is **complete** for six cases, twelve host models, four bolts and 32 faces (`5e8c52e5…`). Parent's [left component replay](upper-left-block-components.md) is also **complete** (`25f0bb27…`): lateral 0.722296, finished parallel path 0.142295, mean washer pressure 0.667024 and smooth-bolt VM/92 ksi 0.275588. The [right integration](upper-right-block.md) is complete (`0b0b392b…`, published at `d1014710`): respective indices 0.813949, 0.160367, 0.770232 and 0.313740. Both use a common rigid cleat gauge; neither qualifies elastic timber or changes the frame force allocation.

## Per-block evidence map

Each row retains four block-axis incidences. Exact axis IDs, receiver interfaces, simultaneous cases, signed ties, member witnesses, seat pointers, hardware profile specifications and operation pointers are in the machine file. **V/T** means the original frame peak lateral force and its simultaneous signed tie, in N; independent maxima are not combined. **N/ST** gives this block's completed conditional bore-free normal and compatible shear/torsion indices, not a whole-joint capacity; `—` means the rectangular trace is inapplicable, not failed.

**M**: current member/body balance and restraint/prism screens, including each host. **R/WA**: individual remaining-bolt/ideal-annulus references. **TC/BC**: top/bottom same-state components and finished paths. **E/H**: end-grain/header method. **S**: separate lower-left service references. **P**: partial central-ring result. **K/KB/KF**: continuous-knee reference/static bearing/common-shaft placement. **Left/Right**: their own complete finite rigid-block response. Seat geometry is already indexed for every incident axis; WA alone is not proof of supported contact.

**A**: preserved component extraction records and conditional assembly order; **CAP**: use the already completed captured-nut alternative on that row's `rail_2`; **T**: corrected top straight approaches and side-before-rail installation/rail-before-side removal. `+2` identifies the two axes in that block covered by the completed twelve-axis length extension screen. These are bounded geometric/operation scopes, not observed installation or a new qualification checklist.

| Block | Hosts | Frame V / simultaneous T (N) | Completed wood N / ST | Completed bolt / support methods | Fit / operation | Recorded remaining scope |
| --- | --- | ---: | ---: | --- | --- | --- |
| `bottom_center_left_cleat` | `base_principal_center_left`<br>`base_rail_bottom_left` | 5.528 / 9.269 | 0.000382 / 0.003201 | M, R, WA | A+CAP | W |
| `bottom_center_right_cleat` | `base_principal_center_right`<br>`base_rail_bottom_right` | 4.927 / 3.438 | 0.000373 / 0.002181 | M, R, WA | A+CAP | W |
| `bottom_outer_left_cleat` | `base_rail_bottom_left`<br>`base_side_left` | 243.435 / 174.435 | 0.013931 / 0.062983 | M, BC, R, WA | A+CAP | W, C |
| `bottom_outer_right_cleat` | `base_rail_bottom_right`<br>`base_side_right` | 4.842 / 5.361 | 0.000380 / 0.003397 | M, BC, R, WA | A+CAP | W, C |
| `center_post_cleat_left` | `base_header`<br>`base_post_center_left` | 0.000 / 17.117 | — / — | M, E, H, R, WA | A; +2 | W, H |
| `center_post_cleat_right` | `base_header`<br>`base_post_center_right` | 0.000 / 4.951 | — / — | M, E, H, R, WA | A; +2 | W, H |
| `center_principal_cleat_left` | `base_header`<br>`base_principal_center_left` | 26.392 / 18.871 | — / — | M, E, H, R, WA | A; +2 | W, H |
| `center_principal_cleat_right` | `base_header`<br>`base_principal_center_right` | 29.887 / 20.748 | — / — | M, P, E, H, R, WA | A; +2 | W, H, P |
| `knee_outer_left_inner_frame_block` | `base_header`<br>`base_side_left` | 206.532 / 230.645 | — / — | M, E, H, K, KB, KF, R, WA | A; +2 | W, H, K |
| `knee_outer_left_spine` | `base_post_outer_left`<br>`base_side_left` | 664.341 / 95.460 | 0.085108 / 0.248392 | M, K, KB, KF, R, WA | A | W, K |
| `knee_outer_right_inner_frame_block` | `base_header`<br>`base_side_right` | 206.501 / 224.898 | — / — | M, E, H, K, KB, KF, R, WA | A; +2 | W, H, K |
| `knee_outer_right_spine` | `base_post_outer_right`<br>`base_side_right` | 647.635 / 98.962 | 0.087274 / 0.251758 | M, K, KB, KF, R, WA | A | W, K |
| `left_service_inner_lower_cleat` | `base_principal_center_left`<br>`base_rail_service_lower_left` | 7.134 / 2.507 | 0.000319 / 0.002413 | M, R, WA | A | W |
| `left_service_inner_upper_cleat` | `base_principal_center_left`<br>`base_rail_service_upper_left` | 2.579 / 9.359 | 0.000398 / 0.004152 | M, R, WA | A | W |
| `left_service_outer_lower_cleat` | `base_rail_service_lower_left`<br>`base_side_left` | 7.092 / 7.192 | 0.000308 / 0.002823 | M, S | A | W |
| `left_service_outer_upper_cleat` | `base_rail_service_upper_left`<br>`base_side_left` | 5.296 / 5.553 | 0.000383 / 0.002401 | M, R, WA | A | W |
| `top_center_left_cleat` | `base_principal_center_left`<br>`base_rail_top` | 16.051 / 0.208 | 0.001092 / 0.007661 | M, R, WA | A | W |
| `top_center_right_cleat` | `base_principal_center_right`<br>`base_rail_top` | 46.003 / 3.052 | 0.001288 / 0.012803 | M, R, WA | A | W |
| `top_outer_left_cleat` | `base_rail_top`<br>`base_side_left` | 975.111 / 461.188 | 0.043462 / 0.158990 | M, TC, Left | T | W, C |
| `top_outer_right_cleat` | `base_rail_top`<br>`base_side_right` | 1098.757 / 527.959 | 0.048672 / 0.184692 | M, TC, Right | T | W, C |
| `wj04_lower_full_stock_cleat` | `base_principal_center_right`<br>`base_rail_service_lower_right` | 5.874 / 1.811 | 0.000245 / 0.002118 | M, R, WA | A | W |
| `wj04_upper_g7_crosscut_full_stock_cleat` | `base_principal_center_right`<br>`base_rail_service_upper_right` | 1.976 / 0.000 | 0.000229 / 0.003318 | M, R, WA | A | W |
| `wj06_outer_lower_right_cleat` | `base_rail_service_lower_right`<br>`base_side_right` | 5.533 / 3.559 | 0.000310 / 0.002836 | M, R, WA | A | W |
| `wj06_outer_upper_right_cleat` | `base_rail_service_upper_right`<br>`base_side_right` | 5.231 / 4.341 | 0.000386 / 0.002420 | M, R, WA | A | W |

## Exact finite remaining joint work

The identifiers below describe gaps already recorded by the consumed methods. They do not infer work from the register's generic null capacity fields. W is tied to each named block/host's actual opening intervals and signed cuts; it does not request another gross-member screen or a full elastic timber solve.

| ID | Existing unresolved requirement | Exact scope |
| --- | --- | --- |
| P | Resolve nut-to-washer-to-supported-wood transfer at center_principal_right_2 over the passage-side unsupported crescent. The 10 mm central ring is already supported; its current six-state pressure scenario is complete. Do not assign a full-annulus ratio to this seat. | Only `center_principal_right_2` nut seat on `base_principal_center_right`. |
| K | Join the two lateral planes, one physical tie and receiver bearing fields in a loaded common-shaft state for the four continuous bolts. Reuse the 24 fields, 96 static endpoint witnesses and 96 successful geometric placements; no placement replay is required. | Four continuous knee-side bolts shared by the left/right spine and inner frame blocks; four physical bolts, not eight. |
| H | Resolve header local splitting/torque interaction and oblique group applicability using the existing 72 states, 36 interfaces and 1,260 section states. The finite section/contact, Ceg and Cg scenarios are complete; F90 is characteristic, not adopted resistance. | Six header duties: two center-post, two center-principal and two inner knee blocks; twelve header axes. |
| C | Integrate local wood/group/splitting and washer transfer with simultaneous corner states. For the top corners use their own compatible local bolt allocations; original frame-allocation splitting cuts cannot silently qualify redistributed individual bolts. Elastic cleat deformation remains a model limit, not a new blanket solve requirement. | Two top and two bottom outer cleats; current component results stay active. Top allocations have finite compatible rigid-block responses; bottom component/body-balance scope remains separate. |
| W | Use the named finished bore/passage intervals and current signed cuts to resolve local ligament transfer, opening concentrations and short-block shear/torque. Bore-free member references supply no result at those intervals. | 24 blocks and their named hosts; exact interval counts and current geometry pointers are in each `member_checks` record. Header section/contact results and corner finished tangent paths remain completed partial coverage. |

Both top common-block responses and their component replays are finished. The finite next joint packets are the single central partial-seat transfer, the shared left/right continuous-knee transfer and the six named header duties. Corner resistance and named finished-opening transfer then use their saved simultaneous actions. This is a reuse agenda; it authorizes no mechanics execution or physical work.

## Completed geometry and conditional assumptions

All **96 knee shaft placements** remain completed, alongside 24 bearing fields and 96 static endpoint witnesses. Their loaded contact-compatibility gap is K, not a reopened placement failure. The 92 ksi endpoint scenario peaks at 0.922843; the alternative 45 ksi sensitivity reaches 1.317816. Neither scenario establishes delivered asymmetric-bolt resistance or a failed adopted criterion.

All **twelve bolt-tip/travel extension screens** are complete: four center-post, four principal/header and four inner knee/header axes, with no added overlap or undecided pair. The purchasing profile specification already covers all **104 bolts, 104 nuts and 208 washers**, separately from **66 Hillman screws**. Delivered LB/runout, full-form thread/nut engagement and bearing faces remain conditional product facts. The optional three-pitch projection is not an adopted failure rule. Do not restart the finished length checks from those unknowns.

Remaining and upper seat records, corrected top/bottom seats, primary knee offset evidence and **24 retained nominal annuli/72 probes** stay completed within their geometry scopes. Only the central passage-side nut seat has a recorded partial-support exception. Its smaller 10 mm supported ring is already complete (area 24.358092 mm², current pressure scenario 0.942288 MPa, conditional ratio 0.218668); the unsupported crescent has no full-annulus credit. Washer/head/nut metal properties and loaded spreading are separate from supported geometry.

The four direct nut-slide collisions already have bounded captured-nut alternatives. Preserve those sequences. For the retained leg stacks, preserve the intact-harness staging assumption at `wire_010_A10_A11` and `wire_130_K10_K11`. Top turning/counterhold and full stroke remain outside the straight-approach scope. These limits do not invalidate completed geometric routes or create another blanket operation gate.

The twelve retained axes are six separate pairs, outside the 96 block incidences. Their fresh individual/row-factor maximum is 0.962538; fresh 3/8- and 1/2-inch ideal pressure ratios are 0.208053 and 0.264300. Historical support-report pressures are not reused. The machine file joins all six arrangements to current force/component records and the completed concentric geometry; actual oblique Cg and complete local/washer resistance remain unassigned.

Parent retains the top-rail intact-prism comparison **1.021524** against the unchanged duration reference and the upper-left `edge_2` screw comparison (**1,871.251 N** axial with **726.611 N** lateral). These are explicit unresolved declared comparisons, not measured physical failures. Source rank 296/297, nonunique fixed-force seating, timber restraint/material hypotheses, screw laws and no-slip floor stay conditional. No adopted block failure is inferred from them; no floor test, material change or external sign-off is added.

## Machine receipt and reproduction

Frozen direct inputs:

| Input | SHA-256 |
| --- | --- |
| `operators-attempt02/operator-assessment.json` | `1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `rawlocal/joint-register/attempt01/register.json` | `79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca` |
| `rawlocal/upper-left-block/attempt01/checks.json` | `5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0` |
| `rawlocal/upper-left-block-components/attempt01/checks.json` | `25f0bb27a752f68d28ededb97017b1675d47751f44922d95d021d1b91e096420` |
| `rawlocal/upper-right-block/attempt01/checks.json` | `0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b` |

Machine table: [`duties.json`](rawlocal/remaining-block-duties/attempt02/duties.json). Source/output receipt: [`receipt.json`](rawlocal/remaining-block-duties/attempt02/receipt.json). Raw evidence stays ignored. The producer reads JSON/CSV metadata and hashes saved bytes; it opens no force/operator array and imports no CAD/mechanics helper. Each compatible method artifact is authenticated against the frozen register. Direct consumed source hashes are rechecked before writing. Inherited mutable producer differences remain provenance, not a new numerical failure.

From the repository root, use a fresh child under the owned raw folder:

```sh
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/remaining-block-duties.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/remaining-block-duties/attempt02-replay
```

Only this producer, this table and `rawlocal/remaining-block-duties/` belong to this task. Completed sources remain active and preserved; no archive, pruning, shared-document edit, staging or commit is performed. No frame/native/CAD/heavy run or test is required by this consolidation. Complete joint acceptance and physical release remain false.
