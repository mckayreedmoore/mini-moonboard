# Ordinary transient contact iteration audit

**Scope: post-run generated contact-element topology only.** No solver execution or CAD work is performed by this parser. It refuses a live checkpoint and binds the parsed CEL bytes to the terminal execution record.

Checkpoint: `/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-transient-checkpoint-attempt01`. Execution status: `bounded_timeout`; solver return code: `137`. Parsed 1260890 CEL elements in 35 distinct step/increment/attempt/iteration groups. A `pilot.rout` file is present: false; no final converged response is available.

Contact-element pair identity is **not explicit** in the CEL set name. The set name records step, increment, attempt, and iteration. The parser assigns pair ID from ordered master/slave connectivity owners, using the pinned source's `nodefm` then `nodefs` output order, the frozen disjoint mesh node-owner table, and the original contact manifest. The static owner mapping has 35 ordered owner tuples for 35 pairs; mesh node ownership disjoint=true. Exactly mapped=1260890; ambiguous/unmapped=0.

CEL SHA-256: `24629b60d8800ee89d9c38edae382c4b69ad8ac59fe9fb2713075329631ae09d`; terminal output hash match=true. Contact manifest SHA-256: `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d`. Mesh JSON SHA-256: `1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07`. `gencontelem_f2f.f` SHA-256: `2dd474804f18ef01743a81101d6b852569bd567ef724ccf5c6043352fb482332`.

## CEL/CVG alignment and final block

There are 34 CVG rows and 35 CEL iteration groups. 34 CVG rows match CEL totals exactly; there are 0 count mismatches and 1 CEL-only group(s). The terminal CEL group parses structurally but lacks a matching CVG row; the launcher ended by bounded timeout, so this group may be pre-solve or partially appended and its completeness is unverified. It is excluded from confirmed switching rankings.

## CVG-aligned iteration endpoints

The first and last rows with exact CVG/CEL total agreement are step 1, increment 1, attempt 1, iterations 1 and 34. These are solver iteration diagnostics, not accepted time-step endpoints. The total generated contact-element count changes from 93540 to 40510 (-53030).

| Contact family | First aligned count | Last aligned count | Delta |
| --- | ---: | ---: | ---: |
| `bolt_seat` | 86084 | 35801 | -50283 |
| `open_bolt_shank_to_washer_bore` | 0 | 0 | +0 |
| `open_bolt_shank_to_wood_bore` | 0 | 0 | +0 |
| `wood_wood_finite_interface` | 7456 | 4709 | -2747 |

Owner-resolved first/last counts for all 35 original pairs are in [`endpoint-pair-counts.csv`](endpoint-pair-counts.csv). No owner-level run-to-run comparison is possible here because the older pilot did not emit `pilot.cel`.

## Pair switching rank

Ranked by cumulative appeared plus disappeared master/slave face-node signature multiplicity across adjacent CVG-aligned iterations within the same step, increment, and cutback attempt. Equal counts can still have turnover; regenerated element labels are not used as identities. Transitions involving unaligned CEL-only/mismatched groups are excluded from this ranking and remain in the CSV as unverified.

