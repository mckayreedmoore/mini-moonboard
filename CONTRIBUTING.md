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

Stable model exports belong in `exports/` and must be regenerated in the same
commit as their CadQuery source:

```bash
uv run python -m mini_moonboard.export
```

CadQuery dimensions are always millimetres. Documentation should show both
metric and imperial values and identify whether a value is source-stated,
converted, derived, or still unresolved.

The reference model is not a structurally approved climbing-wall design. Do
not turn provisional observations into construction instructions without a
documented design decision and qualified structural review.

