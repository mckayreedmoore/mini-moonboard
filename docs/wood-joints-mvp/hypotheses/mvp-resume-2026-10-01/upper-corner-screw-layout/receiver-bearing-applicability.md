# Receiver bearing applicability for the frozen N15 continuation

## Decision

The 108 active receiver/case states left null in
[kicker-path-completion](kicker-path-completion.md) have a matching **geometric
bearing law**: 94 are parallel to grain and 14 are oblique. Of these, **93
have a supported conditional DF-L No. 2 stock/reference binding**: 79 parallel
and 14 oblique. The other **15 parallel states** occur on four section-ripped
blocks whose frozen material record supplies only a hypothetical final-section
DF-L No. 2, C_F=1 arithmetic reference. Their geometry admits parallel bearing,
but their matching NDS stock/grade/size reference remains unsupported. A finite
study comparison for those 15 must retain that label and a null supported
resistance result.

The parent has completed the scalar addendum for these same 108 target states,
as recorded below. The worker has only joined saved results and annotated this
document; no stress, capacity, utilization or mechanical result was recalculated.
All 108 original N15 result fields remain null in the original frozen leaf.
The separate completed continuation is the parent-only scalar addendum in
[receiver-bearing-completion.py](receiver-bearing-completion.py), using the
saved compression and active net area. Its API is below; neither entry point
has been executed by the worker.

The input is the unadopted 108-axis proposal with its actual 66 panel/kicker
axes and six saved cases. The reviewed 104-axis model remains separate. Loads
remain 250 lb × 2, signed 300 N, the original 100 mm lever, saved gravity and
25 kg equipment allowance. Candidate adoption, acceptance and release flags
retain their existing values.

## Completed parent scalar addendum

The parent ran
[`rawlocal/receiver-bearing-completion/attempt01/receiver-bearing-addendum.json`](rawlocal/receiver-bearing-completion/attempt01/receiver-bearing-addendum.json)
with producer SHA-256
`767da34553071c946b9f0ea88047bb1dedf83b7034cdb47e4945382cb50de8b4`.
Exit was 0 and status is
`COMPLETE_SCALAR_BEARING_ADDENDUM_WITH_EXPLICIT_LIMITS`. Its
[receipt](rawlocal/receiver-bearing-completion/attempt01/receipt.json) binds
117 source pins and three output artifacts. The worker's read-only artifact
hash join matches all three receipt entries. These are the same 108 unique
target states and 30 receiver/interface identities; each has the two existing
C_D scenarios. No new state, load, connection or geometry is introduced.

### Scenario and null accounting

| Saved scenario | Conditional parallel finite / exceeding 1 | Conditional Hankinson finite / exceeding 1 | Study-only finite hypothetical / exceeding 1 | Study-only supported ratios null |
| --- | --- | --- | --- | --- |
| `cd1`, C_D=1 | 79 / 0 | 14 / 0 | 15 / 0 | 15 |
| `cd1_25`, C_D=1.25 | 79 / 0 | 14 / 0 | 15 / 0 | 15 |

Each scenario has 93 finite conditional mean-reference comparisons and 15
null supported-resistance comparisons. Across the two scenarios there are 186
finite conditional entries and 30 supported null entries, on the same 108
states. All 15 study states also retain null `supported_ratio_exceeds_one`;
their finite hypothetical ratios are separately labeled and do not supply a
supported resistance. Every target's `complete_connection_resistance` remains
null in both scenarios.

### Saved same-state peaks

The following numbers are copied from the actual addendum's
`same_state_extrema`. Each row retains its complete saved witness; values from
different states are not combined.

