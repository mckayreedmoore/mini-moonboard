# Selected working set

This is the selected screw-and-bracket floor-runner baseline. The separate
[wood-joint development lane](wood-joints-mvp/README.md) is also active; it
does not replace this authority or inherit its passes. Earlier options remain
available in the [design-history catalog](history/design-history.md) and viewer.

## Open these first

| Role | Path |
| --- | --- |
| Machine authority | [`current-candidate.json`](../current-candidate.json) |
| Human constraints | [`AGENTS.md`](../AGENTS.md) |
| Shop packet | [`floor-flush-shop-checklist.md`](floor-flush-shop-checklist.md), [`floor-flush-assembly-guide.md`](floor-flush-assembly-guide.md), [`floor-flush-construction/`](floor-flush-construction/), [`floor-flush-width-option.md`](floor-flush-width-option.md); kerf-right sheets in [`floor-flush-construction-kerf-right/`](floor-flush-construction-kerf-right/); later insert option [`screw-repair-inserts.md`](screw-repair-inserts.md) |
| Evidence | [`floor-runner-mvp-master-plan.md`](floor-runner-mvp-master-plan.md), [`floor-runner-mvp-criteria.md`](floor-runner-mvp-criteria.md), [`floor-runner-mvp-evidence.json`](floor-runner-mvp-evidence.json) |
| Frame | `mini_moonboard/compact_floor_flush_frame.py` (wrapper over preserved taper/recess modules; do not unroll unless geometry changes) |
| Viewer | `site/hybrid/compact-floor-flush-development/`; the 4×8 kerf variant is `site/hybrid/compact-floor-flush-kerf-right/` |
| Six-case archives | `fea/results/floor-runner-mvp/` |
| Geometry snapshot named in authority | `fea/results/clear-space-floorflush/a12-left/geometry.json` |

Start at [docs/README.md](README.md) if you are building. Older studies are in
[history/](history/).

## Outside this baseline's reading path

- `site/hybrid/` other than the two selected plywood-width variants
- `exports/` historical candidate folders
- `fea/generated/` and `fea/results/` other than the two trees above
- [docs/history/](history/) (older studies)
- Documents named `current-*` except those listed in `current-candidate.json`

This is a reading guide, not a deletion or sparse-checkout list. The selected
model imports earlier geometry modules, and evidence can reference ignored
generated files. Preserve historical viewer assets, inherited code, saved
results and other agents' work. See the
[cleanup evaluation](repository-cleanup-evaluation-2026-09-28.md) before moving
or pruning files. No Git history rewrite is needed.

## Next geometry change

If the selected frame changes, write a complete selected-module contract
(inventory, bolts, angles, datums) rather than another `__getattr__` overlay.
Keep the taper and spliced modules as imports of record.
