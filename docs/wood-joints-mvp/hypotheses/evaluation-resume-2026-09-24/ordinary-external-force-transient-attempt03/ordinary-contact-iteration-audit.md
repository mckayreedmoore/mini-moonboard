# Ordinary transient contact iteration audit

**Scope: post-run generated contact-element topology only.** No solver execution or CAD work is performed by this parser. It refuses a live checkpoint and binds the parsed CEL bytes to the terminal execution record.

**Post-run interpretation correction, 2026-09-27:** this Markdown summary was
manually corrected after independent review. The parser and machine-readable
JSON are preserved unchanged. The correction clarifies that pair orientation
is coupon-supported rather than source-inspected, that the stop was a 600-second
accepted/monitor-progress watchdog, and that iteration snapshots must be grouped
by increment.

Checkpoint: `/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-external-force-transient-attempt03`. Execution status: `no_accepted_or_monitor_progress_timeout`; solver return code: `137`. Parsed 1228234 CEL elements in 41 distinct step/increment/attempt/iteration groups. A `pilot.rout` file is present: false; no final converged response is available.

Contact-element pair identity is **not explicit** in the CEL set name. The set name records step, increment, attempt, and iteration. Pair IDs are reconstructed from ordered master/slave connectivity owners, the frozen disjoint mesh node-owner table, and the original contact manifest. Master-first/slave-second orientation is supported by a pinned 2.23 C3D6 known-answer coupon. That coupon checks one small pair; the full-model mapping is coupon-mediated, not verified by inspecting the unavailable `gencontelem_f2f.f` source. The static owner mapping has 35 ordered owner tuples for 35 pairs; mesh node ownership disjoint=true. Exactly mapped=1228234; ambiguous/unmapped=0.

CEL SHA-256: `2af93f987776fd8072206b86aab17888732282ae39aacb28709e9f287d1fc81b`; terminal output hash match=true. Contact manifest SHA-256: `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d`. Mesh JSON SHA-256: `1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07`. The generator source file is unavailable for source-level inspection in this audit.

## CEL/CVG alignment and final block

There are 40 CVG rows and 41 CEL iteration groups. All 40 CVG rows match CEL totals exactly; there are 0 count mismatches and 1 CEL-only group. The unaligned group is step 1, increment 2, attempt 1, iteration 23, with 23,559 elements. Its completeness is unverified and it is excluded from confirmed switching rankings. The runner stopped the container after 600 seconds without a new accepted `.sta` state or complete monitor block. `.cvg` iteration records continued through iteration 22; this was not a claim of no solver iteration activity.

## CVG-aligned iteration snapshots by increment

Do not compare the first aligned row of increment 1 with the last aligned
row of increment 2 as one iteration trajectory. Within-increment snapshots
are:

| Step | Increment | Aligned iterations | First count | Last count |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 1 to 18 | 93540 | 18152 |
| 1 | 2 | 1 to 22 | 17732 | 24398 |

These are generated contact-element counts in solver iteration snapshots, not
physical contact forces or a capacity measure. Increment 2 did not converge.
The CEL-only iteration-23 group is not used in this table.

| Contact family | Increment 1, it1 | Increment 1, it18 | Increment 2, it1 | Increment 2, it22 |
| --- | ---: | ---: | ---: | ---: |
| `bolt_seat` | 86084 | 16943 | 16256 | 22529 |
| `open_bolt_shank_to_washer_bore` | 0 | 0 | 0 | 0 |
| `open_bolt_shank_to_wood_bore` | 0 | 0 | 0 | 0 |
| `wood_wood_finite_interface` | 7456 | 1209 | 1476 | 1869 |

The generated [`endpoint-pair-counts.csv`](endpoint-pair-counts.csv) contrasts
the first and last aligned rows across the whole run, so its endpoint pair
totals span increments 1 and 2. Use
[`iteration-pair-counts.csv`](iteration-pair-counts.csv) for increment-specific
snapshots. No owner-level run-to-run comparison is possible because the older
pilot did not emit `pilot.cel`.

## Pair switching rank

Ranked by cumulative appeared plus disappeared master/slave face-node signature multiplicity across adjacent CVG-aligned iterations within the same step, increment, and cutback attempt. Equal counts can still have turnover; regenerated element labels are not used as identities. Transitions involving unaligned CEL-only/mismatched groups are excluded from this ranking and remain in the CSV as unverified.

