# Aligned first-knot contact-force audit

This read-only audit uses the immutable first accepted point at `t = 0.001 s` from
`ordinary-transient-aligned-first-knot-snapshot-attempt01`. It verifies the snapshot,
input-freeze, contact manifest, contact fragment, and DAT hashes before parsing.

- Snapshot hash: `a91a8412e25c92952ab414e5b65e29cb89a6364a9f114a49fa1ef6c7e81d272e`
- Frozen aligned input hash: `c3349f42bb8aaa3721e90f8f36ffd823c985ba9e0cffc6d8474b8154e1c5e267`
- DAT hash: `9bdf44cb6f7216128e0ba97f0c734011a0f0502b339d840ad99d33195e7b8123` (4058970 bytes)
- Contact manifest hash: `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d`; 35 ordered pairs.
- Aligned run deck: `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-aligned-attempt01/pilot.inp`; SHA-256 `48649259ba8441429a5dd094ae08487e3713d6b5b860ac39ca1acf71b837d963`.
- Direct deck check: 35 pair-specific CONTACT PRINT cards request `CF,CFN,CFS` in WJCP_001–035 order, plus one global `CDIS,CSTR,CELS,CNUM` card.
- The existing contact-wrench benchmark confirms the solver's three identical report labels follow the requested order `CF, CFN, CFS`; CF is the slave-side contact resultant.

The DAT has 100 report blocks: WJCP_001–033 have complete CF/CFN/CFS triplets; WJCP_034 has a CF report with a finite zero force and six NaN centroid/mean-normal values, but its remaining CF fields and CFN/CFS blocks are absent; WJCP_035 has no report. This is a partial output capture, not a complete 35-pair report.

Among complete triplets, CFN repeats the CF total-force vector for 33 pairs; it is kept separate and never counted again. CFS nonzero total-force records: 0.

The 16 bore pairs have 15 observed CF records; all observed CF vectors are exactly zero: `True`. 14 complete bore triplets also report zero area and NaN centroid/mean normal. Pair 034 has only a zero CF and NaN centroid/normal; pair 035 is absent, so the snapshot cannot verify all 16 bore pairs.

