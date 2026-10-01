# Attempt04 independent test-coverage review

Read-only review of maintained public behavior and the fail-closed method boundary. No earlier review reports were consulted. No source or tests were changed; no solver or Docker was run.

## Reviewed pins

The attempt04 packet pins match the maintained working-tree files:

- `mini_moonboard/nds_2024_group_action.py`: `d0d8cf193c9fb26206e459e749c176f0ace5b41bb472ffc24217d8a5942874f6`
- `tests/test_nds_2024_group_action.py`: `c0137a5144e135e2bac3a4eb6861e0e85d10750b0b3471eb4fc55df13222c3f2`
- `docs/wood-joints-mvp/criteria-method-map.md`: `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`
- Patch: `df4268c1fb255f228ff1da58865a6085efc342509b16d6c1c5cc3951f233ba1a`; `source-pins.json`: `dcf5fd27defe0c50f1db0f46eea079f80e05a3d0b303bc033a3b970c9824f0ee`.

The `base/` source and test snapshots match the attempt03 base pins recorded in the packet. The maintained focused suite passes: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py` → **34 passed**.

## Ranked finding

**P2 — vector norm overflow can bypass the alignment gate.** Tests cover NaN and derived coordinate overflow, but do not cover a finite three-vector whose norm overflows. In `_unit` ([source](/home/mckay-linux/repos/mini-moonboard/mini_moonboard/nds_2024_group_action.py:155)), dividing finite components by an infinite norm produces `(0, 0, 0)`. The load path then compares that zero vector to the row axis at lines 407–412; its cross norm is zero, so a materially misaligned resultant is accepted. The same normalization is used for member grain at line 322, which can select the parallel-to-grain area branch for a nonparallel vector.

Reproduction with the maintained public function: set `load_case.lateral_resultant_xyz_lbf` to `[1.7e308, 1.7e308, 0.0]` in the standard synthetic `payload()` fixture and compute its expected canonical digest. The result is `calculated_method_only` with `cg ≈ 0.9766839378`; this 45° load should return `pending` because it is not aligned with the row. A matching test should assert fail-closed behavior for overflowing resultant and grain norms.

The existing tests meaningfully exercise published Cg answers, supported geometry and area paths, source and digest mismatches, and four-or-more-member rejection through both public APIs. The uncovered normalization edge means the focused test suite does not yet establish the numeric fail-closed boundary for every normalized public input vector.
