# Attempt04 correctness review

Scope: read-only correctness review of attempt04's patch and maintained implementation. No solver, Docker, candidate inputs, or candidate status changes were used.

## Hashes checked

| Artifact | SHA-256 | Result |
| --- | --- | --- |
| `attempt04.patch` | `df4268c1fb255f228ff1da58865a6085efc342509b16d6c1c5cc3951f233ba1a` | Matches `source-pins.json`; reverse `git apply --check` succeeds against maintained files |
| `mini_moonboard/nds_2024_group_action.py` | `d0d8cf193c9fb26206e459e749c176f0ace5b41bb472ffc24217d8a5942874f6` | Matches maintained pin |
| `tests/test_nds_2024_group_action.py` | `c0137a5144e135e2bac3a4eb6861e0e85d10750b0b3471eb4fc55df13222c3f2` | Matches maintained pin |
| `docs/wood-joints-mvp/criteria-method-map.md` | `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7` | Matches maintained pin |
| `source-pins.json` | `dcf5fd27defe0c50f1db0f46eea079f80e05a3d0b303bc033a3b970c9824f0ee` | Read and internally consistent with maintained hashes |
| `validation.json` | `ac92545e0b530924b275db13432a376f3908c0dfd2b368b7c2ea99187366fb7e` | Read; recorded patch and test-output hashes match |
| `offline-test-output.txt` | `73240cdaab3350e1db617e842b82ef4ecec3d2cdf4a6ae90cb8af443127e297b` | Matches validation pin; reports 34 passed |
| Base source snapshot | `8dac7e4b749d7b9253b5a4801c169d759e486030aac719b8c55dae80d9606488` | Matches base pin |
| Base test snapshot | `5a63579be46d795068e44f77244366d6d2bc411d574eb52e5fe9af9ccf9d0365` | Matches base pin |
| Base method-map in `HEAD` | `2ab30c154d75306cb83c88fdde98f7af8082b3c57089a9fdf587c5b3b9818182` | Matches base pin |

## Finding

**P2 — Direction-vector normalization can silently accept an invalid direction.** In `_unit` at `mini_moonboard/nds_2024_group_action.py:159-161`, a finite vector whose Euclidean norm overflows to infinity is divided by infinity and becomes `(0, 0, 0)`. The downstream alignment checks then treat its cross product as zero: a load direction can be accepted as aligned at lines 407-412, and a grain direction can be classified as parallel at lines 319-324. This returns a method factor for input that is outside the stated aligned-load / parallel-grain scope rather than returning `pending`.

Reproduction using the existing synthetic payload helper, recomputing its canonical digest and supplying matching expected bindings:

- Set `load_case.lateral_resultant_xyz_lbf` to `[1.7e308, 1.7e308, 1.7e308]`. The evaluator returns `calculated_method_only`, `cg = 0.9766839378238344`, although this resultant is not aligned with the x-axis row.
- Alternatively, set `members.main.grain_axis_xyz` to the same vector. The evaluator again returns `calculated_method_only`, using the parallel-grain area path even though the supplied axis is diagonal to the load.

All components are finite and the record digest and source bindings match, so this reaches the normalization path. Guard normalization against a non-finite or zero resulting norm (or normalize by a scale-safe method) before using a vector in direction checks.
