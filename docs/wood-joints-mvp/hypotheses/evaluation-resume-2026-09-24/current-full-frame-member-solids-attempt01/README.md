# Current full-frame member solids — attempt01

## Result

This package replays the owner-reviewed
`led-clearance-2x6-runner-seated-blocks-v1` geometry and exports the 50 current
timber, plywood-panel, and connector-block solids as individual STEP files.
The files and manifest are staged together and promoted as `bundle/`. It
preserves the separate selected baseline `compact-floor-flush-development`.

The bundle covers 20 timber members, six panels, and 24 candidate blocks. The
producer selects the 26 inventory-named wood and panel members from the larger
source assembly, then applies current finished-host and panel-replacement
geometry. It binds the current candidate authority, reviewed scene and report,
source inventory, attempt02 full-frame manifest, all project modules loaded by
the geometry replay, and in-repository files read through `Path.read_text` or
`Path.read_bytes`. Each body has a source geometry fingerprint, a rounded
summary fingerprint, a STEP file hash, and a readback summary. STEP round trips
are checked for validity, one-solid topology, bounds, volume, and symmetric
difference volume.

The first `--write` stopped before STEP export because the source assembly also
contains non-inventory hardware and overlay bodies. The source selection now
requires each of the 26 inventory IDs exactly once and filters the unrelated
bodies out of this export. No files were promoted by the failed run.

## Limits

This closes exact member-geometry availability only. The 26 source members
retain source-inventory identity; the 24 blocks use the current finished
candidate map. The shape-summary hash is a rounded geometric cross-check, not
a kernel-canonical BRep hash. Source hashes and STEP hashes bind the exported
files to the replayed inputs.

The bundle does not provide per-member grain/R/T assignments, received-stock
properties, selected hardware, active contact or attachment mechanics, solver
mappings, current demands, or resistance checks. No mesh or native solve is
included. Acceptance, fabrication, and climbing-release flags remain false.

## Reproduction

From the repository root:

```sh
solids_dir=docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/
solids_dir+=current-full-frame-member-solids-attempt01
uv run --no-sync python "$solids_dir/produce.py" --verify
```

`--write` creates `bundle/current-full-frame-member-solids.json` and the 50
files under `bundle/members/` once; it refuses to overwrite an existing
artifact. It stages the complete bundle first, then atomically promotes the
containing directory. `--verify` replays the geometry, checks every pinned
input and hash, and compares every STEP readback against the replayed solid.
