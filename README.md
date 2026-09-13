# Independent DIY frame plans for the Mini MoonBoard

Explore a freestanding Mini MoonBoard frame through an interactive 3D model,
CAD downloads and documented engineering studies. This is an independent
project, not affiliated with or endorsed by Moon Climbing.

**Development project — not released for construction or climbing.** The preferred
candidate is `compact-thick-development`: solid 4×6 legs and flush outer rims,
three bolts per leg, and a shallower 2×6 kicker base. Its changed connections and
base require their own engineering checks; the preceding single-pivot results
do not qualify this revision.

**[Open the preferred 3D model](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-thick-development&view=rear)** ·
**[Download the STEP assembly](https://mckayreedmoore.github.io/mini-moonboard/hybrid/compact-thick-development/assembly.step)** ·
**[Read the candidate study](docs/compact-thick-study.md)**

The inclined members retain a 7 mm rear overhang above the 139.7 mm-deep base,
limiting the triangular end cuts. The top and service rails are shortened to
fit between the inward-shifted rims. The 277 mm kicker datum, 66 SPAX
panel/kicker screws and accepted plywood/T-nut construction remain.

The [single-2×6 baseline](docs/no-shoes-candidate.md) and
[single-pivot 4×6 study](docs/thick-leg-pivot-study.md) remain preserved comparisons.
Published [material specifications](docs/leg-material-basis.md) and the owner's
no-sliding floor assumption remain the design basis.

## Start here — no software installation needed

| What you want to do | Open this |
| --- | --- |
| Rotate the latest frame and inspect parts | [Interactive viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-thick-development&view=rear) |
| Inspect the unselected solid 4×6 pivot option | [Development viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=thick-leg-centered-pivot-development&view=rear) |
| Understand the shoe removal and pad allowance | [Candidate changes and assessment status](docs/no-shoes-candidate.md) |
| Open the latest geometry in CAD software | [STEP assembly](https://mckayreedmoore.github.io/mini-moonboard/hybrid/compact-thick-development/assembly.step) |
| Find current cuts, drilling, hardware and pad-height changes | [Compact construction package](docs/compact-construction-package.md) |
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

See the [design review and finite verification plan](docs/current-design-review.md)
for what remains necessary, what is historical, and which checks should not drive
additional reinforcement. Geometry acceptance and structural acceptance are separate.

The [current whole-frame equilibrium screen](docs/current-frame-equilibrium.md)
uses the current CAD mass, all 142 hold positions and actual timber footprints.
It checks compression-only support equilibrium. The subsequent
[internal-response calculation](docs/current-frame-response.md) evaluates the
assembled frame and compares its member and connection demands with stated
references; it does not release the design for construction. Published base-angle directions and capacities are recorded
in the [current connection basis](docs/current-base-connection-basis.md).

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
uv run python -m mini_moonboard.compact_thick_exports
# Rebuild into an empty temporary directory and compare every current artifact:
uv run python -m mini_moonboard.compact_thick_exports --check
```

Outputs are in [`site/hybrid/no-shoes-development/`](site/hybrid/no-shoes-development/).
Use `--root /path/to/empty-directory` to generate a standalone candidate bundle.
Meshes use assembled world coordinates and retain individually selectable bolt
components. The manifest records transitive local Python dependencies, geometry
reference data and the locked toolchain. It does not authenticate unrelated
historical exports. CI runs the current-candidate rebuild and current/shared
regression tests by default. Historical tests and the reference/V1 export check
are opt-in; see [Contributing](CONTRIBUTING.md#checks).
The current candidate does not yet have a released cut/drilling package.
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
