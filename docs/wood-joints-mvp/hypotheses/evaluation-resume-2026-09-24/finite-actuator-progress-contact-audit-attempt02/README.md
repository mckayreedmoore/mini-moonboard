# Finite-actuator progress contact-output audit

This read-only audit is bound to an immutable finite-actuator output-prefix snapshot. It does not open the live source case. CEL and FRD were not read or hashed.

Snapshot manifest SHA-256: `e315511717f1da5ea94deeee6b582db0f454280487fc19a1ef6698177c3e2051`. Captured `pilot.dat` SHA-256: `cede252afb924f93857d26d6a7dd6d2496a210aa3346ab4a2d0d01212e06946b` (87192621 bytes). Captured `pilot.sta` SHA-256: `b6bd0ec4e4843d64b9ec308868aa1cb29edf4569fa474f3d68df7352c2f726ec`.

The snapshot contains 5 accepted state(s), from `t=0.0005 s` through `t=0.0025 s` (increment 1 through 5; all attempts are 1). It is a non-atomic output-prefix capture made while the source process was running, with mechanical acceptance false; it is not a terminal run or a joint acceptance result.

## Contact-source binding

The child snapshot binds its `contact-fragment.inc` to SHA-256 `e70fc43593e8e5a5b8e445f88122fb5e675dc788207be6e6031aae9c1f71cac5`, identical to the frozen K1e4 parent fragment. The child input-freeze lineage binds parent `pilot.inp` `48649259ba8441429a5dd094ae08487e3713d6b5b860ac39ca1acf71b837d963` and parent `contact-manifest.json` `e0a698bde664469f2d079ae5d6d98cd89a3b74af735752d3b9d5666d933beee7`; the parent manifest’s 35 ordered pair IDs/categories/owners match the upstream source manifest `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d`. The child snapshot does not copy a contact manifest, so the audit reads the parent manifest under that verified source-lineage pin. The upstream source freeze separately binds the earlier manifest/fragment `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d` / `35a4513b7877b04b0c2be053f3084d07178a148c606780d12d54388636574b24`.

Both child and K1e4 parent decks contain 35 ordered pair-specific `CF,CFN,CFS` requests plus one global `CDIS,CSTR,CELS,CNUM` request. All `521/521` observed DAT report headers have matching expected slave/master surface IDs and request slots.

## Captured output coverage

| Accepted time (s) | Increment | Iterations | Pair report headers | Complete triplets | Partial pairs | Missing pairs | Global CDIS rows | CNUM |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0005 | 1 | 22 | 105/105 | 35/35 | 0 | 0 | 97275 | 97275 |
| 0.001 | 2 | 7 | 105/105 | 35/35 | 0 | 0 | 105903 | 105903 |
| 0.0015 | 3 | 6 | 105/105 | 35/35 | 0 | 0 | 107910 | 107910 |
| 0.002 | 4 | 6 | 105/105 | 35/35 | 0 | 0 | 109055 | 109055 |
| 0.0025 | 5 | 8 | 101/105 | 33/35 | 1 | 1 | 109083 | 109083 |

At final accepted time `0.0025 s`, the global CDIS block is complete by its count: `109083` rows and `CNUM=109083`. Global CDIS/CNUM completeness is separate from per-pair CF/CFN/CFS coverage.

Complete 35-pair CF/CFN/CFS coverage is observed at accepted times: `0.0005 s`, `0.001 s`, `0.0015 s`, `0.002 s`. The consecutive full-coverage prefix ends at `0.002 s`. At the final accepted state, incomplete rows are: WJCP_034 partial (CF=complete_fields, CFN=partial_or_malformed_record, CFS=missing); WJCP_035 missing (CF=missing, CFN=missing, CFS=missing).

## Per-pair report coverage

At `t=0.0005 s`, the earlier first-knot snapshot had 101/105 pair headers: WJCP_034 had a complete CF, partial CFN with no numeric force row, and missing CFS; WJCP_035 was absent. This later progress snapshot contains all 105 headers and all 35 complete triplets at the same accepted time. The captured outputs differ; the cause is not established. Any pair still partial or missing at the final state remains unavailable, never zero-filled.

## Bore-pair CF reports at final accepted time

The manifest has 16 bore pairs. A complete CF report was observed for 15/16 bore pairs at the final accepted state, and for 16/16 distinct bore pairs across all accepted states. Positive-area events observed: none. Finite nonzero CF-vector events observed: none. These are report observations only; zero/missing force does not prove an open physical gap. No q-based seating inference is made.

| Time (s) | # | Bore pair | CF status | Area (mm²) | CF vector (N) |
| ---: | ---: | --- | --- | ---: | --- |
| 0.0025 | 20 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 21 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 22 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 23 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::base_rail_bottom_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 24 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 25 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 26 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::bottom_center_right_cleat::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 27 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::base_principal_center_right::shaft_to_wood_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 28 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 29 | `bottom_center/clip_horizontal_bottom_right_1/rail_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 30 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 31 | `bottom_center/clip_horizontal_bottom_right_1/rail_2::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 32 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 33 | `bottom_center/clip_horizontal_bottom_right_1/principal_1::shaft_to_nut_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 34 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_head_washer_bore` | complete_fields | 0 | (0, 0, 0) |
| 0.0025 | 35 | `bottom_center/clip_horizontal_bottom_right_1/principal_2::shaft_to_nut_washer_bore` | missing | not reported | not reported |

The full per-time 35-pair coverage and 16-pair bore history are in the CSV files. CFN is treated as a duplicate normal-force report and never added to CF; CFS remains separate.

This snapshot does not establish contact capacity, response between accepted states, mechanical acceptance, physical seating, or inspection. No native solve, CAD operation, or CEL scan was performed for this audit.

Machine-readable provenance and field states are in [`contact-audit.json`](contact-audit.json).
