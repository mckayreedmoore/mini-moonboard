# Round-passage candidate: analysis and remaining checks

The `round-bore-service-development` candidate is a development model, not a
construction release or an achieved climbing-weight rating. Use its own
[build draft](round-service-build-plan.md),
[drilling references](round-service-drilling/drilling.pdf) and
[connection schedule](../exports/round-bore-service-development/connections.csv).
The build draft includes the [tools and equipment](round-service-build-plan.md#tools-and-equipment)
required for the proposed operations.

## What changed

Four main panels have twelve screws each; two kickers have four each, for
56 panel attachments. Left/right positions are mirrored and the principal
rows share heights. This is a comparison layout, not a demonstrated minimum.
The preceding 87/75-screw comparison does not isolate the effect of this new
count because the new candidate also changes screw positions and timber passages.

The [initial layout audit](../fea/results/round-layout-initial-fit-v1.tar.gz)
preserves an instructive failure: all collision/fit gates passed, but the two
upper center screws had only 20.95 mm to the principal ends. This failed the
31.75 mm away/perpendicular and 44.45 mm reversible end-distance references.
The revised pattern lowers the shared top row while retaining mirrored,
straight, uniformly spaced principal rows and twelve screws per face.

Thirty-two enclosed 25.4 mm passages replace open wiring grooves. The routing
uses the owner's approximate 304.8 mm bulb-base pitch and 12.7 mm maximum
component diameter. The lights install after the panels, with the intact strand
fed through the passages. Modeled route length and clearance do not demonstrate
physical feeding, bend limits or installation slack.

Eight leg bolts retain a head, nut and two washers each, with nuts inside.
Commercial brackets retain their specified structural screws. The panel screws
have a nominal 90-degree, 8.128 mm flat-head envelope and matching flush seats.
The modeled 2.6035 mm cone is not a shop countersink depth: establish the seat
with the received screw and a controlled setup on representative plywood.

## Current geometry and product-reference checks

The [current audit](../fea/results/round-service-audit-v1.json) passes all its
tested geometry and product-spacing gates. It authenticates the exact layout,
56 panel/kicker screws, eight complete leg bolt stacks, 24 brackets with
144 specified screws, 132 lights, 131 inter-light routes and 32 round passages.
No tested wood, bracket, fastener or electrical collision remains. Both upper
center screws now have 46.9 mm to the principal end, above the 44.45 mm
reversible end-distance reference.

The 50.95 mm independent center panel-edge overhang remains. Passing these
geometric references establishes neither panel resistance nor equal screw load
sharing. Round-passage residual sections, bracket capacity and actual wiring
installation remain separate checks.

## Fresh coupled-frame diagnostic

The [three-case native archive](../fea/results/round-frame-batch-v1.tar.gz)
contains input decks, solver output, source snapshots, active-contact iterations
and reports for the revised geometry. All three final probes pass their global
equilibrium, interpolation and compression-only bearing checks.

| Loaded hold | Maximum panel movement (mm) | Maximum timber movement (mm) |
| --- | ---: | ---: |
| F10 | 25.523 | 22.337 |
| C6 | 20.846 | 18.196 |
| C10 | 17.012 | 13.618 |

These are absolute modeled displacements, not panel deflection relative to its
supports or comparisons with a verified serviceability criterion. Inputs remain
250 lb body mass, twice body weight downward, 300 N horizontal force, a 100 mm
hold standoff and a 20 × 20 mm load patch. Timber and plywood remain isotropic
at 7,000 MPa; connection springs remain 1,000 N/mm in each direction. Feet are
clamped in this diagnostic, so it does not establish unanchored-floor behavior.

The retained rectangular timber surrogate is extracted from the round-bored
wood afresh. It excludes material in front of the deepest passage over the whole
member length; that is a stiffness idealization, not an exact perforated-member
model or a strength bound. Local bore/countersink stresses, actual plywood
orthotropy, connection failure and cyclic response remain unresolved.

The [signed fastener screen](../fea/results/round-panel-fastener-screen-v1.json)
finds a maximum withdrawal demand of **1.551 kN** at
`round_panel_upper_left_center_3` in F10. This is **2.114 times** the optimistic
unadjusted 0.734 kN withdrawal reference and **1.644 times** the conditional
0.943 kN head reference. Maximum lateral demand is 1.038 kN at the adjacent
top center screw. No applicable adjusted combined-action capacity is established.
The head reference additionally requires plywood properties not established for
the owned Roseburg stock. These are screening flags, not proven physical failure
or evidence that a particular larger screw count is necessary.

### Sensitivity to load assumptions

The [F10 load-assumption archive](../fea/results/round-load-sensitivity-v1.tar.gz)
changes one input at a time on the identical frozen mesh, attachments and gravity
load. All three probes pass the same numerical equilibrium/contact checks.

| F10 scenario | Maximum panel movement (mm) | Maximum screw withdrawal (kN) |
| --- | ---: | ---: |
| Baseline: 2× body weight, 300 N horizontal, 100 mm standoff | 25.523 | 1.551 |
| Body multiplier reduced to 1; other inputs unchanged | 15.720 | 0.849 |
| Horizontal force removed; other inputs unchanged | 22.071 | 1.413 |
| Standoff reduced to the front surface; other inputs unchanged | 26.145 | 1.293 |

The front surface remains half a panel thickness from its modeled midsurface,
so the last case still has the corresponding moment arm. Reducing individual
loads or offsets need not reduce every displacement in this coupled system.
Even the 1× body-weight probe exceeds the optimistic 0.734 kN withdrawal
reference. This does not validate the baseline load assumptions or establish
physical failure: actual stiffness, materials, use loads and connection behavior
must be resolved. Do not select smaller assumed loads merely to obtain a pass.

These probes support questioning the selected loads, but do not establish that
the numerical checks are too strict. No probe changes the 56 attachments, spring
stiffness, plywood properties, load-patch size or support conditions. The 1×
case still includes the 300 N horizontal force and 100 mm standoff; it is not a
simple hanging-body test. All three maxima remain at the same upper-left center
screw. The baseline and three variations are insufficient to establish a
minimum screw count or to transfer the performance of a different twelve-screw
commercial panel/frame assembly. Keep the twelve-per-panel comparison layout;
resolve the assumed connection stiffness and actual plywood/fastener resistance
before changing the count solely to reduce these calculated demands.

The archive replay test authenticates the F10 parent report and final input,
then checks identical nodes, elements, framing, passages, attachment springs
(apart from the solved contact active set), and reconstructed loads. This ties
the study to the final 56-attachment candidate rather than an earlier frame.

## Mass and rigid-floor screen

Fresh CAD integration gives **167.079 kg (368.35 lb)** for the represented
frame, panels and structural hardware. Assumed densities are 600 kg/m³ for
wood/plywood and 7,850 kg/m³ for steel. Holds, their unmodeled hardware and
electrical components are excluded; this is not a measured finished weight.

The [source-bound floor evidence](../fea/results/round-service-floor-v1.json.gz)
contains 1,296 finite load cases at each assumed friction coefficient. Only
four posts and two leg feet receive support credit; kicker edges do not.

| Assumed friction | Feasible polygon witnesses | Infeasible polygon cases | Cases proven impossible by a circular-friction necessary condition |
| --- | ---: | ---: | ---: |
| 0.1 | 533 | 763 | 720 |
| 0.2 | 1,296 | 0 | 0 |
| 0.4 | 1,296 | 0 | 0 |

The other 43 polygon failures at friction 0.1 are inconclusive for circular
friction cones. Independent replay checks the saved forces, moments, contact
normals and friction inequalities. A feasible rigid witness does not qualify
the actual floor, leg connections or flexible structure. Actual friction,
contact conditions and delivered mass remain unverified.

## Qualification boundaries

Keep the owned Roseburg plywood. Its actual thickness, stamp, strength axis and
properties must be checked; a Structural I research reference is not permission
to substitute those properties into this model. The
[assumption verification ledger](provisional-design-assumptions.md) separates
analyst-selected inputs from published conditional reference values.

Remaining decisions include panel and connection resistance, local drilled
sections, floor behavior, actual harness installation and supported assembly or
disassembly stages. The [insert repair guide](threaded-insert-repair-guide.md)
requires a separate damaged-wood assessment and physical evidence; nominal
reserve space does not authorize a repair. The
[fresh insert assessment](../fea/results/round-insert-repair-v1/report.json)
passes all 56 nominal reserve/head-clearance checks, but effective thread
engagement, recess, seating and actual repair resistance remain unqualified.

## Reproduction

These commands create new evidence/output locations; generators refuse to
overwrite existing published results. Use a fresh checkout or new output paths
when repeating a study.

```sh
uv run python -m fea.round_service_audit --output /tmp/round-audit.json
uv run python -m fea.round_service_floor --output /tmp/round-floor.json.gz
uv run python -m fea.round_panel_frame --hold F10 --output /tmp/round-f10
uv run python -m fea.round_insert_repair_assessment --output /tmp/round-insert-fit
uv run pytest -q tests/test_round_frame_evidence.py tests/test_round_service_floor_evidence.py tests/test_panel_load_sensitivity.py tests/test_round_load_evidence.py
```

The native archives include their batch launch scripts. The frame runner needs
the pinned solver container image recorded in each report. Replay tests require
no solver and independently check saved output against the recorded inputs.
