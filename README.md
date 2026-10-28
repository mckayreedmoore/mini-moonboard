# Mini MoonBoard

A Python/CadQuery project exploring a timber frame for a Mini MoonBoard-sized
climbing wall. Python builds the parts, hardware and machining geometry;
CadQuery exports STL meshes, STEP assemblies and JSON metadata. A static
Three.js browser viewer displays those pre-generated assets, with part picking,
connection inspection, hold previews and shareable problem highlights.

**[Current local development · shorter bolts · four spacers](http://127.0.0.1:8767/?model=eoere-v11-shorter-bolts-preview&view=rear&holds=off)**

The active [114-bolt zero-spacer evaluation](docs/bolted-frame-development/owner-frame-v11/zero-spacer-eight-bolt/README.md) retains every eight-bolt joint and has its own [viewer route](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-v11-zero-spacer-preview&view=rear&holds=off), six-case bank and provisional hardware/template packet. It remains an unselected development candidate with recorded material and geometry limits.

The current geometry is **`v11-shorter-bolts-v1`**, selected by the [owner's spacer-reduction decision](docs/bolted-frame-development/owner-frame-v11/owner-shorter-bolt-selection.json). It retains V9's straight-sided cleats with two glued nominal ¾-inch plywood leaves per side, eight bolts per cleat, eight at each outer top corner and four at each center top connection. Top and side stock remains actual 88.9 × 139.7 mm, with no wood packers.

The [checked geometry receipt](docs/bolted-frame-development/owner-frame-v11/shorter-bolts/geometry-receipt.json) records **1,089 parts, 112 bolt stacks and four metal spacers**, with 24 angles and 66 Hillman axes. Twenty shorter header/cleat bolts replace their longer versions and their twenty sleeves are removed; frame, cleats, holes, axes, heads and washer seats stay fixed. The [original 24-spacer V11 viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-v11-v9-eight-bolt-preview&view=rear&holds=off) and all its evidence remain preserved. Fully threaded and zero-spacer alternatives remain unselected.

**Its own six-case calculations and twelve independent replays are complete.** The [matched review](docs/bolted-frame-development/owner-frame-v11/shorter-bolts/reference-review.json), [signed geometry](docs/bolted-frame-development/owner-frame-v11/shorter-bolts/geometry-applicability.json) and [current joint disposition](docs/bolted-frame-development/owner-frame-v11/shorter-bolts/current-joint-disposition-v5.json.gz) retain the conditional references, diagnostics and unresolved connection qualifications. The [development summary](docs/bolted-frame-development/README.md) and [revision index](docs/bolted-frame-development/development-revisions.json) separate current selection from preserved evidence. Delivered hardware, bond, floor and complete joint strength remain unqualified; no purchase, cut/drill, fabrication, climbing or structural release follows from selection.

## Run locally

Use Python 3.12 and [uv](https://docs.astral.sh/uv/), from the repository root:

```sh
uv sync --locked
uv run python -m http.server 8767 --bind 127.0.0.1 --directory site
```

Open the [current four-spacer development viewer](http://127.0.0.1:8767/?model=eoere-v11-shorter-bolts-preview&view=rear&holds=off); the original V11 and Candidate 13 remain separate historical choices.
This serves committed visualization assets. It does **not** regenerate CAD or
replay an engineering study. Browser rendering also needs access to the pinned
Three.js modules on unpkg.com.

The current 4×6 viewer is included in the repository's site assets and uses the
normal port 8767 server above. Its runtime needs no ignored development outputs.
Candidate 13 and the earlier port 8780 preview remain preserved.

The [existing four-spacer public viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-v11-shorter-bolts-preview&view=rear&holds=off)
retains its own assets. The new selection and labels are local until the normal
successful-CI Pages workflow runs outside the commit/push blackout. Historical viewer choices
remain available; the selected baseline remains the no-query default.

For a reproducible CAD export, start with the
[preserved-baseline software walkthrough](CONTRIBUTING.md#software-walkthrough).
It builds into a separate directory from tracked inputs. Latest-development
regeneration and structural replay have additional ignored input requirements.

## Find your way around

| Role | Entry point |
| --- | --- |
| Python models and shared geometry | [mini_moonboard/](mini_moonboard/) |
| Normal commands and one end-to-end pipeline | [Contributor guide](CONTRIBUTING.md#software-walkthrough) |
| Browser application and generated display assets | [site/](site/) |
| Portable checks and explicit evidence/history selection | [Tests and checks](CONTRIBUTING.md#checks) |
| Active bolted-frame development | [Development summary](docs/bolted-frame-development/README.md) |
| Preserved selected baseline | [current-candidate.json](current-candidate.json) and [baseline documents](docs/README.md) |
| Earlier designs, failed experiments and lessons | [Design history](docs/history/design-history.md) |
| Mesh sharing and evidence recovery | [Repository agreements](AGENTS.md) and [recovery instructions](CONTRIBUTING.md#current-development-and-input-recovery) |

The preserved selected baseline is `compact-floor-flush-development`.
`current-candidate.json` identifies that screw-and-bracket baseline;
`docs/bolted-frame-development/development-revisions.json` separately identifies
active bolted development. The viewer's no-query default remains the baseline.
Use the explicit demo links above for current development.

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before editing.
Historical-looking Python modules can still be live dependencies; frozen
producers and evidence retain their original identities.

## Scope

Independent DIY project; not affiliated with or endorsed by Moon Climbing.
These are engineer-unreviewed conditional records with unresolved strength
findings, not fabrication or climbing approval. Software checks establish
consistency within their scope, not physical safety. The selected baseline,
current development and historical studies keep separate evidence and limits.

<details>
<summary>Current development scope and engineering findings</summary>

Candidate 13 contains 22 sawn members, four nominal half-inch plywood leaves
bonded into two cleats, 24 angles, 116 bolt stacks and 66 Hillman screws.
Its own six 250 lb cases use a 2.0 downward multiplier and 300 N horizontal
force, with two independent replays each. Timber, cleat and steel reference
families are below one; 26 trial bearing flags across 13 components remain.
Those signature-group diagnostics are not established complete NDS joint
capacities or physical safety margins. Complete joint/geometry, screw,
bond, delivered hardware and support/contact qualification remain open.

The [development entry](docs/bolted-frame-development/README.md) and
[Candidate 13 layout](docs/bolted-frame-development/owner-frame-v10/layout.md)
route to the portable source-bound viewer and conditional planning packet.
V9 and older candidates retain their geometry and results. Fabrication,
drilling, structural assembly and climbing remain on hold.

</details>
