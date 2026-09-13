# Independent DIY frame plans for the Mini MoonBoard

Explore a freestanding Mini MoonBoard frame through an interactive 3D model,
CAD downloads and documented engineering studies. This is an independent
project, not affiliated with or endorsed by Moon Climbing.

**Development project — not released for construction or climbing.** The latest
candidate is `no-shoes-development`: single 2×6 support legs and outer rims,
commercial base angles, and a raised kicker for a 5-inch pad. Geometry checks
have passed; whole-frame structural assessment remains pending.

**[Open the latest 3D model](https://mckayreedmoore.github.io/mini-moonboard/?model=no-shoes-development&view=rear)** ·
**[Download the STEP assembly](https://mckayreedmoore.github.io/mini-moonboard/hybrid/no-shoes-development/assembly.step)** ·
**[Read the candidate notes](docs/no-shoes-candidate.md)**

## Latest candidate: no custom steel shoes

- Single nominal 2×6 support legs and outer rims, with four ⅜-inch bolts per leg.
  Other members retain their existing stock sizes; this is not an all-2×6 frame.
- Two standard Simpson ML24Z base angles and twelve specified SDS screws replace
  the custom steel shoes. Fresh timber uses the original bearing detail, without
  shoe holes or shoe-clearance cuts.
- **277 mm (10.91 inches) floor-to-main-face kicker datum:** 150 mm of exposed
  kicker above a 127 mm (5-inch) pad allowance. This is 52 mm above the preceding
  225 mm datum. Posts, rear legs and kicker plywood extend to the floor; the pad
  is not a structural support.
- Existing plywood, 142 selectable T-nuts and enclosed LED passages remain.
  Panel attachments total 66 SPAX structural screws: twelve per main panel and
  nine per kicker. Hold bolts are not modeled.

Focused checks cover the restored hardware, extended members and floor contact,
retained leg sections, kicker-screw clearance against the base angles, export
provenance and browser placement. These are geometry checks, not a load rating.
The next assessment must determine whole-frame load sharing and connection forces
for this geometry. Earlier reinforced calculations do not transfer to it.
Published [material specifications](docs/leg-material-basis.md) and the accepted
panel/T-nut construction are the design basis; no panel or T-nut upgrade is
proposed. The frame analysis retains the owner's no-sliding assumption.

## Start here — no software installation needed

| What you want to do | Open this |
| --- | --- |
| Rotate the latest frame and inspect parts | [Interactive viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=no-shoes-development&view=rear) |
| Understand the shoe removal and pad allowance | [Candidate changes and assessment status](docs/no-shoes-candidate.md) |
| Open the latest geometry in CAD software | [STEP assembly](https://mckayreedmoore.github.io/mini-moonboard/hybrid/no-shoes-development/assembly.step) |
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

See the [design review and finite verification plan](docs/current-design-review.md)
for what remains necessary, what is historical, and which checks should not drive
additional reinforcement. Geometry acceptance and structural acceptance are separate.

The [current whole-frame equilibrium screen](docs/current-frame-equilibrium.md)
uses the current CAD mass, all 142 hold positions and actual timber footprints.
It checks compression-only support equilibrium; internal member and joint strength
remain to be assessed. Published base-angle directions and capacities are recorded
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

The current model is [`no_shoes_frame.py`](mini_moonboard/no_shoes_frame.py).
Its `uncut_wood_parts()`, `parts()` and `connections()` expose raw stock,
machined parts and connections. Named face/header datums and explicit floor-member
roles define the current height change. Historical geometry factories remain
source dependencies; historical meshes and manifests are not build inputs.
Its matching exporter regenerates every current viewer mesh, the inventory,
source hashes and a normalized STEP assembly directly from CAD:

```sh
uv run python -m mini_moonboard.no_shoes_exports
# Rebuild into an empty temporary directory and compare every current artifact:
uv run python -m mini_moonboard.no_shoes_exports --check
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
