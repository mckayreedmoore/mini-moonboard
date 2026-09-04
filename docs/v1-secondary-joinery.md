# V1 secondary joinery schedule

This schedule completes the physical connections that are represented as
face-to-face contacts in the V1 STEP model but are not the generated primary
entries in `mini_moonboard_v1_connection_schedule.csv`. The matching generated
[`mini_moonboard_v1_secondary_joinery_schedule.csv`](../exports/mini_moonboard_v1_secondary_joinery_schedule.csv)
controls the count and screw specification; this document controls the relative
patterns. Measurements are from the
finished part edges, after the two 18 mm laminations have cured and been
trimmed flush. Pilot every plywood screw hole; do not substitute drywall
screws.

It is a **provisional construction specification**, not a substitute for the
structural review required by the build package. Before production assembly,
perform every listed screw stack on an offcut from the actual plywood batch.

| Interface | Per-interface pattern | Interfaces | Hardware quantity |
| --- | --- | ---: | ---: |
| Rail splice cover to its lower/upper rail segments | 2 #10 x 2.5-in structural wood screws into each rail segment. Centres are 50 mm in from each splice side edge and 75 mm either side of the panel seam along the rail. | 5 splice covers | 20 x #10 x 2.5-in |
| Each rail-cross-tie half to each contacted face rail | 2 #10 x 2.5-in structural wood screws, 45 mm either side of the tie centreline. Drive board-normal from the tie exterior into the rail. | 18 tie/rail contacts | 36 x #10 x 2.5-in |
| Each rear-tie half to its lower leg | 2 x 5/16-in x 10-in structural lag screws with washers. Drive from the accessible **leg exterior** toward center, through the 36 mm leg and at least 200 mm into the tie end. Use the generated global schedule. | 6 tie/leg contacts | 12 x 5/16-in x 10-in |
| Each rear/rail tie center splice to its two halves | 2 #10 x 2.5-in structural wood screws into each half. Centres are 50 mm from each splice end and 45 mm either side of the tie centreline. | 6 center splice plates | 24 x #10 x 2.5-in |
| Kicker/main exterior side gusset to each panel edge | 4 #10 x 2-in structural wood screws per panel edge. On the kicker, centres are 75, 125, 175, and 200 mm above its bottom; on the main, measure 75, 150, 250, and 350 mm along the main edge from the seam. | 4 panel edges | 16 x #10 x 2-in |
| Blank-kicker backing to its kicker panel | 4 #10 x 2-in structural wood screws, at X=150 and 1068 mm from its outside panel edge and Z=25 and 55 mm above floor. Drive from backing into the blank 75 mm extension. | 2 backings | 8 x #10 x 2-in |
| Kicker-backing center seam splice to both backings | 2 #10 x 2.5-in structural wood screws into each backing. Centres are 50 mm from each splice end and Z=37.5 mm above floor. | 1 seam splice | 4 x #10 x 2.5-in |

The `#10 x 2.5-in` count is **84** and the `#10 x 2-in` count is **24**.
Buy at least 10 percent extra of each, plus the 60 `#10 x 3.25-in`
panel-to-rail screws already specified in the primary connection schedule.

## Kicker/main gusset cut profile

Each exterior gusset starts as one of the 400 x 470 mm two-ply blanks in the
cut list. With the blank's lower-left corner at the gusset's lowest/rearmost
corner, transfer this four-point support-side profile in millimetres:
`(31.8, 0)`, `(31.8, 150.0)`, `(0, 161.6)`, `(257.1, 468.0)`.
The profile's 257.1 mm horizontal by 468.0 mm vertical envelope leaves the
specified blank margin. Mirror it for the opposite exterior side. The STEP
assembly is the controlling shape check; reject any hand-transferred profile
that does not bear continuously on both the kicker and the lower main panel.

## Assembly controls

1. Laminate every support part in matched pairs with full-face adhesive and
   clamp pressure distributed by cauls. Keep the grain/face orientation
   consistent within each pair. Do not rely on screws to replace a failed or
   uncured laminate.
2. Dry assemble every secondary interface, clamp it flush, then mark all
   centres from this table. A screw may not be moved toward a plywood edge or
   toward a panel bore merely to avoid a defect; revise and document the part
   if a center cannot be used.
3. For rail splices, install the lower and upper rail segments with a tight
   square butt at the main-panel seam. The 400 mm cover plate must extend
   200 mm on either side of that seam before its four screws are installed.
4. For rail ties and all tie-center splices, use both screws only after their
   full contact faces bear without gaps. A tie that touches only at a corner is
   rejected. Install each rear-tie-to-leg lag from the leg exterior using its
   global connection-schedule datum; never attempt to drive a long screw from
   the tie's center toward the leg.
5. For the side gussets and blank-kicker backing, confirm every screw stays on
   the support/exterior side and does not emerge through the climbing surface.
6. Recheck all screw heads after the first non-climbing shake/rack inspection.
   Loose, split, stripped, or face-breaking fasteners require replacement and
   a recorded corrective action before the board is loaded.

These patterns deliberately keep the primary 3/8-in leg/rail and knee bolts
separate: use their exact global coordinates from the generated CSV, not this
relative schedule.
