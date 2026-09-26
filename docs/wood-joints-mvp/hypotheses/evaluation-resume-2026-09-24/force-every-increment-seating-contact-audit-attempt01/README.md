# Force-every-increment seating contact-onset audit

This audit uses only the immutable output-prefix snapshot `force-every-increment-seating-prefix-attempt01`. Snapshot manifest SHA-256 `001cefdb37a52bdf6bc6d1d590310c93d91d7f5b2f7cf0a35ad2e10c097e0d8a`; input-freeze SHA-256 `f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66`. The captured DAT is 353025378 bytes with SHA-256 `5b9ef4ed407c11008c0d2f31dc92037a08564a41859825c0a54ea587f71fa3e4`.

`pilot.sta` contains 20 accepted increments from 0.001 through 0.02 s. The execution record was `running` at capture and declares mechanical acceptance false. The capture is non-atomic; only accepted states are reported. No live output folder was read.

## First observed bore force and area

The earliest finite nonzero bore CF vectors are at `t=0.02 s` (4 pair reports share this first accepted time).

| Pair | Bore interface | Wood/master owner | Bolt/slave owner | CF vector (N) | Area (mm²) |
| --- | --- | --- | --- | --- | ---: |
| WJCP_020 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | (-1.538434, -8.615487, 7.227133) | 2.395896 |
| WJCP_022 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | (-0.4641958, -7.852277, 6.589487) | 6.103547 |
| WJCP_024 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | (0.01732653, -11.13889, 9.65674) | 3.977105 |
| WJCP_026 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | (0.01363635, -11.31264, 9.925294) | 2.795686 |

The first positive-area bore CF report occurs at `t=0.02 s` on WJCP_020, `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` (master owner `W00_BOTTOM_CENTER_RIGHT_CLEAT`, slave owner `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION`): area=2.395896 mm², CF=[-1.538434, -8.615487, 7.227133] N.

The first positive-area-and-nonzero-CF event (if any) is separately recorded in the JSON. A complete CF record with exact-zero force/area remains a reported zero, while an absent or partial report remains unknown. CFN is not added to CF; CFS is kept separate. A first nonzero CF vector is only an output event and does not establish complete physical seating, bolt capacity, reaction balance, or mechanical acceptance.

## Per-increment pair and global-output coverage

| Time (s) | Inc. | Headers | Full triplets | Partial | Missing | CDIS rows | CNUM |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.001 | 1 | 105/105 | 35/35 | 0 | 0 | 109308 | 109308 |
| 0.002 | 2 | 105/105 | 35/35 | 0 | 0 | 108958 | 108958 |
| 0.003 | 3 | 105/105 | 35/35 | 0 | 0 | 108985 | 108985 |
| 0.004 | 4 | 105/105 | 35/35 | 0 | 0 | 109021 | 109021 |
| 0.005 | 5 | 105/105 | 35/35 | 0 | 0 | 108917 | 108917 |
| 0.006 | 6 | 105/105 | 35/35 | 0 | 0 | 108874 | 108874 |
| 0.007 | 7 | 105/105 | 35/35 | 0 | 0 | 108927 | 108927 |
| 0.008 | 8 | 105/105 | 35/35 | 0 | 0 | 108963 | 108963 |
| 0.009 | 9 | 105/105 | 35/35 | 0 | 0 | 108986 | 108986 |
| 0.01 | 10 | 105/105 | 35/35 | 0 | 0 | 109025 | 109025 |
| 0.011 | 11 | 105/105 | 35/35 | 0 | 0 | 109002 | 109002 |
| 0.012 | 12 | 105/105 | 35/35 | 0 | 0 | 108871 | 108871 |
| 0.013 | 13 | 105/105 | 35/35 | 0 | 0 | 108838 | 108838 |
| 0.014 | 14 | 105/105 | 35/35 | 0 | 0 | 109961 | 109961 |
| 0.015 | 15 | 105/105 | 35/35 | 0 | 0 | 109164 | 109164 |
| 0.016 | 16 | 105/105 | 35/35 | 0 | 0 | 109184 | 109184 |
| 0.017 | 17 | 105/105 | 35/35 | 0 | 0 | 108954 | 108954 |
| 0.018 | 18 | 105/105 | 35/35 | 0 | 0 | 108456 | 108456 |
| 0.019 | 19 | 105/105 | 35/35 | 0 | 0 | 108297 | 108297 |
| 0.02 | 20 | 100/105 | 33/35 | 1 | 1 | 72155 | 72155 |

All observed pair headers are checked for both matching slave/master surface IDs and expected WJCP/CF-CFN-CFS slot. Per-pair fields and missing/partial states are in `pair-coverage.csv`. Complete global CDIS/CNUM output does not imply complete pair CF/CFN/CFS output.

Incomplete pair states:

- t=0.02s: WJCP_034 partial (CF=partial_fields,CFN=missing,CFS=missing); WJCP_035 missing (CF=missing,CFN=missing,CFS=missing)

## Bore-pair CF history

There are 16 manifest bore pairs. Bore CF output was observed at 318 of 320 possible accepted pair-states. Positive-area events: 4; finite nonzero-CF events: 4.

| Time (s) | Pair # | Bore pair | CF status | Area (mm²) | CF vector (N) |
| ---: | ---: | --- | --- | ---: | --- |
| 0.001 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.001 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.002 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.003 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.004 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.005 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.006 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.007 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.008 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.009 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.01 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.011 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.012 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.013 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.014 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.015 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.016 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.017 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.018 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.019 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 2.395896 | (-1.538434, -8.615487, 7.227133) |
| 0.02 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 6.103547 | (-0.4641958, -7.852277, 6.589487) |
| 0.02 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 3.977105 | (0.01732653, -11.13889, 9.65674) |
| 0.02 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 2.795686 | (0.01363635, -11.31264, 9.925294) |
| 0.02 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.02 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | partial_fields | unknown | (0, 0, 0) |
| 0.02 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | missing | unknown | unknown |

No inference is made about times after the captured `0.020 s` state, responses between outputs, physical seating, or joint acceptance. The DAT reports a contact-force vector for each named pair; CFN is not treated as an independent force to add. No CEL or FRD fields were used; CEL was not captured, and the FRD file was present in the snapshot but not read or hashed.

Machine-readable report and source pins are in [`contact-onset-audit.json`](contact-onset-audit.json).
