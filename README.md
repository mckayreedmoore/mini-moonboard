# Independent DIY frame plans for the Mini MoonBoard

Explore a freestanding Mini MoonBoard frame through an interactive 3D model,
CAD downloads and documented engineering studies. This is an independent
project, not affiliated with or endorsed by Moon Climbing.

**Selected DIY candidate: `compact-spliced-knee-development`.** Solid 4×6 legs
and flush rims retain the compact 2×6 base. Each leg has two ½-inch upper bolts
at 56 mm pitch. Four independent, unnotched diagonal 2×6 pieces form the knee
braces, with four ⅜-inch splice bolts per side and two ⅜-inch bolts at each
brace endpoint: 20 complete bolt stacks in total.

**[Open the selected 3D model](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-spliced-knee-development&view=rear)** ·
**[Build package](docs/compact-spliced-build-package.md)** ·
**[Current calculation and limits](docs/compact-splice-study.md)**

The endpoint is an **engineer-unreviewed DIY package**, conditional on its
stated load cases, specified lumber/catalog hardware and no-slip floor
assumption. The [completion record](docs/current-diy-completion-record.md)
tracks the final evidence gates. No unconditional climber rating is claimed.
The 277 mm kicker datum, 66 panel/kicker screws and accepted plywood/T-nut
construction remain. Earlier failed joints are preserved historical studies.

Two separate [clear-space alternatives](docs/clear-space-study.md) address the
inboard knee obstruction: continuous 2×6 floor rails or exterior 4×6/2×6
braces. Each has its own force cases, geometry and fabrication packet. Both
include the revised base-angle placement; the selected reference stays available.

## Start here — no software installation needed

| What you want to do | Open this |
| --- | --- |
| Rotate the latest frame and inspect parts | [Interactive viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-spliced-knee-development&view=rear) |
| Compare floor rails and exterior braces | [Assessment and fabrication packages](docs/clear-space-study.md) · [Dimensioned comparison](docs/clear-space-comparison.svg) |
| Inspect the unselected solid 4×6 pivot option | [Development viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=thick-leg-centered-pivot-development&view=rear) |
| Understand the shoe removal and pad allowance | [Candidate changes and assessment status](docs/no-shoes-candidate.md) |
| Open the latest geometry in CAD software | [STEP assembly](https://mckayreedmoore.github.io/mini-moonboard/hybrid/compact-spliced-knee-development/assembly.step) |
| Find current cuts, drilling, hardware and pad-height changes | [Spliced-knee build package](docs/compact-spliced-build-package.md) |
| Check specified lumber and bolt materials | [Material basis](docs/leg-material-basis.md) |
| See settled choices and calculation scope | [Current design basis and decision log](docs/current-design-basis.md) |
| Review purchased plywood and hold hardware | [Purchased materials](docs/purchased-materials.md) and [T-nuts and hold-bolt guidance](docs/moonboard-hold-hardware.md) |
| Understand the lighting route | [LED hookup schematic](docs/horizontal-service-wiring.svg) and [kit notes](docs/led-wiring-reference.md) |

The viewer lets you rotate, pan and zoom, select individual parts, change units
and hide categories. Use **Inspect connection** to view representative complete
bolt stacks. Use **Design** to compare candidates, each with its own geometry and
limits. The [prototype weight notes](docs/prototype-weights.md) explain the
estimates; displayed frame weight is not climber capacity.

## Engineering status

The agreed endpoint is an **engineer-unreviewed DIY design**. The
[completion record](docs/current-diy-completion-record.md) states the finite
deliverables and remaining calculated limitations; external sign-off is not a
completion requirement.

The [spliced-knee study](docs/compact-splice-study.md) is the authority for this
assembly's numerical, connection, member and hardware comparisons. Earlier
whole-frame reports remain historical evidence; their failures or passing
results do not transfer to the changed load path. Use the matching
[build package](docs/compact-spliced-build-package.md) for dimensions and hardware.

## Historical designs and studies

[Open the historical design archive](docs/history/README.md) for earlier 2×6/2×8
comparisons, custom-shoe designs, old plans and numerical studies. Their dimensions,
hardware schedules and results do not transfer automatically to the current candidate.

## Working on the models or analysis

For code changes, use Python 3.12 and [uv](https://docs.astral.sh/uv/).
See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and CAD-viewer instructions.
From a local checkout:

```sh
uv sync --locked
uv run ruff check .
uv run pytest
uv run scripts/smoke_test.py
```

The complete test suite includes CAD and evidence checks and can take time.
Running tests is separate from launching new finite-element solves. Individual
study documents describe their solver commands and assumptions.

The preferred model is [`compact_thick_frame.py`](mini_moonboard/compact_thick_frame.py).
Its `uncut_wood_parts()`, `parts()` and `connections()` expose raw stock,
machined parts and connections. Named face/header datums and explicit floor-member
roles define the current height change. Historical geometry factories remain
source dependencies; historical meshes and manifests are not build inputs.
Its matching exporter regenerates every current viewer mesh, the inventory,
source hashes and a normalized STEP assembly directly from CAD:

```sh
uv run python -m scripts.compact_spliced_exports
# Rebuild into an empty temporary directory and compare every current artifact:
uv run python -m scripts.compact_spliced_exports --check
```

Outputs are in [`site/hybrid/compact-spliced-knee-development/`](site/hybrid/compact-spliced-knee-development/).
Use `--root /path/to/empty-directory` to generate a standalone candidate bundle.
Meshes use assembled world coordinates and retain individually selectable bolt
components. The manifest records transitive local Python dependencies, geometry
reference data and the locked toolchain. It does not authenticate unrelated
historical exports. CI runs the current-candidate rebuild and current/shared
regression tests by default. Historical tests and the reference/V1 export check
are opt-in; see [Contributing](CONTRIBUTING.md#checks).
Generate the matching [cut/drilling packet](docs/compact-spliced-build-package.md)
with `uv run python -m scripts.compact_spliced_construction`.
Historical drawing generators are described with their corresponding designs in
[the archive](docs/history/README.md).

The older `uv run python -m mini_moonboard.export` command regenerates the
reference/V1 artifacts checked by the optional historical CI run; it does not regenerate every development
variant. Check [.github/workflows/ci.yml](.github/workflows/ci.yml) for the actual
lint, test, smoke and export checks. A passing workflow is not structural approval.

| Folder | Purpose |
| --- | --- |
| [`mini_moonboard/`](mini_moonboard/) | Parametric CadQuery models, hardware and exporters |
| [`docs/`](docs/) | Plans, assumptions, source references and study explanations |
| [`exports/`](exports/) | Candidate-specific STEP files, renders and schedules |
| [`fea/`](fea/) | Geometry audits and structural/numerical diagnostics |
| [`fea/results/`](fea/results/) | Saved evidence and source-bound reports |
| [`site/`](site/) | Browser viewer and selectable model meshes |
| [`tests/`](tests/) | Geometry, behavior and evidence-replay checks |

For a supplied SketchUp reference, `scripts/import_sketchup.py` can extract OBJ
geometry and a JSON summary; see its `--help`. Imported geometry is a comparison
input and does not become an approved frame automatically.

## Questions and project support

Use [GitHub issues](https://github.com/mckayreedmoore/mini-moonboard/issues) for
questions or reproducible problems. Include the viewer's design name and the
relevant drawing or report link so the discussion stays tied to one revision.
Maintained by [McKay Reed Moore](https://github.com/mckayreedmoore).
[Support the project on Ko-fi](https://ko-fi.com/mckayreedmoore).
