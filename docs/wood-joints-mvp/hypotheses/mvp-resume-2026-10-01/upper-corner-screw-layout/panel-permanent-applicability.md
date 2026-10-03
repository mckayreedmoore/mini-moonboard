# N14 permanent-only panel and screw comparison

## Disposition

**The applicable permanent-only numerical reference work is completed.**
The parent executed frozen
[panel-permanent-completion.py](panel-permanent-completion.py), producer
`196a3211`, at `rawlocal/panel-permanent-completion/attempt01`. The actual
status is `COMPLETED_PERMANENT_REFERENCE_COMPARISON_WITH_EXPLICIT_GAPS`.
The run returned 66 screw states, six panel balances, 22 panel/receiver
groups and 376 gross cut traces at CD0.9, with zero reference exceedances.
This completes the omitted permanent comparison under the existing
reference assumptions; actual product, local strength and frame acceptance
remain separate limits below.

Read-only result inspection matched the parent's exact receipt/summary
hashes, all eight declared output hashes and all 24 source pins. No producer
code or raw result changed. The parent run and this annotation performed
zero tests and zero frame/model/native/CAD solves; this worker only read
saved results and updated this note.

## Consumed permanent state

The source is [resolver attempt02](knee-bridge-permanent-resolve.md),
`rawlocal/knee-bridge-permanent-resolve/attempt02`. Its comparison reports
`COMPLETED_BOUNDED_NUMERICAL_COMPARISON_WITH_EXPLICIT_GAPS` and
post-execution source authentication true. The implemented consumer selects
only **`permanent-only_gap`, gap scale 1.0**.

| Saved item | Actual content or recorded audit |
| --- | --- |
| `response.npz` | Nominal raw connector forces `(1888,)`, lumped relative motions `(1612,)`, rigid coordinates `(300,)`, all float64; separate zero-gap arrays are also preserved |
| Nominal state status | `PASS_CONDITIONAL_WITH_BOUNDED_SEATING` |
| Nominal force/moment balance | 9.890754881780595e-12 N / 5.512063830432766e-9 Nmm |
| Nominal finite-law / circular-law error | 2.2147779077386076e-7 N / 4.905826855861051e-10 N |
| Nominal force-bearing rank / certificate nullity | 296 / 4; bounded certificate, strict stability and frame acceptance false |
| Gravity load selection | Unfactored column 0 of frozen `F`, `e`, `W`; multiplier 1.1110134616260479 once |
| Permanent mass basis | Modeled 225.19791414318078 kg plus proportional 25 kg equipment once |
| Live gravity / horizontal / moment scales | All 0.0 |

The shared gravity source provides `H (1888,1888)`, `D (1888,300)`,
`e (1888,12)`, `W (300,12)`, `F (37647,12)`, physical DOF labels and
the frozen sparse `B` connector-footprint projection. Its exact model,
material-axis bindings, rows and source connections are the same bytes
bound by N14 and the resolver. The saved permanent producer checked all
gravity columns against column 0 without modifying them.

The connection/ownership join identifies **66 screws**, each with two
signed lateral rows and one unilateral axial row: 12 per main panel and
nine per kicker, across six panels. The actual permanent component-force
entries and relative motions supplied the now-exported per-screw tension,
lateral norm, opening and CD0.9 ratios. No live-case maximum was scaled to
produce these permanent demands.

`member-actions.npz` and `body-balances.json` contain the existing
**44 timber bodies across two states**, with 88 balance records. They
contain no main-panel or kicker action arrays. Their wood comparisons
therefore did not already close the N14 panel gap. The completed consumer
recovered panel actions from the full saved raw forces and frozen `F/B/D`
using N14's existing procedure and unchanged load sharing.

## Executed attempt01 results

The saved catalog records `duration_factors=[0.9]` and `CD_applied_once=true`.
The same gravity/equipment state supplies every simultaneous force tuple.

### Gross plywood component comparisons

| Component | Group 1 maximum ratio | Group 4 reference sensitivity | Exceeded traces, each group |
| --- | ---: | ---: | ---: |
| Axial | 0.00390780494624901 | 0.006406237616801654 | 0 |
| Bending | 0.10393914944064542 | 0.15513305886663492 | 0 |
| Planar/rolling shear | 0.038441340425560556 | 0.038441340425560556 | 0 |

