# Attempt07 architecture and integration review — 2026-09-28

**Review result:** no blocking architecture or integration finding in the scoped attempt07 method change.

## Scope and assessment

Reviewed the attempt07 package, its maintained `mini_moonboard/nds_2024_group_action.py` module and focused tests, `criteria-method-map.md`, and the current criteria coverage Markdown/JSON. The change is cohesive: it reuses the module's strict canonical-JSON byte encoder when comparing changed scalar leaves. That closes the package's signed-zero path omission while also preserving JSON type distinctions such as integer `1` versus boolean `true`.

The sensitivity flow remains bounded by the method contract. It validates each scenario through the separately supplied bindings and full-record digest, checks scenario/candidate/group identities, and compares the declared changed paths with the recursively observed paths. Its reported result is explicitly `calculated_method_sensitivity_only`; `capacity` remains null and `criterion_disposition` remains `pending`. The group-factor producer has a narrow method scope and fails closed outside it. The code states that it cannot authenticate the authority of caller-supplied manifests, leaving that trust decision with the coordinator.

The criteria method map names the producer while spelling out its input scope and exclusions. The current coverage status still says there are no candidate group factors or group actions and keeps `additional_group_reduction_sensitivity` pending. This is consistent: a synthetic/table-fixture method result does not satisfy the candidate evidence dependency. No acceptance or candidate-capacity claim leaks into the integration records.

## Findings

None for the reviewed scope.

## Reproducibility and pins

The package's listed terminal hashes match the reviewed README, patch, offline test output, source pins, and validation files. The attempt06 source snapshots match their pinned base digests. Applying `attempt07.patch` with `git apply --check`, then applying it to copies of those pinned snapshots, reproduced the maintained module and test hashes exactly. This confirms an exact replay without fuzzy patch application.

The focused command was reproduced:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py
40 passed in 1.21s
```

The attempt07 package validation and source-pins both bind the current method-map digest; it matches the reviewed `criteria-method-map.md` bytes. The audited module and test files are untracked in the current worktree, so this report binds the exact reviewed working-tree content by SHA-256 rather than a committed blob.

## Limits

This review establishes source/package identity and integration scope only. It does not validate coordinator authority, candidate group inputs, candidate applicability, resistance, demand distribution, or criterion acceptance. No solver or Docker was invoked.