| # | Pair ID | Family | Master owner | Slave owner | CF force on slave (N) | Magnitude (N) | Centroid (mm) | Mean normal | Area (mm²) | Records |
| ---: | --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| 01 | `bottom_center_right_cleat_to_base_rail_bottom_right::wood_to_wood` | `wood_wood_finite_interface` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `(9.172473e-17, 0.0002489072, 0.000296636)` | 0.000387230824 | (114.7568, 22.46835, 445.3811) | (-9.538769e-14, -0.6427876, -0.7660444) | 268.4104 | 3_of_3 |
| 02 | `bottom_center_right_cleat_to_base_principal_center_right::wood_to_wood` | `wood_wood_finite_interface` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `(0.002506931, -8.320125e-18, -2.69594e-18)` | 0.002506931 | (89.05, 63.87367, 472.7163) | (-1, -6.976555e-17, -1.588798e-17) | 1290.081 | 3_of_3 |
| 03 | `base_rail_bottom_right_to_base_principal_center_right::wood_to_wood` | `wood_wood_finite_interface` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `(0.007460538, 2.348462e-18, 1.266474e-18)` | 0.007460538 | (89.05, -34.11034, 465.9732) | (-1, -8.267705e-17, -1.646288e-16) | 195.4264 | 3_of_3 |
| 04 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_head` | `head_washer_to_head` | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | `M01_A00_HEAD_WASHER` | `(2.016365e-18, -0.0001059173, -0.0001262273)` | 0.00016477805 | (134.3992, 85.51227, 511.1843) | (-8.712387e-15, 0.6427876, 0.7660444) | 19.73607 | 3_of_3 |
| 05 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_first_receiver` | `head_washer_to_first_receiver` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M01_A00_HEAD_WASHER` | `(-1.54321e-17, 0.0001065706, 0.0001270059)` | 0.000165794425 | (135.0585, 84.65476, 509.2513) | (-3.844216e-13, -0.6427876, -0.7660444) | 61.14167 | 3_of_3 |
| 06 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_nut` | `nut_washer_to_nut` | `M03_A00_NUT` | `M02_A00_NUT_WASHER` | `(-2.710199e-18, 9.888899e-05, 0.0001178513)` | 0.000153843951 | (136.0867, 2.065155, 410.1129) | (8.513376e-15, -0.6427876, -0.7660444) | 13.09333 | 3_of_3 |
| 07 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_last_receiver` | `nut_washer_to_last_receiver` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `M02_A00_NUT_WASHER` | `(-6.583577e-17, -9.828088e-05, -0.0001171266)` | 0.000152897913 | (135.0715, 2.497181, 412.4029) | (-7.060575e-13, 0.6427876, 0.7660444) | 38.56834 | 3_of_3 |
| 08 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_head` | `head_washer_to_head` | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | `M05_A01_HEAD_WASHER` | `(-5.74594e-19, -2.670913e-05, -3.183071e-05)` | 4.15520363e-05 | (135.6187, 58.64481, 533.7288) | (2.029136e-14, 0.6427876, 0.7660444) | 11.9456 | 3_of_3 |
| 09 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_first_receiver` | `head_washer_to_first_receiver` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M05_A01_HEAD_WASHER` | `(-2.25858e-17, 2.745864e-05, 3.272393e-05)` | 4.27180583e-05 | (135.6753, 58.60096, 531.113) | (1.266943e-12, -0.6427876, -0.7660444) | 23.34024 | 3_of_3 |
| 10 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_nut` | `nut_washer_to_nut` | `M07_A01_NUT` | `M06_A01_NUT_WASHER` | `(-7.919551e-19, 1.805325e-05, 2.151502e-05)` | 2.80858669e-05 | (140.6485, -24.218, 432.167) | (2.273212e-14, -0.6427876, -0.7660444) | 1.282465 | 3_of_3 |
| 11 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_last_receiver` | `nut_washer_to_last_receiver` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `M06_A01_NUT_WASHER` | `(2.006105e-17, -1.722867e-05, -2.053233e-05)` | 2.68030529e-05 | (135.3985, -23.07002, 433.8564) | (-3.109304e-13, 0.6427876, 0.7660444) | 25.66815 | 3_of_3 |
| 12 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_head` | `head_washer_to_head` | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | `M09_A02_HEAD_WASHER` | `(-0.00186622, 3.75326e-18, -3.930684e-18)` | 0.00186622 | (179.982, 28.01005, 477.2489) | (1, -9.679363e-16, 3.516077e-15) | 4.790229 | 3_of_3 |
| 13 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_first_receiver` | `head_washer_to_first_receiver` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M09_A02_HEAD_WASHER` | `(0.001858126, 8.993298e-19, 6.466934e-19)` | 0.001858126 | (177.95, 30.21663, 476.4042) | (-1, 1.43866e-16, -2.83411e-16) | 25.65558 | 3_of_3 |
| 14 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_nut` | `nut_washer_to_nut` | `M11_A02_NUT` | `M10_A02_NUT_WASHER` | `(0.001952292, -9.452305e-19, -1.327101e-18)` | 0.001952292 | (48.918, 35.38954, 469.9981) | (-1, 6.878377e-16, 4.361126e-16) | 8.367122 | 3_of_3 |
| 15 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_last_receiver` | `nut_washer_to_last_receiver` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `M10_A02_NUT_WASHER` | `(-0.001960431, 2.327811e-20, -3.665115e-20)` | 0.001960431 | (50.95, 32.83649, 472.5685) | (1, 1.200122e-16, -9.746814e-17) | 24.17977 | 3_of_3 |
| 16 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_head` | `head_washer_to_head` | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | `M13_A03_HEAD_WASHER` | `(-0.001658325, 4.704113e-18, -4.812192e-18)` | 0.001658325 | (179.982, 49.12377, 502.6552) | (1, -1.704994e-15, 3.865466e-15) | 3.846794 | 3_of_3 |
| 17 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_first_receiver` | `head_washer_to_first_receiver` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M13_A03_HEAD_WASHER` | `(0.001650365, 1.133039e-18, 1.07142e-19)` | 0.001650365 | (177.95, 49.90866, 498.7142) | (-1, -6.294202e-16, -3.604349e-16) | 24.71239 | 3_of_3 |
| 18 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_nut` | `nut_washer_to_nut` | `M15_A03_NUT` | `M14_A03_NUT_WASHER` | `(0.001737724, 1.336152e-18, -2.932207e-19)` | 0.001737724 | (48.918, 57.88173, 495.3482) | (-1, -3.897516e-17, 9.858812e-18) | 4.854073 | 3_of_3 |
| 19 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_last_receiver` | `nut_washer_to_last_receiver` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `M14_A03_NUT_WASHER` | `(-0.001744951, -1.253718e-19, 7.469477e-20)` | 0.001744951 | (50.95, 55.35433, 498.6073) | (1, 9.307357e-17, -1.752729e-16) | 31.22963 | 3_of_3 |
| 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | `open_bolt_shank_to_wood_bore` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | `open_bolt_shank_to_wood_bore` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | `open_bolt_shank_to_wood_bore` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | `open_bolt_shank_to_wood_bore` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | `open_bolt_shank_to_wood_bore` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | `open_bolt_shank_to_wood_bore` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | `open_bolt_shank_to_wood_bore` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | `open_bolt_shank_to_wood_bore` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | `open_bolt_shank_to_washer_bore` | `M01_A00_HEAD_WASHER` | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | `open_bolt_shank_to_washer_bore` | `M02_A00_NUT_WASHER` | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | `open_bolt_shank_to_washer_bore` | `M05_A01_HEAD_WASHER` | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | `open_bolt_shank_to_washer_bore` | `M06_A01_NUT_WASHER` | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | `open_bolt_shank_to_washer_bore` | `M09_A02_HEAD_WASHER` | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | `open_bolt_shank_to_washer_bore` | `M10_A02_NUT_WASHER` | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | 0 | 3_of_3 |
| 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | `open_bolt_shank_to_washer_bore` | `M13_A03_HEAD_WASHER` | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | `(0, 0, 0)` | 0 | NaN | NaN | missing | 1_of_3 |
| 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | `open_bolt_shank_to_washer_bore` | `M14_A03_NUT_WASHER` | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | `missing` | missing | missing | missing | missing | no_report |

