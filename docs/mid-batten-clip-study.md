# Mid-batten side-grain clip study

2026-09-06. **Read-only geometry investigation, not a frame change, qualified
fit, product selection or capacity claim.** This is separate from the existing
`screw-spacing-development` / untied `2x8-foot100` candidate. Its eight generic
mid-batten end screws remain unresolved: four are 138.9 mm long and four are
189.7 mm long, passing through rails into batten end grain.

## Proposed location and official model

Investigate an angle on the **negative-X side of both mid-battens**, joining
their side grain to adjacent rail side grain. Board-local dimensions are mm;
backing occupies N = 0–38.1. Batten centres are X = −519.2 and +680.8, width
88.9. Each has these four butt-joint stations (eight total):

| S | Batten extends from joint toward |
| --- | --- |
| 88.9 | +S |
| 1149.35 | −S |
| 1289.05 | +S |
| 2349.5 | −S |

The [official UK A21 page](https://www.strongtie.co.uk/en-UK/products/angles-a)
links full-hole [IFC](https://www.strongtie.co.uk/sites/default/files/field_media_file_1/2024/05/15/025407/c-a21-3d-cad-mult-prod.ifc)
and [SAT](https://www.strongtie.co.uk/sites/default/files/field_media_file_1/2024/05/15/025404/c-a21-3d-cad-mult-prod.sat).
The millimetre-defined IFC has local width X = ±17.4625, long leaf Y =
−51.9684…0, short leaf Z = 0…39.2684, thickness 1.1684. Hole centres:

| Leaf | Local coordinates |
| --- | --- |
| Long, normal Z | (X,Y) = (−7.9375,−42.4434), (+7.9375,−29.7434) |
| Short, normal Y | (X,Z) = (−7.9375,17.0434), (+7.9375,29.7434) |

SAT confirms Ø4.3434 holes. Free-tip chamfers are 6.35 mm across the width,
leaving full reach over the central 22.225 mm; they do not clear through-N
reliefs. The model does not establish a manufactured bend radius or tolerances.

The [UK schedule](https://pim.strongtie.eu/api/v1/public/download/gb/en/product/305/A.pdf)
lists nominal 50×38×35×1.2 mm and two 3.75×30 mm nails per member. The separate
[US screw schedule](https://www.strongtie.com/products/fastening-systems/technical-notes/sd-connector-screw-approved-connectors)
lists four #9×1½-inch SD Connector screws for A21. **Regional product/dimensional
equivalence and installation suitability are not established.**

## Clearance calculation and next inspection

For the proposed mounting, timber touches model outer planes Y=0/Z=0:
outward reach is **39.2684**, not nominal 38. Batten faces X=−563.65/+636.35
lie beside relief columns X=−619.2/+580.8. Thus tip-to-relief ΔX is
`100 − 44.45 − 39.2684 = 16.2816`. Bottom/upper-seam ΔS are 8.9/9.05.
For 20 mm relief radius plus a declared **2 mm geometric screen allowance**,
required +X shift is `sqrt(22² − ΔS²) − 16.2816`:
**3.837793629 / 3.770768937 mm**. Common **+3.9 mm** passes this model-only
calculation, not a manufacturing-tolerance design. A rounded +5 mm alternative
could be inspected but is not selected.

Next inspect all eight exact solids, opposite-S rotations, fasteners, tools,
reliefs, edge/end distances and installation sequence. Move attached ribs,
angles, rib screws and corresponding receiving holes with each batten; recheck
panel-screw engagement and every neighbouring connection. Keep the MoonBoard
hold grid fixed. Rebuild affected stock without abandoned bores. No CAD change
or completed fit test is recorded here.
