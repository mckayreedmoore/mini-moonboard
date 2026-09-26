# Matched first-knot contact penalty comparison

This read-only comparison evaluates K=100000 and K=10000 at the same recorded `t = 0.001 s` knot. It uses the immutable first-knot DAT snapshots, the declared penalty comparison contract, and the existing bounded report parser. It does not read solver outputs from the live folders.

- Baseline snapshot/DAT/freeze hashes: `a91a8412e25c92952ab414e5b65e29cb89a6364a9f114a49fa1ef6c7e81d272e`, `9bdf44cb6f7216128e0ba97f0c734011a0f0502b339d840ad99d33195e7b8123`, `c3349f42bb8aaa3721e90f8f36ffd823c985ba9e0cffc6d8474b8154e1c5e267`.
- Child snapshot/DAT/freeze hashes: `168bf36c4d76b232696bf9099c06ec64d4c464c12ba8a4bd083059238ba9943e`, `b4fb37761c513d2d169ebf76d45459122061ecd2b5c657845f0342cf2bd96137`, `4f5d892d6f6270ae2d645463255a048b8b719331a0906412c4c4b85fd304f367`; child DAT 18171708 bytes.
- Comparison contract hash: `0d854a2d3d75bd395b00eae3c5b563a00e595b9b38da63d4ceb3d8c637ffd9b7`; time tolerance `1e-08 s`.
- Input verification: 35 manifest pair records match exactly; the contact-fragment diff is one line, `100000` → `10000`, corresponding to K 100000 → 10000 N/mm³.
- The actual shared `pilot.inp` hash `48649259ba8441429a5dd094ae08487e3713d6b5b860ac39ca1acf71b837d963` has 35 per-pair CONTACT PRINT cards requesting `CF,CFN,CFS`, plus global `CDIS,CSTR,CELS,CNUM`. Both branch load/amplitude freezes match; RAMP_N(0.001 s) = 0.000298, so the common reference force is 0.0298 N per side.

## Coverage and triage

The K=100000 baseline has 100 DAT report blocks: 33 complete triplets, pair 034 CF only, pair 035 absent. The K=10000 snapshot has 104 blocks: 34 complete triplets, pair 035 CF and CFN only. The compared fields are matched records only; no state is interpolated.

| Quantity | Matched vectors | Base only | Child only | Both missing | r > 10% flags | Max absolute L∞ change (N) | Max relative r |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: |
| CF | 34 / 35 | none | WJCP_035 | none | 18 | 0.01192827 | 11.90424 |
| CFN | 33 / 35 | none | WJCP_034, WJCP_035 | none | 18 | 0.01192827 | 11.90424 |
| CFS | 33 / 35 | none | WJCP_034 | WJCP_035 | 0 | 0 | 0 |

CF contact-patch state is known and matched for 33 pairs; state changes: none observed. Unknown/missing state records: WJCP_034, WJCP_035.

CFN is compared as a separate requested output. In complete matched groups it duplicates the CF total-force vector; it is never added to CF. CFS-only force vectors are also compared separately.

## Per-pair CF vectors

The table preserves signed global components. Absolute changes and relative `r` follow the contract's infinity-norm definition and 1e-6 N denominator floor. A force vector can be compared even if other fields in its block are incomplete; coverage flags retain that distinction.

