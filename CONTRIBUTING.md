# Contributing

## Development setup

This project uses Python 3.12, [uv](https://docs.astral.sh/uv/), CadQuery, and
OCP CAD Viewer. The tested environment is Ubuntu 24.04 under WSL.

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create or refresh the repository-local environment:

```bash
uv sync
```

Open the repository from WSL with `code .`, select `.venv/bin/python`, and
install the VS Code extensions **Python**, **Remote - WSL**, and
**OCP CAD Viewer** for interactive model viewing.

FFmpeg is optional and is only needed when extracting frames from video
references:

```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

## Checks

Run all checks before committing:

```bash
uv run ruff check .
uv run pytest
uv run scripts/smoke_test.py
```

The default test run covers the current candidate and shared geometry, hardware,
and analysis utilities. Preserved historical-model tests are opt-in:

```bash
uv run pytest --include-historical                 # Current and historical tests
uv run pytest --include-historical -m historical   # Historical tests only
```

`tests/historical.txt` lists excluded modules and historical cases within mixed
modules. New tests run by default unless explicitly added to that inventory.
Historical modules are excluded before import during normal discovery. Even an
explicit historical test path requires `--include-historical` to execute.
Shared calculations remain active even when their filenames name an older model.
CI uses the same default; its manual workflow can also include historical tests
and the historical reference/V1 export comparison.

The September 12, 2026 full run had 2,777 passes, eight skips and three historical
source-inventory failures in `test_reinforcement_review.py`,
`test_round_service_export_contract.py` and `test_round_structural_global_envelope.py`.
All three also fail at the preceding commit `e546017`: their broad source glob
discovers six successor files absent from the preserved reports. Historical
opt-in retains these failures; it does not regenerate or qualify old evidence.

Optional CPU parallelism can be tried without changing the locked CAD environment:

```bash
uv run --with pytest-xdist pytest -n 4 --dist loadfile
```

`loadfile` keeps a file's tests together so they can reuse process-local CAD
caches. A local four-worker trial passed 299 current/shared tests in 23.4 seconds,
approximately the same as serial execution. Keep serial execution as the default;
additional workers did not improve this reduced suite in that trial.

Regenerate the current candidate after changes to its source or geometry inputs:

```bash
uv run python -m mini_moonboard.no_shoes_exports
uv run python -m mini_moonboard.no_shoes_exports --check
```

The current exporter builds all meshes, metadata and STEP from CAD without
reading historical export bundles. `--check` uses an empty temporary output
directory and compares the rebuilt assets and source manifest with the committed
candidate. `--root PATH` permits an independent output directory. Source hashes
cover the transitive local Python imports, explicit geometry reference files and
locked environment. Geometry-source changes can also invalidate analysis records;
rerun affected calculations rather than merely replacing their stored hashes.

Reference/V1 model and panel-datum exports belong in `exports/` and must be
regenerated when their corresponding source changes:

```bash
uv run python -m mini_moonboard.export
```

The STEP exporter removes color metadata and normalizes unstable Open CASCADE
timestamps and assembly counters so unchanged geometry produces byte-identical
artifacts. Colors remain available when viewing the CadQuery assembly directly.
CI always checks the current candidate rebuild and fails when its committed
artifacts are stale. The reference/V1 export check runs only when historical
testing is requested through the manual workflow.
The panel-datum CSV and SVG are also deterministic; the SVG is a visual
verification drawing only and must never be treated as a drilling template.

CadQuery dimensions are always millimetres. Documentation should show both
metric and imperial values and identify whether a value is source-stated,
converted, derived, or still unresolved.

Keep real site measurements in the ignored `design_inputs.toml`, created from
`design-inputs.example.toml`. Validate it before using a custom kicker value or
starting detailed frame design:

```bash
uv run python -m mini_moonboard.site_inputs design_inputs.toml
```

The reference model is not a structurally approved climbing-wall design. Do
not turn provisional observations into construction instructions without a
documented design decision and qualified structural review.
