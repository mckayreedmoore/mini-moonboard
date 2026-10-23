# Mini MoonBoard

A Python/CadQuery project exploring a timber frame for a Mini MoonBoard-sized
climbing wall. Python builds the parts, hardware and machining geometry;
CadQuery exports STL meshes, STEP assemblies and JSON metadata. A static
Three.js browser viewer displays those pre-generated assets, with part picking,
connection inspection, hold previews and shareable problem highlights.

**[Current development demo · run locally](http://127.0.0.1:8767/?model=eoere-current-frame-development&view=rear)**

The current geometry is **`eoere-local-front-bolt-moves-v4`**. Its
[development entry and revision index](docs/bolted-frame-development/README.md)
record the exact model, engineering findings and remaining work. The viewer
runs entirely in the browser; it does not call a Python CAD backend.

## Run locally

Use Python 3.12 and [uv](https://docs.astral.sh/uv/), from the repository root:

```sh
uv sync --locked
uv run python -m http.server 8767 --bind 127.0.0.1 --directory site
```

Open the current-development link above.
This serves committed visualization assets. It does **not** regenerate CAD or
replay an engineering study. Browser rendering also needs access to the pinned
Three.js modules on unpkg.com.

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

The owner-directed model removes the two outboard knees, two leg packers and
508-mm top-rail extension. It has 20 sawn members, four trimmed nominal ¾-inch
plywood cleats at the lower header corners, 24 angles, 92 bolt stacks,
184 washers and 26 factory spacers. The 32 enclosed LED passages and 66 Hillman
axes remain. The lower front bolts now sit60mm above the floor, with upper bolts at100mm. Their own six-case references fall to0.937 wood bearing and0.893 bolt axial/bending. Cleat-row and upper-bolt-size trials were rejected for incompatible factory holes and edge distances. Its geometry clears nominal occupancy. The completed ideal-bond
investigation reaches1.066 nominal or1.129 with the thickness allowance on
the declared four-host floor basis; bolt and timber references also exceed1.0.
The full frame does not pass, and no preceding strength pass transfers.
The completed 102-bolt/extended-top evaluation remains preserved within its own
geometry. Panel/Hillman strength remains deferred and unresolved. Actual stock,
hardware, fit and floor are unobserved; no fabrication or climbing release.

</details>
