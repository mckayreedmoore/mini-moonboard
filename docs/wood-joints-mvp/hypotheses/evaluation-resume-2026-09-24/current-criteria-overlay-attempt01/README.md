# Current criteria source overlay — attempt01

This attempt lets the exact47 aggregator consume the current method map while
preserving the frozen coverage file and its historical method-map digest. The
versioned [`source-overlay.json`](source-overlay.json) records the immutable
coverage digest, historical and current map hashes, reconciliation-record
hash, and the hash-bound coordinator review status.

The aggregator accepts the overlay only when all bound files resolve at their
fixed paths and hashes, the frozen coverage still contains the historical pin,
the current method map matches both the overlay and parent-reviewed
reconciliation, and the review document has status
`PASS_SOURCE_PROVENANCE_RECONCILIATION_ONLY`. It also verifies the review's
hashes for the reconciliation script, README and reconciliation record. A
missing or mismatched overlay, review, or source leaves the original
“planning coverage is stale against its method map” blocker in place.

The review is limited to source provenance. The old map hash remains
`1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80`; the
current tracked map hash is
`2ab30c154d75306cb83c88fdde98f7af8082b3c57089a9fdf587c5b3b9818182`. The
frozen coverage digest remains
`c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c`, and
the reconciliation record is pinned at
`6c52afa400f2fe2a3a8b566aa0f8ec0869df12334fcadf2b3347a2fba8d2c233`. No
frozen coverage or method-map file is edited.

## Current status

`current-inventory/current-aggregate.json` retains 47 `pending` rows. The
valid provenance overlay removes only the stale embedded map-pin error.
Applicability cells, adopted acceptance sources, fresh current demands and
per-scope result evidence remain open. The reconciliation's one-row
`steel_direct` change is source history only; it does not establish a method,
resistance, or criterion disposition. Engineering completion and every release
flag remain false.

## Validation

The focused suite includes positive mechanics fixtures and adversarial overlay
mutations for the current map hash, frozen coverage digest, reconciliation
hash and review status. It also removes the overlay binding to confirm that the
stale-pin error remains fail-closed. The focused run passes all 22 tests.

```sh
.venv/bin/python -m pytest -q tests/test_wood_joint_wj08_criteria.py
.venv/bin/python -m py_compile scripts/wood_joint_wj08_criteria.py
```

Generate the read-only current inventory with:

```sh
.venv/bin/python scripts/wood_joint_wj08_criteria.py \
  --bootstrap-current \
  --output-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-criteria-overlay-attempt01/current-inventory
```

The next consumer remains T11, “Resolve exact 47-criterion register.” This
artifact supplies provenance for the method-map source only; it closes no
criterion and grants no engineering or release status.

## Files

- `source-overlay.json`: hash-bound current-source overlay and coordinator
  review reference.
- `current-inventory/`: independent unresolved expectations, empty evidence,
  and the current 47-row aggregate.
- `input-pins.json`: source, overlay, review, and prior-attempt pin inventory.
- `sha256.json`: terminal hashes for this artifact, implementation and tests.
