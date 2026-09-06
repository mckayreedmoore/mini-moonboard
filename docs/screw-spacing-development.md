# Separate screw-spacing development candidate

`screw-spacing-development` extends `independent-leg-development` without
changing either predecessor. **Provisional geometry screen, not manufacturer
approval, selected hardware, connection resistance or structural validation.**
The four independent leg plies, six internal stitch bolts, climbing panels,
panel screw pattern, vertical wiring corridors and 165.1 mm vertical seam
battens are retained. There is no adhesive or leg-interface friction credit.

Inspect the [selectable 3D model](https://mckayreedmoore.github.io/mini-moonboard/?model=screw-spacing-development),
[STEP assembly](../exports/screw-spacing-development/screw-spacing-development.step),
[metric/imperial parts list](../exports/screw-spacing-development/screw-spacing-development_parts.csv),
[connection schedule](../exports/screw-spacing-development/screw-spacing-development_connections.csv)
and [rear view](../exports/screw-spacing-development/screw-spacing-development_rear.png).

## Changed seam joints

Coordinates are board-local millimetres: X across the board, S uphill and N
through the backing. All front screws start at N = 0. Rear offsets are relative
to the rib centre S. Rib width/depth remain 63.5/89.95 mm.

| Seam rib | Centre X / S | Front screw X / S | Rib length | Rear rib bolt S offsets |
| --- | --- | --- | ---: | --- |
| Row 1 left | -54 / 400 | -54 / 330 | 350 | ±35 |
| Row 1 right | 54 / 400 | 54 / 505 | 420 | ±70 |
| Row 2 left | -76 / 1219.2 | -76 / 1219.2 | 300 | ±70 |
| Row 2 right | 76 / 1219.2 | 76 / 1219.2 | 300 | ±35 |
| Row 3 left | -54 / 2000 | -54 / 1930 | 350 | ±35 |
| Row 3 right | 54 / 2000 | 54 / 2105 | 420 | ±70 |

All six mid ribs and their screws remain at X = -519.2 / 680.8 and
S = 400 / 1219.2 / 2000, with 300 mm rib lengths. Only the two row-2 seam
angles and their beam holes move outward, by 22 mm. Angle dimensions and bolt
lengths remain unchanged. Swapping the row-1/3 rear stagger preserves the
opposing nominal nut/socket separation while allowing the offset front screws.
Those four ribs each provide 105 mm front-screw end distance and 140 mm nearest
rear-bolt end distance. Longer left ribs retain the actual open wire chase;
relocating the row-2 ribs leaves the existing corridor clear.

Moved receivers are rebuilt from undrilled bodies and drilled using the complete
current connection inventory. Backing reliefs are recreated before drilling.
Swapped angle holes and moved front/beam holes therefore do not leave abandoned
bores. Unchanged parts, including all four leg plies, retain their predecessor
objects and machining.

## What the spacing screen establishes

The [SDWS16 study](front-rib-fastener-selection.md) identifies the relevant
[2025 guide, p. 47](https://ssttoolbox.widen.net/content/zpm9nibpvz/pdf/C-F-2025TECHSUP.pdf)
and [ER-192, Table 26/Figure 20](https://forms.iapmo.org/ues_reports/reports/er_0192.pdf).
These give 25.4 mm row separation and 50.8 mm in-row pitch for the applicable
SDWS16312 lateral arrangements; the indicated row arrangement also carries a
0.91 shear-load factor. The candidate assigns no capacity from that table.

For the row-2 horizontal batten, grain follows X. Parallel-to-grain loading
uses rows at S = 1169.2, 1219.2 and 1269.2: minimum row separation 50 mm,
minimum in-row pitch 100 mm. Perpendicular-to-grain loading uses fixed-X rows:
the closest columns are ±76 and ±50, giving 26 mm row separation, again with
100 mm minimum in-row pitch. These are complete row-set checks, with no credit
from the smaller 11.1125 mm close-stagger allowance. The nominal 26 mm result
leaves only 0.6 mm above the row minimum; fabrication tolerances remain open.

Rows 1/3 use a conservative directional screen for their near-aligned vertical
strips: every front/other parallel screw pair sharing a batten must separate by
at least 50.8 mm in X or S. This is a project geometry comparison, not a radial
manufacturer rule or approval of mixed products. Both members' grain-relative
outside edges/ends are checked separately. The actual relief boundary and
crossed-bore screens retain their prior 25.4 mm and 25 mm project thresholds;
neither supplies a notch or splitting resistance.

## Verification and remaining decisions

`uv run pytest tests/test_spacing_frame.py` checks the exact 226-connection
inventory, preserved plies/stitches and parts, all twelve front positions,
actual CAD thread receiving wood, body/hardware collisions, receivers and
connectivity, bolt bores and superseded holes, nominal socket/withdrawal
envelopes, LED/wiring corridors, and four separate floor faces.
Screw clearance and pilot cores are checked separately from the larger nominal
thread envelope: the cores must be empty, while the receiving wood must remain
available for engagement.

The larger published 5.4864 mm thread envelope is tested through 50.8 mm of
actual net rib wood. Hardware **still uses the generic predecessor envelopes**;
this test does not select SDWS16312 or establish its head seating. Resolve the
product head profile, pilot/clearance machining, mixed panel/rib fasteners,
material grade/species, notches, tolerances, combined demands and capacity
before treating this as a construction detail. No predecessor FEA result
transfers automatically to the changed geometry.

## Publication checks

The eight spacing tests, five independent-ply tests and four export tests passed.
Sequential regeneration preserved every existing joint-development and
independent-leg-development CAD/viewer artifact byte-for-byte. The export-order
regression uses exact CAD bounds for ply cutting planes, preventing cached
display tessellation from changing the 19.05 mm plies.

Export tests additionally probe actual STL triangles through the seam and
stitch bores, rather than relying only on bounding boxes or source CAD. Real
browser checks loaded all 293 entries in both independent-ply and revised-spacing
variants, clicked all four plies and six stitches, verified the preserved
plywood default and selector navigation, and reported no browser errors.
Front and selected-stitch screenshots were visually inspected for the new
variant. A final independent correctness, testing and architecture review pass
found no substantial remaining findings. These checks do not qualify materials,
installation details, load resistance or climbing use.
