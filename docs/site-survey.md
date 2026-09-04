# Site survey and design-input worksheet

This worksheet records later human checks. V1 intentionally proceeds without a
room survey and treats the crash pad as a separate element; neither is an input
to the provisional board-and-legs model. Record measured values in both unit
columns; do not fill one column with nominal product names such as "8 foot" or
"3/4 inch."

## Machine-readable inputs

The worksheet remains the human review record. Once its fields are measured,
copy [`design-inputs.example.toml`](../design-inputs.example.toml) to the
ignored `design_inputs.toml` file and enter the canonical millimetre values:

```bash
cp design-inputs.example.toml design_inputs.toml
uv run python -m mini_moonboard.site_inputs design_inputs.toml
```

The legacy validator reports missing fields and derives a pad-dependent kicker
height as:

```text
highest deployed pad surface + desired clear face + 150 mm official active zone
```

It is not the v1 design gate and does not approve the room, impact area, frame,
floor interface, or structural design.

## Installation and reviewer

| Input | Value |
| --- | --- |
| Installation city/state/country | **unresolved** |
| Applicable building or owner restrictions | **unresolved** |
| Qualified structural/carpentry reviewer | **unresolved** |
| Intended users and maximum anticipated body mass | **unresolved** |
| Fixed assembly or demountable for relocation | **unresolved** |

## Clear room envelope

Measure to the nearest 3 mm / 1/8 in at several points. Use the smallest clear
dimension and sketch the locations of every obstruction.

| Input | Metric | Imperial | How to measure |
| --- | ---: | ---: | --- |
| Clear width | **unresolved** mm | **unresolved** in | Wall/obstruction to wall/obstruction across the board |
| Clear depth | **unresolved** mm | **unresolved** in | Front landing-area limit to rear obstruction |
| Minimum ceiling height | **unresolved** mm | **unresolved** in | Finished floor to lowest ceiling/beam/fixture over the entire footprint |
| Door/opening width and height | **unresolved** mm | **unresolved** in | Smallest opening that prefabricated parts must pass through |
| Required egress clearance | **unresolved** mm | **unresolved** in | Clearance that must remain after installation |

Also record the position and projection of windows, doors, trim, baseboards,
outlets, radiators, sprinklers, lights, fans, ducts, and plumbing. Photographs
should include a tape or other known scale in the same plane as the measured
feature.

## Floor interface

| Input | Metric | Imperial | Notes |
| --- | ---: | ---: | --- |
| Floor slope across width | **unresolved** mm/m | **unresolved** in/ft | Measure beneath every planned foot |
| Floor slope across depth | **unresolved** mm/m | **unresolved** in/ft | Measure beneath every planned foot |
| Step or local height variation | **unresolved** mm | **unresolved** in | Record position |
| Finish and substrate | **unresolved** | **unresolved** | Identify finish and the load-bearing substrate below it |
| Condition | **unresolved** | **unresolved** | Record cracks, loose finish, moisture, damage, deflection, and any repair needed |
| Permitted attachment | — | — | Confirm whether drilling/anchoring is prohibited |

The frame design must not assume that finish flooring can resist concentrated
load, sliding, uplift, or overturning. The reviewer must establish the floor
interface and any required load-spreading or anti-slip details.

## Crash-pad system (separate; not part of v1)

Measure the pads in their deployed climbing arrangement, including gaps,
hinges, overlaps, and wall contact.

| Input | Metric | Imperial |
| --- | ---: | ---: |
| Manufacturer and model | **unresolved** | **unresolved** |
| Deployed width | **unresolved** mm | **unresolved** in |
| Deployed depth | **unresolved** mm | **unresolved** in |
| Unloaded thickness | **unresolved** mm | **unresolved** in |
| Highest overlap or seam | **unresolved** mm | **unresolved** in |
| Horizontal distance from kicker face | **unresolved** mm | **unresolved** in |
| Method for preventing gaps/movement | **unresolved** | **unresolved** |

Do not infer an impact area from the footprint of a portable pad. The required
impact-attenuating surface and clear fall zone must be established separately
under the applicable guidance and qualified review.

The gap-prevention entry must identify every seam, hinge, wall/kicker edge, and
pad-to-pad junction; state the physical restraint or overlap used at each one;
and be verified after the pads are deployed. A pad arrangement that can migrate
or expose a hard edge is not accepted.

## Obstructions and egress (deferred; not part of v1)

Record every item within the board, frame, landing, and required egress areas.
The image/video is not a scaled survey and cannot clear any item in this table.