The axial witness is `main_lower_left`, cut axis 1, station 505.486808 mm,
gross width 1217.6125000000002 mm, signed mean −0.24637014467896162 N/mm.
The bending witness is `main_upper_left`, cut axis 0, station −400.938755 mm,
gross width 1219.2000000000005 mm, signed mean 15.777501667666494 Nmm/mm.
The rolling-shear witness is `main_upper_left`, cut axis 0, station
−495.938755 mm, the same gross width, signed mean 0.17671789514822245 N/mm.
Group 4 retains the saved Group 1 elastic response. All 376 cut records
remain gross diagnostics with local/net-section resistance null and
complete panel acceptance false.

### Named screw reference comparisons

Every named scenario below has **66 finite states, zero exceeded states
and zero geometry-unsupported states**. This is the recorded generic
reference geometry applicability, not delivered Hillman qualification.
All keys use `/CD0.9`; combined keys append `/lateral_0` or `/lateral_1`.

| Head scenario | Existing G / diameter / net thickness, mm | Maximum ratio |
| --- | --- | ---: |
| `head_0` | .42 / 7.5 / 14 | 0.5316840080174644 |
| `head_1` | .42 / 9.2202 / 17.25625 | 0.35087799383672985 |
| `head_2` | .50 / 9.2202 / 17.25625 | 0.24757951245119653 |
| `head_3` | .50 / 9.2202 / 18.25625 | 0.23401815606907003 |
| `head_4`, retailer nominal | .42 / 9.017 / 17.25625 | 0.35878510355699433 |
| `head_5`, retailer nominal | .50 / 9.017 / 17.25625 | 0.2531587690698151 |
| `head_6`, retailer nominal | .50 / 9.017 / 18.25625 | 0.23929180465654207 |

| Withdrawal scenario | Existing timber G / effective thread, mm | Withdrawal maximum | Combined maximum, `lateral_0` | Combined maximum, `lateral_1` |
| --- | --- | ---: | ---: | ---: |
| `withdrawal_0` | .45 / 30 | 0.25548298473481224 | 0.5322500609260699 | 0.4701108055479193 |
| `withdrawal_1` | .45 / 38.1 | 0.20116770451560012 | 0.49895330184466447 | 0.4368140464665139 |
| `withdrawal_2` | .45 / 42.333333333333336 | 0.18105093406404013 | 0.4866211688515514 | 0.4244819134734008 |
| `withdrawal_3` | .45 / 45.24375 | 0.1694043827499791 | 0.4794815129081701 | 0.4173422575300195 |
| `withdrawal_4` | .50 / 30 | 0.20694121763519793 | 0.502492624013688 | 0.4403533686355374 |
| `withdrawal_5` | .50 / 38.1 | 0.16294584065763612 | 0.47552224915774954 | 0.413382993779599 |
| `withdrawal_6` | .50 / 42.333333333333336 | 0.14665125659187253 | 0.465533221433328 | 0.4033939660551774 |
| `withdrawal_7` | .50 / 45.24375 | 0.13721755002748307 | 0.45975010011918915 | 0.3976108447410386 |
| `withdrawal_8` | .55 / 30 | 0.17102579969851064 | 0.4804754860458925 | 0.41833623066774195 |
| `withdrawal_9` | .55 / 38.1 | 0.1346659840145753 | 0.45818592004924924 | 0.39604666467109867 |
| `withdrawal_10` | .55 / 42.333333333333336 | 0.12119938561311777 | 0.44993052523567767 | 0.3877912698575271 |
| `withdrawal_11` | .55 / 45.24375 | 0.11340293390701077 | 0.4451510861330836 | 0.383011830754933 |

| Contacting-face lateral scenario | Existing plywood bearing reference, psi | Maximum ratio |
| --- | ---: | ---: |
| `lateral_0` | 3350 | 0.47826001573945026 |
| `lateral_1` | 4650 | 0.39914342429543725 |

Every head and withdrawal maximum occurs on
`round_panel_upper_right_service_1`, `main_upper_right` /
`base_rail_service_upper_right`: simultaneous tension 132.46524084443982 N,
lateral 23.698355888597337 N, positive opening 0.04924946429215135 mm.
Every lateral and combined maximum occurs on
`round_panel_upper_left_rim_4`, `main_upper_left` / `base_side_left`:
simultaneous tension 131.19323823726415 N and lateral 166.47135223696083 N.
No independent demand peaks were combined.

