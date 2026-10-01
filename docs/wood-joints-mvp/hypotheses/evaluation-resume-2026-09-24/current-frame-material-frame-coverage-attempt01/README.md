# Current-frame conditional material-frame coverage — attempt01

## Result

This offline packet joins the existing conditional orientation scenarios to
the exact 50-body current-revision STEP inventory: 20 frame timbers, 24
connector blocks, and six plywood panels. It carries the source grain/frame
directions for the 44 timber/block bodies and both recorded transverse
orientation cases for each block. The six plywood panels remain unresolved
because product, sheet identity, layup, and strength-axis evidence are absent.

The coverage record is
[`coverage.json`](coverage.json), with all four JSON source hashes and the 50
exact STEP file hashes in [`source-pins.json`](source-pins.json). Its record
SHA-256 is
`067764e877a7c419ae1bab1bea285c0d8a329ff8053ff29633128fd12c584d2d`.

The source JSON pins are:

| Input | SHA-256 |
| --- | --- |
| Current attempt04 manifest | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| Exact 50-body STEP descriptor | `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420` |
| 20 frame-timber orientation map | `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` |
| 24 connector-block orientation map | `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480` |

## Source and frame checks

The producer authenticates those four JSON files, hashes all 50 STEP files,
and compares IDs, kinds, paths, file hashes, sizes, shape summaries, and source
shape fingerprints between the attempt04 manifest and the STEP descriptor. It
requires exact identity joins for the 20 timber and 24 block scenarios. It
checks frame orthogonality and handedness, reconstructs each timber grain
vector from its local frame components, and validates both `ring_R_on_X` and
`ring_R_on_T` scenarios for every block. The block map's three documented
frame construction methods are retained as source lineage.

These are conditional source orientation scenarios, not observations of
delivered boards. The frame-timber map leaves growth-ring orientation
unresolved. All entries keep density, grade, species group, elastic properties,
material IDs, and solver body/element/node/DOF IDs null. Readiness, acceptance,
native execution, and release flags remain false. This packet does not produce
a mesh or mechanics model; the separate T09 mesh source audit records that the
available patch mesh contains only three of the 50 current wood identities.

## Reproduction

Run from the repository root. The write command is exclusive and creates only
`coverage.json` and `source-pins.json` in this new attempt directory.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/wood_joint_current_frame_material_frame_coverage_attempt01.py \
  --repo-root . \
  --attempt-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-material-frame-coverage-attempt01 \
  --write

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/wood_joint_current_frame_material_frame_coverage_attempt01.py \
  --repo-root . \
  --attempt-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-material-frame-coverage-attempt01 \
  --verify

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_wood_joint_current_frame_material_frame_coverage_attempt01.py

sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-material-frame-coverage-attempt01/SHA256SUMS
```
