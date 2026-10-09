# Mini MoonBoard DIY frame

Engineering models, calculations, viewers and conditional shop documents for
a Mini MoonBoard-sized climbing wall. This is an independent project, not
affiliated with or endorsed by Moon Climbing.

## Active development: eoere bolted frame

Start at the [eoere development summary](docs/wood-joints-mvp/README.md) and
[build-completion sequence](docs/wood-joints-mvp/completion-ledger.md#build-package-completion).
Their retained `wood-joints-mvp` paths contain the active work and its history.
The current approach uses **22 eoere angles, two exterior 2×6 cleats, 22
timbers, 100 through-bolt stacks and 66 purchased Hillman panel/kicker screws**.
The current geometry centers the six rails' 30 wire passages on the original
grid columns and retains the two already-aligned upright passages. All 132 LED
endpoints and 131 links remain fixed. It also trims both exterior cleats' projecting corners along
the rear edges of the sloping sides. Full 38.1-mm cleat thickness, all 100
bolt positions and all 66 screw axes remain unchanged. The
[aligned-wire viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-bolted-aligned-wire-development&view=rear)
and [geometry receipt](docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-aligned-wire-v1.json)
record this separate, unevaluated geometry revision. The preceding trimmed-cleat
viewer and all earlier choices remain available; a center-principal shift is unadopted.

The preserved, untrimmed raised-rail model has a completed [conditional six-case numerical packet](docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/fixed-floor-numerical-mvp-v1.json)
under **250 lb ×2, 300 N horizontal, a 100-mm hold arm** and recorded gravity.
Its explicit support scenario retains 32 compression-only normal contacts and
assumes no slip at the two rear legs. All six fresh fields and their scoped
component/joint records pass source and numerical review; reference exceedances
and null complete joint resistance remain recorded. The owner stopped further
panel/screw remedies. The [earlier eoere A12 viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-bolted-development&view=rear)
and its evidence remain preserved separately.
The [original Eoere proposal contract](eoere-bolted-candidate.json) binds the
earlier `eoere-far-pairs-cleat-corners-v1` geometry; use the development summary
and latest geometry receipt for subsequent revisions. It remains separate from
the selected baseline. No physical floor capacity, fabrication or climbing
release is established.

The [preserved raised-rail shop and assembly guide](docs/wood-joints-mvp/eoere-shop-assembly-guide.md)
organizes the nominal cut/hole datums, all 100 hardware stacks and 200 access
sides, receiving limits, assembly/removal order and cost/mass scope. Missing
dimensions, tools and actual observations stay explicit; coherent documentation
does not supply the model's unknown complete joint capacities. Its original
cleat profiles, wire-cut coordinates and six-case findings do not evaluate the
subsequent trim or aligned passages.

Builder-support work starts with the
[drilling and fixture development guide](docs/wood-joints-mvp/eoere-builder-drilling-guide.md).
It distinguishes single-timber bracket drilling from proposed matched-part
setups for the 20 two-timber axes. Finished fixture drawings, drill-bit
instructions, tool paths and manufacturing tolerances remain unresolved.

## Preserved wood-joint studies

The [WJ24 viewer](https://mckayreedmoore.github.io/mini-moonboard/wood-joints-wj24-viewer.html),
[engineering disposition](docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/mvp-joint-disposition.md)
and [knee-bridge packet](docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-working-package.md)
preserve the earlier 24-block, 44-timber studies with 104 or 108 bolt axes.
Their 47 formal criteria, conditional packet status and unresolved splitting
resistance belong to those frozen studies. Their geometry, loads, passes and
capacities do not transfer to the eoere frame.

## Selected baseline and design history

The selected screw-and-bracket baseline remains `compact-floor-flush-development`,
governed by [current-candidate.json](current-candidate.json). Its preserved
[reference packet](docs/README.md) contains the plywood variants, checklist,
assembly guide and baseline evidence. The [selected working set](docs/selected-working-set.md)
lists that baseline's files. Its passes do not qualify the eoere development lane.

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

Open [the local aligned-wire viewer](http://localhost:8767/index.html?model=eoere-bolted-aligned-wire-development&view=rear)
for the latest geometry revision, or choose a preserved model in the Design list.
Contributor instructions cover affected checks, mesh aliases and verified
evidence archiving. Preserve frozen inputs and historical results.