| Rank | Pair ID | Category | Master owner | Slave owner | Iteration transitions with change | Count-changing transitions | Signature turnover | Maximum absolute count change |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_head` | `bolt_seat` | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | `M01_A00_HEAD_WASHER` | 38 | 38 | 83865 | 13421 |
| 2 | `bottom_center_right_cleat_to_base_rail_bottom_right::wood_to_wood` | `wood_wood_finite_interface` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | 38 | 38 | 56523 | 14295 |
| 3 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_head` | `bolt_seat` | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | `M05_A01_HEAD_WASHER` | 38 | 38 | 54672 | 9099 |
| 4 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_nut` | `bolt_seat` | `M15_A03_NUT` | `M14_A03_NUT_WASHER` | 38 | 38 | 42083 | 5535 |
| 5 | `bottom_center_right_cleat_to_base_principal_center_right::wood_to_wood` | `wood_wood_finite_interface` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | 38 | 38 | 37607 | 2258 |
| 6 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_nut` | `bolt_seat` | `M11_A02_NUT` | `M10_A02_NUT_WASHER` | 38 | 38 | 36634 | 5541 |
| 7 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_head` | `bolt_seat` | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | `M09_A02_HEAD_WASHER` | 38 | 37 | 36452 | 3046 |
| 8 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_head` | `bolt_seat` | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | `M13_A03_HEAD_WASHER` | 38 | 38 | 35857 | 3350 |
| 9 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/head_washer_to_first_receiver` | `bolt_seat` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M09_A02_HEAD_WASHER` | 38 | 38 | 30943 | 1772 |
| 10 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_nut` | `bolt_seat` | `M07_A01_NUT` | `M06_A01_NUT_WASHER` | 38 | 37 | 30311 | 4495 |
| 11 | `bottom_center/clip_horizontal_bottom_right_1/principal_1/nut_washer_to_last_receiver` | `bolt_seat` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `M10_A02_NUT_WASHER` | 38 | 38 | 27651 | 1352 |
| 12 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_nut` | `bolt_seat` | `M03_A00_NUT` | `M02_A00_NUT_WASHER` | 38 | 37 | 26334 | 5154 |
| 13 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/head_washer_to_first_receiver` | `bolt_seat` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M13_A03_HEAD_WASHER` | 38 | 38 | 19040 | 1042 |
| 14 | `bottom_center/clip_horizontal_bottom_right_1/principal_2/nut_washer_to_last_receiver` | `bolt_seat` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `M14_A03_NUT_WASHER` | 38 | 38 | 19007 | 1406 |
| 15 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/head_washer_to_first_receiver` | `bolt_seat` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M01_A00_HEAD_WASHER` | 31 | 31 | 17337 | 4784 |
| 16 | `bottom_center/clip_horizontal_bottom_right_1/rail_1/nut_washer_to_last_receiver` | `bolt_seat` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `M02_A00_NUT_WASHER` | 24 | 24 | 16144 | 7351 |
| 17 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/nut_washer_to_last_receiver` | `bolt_seat` | `W01_BASE_RAIL_BOTTOM_RIGHT` | `M06_A01_NUT_WASHER` | 31 | 31 | 9687 | 4155 |
| 18 | `bottom_center/clip_horizontal_bottom_right_1/rail_2/head_washer_to_first_receiver` | `bolt_seat` | `W00_BOTTOM_CENTER_RIGHT_CLEAT` | `M05_A01_HEAD_WASHER` | 19 | 19 | 8321 | 2604 |
| 19 | `base_rail_bottom_right_to_base_principal_center_right::wood_to_wood` | `wood_wood_finite_interface` | `W02_BASE_PRINCIPAL_CENTER_RIGHT` | `W01_BASE_RAIL_BOTTOM_RIGHT` | 38 | 38 | 2798 | 419 |

## Switching by contact family

| Family | Cumulative signature turnover |
| --- | ---: |
| `bolt_seat` | 494338 |
| `open_bolt_shank_to_washer_bore` | 0 |
| `open_bolt_shank_to_wood_bore` | 0 |
| `wood_wood_finite_interface` | 96928 |

## Files and limits

- Full per-iteration counts for all 35 manifest pairs, including zeros: [`iteration-pair-counts.csv`](iteration-pair-counts.csv).
- Adjacent-iteration count changes and retained/appeared/disappeared face signatures: [`pair-switching-transitions.csv`](pair-switching-transitions.csv).
- Owner-resolved first/last CVG-aligned comparison: [`endpoint-pair-counts.csv`](endpoint-pair-counts.csv).
- Full machine-readable grouped result and unresolved element samples: [`ordinary-contact-iteration-audit.json`](ordinary-contact-iteration-audit.json).

Counts/signature changes locate where generated contact-face associations changed. They do not establish physical chatter, normal pressure, contact force, residual or force convergence, a cause for the change, or structural acceptance. Rounded solver fields printed as `0.000000` are not treated as exact zeros. A missing/ambiguous owner mapping remains unresolved.
