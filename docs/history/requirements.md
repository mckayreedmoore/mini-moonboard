# Mini MoonBoard requirements

## Source policy

The official documents remain at their publisher's URLs rather than being
copied into this repository:

- [MoonBoard DIY Kit Build Guide](https://moonclimbing.com/media/moonboard-pdf/How-to-build-a-MoonBoard_v2.3.pdf)
- [Mini MoonBoard Template Guide - Metric](https://moonclimbing.com/media/moonboard-pdf/Mini_MoonBoard_Template_Guide_Metric.pdf)
- [Mini MoonBoard Template Guide - Imperial](https://moonclimbing.com/media/moonboard-pdf/Mini_Moonboard_Template_Guide_IMPERIAL.pdf)
- [MoonBoard LED System V3 Installation and Troubleshooting Guide, version 5.2](https://moonclimbing.com/media/moonboard-pdf/NewMB_LED_Instructions_may2024.pdf)
- [Official Mini MoonBoard 2020 DIY Kit page](https://us.moonclimbing.com/products/mini-moonboard-2020-diy-kit)

These sources were accessed on 2026-09-03. Check them again before fabrication
in case Moon Climbing publishes a revision.

The downloaded bytes used for this review had the following fingerprints.
These hashes detect a later publisher-side change; they are not a substitute
for checking that a newer official document exists.

| Document | Pages | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| DIY Kit Build Guide | 3 | 1,248,505 | `2f3d1563cf405a6dd297bf5ca61592806b39d56a024bce260e496305d88917c2` |
| Metric template | 1 | 72,837 | `7bc1cdeb1111c3292ffef4e9929deaed15e531fb7de30b80fd2d88eab78012e6` |
| Imperial template | 1 | 107,550 | `84a032deacb02800bd035b4795f26cae7cf97e4217e4265ff31723db392bd14b` |
| LED V3 guide, version 5.2 | 8 | 48,472,717 | `b783ae3a5b1b844f5f6a92cc910b95ba232b398d6fa9265fbf85035c1cd33373` |

## Official geometry

| Requirement | Source-stated metric | Source-stated imperial | Notes |
| --- | ---: | ---: | --- |
| Board angle | 40 degrees from vertical | 40 degrees from vertical | Fixed Mini MoonBoard geometry |
| Main panels | 4 x 1220 x 1220 mm nominal | 4 x 48 x 48 in | Two panels wide by two high |
| Main surface | 2440 x 2440 mm nominal | 8 x 8 ft nominal | Before the kicker |
| Main panel thickness | 18 mm | 0.71 in converted | Birch plywood |
| Official kicker panels | 2 x 1220 x 150 mm | 2 x 48 x 5.9 in | Custom design will be taller |
| Upright supports | 4 at 813 mm spacing | 4 at 2 ft 8 in spacing | Frame requirement, not member sizing |
| Overall width | 2440 mm | 8.01 ft | Plus safe fall zone |
| Overall depth | 1569 mm | 5.15 ft | Plus safe fall zone |
| Overall height | 2020 mm | 6.63 ft | Plus matting |

The official height and depth are rounded values. From a 2440 mm sloped main
surface at 40 degrees from vertical and a 150 mm vertical kicker:

- vertical projection = 2440 x cos(40 degrees) = 1869.1 mm;
- overall height = 1869.1 + 150 = 2019.1 mm, rounded to 2020 mm; and
- horizontal projection = 2440 x sin(40 degrees) = 1568.3 mm, rounded to
  1569 mm.

All CadQuery geometry uses millimetres. Documentation converts exact model
values to inches using 25.4 mm per inch, normally rounded to 1/16 inch for shop
dimensions. A source-stated imperial dimension is not silently replaced with a
conversion.

## Official assembly constraints

The DIY build guide says its frame suggestions are basic requirements, that the
actual structural frame may differ, and that the published height, width, and
angle must be retained. It expects basic carpentry capability, tools, and at
least two people for assembly. This repository treats those statements as a
reason to require review of the completed custom freestanding frame, not as a
structural design specification.

For the Mini layout, the guide specifies four upright support lines at 813 mm
/ 2 ft 8 in spacing, placed above the kickboard at the 40-degree board angle.
It directs builders to attach two kicker panels and four main panels, then use
18 mm plywood strips to brace panel joints as shown. The guide does not give a
dimensioned strip schedule, member sizes, fastener schedule, connection design,
or freestanding stability design, so none is inferred here.

The guide directs hold setup through the MoonBoard app or website so each hold
uses its correct grid reference and orientation. The current V3 LED guide
specifies 13 mm / 1/2 in LED holes beneath the corresponding T-nuts and advises
testing LEDs before installation. That diameter applies only if the selected
system is covered by that V3 guide; record the actual LED-system version and
follow its supplied guide before drilling.

The current official build page says metric setups use M10 T-nuts and bolts,
with 3/8 in as the imperial equivalent. It specifies a 13 mm / 1/2 in T-nut
drill hole and a 10 mm / 0.393 in T-nut barrel length. The US Mini 2020 product
page also describes 3/8 in pre-drilled panels and included M10 hold bolt kits
as compatible. Select one physical hardware system, record its manufacturer
dimensions, and make a plywood offcut test before producing all holes; the
published descriptions are not permission to mix incompatible parts.

## Panel template

The template guides define columns A-K and rows 1-12 for the Mini MoonBoard.
The metric sheet shows a 200 mm repeating T-nut grid and a typical 100 mm
T-nut-to-LED-row offset. It also contains the separate kickboard foothold
pattern.

The template files are not mutually exact conversions: the metric guide labels
an overall width of 2437 mm, while the imperial guide labels 96 1/64 in
(2438.8 mm). The build guide uses a nominal 2440 mm envelope. Therefore:

1. preserve the official metric and imperial drawings independently;
2. choose the fabrication system before authorizing a drilling model for cuts;
3. print the chosen template at 100 percent scale; and
4. measure its calibration dimensions before drilling any panel.

Moon's [current build guide](https://moonclimbing.com/build-your-moonboard)
also calls for four upright supports at 813 mm
(2 ft 8 in) spacing and says that the frame's structural requirements can vary
by installation. V1 preserves the four-primary-support arrangement as four
board-parallel rails at 812.8 mm centers across its controlled 2438.4 mm
surface; its fifth center-seam rail is a panel-joint reinforcement, not a
substitute primary upright. This reproduces the layout requirement while
leaving the unanchored frame's structural design subject to the V1 review gate.

The V1 CAD assembly now includes provisional visual/drill bores at the
source-backed main T-nut, LED, and official kicker foothold centres encoded in
[`panel-grid.md`](panel-grid.md). It uses the selected Escape 7/16-in bore and
conditional 13 mm LED bores to expose geometry and clearance issues. Physical
production drilling still requires the selected hardware, template system, and
actual plywood-sheet test.

## Source discrepancies and cautions

- The current `v2.3` build-guide URL serves a document whose footer says
  version 2.2, July 2023.
- The build-guide imperial typography appears to omit decimal points in some
  height labels. Use its metric values and the official product page rather
  than interpreting those strings literally.
- Nominal 3/4 in plywood is 19.05 mm, not 18 mm. Measure actual stock before
  modelling joints or fastener lengths.
- The official US product page mentions both 3/8 in and M10 hold hardware.
  Select T-nuts and bolts as one verified system; do not assume they are
  interchangeable.
- Moon Climbing specifies additional matting and safe-fall-zone requirements
  but does not define them in these documents. Those clearances remain a site
  and safety-review input.

## Remaining inputs before structural fabrication

- actual plywood sheet dimensions, grade, ply count, and measured thickness;
- accepted frame-member lamination count and adhesive schedule;
- connection hardware, joint geometry, and assembly/disassembly requirement;
- design loads, connection loads, floor interface, and anti-racking strategy;
- qualified review of the completed load path and local requirements.

V1 deliberately fixes a 225 mm kicker and excludes the crash pad, room survey,
obstructions, and egress from its design scope. Those remain separate site and
safety work; omitting them does not approve installation or climbing use.
