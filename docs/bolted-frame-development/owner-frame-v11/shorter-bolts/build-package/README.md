# V11 build planning and printable layout tools

This packet applies to `v11-shorter-bolts-v1`: the current 112-bolt shorter-stack trial with the original V9 cleats, standard 4×6 top and sides, and four remaining metal spacers. The frame, cleats, holes and bolt locations have not changed during this follow-through. It is separate from the selected screw-and-bracket baseline.

The six frame-load cases and twelve replays are complete. Connection interpretation remains open. These files support stock/hardware planning and printing templates for fit and layout review; structural cutting, drilling and climbing remain on hold. Actual/Disposition cells stay blank until observed.

## Start here

- [Grouped bolt shopping list](hardware/shopping-list-v1.csv) and [shopping/readiness note](hardware/shopping-readiness-v2.md).
- [Member and cut-reference plan](geometry-packet/builder-plan.md), [member table](geometry-packet/member-cut-planning.csv) and [stock allocation](geometry-packet/stock-allocation.csv).
- [Rear-foot left/right templates](runner-leg-jigs/README-v3.md), with separate [left STL](runner-leg-jigs/prototype-v3-verified/left-rear-foot-leg-marking-jig.stl) and [right STL](runner-leg-jigs/prototype-v3-verified/right-rear-foot-leg-marking-jig.stl).
- [Reusable horizontal-rail bracket jig](bracket-jig/README.md), [placement drawing](bracket-jig/placement.svg) and [12-position registration table](bracket-jig/registration-table.md). The checked subset is the 12 horizontal-rail beam flanges, used before joining the perpendicular member; post flanges, headers and outer tops are excluded.
- [152 receiver-profile intersections](geometry-packet/receiver-planning.csv) and [66 panel/kicker screw axes](geometry-packet/panel-screw-axis-planning.csv). These are review coordinates, not ready-to-drill face marks or bit sizes.

## Current bolt quantities

| Nominal size and length | Grade/type | Quantity |
| --- | --- | ---: |
| 3/8–16 × 2½ in | Grade 5 hex | 48 |
| 3/8–16 × 3 in | Grade 5 hex | 8 |
| 3/8–16 × 4½ in | Grade 5 hex | 2 |
| 3/8–16 × 4¾ in | Grade 5 hex | 32 |
| 3/8–16 × 7 in | Grade 5 hex | 4 |
| 3/8–16 × 6 in | A574 socket head | 4 |
| 3/8–16 × 6½ in | A574 socket head | 12 |
| 1/2–13 × 8½ in | Grade 5 hex | 2 |

The CSV preserves exact current SKUs, nuts, washers, lengths and axis ownership. Totals are 112 bolts, 112 nuts, 224 washers and four half-inch-long sleeves. The model requires 24 Eoere angles; the owner reports owning that bracket model, but a delivered count has not been recorded. The 66 Hillman panel/kicker screws are outside this bolt schedule. The [current product-link check](hardware/current-link-check-v1.json) confirms the eight bolt descriptions and records package units; stock and delivery dates remain unknown.

The shopping note's 80-axis partition means only that those axes are outside its two named top/A574 reviews. It is not a cleared order. The two outer-top joints still have spacing/end questions, the socket-head material basis remains open, and the additional rear force-and-moment/bearing work also controls readiness. No smaller bolt, replacement angle or spacer removal is selected here. Nominal bolt length alone does not guarantee the required body, thread, runout and nut-seating dimensions.

## Printing and marking

Print the rear-foot STL for the correct side in millimetres at 100% scale, flat contact skin on the bed and ribs upward. Each is about 149 × 141 × 8.2 mm. They mark one current rear-foot axis per leg through a 2 mm awl aperture. The old two-target runner sheet is historical; do not drill its extra target. Front-upright/runner holes have a different datum and are not supplied by the rear-foot stencil.

Bracket files use the [Amazon dimension image](https://m.media-amazon.com/images/I/61D4fLDkfiL._AC_SL1500_.jpg), which labels 2-inch × 1⅝-inch pitches and nominal 3½-inch legs. It does not dimension the hole-edge offsets or inside bend radius. The one-piece positioning prototype has joined rail-side/end stops and angle-edge lips. It uses actual steel holes for transfer marking through two far-row access windows. Several other post connections lie midway along members and need a separate height datum; one end-registering tool cannot locate those from the timber ends. Do not use it to populate every factory hole. The two outer-top eight-bolt patterns remain outside the marking-use instructions pending their review.

These are nonstructural print/fit prototypes, not precision drill guides. Follow each template's placement and contact-face instructions. Actual wood, bracket and printed-part fit, clamp setup and marking accuracy have not been observed. Final bits, bushings, pilot depths and drilling sequence have not been selected by copying analysis-bore diameters.

## Stock and source scope

The current geometry packet contains 20 sawn members, four nominal ¾-inch cleat leaves and six face panels. Provisional stock before owned-stock credit is five 2×6×8, three 2×6×10, three 4×6×8 and two 4×6×10. The allocation uses current finished member envelopes with stated trim/kerf allowances; it is not a final saw setting. Preserve the right-side offset and the actual rear-leg recess. There are no wood packers or built-up substitutes.

The cleats remain two glued nominal ¾-inch leaves per side, 38.1 mm nominal combined thickness with a 36.5 mm strength allowance. The saved plywood category, strength direction and perfect-bond assumption remain conditional. Face-panel ownership alone does not qualify cleat plywood or the shop-made bond.

[Manifest](manifest.json) binds the current geometry, receipt, force bank, joint assessment, source packets and every published file. Detailed CAD, STEP references, controls and reproducible producers remain in the retained ignored development packet. The original worker packets and earlier unsuccessful template drafts remain preserved. This compilation adapts document links where needed; it does not rewrite their numerical evidence or promote the development trial into the selected baseline.
