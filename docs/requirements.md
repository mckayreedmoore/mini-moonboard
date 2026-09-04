# Mini MoonBoard requirements

## Source policy

The official documents remain at their publisher's URLs rather than being
copied into this repository:

- [MoonBoard DIY Kit Build Guide](https://moonclimbing.com/media/moonboard-pdf/How-to-build-a-MoonBoard_v2.3.pdf)
- [Mini MoonBoard Template Guide - Metric](https://moonclimbing.com/media/moonboard-pdf/Mini_MoonBoard_Template_Guide_Metric.pdf)
- [Mini MoonBoard Template Guide - Imperial](https://moonclimbing.com/media/moonboard-pdf/Mini_Moonboard_Template_Guide_IMPERIAL.pdf)
- [Official Mini MoonBoard 2020 DIY Kit page](https://us.moonclimbing.com/products/mini-moonboard-2020-diy-kit)

These sources were accessed on 2026-09-03. Check them again before fabrication
in case Moon Climbing publishes a revision.

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

## Panel template

The template guides define columns A-K and rows 1-12 for the Mini MoonBoard.
The metric sheet shows a 200 mm repeating T-nut grid and a typical 100 mm
T-nut-to-LED-row offset. It also contains the separate kickboard foothold
pattern.

The template files are not mutually exact conversions: the metric guide labels
an overall width of 2437 mm, while the imperial guide labels 96 1/64 in
(2438.8 mm). The build guide uses a nominal 2440 mm envelope. Therefore:

1. preserve the official metric and imperial drawings independently;
2. choose the fabrication system before generating a drilling model;
3. print the chosen template at 100 percent scale; and
4. measure its calibration dimensions before drilling any panel.

The first CAD milestone intentionally models panel blanks and seams, not the
T-nut, LED, hold, or mounting holes. The hole model will be added only after
the template system and actual plywood sheets are verified.

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

## Required inputs for the buildable frame

- crash-pad make, model, deployed thickness, width, and depth;
- exposed kicker height desired above the deployed pad;
- available ceiling height, floor footprint, and surrounding fall zone;
- actual plywood sheet dimensions, grade, ply count, and measured thickness;
- accepted frame-member lamination count and adhesive schedule;
- connection hardware, joint geometry, and assembly/disassembly requirement;
- design loads, connection loads, floor interface, and anti-racking strategy;
- qualified review of the completed load path and local requirements.