## Slave-side owner subtotals

These sum only the available CF vectors for pairs where the listed owner is the manifest slave. They exclude every master-side contribution, so they are interaction subtotals rather than full body forces or reactions. The owner coverage flag counts manifest pairs with that owner in the slave role.

| Slave owner | CF vectors present / expected | All slave-role CF vectors observed | CF subtotal (N) | Magnitude (N) |
| --- | ---: | --- | --- | ---: |
| `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | 4 / 4 | True | (0, 0, 0) | 0 |
| `M01_A00_HEAD_WASHER` | 2 / 2 | True | (-1.3415735e-17, 6.533e-07, 7.786e-07) | 1.01637535e-06 |
| `M02_A00_NUT_WASHER` | 2 / 2 | True | (-6.8545969e-17, 6.0811e-07, 7.247e-07) | 9.46037981e-07 |
| `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | 4 / 4 | True | (0, 0, 0) | 0 |
| `M05_A01_HEAD_WASHER` | 2 / 2 | True | (-2.3160394e-17, 7.4951e-07, 8.9322e-07) | 1.16602196e-06 |
| `M06_A01_NUT_WASHER` | 2 / 2 | True | (1.92690949e-17, 8.2458e-07, 9.8269e-07) | 1.28281402e-06 |
| `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | 4 / 4 | True | (0, 0, 0) | 0 |
| `M09_A02_HEAD_WASHER` | 2 / 2 | True | (-8.094e-06, 4.6525898e-18, -3.2839906e-18) | 8.094e-06 |
| `M10_A02_NUT_WASHER` | 2 / 2 | True | (-8.139e-06, -9.2195239e-19, -1.36375215e-18) | 8.139e-06 |
| `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | 3 / 4 | False | (0, 0, 0) | 0 |
| `M13_A03_HEAD_WASHER` | 2 / 2 | True | (-7.96e-06, 5.837152e-18, -4.70505e-18) | 7.96e-06 |
| `M14_A03_NUT_WASHER` | 2 / 2 | True | (-7.227e-06, 1.2107802e-18, -2.1852593e-19) | 7.227e-06 |
| `W00_BOTTOM_CENTER_RIGHT_CLEAT` | 2 / 2 | True | (0.002506931, 0.0002489072, 0.000296636) | 0.00253666134 |
| `W01_BASE_RAIL_BOTTOM_RIGHT` | 1 / 1 | True | (0.007460538, 2.348462e-18, 1.266474e-18) | 0.007460538 |

## Method and limits

The actual frozen aligned `pilot.inp` hash is verified directly: it contains 35 pair-specific CONTACT PRINT cards in WJCP_001–WJCP_035 order, each requesting `CF,CFN,CFS`, and one global CONTACT PRINT card requesting `CDIS,CSTR,CELS,CNUM`. The matching frozen contact fragment numbers the same surface pairs in order; the matching manifest has 35 ordered owner rows. The existing CalculiX 2.21 contact-wrench benchmark independently confirms that the three same-labeled report blocks follow the requested order. This audit uses only CF as the primary total force on the slave surface. CFN's duplicate is preserved in the CSV/JSON, not summed. No master resultant or detailed wrench balance is inferred.

For complete bore records, zero CF force plus zero reported contact area and undefined centroid/mean normal indicates that this output contains no contact patch for that pair at this state. Zero resultant by itself cannot prove separation, and this single state cannot establish that the bore remains open through the transient. The final two bore pairs are not fully represented in the capture.

No reaction, impulse, force history, gap size, capacity, or joint acceptance is inferred from this single state. The loaded reference diagnostic's 100 N label is a reference scale; the snapshot README records the actual applied force at this knot as 0.0298 N per side.

Machine-readable per-pair CF force table: [`pair-contact-forces.csv`](pair-contact-forces.csv). Every observed CF/CFN/CFS report, including each centroid/normal record, is in [`pair-contact-reports.csv`](pair-contact-reports.csv). Slave-side subtotals: [`slave-owner-force-subtotals.csv`](slave-owner-force-subtotals.csv). Full provenance and parsed records: [`contact-force-audit.json`](contact-force-audit.json).
