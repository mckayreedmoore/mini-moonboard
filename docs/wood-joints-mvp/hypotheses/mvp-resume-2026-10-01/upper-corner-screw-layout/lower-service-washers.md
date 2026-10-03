# Lower-left service washer wood-bearing reference

**Parent arithmetic completed with exit code 0: four axes, eight endpoints,
24 signed axis/case states and 48 applicable comparisons.** The worker's earlier
preparation checked source hashes, standard-library imports, syntax and lint.
The bounded gap is the four lower-left outer service
axes omitted from `bolted-replay-results/remaining-attempt02/washer-reference-states.csv`:

```text
left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/lower_rail_1
left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/lower_rail_2
left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/lower_side_1
left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/lower_side_2
```

[The producer](lower-service-washers.py) produced **eight endpoints × six current
nominal cases = 48 conditional annular WOOD-BEARING comparisons**. It uses the
same 14 CSV columns and annulus/reference equations as the frozen remaining
washer helper. That helper imports CAD and mechanics modules and has no separate
washer-only function, so this small producer reads its frozen snapshot and
schema as evidence and performs the annulus arithmetic with the standard library.
It imports no CAD or numerical package and opens no force/operator array.

## Completed parent result

The saved `counts` are `axes=4`, `endpoints=8`, `signed_axis_case_states=24`,
`washer_reference_states=48` and `applicable_reference_states=48`. All 48
conditional annular wood-bearing comparisons are applicable within the recorded
nominal support and material scenario.

The saved `peak_conditional_wood_bearing_reference` is **K12-right,
`lower_rail_1`, head endpoint on `left_service_outer_lower_cleat`**, with full
axis ID
`left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/lower_rail_1`.

| Saved peak field | Value |
| --- | ---: |
| `outer_tie_signed_n` | 11.206614391903017 N |
| `axis_grain_absolute_dot` | 6.332022128852088e-10 |
| `ideal_full_annulus_area_mm2` | 213.62787318750497 mm² |
| `ideal_annulus_pressure_mpa` | 0.05245857773468902 MPa |
| `wood_reference_mpa` | 4.309223308230226 MPa |
| `ideal_pressure_over_wood_reference` | 0.012173557502693791 |

Its route is `PERPENDICULAR_BASE_REFERENCE`,
`full_annulus_reference_applicable=true` and `known_partial_support=false`.
`actual_supported_pressure_mpa` and `washer_metal_resistance_n` remain null.
This peak is a conditional wood-bearing comparison, not an actual washer/contact
pressure, metal resistance or complete-joint acceptance.

The parent supplied these completed artifact hashes; final authentication and
publication remain with the parent:

| Artifact under `rawlocal/lower-service-washers/attempt01/` | SHA-256 |
| --- | --- |
| [Result and full census](rawlocal/lower-service-washers/attempt01/result.json) | `cea8ed7447fd3b73a50833bd3cbe67310917e7d37e02b1d1fcb59489997997db` |
| [Washer reference CSV](rawlocal/lower-service-washers/attempt01/washer-reference-states.csv) | `c149882f172ab6456259f4d5e677db8a9cb0f019f8171b5487fc2b162b57b75a` |
| [Source/output receipt](rawlocal/lower-service-washers/attempt01/receipt.json) | `1e9f911f7dc24ea9ffc4257a6ae0756e3fee731bc1eac209a92b1449b9209dd0` |

## Sources and binding

The existing lower-service reference is saved at
[`../service-joint-current-attempt03/four-screw-250-attempt03/result.json`](../service-joint-current-attempt03/four-screw-250-attempt03/result.json),
SHA-256 `850a31de41efc8e710cb45660f9822852469303e0e391fb70ed325977558293c`.
It contains 24 current signed axis/case states and individual lateral references,
with no washer reference. Only its `simultaneous_tension_n` fields supply this
packet's demands. Its pins must bind the exact current response, comparison,
model, row identities and model inputs below; the six cases retain their source
order and `gap_scale=1.0`.

| Direct source | SHA-256 |
| --- | --- |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `operators-attempt02/model-inputs.json` | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| `../../lower-left-service-joint/results/attempt01/geometry-evidence.json` | `5692b6620fffe0c36f729f4d0cac607c3012c9a9a112659d12a521432bed6c24` |
| `/tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json` | `64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3` |
| `bolted-replay-results/remaining-attempt02/washer-reference-states.csv` | `43da5dab2bc0ed8761959767aecec466a645a3832509c7162e494cc4da17f35b` |
| `bolted-replay-results/remaining-attempt02/producer.py.snapshot` | `4d9ea0e03ab98ba4bc8c9e4641a85d5e54603c59cf2ab1d17385de4c16dc964f` |

