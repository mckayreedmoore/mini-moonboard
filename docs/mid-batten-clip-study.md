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

## Clearance calculation

For the proposed mounting, timber touches model outer planes Y=0/Z=0:
outward reach is **39.2684**, not nominal 38. Batten faces X=−563.65/+636.35
lie beside relief columns X=−619.2/+580.8. Thus tip-to-relief ΔX is
`100 − 44.45 − 39.2684 = 16.2816`. Bottom/upper-seam ΔS are 8.9/9.05.
For 20 mm relief radius plus a declared **2 mm geometric screen allowance**,
required +X shift is `sqrt(22² − ΔS²) − 16.2816`:
**3.837793629 / 3.770768937 mm**. Common **+3.9 mm** passes this model-only
calculation, not a manufacturing-tolerance design. A rounded +5 mm alternative
is inspected below but is not a selected manufacturing design.

## Separate +5 mm CAD inspection

[`clip_frame.py`](../mini_moonboard/clip_frame.py) now provides the separate
`mid-batten-clip-development` model; the existing baseline is unchanged.
Four mid-battens, six attached ribs and six rear angles move +5 mm in CAD X,
along with 30 dependent connection axes. The 64 panel and 16 kicker screw axes and
MoonBoard hole grid stay fixed. Affected receivers are rebuilt from undrilled
stock, removing the eight former end-grain screw bores and relocating dependent
bores. Eight clips and 32 provisional fasteners replace eight screws:
250 connections total.

Seven actual-CAD tests pass:

```sh
uv run pytest -q tests/test_clip_frame.py
```

They check the eight outlined/perforated clips, opposite-S orientations,
body/head/hardware collisions, shaft receivers, old-bore removal, existing
socket/LED/wiring envelopes and all 32 provisional straight-driver approaches.
Minimum clip-to-relief clearance is **3.06765 mm**, exceeding the unchanged
2 mm geometric screen. This is nominal CAD clearance, not tolerance approval.
The tests use board-local enclosing bounds before nearby solid-distance checks:
the CAD kernel returned a false zero distance for a remote, nonintersecting pair
whose S intervals were over 800 mm apart.

**The new fasteners are unselected screw-envelope explorations, not the UK
product's specified nails.** Each models a Ø3.75×30 mm shaft, Ø10×3 mm pan head
and Ø10×25 mm straight driver approach. These dimensions do not establish an
available or approved screw, a nail-driving clearance, or US/UK equivalence.
No purchasing schedule, manufacturer spacing compliance, bend/tolerance fit,
installation-sequence approval or joint capacity follows from these tests.

The variant is not yet registered/exported in the online viewer and no FEA has
been run on it. Next: resolve a compatible connector/fastener installation,
publish the separately labeled viewer variant, then qualify its joint demands
without adhesive/composite-action credit or replacing the original failed FEA
evidence.
