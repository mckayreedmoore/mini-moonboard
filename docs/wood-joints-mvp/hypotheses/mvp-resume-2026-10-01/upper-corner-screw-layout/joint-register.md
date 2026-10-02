# Current four-screw-layout joint register

This register indexes the frozen 250 lb, six-case working scenario after the
four owner-authorized upper-panel screw moves. It connects each physical bolt
to its current saved forces and applicable method records. It supplies no new
joint capacity or acceptance. Complete joints and physical release remain
**HOLD**; the 47-criterion authority and release flags are unchanged.

The [preserved earlier register](../joint-register.md) uses the historical
`ec69b49c…` force source. Its numerical envelopes are not used here. Current
method selection follows [bolted replay](bolted-replay.md),
[header replay](header-replay.md), [knee replay](knee-replay.md) and
[member replay](member-replay.md).

The [upper-right combined-transfer extension](upper-right-combined-transfer.md)
uses this exact force source for 72 local bolt/contact states. Its smooth-shank
steel proxies remain below the declared 92 ksi hypothesis; seat concentration,
rigid-washer transfer and independent host poses retain their explicit limits.
It supplies no complete-joint acceptance or new register force allocation.
Its [shared-rail extension](upper-right-rail-pair.md) balances all six interface
wrenches with one rail pose and derives a different compatible bolt split.
Those local reactions do not replace the register's saved frame forces.

## Census and force convention

The current index contains **24 blocks, 104 physical bolt axes, 96 block-axis
incidences and 66 separate Hillman 42605 panel/kicker screw axes**. The bolt
count comprises 92 candidate axes and twelve retained frame bolts. The four
continuous `knee_outer_{left,right}_side_{1,2}` bolts each serve two block
duties and are counted once as physical hardware. There are 108 bolt lateral
interfaces: 96 candidate and twelve retained.

The six cases are `a12-rear`, `a12-forward`, `a12-left`, `k12-right`,
`k12-rear` and `a1-rear`. Every force comes from nominal-gap scale 1.0,
`case_id + '_gap_raw_force_n'`, in `frame-250-attempt02/response.npz`.
Rows are mapped through `operators-attempt02/row-identities.json` and the
current model, including the two moved center screws' top-rail receivers.

For a bolt, **V is the resultant of the two signed components on one saved
interface**. T is the simultaneous signed outer-seat tie, with positive values
denoting tension. Separate knee planes are retained separately; their
magnitudes are not added into a bolt load or capacity. Opposed end-seat forces
belong to one physical axial tie. A table's V and T envelopes may occur in
different cases; the machine index retains their simultaneous companions.
For screws, the same axial force acts on the head pull-through and timber
withdrawal routes; these have separate resistances.

The frame supplies saved simultaneous forces and bounded fixed-force seating
certificates, with nominal-state ranks 296/297. These do not supply unique
poses, a full motion envelope or strict tangent stability. Timber, screw
stiffness, bolt profiles, no preload/friction and the no-slip floor remain
declared source assumptions. This register neither changes those laws nor
transfers an earlier frame pass.

## Current method coverage

| Method | Exact scope | Applicability limit |
| --- | --- | --- |
| Remaining-bolt screen | 92 physical axes: 80 candidate and twelve retained; 576 plane states | 384 candidate and 72 retained single-shear references; 72 end-grain and 48 continuous-knee plane states have null single-shear resistances. |
| Top-corner components | Eight axes; 48 simultaneous states; sixteen finished paths and sixteen washer seats | Declared lateral/group sensitivities and pressure/stress demands; no complete axial/lateral/contact solution or washer metal resistance. |
| Upper-right shared rail | Two axes, sixteen face cells and six local interface-wrench states | One declared K20 branch with fixed cleat and rigid washers; no coupled side group, frame redistribution, washer metal resistance or complete joint acceptance. |
| Bottom-corner components | Eight axes; 48 simultaneous states; sixteen paths and sixteen washer seats | Overlaps the remaining-bolt census; it is additional method coverage, not extra hardware or an independent joint acceptance. |
| End-grain route | Twelve axes; 72 signed states | Conditional Fe-perpendicular and one Ceg application; adjusted detailing/group and complete transfer remain separate. |
| Lower-left outer service | Four axes; 24 signed states | Fresh individual lateral references fill the remaining screen's exclusion; zero-force direction/reference fields remain null. |
| Header joint method | Six joints, twelve axes, 72 bolt states, 36 interfaces and 42 body balances | Finite section/contact and row-factor sensitivities; no universal oblique detailing rule or local splitting/torque resistance. |
| Partial central seat | `center_principal_right_2`; six states | Supported central ring only; actual nut footprint and washer transfer across the unsupported outer crescent remain unqualified. |
| Retained pairs / washers | Six pairs, 72 axis states; 24 washer seats, 144 seat states | Row factors and full-annulus pressures are hypotheses; actual oblique Cg, seat support and metal transfer remain null. |
| Continuous knees | Four physical bolts, 24 bolt states, 48 planes and twelve groups | Summed-endpoint reference scenarios and affine equilibrium witnesses are not a normative asymmetric-bolt resistance or a displacement-compatible solution. |
| Common knee shaft placement | 96 constructions across both saved gap scales | Geometric representative-pose witnesses only; nominal rows are indexed separately from zero-gap rows. No loaded contact compatibility is established. |
| Member screens | 20 frame timbers, 24 blocks, 264 balances and 55,176 cuts | Elementary member references do not qualify disturbed joint regions, excluded old/new hole slices or whole joints. |

