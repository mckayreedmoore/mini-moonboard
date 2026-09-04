# Materials ledger

This ledger separates source-backed climbing-surface requirements from the
provisional V1 construction package. The generated
[`v1 BOM`](../exports/mini_moonboard_v1_bom.csv) and
[sheet-nesting plan](v1-sheet-nesting.md) are the controlled purchase/count
references; this page records what still requires a human audit.

## Confirmed or source-backed

| Material or component | Current requirement | Status |
| --- | --- | --- |
| Main climbing panels | 4 birch plywood panels, 1219.2 x 1219.2 mm v1 stock target | One factory-width panel per 4 x 8 sheet; its 2438.4 mm overall width is within 0.4 mm of the imperial template width. Verify official-template calibration and actual stock. |
| Kicker panels | 2 birch plywood panels, 1219.2 x 225 mm v1 stock target | Provisional v1: 150 mm active zone plus 75 mm blank extension below |
| Main horizontal panel-joint backing | Five 36 mm laminated, 180 x 60 mm bearing blocks | CAD and primary connection schedule bridge the lower/upper main-panel seam; screw datums are generated |
| Hold hardware | Escape Climbing 3-hole screw-in T-nuts, 3/8-16 | Selected; use 7/16 in bore after offcut fit test, 142 positions minimum, and matching 3/8-16 hold bolts |
| Climbing holds and LEDs | User-owned Mini MoonBoard 2025 Setup Hold Bundle, SKU 60-105-2025, and MoonBoard LED System, SKU 60-201-V5 | The hold set is a replaceable board-layout configuration, not a frame input. The 2025 bundle has 138 holds and excludes bolts/T-nuts/LEDs. The standard LED kit supplies four 50-LED strings / 200 bulbs; V1 installs 132 and retains 68 (18 on the third-string tail and a whole unused fourth string), including Moon's two terminal spares. |
| Surface finish | Durable coating suitable for the climbing panels | Exact coating system unresolved |

The user-selected panel stock is [Swaner Hardwood 3/4-in x 4-ft x 8-ft C-3
Birch Plywood, Home Depot product 165921](https://www.homedepot.com/p/Swaner-Hardwood-3-4-in-x-4-ft-x-8-ft-C-3-Birch-Plywood-165921/202085716), recorded 2026-09-04.
The selected hold insert is [Escape Climbing 3-hole screw-in T-nut, Amazon
ASIN B00FJGT7QI](https://www.amazon.com/dp/B00FJGT7QI?ref=ppx_yo2ov_dt_b_fed_asin_title),
recorded 2026-09-04. These are user-provided listing references, not verified
material certifications: availability, dimensions, grade, and every listing
claim remain provisional until the received samples and offcut test are logged.

The user-owned [Mini MoonBoard 2025 Setup Hold Bundle](https://us.moonclimbing.com/products/mini-moonboard-2025-hold-set)
is SKU `60-105-2025`. Moon states it contains 138 holds—Original School Holds,
School Holds Set F, and Wood Holds B/C—and that bolts, T-nuts, and LED hardware
are not included. The 2020 and 2025 Mini hold configurations are interchangeable
on this same frame: their selection changes only the app-directed hold position,
orientation, hold-bolt inventory, and unused insert count. It does not change
the panel envelope, rails, legs, structural fasteners, or FEA model. The
per-hold bolt inventory and orientation transfer are controlled by
[`v1-hold-installation.md`](v1-hold-installation.md), not guessed from panel CAD.

## Provisional frame approach

The v1 concept has three assemblies: the board/kicker and two exterior
hockey-stick legs. Every support member is a two-ply laminate of nominal 3/4
in birch plywood. Each leg follows the board to the datum two T-nut rows below
the top, bends at the datum five rows below the top, and reaches the floor at
a provisional 60-degree angle to the descending board line. It is unanchored.
This is a geometry/manufacturing preference, not a validated structural
specification.

The V1 cut list and nesting plan now account for the frame stock. Do not cut
load-bearing parts or purchase irreversible hardware until these human-audit
items are resolved:

- plywood species, structural grade, veneer quality, and sheet dimensions;
- measured sheet thickness and number of laminated layers;
- structural adhesive, spread rate, open time, clamping pressure, and cure;
- the reviewer disposition for every panel, rail, tie, and kicker/main joint;
- bolt, screw, washer, insert, and plate specifications;
- edge sealing and finish appropriate to the installation environment; and
- replaceable feet, anti-slip treatment, and floor protection.

## Selected hardware and LED provisions

The selected Escape hardware is imperial 3/8-16 screw-in T-nuts. Its specified
7/16 in bore differs from Moon Climbing's generic 13 mm / 1/2 in T-nut bore;
the Escape offcut test governs the selected T-nut installation. Use only
matching 3/8-16 bolts. Do not mix M10 bolts with these inserts. The received
sample measures about a 1 in (25.4 mm) flange, 0.07 in (1.86 mm) flange
thickness, 1/2 in (12.7 mm) body depth, and three roughly 3.2 mm flange screw
holes. An adjacent 12.78 mm inside-edge gap derives a 15.98 mm center-to-center
spacing for equal 3.2 mm holes, but this is only a check value. After the main
7/16 in bore is drilled, seat each physical insert, mark through its own three
holes, then pilot-drill: the received part controls the screw pattern.

Moon Climbing's own hardware path instead calls for metric M10 T-nuts and
bolts (with 3/8 in described as the imperial counterpart) and its build page
lists a 13 mm / 1/2 in bore with a 10 mm barrel. If MoonBoard T-nuts are used,
buy the required fixing screws separately and confirm the exact selected
product's bore, barrel, flange, and screw requirements on an offcut.

The selected [MoonBoard LED System](https://us.moonclimbing.com/products/moonboard-led-kit)
is SKU 60-201-V5. Drill the 13 mm LED holes at the official LED datums and
provide protected rear routing to the controller, with access to its switch,
only after the supplied V5 guide confirms that 13 mm diameter for this kit.
The received LED projects about 31 mm behind the panel: a 24 mm lugged cylinder
(12.7 mm maximum diameter, about 11.7 mm core) and a 7 mm, about 7.5 mm dome
observed at roughly a 75-degree axis. That leaves only 5 mm in V1's 36 mm
service gap and must be dry-fitted at every rail/block condition.
The kit includes a controller, four 50-LED strings, supplementary power feeds,
and a 5 V adapter according to the selected product listing. The listing's 200
bulbs include 2 spares and describes 66 extra bulbs on a Mini. Install 132
LEDs: two complete strings plus 32 LEDs from the third string. Retain its
remaining 18 bulbs and the unused fourth string (68 uninstalled bulbs total).
Reconcile every LED with the supplied V5 guide during the offcut/template
audit. A future kit version is a separate compatibility variant:
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
