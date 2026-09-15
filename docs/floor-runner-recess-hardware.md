# Hardware for the recessed floor-runner trial

Research date: September 14, 2026. This is the corrected modeled hardware schedule for `compact-floor-recess-development`, not a construction release. No order or delivered-lot measurement is represented.

## Twelve complete bolt stacks

| Quantity | Location | Bolt | Wood grip |
| ---: | --- | --- | ---: |
| 4 | Upper leg/rim joints | Existing [Bolt Depot 407, ½-13 × 8-inch Grade 5](https://boltdepot.com/Product-Details?product=407) | 177.8 mm |
| 4 | Front post/runner joints | Existing [Bolt Depot 367, ⅜-16 × 4-inch Grade 5](https://boltdepot.com/Product-Details?product=367) | 76.2 mm |
| 4 | Recessed rear runner/leg joints | **[Bolt Depot 368, ⅜-16 × 4½-inch Grade 5](https://boltdepot.com/Product-Details?product=368)** | **88.9 mm** |

Retain four half-inch nuts and eight half-inch washers under the [existing upper-joint hardware basis](compact-half-inch-hardware.md). The eight smaller bolts use eight [Grade 5 nuts, Bolt Depot 2571](https://boltdepot.com/Product-Details?product=2571), and sixteen [Grade 5 USS washers, Bolt Depot 15023](https://boltdepot.com/Product-Details?product=15023). Their catalog bounds and resistance assumptions remain those in [clear-space hardware](clear-space-hardware.md). All heads face inward; nuts and tips face outward.

## Why the initial 5-inch rear bolt must change

The first model used a 127 mm bolt and 25.4 mm thread length, placing the thread start 101.6 mm from under the head. With 88.9 mm grip and two modeled 2.032 mm washers, the nut must begin seating at **92.964 mm**. That places its seat before the modeled usable thread: the stack cannot tighten as represented. A cylindrical CAD shaft alone does not detect this problem. That 5-inch/minimum-thread combination is rejected. The current model uses the corrected 4½-inch rear bolts; matching exports and schedules must be regenerated before use.

A 4½-inch bolt is 114.3 mm long. With the same modeled thread length, its thread starts at **88.9 mm**, before the nut seat. The nominal 8.5598 mm nut ends at 101.5238 mm, leaving 12.7762 mm of projected bolt. Bolt Depot specifies product 368 as partially threaded SAE J429 Grade 5, length +0/−0.10 inch, with at least one inch of thread. See the [product specification](https://boltdepot.com/Product-Details?product=368).

## Delivered thread and seating checks

For the retained nominal-diameter bearing route, require full body through at least `grip + head-washer thickness − nut-side bearing length/4`. With the maximum catalog washer thickness of 2.6416 mm:

| Joint | Nut-side timber | Required full body to first transition |
| --- | ---: | ---: |
| Front | 38.1 mm runner | 69.3166 mm |
| Rear | 50.8 mm remaining leg | **78.8416 mm** |

Treat runout as threaded. For feasibility, the shortest listed 4½-inch bolt minus the minimum thread length gives 86.36 mm; this exceeds the rear threshold but is **not** a guaranteed minimum full-body length. Actual threads can be longer than the published minimum. [Bolt Depot explains this limitation and offers current-stock measurements](https://boltdepot.com/Fastener-Information/Bolts/US-Thread-Length).

Using minimum bolt length, two maximum washers and maximum nut height leaves **9.017 mm** beyond the rear nut. Two minimum washers place its bearing face 3.2512 mm beyond the nominal thread start. Verify actual usable thread begins before that face, the nut seats fully, and complete threads extend beyond the nut. Actual wood thickness changes require recalculating these positions. These dimensional checks do not qualify the recessed wood connection or establish a preload.
