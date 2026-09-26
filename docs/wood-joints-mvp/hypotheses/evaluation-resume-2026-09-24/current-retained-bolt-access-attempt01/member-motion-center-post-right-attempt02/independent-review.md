# Independent review of right center-post motion attempt02

This read-only review covers the right-post producer, its parent-run report,
the shared envelope/intersection helpers, and the frozen STEP manifest. I did
not run CAD or regenerate geometry. The six focused producer tests pass.

For the modeled post-removal scene, the report supports a straight
`base_post_center_right` translation of 140.7 mm in global `+Y`, with no
reported intersection above the configured `1e-6 mm³` volume tolerance. This
is a conservative modeled-scene result. It establishes no positive clearance
margin, support or staging method, usable tool/cable access, physical
transport, or complete removal sequence.

## Direction, endpoint, and continuous envelope

The producer derives withdrawal from the current right-kicker panel screw
axes `round_kicker_right_center_1/2`, both `[0, -1, 0]`; it checks the actual
post's planar faces for outward normals aligned with `+Y`. The candidate
connector axes `center_post_right_1/2` are checked as transverse prerequisites
and do not define motion direction. The pinned member dependency row has no
retained frame-bolt axes to remove for this move.

The 140.7 mm endpoint is calculated after excluding only obstacles with strict
transverse X/Z bounding-box separation. Touching transverse bounds remain in
the relevant set. Here `timber/base_header` is the sole relevant obstacle and
the final axial BBox gap is 1.0 mm. The other 209 obstacle boxes are strictly
transversely separated; independently, the endpoint target BBox is disjoint
from all 210 stationary obstacle BBoxes. This is an endpoint condition and
does not give clearance at intermediate positions.

For the continuous path, the producer builds a convex hull from the target
STEP vertices and their translated copies, then verifies that the exact source
and endpoint BReps are contained in it. The hull has 32 vertices and 12
triangular facets. The intersection helper receives all 210 stationary
obstacles: bounding-box broadphase separates 209, while one exact BRep
intersection test runs and returns no hit above `1e-6 mm³`. Because the
conservative hull has no reported hit, the exact nonconvex refinement is
marked not needed. This supports a no-overlap conclusion for the modeled
straight route; it does not establish a positive gap or quantify sub-threshold
intersection volume.

## Provenance and limits

The report's producer digest matches the on-disk source
(`057a5e78…78bb81a7`), and its report digest matches the parent execution
record (`04bebd24…cfd6899`). I verified all 211 manifest-listed STEP file
hashes, the manifest digest, and the report/execution source and report pins.
The report binds revision `led-clearance-2x6-runner-seated-blocks-v1`, the
current geometry snapshot, source inventory, grip report, shared runner, and
face-sweep helper. The parent execution record reports return code 0 with
CadQuery 2.8.0, OpenCASCADE 7.9.3.1.1, NumPy 2.5.2, SciPy 1.18.1, and Python
3.12.3.

Compared with the pinned right attempt01 report (1816.646483 mm), attempt02's
shorter endpoint follows the strict transverse-relevance filter for endpoint
travel; the filter does not remove obstacles from the continuous envelope
collision pass. The report assumes all 92 candidate connector bodies/stacks,
the right kicker panel and its panel/kicker screws, holds/T-nuts, and lights
were removed or staged earlier; the remaining 60 retained physical roles and
131 modeled wires stay stationary. Temporary supports, capture, workspace,
staging, actual cables, tool access, and handling are outside the model. The
report correctly leaves support/staging, transport, and a complete sequence
unestablished.