Fresh header placement has 70 zero-in-plane states with null first-ray fields
and two directional states with no first-ray comparison below 4D. The older
five short oblique comparisons are not current results. Absence of a short
comparison does not establish a universal detailing or splitting resistance.

## Connector blocks

The machine index is the authority for exact axes, receiver pairs, interface
rows, method pointers and six simultaneous state records. The compact table
below reports separate demand envelopes, in N, rather than joint capacities.

Forces are rounded to 0.1 N; the machine file retains full signed values. Axis labels use the final segment, scoped by block; full IDs and all planes remain in the machine file. **R** remaining-bolt, **WA** its ideal annulus, **TC/BC** top/bottom components, **E** end-grain, **H** header, **S** lower service, **CS** central seat, **K** knee endpoint, **KB** affine bearing and **KF** geometric fit. Member methods cover every block separately.

| Block | Incident duties / hosts | Peak V / simultaneous T, N | Separate peak T, N | Methods |
| --- | --- | --- | --- | --- |
| `bottom_center_left_cleat` | `principal_{1,2}` → `base_principal_center_left`<br>`rail_{1,2}` → `base_rail_bottom_left` | 5.5 / 9.3<br>a1-rear / `principal_1` / plane-1 | 9.3<br>a1-rear / `rail_1` | R, WA |
| `bottom_center_right_cleat` | `principal_{1,2}` → `base_principal_center_right`<br>`rail_{1,2}` → `base_rail_bottom_right` | 4.9 / 3.4<br>k12-right / `rail_2` / plane-8 | 8.6<br>k12-right / `principal_1` | R, WA |
| `bottom_outer_left_cleat` | `rail_{1,2}` → `base_rail_bottom_left`<br>`side_{1,2}` → `base_side_left` | 243.4 / 174.4<br>a1-rear / `side_1` / plane-11 | 176.6<br>a1-rear / `side_2` | BC, R, WA |
| `bottom_outer_right_cleat` | `rail_{1,2}` → `base_rail_bottom_right`<br>`side_{1,2}` → `base_side_right` | 4.8 / 5.4<br>k12-rear / `side_1` / plane-15 | 14.8<br>a12-left / `side_1` | BC, R, WA |
| `center_post_cleat_left` | `center_post_header_left_{1,2}` → `base_header`<br>`center_post_left_{1,2}` → `base_post_center_left` | 0.0 / 17.1<br>k12-right / `center_post_header_left_1` / plane-17 | 17.1<br>k12-right / `center_post_header_left_1` | E, H, R, WA |
| `center_post_cleat_right` | `center_post_header_right_{1,2}` → `base_header`<br>`center_post_right_{1,2}` → `base_post_center_right` | 0.0 / 5.0<br>k12-right / `center_post_header_right_1` / plane-19 | 21.2<br>a12-forward / `center_post_header_right_1` | E, H, R, WA |
| `center_principal_cleat_left` | `center_principal_header_left_{1,2}` → `base_header`<br>`center_principal_left_{1,2}` → `base_principal_center_left` | 26.4 / 18.9<br>a12-left / `center_principal_header_left_2` / plane-26 | 29.4<br>k12-right / `center_principal_header_left_2` | E, H, R, WA |
| `center_principal_cleat_right` | `center_principal_header_right_{1,2}` → `base_header`<br>`center_principal_right_{1,2}` → `base_principal_center_right` | 29.9 / 20.7<br>k12-right / `center_principal_header_right_2` / plane-28 | 29.2<br>k12-rear / `center_principal_header_right_1` | CS, E, H, R, WA |
| `knee_outer_left_inner_frame_block` | `knee_outer_left_inner_header_{1,2}` → `base_header`<br>`knee_outer_left_side_{1,2}` → `base_side_left` | 206.5 / 230.6<br>a12-rear / `knee_outer_left_side_2` / plane-40 | 321.5<br>a12-left / `knee_outer_left_side_2` | E, H, K, KB, KF, R, WA |
| `knee_outer_left_spine` | `knee_outer_left_post_{1,2}` → `base_post_outer_left`<br>`knee_outer_left_side_{1,2}` → `base_side_left` | 664.3 / 95.5<br>a12-left / `knee_outer_left_side_1` / plane-37 | 321.5<br>a12-left / `knee_outer_left_side_2` | K, KB, KF, R, WA |
| `knee_outer_right_inner_frame_block` | `knee_outer_right_inner_header_{1,2}` → `base_header`<br>`knee_outer_right_side_{1,2}` → `base_side_right` | 206.5 / 224.9<br>k12-rear / `knee_outer_right_side_2` / plane-48 | 332.9<br>k12-right / `knee_outer_right_side_2` | E, H, K, KB, KF, R, WA |
| `knee_outer_right_spine` | `knee_outer_right_post_{1,2}` → `base_post_outer_right`<br>`knee_outer_right_side_{1,2}` → `base_side_right` | 647.6 / 99.0<br>k12-right / `knee_outer_right_side_1` / plane-45 | 332.9<br>k12-right / `knee_outer_right_side_2` | K, KB, KF, R, WA |
| `left_service_inner_lower_cleat` | `lower_principal_{1,2}` → `base_principal_center_left`<br>`lower_rail_{1,2}` → `base_rail_service_lower_left` | 7.1 / 2.5<br>a1-rear / `lower_principal_2` / plane-54 | 10.1<br>a1-rear / `lower_principal_1` | R, WA |
| `left_service_inner_upper_cleat` | `upper_principal_{1,2}` → `base_principal_center_left`<br>`upper_rail_{1,2}` → `base_rail_service_upper_left` | 2.6 / 9.4<br>a12-left / `upper_rail_2` / plane-64 | 13.0<br>a12-left / `upper_principal_1` | R, WA |
| `left_service_outer_lower_cleat` | `lower_rail_{1,2}` → `base_rail_service_lower_left`<br>`lower_side_{1,2}` → `base_side_left` | 7.1 / 7.2<br>a1-rear / `lower_side_2` / plane-52 | 11.2<br>k12-right / `lower_rail_1` | S |
| `left_service_outer_upper_cleat` | `upper_rail_{1,2}` → `base_rail_service_upper_left`<br>`upper_side_{1,2}` → `base_side_left` | 5.3 / 5.6<br>a12-forward / `upper_side_1` / plane-59 | 10.4<br>k12-right / `upper_side_1` | R, WA |
| `top_center_left_cleat` | `principal_{1,2}` → `base_principal_center_left`<br>`rail_{1,2}` → `base_rail_top` | 16.1 / 0.2<br>a12-rear / `principal_2` / plane-66 | 45.5<br>a12-left / `rail_2` | R, WA |
| `top_center_right_cleat` | `principal_{1,2}` → `base_principal_center_right`<br>`rail_{1,2}` → `base_rail_top` | 46.0 / 3.1<br>k12-rear / `principal_2` / plane-70 | 73.3<br>k12-rear / `principal_1` | R, WA |
| `top_outer_left_cleat` | `rail_{1,2}` → `base_rail_top`<br>`side_{1,2}` → `base_side_left` | 975.1 / 461.2<br>a12-left / `side_2` / plane-76 | 660.7<br>a12-left / `rail_1` | TC |
| `top_outer_right_cleat` | `rail_{1,2}` → `base_rail_top`<br>`side_{1,2}` → `base_side_right` | 1098.8 / 528.0<br>k12-rear / `side_2` / plane-80 | 757.3<br>k12-right / `rail_1` | TC |
| `wj04_lower_full_stock_cleat` | `lower_principal_{1,2}` → `base_principal_center_right`<br>`lower_rail_{1,2}` → `base_rail_service_lower_right` | 5.9 / 1.8<br>a12-left / `lower_principal_2` / plane-82 | 7.1<br>a12-left / `lower_principal_1` | R, WA |
| `wj04_upper_g7_crosscut_full_stock_cleat` | `upper_principal_{1,2}` → `base_principal_center_right`<br>`upper_rail_{1,2}` → `base_rail_service_upper_right` | 2.0 / 0.0<br>a12-left / `upper_rail_1` / plane-87 | 12.8<br>k12-right / `upper_principal_1` | R, WA |
| `wj06_outer_lower_right_cleat` | `lower_rail_{1,2}` → `base_rail_service_lower_right`<br>`lower_side_{1,2}` → `base_side_right` | 5.5 / 3.6<br>k12-rear / `lower_side_2` / plane-92 | 11.3<br>a12-left / `lower_rail_1` | R, WA |
| `wj06_outer_upper_right_cleat` | `upper_rail_{1,2}` → `base_rail_service_upper_right`<br>`upper_side_{1,2}` → `base_side_right` | 5.2 / 4.3<br>k12-right / `upper_side_1` / plane-95 | 10.5<br>a12-left / `upper_side_1` | R, WA |

