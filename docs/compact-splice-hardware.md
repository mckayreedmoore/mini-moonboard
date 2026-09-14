# Catalog hardware for the independent knee splices

Research date: 2026-09-13. Applies to `compact-spliced-knee-development`.
This identifies purchasable components and conservative assessment inputs;
no order was placed and no delivered lot has been inspected. Upper half-inch
hardware remains covered by [its separate assessment](compact-half-inch-hardware.md).

## Concrete schedule

| Quantity | Function | Catalog reference | Relevant specification |
| --- | --- | --- | --- |
| 8 | Central splice bolts | [Bolt Depot 367](https://boltdepot.com/Product-Details?product=367) | 3/8-16 × 4 inches, partially threaded SAE J429 Grade 5; ASME B18.2.1; length +0/−0.06 inch; thread length minimum 1 inch. |
| 8 | Brace-to-host bolts | [Bolt Depot 371](https://boltdepot.com/Product-Details?product=371) | 3/8-16 × 6 inches, partially threaded SAE J429 Grade 5; ASME B18.2.1; length +0/−0.10 inch; thread length minimum 1 inch. |
| 16 | Nuts | [Bolt Depot 2571](https://boltdepot.com/Product-Details?product=2571) | Matching 3/8-16 SAE J995 Grade 5, ASME B18.2.2; height 0.320–0.337 inch, across flats 0.551–0.563 inch. |
| 32 | Head and nut washers | [Bolt Depot 15023](https://boltdepot.com/Product-Details?product=15023) | Grade 5 USS, ASME B18.21.1; OD 0.993–1.030 inch, bore 0.433–0.453 inch, thickness 0.064–0.104 inch. |

The washer is described as tempered medium-carbon steel. Its grade label does
not supply a numerical plate-yield guarantee. Retain **33 ksi washer yield as
an explicit conditional material assumption**, pending supplied material
conformity; do not substitute bolt tensile yield for washer plate yield.

## Conservative resistance envelope

Use minimum washer OD **25.2222 mm**, minimum thickness **1.6256 mm**, and
maximum washer bore **11.5062 mm**. The rendered 25.4 × 2.032 mm washer with
11.1125 mm bore is nominal geometry, not this lower-bound resistance envelope.
A thickness-only plate-bending sensitivity increases demand ratio by
(2.032/1.6256)² = **1.5625**, before bore and diameter effects. An assumed
bearing seat of 95% of minimum nut across-flats dimension is **13.29563 mm**;
that 95% factor is an assessment assumption rather than a catalog dimension.

Bolt Grade 5 material permits the same conditional 90 ksi tensile-yield route
explained in the linked half-inch assessment. This does not establish that
unverified threaded regions may be analyzed at full nominal diameter.

## Stack and thread feasibility

Install all bolt heads toward the board center and nuts/threaded ends toward
the outside. At the rim endpoint, the head seats on the 88.9 mm rim and the
nut on the 38.1 mm knee piece; at the leg endpoint, the head seats on the
38.1 mm knee piece and the nut on the 88.9 mm leg. At each splice, the head
seats on the inboard knee piece and the nut on the outboard knee piece.
Splices contain two 38.1 mm pieces, giving **76.2 mm** wood grip; brace-to-host
connections contain 38.1 + 88.9 mm, giving **127 mm** grip. The following arithmetic uses the
shortest catalog bolt, two thickest washers (2.6416 mm each), and tallest nut
(8.5598 mm). It assumes the stated wood grips without additional stock variation.

| Connection | Minimum bolt length | Maximum stack including nut | Tip beyond nut |
| --- | ---: | ---: | ---: |
| Splice | 100.076 mm | 90.043 mm | 10.033 mm |
| Brace to host | 149.860 mm | 140.843 mm | 9.017 mm |

These exceed two nominal 16-TPI thread pitches (3.175 mm), but actual tip
chamfer and usable formed-thread engagement still matter. With the longest
bolt and minimum 25.4 mm thread length, the theoretical thread starts are
76.2 and 127 mm. Even two minimum-thickness washers place the nut bearing
faces at 79.4512 and 130.2512 mm, respectively, leaving **3.2512 mm** for
runout before the nut seat. Verify fully usable threads reach that seat;
thread-length arithmetic alone does not certify runout clearance.

[The supplier's thread table](https://boltdepot.com/Fastener-Information/Bolts/US-Thread-Length)
explicitly specifies a **minimum**, and says supplied threads may be longer.
Therefore the model's exact 25.4 mm thread length cannot serve as a maximum
thread-penetration guarantee. For the established quarter-bearing conditional
nominal-diameter route, count the entire transition as threaded material.
With a maximum-thickness head washer, the first reduced/transition section
must begin no earlier than the following distances from under the head:

| Connection | Nut-side wood thickness | Minimum full-body shank through transition |
| --- | ---: | ---: |
| Splice | 38.1 mm | **69.3166 mm** = 76.2 + 2.6416 − 38.1/4 |
| Rim endpoint | 38.1 mm | **120.1166 mm** = 127 + 2.6416 − 38.1/4 |
| Leg endpoint | 88.9 mm | **107.4166 mm** = 127 + 2.6416 − 88.9/4 |

Reversing the rim-end bolts places their threads in the thinner knee member,
so their required unthreaded length increases. The scheduled 6-inch bolt
remains usable only when its actual transition satisfies this tighter limit.
Check actual wood and washer dimensions when applying these thresholds.
Hardware that does not meet these conditions is outside the selected
nominal-diameter build basis; the reference-root sensitivity does not qualify an
unmeasured thread root.

The installation orientation is supplied by
`mini_moonboard/compact_spliced_installation.py`; the archived six-case native
model retains its original hardware orientation. Timber geometry, holes,
bolt diameters, grips and matched washer envelopes remain unchanged. Both
washer seats use the same conservative resistance inputs; reversing head and
nut does not change those comparisons. See the current build package for the
installation revision and its equivalence evidence. The
[current six-case assessment](compact-splice-study.md) checks this
minimum-dimension resistance envelope and passes every listed conditional
criterion. Catalog availability alone does not qualify delivered components.
