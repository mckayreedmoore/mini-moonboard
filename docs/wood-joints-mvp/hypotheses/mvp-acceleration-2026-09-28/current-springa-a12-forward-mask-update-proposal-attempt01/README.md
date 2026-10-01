# A12-forward floor-mask update proposal

This packet prepares one input-only candidate from the strict normal-gap
intervals in the rejected A12-forward selected attempt03 response. It does not
freeze, run, export forces, or establish a compatible floor branch.

## Source and cause

There is no top-level packet literally named
`current-springa-a12-forward-normal-interval-diagnostic-attempt01`. The
relevant checked lineage is:

| Proposed input | Selected cells | Input model SHA256 | Relationship to the latest stable positive set M4 |
| --- | ---: | --- | --- |
| selected attempt01 (M1) | 35 | `50edee6194d3abdb758e8e7eb17f361b10cae7fc839dcedfa9f24f070d25324b` | M4 retains all 35 and adds `floor_base_floor_left_15`, `floor_base_floor_left_17`. |
| selected attempt02 (M2) | 31 | `b50f560a1296f13a567bf37c17e6cd532ce9699d16b7700421b098aedd1420fe` | M4 removes `floor_base_floor_left_1`, `floor_base_floor_right_7`; it adds left_15, left_17, right_0, right_2, right_4, right_6, post_center_right_0, and lumber_leg_left_2. |
| selected attempt03 (M3) | 37 | `4f7d3f0a70a534a1c38cd0ce6e48990eb7b098dc82dc5fc2f412ff34eca3ff0f` | M4 removes left_9, left_11, left_13 and adds left_15, left_17, post_outer_left_1. |

M4 is the same 37-cell strict-positive set in all seven printed states of
`current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/diagnosis.json`
(SHA256 `03d77cde6c1ca73f32fe7036cdf462df60de5fd929207f585d594fbacafb9194`).
The diagnosis is for selected attempt03, whose input is M3. Every state
classified all 100 normal carriers: 37 strictly positive and 63 strictly
separating after printed-token interval bounds, with no ambiguous cells. These
are classifications of that run only; no force or reaction values were
adopted, and its parent assessment rejects corner-demand use and mechanical
acceptance.

The successive inputs have 35, 31, and 37 bearing cells, hence 70, 62, and 74
floor tangential MPC rows. The 100 normal SPRINGA laws and source loads remain
fixed, but each selected-bearing mask changes which floor tangential
constraints are present. Those changed constraints alter the structural
support/load path and can change the normal-gap sign pattern. Thus a stable
37-cell output from M3 is not evidence that M1, M2, or M3 is a self-consistent
active set. M4 is a justified *next explicit input hypothesis* because it is
the unambiguous source-derived sign set from all seven M3 states and has not
been used as an input in this lineage. Its recurrence and compatibility remain
unknown until that distinct input is independently evaluated.

## Prepared input

`prepare_m4_proposal.py` reconstructs the M4 screen from the pinned intervals,
checks the prior masks and source hashes, and calls the existing case-bound
selected-floor adapter. The resulting `screen.json` is diagnostic-only and
binds the all-bearing A12-forward controls model/deck, load register, case
model, and prior selected run. The prepared model/deck are in `a12-forward/`;
its audit reports `PASS_SELECTED_FLOOR_INPUT_ALGEBRA_AND_SOURCE_PRESERVATION`.
It retains all 100 normal laws, all 348 bilateral SPRING2 carriers and 50
physical bodies, with 37 selected cells/74 tangent rows and 63 inactive cells.

`check_m4_input_gate.py` builds the standard case-context instance from the
existing A12-forward input-context template and contract, rebinding only the
M4 diagnostic screen and exact prepared model/deck paths and hashes. It calls
the unchanged pinned 711 `_validate_case_context` and `_validate_model`
methods, with the pinned stable recovery source. Result:
`PASS_PINNED_711_CASE_CONTEXT_AND_MODEL_INPUT_GATE`; see `case-context.json`,
`input-gate.json`, and the compact direct/transitive source pins in
`input-gate-source-pins.json`. This remains an input gate only; it does not
create a frozen run context or native-ready status.

Reproduction command in a clean checkout with these pinned sources:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/\
current-springa-a12-forward-mask-update-proposal-attempt01/prepare_m4_proposal.py
```

The script refuses to overwrite `a12-forward/`. This proposal grants no native
readiness: no new freeze, solve, response-force adoption, corner demands, or
mechanical acceptance are present. In particular, a future input run must be
checked against its own positive-selected/zero-force inactive normal
complementarity and the existing MPC, spring, body/global, and source-load
criteria; neither M3 response nor rejected-run forces transfer to M4.