All 66 records have `loaded_opening_present=true`; none demonstrates
contacting-face lateral applicability. The lateral/combined values remain
the existing contacting-face diagnostics. All 66 steel ratios are null;
the run contains 66 finite steel-demand diagnostics and zero steel
resistance states. Saved hypothetical-root stress maxima are
11.315075156393075 MPa tension at the service-right witness,
14.21985005228382 MPa shear and 27.059125892100862 MPa required same-section
von Mises yield at the rim-left witness. These are required-strength
diagnostics without an assigned Hillman strength or bending/profile basis.

### Actual consumer audits and frozen outputs

| Consumer audit | Recorded residual | Unchanged gate |
| --- | ---: | ---: |
| Force balance | 9.890754881780595e-12 N | < 1e-5 N |
| Moment balance | 5.512063830432766e-9 Nmm | < 0.01 Nmm |
| Relative compatibility | 6.59596821606101e-10 mm | < 1e-6 mm |
| Screw law | 1.0714948928125523e-9 N | < 1e-4 N |

All detailed inherited basis, footprint, opposite-wrench/cut, geometry and
finite-value gates completed. The source nominal certificate remains
bounded rank 296/nullity four, with strict stability and frame acceptance
false. The receipt preserves all product/local-panel, full-frame/joint,
N14 acceptance and physical/fabrication release flags false.

| Permanent attempt01 output | SHA-256 |
| --- | --- |
| `receipt.json` | `7aa5d81d425ce46006943cb37cc44f78fea569b5c0cff454cd8eeb8dc75ea69d` |
| `summary.json` | `41744ca9174ca20cc6210299acbfda3cf0f304d414480f097926fe0ce2a833f4` |
| `sources.json` | `d696e0ad5bb12980b41c48b11913660509f3727cd52589f720fbf0465364e49f` |
| `screw-states.jsonl` | `9a05147bd3735faed48cacadb2ddc4fac0d66af17cda90073d47641ee5dbc515` |
| `screw-groups.jsonl` | `7275dce4b7ba90648e4108db632ddb5a1f83700751a86700193810f91654816e` |
| `panel-balances.jsonl` | `1f51f6938dbc2da89bf011f73d8963a84cf82a54ad3f027700c86c4b5685a73c` |
| `panel-cuts.jsonl` | `c9d82e16feb2e26724a53dacdd85f2ab32f1cd706e3d228ad82ab2315721d1af` |
| `producer.py.snapshot` | `196a3211ee78edc0a7b93b25559d5b62f0dc1a3812e417baa43d3b3554261190` |
| `.gitignore` | `cdbcae15105d6b781e620813c79c7e868740d4e9cc53ce6f5fcbbc12387adf4b` |

## Implemented consumer and frozen API

Owned producer: `panel-permanent-completion.py`. API:

```python
source_pins() -> dict[Path, str]
prepare(output=None) -> dict  # authenticate and join identities/headers only
run(output: Path) -> dict     # parent executes one saved-state postprocessor
```

`output` must be a fresh immediate child of
`rawlocal/panel-permanent-completion/`. `prepare()` returns its source manifest
without writing files; `prepare(output)` writes a preparation receipt in a
fresh child. `run(output)` performs the one numerical traversal. Preparation pins the
resolver comparison/response, common physical inputs, N14 producer and
unadjusted reference evidence, plus every pure helper actually consumed.
Execution authenticates these sources before and after, preserves a
producer snapshot and emits explicit STOP evidence on any failed gate after
output creation. Initial source authentication or fresh-path rejection creates
no output. Only Python 3.12.3 and NumPy 2.5.2 are needed for the scalar/array
consumer; no solver or new library behavior is required.

The CLI uses `--output PATH`; add `--prepare` for source-only preparation.
The parent owns serialization and the execution slot. There is exactly one
saved state and one fixed census traversal, with no solve, search, retries or
iteration budget. No in-process execution lock is claimed by this consumer.

The existing [duration applicability](panel-duration-applicability.md)
records the primary permanent CD0.90 basis. The live packet's CD1.25/1.60
comparisons supply no permanent strength increase.

The adapter reuses frozen N14 `definitions`, `nominal_receiver`, `screw_references`,
`panel_sections` and `comparison_row` functions, the existing pure `wrench`
helper, and existing plywood/combined screw reference helpers. Authenticated
pure definitions are compiled into a private namespace. The same frozen
`assess()` body supplies recovery and audits after four exact expression
adaptations: gravity-only `W`, `e` and `F`, and the final 66/6 census. Every
pattern must match exactly once. Its case tuple and response path are private
bindings. The frozen `summarize()` body receives only the three 396-to-66
literal changes, one 36-to-6 change and nominal-case count 6-to-1.
N14's live `sources()`, `build()` and producer orchestration are not called.
No shared globals or frozen files are modified, and no recovery pipeline is
copied. The original live functions bind six cases and live odd columns,
so substituting only a response path would be insufficient.

