# Attempt08 independent correctness review

Verdict: **REVISE — the immutable package does not reproduce its advertised delta.** The reviewed maintained snapshot passes its 43 focused tests and 27 additional expected-behavior probes. The three supplied path findings are addressed by those bytes. One low-priority false-pending limitation remains for a whitespace-only top-level JSON key.

This review read only attempt08, the exact maintained source/test files, and `docs/wood-joints-mvp/criteria-method-map.md`. It did not inspect previous attempts or previous review reports. The prior findings stated in the task were used as review targets. The reviewer did not edit source, test, package, or map files. No Docker, solver, or native mechanics execution occurred.

## Findings

### P1 — Included base files are the post-patch files, so the declared replay fails

`source-pins.json` lines 6–9 declare the attempt07 source/test hashes, and `validation.json` reports a successful no-fuzz replay. Both files actually stored in attempt08's `base/` have the maintained attempt08 hashes. Copying those files to a temporary directory and running `patch --batch --forward --fuzz=0 -p1 -i <attempt08>/attempt08.patch` exits 1. All three source hunks and the test hunk are skipped as reversed or previously applied. The resulting source files already match maintained bytes because the starting files did; that is not successful replay evidence.

| File | Declared base SHA-256 | Observed included base SHA-256 |
| --- | --- | --- |
| `mini_moonboard/nds_2024_group_action.py` | `f6ba3e0e92ce049c7c22d0407acc5d455609c7ff22ca088ce8ab774c15bf8811` | `010a883aa9b5d012844bb9ffd631e6a6560c6531e80f95134ad5551374d2e9d6` |
| `tests/test_nds_2024_group_action.py` | `dc03a74055f53c001d2ad17d36af47045302e3a85c4fcc0a7d054fdd07079d25` | `e7ed2c7dbd403039bc28752072d1a1086f6d2aa3b7b07b8d5831b405efb3d965` |

Preserve this attempt and publish a new package with the actual declared pre-patch bytes and fresh replay evidence. Evidence: [verification.json](verification.json) and [patch-replay-output.txt](patch-replay-output.txt). The parent independently acknowledged the packaging mistake during review; the finding above comes from direct hashing and replay.

### P3 — A whitespace-only top-level JSON key cannot be named in a valid contract

At `mini_moonboard/nds_2024_group_action.py:547`, a nonempty key containing only whitespace remains whitespace in the generated path. At line 656, `not path.strip()` rejects that exact path. For two otherwise valid, separately bound records with a root key `" "` changed from `1` to `2`, both factor calls return `calculated_method_only`, but a freshly hashed and independently bound sensitivity contract with `changed_input_paths=[" "]` returns `pending` with `invalid_sensitivity_changed_input_paths`. No alternative path spelling matches the generated path.

This is a false-pending edge case, not an acceptance or hash-check bypass. It affects arbitrary top-level extension keys; the ordinary schema fields, empty-key escape, and nested whitespace keys are unaffected. The supplied patch does not introduce the strip validation, so this is an existing limitation discovered in the reviewed implementation. Either explicitly restrict such extension keys at the input boundary or make their path representation compatible with contract validation. The archived `whitespace-root-key-false-pending` probe reproduces it.

## Correctness checks

- Actual paths and declared paths use the same lexical set normalization. The twelve-fastener pitch scenario calculates correctly even with reversed or duplicate contract ordering; omitted or extra paths remain pending.
- Array growth and shrinkage require `.length` plus every added or removed whole-item index. Independent 2-to-12 and 12-to-2 fastener cases accept complete declarations and reject length-only, omitted-item, or omitted-length declarations. A nested-array growth case also passes. Overlapping indices retain recursive leaf comparisons, while value-type changes require the whole parent path.
- Object-key escaping distinguishes a literal dotted key from nested keys, and a literal bracketed key from an array element. Backslash, dot, both brackets, the empty key, and a literal backslash-plus-e key remain distinct when they coexist in one object. Omitting an escaped literal key is rejected. A real object `length` field and an array's length marker remain distinct in the checked structure.
- Contract content hashes, independent binding hashes, coordinator review status, composite classification, group identity, both scenario identities, and common load-case identity continue to fail closed when mismatched. The focused suite additionally covers missing bindings, payload digest mismatches, strict-JSON rejection, and supported-method limits.
- Every independent probe preserves `capacity: null` and `criterion_disposition: pending`. Successful comparisons identify themselves as method sensitivities only. The supplied source patch changes path reconciliation and normalization, with no resistance, criterion acceptance, geometry, or solver change.

## Validation and pins

The maintained focused command was `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<repo> .venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py`: **43 passed in 1.26s**. See [maintained-focused-tests.txt](maintained-focused-tests.txt).

The archived [behavioral-probe.py](behavioral-probe.py) ran through the public evaluator using the maintained synthetic fixture builders and independently enumerated expected paths. It recorded **27 expected-behavior checks plus the reproduced whitespace-key limitation**. See [behavioral-probe-results.json](behavioral-probe-results.json). Tests were not mislabeled as successful replay tests after the package replay failed.

After the concurrent successor edits, the focused suite and probes were rerun from a temporary copy of the exact reviewed source/test bytes preserved in attempt08's included base. The focused suite passed **43 tests in 0.08s**, and all 27 expected-behavior probes plus the limitation reproduction matched. The probe results record the imported source and fixture hashes. [pinned-snapshot-validation.json](pinned-snapshot-validation.json) binds this check; copying the already post-patch bytes is explicitly not a successful forward patch replay.

The patch hash `eaa0b29cd29f3f2c88fc0c63920116c856df30c95e74a675ee9c7fda825a6595`, the maintained source/test pins, all ordinary package terminal-hash entries, and the criteria-map pin match. The map hash is `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`; it still states that all 36 migrated legacy criteria and 11 candidate obligations remain pending. The two prior-artifact hash references in source-pins.json were not independently reauthenticated because prior attempts were outside this review's permitted reads.

[verification.json](verification.json) records exact input hashes and direct check results. After the tests and probes, the parent changed the maintained source/test files for successor work and confirmed that ownership. The preserved attempt08 package and the criteria map remained unchanged. This report applies only to the original reviewed hashes, which also remain available in attempt08's included base files; it does not review the successor bytes. [terminal-hashes.json](terminal-hashes.json) binds this report and its evidence files and records both the reviewed hashes and the later observed maintained hashes. This review establishes no candidate capacity, criterion disposition, fabrication permission, or climbing release.
