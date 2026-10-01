# WJ-08 exact47 aggregator boundary — attempt01

This attempt adds a reusable fail-closed aggregator for the exact 47 criteria
in `criteria.json`. It checks evidence identity, source hashes, independently
declared scope cells, finite numeric comparisons, simultaneous signed demand
records, and disposition consistency. It does not calculate capacities,
select methods, establish applicability, or make engineering acceptance.

## Current result

`current-aggregate.json` contains 47 `pending` rows. The current expected-scope
manifest marks all rows unresolved because there is not yet a reviewed WJ-07 /
WJ-08 manifest declaring the exact applicable station, physical-interface and
load-case cells for each criterion. The empty evidence bundle contains zero
producer records; it is not used as proof that coverage is complete.

The current full-frame input manifest is pinned to
`led-clearance-2x6-runner-seated-blocks-v1`, but states that fresh full-frame
demands, a complete mechanical contact/attachment model and selected
structural hardware are unavailable. Its six load-case records are applied
inputs only. Those facts keep dynamic resistance rows pending.

The planning coverage file also pins `criteria-method-map.md` to
`1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80`; the
current file hashes to
`2ab30c154d75306cb83c88fdde98f7af8082b3c57089a9fdf587c5b3b9818182`.
This is a source-integrity blocker, separate from the absent expected scopes,
fresh demands and current resistance evidence. Neither file was changed for
this attempt.

The safe resolution is to preserve the frozen coverage file and create a new,
versioned source-reconciliation artifact that records both hashes, reviews the
actual method-map content against the intended scope, and is explicitly
reviewed by the coordinator. A later expectation/coverage overlay can bind the
current method-map hash only when it also binds that reconciliation artifact
and rechecks the affected methods. Do not silently rewrite the old pin or
transfer prior criterion evidence. Until that review exists, the mismatch
remains blocking.

## Evidence contract

The expectation manifest is a separate input from producer evidence. Its
source bindings must point at the fixed criteria register, planning register,
candidate authority, current full-frame manifest and method map. Each scope
cell names its station, interface, case and/or other entity; its identifiers
must resolve through JSON pointers into hash-verified independent source
manifests. Producer-provided `expected_coverage` is rejected.

An applicable expectation cannot have an empty scope list. A cell without a
case must state why the check is static; the aggregator does not impose a load
case on static identity or geometry checks. Case-based evidence must bind a
fresh simultaneous demand source whose JSON pointer resolves to the exact case
record and wrench, the exact governing case, a signed force and moment vector,
and units. Each evaluated row must bind candidate and revision,
method ID/version/scope, source hashes, finite result and limit, matching
units, comparison, governing mode and known limits.

Producer states use the plan vocabulary: `unverified`, `failed`,
`passed_under_recorded_assumptions`, and `not_applicable_with_reason`. The
aggregate maps those to `pending`, `failed`, `conditional_pass`, or a justified
`not_applicable_with_reason`. N/A requires a source-backed reason, named
replacement criteria, and preserved obligations that the replacements cover.
Every aggregate keeps engineering completion and all release flags false.

The positive tests use an explicit
`TEST_ONLY_NOT_ENGINEERING_EVIDENCE` marker and assert that synthetic
conditional passes never set completion or release flags. These values are
mechanics-of-the-aggregator fixtures only.

## Run and next consumer

Run the current inventory with:

```sh
python3 scripts/wood_joint_wj08_criteria.py \
  --bootstrap-current \
  --output-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-criteria-aggregator-attempt01
```

For a future evidence bundle, call the script with `--criteria`, `--coverage`,
`--candidate`, `--frame-manifest`, `--expectations`, `--evidence`, and `--output`.
The next consumer is queue task **T11, “Resolve exact 47-criterion register.”**
It can use this interface after independent WJ-07/WJ-08 expected-scope inputs
and required WJ-09 current demand records arrive; rows that need hardware or
cost data also require WJ-10 sources. This artifact itself closes no criterion.

## Files

- `expected-coverage.json`: independent-scope contract; every current row is
  explicitly unresolved.
- `empty-evidence.json`: current producer bundle with no records.
- `current-aggregate.json`: reproducible 47-row pending inventory and hashes.
- `input-pins.json`: current authority/readiness inventory and source hashes.
- `sha256.json`: terminal hashes for this attempt's code, tests, inputs and
  generated artifacts.