| Item/location | Projection or clearance | Effect / required action |
| --- | ---: | --- |
| Doors, windows, trim, outlets, radiators, lights, fans, ducts, sprinklers, plumbing, and stored items | **unresolved** mm / **unresolved** in | **unresolved** |
| Required egress route(s), including smallest remaining width and height after installation | **unresolved** mm / **unresolved** in | **unresolved** |

Do not place the board, frame, pads, wiring, or stored equipment in a required
egress route. Confirm the final route with the owner or authority having
jurisdiction before installation.

## Taller kicker relationship

The official main surface rises 1869.1 mm / 73.59 in vertically and projects
1568.4 mm / 61.75 in horizontally. Therefore, before frame and rear-leg
allowances:

```text
main-surface top height = total kicker height + 1869.1 mm
main-surface projection = 1568.4 mm
```

V1 fixes the official foothold row at 75 mm / 2.95 in below the main-surface
seam. Its blank extension equals that same 75 mm datum below Moon Climbing's
150 mm active zone:

```text
total v1 kicker height = 75 mm blank extension + 150 mm active zone = 225 mm
```

This fixes only the board geometry. It does not define a pad relationship or
an impact surface.

| Input | Metric | Imperial |
| --- | ---: | ---: |
| Blank extension below official active zone | 75 mm | 2.95 in |
| Total v1 kicker height | 225 mm | 8.86 in |
| Nominal-reference main-surface top height | 2094.1 mm | 82.44 in |

Any later pad-clearance decision is a separate design/safety task, not a Moon
Climbing recommendation or a change to this fixed v1 board geometry. The
controlled 48-in-stock V1 model deliberately uses 1218.0 mm panels, so its
actual main-surface top is 2092.9 mm; see the V1 build package rather than
using this nominal-reference calculation for cuts.

## Plywood and hardware samples

Record values from the stock that can actually be purchased, ideally from the
same batch intended for construction.

| Input | Metric | Imperial |
| --- | ---: | ---: |
| Panel sheet length x width | **unresolved** mm | **unresolved** in |
| Selected panel-stock reference | Swaner Hardwood C-3 birch plywood, Home Depot 165921; user-provided URL recorded 2026-09-04 | **unresolved** pending received-sheet measurement |
| Panel measured thickness: min/average/max | **unresolved** mm | **unresolved** in |
| Frame-lamination sheet length x width | **unresolved** mm | **unresolved** in |
| Frame-ply measured thickness: min/average/max | **unresolved** mm | **unresolved** in |
| Species, grade, ply count, and certification | **unresolved** | **unresolved** |
| Hold/T-nut thread standard | 3/8-16 Escape screw-in T-nuts selected | 3/8-16 Escape screw-in T-nuts selected |
| Selected T-nut reference | Escape 3-hole screw-in T-nut, Amazon ASIN B00FJGT7QI; user-provided URL recorded 2026-09-04 | **unresolved** pending sample inspection |
| T-nut body length, flange diameter, and flange thickness | **unresolved** mm | **unresolved** in |
| T-nut hole diameter and barrel length | 11.11 mm / 7/16 in bore per selected Escape listing; barrel actual sample **unresolved** | 7/16 in bore per selected Escape listing; barrel actual sample **unresolved** |
| LED-system version and guide revision | MoonBoard LED System, SKU 60-201-V5; supplied guide revision **unresolved** | MoonBoard LED System, SKU 60-201-V5; supplied guide revision **unresolved** |
| LED body diameter, shoulder diameter, body length, and rear clearance | **unresolved** mm | **unresolved** in |
| LED hole diameter | 13 mm / 1/2 in for the selected MoonBoard guide; purchased system **unresolved** | 13 mm / 1/2 in for the selected MoonBoard guide; purchased system **unresolved** |

Photograph product labels and retain a sample T-nut, bolt, LED, and plywood
offcut for fit checks before production drilling. Take thickness readings at
multiple positions on each actual sheet, record the minimum, arithmetic mean,
and maximum, and do not substitute nominal thickness. The official hole and
barrel figures above are from Moon Climbing's [current build guidance](https://moonclimbing.com/build-your-moonboard);
they do not replace measurements of the purchased T-nuts or LEDs.

## Survey acceptance

- [ ] Every unresolved field needed by the selected design is completed.
- [ ] Metric and imperial entries agree within the stated measurement accuracy.
- [ ] A dimensioned room sketch and scaled photographs are attached.
- [ ] The deployed pad arrangement is photographed and dimensioned.
- [ ] Actual stock and hardware samples have been measured.
- [ ] The reviewer has confirmed that the collected inputs are sufficient for
      detailed frame design.
