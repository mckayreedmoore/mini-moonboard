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
uv sync --locked
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

## Software walkthrough

The supported entry points are existing commands, not a universal configuration
or task-runner framework. Run them from the repository root after
`uv sync --locked`.

The routing checks use Node.js; this walkthrough was checked with Node 24.18.0.
Node is not needed to serve the existing viewer assets.

| Task | Command or reading path | What it establishes |
| --- | --- | --- |
| View the current development | `uv run python -m http.server 8767 --bind 127.0.0.1 --directory site`, then the [current local model](http://127.0.0.1:8767/?model=eoere-packer-free-standard-stock-preview&view=rear) | Serves existing assets; no CAD rebuild or structural replay |
| Fast portable checks | `node --test tests/*.mjs` and `uv run pytest -q tests/test_test_selection.py tests/test_viewer_mesh_assets.py` | Revision/document routing, preserved overlay contracts, test selection and mesh-sharing contracts |
| Normal maintained regression | The commands under [Checks](#checks) | The default maintained test selection, lint and CAD smoke check |
| Historical or recovered replay | The explicit pytest opt-ins under [Checks](#checks), after restoring their inputs | Those named evidence checks; missing inputs still fail |

A reproducible export path is the **preserved selected baseline**, not the
latest bolted development:

1. [current-candidate.json](current-candidate.json) names the baseline and its
   producers. [The width option](docs/floor-flush-width-option.md) distinguishes
   bought 4×4 panels from the kerf-right 4×8 presentation of that same candidate.
2. [floor_flush_width.py](mini_moonboard/floor_flush_width.py) adapts
   [compact_floor_flush_frame.py](mini_moonboard/compact_floor_flush_frame.py).
   The latter delegates some behavior through `previous` and `__getattr__` to
   older frame modules. Those modules are live source dependencies.
3. [floor_flush_exports.py](scripts/floor_flush_exports.py) supplies the selected
   model, width-specific metadata and source inventory. It uses shared helpers
   through [clear_space_exports.py](scripts/clear_space_exports.py), whose
   `shared` module is [no_shoes_exports.py](mini_moonboard/no_shoes_exports.py).
   Historical names here describe provenance, not unused code.
4. The shared exporter validates CAD bodies and writes `parts.json`,
   `models/*.stl`, `assembly.step` and `manifest.json`. The STEP file omits the
   electrical display; the manifest records that scope and source/artifact
   hashes. Existing STEP normalization preserves deterministic output.
5. [site/index.html](site/index.html) selects a model and loads its generated
   assets. [mesh-assets.mjs](site/mesh-assets.mjs) resolves shared STL aliases;
   design-specific overlays validate their own scene identities. The browser
   never imports Python or performs the CAD build.

Build only the official-width baseline into a new output directory:

```sh
moonboard_export_root=$(mktemp -d)
uv run python -m scripts.floor_flush_exports --width official --root "$moonboard_export_root"
```

The outputs are under
`$moonboard_export_root/hybrid/compact-floor-flush-development/`. This command
leaves the committed viewer and construction packets alone. To rebuild in a
temporary directory and compare against the committed official-width assets:

```sh
uv run python -m scripts.floor_flush_exports --width official --check
```

Dimensions are mostly Python constants and derived geometry; selected material,
hardware and wiring references are JSON. `design_inputs.toml` is an optional,
ignored site-input file, not a replacement for all model parameters. The tracked
baseline export above does not require private measurements or the latest
ignored mechanics banks. Current development producers do require their
recorded cached solids, fields and sources: use the
[recovery instructions](#current-development-and-input-recovery), and keep
serving, regeneration and structural replay as separate claims.

### Viewer modules

`site/index.html` owns model selection, guarded loaders, part picking and bolt
inspection. Presentation lives in `viewer-scene.mjs` (camera, lighting and render
loop), `viewer-holds.mjs` (approximate holds and problem links),
`viewer-annotations.mjs` (display-only pads, dimensions and reference person)
and `viewer.css`. Existing overlay modules retain their revision-specific
identity checks; `documentation-links.mjs` and `mesh-assets.mjs` keep document
routing and mesh aliases separate.

A rendered regression runs in CI as a separate viewer job, before waiting for
the full CAD suite. It first runs all Node contracts (`node --test tests/*.mjs`),
then uses Playwright 1.59.1 and Chromium against committed assets. A browser
failure fails CI; the normal maintained suite and existing validation gates
still run. Available browser JSON receipts are printed even after a failure.

For local checks, use an existing Playwright installation with Chromium. Serve
`site/` as above, then run from the repository root:

```sh
node scripts/check_viewer_browser.cjs /path/to/playwright http://127.0.0.1:8767/ /tmp/moonboard-browser.json
```

It checks the current model, baseline, kerf-right option and two historical
routes, plus picking, controls, problem links, navigation and error messages.
The optional fourth argument compares complete model snapshots from a preceding
checkout. Its full-run pass/fail flag remains in the new receipt, so a later
baseline interaction failure is still visible. HTTPS verification is enabled
by default. If a local proxy requires it, `VIEWER_BROWSER_IGNORE_HTTPS_ERRORS=1`
explicitly enables the override and records it in the receipt; CI does not set
it. No browser package is added to the Python lockfile. CI installs the pinned
package in its temporary directory and uses Playwright's documented
[`install --with-deps chromium`](https://playwright.dev/docs/browsers#install-system-dependencies)
to provision its browser and system libraries.

## Checks

Run checks affected by the change before committing. For code or model changes,
the normal repository checks are:

```bash
uv run ruff check --no-cache mini_moonboard fea scripts tests --extend-exclude fea/contact_wrench_benchmark.py
uv run python -m scripts.compact_viewer_meshes --run -- uv run pytest
uv run scripts/smoke_test.py
```

For navigation-only changes, check changed local links/fragments, viewer query
identities and any preserved historical payload hashes. Archive-only work also
needs verified restoration and unchanged-source checks. Those changes do not
justify a CAD rebuild, native solve or complete historical export.

Lint excludes immutable launch and search-controller snapshots under
`fea/results/`; preserve those source witnesses rather than reformatting them.
Maintained analysis code remains linted.
Ruff 0.16 expands the default rules. Exact source/rule waivers in `ruff.toml`
preserve issued native and analysis witnesses instead of changing their bytes.
`tests/frozen-lint-sources.json` pins all 78 waived files and their exact rules;
its active test rejects changed source bytes or an unrecorded waiver. Portable
maintained code and new helpers retain the current defaults. Executable shebang
files have executable Git modes. The five maintained packet directories are
also linted explicitly by [CI](.github/workflows/ci.yml).

The default test run covers the selected baseline, active development checks
and shared geometry, hardware and analysis utilities. Preserved historical-model
tests are opt-in:

```bash
uv run pytest --include-historical                 # Current and historical tests
uv run pytest --include-historical -m historical   # Historical tests only
```

`tests/historical.txt` lists excluded modules and historical cases within mixed
modules. New tests run by default unless explicitly added to that inventory.
Historical modules are excluded before import during normal discovery. Even an
explicit historical test path requires `--include-historical` to execute.
Shared calculations remain active even when their filenames name an older model.
The preserved no-shoes asset-provenance check is historical: its manifest records
its original environment hashes. Its geometry tests remain active, while the
selected candidate's artifact provenance and rebuild are checked in CI.
CI uses the same default; its manual workflow can also include historical tests
and the historical reference/V1 export comparison.
The current inventory additionally identifies old PB/WJ/barrel/thin-frame replay
tests that need frozen ignored source banks or earlier model/source bindings.
Those exact modules/cases remain available with `--include-historical`; missing
inputs and source drift still fail there. Synthetic yield calculations and
portable orchestration tests remain in the default suite. This separation does
not repair or requalify historical evidence, and no missing-file auto-skip is used.

Current qualification tests that authenticate recovered local source banks
have a separate, explicit opt-in:

```bash
uv run pytest --include-recovered-evidence
uv run pytest --include-recovered-evidence -m recovered_evidence
```

`tests/recovered-evidence.txt` lists exact functions whose frozen mechanics
fixtures also authenticate ignored historical fields, operators, cached solids
and standards. These remain current evidence checks, separate from the
historical inventory. Their original test and producer bytes are preserved.
The published qualification inventory at `e2ddd1a0` retained 387 portable
controls and 216 controls requiring recovery inputs; all 603 passed with those
inputs present. Later cleat work adds nine local-kernel controls in three
explicit function entries to the recovered inventory. Their unchanged kernel
stays at its frozen ignored path; algebra, source guards and mesh-pair controls
continue to run by default. Use pytest's collected counts for the current tree.
Selecting the opt-in never skips missing or changed inputs.
Nine small, unchanged helper/contract files are retained at their original
paths for the portable checks; large evidence banks and manuals stay ignored.
Use the [qualification recovery notes](docs/wood-joints-mvp/completion-ledger.md#engineering-closure-beyond-the-assessment)
alongside the navigation recovery kit below for the shared topology/review inputs.

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
caches. An earlier reduced-suite four-worker trial passed 299 tests in 23.4 seconds,
approximately the same as serial execution. Keep serial execution as the default;
additional workers did not improve this reduced suite in that trial.

Regenerate the selected baseline after changes to its source or geometry inputs:

```bash
uv run python -m scripts.floor_flush_exports
uv run python -m scripts.floor_flush_construction
uv run python -m scripts.current_candidate --check-exports
```

The selected modules and package references are recorded in
[`current-candidate.json`](current-candidate.json). Update that authority when
selection changes. `scripts.current_candidate` checks candidate identities,
source/artifact hashes, drawing-to-viewer links, the viewer default and leading
document references. Its reported manifest hashes identify the exact export and
drawing snapshots; a candidate name alone does not identify a revision.
Recorded assessments retain their own input revisions and open gates.
[`current-candidate-applicability.json`](current-candidate-applicability.json)
discloses the selected baseline's intentional two-clip geometry change after
its frozen six-case assessment. It supplements the original authority without
changing its bytes. Validation authenticates the preceding model inside all six
source archives and the exact live model digest, retaining strict checks on
every other source and artifact. Machine output derives a historical scope and
explicitly marks current mechanical acceptance unverified. This disclosure does
not transfer the preceding case passes or exempt current export rebuilding.
The [recorded-evidence inventory](docs/current-candidate-status.md) is checked
against those files, including criteria counts, geometry-snapshot agreement and
open gates. After an intentional assessment or geometry update, review the
inputs and refresh only that summary with
`uv run python -m scripts.current_candidate --write-status`; this command does
not recalculate or qualify the evidence. A passing
configuration check does not establish mechanical acceptance or fabrication release.
Use `uv run python -m scripts.current_candidate` for this check without a CAD rebuild.

The selected-baseline exporter builds all meshes, metadata and STEP from CAD without
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
CI always checks the selected-baseline rebuild and fails when its committed
artifacts are stale. The reference/V1 export check runs only when historical
testing is requested through the manual workflow.
The panel-datum CSV and SVG are also deterministic; the SVG is a visual
verification drawing only and must never be treated as a drilling template.

Viewer meshes share byte-identical assets through `site/mesh-aliases.json`.
Frozen `parts.json` and evidence manifests retain their original paths and
hashes; both selected plywood-width packets keep their meshes locally. For
tools that read legacy paths, temporarily restore independent mesh copies:

```bash
uv run python -m scripts.compact_viewer_meshes --run -- uv run pytest -q
uv run python -m scripts.compact_viewer_meshes --run -- uv run python scripts/build_prototype_weights.py
uv run python -m scripts.compact_viewer_meshes --check
```

The wrapper shares meshes again after a successful command. After a failed
command it removes unchanged temporary copies and preserves changed outputs
for inspection. Use it for historical exports and replays as well as tests.

Closed ignored experiment trees can be stored outside the checkout with
`scripts/evidence_archive.py`. Its `create` command writes a file-level hash
manifest, verifies the archive, restores a fresh external tree and checks every
restored file before permitting a separate `prune` operation. `restore` refuses
an existing destination. Retrieve historical raw paths from the verified tree
before running a replay that needs them; retained result packets and manuals
remain at their existing repository paths. See the
[cleanup record](docs/repository-cleanup-evaluation-2026-09-28.md) for archive
locations and the current keep/archive/delete dispositions.

## Current development and input recovery

The [compact bolted-frame entry](docs/bolted-frame-development/README.md) is the maintained
model/shop/response revision map. `current-candidate.json` continues to select
the preserved screw-and-bracket baseline. The original Eoere proposal contract
also retains its own revision; neither file selects a later development scene.
The active name is **Compact bolted frame**, `compact-bolted-frame-development`.
Its [checked index](docs/bolted-frame-development/development-revisions.json)
maps that name to the original evidence candidate and keeps geometry, optional
preview, shop overrides and response separate. Frozen Eoere/wood-joint IDs and
paths retain their meanings; the former entry remains a compatibility pointer.

Run the fast Git-only checks without CAD, a browser or recovered raw inputs:

```sh
node --test tests/test_bolted_development.mjs tests/test_documentation_links.mjs
uv run pytest --import-mode=importlib -q fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/z180-mechanics-inputs-v1/test_descriptor.py
```

The Node tests check revision/scene identities, incoming descriptions, rejection
controls and current-versus-history documentation routes. The Python test reuses
synthetic moment, source and output guards from the
separate proposal packet; it does not evaluate candidate strength. CI aggregates
this gate with its existing separately scoped checks. Keep the main entry within
150 lines and link detailed results from the existing ledger.

Pages now follows successful `CI` completion on `master` and checks out that
run's exact commit. It publishes the verified committed assets without rebuilding
them. Each Pages run names its triggering CI run ID and validated commit for
publication checks. To request publication manually, run **CI** on `master`; there is no
independent Pages dispatch that bypasses validation. See GitHub's
[workflow-run event documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run).

The latest geometry and scoped studies depend on ignored cached solids, fields,
operators, manuals and source banks. A Git clone supplies only part of those
inputs. Follow the [latest recovery update](docs/repository-cleanup-evaluation-2026-09-28.md#maintenance-changes-following-this-evaluation)
for the exact snapshot, companion manifests, external paths and recovery command.
Restore into a fresh external directory; compare required hashes before placing
missing inputs at their original identities. Preserve newer files and other
workers' tracked/untracked work. A recovery snapshot does not authorize pruning.

After recovering inputs, the existing cheap v3 source gate can verify its frozen
producer and rejection controls without executing CAD:

```sh
python3 -B scripts/check_eoere_2026_replay_inputs.py --out fea/generated/eoere-source-check-NEW.json
```

Choose a new receipt path for each call. This gate covers the preserved v3
inputs, not a new extended-cleat response or complete-joint resistance. CI's
baseline and earlier wood-joint checks retain their separate scopes; full Eoere
replays require the documented local inputs and explicit affected-check commands.

Keep the current development summary in `docs/bolted-frame-development/README.md`.
Update that page for routine continuation; link immutable experiments instead
of adding another dated status document. Preserve distinct frozen input states
and failed results when bundling completed experiments.

CadQuery dimensions are always millimetres. Documentation should show both
metric and imperial values and identify whether a value is source-stated,
converted, derived, or still unresolved.

Keep real site measurements in the ignored `design_inputs.toml`, created from
`design-inputs.example.toml`. Validate it before using a custom kicker value or
starting detailed frame design:

```bash
uv run python -m mini_moonboard.site_inputs design_inputs.toml
```

The reference model is not a structurally approved climbing-wall design.
Construction release follows the selected candidate's documented completion
gates and explicit conditional DIY scope; consistent software artifacts alone
do not establish resistance or release.
