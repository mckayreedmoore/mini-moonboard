# K12-right attempt03 floor-normal recurrence diagnosis

This packet classifies all 100 source-owned floor-normal carriers at all seven
increments of `springa-selected-k12-right-attempt03` using the pinned 711
zero-U response parser and interval classifier. It compares the resulting
strict-positive sets against the selected input masks for right attempts01,
02, and03. Attempt01 and02 classifications are reused from their pinned
diagnostics; attempt03 is classified afresh from its pinned `.dat` file.

The exact sequence is **right01 original 10 → right02 updated 10 → right03
selected 11 → right02 updated 10**. Attempt03 has 10 strict-positive, 90
strictly separated, and zero unresolved normals at each of its seven recorded
increments. The alternating cell is `floor_lumber_leg_right_0`: attempt02 found
it positive while inactive, while attempt03 finds it separated while
selected. The exact interval positions, set differences, and all 700 current
normal classifications are in
[`k12-right-attempt03-normal-interval-comparison.json`](k12-right-attempt03-normal-interval-comparison.json).

This is a two-mask recurrence for these three source-bound case states, not a
general contact-law result. It supports stopping repeated fixed-support mask
updates here and investigating the support-formulation dependency. The
attempt03 strict response audit remains rejected because selected SPR1311 is
not strictly positive. No corner demands or conditional forces are usable;
this packet exports no forces, proposes no new mask, and runs no solver. It
does not infer physical floor failure, establish another case's behavior, or
accept a joint.

Reproduce and verify from the repository root with:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-k12-right-attempt03-normal-interval-diagnostic-attempt01/produce.py --verify
```

`produce.py --write` regenerates the JSON report only after verifying every
listed source pin. `SHA256SUMS` covers this packet's producer, report, and
README. The report's `artifact_provenance.source_file_sha256` records the
external input and method pins used by the computation.
