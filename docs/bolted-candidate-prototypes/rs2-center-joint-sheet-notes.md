# RS-2 fixed-member center joint: drawing notes

The [shared-axis sheet](../../exports/rs2-center-joint/rs2-ab205-shared.svg) and
[staggered-axis sheet](../../exports/rs2-center-joint/rs2-ab205-stagger.svg)
are **NON-DRILLING**
information drawings. They show the left center principal, header, and post in
their current raw CAD positions, with two separate, unselected AB205 hypotheses.
No trial hole, fitting orientation, bolt stack, or row is accepted. No fabrication
release is implied. The right station is not evaluated by these representative
sheets.

Regenerate from the current source solids and frozen CSV:

```sh
.venv/bin/python scripts/draw_rs2_center_joint.py
.venv/bin/pytest -q tests/test_draw_rs2_center_joint.py
```

## Geometry and symbol key

| Item | Source / depiction |
| --- | --- |
| Raw members | `floor_flush_width.variant(KERF_RIGHT).uncut_wood_parts()`; green principal, tan header, brown post. Side profile uses actual broad-face vertices, including the oblique principal cut. |
| Grain | Principal rises in +Y/+Z; post vertical; header runs in X. Arrows/text are directional, not grade or strength evidence. |
| Physical width | Kerf-right is 2435.225 mm overall versus the separate official 2438.4 mm presentation. Header runs X = −1219.2 to +1216.025 mm. This local drawing uses the physical kerf-right solids. |
| Nominal fitting | Red top and purple underside ideal L outlines: AB205 short vertical leg 88.9 mm, long horizontal leg 104.775 mm; width 41.275 mm and nominal thickness 6.35 mm. Bend at principal/header top or post/header underside. Actual product orientation, bend radii, hole registration, material, tolerance, and installation are unverified. |
| Trial axes | Two nominal 12.7 mm fasteners per fitting leg, with nominal 14.2875 mm wood-bore circles. Vertical short-leg offsets from bend: 20.6375, 68.2625 mm. Horizontal long-leg offsets: 36.5125, 84.1375 mm. Circles and plan marks are center axes, not drilled geometry. |
| Fixed geometry | Header Z = 238.9–277.0 mm; left principal/post outer face X = −89.05 mm. Top Y = −95.382052 mm. |

The **shared** sheet places the underside row at top Y = −95.382052 mm. Its two
header axes coincide with the top fitting's two header axes: six unique trial
wood axes, with two proposed shared through-header bolts and four separate
principal/post axes. The shared stack and unequal opposing actions need a
complete method; independent single-shear ratings cannot simply be added.

The **stagger** sheet keeps the top row fixed and places the underside row at
Y = −119.666026 mm, the recorded conditional parallel-loading trial midpoint.
It depicts eight separate trial wood axes. The 24.283974 mm Y separation and
9.996474 mm nominal bore web are geometry observations only. A perpendicular
loading row rule, load direction, local member behavior, and tolerances remain
unresolved; the underside row is not selected.

## Protected existing axes

Blue `S` crosses show the four retained Hillman panel/kicker screw start axes
whose frozen CSV start points lie in this local 3D crop (X −230…13,
Y −205…31.5, Z 0…395 mm):

| Mark | Frozen `name` | X, Y, Z start (mm) |
| --- | --- | --- |
| S1 | `round_panel_lower_left_center_1` | −70, 20.153, 322.070 |
| S2 | `round_kicker_left_center_1` | −70, −17.744, 60 |
| S3 | `round_kicker_left_center_2` | −70, −17.744, 192 |
| S4 | `kicker_header_left_1` | −200, −17.744, 257.95 |

All **66** panel/kicker screw axes and all **12** retained frame-bolt axes remain
protected at their original locations in
[`connection-axes.csv`](../floor-flush-construction-kerf-right/connection-axes.csv).
No retained frame-bolt start is in the crop: all 12 are at |X| > 1000 mm and
point farther outboard or remain there. The crosses are locations only; the
historical occupied screw diameters/lengths are **not** physical clearance
envelopes. Purchased Hillman length is 63.5 mm. A
[retailer-listed 0.355-in head diameter](../bolted-candidate-hillman-42605-dimensions.json)
is available for nominal sensitivity only; shaft major diameter, head
tolerance, installed seat/projection, and path clearance remain unresolved.
The [nominal four-screw clearance screen](center-screw-clearance-requirements.json)
reports finite shaft-centerline distances to trial bores and drilled ideal steel,
but is not a physical-envelope pass or drilling instruction.

## Inputs still required before any drilling decision

| Class | Required evidence / immediate rejection trigger |
| --- | --- |
| Geometry | Measured AB205 hole, bend, radius, flange and edge dimensions; bolt shoulder, washers, nuts, tool and withdrawal paths. A measured clash or impossible assembly order rejects the arrangement. |
| Material | Product-specific steel specification and minimum base-metal thickness; fastener and timber properties. Unsupported steel strength prevents calculation. |
| Resistance method | Oblique-cut principal end and local tear-out/splitting interpretation; header/post edge and row direction; steel, wood, bolt, contact and slip checks; shared-stack treatment if applicable. An applicable rule or complete calculation must establish each path. |
| Actual demand | Simultaneous signed force and moment actions at top and underside fittings, header, principal, and post under retained loads. Historical component maxima are not a proven demand for this new joint; see the [demand worksheet](../bolted-candidate-center-demand-worksheet.md). |
| Installation/access | Physical panel screw envelopes, adjacent replacement fittings, service access after panels, assembly sequence, and tolerances. Failure of any protected-axis or tool corridor check rejects that layout. |

The current records
[`ab205-center-fit.json`](ab205-center-fit.json) and
[`center-y-stagger.json`](center-y-stagger.json) are conditional screens, not
source approval. ABB's channel-connection rating is not a wood-joint rating.
