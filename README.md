# Mini MoonBoard

Source-backed requirements and parametric CadQuery models for a freestanding
Mini MoonBoard.

## Status

This repository currently models the official Mini MoonBoard panel envelope.
It does **not** yet contain a structurally approved frame, bill of materials,
cut list, or construction guide. Those depend on the final kicker height,
crash-pad dimensions, room constraints, joinery, and structural review.

The eventual design target is an indoor, freestanding plywood A-frame inspired
by the reference photo and Moon Climbing video. The climbing panels will be
fabricated from birch plywood rather than purchased pre-drilled.

Reviewed renders of the completed assembly will be added here only with the
build-ready release, after the frame and custom kicker are designed and
accepted. The current reference-envelope exports are not frame renders.

## Reference dimensions

| Property | Metric | Imperial |
| --- | ---: | ---: |
| Main climbing surface | 2440 x 2440 mm | 8 ft x 8 ft nominal |
| Official kicker | 150 mm | 5.9 in |
| Angle from vertical | 40 degrees | 40 degrees |
| Official overall envelope | 2440 x 1569 x 2020 mm | 8.01 x 5.15 x 6.63 ft |
| Main panel thickness | 18 mm | 0.71 in |

The 150 mm kicker is retained only as an official reference. The custom taller
kicker remains unset until the crash pad is selected.

## Development

```bash
uv sync
uv run ruff check .
uv run pytest
uv run python -m mini_moonboard.export
uv run python -m mini_moonboard.site_inputs design_inputs.toml
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full setup and workflow.

## Repository map

- [`docs/requirements.md`](docs/requirements.md): official dimensions, unit
  conversions, source conflicts, and design constraints.
- [`docs/reference-analysis.md`](docs/reference-analysis.md): observations from
  the supplied photo and reference video.
- [`docs/design-basis.md`](docs/design-basis.md): resolved inputs, open design
  decisions, applicable-review references, and build-readiness gates.
- [`docs/panel-grid.md`](docs/panel-grid.md): source-backed main T-nut and LED
  center coordinates plus unresolved drilling inputs.
- `exports/mini_moonboard_metric_template_datums.{csv,svg}`: reproducible
  dual-unit center-data table and visual verification drawing.
- `exports/mini_moonboard_reference_panel_cut_list.csv`: generated panel-only
  cut list; it intentionally excludes the unresolved frame BOM.
- [`docs/site-survey.md`](docs/site-survey.md): dual-unit worksheet for room,
  crash-pad, kicker-clearance, stock, and review inputs.
- [`design-inputs.example.toml`](design-inputs.example.toml): validated,
  machine-readable companion to the site-survey worksheet.
- [`docs/change-control.md`](docs/change-control.md): controlled-release,
  reviewer-record, and field-deviation process.
- [`docs/inspection-maintenance.md`](docs/inspection-maintenance.md):
  commissioning and inspection-record framework pending reviewer approval.
- [`docs/materials.md`](docs/materials.md): confirmed and provisional material
  requirements.
- `mini_moonboard/`: CadQuery source and export command.
- `exports/`: committed STEP and dimensioned SVG outputs.
- `.github/workflows/ci.yml`: lint, test, CadQuery smoke, and stale-export
  checks on every push and pull request.

## Safety

A climbing wall is a life-safety structure subject to dynamic loads. Moon
Climbing instructs builders to seek professional advice if they have any doubt
about construction. Have the completed frame design, connections, substrate,
and installation reviewed by a qualified carpenter, climbing-wall builder, or
structural engineer before producing a build guide or beginning construction.
