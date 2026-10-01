# WJ-08 exact47 aggregator boundary — attempt02

Attempt02 hardens the maintained exact47 evidence aggregator after review
found that attempt01 trusted producer-selected method terms and demand source
paths when those values were internally self-consistent. The validator now
requires each applicable expected scope to resolve a method, version, scope,
comparison, finite limit and unit from a hash-bound independent acceptance
manifest. A dynamic scope must also resolve its case and simultaneous wrench
through an independently bound demand manifest and the exact expected case
pointer. Producer method metadata, acceptance terms, demand path, hash, pointer
and wrench must match those independent sources.

The interfaces `wood_joint_acceptance_contract_manifest/v1` and
`wood_joint_current_demand_manifest/v1` are aggregator input contracts. They
are not engineering acceptance schemas or adopted methods. Current authoritative
per-scope acceptance terms and fresh demand bindings have not been supplied.
The current expectation builder therefore fails closed with named open fields:
`scope_cells`, `acceptance_contract_source`,
`demand_source_binding_for_dynamic_scope`, and
`fresh_per_scope_result_evidence`. No current row can pass until the WJ-07/WJ-08
scope manifest, the method/acceptance source and fresh current demand inputs
are independently frozen and bound. Static identity or geometry scopes may
omit a load case only when their independent scope contract justifies it.

## Current inventory

`current-inventory/current-aggregate.json` contains exactly 47 `pending` rows;
there are no `failed`, `conditional_pass` or N/A rows. Current full-frame
demands are unavailable, and the evidence bundle is empty. A positive fixture
in the focused tests exercises aggregator mechanics only; it is marked
`TEST_ONLY_NOT_ENGINEERING_EVIDENCE` and makes no capacity or engineering
claim. Engineering completion and all release flags remain false.

The frozen coverage source still pins `criteria-method-map.md` to
`1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80`, while
the current tracked method map hashes to
`2ab30c154d75306cb83c88fdde98f7af8082b3c57089a9fdf587c5b3b9818182`. This
stale pin is preserved as a distinct source-integrity finding; it is not the
same as missing expected scope, missing acceptance terms, missing fresh
demands, or missing result evidence. Neither frozen source was edited.

Resolve the pin by preserving `current-criteria-coverage.json` and adding a
versioned reconciliation record that includes both hashes and a content review
of the method map against the intended coverage. The coordinator should review
that record before a later current-source overlay binds the observed method-map
hash and reconciliation record. Do not silently replace the frozen pin or
transfer prior criterion evidence.

## Validation and next consumer

Run the focused boundary suite with:

```sh
.venv/bin/python -m pytest -q tests/test_wood_joint_wj08_criteria.py
```

The adversarial cases change only the producer method or limit, and separately
substitute a self-consistent demand artifact with its own matching path and
hash. Each attempt remains pending because it does not match the independent
acceptance or demand binding. Static geometry mechanics are also tested without
inventing a load case. The current inventory was generated with:

```sh
.venv/bin/python scripts/wood_joint_wj08_criteria.py \
  --bootstrap-current \
  --output-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-criteria-aggregator-attempt02/current-inventory
```

The next consumer is T11, “Resolve exact 47-criterion register.” T11 may consume
this interface after its independent scope, acceptance and current-demand
inputs are frozen and the stale method-map pin has a reviewed reconciliation.
This attempt closes no criterion and grants no engineering or release status.

## Files

- `current-inventory/expected-coverage.json`: current unresolved independent
  expectations with explicit open fields.
- `current-inventory/empty-evidence.json`: empty current producer evidence.
- `current-inventory/current-aggregate.json`: read-only current 47-row result.
- `input-pins.json`: source and readiness status, including the preserved pin
  mismatch.
- `source-snapshots/` and `attempt01-source-freeze.json`: byte-preserved
  attempt01 code, tests and terminal hashes.
- `sha256.json`: terminal hashes for attempt02 code, tests and outputs.
