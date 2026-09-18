# Mini MoonBoard DIY frame

Plans, a 3D viewer, and shop sheets for a Mini MoonBoard-sized climbing wall
you can build yourself. This is an independent project, not affiliated with or
endorsed by Moon Climbing.

This is a DIY build. It has not been signed off by an engineer.

## Start here

**How you get the plywood decides which sheets to use.**

| Your plywood | Cut and drill sheets | 3D model |
| --- | --- | --- |
| Bought as **4×4** (or Mini kit panels) | [github.com/mckayreedmoore/mini-moonboard/tree/master/docs/floor-flush-construction](https://github.com/mckayreedmoore/mini-moonboard/tree/master/docs/floor-flush-construction) | [https://mckayreedmoore.github.io/mini-moonboard/](https://mckayreedmoore.github.io/mini-moonboard/) |
| **Cut from 4×8** (saw takes about 1/8 in) | [github.com/mckayreedmoore/mini-moonboard/tree/master/docs/floor-flush-construction-kerf-right](https://github.com/mckayreedmoore/mini-moonboard/tree/master/docs/floor-flush-construction-kerf-right) | [https://mckayreedmoore.github.io/mini-moonboard/?model=compact-floor-flush-kerf-right](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-floor-flush-kerf-right) |

You can also open the 3D page and, under **Design**, pick **Bought 4×4 plywood**
or **Cut from 4×8**. You do not have to edit the address bar.

Why two folders: a 4×8 ripped in half loses about 1/8 in to the blade, split
across both faces. Hold and screw layout still starts from the left, like the
Moon drawings, so that missing width lands on the right. More detail:
[Which plywood packet](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/floor-flush-width-option.md).

Start in [docs/](https://github.com/mckayreedmoore/mini-moonboard/tree/master/docs)
([docs/README.md](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/README.md)).
Then follow the [shop checklist](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/floor-flush-shop-checklist.md)
and [assembly guide](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/floor-flush-assembly-guide.md).
Use only the folder that matches your plywood. Do not mix them.

The selected design name in the files is `compact-floor-flush-development`.

## What you are building

4×6 rear legs and side rims, 2×6 header, posts, rails and floor runners, whole
kicker panels, a 1:12 cut on the back of each rear leg, twelve bolt stacks,
24 Simpson ML24Z angles with SDS screws, and 66 Hillman deck screws through
the faces.

- **Angle screws (SDS):** 5/32 in pilot through the metal angle into the wood.
- **Face screws (Hillman #10):** Kobalt #10 bit, 1/8 in pilot and 3/8 in
  countersink. Try it on a scrap first.
- **Frame bolts:** slightly oversize holes; use partially threaded bolts and
  check the smooth shank on the parts you actually bought.

Calculations used 250 lb holds and assumed the feet stay put. Some Simpson
angle actions have no published rating; that is noted in the ledger. Crash pads
in the 3D view are a size check only. Older designs are in the archive menus.

## If you want the background

| Document | What it is |
| --- | --- |
| [Shop checklist](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/floor-flush-shop-checklist.md) | Cut, drill, assemble, inspect |
| [Assembly guide](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/floor-flush-assembly-guide.md) | Order of work and hardware |
| [Which plywood packet](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/floor-flush-width-option.md) | 4×4 vs 4×8 |
| [Build package](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/floor-flush-build-package.md) | Parts list and current status |
| [MVP master plan](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/floor-runner-mvp-master-plan.md) | How the calculations were finished |
| [Completion ledger](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/floor-runner-mvp-completion-ledger.md) | What passed and what is still open |
| [History](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/history/README.md) | Older ideas; not current |

What is left is buying lumber, cutting, and filling in the checklist as you go.

## For people editing the code

```sh
uv sync --locked
uv run python -m http.server 8767 --directory site
uv run python -m scripts.floor_flush_exports
uv run python -m scripts.floor_flush_construction
uv run python -m scripts.current_candidate --check-exports
uv run pytest -q
```

[`current-candidate.json`](https://github.com/mckayreedmoore/mini-moonboard/blob/master/current-candidate.json)
points at the selected files. See
[CONTRIBUTING.md](https://github.com/mckayreedmoore/mini-moonboard/blob/master/CONTRIBUTING.md).
