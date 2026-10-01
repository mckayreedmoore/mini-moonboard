# Current timber cut-yield scenarios, attempt 02

This append-only packet hardens attempt01's 30 deterministic cut-length arithmetic scenarios and authenticates the prior report and independent review. It closes four validation gaps: both source revision IDs are checked, attempt01's entire verification record is compared with its expected values, non-finite numeric inputs are rejected, and the attempt04 manifest must contain exactly 24 unique block IDs.

The schedule remains tied to `led-clearance-2x6-runner-seated-blocks-v1`. It contains the same 24 blank IDs, stock classes, finished sections, and lengths: 18 4x4, four 4x6, and two 2x6 blanks. Different finished sections remain separate arithmetic cohorts; scenarios do not share an unsawn 4x6 source stick across the two post-rip sections. Four ripped 4x6 blanks retain unresolved post-rip grade disposition.

Published length leads and explicit hypothetical kerf/end-trim inputs are scenario parameters. Each proposed blank incurs one full kerf, including the last blank in an arithmetic bin; configured end trim is charged once per bin. The deterministic packing is arithmetic only. It does not establish local or available stock, a product choice, physical fit, accepted material or grade, purchase quantities, prices, cutting authorization, or release. The two 2x6 listing leads preserve their different green/kiln-dried descriptions and are not selected.

`source-pins.json` fixes the exact hashes of the raw schedule, manifest, grade and material status, revision, selected-candidate authority, all attempt01 artifacts, and its independent review. The verifier fails closed on any pinned-source drift, re-runs the attempt01 report from pinned inputs, and checks the complete attempt01 and attempt02 verification objects.

From the repository root:

```sh
.venv/bin/python scripts/build_current_timber_cut_yield_scenario_attempt02.py --write
.venv/bin/python scripts/build_current_timber_cut_yield_scenario_attempt02.py --check
.venv/bin/python -m pytest -q tests/test_current_timber_cut_yield_scenario_attempt02.py
.venv/bin/ruff check scripts/build_current_timber_cut_yield_scenario_attempt02.py tests/test_current_timber_cut_yield_scenario_attempt02.py
```

`--write` emits the arithmetic report and verification record. `--check` authenticates the pinned source set and stored outputs without rewriting them.
