# Current-frame conditional material-frame coverage — attempt03

## Finding and repair

Attempt02 bound each block case ID to its radial source axis, material `R`
vector, and CalculiX radial orientation point. Its independent review found
that `tangential_axis_local_name` still passed through unchecked: changing the
`ring_R_on_X` case label from `T` to `X` while leaving vectors intact passed.
Attempt03 validates the complementary local-axis name for both cases:
`ring_R_on_X` names `T`, and `ring_R_on_T` names `X`.

The tangential local-axis name identifies an axis without fixing its sign. The
signed material `T` vector must be sign-equivalent to that named source axis,
and the material frame must remain right-handed (`T = L × R`). Thus the
`ring_R_on_T` case names local axis `X` while its signed material `T` vector
points along `−X`. The output preserves both the positive source-axis vector
and the signed material `T` vector so that distinction remains inspectable.
The source basis is the pinned block material-frame map
([SHA-256](source-pins.json)
`8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480`).

The producer pins the attempt02 independent review
([report](../current-frame-material-frame-coverage-attempt02-independent-review-2026-09-28/report.md),
SHA-256 `a84586a9dbfd38cea10701fa68e158acc8675c261d436c9d8fdf45fec895d1fd`)
and carries the attempt01 radial-axis review forward
([report](../current-frame-material-frame-coverage-attempt01-independent-review-2026-09-28/report.md),
SHA-256 `254aeb9a09447d10c461e187b8c92210f05dd793582f621d28cee2e821b0e405`).
Both prior attempts and both review records remain unchanged.

## Source boundary

The output is a conditional frame-coverage record for the exact attempt04
inventory: 20 frame timbers, 24 connector blocks, and six unresolved plywood
panels. It authenticates seven attempt02/review files and all 61 files in
attempt02's inherited lineage, for 68 files total. The inherited lineage
includes the attempt01 producer, tests, packet, radial-axis review, four
original JSON inputs, and all 50 exact STEP bodies. The block map, including
the sign convention above, is hash-pinned in the inherited source list.

All material properties, product assignments, solver body/element/node/DOF
IDs, and panel orientation/material fields remain null. Readiness, acceptance,
native execution, and release flags remain false. This record does not create
a mesh or mechanics model and does not establish joint response or candidate
acceptance.

## Reproduction

Run from the repository root. `--write` creates only `coverage.json` and
`source-pins.json` and refuses to replace existing files.

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