## Retained frame arrangements

Twelve retained axes remain six two-bolt arrangements. They are separate from
the 96 candidate block-axis incidences.

**RG** is the retained pair row-factor sensitivity; **RW** is its catalog-family annulus reference. Actual oblique Cg, supported seat pressure and washer metal resistance remain null.

| Arrangement / axes 1 and 2 | Receiver pair | Peak V / simultaneous T, N | Separate peak T, N | Methods |
| --- | --- | --- | --- | --- |
| `lumber_leg_bolt_left_{1,2}` | `base_side_left` ↔ `lumber_leg_left` | 1864.3 / 420.5<br>a12-rear / `lumber_leg_bolt_left_2` / wood-interface | 846.7<br>a12-left / `lumber_leg_bolt_left_2` | R, WA, RG, RW |
| `lumber_leg_bolt_right_{1,2}` | `base_side_right` ↔ `lumber_leg_right` | 1834.0 / 484.8<br>k12-rear / `lumber_leg_bolt_right_2` / wood-interface | 887.9<br>k12-right / `lumber_leg_bolt_right_2` | R, WA, RG, RW |
| `rail_front_bolt_left_{1,2}` | `base_floor_left` ↔ `base_post_outer_left` | 1043.4 / 194.7<br>a12-forward / `rail_front_bolt_left_2` / wood-interface | 350.5<br>a12-left / `rail_front_bolt_left_2` | R, WA, RG, RW |
| `rail_front_bolt_right_{1,2}` | `base_floor_right` ↔ `base_post_outer_right` | 1018.8 / 354.7<br>k12-right / `rail_front_bolt_right_2` / wood-interface | 354.7<br>k12-right / `rail_front_bolt_right_2` | R, WA, RG, RW |
| `rail_rear_bolt_left_{1,2}` | `base_floor_left` ↔ `lumber_leg_left` | 656.4 / 78.3<br>a12-forward / `rail_rear_bolt_left_1` / wood-interface | 141.3<br>a12-left / `rail_rear_bolt_left_2` | R, WA, RG, RW |
| `rail_rear_bolt_right_{1,2}` | `base_floor_right` ↔ `lumber_leg_right` | 630.3 / 84.8<br>k12-right / `rail_rear_bolt_right_1` / wood-interface | 139.4<br>k12-right / `rail_rear_bolt_right_2` | R, WA, RG, RW |