The new orchestration is bounded to this one nominal state:

1. Select the three `permanent-only_gap_*` arrays; require finite values
   and exact shapes. Retain the source's bounded-seating status and flags.
2. Use `load = factor * W[:,0]`, `nodal_load = factor * F[:,0]` and
   `relative = D @ a + factor * e[:,0] - H @ raw_force`. Include no live
   column and no second equipment multiplier.
3. Reuse N14's nonfloor row-to-lumped-motion mapping, screw basis/sign
   checks, unilateral axial and bilateral lateral laws. Recover each
   simultaneous tension/lateral tuple and signed opening. Preserve
   opposite panel/receiver wrenches and rigid/relative motion reporting.
4. Recover panel connector nodal loads with the frozen `-B.T @ raw_force`
   footprint. Join the frozen physical DOFs; use the same full physical
   nodal census, panel axes, cut stations, both cut halves and gross widths.
   Audit nodal `F/W`, connector `B/D` wrench agreement and panel balance.
5. Reuse the saved unadjusted N14 screw reference scenarios with
   `duration_factors=[0.9]`. Reuse `panel_sections` for gross demands and
   normal references; a private output adapter emits CD0.9 strengths and
   ratios, preserving the original normal references explicitly. Adjust
   bending, axial tension/compression and planar shear once. Keep Group 4
   reductions and width factors once; do not adjust stiffness, geometry,
   deformation-limited bearing or steel by duration.

Keep N14's existing consumer gates: body/panel force residual below
1e-5 N, moment residual below 0.01 Nmm, relative-motion residual below
1e-6 mm, screw law error below 1e-4 N and the existing detailed
basis/footprint/geometry guards. Failure stops this consumer and transfers
no acceptance. No tolerance change or iteration is proposed.

Required fixed traversal is **66 screw states, six panel balances,
22 panel/receiver groups and 376 gross cut traces**. The group and cut
censuses are recorded for each existing N14 case; the consumer
must retain the same full node/axis census even at zero nodal force.
Outputs are `screw-states.jsonl`, `screw-groups.jsonl`,
`panel-balances.jsonl`, `panel-cuts.jsonl`, `summary.json`, `sources.json`
and a receipt or STOP, with hashes. There is no solve, iterative search,
new load variant, profile assumption, product lookup or measurement gate.
The status on completed arithmetic is
`COMPLETED_PERMANENT_REFERENCE_COMPARISON_WITH_EXPLICIT_GAPS`; it does not
require every reference to pass. The parent owns the single bounded execution
and disposition of actual ratios and unsupported entries.

Source preparation authenticated **24 pins**, including the producer, and
confirmed all adapter patterns. Neither import nor preparation loaded NumPy,
SciPy, OSQP or Clarabel. Syntax compilation passed without bytecode output.
No software tests or new known-answer experiments were run. At numerical
execution, the unchanged N14 `references()` function recomputes its existing
bases and requires exact equality with the frozen N14 head, withdrawal and
lateral catalogs before setting the private duration tuple to `[0.9]`.
The existing N14 receipt/summary provide the recorded formula evidence.

Executed producer snapshot SHA-256:
`196a3211ee78edc0a7b93b25559d5b62f0dc1a3812e417baa43d3b3554261190`.
The maintained source uses dictionary literals after three C408 style fixes;
its SHA-256 is `0e699b152173513c7c8728ebef893bdc4a4b9e03ca930f7478d8465767aa90f9`.
The parent compared both syntax trees after normalizing keyword `dict()` calls
to literals: they are identical. Targeted Ruff passes. The executed snapshot,
receipt and all eight numerical output hashes remain unchanged; the historical
producer pin resolves through `attempt01/producer.py.snapshot`. No numerical
rerun followed this publication cleanup.
The 24-source manifest returned by `prepare()` has canonical SHA-256
`262e0e93a0ab54f3e76a2530a4b44e41bf567971b6497ef914428568baec4672`,
using UTF-8 JSON with `sort_keys=True, separators=(",", ":")` on
`source_sha256`. This includes the producer itself. No raw run was created
by this worker.

## Exact applicability limits retained

