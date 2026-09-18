# Selected working set

This is the live floor-runner lane. Everything else is preserved evidence.
It does not rewrite git history or move archives to git-lfs.

## Open these first

| Role | Path |
| --- | --- |
| Machine authority | [`current-candidate.json`](../current-candidate.json) |
| Human constraints | [`AGENTS.md`](../AGENTS.md) |
| Shop packet | [`floor-flush-shop-checklist.md`](floor-flush-shop-checklist.md), [`floor-flush-assembly-guide.md`](floor-flush-assembly-guide.md), [`floor-flush-construction/`](floor-flush-construction/) |
| Evidence | [`floor-runner-mvp-master-plan.md`](floor-runner-mvp-master-plan.md), [`floor-runner-mvp-criteria.md`](floor-runner-mvp-criteria.md), [`floor-runner-mvp-evidence.json`](floor-runner-mvp-evidence.json) |
| Frame | `mini_moonboard/compact_floor_flush_frame.py` (wrapper over preserved taper/recess modules; do not unroll unless geometry changes) |
| Viewer | `site/hybrid/compact-floor-flush-development/` |
| Six-case archives | `fea/results/floor-runner-mvp/` |
| Geometry snapshot named in authority | `fea/results/clear-space-floorflush/a12-left/geometry.json` |

## Safe to ignore while building this candidate

- `site/hybrid/` other than `compact-floor-flush-development`
- `exports/` historical candidate folders
- `fea/generated/` and `fea/results/` other than the two trees above
- Unselected `docs/*-development*.md` packages
- Documents named `current-*` except those listed in `current-candidate.json`

Optional git sparse-checkout of that list is a local convenience. Do not
`git lfs migrate` existing history as a prerequisite to shop work.

## Next geometry change

If the selected frame changes, write a complete selected-module contract
(inventory, bolts, angles, datums) rather than another `__getattr__` overlay.
Keep the taper and spliced modules as imports of record.
