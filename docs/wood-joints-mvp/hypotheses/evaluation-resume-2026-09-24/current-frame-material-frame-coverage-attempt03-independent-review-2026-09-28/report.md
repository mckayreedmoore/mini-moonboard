# Independent review: T09 current-frame material-frame coverage attempt03

Reviewed 2026-09-28 against candidate `compact-floor-flush-wood-joints-development`, revision `led-clearance-2x6-runner-seated-blocks-v1`.

## Disposition

**Pass for conditional source-frame coverage only.** Attempt03 closes attempt02's tangential-axis label-only finding. For each of the 24 blocks, it binds `ring_R_on_X` to source `X` radially and source `T` tangentially, and binds `ring_R_on_T` to source `T` radially and source `X` tangentially. It preserves the positive source tangential axis separately from the signed material `T` vector. The signed vector is sign-equivalent to the complementary source axis and reconstructs as `T = L × R`.

I independently checked all 48 block scenarios against the pinned block map and frozen output. For each case, the radial label, source radial vector, material `R`, and CalculiX radial point agree; the tangential label and positive source-axis vector agree; material `L` agrees with the conditional grain vector; material `T` is sign-equivalent to the complementary source axis; `L × R` equals signed `T`; and both CalculiX orientation points equal `L` and `R`. The source `N/T/X` bases are unit and orthogonal. This includes the `ring_R_on_T` cases where the local tangential axis is `X` while right-handed reconstruction requires signed material `T = −X`.

The inherited attempt01 review had found that case IDs could be retained while swapping the two radial frames. Attempt02 bound each radial case ID to its source axis, material `R`, and CalculiX radial point; its independent review then found the tangential-label gap now repaired by attempt03. Attempt03 pins both prior review reports and the attempt02 producer, tests, packet, source pins, and checksums.

## Inventory and evidence boundary

The emitted revision inventory contains exactly 50 distinct body IDs and matches the manifest and STEP descriptor: 20 frame timbers, 24 candidate blocks, and six unresolved plywood panels. The output retains all six panels as unresolved. Material assignments and solver mappings are null; readiness, acceptance, native-execution, and release flags are false.

This is an orientation-coverage record, not a mesh or mechanics model. It establishes no material properties, solver DOF mapping, joint response, load transfer, criterion disposition, candidate acceptance, fabrication readiness, or release.

## Reproduction and integrity

- Focused attempt03 tests: **6 passed**.
- Documented attempt03 `--verify`: **passed**, 68 authenticated files, 50 bodies, coverage record SHA-256 `ddc32d90ea77e80240c7feee81b65c500f540d4b8d87b958ea94e0961de697aa`.
- Ruff on the attempt03 producer and tests: **passed**.
- Attempt03 `SHA256SUMS`: all five entries **passed**.
- Independent lineage audit: all 68 unique source-lineage paths matched their pinned byte sizes and SHA-256 values; the set comprises seven authenticated attempt02/review artifacts plus 61 inherited attempt01/review and source files.
- Independent inventory and axis audit: **50/50** body identities matched; **48/48** block scenarios passed the checks above.

The following hashes bind the exact attempt03 bytes reviewed:

| Artifact | SHA-256 |
| --- | --- |
| `scripts/wood_joint_current_frame_material_frame_coverage_attempt03.py` | `4d857850d4199f59256763dff15065ea31bb7ec115c840c46c0692a35b2fa91c` |
| `tests/test_wood_joint_current_frame_material_frame_coverage_attempt03.py` | `0c80ed67b0535638d8d17bc272faf1d0415b8ad48c226b4cc26fe6ca88a5b03e` |
| attempt03 `README.md` | `880d99bd125da08bab5f8d177877fd5be4ec825593ef28a42f3ea164b0cb81ce` |
| attempt03 `coverage.json` | `530871fd917e6566e508f69b75282674781b11eae29aaf37afb0675cf906bc3d` |
| attempt03 `source-pins.json` | `4ed640f0c0051ce29c20af2818ec173e62afded072c7d9a61e9cc647c4fc9ba3` |
| attempt03 `SHA256SUMS` | `59913f8e69a8a4a264dfb68b5a576a13ab55d6a8c194c818792e03c77adea881` |

The source-pins file binds 68 exact lineage paths and includes the prior review hashes: attempt01 `254aeb9a09447d10c461e187b8c92210f05dd793582f621d28cee2e821b0e405` and attempt02 `a84586a9dbfd38cea10701fa68e158acc8675c261d436c9d8fdf45fec895d1fd`. Its full-file hash above binds that lineage inventory. The frozen source-map hashes are: block map `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480`, manifest `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`, STEP descriptor `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420`, and timber map `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409`.

Commands run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/wood_joint_current_frame_material_frame_coverage_attempt03.py \
  --repo-root . \
  --attempt-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-material-frame-coverage-attempt03 \
  --verify

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_wood_joint_current_frame_material_frame_coverage_attempt03.py

.venv/bin/ruff check \
  scripts/wood_joint_current_frame_material_frame_coverage_attempt03.py \
  tests/test_wood_joint_current_frame_material_frame_coverage_attempt03.py

sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-material-frame-coverage-attempt03/SHA256SUMS
```
