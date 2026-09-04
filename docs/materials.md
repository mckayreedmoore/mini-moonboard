# Materials ledger

This ledger separates confirmed climbing-surface requirements from provisional
frame ideas. It is not yet a purchasing list.

## Confirmed or source-backed

| Material or component | Current requirement | Status |
| --- | --- | --- |
| Main climbing panels | 4 birch plywood panels, 1218.0 x 1218.0 mm v1 stock target | Two panels per 4 x 8 sheet leave 2.4 mm total rip allowance; verify official-template calibration and actual stock |
| Kicker panels | 2 birch plywood panels, 1218.0 x 225 mm v1 stock target | Provisional v1: 150 mm active zone plus 75 mm blank extension below |
| Horizontal joint braces | 18 mm (0.71 in) plywood strips behind panel joints | Required by Moon Climbing; strip dimensions unresolved |
| Hold hardware | Escape Climbing 3-hole screw-in T-nuts, 3/8-16 | Selected; use 7/16 in bore after offcut fit test, 142 positions minimum, and matching 3/8-16 hold bolts |
| Climbing holds and LEDs | Mini MoonBoard 2020 layout-compatible holds and MoonBoard LED System, SKU 60-201-V5 | Selected listing states 200 bulbs including 2 spares and 66 extra on Mini, reconciling to 132 official Mini LED centre datums; supplied V5 guide controls installation |
| Surface finish | Durable coating suitable for the climbing panels | Exact coating system unresolved |

The user-selected panel stock is [Swaner Hardwood 3/4-in x 4-ft x 8-ft C-3
Birch Plywood, Home Depot product 165921](https://www.homedepot.com/p/Swaner-Hardwood-3-4-in-x-4-ft-x-8-ft-C-3-Birch-Plywood-165921/202085716), recorded 2026-09-04.
The selected hold insert is [Escape Climbing 3-hole screw-in T-nut, Amazon
ASIN B00FJGT7QI](https://www.amazon.com/dp/B00FJGT7QI?ref=ppx_yo2ov_dt_b_fed_asin_title),
recorded 2026-09-04. These are user-provided listing references, not verified
material certifications: availability, dimensions, grade, and every listing
claim remain provisional until the received samples and offcut test are logged.

## Provisional frame approach

The v1 concept has three assemblies: the board/kicker and two exterior
hockey-stick legs. Every support member is a two-ply laminate of nominal 3/4
in birch plywood. Each leg follows the board to the datum two T-nut rows below
the top, bends at the datum five rows below the top, and reaches the floor at
a provisional 60-degree angle to the descending board line. It is unanchored.
This is a geometry/manufacturing preference, not a validated structural
specification.

Do not purchase frame stock from this table yet. The design must still set:

- plywood species, structural grade, veneer quality, and sheet dimensions;
- measured sheet thickness and number of laminated layers;
- structural adhesive, spread rate, open time, clamping pressure, and cure;
- scarf, lap, spline, or mechanical reinforcement at any member extension;
- bolt, screw, washer, insert, and plate specifications;
- edge sealing and finish appropriate to the installation environment; and
- replaceable feet, anti-slip treatment, and floor protection.

## Selected hardware and LED provisions

The selected Escape hardware is imperial 3/8-16 screw-in T-nuts. Its specified
7/16 in bore differs from Moon Climbing's generic 13 mm / 1/2 in T-nut bore;
the Escape offcut test governs the selected T-nut installation. Use only
matching 3/8-16 bolts. Do not mix M10 bolts with these inserts.

Moon Climbing's own hardware path instead calls for metric M10 T-nuts and
bolts (with 3/8 in described as the imperial counterpart) and its build page
lists a 13 mm / 1/2 in bore with a 10 mm barrel. If MoonBoard T-nuts are used,
buy the required fixing screws separately and confirm the exact selected
product's bore, barrel, flange, and screw requirements on an offcut.

The selected [MoonBoard LED System](https://us.moonclimbing.com/products/moonboard-led-kit)
is SKU 60-201-V5. Drill the 13 mm LED holes at the official LED datums and
provide protected rear routing to the controller, with access to its switch,
only after the supplied V5 guide confirms that 13 mm diameter for this kit.
The kit includes a controller, four 50-LED strings, supplementary power feeds,
and a 5 V adapter according to the selected product listing. The listing's 200
bulbs include 2 spares and describes 66 extra bulbs on a Mini, leaving 132
installed positions—the same count as the official Mini LED centre datums in
this package. Reconcile every LED with the supplied V5 guide during the
offcut/template audit. A future kit version is a separate compatibility variant:
it must retain the official datum pattern only if its supplied guide specifies
the same hole, wiring, controller-clearance, and power requirements.

## Generated reference panel cut list

[`exports/mini_moonboard_reference_panel_cut_list.csv`](../exports/mini_moonboard_reference_panel_cut_list.csv)
is generated from the CadQuery source and covers only the four main panel
blanks and two kicker blanks. It deliberately excludes the frame, joint braces,
fasteners, holds, LEDs, finish, waste allowance, and nesting because those
require the selected stock and reviewed frame design.

To evaluate the v1 225 mm kicker in a separate directory:

```bash
uv run python -m mini_moonboard.export --kicker-height-mm 225 --output-dir /tmp/mini-moonboard-v1
```

Replace `225` only after the kicker geometry is deliberately revised;
the output remains a reference panel list until frame review is complete.

## BOM completion rule

The bill of materials and cut list can be released only after the parametric
frame model contains every load-bearing member and connection, sheet nesting
is generated from actual stock sizes, and the structure has received qualified
review. The crash pad remains a separate later climbing/use gate, not a V1
BOM or cut-list input.
