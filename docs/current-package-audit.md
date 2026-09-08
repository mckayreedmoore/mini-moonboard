# Current package verification — September 8, 2026

Candidate: `wide-principal-development`. This audit checks consistency and
operation of the local review package. It is not structural certification or a
verification of the currently deployed GitHub Pages revision.

## Geometry, hardware and machining

**57 tests passed in 42.51 seconds**:

```sh
uv run pytest -q tests/test_wide_frame.py tests/test_wide_exports.py \
  tests/test_wide_machining.py tests/test_wide_machining_features.py \
  tests/test_wide_machining_drawings.py tests/test_wide_machining_evidence.py \
  tests/test_wide_bracket_axes.py tests/test_wide_purchase_bom.py \
  tests/test_selected_hardware.py
```

Coverage includes current CAD body validity and nominal collision checks,
bracket screw receiver intervals, reserved hold/LED service space, insert
receiver envelopes, post/header contact, complete saved machining replay,
part-local/world coordinate conversions, metric/imperial schedules, drawing
source/artifact hashes, purchase quantities and all published STL bounds.

The checked inventories remain 29 wood parts, 56 inserts, 18 angle bodies and
188 connection assemblies, for 291 selectable entries. The machining replay
checks 276 connection/member rows and the recorded through-bores, service
reservations, countersinks, bearing planes, housings and counterbores.
Nominal clearance and source consistency do not establish machining tolerance,
installation feasibility under every real-stock variation, or resistance.

## Browser operation

The existing `scripts/check_mvp_viewer.cjs` passed for the current candidate in
headless Chromium at 1440 × 1000. An already installed Playwright package was
reused; no project dependencies or application code were changed. The test was
served from `site/` on temporary localhost port 8767, substituting only that port
for the script's default 8766 at runtime to preserve an existing server.

The check loaded all 291 meshes, selected the rear principal with actual pointer
input, verified dual-unit part text and the rear-view camera, and exercised the
grid-overlay/late-manifest update. Page-error and failed-request collections
were empty. Screenshots of the front, selected part, rear and grid states were
captured locally; front/grid images were visually inspected.

Observed usability limitation: the fixed control panel partly obscures the
reference person and nearby labels at this viewport. This is deferred interface
work, not a hidden structural discrepancy. This check does not claim mobile
coverage, every part's click accessibility, offline operation or live-site
deployment verification.

To repeat on an available port 8766, serve `site/` there and use:

```sh
node scripts/check_mvp_viewer.cjs /path/to/installed/playwright wide-principal-development
```

## Disposition

No new CAD or schedule defect was found in these checks. Retain the current
geometry for review while resolving the [six release gates](current-review-guide.md).
In particular, actual three-member leg-bolt behavior, no-glue-credit ply load
sharing, backing retention, panel-insert anchorage and unanchored contact are
not established by these passing package checks. Recent FE evidence remains
conditional; no build or climbing approval follows.
