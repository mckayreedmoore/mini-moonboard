# Reported official pattern versus the frozen panel mounting

## Finite finding

The frozen model already has **12 screws on each main panel**: four on the
outer longitudinal receiver, four on the center longitudinal receiver, two
on its outer horizontal rail and two on its service rail. Thus the owner's
reported **four per edge, with corners shared by adjacent edges** agrees with
the count: `4 × 4 − 4 = 12`. Sharing means a corner belongs to two edges of
one panel; it does not mean one screw fastens two neighboring panels.

The current coordinates do not form four straight screw rows around a
rectangle. The upper panels' two top-rail screws are **65.95 mm farther up
the slope** than their four longitudinal-column endpoints. The lower panels'
two bottom-rail screws are **76.9 mm farther inward/up the slope** than their
column endpoints. These offsets are real model differences to examine before
selecting alternative hardware. Neither the count nor these offsets proves
the cause of the saved connection demands or a physical failure.

The [owner's video reference at 1:39](https://www.youtube.com/watch?v=wDB6Lg4x_lM&t=99s)
could not be fetched on October 2, 2026: the fetch returned “Online fetch
throttled.” The described pattern is used as an explicit comparison
hypothesis. This worksheet does not independently verify its screw locations,
spacing, fastener product or backing. The [historical video review](../../../../history/panel-screw-reference-review.md)
examined retained frames at 0:53–1:08 and could not certify the screw count;
that is a different interval from the requested 1:39.

## Frozen station and receiver comparison

Coordinates are in millimeters, projected from the saved global coordinates:

```text
X = global x
T = cos(50°) y + sin(50°) z    (up the inclined panel)
N = −sin(50°) y + cos(50°) z
```

All main screw origins have `N = 191.584718`; the modeled axis proceeds in
positive N. Suffixes below follow `round_panel_{upper/lower}_{left/right}_`.
Values are rounded to 0.001 mm for the table; the two offsets above are
computed before rounding.

| Stations per panel | Count | Current receiver | Upper panel T | Lower panel T |
| --- | ---: | --- | --- | --- |
| `rim_1` through `rim_4` | 4 | `base_side_{left/right}` | 1478.874, 1837.257, 2195.641, 2554.024 | 259.674, 618.057, 976.441, 1334.824 |
| `center_1` through `center_4` | 4 | `base_principal_center_{left/right}` | Same four values as rim | Same four values as rim |
| `edge_1`, `edge_2` | 2 | Upper: `base_rail_top`; lower: `base_rail_bottom_{left/right}` | 2619.974 | 336.574 |
| `service_1`, `service_2` | 2 | `base_rail_service_{upper/lower}_{left/right}` | 1478.874 | 1334.824 |

The outer column is at `X = −1200.150` on the left or `1196.975` on the
right. The center column is at `X = −70/+70`. Both horizontal pairs use
`X = −435.075, −835.075` on the left or `435.075, 835.075` on the right.
Consequently the upper bottom row and lower top row already align with their
longitudinal endpoints. The upper top row and lower bottom row do not.

There are **48 main-panel screws plus 18 kicker screws = 66 purchased
Hillman 42605 screws**. Four main axes—the lower `edge_1/2` pair on each
side—are recorded owner-directed moves of +76.9 mm along T. The other four
recorded moves are center-kicker axes. This comparison does not import the
older box-frame study's 16-kicker/64-total screw policy.

## Backing implications of making the rows straight

The following ranges are projected **saved physical-node envelopes**, useful
for identifying an assigned receiver that a proposed station would miss.
They do not certify a new axis's finished backing, bore or installation.

| Existing receiver | T range, mm |
| --- | --- |
| Top rail | 2600.924–2639.024 |
| Bottom rail, either side | 317.524–355.624 |
| Upper service rail | 1459.824–1497.924 |
| Lower service rail | 1315.774–1353.874 |
| Outer side, left | 99.257–2639.024 |
| Center principal, left | 94.757–2600.924 |

The longitudinal receiver envelopes in this table use the left members;
the screw T elevations in the station table are common to both sides.
The main panel T outlines are 1419.824–2639.024 for upper panels and
200.624–1419.824 for lower panels. Thus current upper interior top screws
are 19.05 mm from the panel's top, while its longitudinal top endpoints
are 85 mm from that top. Current lower interior bottom screws are 135.95 mm
from the panel's bottom, while its longitudinal bottom endpoints are 59.05 mm
from that bottom. These are unequal insets, not measured video dimensions.

| Comparison option; no change adopted | Required movement | Assigned-receiver implication |
| --- | --- | --- |
| Keep upper column endpoints; bring the two interior top screws onto their line | `edge_1/2`: −65.95 mm T, to 2554.024 | Misses the existing top rail by 46.9 mm below its nearest T edge. Its present receiver assignment cannot be retained. An alternate backing path would need identification. |
| Keep upper top-rail screw line; bring the two top column endpoints onto it | `rim_4`, `center_4`: +65.95 mm T, to 2619.974 | Outer-side envelope extends to that elevation. Center principal ends 19.05 mm below it; the existing top rail spans the inner-corner X locations, making it a possible reassigned receiver. A new bore and finished backing check would be required. |
| Keep lower column endpoints; bring the two interior bottom screws onto their line | `edge_1/2`: −76.9 mm T, to 259.674 | Misses the assigned bottom rail by 57.85 mm below its nearest T edge. An alternate backing path would need identification. |
| Keep lower bottom-rail screw line; bring the two bottom column endpoints onto it | `rim_1`, `center_1`: +76.9 mm T, to 336.574 | Remains within the longitudinal receivers' nominal envelopes. New locations still require finished backing, edge/end distances and hole-conflict checks. |

These are alternative coordinate comparisons, not drilling instructions.
Bringing the endpoints to the current rail-centered interior screws is a
useful first hypothetical layout because it retains those horizontal
receivers. It would move eight main axes across the four panels and change
the two upper inner-corner receivers to the top rail; it has not been
approved, modeled or screened. The current side/principal connection paths
and frame reactions cannot be inherited by those relocated screws.

The current receiver inventory gives every retained main axis one matched
finished-timber bore patch and a nominal 45.24375 mm overlap. It also records
finite panel/receiver contact. Those facts establish the existing modeled
station mapping, not installed thread length, continuous edge support or
new-station support. In particular, plywood seams and separated center
principals cannot inherit the video's unseen support arrangement.

## Decision and next useful step

**No missing screw count is demonstrated.** If the owner's intended pattern
means straight four-screw rows, the present station offsets and upper
inner-corner receiver transition must be resolved explicitly. If varied
insets are acceptable, the current model already supplies the reported count
and edge group membership. The unavailable video does not decide between
those interpretations or mandate any new hardware.

The next useful comparison is an explicit 12-per-panel station drawing under
the owner's mounting specification, with its receiver identities attached.
The rail-centered endpoint option above is one finite hypothesis to consider;
it keeps the 66-screw count and identifies the specific backing changes. Any
subsequent compatible frame comparison belongs to the parent and requires
the actual selected stations. Relocating screws cannot be credited with
reducing saved demands without that calculation.

The saved current response remains the response for its original coordinates
and unqualified Hillman stiffness. The [attachment worksheet](README.md#current-bounded-all-two-receiver-screen-attempt08)
and [generic lateral comparison](lateral-reference.md) remain applicable only
within their recorded assumptions. This note assigns no Hillman capacity,
replacement force distribution, complete joint pass or release. The full
47-criterion authority and all joint/release HOLD boundaries are unchanged.

## Input receipts and arithmetic

Only this worksheet was added. No frame/CAD/native solve, software test,
station edit, staging or commit was performed for it.

| Saved input | SHA-256 |
| --- | --- |
| [Reduced static model inputs](../../mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json) | `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9` |
| [Current frame comparison](../two-receiver-frame-attempt03/comparison.json) | `0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5` |
| [Current response](../two-receiver-frame-attempt03/response.npz) | `774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52` |
| [Frame node geometry](../corner-frame-attempt01/model.json), also pinned by the current comparison | `d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e` |
| [Retained receiver inventory](../../current-panel-receiver-transfer-2026-10-01/receiver-transfer.json) | `0ac0e30d582322f8919277aabec3af134c7bf5ecb2b0523d649622bcd4a47534` |

The response was read without running its producer: twelve saved 1888-entry
force vectors and their companion motion arrays are retained. No force was
reallocated here. The coordinate table is reproducible from repository root
using ordinary read-only arithmetic:

```python
import json
import math
from pathlib import Path

root = Path("docs/wood-joints-mvp/hypotheses")
model = json.loads((root / "mvp-acceleration-2026-09-28"
                   / "reduced-static-attempt01/model-inputs.json").read_text())
c, s = math.cos(math.radians(50)), math.sin(math.radians(50))
for axis in model["connections"]:
    if axis["kind"] != "panel_screw":
        continue
    station = axis["source_record"]
    if not station["panel_member"].startswith("main_"):
        continue
    x, y, z = axis["source_point_xyz_mm"]
    print(axis["axis_id"], station["receiver_member"],
          round(x, 6), round(c * y + s * z, 6))
```
