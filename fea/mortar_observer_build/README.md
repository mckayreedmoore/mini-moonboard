# Separate diagnostic observer build

This is the build path for the [logging-only source patch](../mortar_observer/README.md),
not a validated solver or a new frame result. It uses the previously verified
unmodified upstream image by immutable ID and preserves both installed original
solver binaries. No packages, compiler flags or upstream Makefile are changed.

```sh
uv run python -m fea.mortar_observer_build.build
uv run python -m fea.mortar_observer_build.compare_cube
uv run python -m fea.mortar_observer_build.publish
uv run pytest tests/test_mortar_observer_patch.py tests/test_mortar_observer_build.py
```

The launcher refuses conflicting base/output tags. It creates a unique evidence
directory containing the exact Docker context, launch script, log and result.
The build is bounded to 300 seconds with two compiler workers. Only the two
patched source files are copied into the new image's build tree; all original
archive source hashes are checked against the upstream manifest, with precisely
those two declared exceptions. Original binaries, libraries and compiler
configuration are checked unchanged. The observer's resolved libraries must
also match that preserved inventory.

The observer executable is separately named `/usr/local/bin/ccx-observer-2.21`.
Its image must undergo unchanged small-cube output/history comparisons and
strict diagnostic replay before any full-frame diagnostic run. Compilation or
source insertion checks alone do not qualify its records, local contact law,
joint demands or the board's physical resistance.

## Retained small-cube evidence

The [publication](report.json) binds the successful build, four raw runs
(two cube decks × upstream/observer), and strict replay outputs. All printed
displacements/forces and accepted histories match the unmodified upstream
solver and original archive. Replay covers 28/45 contact calls, including
8/16 accepted increments and 72/144 eligible accepted node observations.
Neither cube has an accepted iteration-limit flag override.

Maximum absolute internal normal residual is approximately 2.603e-9 in both
cases; maximum absolute tangent component is 3.205e-6 / 1.604e-6. These are
reported internal weighted quantities, not millimetres of physical floor slip
or newly chosen acceptance thresholds. Tiny negative regularized openings and
positive friction excess remain in the reports; they are not clamped to zero.

Coverage is against the observer's declared inventory and accepted STA history.
The reader reconstructs weighted multipliers from raw arrays, but not the
full gap/displacement kinematics or contact segmentation. A full-frame run
still needs its launched deck's independent node/pair inventory and provenance
bound to the stream. No redesigned-frame result is provided by these cubes.

An independent test review found that the publication script could accept an
empty/incomplete run list. It now requires exactly four unique successful
case/binary combinations before writing outputs, with corruption regressions.
The retained solver executions and replay quantities did not change.

Independent numerical/source correctness, testing, and architecture/publication
reviews reported no remaining substantial findings after that fix. The 87
observer patch/replay/build tests passed. This review status applies to the
diagnostic implementation, not a professional structural audit.
