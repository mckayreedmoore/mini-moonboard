# Mini MoonBoard DIY frame

Engineering models, calculations, viewers and conditional shop documents for
a Mini MoonBoard-sized climbing wall. This independent project is not affiliated
with or endorsed by Moon Climbing.

## Main development: Compact bolted frame

Start at the **[development summary and revision map](docs/bolted-frame-development/README.md)**.
It identifies the current geometry, matching nominal shop records, applicable
numerical evidence and remaining work.

The current geometry is **`eoere-local-front-bolt-moves-v4`**:
[open the current viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-current-frame-development&view=rear).
The owner-directed model removes the two outboard knees, two leg packers and
508-mm top-rail extension. It has 20 sawn members, four trimmed nominal ¾-inch
plywood cleats at the lower header corners, 24 angles, 92 bolt stacks,
184 washers and 26 factory spacers. The 32 enclosed LED passages and 66 Hillman
axes remain. The lower front bolts now sit60mm above the floor, with upper bolts at100mm. Their own six-case references fall to0.937 wood bearing and0.893 bolt axial/bending. Cleat-row and upper-bolt-size trials were rejected for incompatible factory holes and edge distances. Its geometry clears nominal occupancy. The completed ideal-bond
investigation reaches1.066 nominal or1.129 with the thickness allowance on
the declared four-host floor basis; bolt and timber references also exceed1.0.
The full frame does not pass, and no preceding strength pass transfers.
The completed 102-bolt/extended-top evaluation remains preserved within its own
geometry. Panel/Hillman strength remains deferred and unresolved. Actual stock,
hardware, fit and floor are unobserved; no fabrication or climbing release.

| Need | Start here |
| --- | --- |
| Model, shop records and next actions | [Main development entry](docs/bolted-frame-development/README.md) |
| Current review and preserved shop instructions | [Builder plan](docs/bolted-frame-development/builder-plan.md) |
| Detailed evidence and task dispositions | [Development ledger](docs/wood-joints-mvp/completion-ledger.md#engineering-closure-beyond-the-assessment) |
| Preserved selected baseline | [Baseline reference packet](docs/README.md) · [machine authority](current-candidate.json) |
| Earlier options, failures and lessons | [Design-history catalog](docs/history/design-history.md) |
| Repository organization and evidence recovery | [Cleanup record](docs/repository-cleanup-evaluation-2026-09-28.md) |

## Selected baseline and history

The selected screw-and-bracket baseline remains `compact-floor-flush-development`
under [current-candidate.json](current-candidate.json). Its
[working set](docs/selected-working-set.md) and conditional shop/evidence packet
stay preserved. Its passes do not qualify the compact bolted development frame.

Earlier Eoere, HL35, thin-frame and wood-joint studies remain accessible through
the history catalog and [full viewer collection](https://mckayreedmoore.github.io/mini-moonboard/).
The viewer's no-query default remains the selected baseline; use the explicit
current-development link above. Original proposal contracts keep their own
revision identities.

## Contributor setup

Work on `master` and coordinate file ownership and publication with other agents.
Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before changing
geometry, evidence or archived files.

```sh
uv sync --locked
uv run python -m http.server 8767 --directory site
```

Open [the local current-development viewer](http://localhost:8767/index.html?model=eoere-current-frame-development&view=rear).
Required ignored inputs stay active; follow the documented recovery workflow
before reproducing or archiving evidence.
