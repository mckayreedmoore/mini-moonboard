# Mini MoonBoard

Source-backed requirements and parametric CadQuery models for a freestanding
Mini MoonBoard.

## Status

This repository currently models the official Mini MoonBoard panel envelope.
It contains a provisional v1 climbing-surface and freestanding-leg concept.
It includes a provisional, pre-audit frame, BOM, cut list, and assembly draft.
It does **not** contain a structurally approved or build-ready design.
Structural connections, actual material, floor interface, and stability still
require human review.

The eventual design target is an indoor, freestanding plywood A-frame inspired
by the reference photo and Moon Climbing video. The climbing panels will be
fabricated from birch plywood rather than purchased pre-drilled.

The v1 renders are review artifacts, not approval evidence. The official
reference-envelope exports remain separate from the v1 frame artifacts.

## Reference dimensions

| Property | Metric | Imperial |
| --- | ---: | ---: |
| Main climbing surface | 2440 x 2440 mm | 8 ft x 8 ft nominal |
| Official kicker | 150 mm | 5.9 in |
| Angle from vertical | 40 degrees | 40 degrees |
| Official overall envelope | 2440 x 1569 x 2020 mm | 8.01 x 5.15 x 6.63 ft |
| Main panel thickness | 18 mm | 0.71 in |

V1 uses a 225 mm total kicker: the official 150 mm active zone plus a 75 mm
blank extension below it. The crash pad is a separate, excluded element.

## V1 concept render

![CAD-derived underside climbing-face rendering of the Mini MoonBoard V1 assembly](exports/mini_moonboard_v1_cad_front_render.png)

This raster view is tessellated directly from the V1 CadQuery assembly and
looks upward at the underside—the climbing face. Holds are intentionally not
modelled as arbitrary solids: their 142 exact through-bore provisions are in
the CAD. The 132 LED bores are likewise modelled, while the purchased V5 kit's
controller/cable route remains an installation-audit item until its supplied
guide and installed wire lengths are verified. Rails, bearing blocks, wiring,
and legs belong on the opposite support side.

[Open the interactive V1 3D model](https://mckayreedmoore.github.io/mini-moonboard/) to rotate, pan, zoom, and select a part for bilingual cut-list dimensions.
The viewer also shows the 16 specified structural bolts and 60 primary
rail-to-panel screw axes as selectable cyan, thread-free connection geometry.
Those are the connection locations to be represented in the screening FEA; they
are not a claim that cosmetic cylinder solids model fastener strength.
Use its panel-overlay selector for no labels, amber grid labels, or
high-contrast grid labels. The letters A–K and rows 1–12 follow the canonical
panel datums. Moon-branded artwork is deliberately not bundled until there is
written permission to rehost it publicly; see the official [artwork archive](https://moonclimbing.com/media/moonboard-pdf/Final_Artwork.zip)
and the project [artwork policy](docs/panel-artwork.md).
Its independent overall-dimensions switch draws the provisional complete V1
assembly extents—2762.4 mm / 108.76 in wide, 1636.3 mm / 64.42 in deep, and
2150.8 mm / 84.68 in high—excluding the separate crash pad.

The [side profile](exports/mini_moonboard_v1_concept_side.svg),
[support-side elevation](exports/mini_moonboard_v1_rear.svg), and
[isometric support view](exports/mini_moonboard_v1_isometric.svg) remain
available as audit drawings. They are intentionally links rather than competing
hero images: the CAD-derived climbing-face render above is the clearest visual
summary of the assembly.

The complete pre-audit package—3D model, front/rear/side plans, cut list,
drilling schedule, purchasing estimate, and build sequence—is in
[`docs/v1-build-package.md`](docs/v1-build-package.md).
The accompanying [sheet-by-sheet nesting plan](docs/v1-sheet-nesting.md)
specifies the nine 4 x 8 plywood sheets and one-factory-width-main-panel-per-sheet route.
The [FEA handoff](docs/v1-fea-handoff.md) defines the STEP source, structural
idealization, required inputs, and load cases for qualified FreeCAD/CalculiX or
equivalent analysis; it deliberately contains no invented stress result.
The generated [unanchored stability screen](exports/mini_moonboard_v1_stability_screen.md)
currently finds the V1 footprint requires floor uplift under the sourced
top-row load, so it is a redesign gate rather than a build release.

## SketchUp reference geometry

The supplied reference model can be extracted for inspection without making it
part of the V1 design: `uv run python scripts/import_sketchup.py INPUT.skp
OUTPUT.obj --summary OUTPUT.json`. The OBJ is in millimetres and retains named
hierarchy groups; the optional JSON reports each group's transformed bounds and
face count. Both open or inspect in FreeCAD, Blender, or an online OBJ viewer.
They are comparison-only: do not copy their dimensions or connections into V1
without an explicit audit.

## Development

```bash
uv sync
uv run ruff check .
uv run pytest
uv run python -m mini_moonboard.export
```

`site_inputs` is a separate, deferred site-and-pad worksheet validator; it is
not a V1 build-package gate.

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
- [`docs/site-survey.md`](docs/site-survey.md): deferred human-audit worksheet;
  its crash-pad, room, and egress sections are outside v1 scope.
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
