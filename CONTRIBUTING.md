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

## Checks

Run checks affected by the change before committing. For code or model changes,
the normal repository checks are:

```bash
uv run ruff check .
uv run pytest
uv run scripts/smoke_test.py
```

For navigation-only changes, check changed local links/fragments, viewer query
identities and any preserved historical payload hashes. Archive-only work also
needs verified restoration and unchanged-source checks. Those changes do not
justify a CAD rebuild, native solve or complete historical export.

Lint excludes immutable launch and search-controller snapshots under
`fea/results/`; preserve those source witnesses rather than reformatting them.
Maintained analysis code remains linted.

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
The preserved no-shoes asset-provenance check is historical: its manifest records
its original environment hashes. Its geometry tests remain active, while the
selected candidate's artifact provenance and rebuild are checked in CI.
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
The [recorded-evidence inventory](docs/current-candidate-status.md) is checked
against those files, including criteria counts, geometry-snapshot agreement and
open gates. After an intentional assessment or geometry update, review the
inputs and refresh only that summary with
`uv run python -m scripts.current_candidate --write-status`; this command does
not recalculate or qualify the evidence. A passing
configuration check does not establish mechanical acceptance or fabrication release.
Use `uv run python -m scripts.current_candidate` for this check without a CAD rebuild.

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
node --test tests/test_bolted_development.mjs
uv run pytest --import-mode=importlib -q fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/z180-mechanics-inputs-v1/test_descriptor.py
```

The first checks revision/scene identities, incoming descriptions and rejection
controls. The second reuses synthetic moment, source and output guards from the
separate proposal packet; it does not evaluate candidate strength. CI aggregates
this gate with its existing separately scoped checks. Keep the main entry within
150 lines and link detailed results from the existing ledger.

Pages now follows successful `CI` completion on `master` and checks out that
run's exact commit. It publishes the verified committed assets without rebuilding
them. To request publication manually, run **CI** on `master`; there is no
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