## Finite remaining load-transfer decisions

1. **Panel sharing and the actual head/withdrawal route.** The current model's
   peak nominal screw axial force is 1,871.251 N, at the unchanged upper-left
   `edge_2`, A12-rear, with simultaneous V=726.611 N. The
   [head-reference worksheet](head-reference-basis.md) gives favorable,
   conditional 930.222–984.128 N allowances using the prior retailer-nominal
   9.017 mm head and stated plywood hypotheses. This is an unresolved declared
   comparison, not a measured Hillman failure. Actual product resistance and
   stiffness remain null; the incomplete paired-load sensitivity supplies no
   replacement envelope.
2. **Top-rail shear and torsion.** The fresh compatible intact-prism comparison
   is 1.021524 against the unchanged normal-duration reference, governing at
   K12-rear. Normal/stability references peak at 0.628421 under the stated
   timber restraints. The shear/torsion exception remains; local transfer near
   the cleat and hole slices is not established by that beam field.
3. **Complete corner transfer.** Individual dowel-yield references, signed ties,
   nominal supported areas and washer strip stresses have not been combined
   into a common contact/displacement solution for both orthogonal bolt groups.
   Head/nut footprint, washer reaction distribution, bolt bending, timber
   bearing, local splitting and slip/rotation must refer to the same state.
   [Upper-right washer bounds](upper-right-washer-contact-bounds.md) retain
   their pressure-cap and strip assumptions; they are not predicted physical
   stresses or a product rating.
