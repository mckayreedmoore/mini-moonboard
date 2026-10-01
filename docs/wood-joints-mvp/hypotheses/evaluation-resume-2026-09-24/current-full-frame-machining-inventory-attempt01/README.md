# Current full-frame machining coverage — attempt01

This packet reconciles the reviewed `led-clearance-2x6-runner-seated-blocks-v1`
full-frame manifest and finished STEP bundle against the earlier timber/block
cut inventory. It confirms identity for all 50 members and exact STEP files.
The older cut inventory has matching rows for 44 members (20 timbers and 24
blocks); all six current plywood panels have no row in that inventory.

The packet also enumerates the 92 candidate bolt axes, 12 retained frame-bolt
axes, and 66 panel/kicker screw axes. It records their current member
associations and preserves modeled shaft/occupancy fields where present. It
does not turn those envelopes into cutter dimensions or assert that an axis
already corresponds to a physical hole.

`all_machining_represented` remains **false** and pending. The 44 existing rows
already say they are not complete operation schedules. Six panel operation
inventories are absent. Authoritative bolt-hole and preparatory-hole dimensions,
local section cuts, tolerances, setups, and reviewed cut tickets remain open as
listed in `inventory.json`. No CAD was replayed, no geometry or source artifact
was changed, and no cutting, drilling, fabrication, structural, or climbing
release is made.

## Reproduction

From the repository root:

```sh
.venv/bin/python -B scripts/build_current_full_frame_machining_inventory_attempt01.py --verify
.venv/bin/pytest -q -p no:cacheprovider tests/test_current_full_frame_machining_inventory_attempt01.py
```

The producer only reads pinned JSON, the pinned prior README, and the 50
existing STEP files. `--write` creates `inventory.json` once and refuses to
overwrite it. It never invokes CAD or produces shop instructions.

From the repository root, verify the frozen packet files with:

```sh
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-machining-inventory-attempt01/SHA256SUMS
```
