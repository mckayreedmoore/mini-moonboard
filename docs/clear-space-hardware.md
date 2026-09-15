# Hardware for the exterior-brace and floor-rail trials

Research date: September 13, 2026. This is a catalog and installation assessment
for the separate clear-space candidates. It does not transfer the selected
brace's force results or establish that either trial passes structural checks.
No order was placed and no supplied lot has been measured. Retain the existing
[half-inch upper-joint hardware basis](compact-half-inch-hardware.md).

## Revised exterior upper joint

The current exterior revision uses two half-inch bolts per leg at **64 mm
pitch**, with the leg top projecting **24 mm** normal to the rim rear face.
Its upper round washers require **3.0–3.3528 mm delivered thickness**; the
3.0 mm lower bound is used in the revised washer-bending assessment. Retain
the existing 34.7472 mm minimum outside diameter, 14.6558 mm maximum bore,
33 ksi yield reference and complete plain-body/thread-transition requirements.
The nominal CAD thickness remains 3.175 mm. These limits apply to the four
upper bolt stacks only; the three-eighths-inch washers below are unchanged.
See [the revision and its current evidence](exterior-upper-joint-revision.md).
The preserved floor-rail upper joint retains its original 56 mm pattern and
hardware basis. Do not transfer the revised exterior result to that geometry.

## Purchasable three-eighths-inch hardware

| Use | Catalog product | Published length and thread limits |
| --- | --- | --- |
| Exterior brace, rim endpoints | [Bolt Depot 373](https://boltdepot.com/Product-Details?product=373), 3/8-16 × 8-inch Grade 5 hex bolt | ASME B18.2.1, SAE J429; length +0/−0.18 inch; partially threaded, minimum 1.25-inch thread. |
| Exterior brace, leg endpoints and splices; floor-rail rear joints | [Bolt Depot 371](https://boltdepot.com/Product-Details?product=371), 3/8-16 × 6-inch Grade 5 hex bolt | ASME B18.2.1, SAE J429; length +0/−0.10 inch; partially threaded, minimum 1-inch thread. |
| Floor-rail front joints | [Bolt Depot 367](https://boltdepot.com/Product-Details?product=367), 3/8-16 × 4-inch Grade 5 hex bolt | ASME B18.2.1, SAE J429; length +0/−0.06 inch; partially threaded, minimum 1-inch thread. |

Each uses [Bolt Depot 2571](https://boltdepot.com/Product-Details?product=2571)
3/8-16 Grade 5 nuts, SAE J995/ASME B18.2.2, height 0.320–0.337 inch;
and two [Bolt Depot 15023](https://boltdepot.com/Product-Details?product=15023)
Grade 5 USS washers, ASME B18.21.1. The washer thickness range is
**0.064–0.104 inch (1.6256–2.6416 mm)**. Its maximum is not 0.109 inch.
Washer OD is 0.993–1.030 inch and bore 0.433–0.453 inch. Retain the
[existing minimum-dimension resistance envelope and conditional material assumptions](compact-splice-hardware.md):
25.2222 mm minimum OD, 11.5062 mm maximum bore, 1.6256 mm minimum thickness,
and the explicit 33 ksi washer-yield assumption. Catalog grade wording alone
does not establish washer plate yield.

## Required full-body length

Install heads toward the board center and nuts/tips outward. Let `G` be actual
wood grip, `W` actual head-washer thickness, and `T` the nut-side wood bearing
length. For the retained nominal-diameter, quarter-thread-bearing route,
the first reduced shank or thread-transition section must be at least
`G + W − T/4` from under the head. Count the entire transition as threaded.
The table uses the maximum catalog head washer, 2.6416 mm, and modeled stock
thicknesses. All these thresholds put the head-side member entirely on the
full body; the nut-side member governs. Actual wood variation requires
recalculating the threshold, not assuming the nominal grip remains exact.

| Connection | Head-side → nut-side wood | Grip (mm) | Minimum full body to first transition (mm) |
| --- | --- | ---: | ---: |
| Exterior rim endpoint | 88.9 mm rim → 88.9 mm rim-knee | 177.8 | **158.2166** |
| Exterior knee splice | 88.9 mm rim-knee → 38.1 mm leg-knee | 127.0 | **120.1166** |
| Exterior leg endpoint | 88.9 mm leg → 38.1 mm leg-knee | 127.0 | **120.1166** |
| Floor-rail front | 38.1 mm post → 38.1 mm rail | 76.2 | **69.3166** |
| Floor-rail rear | 38.1 mm rail → 88.9 mm leg | 127.0 | **107.4166** |

For feasibility only, shortest catalog bolt minus minimum thread length gives
166.878 mm for the 8-inch bolt, 124.460 mm for the 6-inch bolt, and 74.676 mm
for the 4-inch bolt. Those lengths exceed the corresponding required values.
However, this is **not a lower bound on supplied full-body length**: minimum
thread length is not maximum thread length, and transition length also matters.
The supplier explicitly offers to measure current stock when needed in its
[minimum-thread table](https://boltdepot.com/Fastener-Information/Bolts/US-Thread-Length).
Measure supplied bolts against the table above before installation; reject
unsuitable transitions instead of silently relying on nominal diameter.

## Nut engagement and runout

The following calculation combines minimum catalog bolt length, two maximum
2.6416 mm washers, maximum 8.5598 mm nut height, and modeled wood grip.

| Bolt / grip | Minimum length (mm) | Maximum complete stack (mm) | Tip beyond nut (mm) |
| --- | ---: | ---: | ---: |
| 8-inch / 177.8 mm | 198.628 | 191.643 | **6.985** |
| 6-inch / 127.0 mm | 149.860 | 140.843 | **9.017** |
| 4-inch / 76.2 mm | 100.076 | 90.043 | **10.033** |

All exceed two nominal 16-TPI pitches, 3.175 mm. Actual tip chamfer and complete
formed-thread engagement still require inspection. With maximum bolt length
and minimum listed thread length, the nominal thread start is 171.45, 127.0,
or 76.2 mm, respectively. Two minimum-thickness washers place the nut's bearing
face 9.6012 mm beyond that start for the 8-inch arrangement and 3.2512 mm beyond
it for the 6- and 4-inch arrangements. Verify usable threads begin before the
nut bearing face, so the nut seats against its washer rather than stopping on
runout. Do not interpret projected tip length as proof of full nut engagement.

The catalog route is feasible under the stated inspection conditions. The
candidate's force, wood, clearance, and washer checks remain separate. Preserve
full flat washer seating and outward tips; do not substitute sloped washer
seats, air-gap spacers, or unverified fully threaded bolts.
