# Step 6 operation-register source drift reconciliation

The frozen [attempt01](../step6-operation-coverage-attempt01/README.md)
currently fails its producer verifier because the live `next-mvp-plan.md` has a
newer hash than the one recorded in the register. Its companion
tool-route-feasibility attempt01 still verifies.

This append-only audit replays the unchanged attempt01 producer against its
current pinned inputs without writing to the predecessor. The only JSON
difference is the `source_bindings` hash for `docs/wood-joints-mvp/next-mvp-plan.md`;
the regenerated README changes only its resulting machine-JSON digest. All
575 operation/service rows, the 92/12/66 axis coverage, 24-block grouping,
operation-order context, ordinary-local-N disposition, and false release flags
are unchanged. The exact source hashes and diff paths are in
`reconciliation.json`.

This records a provenance drift and replay result. It does not assert that a
changed plan is semantically immaterial, repair attempt01 in place, qualify any
physical operation, or close fit, transport, engineering, or release gates.

## Reproduction

From the repository root:

```sh
.venv/bin/python -B scripts/reconcile_step6_operation_coverage_context_drift_attempt01.py --verify
.venv/bin/pytest -q -p no:cacheprovider tests/test_step6_operation_coverage_context_drift_attempt01.py
.venv/bin/ruff check --no-cache scripts/reconcile_step6_operation_coverage_context_drift_attempt01.py tests/test_step6_operation_coverage_context_drift_attempt01.py
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/step6-operation-coverage-attempt01-current-plan-drift-audit-2026-09-28/SHA256SUMS
```

The producer reads the four pinned source files and performs no CAD or native
solver work. `--write` creates `reconciliation.json` once and refuses to
overwrite it.
