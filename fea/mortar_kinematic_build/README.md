# Separate kinematic observer build

This directory owns new v2 build/cube evidence only. It does not replace the
unmodified upstream baseline or v1 observer sources, images, binaries or reports.
The full-frame observer run remains on hold pending cube replay and review.

`python -m fea.mortar_kinematic_build.build` verifies immutable upstream image
`sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0`,
snapshots the v1 and v2 generators and all build support, and builds with two
workers under a 300-second cap. The distinct tag is
`mini-moonboard-fea:ccx-kinematic-observer-2.21-v1`; the new binary is
`/usr/local/bin/ccx-kinematic-observer-2.21`. Existing tags are not overwritten.

The build manifest verifies the entire original 1176-file source inventory,
allowing only the two exact declared patched C files. Both patch generators,
the patched files, original binaries, linked libraries and compiler Makefile
are hash-bound; unchanged original binaries and libraries must remain intact.
The inherited baseline manifest records compiler and original-source details.

`python -m fea.mortar_kinematic_build.compare_cube BUILD_DIRECTORY` resolves the
successful build's immutable ID and verifies its actual manifest/binaries
before four bounded runs: two unchanged archived sliding cube decks, each with
unmodified upstream and the new observer. All printed displacement/reaction
coverage and values, STA histories and existing cube global checks are compared
against the retained original archive. Runs and source snapshots go to a unique
directory. None of these checks is a physical frame/joint capacity approval.

`uv run pytest tests/test_mortar_kinematic_build.py` tests failed-build exit
propagation and exact source-inventory rejection without Docker.

## Completed bounded evidence

`build-sxz5mfwe` completed successfully; immutable new image:
`sha256:8e84d8ad546cd98a861ceba3ccbf4c486b88f38a8b7e4c45f7784ace4cea21e1`.
`cube-9bidnnnr` preserves all four new runs. Both schedules exactly match the
archived printed displacement/reaction fields and STA histories, and pass the
existing global cube checks. The v2 reader checked all 28/45 calls, including
8/16 accepted coupling states, without checker or tolerance changes.

`report.json` binds the successful build, both generators, source/compiler
support, all raw comparison evidence and two complete replay artifacts in
`replay-lj6k7w_c`. The original publication and replay directory remain retained
as `initial-report.json` and `replay-cube-9bidnnnr`; the current publication uses
repository-relative references so evidence can be checked in another checkout.
The publication regression rehashes all four raw runs
and recomputes both complete replay artifacts. Original upstream/v1 evidence
is untouched. Independent segmentation and physical frame/floor/joint capacity
are not established; the full-frame run is still held for runner qualification.

Independent correctness, testing, and architecture/publication reviews found
no substantial remaining findings after portable references and default-CI test
collection were fixed. The focused patch, replay, and build/publication suite
passed 50 tests, including replay from a relocated checkout without Docker.