| Rank | Pair ID | Category | Master owner | Slave owner | Iteration transitions with change | Count-changing transitions | Signature turnover | Maximum absolute count change |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | `bottom_center_right_cleat_to_base_rail_bottom_right::wood_to_wood` | `wood_wood_finite_interface` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | 33 | 33 | 48031 | 7772 |
| 2 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_head` | `bolt_seat` | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | `M05_A01_HEAD_WASHER` | 33 | 33 | 42337 | 9317 |
| 3 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_nut` | `bolt_seat` | `M07_A01_NUT` | `M06_A01_NUT_WASHER` | 33 | 33 | 30826 | 3636 |
| 4 | `bottom_center_right_cleat_to_base_principal_center_right::wood_to_wood` | `wood_wood_finite_interface` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | 33 | 33 | 28310 | 2265 |
| 5 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_head` | `bolt_seat` | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | `M09_A02_HEAD_WASHER` | 33 | 33 | 27618 | 5888 |
| 6 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_last_receiver` | `bolt_seat` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `M02_A00_NUT_WASHER` | 33 | 33 | 27516 | 7369 |
| 7 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_first_receiver` | `bolt_seat` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M09_A02_HEAD_WASHER` | 33 | 33 | 24237 | 2469 |
| 8 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_first_receiver` | `bolt_seat` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M01_A00_HEAD_WASHER` | 33 | 33 | 20790 | 5235 |
| 9 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_head` | `bolt_seat` | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | `M01_A00_HEAD_WASHER` | 33 | 33 | 20758 | 4087 |
| 10 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_nut` | `bolt_seat` | `M03_A00_NUT` | `M02_A00_NUT_WASHER` | 33 | 33 | 18884 | 3587 |
| 11 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_last_receiver` | `bolt_seat` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `M10_A02_NUT_WASHER` | 33 | 33 | 18050 | 1768 |
| 12 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_head` | `bolt_seat` | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | `M13_A03_HEAD_WASHER` | 33 | 33 | 17965 | 3465 |
| 13 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_nut` | `bolt_seat` | `M15_A03_NUT` | `M14_A03_NUT_WASHER` | 33 | 33 | 17541 | 3197 |
| 14 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_first_receiver` | `bolt_seat` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M05_A01_HEAD_WASHER` | 33 | 33 | 17420 | 3057 |
| 15 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_nut` | `bolt_seat` | `M11_A02_NUT` | `M10_A02_NUT_WASHER` | 33 | 33 | 16761 | 3282 |
| 16 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_first_receiver` | `bolt_seat` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M13_A03_HEAD_WASHER` | 33 | 33 | 15310 | 1037 |
| 17 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_last_receiver` | `bolt_seat` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `M14_A03_NUT_WASHER` | 33 | 33 | 10229 | 1285 |
| 18 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_last_receiver` | `bolt_seat` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `M06_A01_NUT_WASHER` | 22 | 22 | 9201 | 1966 |
| 19 | `base_rail_bottom_right_to_base_principal_center_right::wood_to_wood` | `wood_wood_finite_interface` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `W01_BASE_RAIL_BOTTOM_RIGHT` | 33 | 33 | 4068 | 578 |

## Switching by contact family

| Family | Cumulative signature turnover |
| --- | ---: |
| `bolt_seat` | 335443 |
| `open_bolt_shank_to_washer_bore` | 0 |
| `open_bolt_shank_to_wood_bore` | 0 |
| `wood_wood_finite_interface` | 80409 |

## Files and limits

- Full per-iteration counts for all 35 manifest pairs, including zeros: [`iteration-pair-counts.csv`](iteration-pair-counts.csv).
- Adjacent-iteration count changes and retained/appeared/disappeared face signatures: [`pair-switching-transitions.csv`](pair-switching-transitions.csv).
- Owner-resolved first/last CVG-aligned comparison: [`endpoint-pair-counts.csv`](endpoint-pair-counts.csv).
- Full machine-readable grouped result and unresolved element samples: [`ordinary-contact-iteration-audit.json`](ordinary-contact-iteration-audit.json).

Counts/signature changes locate where generated contact-face associations changed. They do not establish physical chatter, normal pressure, contact force, residual or force convergence, a cause for the change, or structural acceptance. Rounded solver fields printed as `0.000000` are not treated as exact zeros. A missing/ambiguous owner mapping remains unresolved.

## Publication boundary

This published parser and its compact report files are not a runnable audit bundle. The source run's `pilot.cel` (195,027,021 bytes; SHA-256 `24629b60d8800ee89d9c38edae382c4b69ad8ac59fe9fb2713075329631ae09d`) and `pilot.cvg` (SHA-256 `69583079799715010e787eac1d3591107b55dc9bf2a5b8d122c854a98a5e38bc`) remain in the local checkpoint and are not committed. The transient directory's duplicate `mesh.inp` and `mesh.json` are also retained locally rather than shipped here. The tracked source mesh bundle is [`ordinary-patch-mesh-attempt02/complete-mesh-evidence.tar.gz`](../ordinary-patch-mesh-attempt02/complete-mesh-evidence.tar.gz), SHA-256 `3bd1b28bdbc9c109c6c96183a01e132cbd4c15f86867dca54e0c6ec3a309f4ac`; it contains `mesh/mesh.inp` (SHA-256 `117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803`) and `mesh/mesh.json` (SHA-256 `1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07`). Other raw solver `.frd` and `.dat` outputs remain local as well. Re-running the audit requires the original terminal files and complete frozen inputs; the published subset alone is not sufficient.