This completed comparison covers one saved permanent force/motion solution. The nominal
certificate records four null coordinates, `fixed_force_unique=false` and
`nonunique_disk_witness_found=true`; this consumer supplies no envelope
over alternative seating states and no strict frame-stability acceptance.
The preserved zero-gap response remains a separate source state and is
not substituted for the nominal demand.

N14's delivered Hillman steel/profile, thread engagement, side-grain and
contacting-face applicability limits remain. Unsupported geometry stays
explicit; a saved positive opening cannot qualify a contacting-face
lateral reference. No screw bending couple or steel resistance is invented.
The existing plywood grade/group, category/layup and axis assumptions
remain; gross panel means do not supply local rolling-shear distribution,
net-hole/countersink strength, hold/head transfer, kicker-cutout resistance,
combined plate strength, buckling or serviceability. Absolute individual
elastic motions remain unavailable. The four internal static bridge bolts
remain outside the global receiver rows and gain no compatibility result.

The permanent-only CD0.9 numerical reference comparison is complete under
these existing limits. No additional numerical inventory or generic missing
experiment remains for this scoped task. Genuine remaining bases are
delivered Hillman steel/section/profile and wood-screw conformity, actual
engagement/contact/load-transfer applicability, and delivered plywood/local
panel strength. The bounded nominal seating and four internal static bolts
retain their existing limitations. Old live, duration, original permanent
STOP and resolver packets remain unchanged. No further implementation or
execution is requested by this annotation.

## Frozen input identities

Paths in the first block are relative to this directory. Common physical
input paths use `rawlocal/knee-bridge-gravity/attempt01/`. Saved output
hashes matched their respective resolver/N14 records; neither receipt nor
comparison is self-pinned.

| Source | SHA-256 |
| --- | --- |
| Resolver02 `comparison.json` | `3179d7d40d60a3e21f101610c83acfb588f7e9612941cd253123c9881bbd708a` |
| Resolver02 `response.npz` | `605ef2df67345633860a7d7d77da89e9ec85e94be62ad3c5cd4737c5a0084033` |
| Resolver02 `member-actions.npz` | `e1f3c22a02b7072bf1941ce02be9d3437d7a709dc00cbf802b8327697cb956e8` |
| Resolver02 `body-balances.json` | `251fc111d3714afdba3b884bb1609cf1d8f0f0d96d358b2f1fd609079406b126` |
| Resolver02 `inputs.json` | `9f6652c939a575417fb7a0b3803cbbad19823f1ea9d9baaaf393e3ccad0103ef` |
| `knee-bridge-permanent-resolve.py` | `cddc75df222c82fadef13218286a2bc375539c98d1d4902c3262cea9e5384ee4` |
| `panel-reference-completion.py` | `1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1` |
| N14 attempt01 `summary.json`, including unadjusted reference catalog | `dfa8a93d686e82b5ee8099ad55fce66f436d1720ab5fb51b4cdf6c1b2761c6f5` |
| N14 attempt01 `receipt.json` | `5b42272f49c1924546abab3bd4d036a0a95f7afb2700055fb2e769ab56a3db91` |
| N14 attempt01 `sources.json` | `bb4ef5b08a4cfa58218a9f8da2749d4b5bc447d3062abbb3c68ff718b2a2792f` |
| `fea/reinforced_panel_checks.py`, repository relative | `1cf47584c36ab5c513ee74072f66782b0aa3907cca6b0ee940218d84693d634d` |
| `../top_corner_actions.py`, pure wrench | `bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5` |
| `../panel-attachment/lateral_reference.py`, pure combined reference | `8bcf31f3e69338de5f16824411ae14567187ce6b92cd05a61f7de3be0de7fbb2` |
| `../panel-attachment/attachment_screen.py`, existing head/withdrawal formulas | `c2acb48370cecb3964172e8ab82d3c8999e2836e97025e1bde778bc03cf6b9dc` |
| Physical `model.dof`, N14's frozen matrix-export source path | `532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d` |
| Preserved `panel-duration-applicability.md` | `0d63e96fa6a3ae77c8391876794138ec053035f4caf9e2ed607524d40b29208d` |
| Common `operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Common `operators.npz` | `7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f` |
| Common `B.npz` | `d109f7db25cb05619e26560e501e7e82f3608fdbb3580f76e64f9beae916128a` |
| Common `row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| Common `model.json` | `c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1` |
| Common `model-inputs.json` | `b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99` |