| Scenario / class | Saved mean stress, MPa | Saved bearing reference, MPa | Saved comparison ratio | Witness: case; receiver / other body; patch; canonical rows |
| --- | ---: | ---: | ---: | --- |
| `cd1` / P | 0.9287507877546675 | 10.238714580355017 | 0.0907097058391156 | `k12-rear`; `base_rail_top` / `base_side_right`; 81; 900–903 |
| `cd1_25` / P | 0.9287507877546675 | 12.798393225443771 | 0.07256776467129247 | `k12-rear`; `base_rail_top` / `base_side_right`; 81; 900–903 |
| `cd1` / O | 0.19898529155501835 | 6.527585845726804 | 0.030483749468462582 | `a1-rear`; `base_side_left` / `base_header`; 14; 388–391 |
| `cd1_25` / O | 0.19898529155501835 | 7.055512579064372 | 0.028202811535686566 | `a1-rear`; `base_side_left` / `base_header`; 14; 388–391 |
| `cd1` / S, hypothetical only | 0.01207832566265329 | 9.307922345777287 | 0.0012976392812444175 | `k12-right`; `center_principal_cleat_left` / `base_header`; 18; 404–407 |
| `cd1_25` / S, hypothetical only | 0.01207832566265329 | 11.634902932221609 | 0.001038111424995534 | `k12-right`; `center_principal_cleat_left` / `base_header`; 18; 404–407 |

P is the conditional parallel class, O the conditional Hankinson class, and S
the unsupported material-binding class. The S ratio column is
`hypothetical_reference_ratio`; its supported ratio remains null. The exact
108-state census and four affected S receivers remain listed below.

### Preserved 0.75 F_c* plate obligation

No conditional parallel state triggers the plate obligation in either saved
scenario: all 79 per scenario have
`BELOW_OR_AT_PLATE_TRIGGER_IN_SAVED_MEAN`, with zero
`PLATE_REQUIRED_NOT_ESTABLISHED` dispositions. The largest saved plate-trigger
ratios are **0.12094627445215411** at C_D=1 and **0.0967570195617233** at
C_D=1.25, both at the P witness above (`k12-rear`, top rail/right side, patch
81, rows 900–903). These are comparisons against 0.75 F_c*, separate from the
strength ratios in the peak table.

The 15 S states per scenario have no hypothetical plate trigger; all retain
`HYPOTHETICAL_BELOW_OR_AT_PLATE_TRIGGER`. Their saved hypothetical maxima are
0.0017301857083258897 and 0.0013841485666607118, respectively, at the S witness
above. This does not resolve their missing supported material references.
All 14 O states retain null plate-trigger ratios and predicates with
`NOT_PARALLEL_BEARING`; those nulls are method applicability, not passes.

No plate is established or added. Exact trimmed face edges, both pair normals,
grain records, canonical row directions and counterface references remain in
the saved interface records. The existing 813 perpendicular means and 219
no-active-area N15 states retain their original scope. The 93 conditional
finite comparisons below one complete this bounded mean-bearing comparison;
they do not establish complete receiver/member/joint resistance, physical peak
pressure, accepted stock or a fabrication/climbing release.

### Actual leaf hashes and consumed method source

| Exact path relative to this directory | SHA-256 |
| --- | --- |
| `rawlocal/receiver-bearing-completion/attempt01/receipt.json` | `2d99bc2f6311e2eb3b8015573b93a0e68952a14d4fe3432d78c1ba6700ccd82a` |
| `rawlocal/receiver-bearing-completion/attempt01/receiver-bearing-addendum.json` | `33b908fffb3222f6f7c3ed47e7383627d0a03fe337ff6a26026758959ff90292` |
| `rawlocal/receiver-bearing-completion/attempt01/producer.py.snapshot` | `767da34553071c946b9f0ea88047bb1dedf83b7034cdb47e4945382cb50de8b4` |
| `rawlocal/receiver-bearing-completion/attempt01/.gitignore` | `240a3e0d37d2e86b614063f5347eb02d4f99ca6c254de6b82871ff8d95532a7d` |

The run consumed this document's pre-annotation method bytes at SHA-256
`7ef58395f7eb5c4e14146a27ea5bfad68e02bee5a8aa918f8fbf5ffc7dc0ca65`.
Before annotation those exact bytes were preserved in the owned ignored
`rawlocal/kicker-path-completion/source-snapshots/receiver-bearing-applicability-7ef58395f7eb5c4e14146a27ea5bfad68e02bee5a8aa918f8fbf5ffc7dc0ca65.md`.
The producer's literal method-document pin remains unchanged. Reproduction
uses those consumed bytes at the original source path; this annotated document
is not substituted into the actual receipt or producer pin. No actual leaf,
producer, N15 packet or source authority is rewritten. The returned current
Markdown hash freezes this result annotation separately.