The frozen geometry join already records eight nominal washer seats and 24 clear
component routes. The four complete connection records and three receiver
records match the original reduced inputs exactly. The producer requires that
equality, pins each finished STEP file and grain map, and binds each endpoint to
the current outer-tie row, head/nut owner, point and receiver interval. It reuses
only the nominal support evidence; it grants no new access or installed-operation
pass. The old geometry join names `/tmp/remaining-washer-seats.json`; the parent
support path above contains the identical frozen bytes and is checked against
that recorded hash.

| Axis suffix | Head endpoint | Nut endpoint | Current outer-tie row, zero based |
| --- | --- | --- | ---: |
| `lower_rail_1` | `left_service_outer_lower_cleat` | `base_rail_service_lower_left` | 1548 |
| `lower_rail_2` | `left_service_outer_lower_cleat` | `base_rail_service_lower_left` | 1549 |
| `lower_side_1` | `base_side_left` | `left_service_outer_lower_cleat` | 1550 |
| `lower_side_2` | `base_side_left` | `left_service_outer_lower_cleat` | 1551 |

## Conditional comparison and limits

Each row preserves the signed current `Ti`. Only pressure uses `max(0, Ti)`;
the same case's tie is used at both endpoints, without combining case maxima.
The source grain direction comes from each current receiver descriptor and must
match its current model material orientation. All eight endpoints must remain
perpendicular to grain for this bounded route. These are recorded conditional
grain orientations, not observations of delivered timber.

The catalog minimum annulus uses OD **0.727 in / 18.4658 mm** and ID **0.327 in /
8.3058 mm** from the existing fastener inputs. The producer evaluates
`A = pi/4 × 25.4² × (OD_in² − ID_in²)` and checks it against the saved catalog
annulus and each endpoint's three `plain_minimum_area` support probes. The
frozen nominal probes at 0.01, 0.05 and 0.1 mm already establish full support
for those unchanged seats; no CAD replay is needed.

The wood comparison retains the remaining helper's **dry, normal-duration
DF-L No. 2 base `Fc_perpendicular=625 psi`**, converted with the same
`0.006894757293168361 MPa/psi`. Pressure is `max(0, Ti)/A` and its comparison
is pressure divided by that base reference. Original material adjustment inputs
are copied into the result without selecting or increasing any factor. The
1350 psi parallel base reference is preserved in the material census but is not
used at these perpendicular endpoints. The candidate block's elastic diagnostic
category stays distinct from this conditional wood strength reference.

Full nominal annular wood support does not establish actual head/nut contact,
washer spreading, eccentric pressure, preload, product conformity or loaded
contact compatibility. `actual_supported_pressure_mpa` and
`washer_metal_resistance_n` remain null. No product yield, steel or plate capacity
is invented; no complete joint or physical release follows from a ratio. This
packet copies the existing source force scope and statuses without making an
independent force-profile claim or changing formal47/all8, rank, stability,
seating or acceptance dispositions.

## Parent execution and deterministic receipt

Recorded parent command for the completed attempt, from the repository root:

```sh
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/lower-service-washers.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/lower-service-washers/attempt01
```

The API is `build() -> (result, pins)` for in-memory parent arithmetic and
`produce(output: Path) -> receipt` for publication. Output must be a fresh child
of the owned raw directory; an existing attempt is refused. The producer writes
`result.json`, `washer-reference-states.csv`, `producer.py.snapshot` and
`receipt.json`. The JSON retains exact axis/end/material/support and signed-force
censuses, source pointers and pins. The receipt binds all direct source and
output bytes and the Python version. Sources are rehashed after arithmetic and
before writing; ordering is fixed and receipts contain no timestamps or output
directory-dependent paths.

Prepared producer SHA-256:
`9d53e8fd8bb7aa3f6df042b7086abc6ed0057febd48a7e4b6cd00d23dc283494`.
The worker's source-only
[preparation receipt](rawlocal/lower-service-washers/source-preparation.json)
pins all 15 frozen direct sources and records the preparation-time pending
status. The completed parent result above supersedes that status without
changing the preparation receipt. Its SHA-256 is
`4e724ccdb9bfd2759b883f543f821d3f572005f66a06a5ea9dc7f52bfdf84110`.

Only this script, this note and ignored `rawlocal/lower-service-washers/` belong
to the original bounded task. This completion annotation changes only this note
after reading the saved parent result. The producer remains frozen at `9d53e8fd`;
all other files are preserved. No rerun or new checks were performed. Final
authentication and publishing remain with the parent. No tests, CAD/native/frame
run, review, staging or commit is performed by this annotation. Washer coverage
and top-host/order/source integration remain with their existing owners. All consumed evidence stays
active; this packet nominates no archive or pruning.
