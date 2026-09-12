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
| Review purchased plywood and hold hardware | [Purchased materials](docs/purchased-materials.md) and [T-nuts and hold-bolt guidance](docs/moonboard-hold-hardware.md) |
| Understand the lighting route | [LED hookup schematic](docs/horizontal-service-wiring.svg) and [kit notes](docs/led-wiring-reference.md) |

The viewer lets you rotate, pan and zoom, select individual parts, change units
and hide categories. Use **Inspect connection** to view representative complete
bolt stacks. Use **Design** to compare candidates, each with its own geometry and
limits. The [prototype weight notes](docs/prototype-weights.md) explain the
estimates; displayed frame weight is not climber capacity.

## Preserved comparisons and older plans

The two preceding leg comparisons retain custom steel base shoes and the older
225 mm kicker datum. They remain available for reviewing the design changes.

| Design | Open the model | Review the evidence |
| --- | --- | --- |
| 2×6 legs and outer rims; four ⅜-inch leg bolts per side; custom base shoes | [2×6 reinforced comparison](https://mckayreedmoore.github.io/mini-moonboard/?model=round-reinforcement-development&view=rear) | [Conditional 150 lb comparison](docs/leg-150-comparison.md) |
| 2×8 legs and outer rims; six ½-inch leg bolts per side; custom base shoes | [2×8 comparison](https://mckayreedmoore.github.io/mini-moonboard/?model=wider-leg-development&view=rear) | [CAD and hardware package](docs/wider-leg-review/README.md) |

Both are unqualified development designs. See the
[criterion-source review and conditional limits](docs/wider-leg-criteria-review.md).

The earlier `round-structural-development` retains its
[build-plan draft](docs/round-structural-build-plan.md),
[drilling PDF](docs/round-structural-drilling/drilling.pdf),
[wood schedule](exports/round-structural-development/wood-parts.csv),
[connection schedule](exports/round-structural-development/connections.csv),
[tools checklist](docs/round-structural-build-plan.md#tools-and-equipment) and
[dated partial costs](docs/material-costs.md). These documents describe that older
candidate, including its 225 mm kicker and 56 panel/kicker screws. **They are not
an updated fabrication package for the latest raised, shoe-free candidate.**
Do not combine one candidate's cut list or analysis with another's geometry.

## Earlier designs and engineering evidence

Older models remain available so changes and failed checks can be reviewed.
They are development history, not alternate approved construction packages.

<details>
<summary>Open the design and analysis index</summary>

| Study or predecessor | Notes and artifacts |
| --- | --- |
| Single-member all-2×6 baseline | [Layout and known failures](docs/single-2x6-layout.md) |
| Selective member enlargement | [Single 3×6 receivers and 2×10 header](docs/selective-2x6-layout.md) |
| Paired horizontal rails | [Separate rail connections and center-base attachment](docs/paired-rail-base.md) |
| Additional vertical principals | [Layout and independent-panel comparison](docs/vertical-principal-development.md) |
| Separated center principals | [Service corridor, bolt inspection and floor/panel screens](docs/split-center-development.md) |
| Denser panel screw rows | [Infill candidate and connection diagnostics](docs/infill-panel-development.md) |
| Round passages with wood panel screws | [Preserved screw-candidate analysis](docs/round-service-analysis.md), [build draft](docs/round-service-build-plan.md) |
| Grooved horizontal service rails | [Previous build draft](docs/horizontal-service-build-plan.md), [archived viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=horizontal-service-development&view=rear) |
| Direct base angles | [Gusset replacement candidate](docs/angle-base-development.md) |
| Wider supports and panel inserts | [Wide-principal package](docs/wide-principal-development.md), [machining references](docs/wide-machining.md), [insert development](docs/panel-insert-development.md) |
| Lumber leg alternatives | [Stock comparison](docs/leg-stock-comparison.md), [lumber response](docs/lumber-leg-response.md), [spread-bolt revision](docs/spread-leg-response.md) |
| Joint and connection studies | [Coupled leg/rim study](docs/coupled-leg-release.md), [qualification ledger](docs/connection-qualification-ledger.md), [connection checkpoint](docs/mvp-connection-checkpoint.md) |
| Contact and numerical checks | [Numerical acceptance basis](docs/numerical-acceptance-basis.md), [floor-contact history](docs/floor-contact-study.md), [increment refinement](docs/full-frame-increment-refinement.md) |
| Original V1 concept | [Box-frame revision](docs/box-frame-revision.md), [V1 render](exports/mini_moonboard_v1_cad_front_render.png), [V1 viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=plywood) |
| Official geometry and conventions | [Requirements](docs/requirements.md), [orientation](docs/orientation.md), [panel-grid notes](docs/panel-grid.md), [artwork policy](docs/panel-artwork.md) |

The [documentation folder](docs/) contains the remaining investigations.
[Archived results](fea/results/) retain their source snapshots and numerical
limits. Early V1 hole layouts and assembly instructions are historical; they
do not replace the current panel datums or hardware schedule.

</details>

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

The current candidate's Python module exposes `wood_parts()`, `parts()`
and `connections()`: raw timber, machined/model parts, and connection records.
CadQuery dimensions are in millimetres. The exporter needs the matching current
audit and refuses to overwrite an existing output directory:

```sh
uv run python -m mini_moonboard.round_service_exports --help
```

Regenerate drilling references into a new directory, then print the authenticated
SVG pages to PDF without a browser. Run from the repository root; replace
`NEW_DRAWING_DIRECTORY` with a path that does not exist yet:

```sh
uv run python -m mini_moonboard.round_service_drilling --output NEW_DRAWING_DIRECTORY
uv run --with pymupdf python scripts/print_drilling_svg.py NEW_DRAWING_DIRECTORY
```

The generator refuses to overwrite a directory. The PDF printer verifies the
source and drawing hashes, refuses to replace an existing `drilling.pdf`, and
records the PDF hash and renderer in the manifest. It does not establish
machining tolerances or structural adequacy.

The older `uv run python -m mini_moonboard.export` command regenerates the
reference/V1 artifacts checked by CI; it does not regenerate every development
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
