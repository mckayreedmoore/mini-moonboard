# Current PB02 BOM and cut-list

Status: **current development inventory only**. This record supersedes older PB02
purchase and partial cut-list summaries as the current inventory. Historical eight-bolt
rejected-pose studies remain unchanged and remain useful only for their bounded trials.
No purchase, drilling, fabrication, or structural release follows from this record.

The [reproduction script](../../scripts/simple_center_pb02_current_bom.py) binds every
wood-piece dimension below to the active PB02 boxes in the V4 viewer. It also requires
the active `ligament_priority` geometry to contain ten PB02 bolt axes, all 66 fixed
panel/kicker screw axes, and a closed fabrication-release flag. The current source
fingerprint is
`4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb`.

The active rear cleat now starts 5 mm above the floor and ends at the unchanged
Z=460 mm top, giving a 455-mm length. This revision assigns no rear-cleat floor bearing.
It was introduced as a concrete geometry response to A12-rear active-set cycling; no
accepted source-bound native result exists for this revised fingerprint.

## Current hardware count and arithmetic

The current basket contains **ten bolts: three 5-in, three 6-in, and four 8-in**,
plus **ten nuts and twenty washers**. It uses the existing illustrative unit prices:
$0.62, $0.71, and $0.94 for the respective bolt lengths; $1.98 per 12-nut pack; and
$1.98 per 16-washer pack.

| Item | Arithmetic | Cost |
| --- | ---: | ---: |
| Bolts | 3×$0.62 + 3×$0.71 + 4×$0.94 | **$7.75** |
| Allocated hardware | bolts + 10/12 nut pack + 20/16 washer pack | **$11.88** |
| First checkout, excluding lumber | bolts + 1 nut pack + 2 washer packs | **$13.69** |

These are arithmetic values, not a quote, stock confirmation, hardware selection, or
complete project cost. Lumber, backer attachment, delivery, tax, waste, and tools are
excluded. Exact delivered bolt, nut, and washer dimensions and properties remain open.

## Current wood pieces

Dimensions are the active viewer's X×Y×Z box dimensions. The cut-length allocation
below follows the established grain/cut direction, not necessarily the first dimension.

| Piece | Active dimensions, mm | Example source stock |
| --- | ---: | --- |
| Shifted right center post | 88.9×88.9×238.9 | 4×4 |
| Post/header block | 88.9×88.9×143.9 | 4×4 |
| Upright-side cleat | 88.9×61.6×183 | 4×4, ripped |
| Header-side cleat | 70.95×145×67 | 4×6, two illustrative rips |
| Rear cleat | 88.9×38.1×455 | 2×4 |
| Kicker backer | 139.7×88.9×238.9 | 4×6 |

## Illustrative stock arithmetic

The example assumes one 2438.4-mm (8-ft) stick of each nominal stock size and one
**3.2-mm crosscut kerf per separated piece**. It includes no end trim, squaring,
defect rejection, or dimensional tolerance.

| Stock | Cut lengths plus kerfs, mm | Consumed | Remainder |
| --- | ---: | ---: | ---: |
| 4×4 | 238.9 + 183 + 143.9 + 3×3.2 | **575.4 mm** | **1863.0 mm** |
| 2×4 | 455 + 1×3.2 | **458.2 mm** | **1980.2 mm** |
| 4×6 | 238.9 + 145 + 2×3.2 | **390.3 mm** | **2048.1 mm** |

The upright-side example assumes a nominal 88.9-mm 4×4 blank ripped to 61.6 mm
with one 3.2-mm kerf, leaving **24.1 mm**. The header-side example assumes the
4×6 cross-section is oriented as 88.9×139.7 mm, then subtracts the 70.95-mm and
67-mm finished dimensions with one 3.2-mm kerf in each direction. The resulting
offcuts are **14.75 mm** and **69.5 mm**. These are illustrative rip calculations,
not a machining plan, usable-offcut credit, or proof that delivered stock can finish
to the modeled dimensions.

Run `.venv/bin/python -m scripts.simple_center_pb02_current_bom` to reproduce the
record. The prior floor-bearing geometry has one corrected `a12-forward` developmental
result; it is not evidence for this 5-mm-clear revision. The active geometry still
requires a new source-bound run, local-ligament/splitting resolution, group and geometry
factors, exact hardware checks, and the remaining load cases. No purchase, drilling,
fabrication, or structural release.
