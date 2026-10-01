# A12-rear BG001 outer-seat stiffness sensitivity input

This packet prepares one input-only sensitivity case from the usable A12-rear
response model. It changes the effective axial stiffness of the two BG001
left-post outer bolt-seat ties and keeps their one-sided tensile law, axes,
coordinates, span, and table domain fixed. It does not alter geometry, member
materials, source loads, other connectors, or floor support input. No native
solve or acceptance is claimed.

The source-bound local sensitivity is
[`current-post-spine-compliance-sensitivity-attempt01/sensitivity.json`](../current-post-spine-compliance-sensitivity-attempt01/sensitivity.json)
(SHA-256 `0994ae3f5a54c6eb985141c54eb3d38d455678482ed2ac5a6205e2a84096a9c0`).
Its scenario 4 uses the local study's nominal ring-case A frame pair
(`ring_R_on_X` and `ring_R_on_source_X`), steel modulus 190,000 MPa, and an
idealized wood influence depth of twice the equivalent washer-area diameter:
33.679894 mm. It produces a series stiffness of 2,401.714360 N/mm at each
seat. The A12-rear model's corresponding baseline ties are 4,670.054188
N/mm, which is the local model's matching frame pair at 200,000 MPa steel and
one equivalent washer-area diameter of influence depth. The prepared value is
0.51428 times baseline.

The calculation in [`fea/wood_joint_reduced_properties.py`](../../../../../fea/wood_joint_reduced_properties.py)
models steel extension and the two outer washer-seat wood-column compliances
in series. The sensitivity packet explicitly says the two-diameter depth is
uncalibrated and the results do not establish real stock stiffness, calibrated
seat compliance, bolt or joint capacity, or a physical stiffness bound. The
190 GPa / two-diameter combination is therefore one declared response
sensitivity point, not a lower-bound property for delivered hardware or
timber. No global steel or timber material card is changed; this variation is
represented by the effective spring stiffness for these two ties only.

The changed springs are `knee_outer_left_post_1/outer-seat-axial-tie`
(`SPR1771`) and `knee_outer_left_post_2/outer-seat-axial-tie` (`SPR1772`).
Both connect `knee_outer_left_spine` to `base_post_outer_left` along global X.
In each runtime binding, only `stiffness_n_per_mm` and the positive 10 mm
force ordinate change. The copied source carrier inventories remain
unchanged as provenance. The native deck has the same two nonlinear spring
table ordinates changed to `24017.14359617,10.0`. The original law remains
`k * max(q_mm, 0)`, with `q = u(second projection) - u(first projection)`,
zero gap/preload, 100 mm numerical span, and the `[-10,+10]` mm table domain.

`prepare.py` pins the baseline model, deck and response; the local sensitivity
result and producer; and the property producer. It checks the selected
sensitivity row, verifies that the JSON differences are exactly the four
runtime stiffness/table fields for these two ties, verifies that the deck
differs on exactly their two force-table lines, and checks the unchanged
one-sided law arithmetically. It does not run the solver or edit the baseline
packet. `variant.json` records the resulting hashes and the complete change
list.

`validate_sensitivity_input.py` is a separate input-only validator. Load it
through `sensitivity_response_core.load_sensitivity_input_validator()` so the
contract has the one authenticated Python class identity. Its
`validate_contract_for_paths(model_path, deck_path)` accepts only these exact
variant paths and hashes, validates the exact baseline through the unchanged
attempt03 input contract, and rejects any other model/deck difference. The
returned sealed `ValidatedSensitivityContract` exposes separate baseline and
variant contract builders. It replaces only the two approved `bindings` rows
in the baseline response-core contract; source inventories, ownership,
support, loads, floor mask, MPCs, and the 348 bilateral SPRING2 rows stay
unchanged. The active selected-floor branch must still be checked independently
for this changed response before any variant demands could be used.

`sensitivity_response_core.py` is a small fork of the pinned 711 zero-U-token
response wrapper. Its ordinary `audit_record(record, data, deck,
case_context)` path still invokes the original strict model/context validator.
The separate `audit_record_with_validated_contract(...)` path accepts only the
exact validator class and its module-private seal, verifies exact model/deck
hashes and source pins, then runs the same physical recovery and gate body.
Plain dictionaries and duck-typed fake builders are rejected. The two frozen
auditors are not edited. The standard 711 context path is not claimed for this
legacy A12-rear screen: its provenance names earlier selected-branch outputs,
not the exact all-bearing controls model/deck that the 711 context validator
requires. The fork’s report records this limitation instead of asserting a
fabricated context.

The read-only verifier replays the existing A12-rear DAT against the sealed
baseline input contract using the 711 recovery core, checks all seven baseline
physical gates and exact raw connector-force/printed-balance parity against
the prior accepted report, and then confirms that the old DAT is rejected by
the variant table law at both changed groups in all seven increments. The
zero-U parser changes the uncertainty radius for exact zero displacement
tokens, so interval identity with the older report is not required. The test
emits no variant force report and does not reuse baseline response forces as
variant demands. Four synthetic exact states also check the changed slope
against analytic SPRINGA forces, including an open-side state. Six negative
input mutations cover a wrong target table, a third spring, load and geometry
changes, a wrong native ordinate, and a changed control card.

Reproduce the input preparation from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-variant-attempt01/prepare.py
```

Reproduce the sealed input validation, synthetic analytic states, A12-rear
baseline replay, and stale-DAT rejection with the pinned precision parser:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-variant-attempt01/verify_sensitivity_input.py
```

The recorded result is in `sensitivity_input_contract_check.json`.
It reports `PASS_EXACT_TWO_TIE_SENSITIVITY_INPUT_CONTRACT`, seven passing
baseline increments (9,044 SPRINGA checks), exact raw force and printed-balance
parity, and rejection of the stale baseline DAT under the altered SPR1771 and
SPR1772 laws. No new native solve, freeze, frame-readiness decision, or
mechanical acceptance is claimed.

No native command is part of this packet.
