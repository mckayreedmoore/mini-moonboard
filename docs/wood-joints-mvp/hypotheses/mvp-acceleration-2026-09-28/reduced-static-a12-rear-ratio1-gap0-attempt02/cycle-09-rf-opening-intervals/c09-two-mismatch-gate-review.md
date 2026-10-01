# c09 two-mismatch predecessor-gate review

Read-only review performed September 29, 2026. No solver was run. The review
covered the c09 predecessor eligibility gate and its focused regression tests.

## Evidence binding

| Artifact | SHA-256 |
|---|---|
| c09 `freeze.json` | `9af8d36214b108d5d928cfca6e2bb3d853ef70ae8170584939157a5f5a962874` |
| c09 `postrun-review.json` | `7e3581c01e71981a27782fb6b4bc4279f41e51933063db3af49c6db5ac7cb061` |
| c09 `source-drift-equivalence-review.json` | `df166af53d7847e04514512b595195fdea43e5186eb5cc567035397258150333` |
| live `fea/wood_joint_reduced_trial.py` | `2992415bed8848c9fbdca7312bd56dfc0b5e12eded183e993e9606f66a25c912` |
| `tests/test_wood_joint_reduced_trial_transition.py` | `b58ca9cb1fa3f067bb1104203cad543a1904a6f70ae6bd53b60f158a89b701ed` |

The gate's normalized AST fingerprint is
`0e85c16217d20fa6ec7114fd7ca1a54db00111d1066c9b1a9605c50f101adac4`.

## Verification

All 907 frozen source snapshots match their manifest hashes. The live tree has
exactly two mismatches:

- `fea/wood_joint_reduced_trial_review.py`: frozen
  `6b13b79eb35f7238bbc9283ef484271927e2dd14a0ff9519e30d1a74a9cc70be`, live
  `63c8548dce96c535ab62aaacc34a6d192f6a48b0f072429a6527750c277706c5`.
- `fea/wood_joint_reduced_trial.py`: frozen
  `f41a90bfcc3016d873b02733c26af85b82f8798763646f6c005299ce658d9305`, live
  `2992415bed8848c9fbdca7312bd56dfc0b5e12eded183e993e9606f66a25c912`.

The gate accepts the first drift only when the bound equivalence evidence is
exact, requires every other live pin to match, and permits the runner drift
only when its AST outside `_postrun_review_integrity_passes` matches the
frozen runner and the normalized gate AST matches the fingerprint above.
Temporary-evidence positive control accepted. Tampering with the sidecar,
reviewer source, another pinned source, runner code outside the gate, or the
gate body was rejected.

Focused verification using the exact hashes above:
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
tests/test_wood_joint_reduced_trial_transition.py` — 13 passed in 12.59 s.
The saved c09 audit remains byte-identical and retains
`postrun_audit_checks_all_pass: false`.

## Result and limits

**c09 is eligible to serve as a predecessor for a reviewed follow-up.** This
eligibility preserves the failed provenance flag; it does not make the c09
response mechanically acceptable and does not authorize a c10 launch. The
parent still owns c10 preparation, exact-freeze review, readiness, ledger
checks, serialized execution and post-run validation. This review applies to
the exact hashes above; edits to the gate or test file require a new review.
