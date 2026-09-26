# Independent review of corrected left center-post motion attempt02

This read-only review covers the corrected left-post adapter, its parent-run
report, the shared envelope/intersection helpers, and the frozen STEP
manifest. I did not run CAD or regenerate geometry. All three focused tests
pass.

For the modeled post-removal scene, the report supports a straight
`base_post_center_left` translation of 140.7 mm in global `+Y`, with no
reported intersection above the configured `1e-6 mm³` volume tolerance. This
is a conservative modeled-scene result. It establishes no positive clearance
margin, support or staging method, usable tool/cable access, physical
transport, or complete removal sequence.

## Left-specific inputs and corrected assumption

The adapter pins the unchanged shared screen logic and configures the left
target and left panel: `base_post_center_left`, `kicker_left`, and current
panel screw axes `round_kicker_left_center_1/2`. The report records both
current axes as `[0, -1, 0]`; it checks the exported left post's planar faces
for outward normals aligned with `+Y`. Candidate bolt axes
`center_post_left_1/2` are recorded as transverse prerequisites and do not
define the motion direction. The target's pinned dependency row has no
retained frame-bolt axes to remove for this move.

Attempt01 is preserved. Its geometry result and machine dependency fields
were left-specific, but its operation-state prose incorrectly named
`center_post_right_1/2`. Attempt02 pins the attempt01 adapter and report,
then constructs the operation-state sentence from the new report's own
`candidate_axis_dependencies_assumed_removed` list. The sentence now names
`center_post_left_1` and `center_post_left_2`. The target STEP hash and
140.7 mm translation match attempt01, so the fix corrects the evidence label
without changing the screened geometry path.

## Endpoint and continuous envelope

The 140.7 mm endpoint is calculated after excluding only obstacles with strict
transverse X/Z bounding-box separation; touching transverse bounds remain in
the relevant set. Here `timber/base_header` is the sole relevant obstacle and
the final axial BBox gap is 1.0 mm. The other 209 obstacle boxes are strictly
transversely separated; independently, the endpoint target BBox is disjoint
from all 210 stationary obstacle BBoxes. This is an endpoint condition and
does not provide clearance at intermediate positions.

For the continuous path, the producer builds a convex hull from the target
STEP vertices and their translated copies, then verifies that the exact source
and endpoint BReps are contained in it. The hull has 32 vertices and 12
triangular facets. The intersection helper receives all 210 stationary
obstacles: bounding-box broadphase separates 209, while one exact BRep
intersection test runs and returns no hit above `1e-6 mm³`. Because the
conservative hull has no reported hit, exact nonconvex refinement is marked
not needed. This supports a no-overlap conclusion for the modeled straight
route; it does not establish a positive gap or quantify sub-threshold
intersection volume.

## Provenance and limits

The report producer digest matches the on-disk adapter
(`71b84ab0…fcfb05ec45`), and the report digest matches the parent execution
record (`ba7d4ff4…fc783995d`). I verified all 211 manifest-listed STEP file
hashes, the manifest digest, the report/execution source and report pins, and
the preserved attempt01 adapter/report pins. The report binds revision
`led-clearance-2x6-runner-seated-blocks-v1`, current geometry snapshot, source
inventory, grip report, configured shared screen, runner, and face-sweep
helper. The parent run returned code 0 with CadQuery 2.8.0, OpenCASCADE
7.9.3.1.1, NumPy 2.5.2, SciPy 1.18.1, and Python 3.12.3.

The report assumes all 92 candidate connector bodies/stacks, the left kicker
panel and its panel/kicker screws, holds/T-nuts, and lights were removed or
staged earlier; the remaining 60 retained physical roles and 131 modeled
wires stay stationary. Temporary supports, capture, workspace, staging,
actual cables, tool access, and handling are outside the model. The report
correctly leaves support/staging, transport, and a complete sequence
unestablished.
