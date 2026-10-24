# Mini MoonBoard

A Python/CadQuery project exploring a timber frame for a Mini MoonBoard-sized
climbing wall. Python builds the parts, hardware and machining geometry;
CadQuery exports STL meshes, STEP assemblies and JSON metadata. A static
Three.js browser viewer displays those pre-generated assets, with part picking,
connection inspection, hold previews and shareable problem highlights.

**[Current packer-free 4×6 development viewer · desktop local](http://127.0.0.1:8767/?model=eoere-packer-free-standard-stock-preview&view=rear&holds=off)**

The current geometry is **`v10-packer-free-flush-return-far-row-only-v1`**. The top and both side rails
are standard nominal **4×6, actual 88.9 × 139.7 mm**, following the
[owner's no-packers direction](docs/bolted-frame-development/owner-frame-v10/owner-no-wood-packers-v1.json).
Fresh geometry, all six cases and both replays, net sections, grips,
rear-joint geometry and clearance are complete. The declared vector section
indices are **0.914625 left side, 0.872071 right side and 0.613288 top**.
[The matched evaluation](docs/bolted-frame-development/owner-frame-v10/packer-free/evaluation.json)
preserves **15 bearing diagnostic rows across eight bolts**. Complete connection,
splitting, fitting/hardware and physical checks remain unresolved. Lengths
remain provisional; no wood packers remain. No purchase or physical release.
The deeper-side results and group benchmarks remain history and were not transferred.
The [current provisional wood list](docs/bolted-frame-development/owner-frame-v10/standard-stock-planning.md)
replaces the historical 4×8 side-stock allocation and credits usable owned material first.

## Run locally

Use Python 3.12 and [uv](https://docs.astral.sh/uv/), from the repository root:

```sh
uv sync --locked
uv run python -m http.server 8767 --bind 127.0.0.1 --directory site
```

Open the [preserved Candidate 13 viewer](http://127.0.0.1:8767/?model=eoere-current-frame-development&view=rear).
This serves committed visualization assets. It does **not** regenerate CAD or
replay an engineering study. Browser rendering also needs access to the pinned
Three.js modules on unpkg.com.

The current 4×6 viewer is included in the repository's site assets and uses the
normal port 8767 server above. Its runtime needs no ignored development outputs.
Candidate 13 and the earlier port 8780 preview remain preserved; no site deployment is performed.

The [published demo](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-retained-2x6-frame-development&view=rear)
shows the preserved 102-bolt revision. The published site checked at commit
`6ded8620` does not yet recognize the local current-model key; use the local
demo for the newer geometry. Publication is separate from this cleanup.

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
