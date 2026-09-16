# Independent DIY frame plans for the Mini MoonBoard

This independent project provides CAD, an interactive viewer and conditional
DIY design studies. It is not affiliated with or endorsed by Moon Climbing.

## Current direction: compact spliced knees, flush leg tops

**`compact-spliced-flush-top-development` is the selected conditional DIY
development. It is not an unconditional rating or construction release.** It
retains the compact 4×6 legs/rims, compact 2×6 base, four independent spliced
2×6 knee pieces, 20 complete outward-facing bolt stacks, 66 panel/kicker
screws, and a 7 mm rear rim reserve. Rear-leg tops are 0 mm projection at the
rim; the two upper bolt pairs per leg remain at 56 mm pitch after relocation.

Use the [current design basis](docs/current-design-basis.md), [completion
record](docs/current-diy-completion-record.md), and [execution plan](docs/engineering-execution-plan.md).
Six fresh no-slip cases meet the listed conditional checks. The tightest
directional placement margin is 0.361 mm and the minimum group-spacing margin
is 1.9 mm; these are installation limits, not safety factors. Full-root lateral
results above 1.0 are recorded sensitivities, not adopted criteria. Retained
ML24Z/SDS separation and independent flange-couple applicability remain an open
connection gate; this package is not ready for fabrication. No floor
runners or 1:12 taper belong to this selected hybrid.

The earlier [taper study](docs/floor-runner-taper-study.md) records six cases
passing its 35 implemented criteria, with later applicability/contact gaps
identified. Those results do not qualify the changed flush geometry. The
[exterior-brace and original floor-rail studies](docs/clear-space-study.md)
remain historical alternatives with their own assumptions and limits.

## View the current local model

```sh
uv run python -m http.server 8767 --directory site
```

Open [the local viewer](http://localhost:8767/?model=compact-spliced-flush-top-development&view=rear).
Select individual timber or hardware, orbit the assembly, hide panels and use
the crash-pad toggle to inspect the two 48 x 72 x 5-inch pads. They sit side by
side, so their center seam runs front to back. Pads are excluded
from frame weight and structural supports. The default now shows the flush
revision; older designs remain in the menu. Current work has not been pushed,
so the public website may still show the preceding design.

The [assembly STEP](site/hybrid/compact-spliced-flush-top-development/assembly.step)
and [part inventory](site/hybrid/compact-spliced-flush-top-development/parts.json)
are generated from the same model. Drawings are dimensional instructions only
when explicitly identified as such; this preview does not release drilling.

## Scope and materials

The intended endpoint is an engineer-unreviewed conditional DIY design under
specified loads, lumber, hardware and installation assumptions. No unconditional
climber weight rating is claimed. Accepted plywood/T-nut construction is retained;
no new floor-friction test, external sign-off or general panel campaign is added.
Current calculations use an explicit conditional no-slip support assumption;
normal floor contact may open. Recorded per-cell Coulomb precursor cases remain
historical evidence, not current floor qualification. A changed assembly requires
its own justified force/contact basis.

See [design decisions](docs/current-design-basis.md),
[purchased materials](docs/purchased-materials.md),
[hold hardware](docs/moonboard-hold-hardware.md),
[preceding bolt requirements](docs/floor-runner-taper-hardware.md), and
[weight notes](docs/prototype-weights.md).

## Reproduce and check

The selected model is
[compact_spliced_flush_top.py](mini_moonboard/compact_spliced_flush_top.py).
Historical floor-flush and tapered-runner tools do not reproduce this candidate.

```sh
uv sync --locked
uv run python -m scripts.compact_spliced_flush_top_geometry --output fea/generated/compact-spliced-flush-top/geometry.json
uv run python -m scripts.compact_spliced_flush_top_exports
uv run python -m scripts.compact_spliced_flush_top_construction
uv run python -m scripts.current_candidate --check-exports
uv run pytest -q
```

Use exporter `--root /path/to/empty-directory` for a standalone geometry bundle.
For a fresh load case, use
`uv run python -m scripts.compact_spliced_flush_top_study --output fea/generated/your-new-case --hold A12 --horizontal -300 0`.
This runs the stated scenario; numerical convergence does not release the design.
The [candidate authority](current-candidate.json) ties the selected modules,
package, hardware schedule and recorded assessment references together. Its
checker verifies configuration consistency, not structural acceptance; exact
export and drawing revisions retain their existing source/artifact hashes.
Construction-package completion is tracked in the plan above. See
[contributor guidance](CONTRIBUTING.md) and the
[historical design archive](docs/history/README.md) for other workflows.
