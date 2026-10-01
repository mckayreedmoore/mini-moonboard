# c09 two-mismatch predecessor-gate review v2

Independent read-only review completed September 29, 2026. No native solver was
run, and no c09 freeze, model, deck, output, saved audit, sidecar, runner, or
test was changed during this review. This review covers only the narrow c09
predecessor-gate rebind; it is not a c10 freeze review or launch authorization.

## Exact inputs

| Evidence | SHA-256 |
|---|---|
| c09 `freeze.json` | `9af8d36214b108d5d928cfca6e2bb3d853ef70ae8170584939157a5f5a962874` |
| c09 saved `postrun-review.json` | `7e3581c01e71981a27782fb6b4bc4279f41e51933063db3af49c6db5ac7cb061` |
| v1 source-drift sidecar (preserved) | `df166af53d7847e04514512b595195fdea43e5186eb5cc567035397258150333` |
| v2 source-drift sidecar | `8edead6dacdbfdf829379a1c2127851d7918ee1e175345b23450a2237ecd16ed` |
| v1 gate review (preserved) | `3f671126c12372bb0bafbf79749fcad8bfcdcc4a2b9f671b38f8fbe30c8f6574` |
| v2 gate review plan | `1cc34bff4a9656ecb93ec3d301751f509f0119211c2452773a500815c51cdd7f` |
| c09 frozen `fea/wood_joint_reduced_trial.py` | `f41a90bfcc3016d873b02733c26af85b82f8798763646f6c005299ce658d9305` |
| live `fea/wood_joint_reduced_trial.py` | `3b97e0cec20bd9a3e0658e461808617d69e293846fcff105ae726b56214520f9` |
| c09 frozen reviewer helper | `6b13b79eb35f7238bbc9283ef484271927e2dd14a0ff9519e30d1a74a9cc70be` |
| live reviewer helper | `89dd47aaed3f3e1ac3c4d6dd1ec3d2efd4e7119fb7ded26cd180984a95b1ade1` |
| focused test hash recorded in v2 plan (baseline) | `377566ef4d68b38fc91a9477e055c43a7d940cdc7821f5676308af4cd97aed5a` |
| final `tests/test_wood_joint_reduced_trial_transition.py` | `639fbb7c7316bdf22d9514147d35903c878683febb1e72ceaa19e66dbb2feec1` |

The v2 sidecar's additional bound c09 evidence was independently re-hashed:
`model.json` `fc19f711a817eaecc8df37dd204f2df4cb3dd55e951e74f02fd260226443915a`,
`response.json` `caa2f520636a0a227c425416ca88fc503f7d4f1fc8b06e2fafac832bac9aaf90`,
`model.dat` `b0b91715405351ff895eef19a534c365da62a05652a23ec6d9389b5cfd62fef7`,
the c09 authorization `2bd3ec93debb70d26bab183e45819528d238d7ff03120c175eeb577ecbbe374a`,
external `independent-review.json` `0b67fc8cebe9f74e4865acb5cce5d210cb4cf20112094a690fc89e6293ae2632`,
internal `review.json` `2a3d8a93ebab3cfd7b8f4d53a7f48d68496230bc2a781a9acc45d0883577bebc`,
and `c10-transition-plan-review.md`
`020d86c2f3497d1e1c815372808a0b96fa85ef51a462e0f2cdd1e2770ceccd57`.

## Findings

All 907 frozen source snapshots match their c09 freeze pins, and all 907 live
paths exist. The live mismatch set is exactly two paths:

| Path | Frozen pin | Live SHA-256 |
|---|---|---|
| `fea/wood_joint_reduced_trial.py` | `f41a90bfcc3016d873b02733c26af85b82f8798763646f6c005299ce658d9305` | `3b97e0cec20bd9a3e0658e461808617d69e293846fcff105ae726b56214520f9` |
| `fea/wood_joint_reduced_trial_review.py` | `6b13b79eb35f7238bbc9283ef484271927e2dd14a0ff9519e30d1a74a9cc70be` | `89dd47aaed3f3e1ac3c4d6dd1ec3d2efd4e7119fb7ded26cd180984a95b1ade1` |

The v2 sidecar matches the exact c09 freeze, postrun review, model, response,
DAT, and transition-report hashes above. Its source comparison matches the
live and frozen reviewer helper hashes. I independently recomputed the
reviewer AST delta: `_authorized_review_binding` is the only added function;
`_check_prior_execution` and `audit_consumed_transition` are the only modified
functions; no functions were removed. Their AST fingerprints match the v2
sidecar. The external authorization review binds the c09 freeze and names the
internal transition review by its exact path and hash.

The live predecessor runner differs from the frozen runner only in
`_postrun_review_integrity_passes`; the AST outside that function is identical.
After replacing the embedded `expected_gate_ast_sha256` literal with the
normalization marker, the gate AST hashes to the pinned
`30027b167c57e7c6cc68fa370d5917482bf64b964afc06aaa857ee0797d8ef68`.
The implementation binds the exact v2 sidecar and reviewer hashes, retains the
exact c09 freeze and saved postrun hashes, validates all 907 snapshots, and
accepts only the two scoped live mismatch paths.

The saved c09 audit remains byte-identical at its reviewed hash and still has
`postrun_audit_checks_all_pass: false`, with its original single failed check
`current_live_tree_matches_all_907_freeze_source_pins`. The v1 sidecar and v1
gate review also retain their original hashes above.

The focused tests include a positive control using the exact v2 evidence and
reject controls for changed sidecar bytes (wrong exact sidecar hash), reviewer
source edit, unrelated pinned-source edit, runner edit outside the gate, and
gate-body tampering. Each tamper case first verifies that the untampered
positive control passes. The tests also reject an audit copy whose saved false
flag is changed to true.

## Verification

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_wood_joint_reduced_trial_transition.py
```

Result: **14 passed in 12.86 s**. The final runner and test hashes were checked
before and after the test run and match the hashes in the table above.

## Verdict and limits

**PASS — the exact v2 c09 predecessor-gate rebind passes this independent
review.** For the saved c09 audit, the reviewed gate accepts the exact
external-review provenance chain while retaining c09's false postrun-audit
result. This establishes c09 predecessor provenance eligibility for a newly
reviewed follow-up only. It does not qualify the c09 mechanics, make the saved
audit pass, review or ready a fresh c10 freeze, authorize a native launch, or
establish mechanical acceptance.
