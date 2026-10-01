# Current-frame conditional material-frame coverage — attempt02

## Finding and repair

Attempt01's independent review found that the block transverse scenario IDs
were not bound to their named radial axes. Its validator accepted orthonormal,
right-handed cases after the `ring_R_on_X` and `ring_R_on_T` radial vectors and
CalculiX orientation points were swapped while IDs remained unchanged. The
finding and reproduction are preserved in the pinned
[attempt01 review](../current-frame-material-frame-coverage-attempt01-independent-review-2026-09-28/report.md)
(SHA-256
`254aeb9a09447d10c461e187b8c92210f05dd793582f621d28cee2e821b0e405`).
Attempt01 and its review remain unchanged.

Attempt02 checks all 48 source cases across 24 blocks and requires
`ring_R_on_X` to name local axis `X` and place both material `R` and the
CalculiX radial orientation point along source `X`. It requires
`ring_R_on_T` to name local axis `T` and place both vectors along source `T`.
The output keeps the scenario ID, `radial_axis_local_name`, source radial
vector, material `R` vector, and all six CalculiX orientation coordinates.
Case order remains X then T for each block.

## Source boundary

The record remains a conditional orientation map for the exact attempt04
inventory: 20 frame timbers, 24 connector blocks, and six unresolved plywood
panels. The producer pins seven attempt01/review files and reauthenticates the
54 original source files (four JSON inputs and 50 exact STEP bodies), for 61
authenticated files total. The pinned attempt01 source record SHA-256 is
`067764e877a7c419ae1bab1bea285c0d8a329ff8053ff29633128fd12c584d2d`; the new
attempt02 record SHA-256 is
`a47a447f47f95ffbf71be47112cbfffdcb6accf5446d67c4d96d03deee713a71`.

Source and output digests, including the attempt01 packet and review, are in
[`source-pins.json`](source-pins.json). The map keeps all material properties,
product assignments, and solver body/element/node/DOF IDs null. The plywood
panels remain unresolved. Readiness, acceptance, native execution, and release
flags remain false; this packet does not create a mesh or mechanics model.

## Reproduction

Run from the repository root. `--write` creates only `coverage.json` and
`source-pins.json` and refuses to replace existing files.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/wood_joint_current_frame_material_frame_coverage_attempt02.py \
  --repo-root . \
  --attempt-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-material-frame-coverage-attempt02 \
  --write

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/wood_joint_current_frame_material_frame_coverage_attempt02.py \
  --repo-root . \
  --attempt-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-material-frame-coverage-attempt02 \
  --verify

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_wood_joint_current_frame_material_frame_coverage_attempt02.py

sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-material-frame-coverage-attempt02/SHA256SUMS
```
