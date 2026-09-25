# Current kerf-right kicker edge obligation

**Disposition:** continuous direct timber backing under the whole inner kicker
edge is not an explicit adopted criterion. The current geometry does show no
center-post backing beneath the seam, but it does not yet prove or disprove the
required edge-support paths. Treat both inner edges and the center seam as an
open panel-support and load-transfer check, not as a demonstrated geometry
failure or an implied mandate to add a continuous member.

## Source obligations

The frozen [selected-candidate criterion](../floor-runner-mvp-criteria.md#adopted-assessment-criteria)
`actual_kicker_cutouts` is an identity check: its target is the “Whole-kicker
inventory for this candidate,” its pass condition is “Exact expected
inventory,” and its evidence is “FR-3 and fresh case.” It does not specify
continuous backing. The wood-joints
[`actual_kicker_cutouts` mapping](criteria-method-map.md) adds preservation of
both inner edge-support paths and all 66 panel/kicker axes.

The pending
[`center_kicker_receiver_paths`](criteria.json) obligation is to connect both
center receiver sides to the frame and both inner edge-support paths. Its
method-map entry calls for tracing all four center axes and both edges into
supported frame paths, including screw engagement/resistance, edge
bearing/splitting, and complete-case forces. `complete_load_path_coverage`
requires each duty to reach the frame/floor through actual interfaces. Owner
scope retains all 66 panel/kicker screws and their purchase policy; it permits
recorded axis moves and requires backing, edge support, installation, and load
transfer to be rechecked
([plan](../bolted-candidate-plan.md#binding-scope),
[owner input](../bolted-candidate-owner-inputs.json)). No source prescribes
continuous direct backing as the required architecture.

## What current geometry establishes

The current records cover `led-clearance-2x6-runner-seated-blocks-v1` at
`b1e8707d`: 58 screw stations remain at source locations and eight moves are
recorded. `round_kicker_left_center_1/2` enter
`base_post_center_left` and `round_kicker_right_center_1/2` enter
`base_post_center_right`; their modeled intersections are receiver geometry,
not Hillman thread engagement or resistance. The exact center seam
is 141.0725/142.8875 mm from the respective center-post inner faces; the posts
are 283.96 mm apart and cannot directly back the seam. Panels meet at a finite
5,056.957 mm² seam face and each has separate contact with `base_header`
(46,323.723 mm²), its center post, and outer post. These whole-face areas do
not establish inner-edge coverage. The two
`center_principal_cleat`-to-kicker pairs are zero-area tangencies, not bearing
support. See the [receiver screen](current-receiver-screen.md) and
[contact graph](current-contact-graph.md).

Next, bind each current inner edge and finished support face, project the
contact patches onto the edge strips, and report covered intervals, gaps, and
unsupported spans. Use current `kicker_left/right`, post, and header solids;
do not reuse removed backer identities or old three-point samples. This is
potential-contact geometry only; the current records lack this projection.

## Mechanics and connection path still required

WJ-08/WJ-09 must use one frozen geometry and fresh simultaneous signed actions
from all six same-configuration cases. Check panel bending/cantilever, local
bearing and edge failure over measured spans; resolve seam/support opening and
transfer through unilateral contact and/or the 18 Hillman axes per kicker.
Use the actual plywood strength/layup basis. Do not credit friction, preload,
glue, equal screw sharing, or zero-area cleat tangencies; a CAD face is not an
active reaction.

Trace support reactions and screw groups through finished receivers to the
frame. Continue the four center-screw reactions from their posts through the
distinct post/header seat and post/cleat/header interfaces, resolving contact,
stiffness, signed actions, and load split. The [panel-screw mechanics
contract](wj24-panel-screw-mechanics-contract.md) gives two bounded Hillman
routes: a six-case zero-screw sensitivity proving independent support suffices,
or screw-dependent transfer checked by an applicable exact-product/joint
method. A failed span or frame-path check identifies what must be revised; it
does not establish continuous direct backing as an adopted requirement.
