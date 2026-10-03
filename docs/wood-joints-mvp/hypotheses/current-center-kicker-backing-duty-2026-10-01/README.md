# Current center-kicker backing and receiver duties

This source audit describes the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` wood-joint candidate. It uses the
existing final panel-receiver join, finished-feature and stock records,
contact graph and all-body face atlas. It imports no STEP and runs no CAD
query, geometry rebuild or native solve. The selected baseline and all
historical evidence remain preserved.

Both kicker rear inner edges lie at X = -1.5875 mm, Y = -36 mm, from
Z = 0 to 277 mm. The finite header contact reaches those edge lines over
Z = 238.9 to 277 mm, a 38.1 mm interval. No finite rear timber patch reaches
either edge line over the lower 238.9 mm. The nearest center-post faces sit
141.0725 mm from the left edge and 142.8875 mm from the right edge. These
are geometric stand-offs, not accepted mechanical spans or failed criteria.

The [projection method](backing.py) validates the saved source-face hashes,
STEP bindings, opposed face-pair joins and rectangular outlines with
contained, disjoint full circular holes. It reconstructs their areas before
projecting material intervals. It retains all 97 kicker-to-other-body pairs:
19 broadphase candidates comprise 11 finite opposed pairs, four exact
separated pairs and four unresolved pairs; the other 78 pairs were separated
only by the upstream AABB screen. Each census row retains its state and
upstream broadphase flag, so the exact-separated and AABB pair identities
remain distinguishable. Unsupported trim is refused rather than
replaced by its bounding box.

The report preserves the source-derived strip-width thresholds for each
rear timber patch. A strip must reach past the post-face stand-off before it
has positive-width intersection with that post. The saved 18.25625 mm panel
thickness is also shown as one reporting width; its supported Z interval
matches the edge-line result. This width is not a required bearing width.
Source signatures are rounded to nine decimals, with their recorded geometry
and arithmetic comparison limits; no new physical tolerance is adopted.

The finite 5,056.957 mm² kicker seam and the small upper kicker/main-panel
bevel contacts remain panel-to-panel geometry. Floor and outer-post contacts
remain separate context. Zero-area center-principal-cleat tangencies are
unresolved and receive no backing credit. Finite areas establish neither
active contact nor force transfer.

The [duty join](duties.py) reconciles the four moved center screws with their
current center posts and finished bore patches. The 45.24375 mm nominal
receiver overlap remains occupancy evidence, not installed engagement or
Hillman resistance. It preserves all 66 panel/kicker screws, the 58 retained
and eight moved stations, and the existing Hillman 42605 purchase/pilot policy.
There are 18 kicker screws in total, nine per kicker. The phrase “18 Hillman
axes per kicker” in the separately pinned current edge-obligation note is a
count error; the current 66-axis inventory supplies the count used here.
That shared note is not edited by this secondary.

Each center post has a distinct direct header seat. Its alternative
connection route runs through two post-to-center-post-cleat bolts and two
cleat-to-header bolts per side. In particular, `center_post_header_*` names
join header to cleat, not header directly to post. The eight structural
candidate bolt duties, their receiver identities and proposed stock remain
separate from the four Hillman axes. Old inner-kicker backers are absent;
their three-point sample results and old acceptance do not transfer.

The existing four center screws supply 84 same-state records across seven
increments of each of three rear cases. Their signed forces, moments,
source application points and rounding bounds remain diagnostic inputs.
The refused recursive reduced-DOF projection stays distinct from the
separate physical-owned endpoint reconstruction. No screw action is
allocated between the direct seat and cleat route. Six-case responses,
active contact, plywood support/edge resistance, exact-product screw
resistance, stiffness and complete receiver-to-frame qualification remain
open.

Continuous direct backing under the whole inner edge is not an adopted
criterion. The measured gap therefore supplies no mandate to add a member
and establishes no revision need by itself. A future failed support/span or
complete-path check must identify the affected detail and its dimensional
consequences before any reviewed geometry is altered. This audit preserves
the climbing surface, panel outlines, 66-screw policy, 92 candidate axes and
twelve starting frame-bolt arrangements and authorizes no physical work.

## Historical provenance limitation

The atlas artifact, geometry producers, exact STEP bindings and numerical
inputs authenticate against their saved bytes. Its historical 217-source
closure has one changed prose pin, `criteria-method-map.md`. The
[dependency note](source-dependency-note.md) traces that file's hash-only
use and records both hashes. The broad historical closure remains
`REFUSED` with `STALE_PROSE_INPUT`; this packet neither repins history nor
claims its public verifier passes. Every original upstream binding remains
represented, and current authority is separately pinned. Any other changed
source stops the producer. Current authority must also match this candidate,
revision and the already authenticated scene, report and snapshot bindings;
the three pending support/path criterion IDs must be unique and complete.

## Reproduction

The [plan](plan.md) records the bounded source-only scope. Exact production
and verification read the frozen local JSON/source closure:

```bash
uv run python docs/wood-joints-mvp/hypotheses/current-center-kicker-backing-duty-2026-10-01/produce.py --write
uv run python docs/wood-joints-mvp/hypotheses/current-center-kicker-backing-duty-2026-10-01/produce.py --verify
```

Both commands are metadata-only. `backing-duty.json` and `source-pins.json`
are ignored local evidence. A clean checkout without those sources can run
the focused synthetic tests; they import no CAD or native runtime:

```bash
uv run pytest -c /dev/null --rootdir docs/wood-joints-mvp/hypotheses/current-center-kicker-backing-duty-2026-10-01 docs/wood-joints-mvp/hypotheses/current-center-kicker-backing-duty-2026-10-01
```

The final [review record](review.md) records exact artifact hashes,
independent comparisons and review disposition. The primary owns final
integration, shared documentation, heavy-run coordination and Git.
