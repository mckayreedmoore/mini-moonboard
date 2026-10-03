# Mini MoonBoard DIY frame

Engineering models, calculations, viewers and conditional shop documents for
a Mini MoonBoard-sized climbing wall. This is an independent project, not
affiliated with or endorsed by Moon Climbing.

## Active development: bolted wood joints

Start at the [wood-joint development summary](docs/wood-joints-mvp/README.md).
Use the [reviewed WJ24 viewer](https://mckayreedmoore.github.io/mini-moonboard/wood-joints-wj24-viewer.html)
to inspect its recorded geometry. The viewer shows the reviewed basis;
the separate knee-bridge proposal is described in its linked packet.

The [engineering disposition](docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/mvp-joint-disposition.md)
collects completed finite checks, working assumptions and unresolved load
and resistance questions. The conditional model/shop packet is complete
within that scope. All 47 formal criteria remain pending and all eight
release flags remain false.
Current work assesses the complete joint system numerically, retaining passing,
failed and unsupported outcomes to decide necessary model changes.

| Wood-joint record | Structural bolts / nuts | Washers | Status |
| --- | ---: | ---: | --- |
| Reviewed basis | 104 / 104 | 208 | Preserved geometry and analytical reference |
| [Knee-bridge packet](docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-working-package.md) | 108 / 108 | 216 | Complete conditional packet; unadopted proposal |

Both retain 24 blocks, 44 timber blanks, 50 transport bodies and 66 purchased
Hillman panel/kicker screws. The proposal adds four bolts in two knee spines;
it does not replace the reviewed authority. The [wood-joint contract](wood-joints-candidate.json)
records this separate development lane.

Calculations retain six cases with 250 lb × 2 downward, signed 300 N horizontal,
the original 100 mm hold lever, recorded gravity and the equipment allowance.
The all-joint demand/path assessment is complete; splitting resistance remains
unresolved. The panel-head reference deficit, assumed material/contact behavior,
no-slip floor and delivered-part limits remain explicit in the disposition.
This engineer-unreviewed documentation supplies no fabrication or climbing release.

## Selected baseline and design history

The selected screw-and-bracket baseline remains `compact-floor-flush-development`,
governed by [current-candidate.json](current-candidate.json). Its preserved
[reference packet](docs/README.md) contains the plywood variants, checklist,
assembly guide and baseline evidence. The [selected working set](docs/selected-working-set.md)
lists that baseline's files. Its passes do not qualify the wood-joint lane.

The [design-history catalog](docs/history/design-history.md) preserves previous
options, results and lessons for reference and a future writeup. Historical
models remain available in the [full viewer collection](https://mckayreedmoore.github.io/mini-moonboard/).

## Contributor setup

Work on `master` and coordinate file ownership and publication with other agents.
Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before changing
geometry, evidence or archived files.

```sh
uv sync --locked
uv run python -m http.server 8767 --directory site
```

Open [the local WJ24 viewer](http://localhost:8767/wood-joints-wj24-viewer.html).
Contributor instructions cover affected checks, mesh aliases and verified
evidence archiving. Preserve frozen inputs and historical results.
