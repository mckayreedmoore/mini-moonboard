# Mini MoonBoard

A Python/CadQuery project exploring a timber frame for a Mini MoonBoard-sized
climbing wall. Python builds the parts, hardware and machining geometry;
CadQuery exports STL meshes, STEP assemblies and JSON metadata. A static
Three.js browser viewer displays those pre-generated assets, with part picking,
connection inspection, hold previews and shareable problem highlights.

**[V9 cleats, 4×6 top and eight-bolt outer corners · desktop local viewer](http://127.0.0.1:8767/?model=eoere-v11-v9-eight-bolt-preview&view=rear&holds=off)**

The current geometry is **`v11-v9-eight-bolt-v4`**. It restores V9's straight-sided cleats with two glued nominal ¾-inch plywood leaves per side. Each cleat has eight bolts, four into the sloping side and four into the upright. The two outer top corners have eight bolts each; the two center top connections retain four. Top and side stock is standard nominal 4×6, actual 88.9 × 139.7 mm, with no wood packers.

The [checked geometry receipt](docs/bolted-frame-development/owner-frame-v11/geometry-receipt.json) records 1,109 parts, 112 bolt stacks, 24 metal spacers, 24 angles and 66 Hillman axes. Nominal occupied clearance passes. The thicker top requires two 50.8 mm center-principal end trims and two matching upper-panel screw moves; two kicker screw positions move down 6.35 mm to clear the added bolts. Four added lower bolts use a provisional seven-inch Grade 5 / half-inch-spacer recipe. Delivered hardware, glue and complete joint strength remain unqualified.

**Fresh six-case calculations and all twelve independent replays are complete.** The [current conditional review](docs/bolted-frame-development/owner-frame-v11/reference-review.json), [physical-row connection calculations](docs/bolted-frame-development/owner-frame-v11/connection-capacity-followthrough.json) and [signed geometry checks](docs/bolted-frame-development/owner-frame-v11/geometry-applicability.json) use this model's own forces. Member and cleat references are below one. The [saved conditional Grade 5 specification](docs/bolted-frame-development/owner-frame-v11/grade5-property-comparison.json) gives zero force-only exceedances; generic-property flags remain preserved and complete joint/geometry qualifications remain unfinished. The [development summary](docs/bolted-frame-development/README.md) and [revision index](docs/bolted-frame-development/development-revisions.json) retain earlier studies separately. The viewer presents those fixed-load conditional results over the unchanged geometry; current cut/drill instructions and physical release are not established.

## Run locally

Use Python 3.12 and [uv](https://docs.astral.sh/uv/), from the repository root:

```sh
uv sync --locked
uv run python -m http.server 8767 --bind 127.0.0.1 --directory site
```

Open the [V9-derived geometry preview](http://127.0.0.1:8767/?model=eoere-v11-v9-eight-bolt-preview&view=rear&holds=off); Candidate 13 remains a separate historical viewer.
This serves committed visualization assets. It does **not** regenerate CAD or
replay an engineering study. Browser rendering also needs access to the pinned
Three.js modules on unpkg.com.

The current 4×6 viewer is included in the repository's site assets and uses the
normal port 8767 server above. Its runtime needs no ignored development outputs.
Candidate 13 and the earlier port 8780 preview remain preserved.

The [V11 development viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-v11-v9-eight-bolt-preview&view=rear&holds=off)
is published through the repository's successful-CI Pages workflow. A local
check or push alone does not establish deployment. Historical viewer choices
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
