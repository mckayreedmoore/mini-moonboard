# Mini MoonBoard DIY frame

Independent CAD, shop instructions and conditional calculations for a Mini
MoonBoard-sized climbing wall. Not affiliated with or endorsed by Moon Climbing.

**Selected design: `compact-floor-flush-development`.** Engineer-unreviewed
conditional DIY under recorded loads, DF-L No. 2, catalog hardware and an
explicit no-slip floor assumption. Not a fabrication release, manufacturer
qualification or climber rating.

## Start here

1. Pick a width: **official Mini 4×4** or **4×8 with 1/8 in kerf on the K / right
   side** (pads in front; right is toward the right leg). See
   [width option](docs/floor-flush-width-option.md).
2. Build from the [shop checklist](docs/floor-flush-shop-checklist.md) and
   [assembly guide](docs/floor-flush-assembly-guide.md).
3. Use matching sheets only:
   - Official: [docs/floor-flush-construction/](docs/floor-flush-construction/)
   - Kerf-right: [docs/floor-flush-construction-kerf-right/](docs/floor-flush-construction-kerf-right/)
4. Do not mix packets. Six-case evidence applies only to the official 4×4.

Machine authority is [`current-candidate.json`](current-candidate.json).
Working constraints: [`AGENTS.md`](AGENTS.md).

## What you are looking at

Solid 4×6 legs and side rims, compact 2×6 header/posts/rails/runners, whole
kickers, a 1:12 rear-leg recess, twelve outward bolt stacks, 24 ML24Z angles
with 144 SDS25112 screws, and 66 Hillman 42605 panel/kicker screws.

- SDS: 5/32 in wood lead hole **through the purchased angle**.
- Hillman: Kobalt 80277 **#10** insert (1/8 in pilot, 3/8 in countersink), then
  an offcut trial.
- Frame bolts: NDS clearance holes; measure delivered shank (no full-thread
  substitutes).

Listed ML24Z catalog forces pass in the saved cases. Separation and
flange-couple actions are **disclosed without capacity**. The floor is an
**unverified no-slip assumption**, not an anchor.

## Viewer

```sh
uv run python -m http.server 8767 --directory site
```

Open [localhost:8767](http://localhost:8767/) (official 4×4) or
[kerf-right](http://localhost:8767/?model=compact-floor-flush-kerf-right).

Current design is the two width presentations. Older candidates are in the
archive menus. Pads are a placement preview only.

## Plans and evidence (short map)

| Document | Role |
| --- | --- |
| [Shop checklist](docs/floor-flush-shop-checklist.md) | Cut, drill, assemble, inspect |
| [Assembly guide](docs/floor-flush-assembly-guide.md) | Sequence and hardware |
| [Build package](docs/floor-flush-build-package.md) | What is in the selected assembly |
| [MVP master plan](docs/floor-runner-mvp-master-plan.md) | How the six-case MVP was finished |
| [Criteria](docs/floor-runner-mvp-criteria.md) | The 36 adopted checks |
| [Completion ledger](docs/floor-runner-mvp-completion-ledger.md) | Passes vs still-open limits |
| [Six-case aggregate](docs/floor-runner-mvp-evidence.json) | Authenticated no-slip results |
| [History](docs/history/README.md) | Older candidates; do not treat as current |

The master plan’s FR-0–FR-8 work is documentation/software complete. Remaining
work is receiving, fabrication and filling blank inspection cells.

## Reproduce

```sh
uv sync --locked
uv run python -m scripts.floor_flush_exports
uv run python -m scripts.floor_flush_construction
uv run python -m scripts.current_candidate --check-exports
uv run pytest -q
```

The checker confirms configuration identity, not structural acceptance. See
[CONTRIBUTING.md](CONTRIBUTING.md).
