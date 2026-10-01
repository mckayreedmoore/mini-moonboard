# Independent review: T09 current-frame material-frame coverage attempt02

Reviewed 2026-09-28 against candidate `compact-floor-flush-wood-joints-development`, revision `led-clearance-2x6-runner-seated-blocks-v1`.

## Disposition

Attempt02 closes attempt01's reported radial-axis binding finding. For every one of 24 candidate blocks, the producer binds `ring_R_on_X` to local source axis `X` and `ring_R_on_T` to local source axis `T`, then checks both the material `R` vector and the CalculiX radial orientation point against that named source axis. The mutation that swaps the two valid radial vectors and orientation points while retaining their scenario IDs now fails. The pinned packet reproduces for the exact 50-body input inventory.

One residual validation gap remains: `tangential_axis_local_name` is copied from the source case into the output without being checked against the scenario ID or source axes. Mutating the first case's label from `T` to `X` while leaving its material frame intact passes `build_coverage()` and emits `X`. This does not reopen the reviewed radial-axis finding or reveal a mismatch in the frozen, hash-pinned source map. If the tangential label is meant to function as validated mapping data, validate it against the complementary local axis (or omit it from the checked output) and add a mutation test.

## Integrity and scope

The attempt02 producer authenticates seven attempt01/review artifacts, checks their fixed SHA-256 values and attempt01 packet checksum inventory, then delegates original-input verification to attempt01. It reconstructs attempt01's coverage and source-pins records and compares them byte-for-byte with the frozen packet. The resulting attempt02 source-pins record accounts for 54 original inputs plus seven authenticated attempt01/review artifacts, 61 files total. The attempt02 `SHA256SUMS` entries match the producer, test, README, coverage record, and source-pins record.

The output covers 20 frame timbers, 24 candidate blocks, and six unresolved plywood panels. Material assignments and solver mappings remain null; readiness, acceptance, native execution, and release flags remain false. This is conditional source-orientation coverage only. It does not establish material properties, a complete mesh or mechanics model, a joint response, candidate acceptance, fabrication readiness, or release.

## Reproduction

- Focused tests: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_wood_joint_current_frame_material_frame_coverage_attempt02.py` — **5 passed**.
- Packet verification: documented attempt02 `--verify` command — **PASS**, 61 authenticated files, 50 bodies, record SHA-256 `a47a447f47f95ffbf71be47112cbfffdcb6accf5446d67c4d96d03deee713a71`; all readiness flags false.
- Packet integrity: `sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-material-frame-coverage-attempt02/SHA256SUMS` — **all five entries passed**.
- Lint: `.venv/bin/ruff check scripts/wood_joint_current_frame_material_frame_coverage_attempt02.py tests/test_wood_joint_current_frame_material_frame_coverage_attempt02.py` — **passed**.
- Independent mutation check: swapping valid radial vectors and CalculiX orientation points across the two scenarios while retaining IDs raises `ValueError` for radial-axis disagreement. Changing only `tangential_axis_local_name` from `T` to `X` succeeds and is copied to the output, confirming the residual gap above.
