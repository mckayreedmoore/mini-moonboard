# Current group-action method — attempt03 maintained patch

Status: exact reviewed attempt02 fail-closed guard applied to the maintained worktree, with a docstring scope clarification. This packet binds the two-file change and its current bytes for parent and independent review.

The evaluator now returns `pending` with null `Cg`, capacity, and criterion disposition for inputs with four or more total members. Its one-to-three-member method scope remains available for method-only calculation when all existing bindings and checks pass. The official-source review did not resolve four-plus NDS-2024 `Cg` integration; this guard is a conservative method boundary, not proof that aggregate treatment is prohibited. No candidate group result, capacity, or criterion pass is produced.

The exact two-file patch is [`fail-closed-scope.patch`](fail-closed-scope.patch). It replays from the pinned base hashes in `source-pins.json` without fuzz and reproduces the maintained module and test hashes.

Focused validation run after the source patch and docstring clarification:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py
29 passed in 1.38s
```

This validates only the evaluator behavior and tests in this worktree. Three fresh review passes against the final source/test hashes and parent validation remain required. No solver, Docker, current-joint case, candidate capacity, or criterion acceptance is included.
