# Mini MoonBoard DIY frame

Engineering models, calculations, viewers and conditional shop documents for
a Mini MoonBoard-sized climbing wall. This independent project is not affiliated
with or endorsed by Moon Climbing.

## Main development: Compact bolted frame

Start at the **[development summary and revision map](docs/bolted-frame-development/README.md)**.
It identifies the current geometry, matching nominal shop records, applicable
numerical evidence and remaining work.

The current geometry is **`eoere-raised-kicker-screws-v1`**:
[open the current viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-kicker-clearance-frame-development&view=rear).
Its optional extra grid remains off and unofficial. The
[checked revision index](docs/bolted-frame-development/development-revisions.json)
separates this geometry and its matching shop plan from the preceding
six-case numerical evidence. Selected bolt lengths override the viewer hardware.
Actual hardware-fit, installation and joint-strength holds remain. No fabrication or climbing
release is established.

| Need | Start here |
| --- | --- |
| Model, shop records and next actions | [Main development entry](docs/bolted-frame-development/README.md) |
| Detailed evidence and task dispositions | [Development ledger](docs/wood-joints-mvp/completion-ledger.md#build-package-completion) |
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

Open [the local current-development viewer](http://localhost:8767/index.html?model=eoere-kicker-clearance-frame-development&view=rear).
Required ignored inputs stay active; follow the documented recovery workflow
before reproducing or archiving evidence.
