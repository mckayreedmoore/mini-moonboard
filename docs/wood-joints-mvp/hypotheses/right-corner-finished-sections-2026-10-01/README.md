# Right corner finished sections

This development packet joins the complete saved five-body right-corner
boundary to exact grain-plane sections of the reviewed finished STEP solids
for `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`.

The members are `base_header`, `base_post_outer_right`, `base_side_right`,
`knee_outer_right_spine` and `knee_outer_right_inner_frame_block`. Six current
right-knee bolt axes have 14 receiver memberships. Their finished bore
centroids, source axis datums and native application points remain distinct
records. The complete header retains its opposite-side and center ports.

The [source plan](plan.py) preserves all 338 physical interfaces: 42 internal
to these five bodies and 296 boundary interfaces. It retains 380 in-scope
interface endpoints, 508 native body-load nodes and the 14 matched finished
bore patches. Coincident grain planes retain every identity. Proposed stock
frames are reporting coordinates, not observed delivered-stock datums.

The [action accounting](actions.py) retains signed forces, moment arms and
source rounding radii in each of the seven saved increments of A12-rear,
A1-rear and K12-rear. Before-plane, on-plane and after-plane point sums use
the same state. On-plane loads remain explicit jumps. Contacts and selected
or released floor channels retain their source provenance, including zero
released actions. The no-slip floor remains an unverified analytical
assumption. Whole-body reconstruction compares with the preserved source
resultants; it adds no physical gate or tolerance.

The [producer](produce.py) authenticates the reused
[signed bolt join](../right-corner-signed-load-path-2026-10-01/produce.py) and
[complete boundary](../right-corner-whole-boundary-2026-10-01/produce.py),
verifies native and geometry source hashes, and queries each saved solid
using the frozen
[section kernel](../upper-outer-finished-sections-2026-10-01/section_geometry.py).
Disconnected planar regions retain separate areas, centroids and area
moments. Summed geometric properties and point-action resultants do not
establish strain compatibility, regional force sharing, recovered section
tractions or timber resistance. Transported point-force moments are not
bolt internal bending.

A station without positive-area properties retains its exact plane and source
identities, the kernel reason and null properties. A completed bounded BRep
intersection distinguishes empty or lower-dimensional geometry from a refused
query. The producer reports partial geometry when any such station exists;
it neither invents a positive area nor moves a native loading station. The
affected section has no accepted properties.

The October 1 bounded extraction completed all 271 planes: 270 have
positive-area properties and 36 of those have disconnected regions. The
`base_side_right` terminal plane near grain station zero returned an empty
BRep intersection and retains eight native body-load identities with null
properties. All 21 states and 5,691 cut records are retained, including the
21 cuts at that plane. This terminal result remains unqualified.

This packet changes no geometry, hardware policy or native response and
transfers no historical candidate pass. It adopts no resistance or criterion,
accepts no joint, establishes no six-case envelope and releases no physical
cuts, fabrication or climbing.

## Reproduction

Validate the exact metadata plan before coordinating a CAD replay:

```bash
uv run python docs/wood-joints-mvp/hypotheses/right-corner-finished-sections-2026-10-01/produce.py --plan-only
```

This source join reads frozen records and creates vector datums without
importing STEP solids or evaluating geometric sections. Its reused source
checker imports CadQuery for those vectors. The full replay queries the saved
solids and runs no native solver. Each CAD launch requires coordination with
the primary; the October 1 reservation authorized one extraction, which has
completed:

```bash
uv run python docs/wood-joints-mvp/hypotheses/right-corner-finished-sections-2026-10-01/produce.py --write
uv run python docs/wood-joints-mvp/hypotheses/right-corner-finished-sections-2026-10-01/produce.py --verify
```

`sections.json` and `source-pins.json` are ignored local evidence. Exact
reproduction requires the frozen local source closure. Source-only tests
exercise the pure plan/action methods and producer refusals without that
closure or CadQuery:

```bash
uv run pytest docs/wood-joints-mvp/hypotheses/right-corner-finished-sections-2026-10-01
uv run ruff check docs/wood-joints-mvp/hypotheses/right-corner-finished-sections-2026-10-01
```

The [validation record](review.md) records the frozen source closure, bounded
run, independent comparisons and review outcome. The primary owns heavy-run
coordination, final integration and Git; this secondary owns the packet.