4. **Continuous knee compatibility and delivered bolt profiles.** The 92 ksi
   endpoint scenario peaks at 0.922843; the alternative 45 ksi scenario reaches
   1.317816. Affine bearing fields satisfy static constraints and common-shaft
   placements exist, but those separate witnesses do not establish one loaded
   contact solution. Actual smooth shank/thread/runout and steel properties
   remain part of the conditional hardware basis.
5. **Local resistance applicability.** Actual oblique group factors, complete
   splitting/torque interaction, excluded finished sections, retained seat
   support and the central washer crescent remain explicit method limits.
   Small component ratios do not remove these missing checks.

The next useful mechanics step is a same-state upper-corner transfer model
that connects the existing orthogonal bolt groups, head/nut/washer reactions
and local timber bearing. Its inputs should come from this index rather than
independently combined component peaks. Parent retains the broader panel
sharing and top-rail decision. This register does not reopen assembly or
movement work or authorize a geometry change.

## Reproduction and receipts

Run from the repository root with the existing environment. The producer
uses NumPy and standard-library parsing plus the preserved register's pure
helpers; it imports no CAD helper and runs no frame/native solve. It refuses
an existing output directory. Choose a fresh attempt for a replay.

```sh
task_packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$task_packet/upper-corner-screw-layout/joint_register.py" \
  --output "$task_packet/upper-corner-screw-layout/rawlocal/joint-register/attempt01"
```

The historical response is authenticated only as inherited receipt provenance;
its force arrays are never opened. Frozen source and output receipts follow.

| Frozen input or maintained producer, relative to this folder | SHA-256 |
| --- | --- |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `operators-attempt02/operator-assessment.json` | `1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |
| `operators-attempt02/model-inputs.json` | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| `joint_register.py` | `c939fd65d340d6c332739525af381b5570290087621fef64e74a8302368c3a6a` |

The completed [machine register](rawlocal/joint-register/attempt01/register.json) contains 624 bolt-axis states, 648 bolt-interface states and 396 screw states. `axes.csv` has 170 physical connector rows; `states.csv` has 1,044 interface rows (648 bolt plus 396 screw). All 246 consumed source/output pins matched before and after indexing, subject to the explicit inherited-receipt distinction below. Ruff passed. No software tests, mechanics solves, geometry operation or review loop ran.

| Output in `rawlocal/joint-register/attempt01/` | SHA-256 |
| --- | --- |
| `register.json` | `79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca` |
| `axes.csv` | `f1a25806d8fcad257ba200b70578d45c1ea564dd1ad6d2a065740aa2fc39cde8` |
| `states.csv` | `e232d05f7f212ae4a61671f0a982a0ed28455b30cb8c0da4ba1a7b81897fb52c` |
| `source-pins.json` | `3dd5c1945aaa039c964b418851e841002abd765e99d6dd35ef1a1647ea7591d0` |
| `producer.py.snapshot` | `c939fd65d340d6c332739525af381b5570290087621fef64e74a8302368c3a6a` |

The source register includes referenced `/tmp` evidence as absolute paths; those files were hashed read-only and preserved. The first binding attempt rejected an unnecessary repository-only path restriction. Subsequent preparation found the inherited helper difference below and an optional knee-record member field; both were corrected in this new producer before any output directory was created. One complete immutable packet was produced.

### Inherited helper receipt distinction

The member-stability receipt records `bottom_corner_checks.py` at `2afb5a8af006c4ae4818e863bc4300d4e63d070a816dd5e96079718d8ede57c3`. The exact archived `../bottom-corner-component-attempt06/producer.py.snapshot` authenticates that version. The maintained helper is `5df7a264354e1488c2a68332820fe927e8dcb1fa9721111ec8fac5c00ad19e26`. The producer checks that the only source difference is changing `reviewed_geometry_changed: false` to propagation from `member_report`. Numerical and geometry helper code is otherwise identical.

`inherited_receipt_differences` preserves that discrepancy and both identities. This is an archive attestation, not a claim that the live file matches its older receipt. Neither helper version is executed here, and the old receipt is not rewritten. Every current numerical method output and the frozen force/operator inputs is authenticated directly.

No historical packet, source geometry, authority, release flag or physical part was changed. Raw evidence stays local and ignored; parent owns publication.
