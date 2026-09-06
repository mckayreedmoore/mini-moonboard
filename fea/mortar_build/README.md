# Separate unmodified CalculiX 2.21 baseline build

This build does not add an observer, change solver contact equations, replace
the packaged solver, or authorize a full-frame analysis. It prepares a known
upstream baseline for a later, separately reviewed instrumentation patch.

The parent image must have ID
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`.
BuildKit needs a local image name rather than a bare image ID, so `build.py`
creates the separate alias `mini-moonboard-fea:base-37671083a88d` directly from
that ID and verifies the final image contains its complete filesystem-layer
prefix. It never changes `mini-moonboard-fea:box-v1`. Existing conflicting alias
or output tags are rejected rather than overwritten.

The [official upstream source](https://www.dhondt.de/ccx_2.21.src.tar.bz2) must
hash to `52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`.
`Makefile.upstream` changes build configuration only: system SPOOLES/ARPACK/
LAPACK paths and modern gfortran's legacy-argument compatibility option.
It compiles the original upstream file lists, does not call the version-rewriting
`date.pl`, and verifies every original archive file is unchanged after building.
Compiler warnings are retained in the build log, not treated as validation.

```sh
uv run python fea/mortar_build/build.py
uv run python -m fea.mortar_build.compare_cube
uv run pytest tests/test_mortar_build.py
```

The build has a 900-second subprocess bound and uses two make workers. Evidence
goes into unique `baseline-*` directories. `/usr/bin/ccx` is checked unchanged
before/after dependency installation; the new binary is separately installed
as `/usr/local/bin/ccx-upstream-2.21`. Its manifest records the source archive,
every original source file, compiler versions, installed package versions,
resolved shared-library hashes, executable hashes and build-support hashes.
Dependency repository versions are recorded, not assumed forever immutable;
the resulting image ID identifies the actual build.

The comparison runs only the two existing archived bottom-supported sliding
cube MORTAR decks (increments 0.25 and 0.125), each with a 60-second bound and
two OpenMP threads. It compares original packaged solver/image, packaged solver
with newly installed libraries, and the new upstream solver. That three-way
split exposes library drift separately from upstream/build differences. Input
bytes are unchanged. Raw outputs, accepted-history equality, maximum printed
U/RF differences from the archived reference and existing external force/moment
checks are retained. Local weak-law validation remains explicitly open.

Do not infer bitwise equivalence or physical correctness from compilation.
Review the actual comparison report before using this image as an observer
baseline. A future observer must be built/tagged separately and compared with
this unmodified build first; no patch or modified binary belongs under its tag.

## Completed baseline

The [published build/comparison manifest](report.json) identifies image
`sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0`.
All six cube executions matched the archived parsed U/RF values exactly and
had identical accepted-increment histories. Existing endpoint global checks
passed. This is printed-output equality on two small cases, not bitwise binary
equivalence or a local-law certificate. Tests replay every retained cube output
against the original archive and bind the build/support/evidence hashes.

The first two failed build attempts are retained: a BuildKit local-image-ID
resolution failure, then a missing `bzip2` extraction dependency. Neither reached
solver compilation. The successful build log, source/compiler/library manifest
and raw cube outputs remain in their uniquely named evidence directories.

### Review fixes and chronology

The reviewed launcher now exits nonzero after persisting a failed Docker build.
Before any comparison solve, it binds the successful build result and manifest
to publication hashes and checks the actual binaries inside the immutable image.
Every solve uses an image ID, never the mutable tag. Six new ID-bound cube runs
again matched the archived U/RF and accepted histories exactly; no rebuild was
needed. `report.json` points to those new runs and retains the original ones.

`pre-review-snapshot/` preserves the original two launcher scripts and original
publication with their original hashes. The successful image was built by that
older build launcher, not by the corrected current script. The new comparison
also contains its exact `compare_cube.launch.py` snapshot. These distinctions
prevent later support fixes from being presented as the source of earlier runs.
