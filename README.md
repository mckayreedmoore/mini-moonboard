# Independent DIY frame plans for the Mini MoonBoard

This independent project provides CAD, an interactive viewer and conditional
DIY design studies. It is not affiliated with or endorsed by Moon Climbing.

## Current direction: flush floor beams

**`compact-floor-flush-development` is the selected development direction. It
is not yet a completed fabrication package.** The owner requested full outboard
2x6 floor beams, whole kicker panels, runner ends flush to the posts and legs,
side-rim bottoms flush to the posts, and rear-leg tops flush to the side rims.
The upper half-inch bolt pairs have been relocated while retaining 56 mm pitch.

Use the [current revision and pending checks](docs/floor-flush-build-package.md)
and [finite DIY completion plan](docs/tapered-runner-completion-plan.md).
Receiver fit does not establish connection strength. The existing rim end-cut
screen fails. One fresh contact-enabled load case is numerically accepted;
taper-method applicability, contact sensitivity, remaining force cases and
fabrication allowances remain open. The [draft assembly guide](docs/floor-flush-assembly-guide.md)
and [current drawings](docs/floor-flush-construction/) describe the proposed build.

The earlier [taper study](docs/floor-runner-taper-study.md) records six cases
passing its 35 implemented criteria, with later applicability/contact gaps
identified. Those results do not qualify the changed flush geometry. The
[exterior-brace and original floor-rail studies](docs/clear-space-study.md)
remain historical alternatives with their own assumptions and limits.

## View the current local model

```sh
uv run python -m http.server 8767 --directory site
```

Open [the local viewer](http://localhost:8767/?model=compact-floor-flush-development&view=rear).
Select individual timber or hardware, orbit the assembly, hide panels and use
the crash-pad toggle to inspect the two 96 x 36 x 5-inch pads. Pads are excluded
from frame weight and structural supports. The default now shows the flush
revision; older designs remain in the menu. Current work has not been pushed,
so the public website may still show the preceding design.

The [assembly STEP](site/hybrid/compact-floor-flush-development/assembly.step)
and [part inventory](site/hybrid/compact-floor-flush-development/parts.json)
are generated from the same model. Drawings are dimensional instructions only
when explicitly identified as such; this preview does not release drilling.

## Scope and materials

The intended endpoint is an engineer-unreviewed conditional DIY design under
specified loads, lumber, hardware and installation assumptions. No unconditional
climber weight rating is claimed. Accepted plywood/T-nut construction is retained;
no new floor-friction test, external sign-off or general panel campaign is added.
Current precursor cases assume per-cell Coulomb friction at mu = 0.4, not measured
friction. A changed assembly requires its own justified force/contact basis.

See [design decisions](docs/current-design-basis.md),
[purchased materials](docs/purchased-materials.md),
[hold hardware](docs/moonboard-hold-hardware.md),
[preceding bolt requirements](docs/floor-runner-taper-hardware.md), and
[weight notes](docs/prototype-weights.md).

## Reproduce and check

The model is [compact_floor_flush_frame.py](mini_moonboard/compact_floor_flush_frame.py).
Its raw stock, machined parts, connections and cut records retain older sources
without changing the preserved native evidence.

```sh
uv sync --locked
uv run python -m scripts.floor_flush_geometry
uv run python -m scripts.floor_flush_exports
uv run python -m scripts.floor_flush_exports --check
uv run python -m scripts.floor_flush_construction
uv run pytest -q
```

Use exporter `--root /path/to/empty-directory` for a standalone geometry bundle.
For a fresh load case, use `uv run python -m scripts.floor_flush_case a12-left --output fea/generated/your-new-case`.
This runs the stated scenario; numerical convergence does not release the design.
Construction-package completion is tracked in the plan above. See
[contributor guidance](CONTRIBUTING.md) and the
[historical design archive](docs/history/README.md) for other workflows.
