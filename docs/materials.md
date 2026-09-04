# Materials ledger

This ledger separates confirmed climbing-surface requirements from provisional
frame ideas. It is not yet a purchasing list.

## Confirmed or source-backed

| Material or component | Current requirement | Status |
| --- | --- | --- |
| Main climbing panels | 4 birch plywood panels, nominally 1220 x 1220 x 18 mm (48 x 48 x 0.71 in) | Geometry confirmed; grade and actual stock thickness to verify |
| Kicker panels | 2 birch plywood panels spanning the 2440 mm (8 ft) width | Width confirmed; custom height unresolved |
| Horizontal joint braces | 18 mm (0.71 in) plywood strips behind panel joints | Required by Moon Climbing; strip dimensions unresolved |
| Hold hardware | One consistent T-nut and bolt system matching the chosen holds | Thread standard must be verified before drilling |
| Climbing holds and LEDs | Mini MoonBoard 2020 layout-compatible sets and LED system | Product selection and quantities outside this milestone |
| Surface finish | Durable coating suitable for the climbing panels | Exact coating system unresolved |

## Provisional frame approach

The current concept is to laminate nominal 3/4 in birch plywood into broad
support members similar to the reference structure. This is a manufacturing
preference, not a validated structural specification.

Do not purchase frame stock from this table yet. The design must still set:

- plywood species, structural grade, veneer quality, and sheet dimensions;
- measured sheet thickness and number of laminated layers;
- structural adhesive, spread rate, open time, clamping pressure, and cure;
- scarf, lap, spline, or mechanical reinforcement at any member extension;
- bolt, screw, washer, insert, and plate specifications;
- edge sealing and finish appropriate to the installation environment; and
- replaceable feet, anti-slip treatment, and floor protection.

## Generated reference panel cut list

[`exports/mini_moonboard_reference_panel_cut_list.csv`](../exports/mini_moonboard_reference_panel_cut_list.csv)
is generated from the CadQuery source and covers only the four main panel
blanks and two kicker blanks. It deliberately excludes the frame, joint braces,
fasteners, holds, LEDs, finish, waste allowance, and nesting because those
require the selected stock and reviewed frame design.

The committed file uses the official 150 mm / 5.9 in reference kicker. To
evaluate a proposed taller kicker in a separate directory:

```bash
uv run python -m mini_moonboard.export --kicker-height-mm 300 --output-dir /tmp/mini-moonboard-300
```

Replace `300` only with the total kicker height resolved from the site survey;
the output remains a reference panel list until frame review is complete.

## BOM completion rule

The bill of materials and cut list can be released only after the parametric
frame model contains every load-bearing member and connection, the taller
kicker and crash-pad relationship are fixed, sheet nesting is generated from
actual stock sizes, and the structure has received qualified review.