| # | Pair ID | Status | Baseline CF (N) | Child CF (N) | Δ child−base (N) | |Δ|∞ (N) | r | Flag |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | --- |
| 01 | `bottom_center_right_cleat_to_base_rail_bottom_right::wood_to_wood` | matched_force_vector | (9.172473e-17, 0.0002489072, 0.000296636) | (-1.151316e-17, 0.0006217101, 0.0007409253) | (-1.032379e-16, 0.0003728029, 0.0004442893) | 0.0004442893 | 1.497759 | True |
| 02 | `bottom_center_right_cleat_to_base_principal_center_right::wood_to_wood` | matched_force_vector | (0.002506931, -8.320125e-18, -2.69594e-18) | (0.0144352, 1.535387e-20, 1.067087e-19) | (0.01192827, 8.335479e-18, 2.802649e-18) | 0.01192827 | 4.758116 | True |
| 03 | `base_rail_bottom_right_to_base_principal_center_right::wood_to_wood` | matched_force_vector | (0.007460538, 2.348462e-18, 1.266474e-18) | (0.008097693, 1.190455e-18, 1.68472e-18) | (0.000637155, -1.158007e-18, 4.18246e-19) | 0.000637155 | 0.08540336 | False |
| 04 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_head` | matched_force_vector | (2.016365e-18, -0.0001059173, -0.0001262273) | (2.336692e-18, -0.0002953555, -0.000351991) | (3.20327e-19, -0.0001894382, -0.0002257637) | 0.0002257637 | 1.788549 | True |
| 05 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_first_receiver` | matched_force_vector | (-1.54321e-17, 0.0001065706, 0.0001270059) | (-1.408746e-16, 0.0002959624, 0.0003527143) | (-1.254425e-16, 0.0001893918, 0.0002257084) | 0.0002257084 | 1.777149 | True |
| 06 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_nut` | matched_force_vector | (-2.710199e-18, 9.888899e-05, 0.0001178513) | (-7.903625e-19, 0.0002894224, 0.0003449202) | (1.919837e-18, 0.0001905334, 0.0002270689) | 0.0002270689 | 1.926741 | True |
| 07 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_last_receiver` | matched_force_vector | (-6.583577e-17, -9.828088e-05, -0.0001171266) | (-9.177185e-17, -0.0002889535, -0.0003443613) | (-2.593608e-17, -0.0001906726, -0.0002272347) | 0.0002272347 | 1.940078 | True |
| 08 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_head` | matched_force_vector | (-5.74594e-19, -2.670913e-05, -3.183071e-05) | (-3.049677e-18, -0.0002297308, -0.0002737825) | (-2.475083e-18, -0.0002030217, -0.0002419518) | 0.0002419518 | 7.601206 | True |
| 09 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_first_receiver` | matched_force_vector | (-2.25858e-17, 2.745864e-05, 3.272393e-05) | (-1.038261e-17, 0.000230404, 0.0002745848) | (1.220319e-17, 0.0002029454, 0.0002418609) | 0.0002418609 | 7.390948 | True |
| 10 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_nut` | matched_force_vector | (-7.919551e-19, 1.805325e-05, 2.151502e-05) | (-1.225942e-19, 0.0002228802, 0.0002656183) | (6.693609e-19, 0.0002048269, 0.0002441033) | 0.0002441033 | 11.34571 | True |
| 11 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_last_receiver` | matched_force_vector | (2.006105e-17, -1.722867e-05, -2.053233e-05) | (-9.79279e-18, -0.000222323, -0.0002649542) | (-2.985384e-17, -0.0002050943, -0.0002444219) | 0.0002444219 | 11.90424 | True |
| 12 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_head` | matched_force_vector | (-0.00186622, 3.75326e-18, -3.930684e-18) | (-0.007228814, 4.229215e-19, -6.531331e-18) | (-0.005362594, -3.330339e-18, -2.600647e-18) | 0.005362594 | 2.873506 | True |
| 13 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_first_receiver` | matched_force_vector | (0.001858126, 8.993298e-19, 6.466934e-19) | (0.007223932, 5.98167e-19, 3.348486e-19) | (0.005365806, -3.011628e-19, -3.118448e-19) | 0.005365806 | 2.887751 | True |
| 14 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_nut` | matched_force_vector | (0.001952292, -9.452305e-19, -1.327101e-18) | (0.007304073, -8.33021e-20, -1.726521e-18) | (0.005351781, 8.619284e-19, -3.9942e-19) | 0.005351781 | 2.741281 | True |
| 15 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_last_receiver` | matched_force_vector | (-0.001960431, 2.327811e-20, -3.665115e-20) | (-0.00731259, -3.240626e-19, -1.477413e-19) | (-0.005352159, -3.473407e-19, -1.110901e-19) | 0.005352159 | 2.730093 | True |
| 16 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_head` | matched_force_vector | (-0.001658325, 4.704113e-18, -4.812192e-18) | (-0.007027263, -8.288936e-19, -6.642524e-18) | (-0.005368938, -5.533007e-18, -1.830332e-18) | 0.005368938 | 3.237567 | True |
| 17 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_first_receiver` | matched_force_vector | (0.001650365, 1.133039e-18, 1.07142e-19) | (0.007023787, 2.070779e-18, 1.468237e-18) | (0.005373422, 9.3774e-19, 1.361095e-18) | 0.005373422 | 3.255899 | True |
| 18 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_nut` | matched_force_vector | (0.001737724, 1.336152e-18, -2.932207e-19) | (0.007086457, 2.054021e-18, 1.042318e-18) | (0.005348733, 7.17869e-19, 1.335539e-18) | 0.005348733 | 3.078011 | True |
| 19 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_last_receiver` | matched_force_vector | (-0.001744951, -1.253718e-19, 7.469477e-20) | (-0.007093492, -2.862612e-19, 2.379348e-19) | (-0.005348541, -1.608894e-19, 1.6324e-19) | 0.005348541 | 3.065153 | True |
| 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | matched_force_vector | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) | 0 | 0 | False |
| 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | child_only | missing | (0, 0, 0) | missing | missing | missing | None |

All 105 pair×quantity comparisons, including CFN and CFS separately and explicit missing records, are in [`contact-comparison.csv`](contact-comparison.csv). CF contact-state comparisons are in [`pair-contact-state.csv`](pair-contact-state.csv); complete provenance and parsed records are in [`comparison.json`](comparison.json).

## Scope limits

The 10% flags are numerical triage rules from the declared contract. They do not define a safe force difference or support a physical-stiffness choice. Contact area changes are not interpreted as material response. Single-state contact forces supply no master-side resultant, action/reaction balance, momentum, impulse, or later contact history. The baseline remains incomplete and child pair 035 lacks CFS; no missing comparison is treated as passing.
