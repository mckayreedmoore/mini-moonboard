# K=10000 terminal contact-history audit

This audit streamed the terminal `pilot.dat` once and reused the validated first-knot report parser for CF/CFN/CFS record field semantics. It grouped records by printed time, then matched each group to accepted `pilot.sta` times and execution observations. No trial time was counted as accepted.

The execution ended `bounded_timeout` (return code `137`; recorded wall-clock elapsed time `2407.139 s`; configured timeout `2400 s`). The last accepted state is `t=0.017 s`, increment `17`, `7` iterations. The requested 0.025 s endpoint was not reached; this accepted increment is not a mechanically accepted joint result.

Frozen DAT SHA-256: `2e726f375f865321d54b89535a9a667678e71b706826eb4d178448667a35460c` (305519240 bytes). Execution SHA-256: `6c5eedb7b2b33f9841f50bbfc8d50642459fc4d50e4825771ce73fc3bb2b47c0`. Input freeze SHA-256: `4f5d892d6f6270ae2d645463255a048b8b719331a0906412c4c4b85fd304f367`. All 17 DAT output times match the accepted `.sta` and execution observation times.

The actual frozen deck hash binds 35 pair-specific `CF,CFN,CFS` requests in WJCP_001–WJCP_035 order plus global `CDIS,CSTR,CELS,CNUM`. The ordered manifest has 35 owner rows. Each report slot is accepted only when the slave-derived pair index matches the expected slot and the WJCP slave/master surface IDs match each other. The request type is assigned by the three-block slot order.

## Accepted-time history

| Accepted time (s) | Increment | Iters | Pair report starts | Complete triplets | Global CDIS rows/CNUM |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.001 | 1 | 26 | 105/105 | 35/35 | 110318/110318 |
| 0.002 | 2 | 12 | 105/105 | 35/35 | 109370/109370 |
| 0.003 | 3 | 6 | 105/105 | 35/35 | 109242/109242 |
| 0.004 | 4 | 4 | 105/105 | 35/35 | 109023/109023 |
| 0.005 | 5 | 2 | 105/105 | 35/35 | 108909/108909 |
| 0.006 | 6 | 4 | 105/105 | 35/35 | 108862/108862 |
| 0.007 | 7 | 3 | 105/105 | 35/35 | 108926/108926 |
| 0.008 | 8 | 3 | 105/105 | 35/35 | 108963/108963 |
| 0.009 | 9 | 4 | 105/105 | 35/35 | 108985/108985 |
| 0.010 | 10 | 4 | 105/105 | 35/35 | 109023/109023 |
| 0.011 | 11 | 5 | 105/105 | 35/35 | 109002/109002 |
| 0.012 | 12 | 5 | 105/105 | 35/35 | 108871/108871 |
| 0.013 | 13 | 5 | 105/105 | 35/35 | 108837/108837 |
| 0.014 | 14 | 6 | 105/105 | 35/35 | 108997/108997 |
| 0.015 | 15 | 6 | 105/105 | 35/35 | 109168/109168 |
| 0.016 | 16 | 6 | 105/105 | 35/35 | 109184/109184 |
| 0.017 | 17 | 7 | 102/105 | 33/35 | 108953/108953 |

Strict surface/order check: `1782/1782` parsed report headers have matching WJCP slave/master IDs; `0` strict deck-order mismatches. A focused negative test confirms that a `WJCP_001_S`/`WJCP_002_M` header is rejected by the same slot gate; its matching-master control passes. The last incomplete time group is still counted as partial output, not completed coverage. The test is in [`test_terminal_contact_order.py`](test_terminal_contact_order.py).

## First reported bore contact

First positive-area CF report among the 16 manifest bore pairs: No positive area was reported for any bore pair in the accepted output history.

First positive-area bore CF report with a finite nonzero CF vector: No positive-area bore CF report with a finite nonzero CF vector was found in accepted output.

These are explicit per-pair report observations. CFN is retained as a duplicate normal-force report and is never added to CF; CFS remains separate. A zero or missing force is not treated as proof of an open gap, and q was not used to infer contact or seating. The 16 bore histories and every accepted-time report status are in the CSV files.

## Last accepted 35-pair coverage

At `t=0.017 s`, there are `102/105` report starts, `33/35` complete triplets, `1` partial pair(s), and `1` absent pair(s). Final report sequence matches the deck: `True`.

At WJCP_034, the CFS block is present but ends after the `total surface force` label; its numeric force row is missing. WJCP_035 has no final-time report block. The missing CFS vector and WJCP_035 force fields remain unavailable, not zero.

| # | Manifest pair | Category | Reports | Field status by request | Complete triplet |
| ---: | --- | --- | ---: | --- | --- |
| 01 | `bottom_center_right_cleat_to_base_rail_bottom_right::wood_to_wood` | wood_wood_finite_interface | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 02 | `bottom_center_right_cleat_to_base_principal_center_right::wood_to_wood` | wood_wood_finite_interface | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 03 | `base_rail_bottom_right_to_base_principal_center_right::wood_to_wood` | wood_wood_finite_interface | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 04 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_head` | head_washer_to_head | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 05 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_first_receiver` | head_washer_to_first_receiver | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 06 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_nut` | nut_washer_to_nut | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 07 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_last_receiver` | nut_washer_to_last_receiver | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 08 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_head` | head_washer_to_head | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 09 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_first_receiver` | head_washer_to_first_receiver | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 10 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_nut` | nut_washer_to_nut | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 11 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_last_receiver` | nut_washer_to_last_receiver | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 12 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_head` | head_washer_to_head | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 13 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_first_receiver` | head_washer_to_first_receiver | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 14 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_nut` | nut_washer_to_nut | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 15 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_last_receiver` | nut_washer_to_last_receiver | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 16 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_head` | head_washer_to_head | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 17 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_first_receiver` | head_washer_to_first_receiver | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 18 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_nut` | nut_washer_to_nut | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 19 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_last_receiver` | nut_washer_to_last_receiver | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | open_bolt_shank_to_wood_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | open_bolt_shank_to_wood_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | open_bolt_shank_to_wood_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | open_bolt_shank_to_wood_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | open_bolt_shank_to_wood_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | open_bolt_shank_to_wood_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | open_bolt_shank_to_wood_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | open_bolt_shank_to_wood_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | open_bolt_shank_to_washer_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | open_bolt_shank_to_washer_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | open_bolt_shank_to_washer_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | open_bolt_shank_to_washer_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | open_bolt_shank_to_washer_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | open_bolt_shank_to_washer_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=complete_fields | yes |
| 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | open_bolt_shank_to_washer_bore | 3/3 | CF=complete_fields, CFN=complete_fields, CFS=partial_or_malformed_record | no |
| 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | open_bolt_shank_to_washer_bore | 0/3 | CF=missing, CFN=missing, CFS=missing | no |

A report with NaN centroid or normal fields remains present-but-undefined if its report rows are present. A truncated report or absent pair is recorded as partial/missing; it is never replaced with zero. Global CDIS/CNUM completeness is counted separately and does not repair pair-specific coverage.

## Limits

The source process stopped at its runtime bound before the requested 0.025 s endpoint. These histories do not establish time accuracy, quasistatic response, physical bore seating, contact capacity, joint acceptance, or performance between the recorded accepted states. `pilot.dat` is read only from the completed terminal run; no native solve, CAD, or Git operation was performed.

Machine-readable provenance and field states are in [`contact-history-audit.json`](contact-history-audit.json).