## NDS basis and exact geometry

NDS 2024 §3.10.1.1 uses net bearing area and F_c*, excluding C_P. Section
3.10.1.3 adds a load-distributing plate/material requirement above 0.75 F_c*.
Section 3.10.1.2 addresses accurately cut, laterally supported end-to-end
bearing. All 94 saved parallel states here have a perpendicular-grain timber
counterface, so none is an end-to-end grain pair. The §3.10.1.3 threshold still
belongs in their comparison. No bearing-face plate is established by these
wood-face records; adjacent bolt washers do not establish that role.
[AWC NDS 2024 Chapter 3, printed p.26 / PDF p.12](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).

Section 3.10.3, Eq. 3.10-1, supplies

```text
F_theta' = Fc_star * Fc_perp' /
           (Fc_star * sin(theta)^2 + Fc_perp' * cos(theta)^2).
```

Appendix J.2–J.3 makes the surface-normal force component the relevant direction
when the complete resultant is oblique to the surface. These saved unilateral
contact rows carry normal compression, so their face normals and each
receiver's longitudinal grain give the appropriate angle. Tangential bolt
action and free couples retain their existing connection/member accounting.
[AWC NDS 2024 Chapter 3 §3.10.3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
[AWC NDS 2024 Appendix J, printed p.187 / PDF p.22](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf).

The following evidence supplies the geometric match:

- `contact-bearing.json` supplies the saved receiver, other body, case,
  `face_identity`, canonical numeric `raw_rows`, positive compression,
  positive active net area and `normal_grain_dot_abs` for every target state.
- Each target `face_identity` is the zero-based index into the frozen
  `contact-geometry.json/contact_patches` list. Its exact two member IDs,
  `source_face_indices`, opposed normals and bounded patch edges match the
  receiver's recorded `profile_planes` facet in frozen `geometry.json`.
  These are planar trimmed face records, including circular hole boundaries
  on the cleat/block faces. No AABB overlap, whole face area or adjacency is
  used to establish bearing.
- The parallel end planes have normal ±X for header/rails, ±Z for
  posts/cleats/spine seats, or the inclined longitudinal normal for the two
  principal/top-rail interfaces. Their saved absolute normal/grain dot is
  exactly `1.0` in N15. Every counterface's saved dot is `0.0`.
- The four oblique receiver interfaces are the bottom horizontal cuts of the
  two center principals and two side members, at Z=277 mm, against the
  header's top face. Receiver normals are −Z; grain is the recorded inclined
  Y/Z direction. N15 saves `normal_grain_dot_abs=0.7660444429154699` for all
  14 states. Their counterface dot is `0.0`. The proposed postprocessor can
  use that saved cosine directly, with no new angle measurement or geometry.
- The frozen strength material map and frame material orientations use the
  same longitudinal directions as the geometric recipes. The inclined
  geometric axis and material L records differ only in their saved decimal
  representation; this document does not recompute an angle. R/T alternatives
  do not change this longitudinal-grain bearing law.

The two modified spine seats are included in the 79 conditional parallel
states. Each is the preserved bottom facet at Z=139.7 mm on its existing floor
runner. The proposal adds transverse holes at grain stations 100 and 250 mm;
the frozen geometry manifest and contact recipes retain the end seat and
standard 2×6 stock binding. These two local bearing applications do not
transfer the 42-member worksheet's whole-member results to changed spines.

## Exact target state census

The key is `(case_id, receiver, other_body, face_identity, raw_rows)`. Each
receiver side is checked once; the opposite body's existing perpendicular
comparison is a second material check of the same force, not another applied
load. Case abbreviations: **AR**=`a12-rear`, **AF**=`a12-forward`,
**AL**=`a12-left`, **KR**=`k12-right`, **KB**=`k12-rear`, **A1**=`a1-rear`;
**all** means those six cases in that order.

**P** means conditional standard-stock parallel reference available;
**O** means conditional standard-stock Hankinson reference available;
**S** means geometric parallel application, study-only material reference and
unsupported NDS stock/reference binding. A receiver facet number below means
`receiver/facetNNN` in the frozen plane recipe. Row ranges are inclusive.

| Receiver | Other body | Patch / receiver facet | Raw rows | Active cases | Count | Decision |
| --- | --- | --- | --- | --- | ---: | --- |
| `base_header` | `knee_outer_left_spine` | 23 / 001 | 468–471 | KR, A1 | 2 | P |
| `base_header` | `knee_outer_right_spine` | 25 / 015 | 476–479 | AF, AL | 2 | P |
| `base_post_center_left` | `base_header` | 8 / 003 | 364–367 | AF, KR, KB, A1 | 4 | P |
| `base_post_center_right` | `base_header` | 9 / 003 | 368–371 | AR, AL, A1 | 3 | P |
| `base_post_outer_left` | `base_header` | 10 / 013 | 372–375 | KR, KB, A1 | 3 | P |
| `base_post_outer_right` | `base_header` | 11 / 013 | 376–379 | AR, AF, AL, A1 | 4 | P |
| `base_principal_center_left` | `base_header` | 12 / 017 | 380–383 | AR, A1 | 2 | O |
| `base_principal_center_left` | `base_rail_top` | 37 / 016 | 532–535 | A1 | 1 | P |
| `base_principal_center_right` | `base_header` | 13 / 017 | 384–387 | KB, A1 | 2 | O |
| `base_principal_center_right` | `base_rail_top` | 48 / 016 | 618–621 | A1 | 1 | P |
| `base_rail_bottom_left` | `base_principal_center_left` | 34 / 018 | 520–523 | A1 | 1 | P |
| `base_rail_bottom_left` | `base_side_left` | 56 / 002 | 692–695 | all | 6 | P |
| `base_rail_bottom_right` | `base_side_right` | 60 / 012 | 726–729 | all | 6 | P |
| `base_rail_service_lower_left` | `base_principal_center_left` | 35 / 018 | 524–527 | AR, AL, KB, A1 | 4 | P |
| `base_rail_service_lower_left` | `base_side_left` | 64 / 002 | 760–763 | A1 | 1 | P |
| `base_rail_service_lower_right` | `base_principal_center_right` | 46 / 001 | 610–613 | AR, AF, KR, KB, A1 | 5 | P |
| `base_rail_service_upper_left` | `base_principal_center_left` | 36 / 018 | 528–531 | all | 6 | P |
| `base_rail_service_upper_right` | `base_principal_center_right` | 47 / 001 | 614–617 | all | 6 | P |
| `base_rail_top` | `base_side_left` | 80 / 002 | 896–899 | all | 6 | P |
| `base_rail_top` | `base_side_right` | 81 / 021 | 900–903 | all | 6 | P |
| `base_side_left` | `base_header` | 14 / 035 | 388–391 | AR, AL, KB, A1 | 4 | O |
| `base_side_right` | `base_header` | 15 / 035 | 392–395 | all | 6 | O |
| `center_post_cleat_left` | `base_header` | 16 / 003 | 396–399 | AF, AL, KR, KB, A1 | 5 | P |
| `center_post_cleat_right` | `base_header` | 17 / 003 | 400–403 | AR, AF, AL, KR, A1 | 5 | P |
| `center_principal_cleat_left` | `base_header` | 18 / 002 | 404–407 | all | 6 | S |
| `center_principal_cleat_right` | `base_header` | 19 / 005 | 408–411 | all | 6 | S |
| `knee_outer_left_inner_frame_block` | `base_header` | 22 / 004 | 464–467 | KR | 1 | S |
| `knee_outer_left_spine` | `base_floor_left` | 2 / 004 | 340–343 | A1 | 1 | P |
| `knee_outer_right_inner_frame_block` | `base_header` | 24 / 004 | 472–475 | AF, AL | 2 | S |
| `knee_outer_right_spine` | `base_floor_right` | 6 / 004 | 356–359 | A1 | 1 | P |

The census has 30 receiver/interface identities and 108 receiver/case states:
P=79, O=14, S=15. No target is a plywood receiver or a dowel-bearing surface.

## Conditional reference bindings and unsupported remainder

The frozen material inputs use the DF-L No. 2 Table 4A base row:
F_c=1350 psi and F_c⊥=625 psi. Table 4A's recorded compression size factors
are 1.1 for standard 2×6/4×6 and 1.15 for standard 4×4. The four section-ripped
blocks explicitly lack a supported final nominal stock/grade/size binding;
their existing C_F=1 entry is study-only.
[AWC NDS 2024 Supplement Table 4A, printed pp.32 and 34 / PDF pp.2 and 4](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf).

The following numbers are copied from the frozen saved member reference join;
they are not recalculated in this continuation:

| Reference scenario | F_c* at C_D=1, MPa | F_c* at C_D=1.25, MPa | F_c⊥', MPa | Use |
| --- | ---: | ---: | ---: | --- |
| Standard 2×6 / 4×6 | 10.238714580355017 | 12.798393225443771 | 4.309223308230226 | P receivers except the two center-post cleats; all O receivers; exact standard 2×6 material-class route for the two modified spine seats |
| Standard 4×4 | 10.704110697643879 | 13.380138372054848 | 4.309223308230226 | Both center-post cleats, 10 P states |
| Final-section DF-L No. 2, C_F=1 study | 9.307922345777287 | 11.634902932221609 | 4.309223308230226 | Four section-ripped blocks, 15 S states; no supported resistance transfer |

F_c⊥' retains C_b=1 and its existing dry-service/deformation-limit reference.
C_D does not multiply that reference. The C_D=1.25 column retains the saved
seven cumulative full-peak days hypothesis; it is not a new duration adoption.
[AWC NDS 2024 Chapter 2 §2.3.2 and Table 2.3.2 footnote 1](https://web-media.awc.org/wp-content/uploads/2021/12/17210153/AWC_NDS2024_20231129_AWCWebsite_Chapter2.pdf).

The 15 unsupported matching-reference states are exactly the S rows above:
12 on the two center-principal cleats and three on the two inner-frame blocks.
Their source records identify final sections 83.9×139.7 mm and 88.9×133.35 mm,
respectively, and prohibit inheritance of the pre-rip 4×6 grade. Giving them a
standard 4×6 size factor or calling their hypothetical final-grade comparison
a supported NDS resistance would change the frozen material basis. Their
existing arithmetic hypothesis remains available as a labeled diagnostic.

No other target lacks a matching bearing law or conditional stock reference.
The original exclusion of two changed spines from the 42-member join concerns
that member worksheet's changed-hole scope. Frozen `material-inputs.json`
already names both spines as standard 2×6 DF-L No. 2 with C_F,c=1.1, so the
local end-seat reference has a current conditional material route without a
whole-member pass transfer.

## Minimal parent-only postprocessor

The new [producer](receiver-bearing-completion.py) has inert import, stdlib-only
`prepare(output)` and parent-only `build(output)`. Both require a fresh immediate
child of `rawlocal/receiver-bearing-completion/`. Existing output and symlink
routes are rejected. No output directory has been created by this worker.

`prepare(output)` authenticates this document, all 94 frozen N15 receipt source
pins, all 13 N15 output artifacts, and the exact consumed geometry/material/NDS
pins below, before joining mechanical records or creating output. It checks the
1,140 saved unique keys, 108 target nulls, 79/14/15 applicability census and 30
interface identities. Each interface retains its complete saved trimmed contact
patch, both face normals, receiver plane recipe, both geometric grains,
receiver material grain and elastic orientation, and the signed ownership of
its four canonical contact rows. The opposite side's saved perpendicular check
references the same rows; no load is counted again.

Prepared scalar results remain null. Sources are authenticated again before
publication, before the new receipt and after it. The receipt hashes every
output artifact, and those artifact hashes are rechecked before return. The
producer imports no existing mechanical producer and calls no mechanical
function during preparation.

`build(output)` uses the same authentication and evaluates only, for each
existing state and the two existing C_D scenarios:

```text
mean_stress = saved_compression_n / saved_active_area_mm2
c = saved_normal_grain_dot_abs
parallel_reference = saved_receiver_Fc_star
oblique_reference = Fc_star * Fc_perp' /
                    (Fc_star * (1 - c*c) + Fc_perp' * c*c)
mean_reference_ratio = mean_stress / applicable_reference
```

The two spine seats bind through their frozen standard 2×6 material record and
the already saved standard-class reference values from the header's reference
entry. Only those material values are reused; no header or historical spine
result is transferred. The producer checks each frozen compression size factor
and both saved F_c* values against the reference table above. It does not
multiply by C_D again or use a column-stability-adjusted F_c value. F_c⊥'
retains its saved value for both scenarios, with C_b=1.

Each state retains its raw key, canonical rows, original N15 state and original
counterface state. P/O scenarios receive `supported_resistance_ratio` and
`supported_ratio_exceeds_one`. S scenarios retain
`supported_resistance_ratio: null` and `supported_ratio_exceeds_one: null`,
while separate `hypothetical_reference_ratio` and
`hypothetical_ratio_exceeds_one` expose the explicitly hypothetical C_F=1
comparison. Prepared values are null in both categories.

For every parallel state it records the §3.10.1.3 predicate
`mean_stress > 0.75 * Fc_star`, separately from `mean_reference_ratio > 1`.
An exceeded plate threshold cannot qualify the existing direct wood-face
configuration on the supplied record. The producer reports that
disposition and leave it visible; it cannot invent a plate or change hardware.
The oblique reference uses Eq. 3.10-1 with its specified F_c* input and keeps
that parallel-only threshold separate.

Outputs are `receiver-bearing-addendum.json` containing the 108 identified
states, their two scenario entries and separate P/O/S same-state extrema, plus
`receipt.json`, `producer.py.snapshot` and `.gitignore`. The receipt binds the
three non-receipt artifacts. Existing 813
perpendicular means and 219 no-active-area states keep their frozen results;
this addendum does not replace the old `contact-bearing.json`. No no-active
state, applicability census or null is a pass.

The existing frozen `fea/reinforced_timber_resistance.py::bearing_check`
contains the Hankinson algebra and C_b=1 convention. Its depth-based reference
selector does not supply all receiver-specific bindings or the parallel plate
predicate. The small addendum uses the saved per-receiver/class
references with that source-backed algebra, without changing or invoking the
historical helper.

### Parent invocation and status

Importing the producer performs no reads or writes. The CLI defaults to
`prepare`; `--build` explicitly selects parent-only scalar arithmetic. The
callable APIs return the output path, status, counts, producer hash and receipt
hash. Both calls need their own fresh output child.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/receiver-bearing-completion.py \
  --build \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/receiver-bearing-completion/parent-attempt01
```

Preparation reports `PREPARED_NOT_NUMERICALLY_RUN`; the scalar build reports
`COMPLETE_SCALAR_BEARING_ADDENDUM_WITH_EXPLICIT_LIMITS`. Neither status is a
structural pass. Plate-trigger exceedance remains
`PLATE_REQUIRED_NOT_ESTABLISHED` for a conditionally bound parallel state;
study-only trigger dispositions carry the `HYPOTHETICAL_` prefix. No acceptance
or release flag becomes true. The parent has completed `attempt01` as recorded
above. AST parsing was the only worker code check; neither entry point was
executed by the worker, and no rerun accompanies this annotation.

## Remaining genuine limits

The actual parent-run scalar means complete this bounded comparison for the 93
conditionally bound states and identify the 15 study-only results. They do not
establish a maximum physical contact pressure, local bore/ligament crushing or
splitting, complete receiver/member/joint resistance, shared timber poses or
whole-frame stability. Saved contact-cell placement and active-area assumptions
remain those of N15. A force/stress exceedance and an unsupported material
binding are different outcomes and must remain distinguishable.

N14 retains its per-screw head/withdrawal/lateral/steel and panel resistance
work. This continuation introduces no panel seam or continuous-strip support
criterion. The saved two edge probes remain boundary observations, with inner
post gaps 141.0725 mm left and 142.8875 mm right; they are neither full-strip
coverage nor a failure. Whole kerf-right kickers, alternate-cut limitations,
shop authority and the existing complete-path resistance nulls remain recorded
in the frozen N15 leaf. No additional load, geometry, stiffness, CAD, native
solve, software test, numerical worker run or review loop belongs to this task.

## Frozen source hashes

Paths below use `H=docs/wood-joints-mvp/hypotheses`,
`U=H/mvp-resume-2026-10-01/upper-corner-screw-layout`, and
`A=U/rawlocal/kicker-path-completion/parent-attempt01`. Hashes are SHA-256.
N15 has 94 authenticated source pins and 13 output artifacts, excluding its
receipt. This applicability record uses its existing receipt closure and the
following exact leaves/source records; it does not replace that closure.

| Exact leaf/source path | SHA-256 |
| --- | --- |
| `A/receipt.json` | `c589a8227000b2afe9ac536cbb7b99e4000f7b6e8b1024066a7e8b43109da402` |
| `A/report.json` | `ed568d974c649e052cdde4c604482c23e611900cea7314f26e9426192a1f03e8` |
| `A/contact-bearing.json` | `e6d71fdd4355c001a6dcf8ce6a5288e4b68c6bdfe4975cae46be13c37b322dea` |
| `A/signed-rows.jsonl` | `fdee4ed9332a3b70c0ea434790a23fb7b318516f27971356fafd07f7ca008878` |
| `A/saved-member-reference-join.json` | `35c303a0ae9cc88a1c6bf599ccb7da8f467ed6bfe40cf2651de5c3f420a371e1` |
| `U/kicker-path-completion.py` / `A/producer.py.snapshot` | `a1483fc420f463d0b5b692b231258c904f849b696851b7b3e227efa30b4256ff` |
| `U/kicker-path-completion.md` | `dd17ec349f511707ddfba9f01e955b8f2dd3ab59e6898cdb7276cffd9fdb6a31` |
| `U/rawlocal/knee-bridge-gravity/attempt01/model.json` | `c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1` |
| `U/rawlocal/knee-bridge-gravity/attempt01/model-inputs.json` | `b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99` |
| `U/rawlocal/knee-bridge-gravity/attempt01/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `U/rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| `U/rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| `U/rawlocal/knee-bridge-frame/attempt02/response/response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| `U/rawlocal/knee-bridge-geometry/attempt01/manifest.json` | `254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147` |
| `H/mvp-resume-2026-10-01/member-screen-attempt02/knee-bridge-gravity01/geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| `H/mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json` | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |
| `H/hardware-material-specification-2026-09-30/material-inputs.json` | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |
| `fea/reinforced_timber_resistance.py` | `d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc` |
| `U/rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf` | `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644` |
| `H/upper-block-strength-2026-10-01/source-cache/source-bounds.json` | `91c8c0c33cb7cc35dc31ba332778a80e1c5a972a6134e5e277a473a2adf719c9` |
| `H/upper-block-strength-2026-10-01/source-cache/appendix-2024-awc-20260911.pdf` | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |
| `H/upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf` | `6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100` |
| `H/hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf` | `1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b` |

The primary specification clauses were read from these existing cached AWC
PDF bytes; no secondary technical source is used. The continuation adds only
the new pure stdlib producer and this owned Markdown update. No new source
search, numerical producer, software test, CAD/frame/native operation or review
was executed by the worker. The actual parent leaf is retained above, and its
consumed pre-annotation method bytes remain recoverable. The producer retains
that original literal document hash. Returned current Markdown and unchanged
producer hashes freeze the result annotation and API separately; no numerical
execution, test, review or staging accompanies this annotation.
