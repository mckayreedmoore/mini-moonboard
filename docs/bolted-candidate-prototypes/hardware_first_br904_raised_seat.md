# BR904 raised center seat: bounded nominal screen

Status: **rejected nominal geometry** for the three tested upper rows. This is
not a drilling pattern, connector selection, material adoption, or rating.
The executable record is `hardware_first_br904_raised_seat.json`.

This screen uses the exact Newhouse/Adamax BR904 model listed as Home Depot
internet #325186317. The [Lowe's BR904 product drawing](https://mobileimages.lowes.com/productimages/d634d853-f9cd-473c-9904-e170613fa268/66922570.jpeg)
shows nominal 1.57-in width, 0.24-in plate, 0.81-in free-end inset, 1.87-in
pitch on each leg, 4.13-in vertical overall, and 3.48-in horizontal length to
the outer bend. Its rounded dimensions imply first near-bend hole distances
of 1.45 in vertically and about 0.80 in horizontally. The script retains the
[Newhouse BR904](https://newhouseelectric.com/products/bracket-90deg-4-hole)
advertised 9/16-in hole diameter and 1-7/8-in pitch for the occupied bores.
The drawing is retailer-hosted nominal information, not a controlled
manufacturing tolerance or a verified bend datum. The Adamax/Newhouse model
identity cross-check is in `newhouse-br904-retail.json`; the delivered Home
Depot part and its actual dimensions remain unverified. No AB205 dimensions
are used.

The kerf-right CAD keeps one-piece center principals, post, and header. A
local raised header region reaches behind the fixed panel face to carry two
inward-pointing upper BR904 seats and one inverted lower post/header BR904.
The trial trims six inner rail ends at X = ±121 mm. Each bracket has two
nominal holes on each leg: eight upper bores and four lower bores. The three
upper bracket centers are Y = -100, -70, and -56 mm. A 1/2-in trial bolt and
the nominal factory-hole radial play of 0.794 mm are used only for wood
search filters. Ideal rectangular plate solids omit the bend radius and
delivered variation.

Across all three poses, the 66 fixed panel/kicker axes retain their receiving
wood. The six fixed panel solids, 12 existing frame axes, and protected screw
envelopes show no nominal clash with the new hardware. Four center kicker
screws still meet the solid post, which spans the kerf-right seam. All changed
CAD timber is one connected solid. The initial lower post bore origin was
incorrectly placed at the post's X edge and reported 11,198.73 mm³ missing
per bore. It was corrected to X = 0 on the rear Y face, drilling direction
+Y; both complete lower post bore envelopes are now inside wood. That former
volume is **not** a geometry failure.

The remaining rejection is substantive within this bounded pose:

- Each inward upper seat intersects its corresponding principal by about
  21,488 mm³. This is an ideal plate/wood collision, not a bend-tolerance
  conclusion.
- The nominal first lower post hole is only 36.83 mm from the post/header
  interface along its vertical grain. It misses a 3.5D plus nominal hole-play
  search marker by 8.414 mm. The far lower header hole is 20.447 mm from
  the rear edge of the raised header and misses the reversible 4D plus play
  marker by 31.147 mm.
- Shifting the upper bracket forward improves the principal edge margin but
  loses the header front edge margin: at Y = -100 the upper principal's
  second hole misses one 4D marker by 43.650 mm; at Y = -70 by 20.668 mm;
  at Y = -56 by 9.944 mm. The upper header front-edge 4D margin is
  +12.406, -17.594, and -31.594 mm respectively.

These are conservative **search filters**, not classified NDS edge or end
distance verdicts for the oblique principal toe, shaped header shoulder, or
combined action. Other poses and changed hidden timber are outside this
three-pose screen. No material property, formed-angle strength, wood-joint
resistance, fastener stack, tool access, or full frame load path is established.
Stop this arrangement before cutting or drilling.
