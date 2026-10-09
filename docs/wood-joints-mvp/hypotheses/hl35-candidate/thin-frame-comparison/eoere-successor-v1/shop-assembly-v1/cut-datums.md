# Raised-rail Eoere nominal cut and hole datums

These tables coordinate the reviewed 22-timber, 22-angle/two-cleat model,
its six panels, 100 physical bolt axes and 66 Hillman axes. They use saved
current geometry and extraction records; no CAD rebuild or new mechanics
evaluation supplies these coordinates. The conditional numerical findings,
reference exceedances and missing complete capacities retain their own limits.
Actual and Disposition cells are blank because delivered dimensions and holes
have not been observed. This packet does not release fabrication or climbing.

| Table | Coverage and use |
| --- | --- |
| [Members](members.csv) | 22 timber and six panel datums, proper local frames, nominal stock allowances and current finished-body source bindings. Includes both 38.1 × 139.7 × 289.7-mm cleats. |
| [Member end datums](member-end-datums.csv) | 184 timber raw-profile vertices, 48 timber end planes and 28 saved panel side-section vertices. Vertex indices identify source points; their order is not necessarily a perimeter traversal. |
| [Receiver holes](receiver-holes.csv) | All 120 saved finished receiver-wall occurrences for 100 unique shafts, with current world axes and local entry/exit datums. Count each shaft once when purchasing; multiple receiver rows describe one shaft's separate wood occurrences. |
| [Panel screw datums](panel-screw-datums.csv) | All 66 current Hillman axes, front-face origins in panel and receiver coordinates, and the four declared lower-axis moves. |

For a member-local point `[l,u,v]`, its world position is
`datum + L*l + U*u + V*v`. The listed basis vectors are unit vectors and
`L cross U = V`. For timbers, L follows nominal source grain; U/V do not
identify observed radial/tangential growth-ring axes. For panels, L increases
across world X, U increases upslope on the main panels or upward Z on the
kickers, and V points into backing. Panel frames describe geometry, not
observed veneer grain. The owner's recorded original eight-foot sheet direction
horizontal across X remains a separate assumption.
The CSV `source` keys resolve through `sources` in the input file; the text
after `#` identifies the corresponding saved JSON field.

Each `raw_end_plane` uses `outward_normal dot local_point = offset`.
Its normal-to-L angle is not automatically a saw setting. Raw profiles and
end planes exclude bores, service cuts and rear recesses. The twenty original
local timber profiles and end definitions are retained; only the two bottom
rail world datums gain the additional 30.625-mm board-tangent translation.
Current receiver entries/exits come from saved finished full-wall intervals,
rather than assuming the whole raw prism remains at each bore. They are
nominal coordinates, not measured bearing lengths or strength acceptance.

The [result](cut-datums-result.json) retains both 1:12 rear-recess definitions:
457.2-mm run, 38.1-mm maximum depth, world Z limits 0–141.7 mm and the right
cutter's −3.175-mm X translation. Its source profile is expressed in world X
and global grain projection S, separate from each member's local datum.
Do not replace it with an unshifted right cutter.

The six panel outlines retain the CAT 23/32 model thickness, 18.25625 mm.
Main-panel nominal width is 1217.6125 mm and upslope blank depth is 1219.2 mm;
kicker blank height is 277 mm. The kicker uses the Y=−36-mm backing slab
trimmed against the unperforated lower main-panel outline. The saved side
sections retain that seam profile; a square top substitute is not this model.
The current [geometry source](../occupied-bottom-rail-v1.json) also retains
all hold/T-nut and LED machining datums under `panel_machining.features`.
Nominal 3/4-inch backing is a separate sensitivity, not measured thickness.
The already cut panels' actual width and thickness remain to be reconciled;
a true 1219.2-mm width exceeds the modeled main width by 1.5875 mm.

Wire-cut definitions and all 131 fixed routes remain in that geometry source.
The recorded front-open cutter combines the route sweep at 8-mm depth with
a front-plane sweep of radius `sqrt(depth² + radius²)`; the wire cutter radius
is 6.35 mm and the recorded connector clearance radius is 9.35 mm.
These are analysis cutter envelopes, not delivered cable or machining
tolerances. Routes and world endpoints stay fixed when the rails move;
finished channels are not translated with the rails. Complete harness shape,
connector release, slack and bend radius remain unverified.

`modeled_bore_envelope_diameter_mm` and modeled underhead length describe
occupancy. They do not select drill bits, delivered lengths or shanks.
Factory holes, absolute heel offsets, formed bends and delivered tolerances
still need their own compatible product datums. No new tolerance is invented
here. The source's 6.35-mm service gap is a nominal allowance, not a machining
tolerance. Arithmetic verification limits in the input file only check saved
coordinate joins. This packet imports no physical test, tightening torque,
offcut proof or engineer-approval requirement from the selected-baseline shop
packet. It also transfers no predecessor tool, removal or resistance pass.

[Inputs](cut-datums-inputs.json) pin ten sources, including the actual raised
inputs SHA `81e9ad126f806a412a8bcb73ae3d0057ef3568ed0fa45986503f97fb5fb62d9f`,
current geometry SHA `ecfb27653a12ac326b1ba8cf4b051038d3de43db775bfc8f43e6c1a36be3744b`
and predecessor shop join SHA `7982d8612014d6d55279f7847798ea3bf87e6c2eca2fa585ef4457daf3787074`.
The result pins the helper and every output table. After recovering any archived
inputs through the [existing ledger](../../../../../completion-ledger.md#build-package-completion),
the following Python 3.12.3 standard-library command recomputes the tables in memory and
checks every output byte without changing them:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/cut-datums.py --check
```
