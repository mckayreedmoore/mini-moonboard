# Independent review: T09 conditional material-frame coverage attempt01

Reviewed 2026-09-28 against candidate `compact-floor-flush-wood-joints-development`, revision `led-clearance-2x6-runner-seated-blocks-v1`.

The frozen record verifies as conditional source coverage for 50 current STEP bodies: 20 frame timbers, 24 connector blocks, and six unresolved plywood panels. Four JSON source pins and all 50 STEP exports are authenticated (54 files total). Manifest-to-descriptor joins compare member ID, kind, path, hash, size, shape-summary hash, and source-shape fingerprint; actual STEP hashes and sizes are rechecked. All three documented block-frame methods occur: 15 saved proper-rigid transforms, 8 global-axis `Solid.makeBox` frames, and 1 pinned WJ04/G7 frame.

The 20 timber and 24 block source bases are orthonormal and right-handed. Timber grain is reconstructed from source-frame components. Each block retains two right-handed grain/transverse frames. The pinned map’s 48 scenario IDs and radial axes agree with X/T as named. All six panels remain unresolved. Material properties and solver identity fields are null; readiness, acceptance, native-execution, and release flags are false. The packet makes no delivered-stock, mesh, mechanics, or release claim.

## Finding: block transverse case names are not bound to their radial axes

`_check_block_row()` checks that both IDs are present and that each frame is orthonormal, right-handed, and aligned with grain. It does not check `radial_axis_local_name` or that `ring_R_on_X` has radial R along source X and `ring_R_on_T` has R along source T. The scenario test checks the IDs and handedness but not this association. Swapping the two cases’ `material_axes_global_xyz` and `calculix_orientation_points_global_xyz` while retaining their IDs passes `build_coverage()` and emits the case names with the opposite radial vectors.

This is a validator/mutation-test gap, not a mismatch in the frozen packet: the pinned source currently has all 48 associations correct, and the normal CLI rejects changed source bytes against its fixed hash. The gap matters if an alternate source is repinned or the builder is called with modified documents. The validator should bind each scenario ID to its declared radial local axis and compare that axis to the source frame.

Mutation reproduction (in memory; no files changed): load `source_documents` with `load_pinned_sources(Path.cwd())`, deep-copy them, then for the first `block_map.members` row swap the two cases’ `material_axes_global_xyz` and `calculix_orientation_points_global_xyz` values. Calling `build_coverage(...)` succeeds. It emits `ring_R_on_X` with radial `[0.0, 0.6427876096865394, 0.766044443118978]` and `ring_R_on_T` with radial `[1.0, 0.0, 0.0]` for that row.

## Reproduction

- The documented `--verify` command passed: `PASS_CONDITIONAL_MATERIAL_FRAME_COVERAGE_ONLY`, 54 authenticated files, 50 bodies, record SHA-256 `067764e877a7c419ae1bab1bea285c0d8a329ff8053ff29633128fd12c584d2d`.
- Focused tests passed: `11 passed in 0.18s`.
- `sha256sum -c .../current-frame-material-frame-coverage-attempt01/SHA256SUMS` passed all five entries.
- The `--write` command was not run because the frozen outputs already exist and the documented write mode is exclusive.
