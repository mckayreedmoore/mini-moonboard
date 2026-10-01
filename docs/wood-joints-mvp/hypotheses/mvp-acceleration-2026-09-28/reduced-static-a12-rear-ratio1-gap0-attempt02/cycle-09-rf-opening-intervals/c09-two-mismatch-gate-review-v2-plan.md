# c09 two-mismatch predecessor-gate v2 independent review plan

Prepared September 29, 2026, after the narrow external-review authorization fix
in the shared reviewer. This is a review plan, not a passing gate review and
not permission to prepare or run c10.

## Frozen and versioned evidence

| Artifact | SHA-256 |
|---|---|
| c09 `freeze.json` | `9af8d36214b108d5d928cfca6e2bb3d853ef70ae8170584939157a5f5a962874` |
| c09 saved `postrun-review.json` | `7e3581c01e71981a27782fb6b4bc4279f41e51933063db3af49c6db5ac7cb061` |
| Original source-drift sidecar v1 | `df166af53d7847e04514512b595195fdea43e5186eb5cc567035397258150333` |
| New source-drift equivalence sidecar v2 | `8edead6dacdbfdf829379a1c2127851d7918ee1e175345b23450a2237ecd16ed` |
| c09-to-c10 transition review | `020d86c2f3497d1e1c815372808a0b96fa85ef51a462e0f2cdd1e2770ceccd57` |
| Existing gate review v1 | `3f671126c12372bb0bafbf79749fcad8bfcdcc4a2b9f671b38f8fbe30c8f6574` |
| Frozen reviewer source | `6b13b79eb35f7238bbc9283ef484271927e2dd14a0ff9519e30d1a74a9cc70be` |
| Current reviewer source after fix | `89dd47aaed3f3e1ac3c4d6dd1ec3d2efd4e7119fb7ded26cd180984a95b1ade1` |
| Current predecessor runner | `2992415bed8848c9fbdca7312bd56dfc0b5e12eded183e993e9606f66a25c912` |
| Current focused transition-test file | `377566ef4d68b38fc91a9477e055c43a7d940cdc7821f5676308af4cd97aed5a` |

The v2 equivalence sidecar is a new artifact. Keep the v1 sidecar and v1 gate
review unchanged as historical evidence. The saved c09 audit remains false;
its recorded live-pin mismatch and false overall result are not to be rewritten.

## Why a fresh gate review is required

The current c09 gate still pins the prior live reviewer SHA
`63c8548dce96c535ab62aaacc34a6d192f6a48b0f072429a6527750c277706c5` and the
v1 sidecar hash. The current reviewer SHA is now
`89dd47aaed3f3e1ac3c4d6dd1ec3d2efd4e7119fb7ded26cd180984a95b1ade1`; the gate
therefore fails closed. The current mismatch set against c09's 907 source pins
remains exactly two paths: the reviewer helper and the previously reviewed
runner gate edit. All 907 retained snapshots still match their original pins.

The v2 sidecar records the reviewer AST delta from the c09 snapshot: it adds
`_authorized_review_binding` and changes `_check_prior_execution` and
`audit_consumed_transition`. The changed predecessor check now validates the
authorization-named external review by exact hash, requires it to bind the c09
freeze, and requires its provenance to bind the internal transition review by
path and hash. It retains the direct checks for the internal review's exact
freeze and ready status, plus the existing authorization, terminal execution,
ledger, output, log, response, recovery, and source-pin checks. The frozen and
current ASTs for the DAT branch derivation, active-set history, deck checks,
and transition entrypoint remain identical.

The old gate review covered the exact old helper and v1 sidecar. It cannot
approve the updated helper or the v2 sidecar. The v2 gate must be reviewed
against its own exact code, test, and evidence hashes.

## Required narrow rebind

After the root coordinator updates the gate, an independent reviewer should
confirm that the gate change is limited to `_postrun_review_integrity_passes`
and that all AST outside that function remains equal to the c09 frozen runner.
The gate may accept the v2 sidecar only under its exact hash and the current
reviewer source only under SHA-256
`89dd47aaed3f3e1ac3c4d6dd1ec3d2efd4e7119fb7ded26cd180984a95b1ade1`. Keep
these exact c09 pins: freeze `9af8d362…`, saved post-run review `7e3581c0…`,
frozen reviewer `6b13b79e…`, and 907 source snapshots. Require the current
live mismatch set to be precisely the reviewer helper and runner gate paths;
reject any additional, missing, or changed path.

Recompute the normalized gate AST fingerprint after the new sidecar and
reviewer hashes are inserted. Pin that fingerprint in the gate and review the
resulting runner hash. Preserve the existing fail-closed behavior for an
incorrect sidecar, reviewer edit, unrelated source edit, runner change outside
the gate, and gate-body tampering. Use a positive control containing the exact
v2 sidecar and the exact current source files.

The independent gate review should bind the current focused test file hash
above, inspect the new regression for authorization to an external review, and
rerun the focused gate and transition checks after the final runner edit. The
parent reports that the new regression passes; this plan records that report
but does not claim an independent test run.

## Review exit and boundary

Pass only if the reviewer verifies all 907 c09 snapshots, the exact two-path
live mismatch set, the v2 sidecar binding, the exact new helper AST, the
normalized gate fingerprint, the positive control, and rejection of all
listed tampering. Keep c09's original false audit flag and its nine contact
sign exceptions intact. A gate pass would establish only c09 predecessor
provenance eligibility for a newly reviewed follow-up. It would not qualify
the c09 response or authorize a c10 native launch. The first c10 freeze is
superseded by the source change; the parent must prepare and independently
review a fresh exact c10 freeze before making readiness or launch decisions.
