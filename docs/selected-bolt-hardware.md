# Selected through-bolt hardware: procurement/design basis

Research checked 2026-09-06. This specifies a reasonable physical hardware
family for the separate transition candidate, **not joint capacity, installation
torque, slip resistance, or permission to build**. No clamp-friction or plywood
glue/composite credit is taken. Ancestor variants retain their original geometry.

## Products and dimensional envelopes

Select 3/8-16 UNC ASTM A307 Grade A **standard hex bolts**, Conquest plain-finish
series, in the six catalog lengths below. These are not heavy-hex structural
bolts, lag screws, carriage bolts, or arbitrary Grade 2 substitutes. The
[manufacturer's bolt specification](https://www.fastenersplus.com/cdn/shop/files/CQ-Hex-Head-Bolts-Spec-Sheet.pdf?v=17509241941931126534)
identifies ASME B18.2.1 dimensions and plain external thread class 2A.

| Bolt feature | Published inches | Converted mm |
| --- | --- | --- |
| Nominal diameter / pitch | 3/8 / 1/16 | 9.525 / 1.5875 |
| Body diameter range | .360–.388 | 9.144–9.8552 |
| Head across flats | .544–.562 | 13.8176–14.2748 |
| Head across corners | .620–.650 | 15.748–16.510 |
| Head height | .226–.268 | 5.7404–6.8072 |
| Reference thread length, these lengths | 1.000 | 25.400 |

Use a **finished hex**, not heavy-hex or jam, 3/8-16 ASTM A563 Grade A nut:
[FMW zinc-plated finished nut](https://www.fmwfasteners.com/products/3-8-16-grade-2-finished-hex-nut-zinc-plated).
Its product text explicitly specifies A563 Grade A, despite the Grade 2 product
title. Published thickness is .320–.337 in (8.128–8.5598 mm), across flats
.551–.562 in (13.9954–14.2748 mm). The ASME-pattern across-corner range is
.628–.650 in (15.9512–16.510 mm), also listed in the
[Delta finished-nut chart](https://www.deltafastener.com/nuts-finished-hex.php).
Use a 9/16-in wrench/socket on the bolt and nut. Its actual outside tool diameter
must still pass the access model. Do not substitute hot-dip-galvanized oversize
tapped nuts. The FMW plain-nut page was not used for dimensional selection: it
contains a wrong-size description and apparently mislabels corner width as
thickness.

Use **two SAE-pattern carbon-steel flat washers per bolt**, one each under head
and nut: [CDE 3/8 SAE USA-made zinc washer](https://cdefasteners.com/order-online/s-a-e-flat-washer-usa-made-zinc/599192),
with its [linked SAE dimensional sheet](https://cdefasteners.com/sites/default/files/product-specs/washerssae.pdf).
The sheet identifies ASME B18.21.1-2009; it does not establish an ASTM F844
material certificate, so do not label this selected SKU F844-certified.

| Washer feature | Published inches | Converted mm |
| --- | --- | --- |
| OD nominal / limits | 13/16 / .805–.827 | 20.6375 / 20.447–21.0058 |
| ID nominal / limits | 13/32 / .401–.419 | 10.31875 / 10.1854–10.6426 |
| Thickness limits | .051–.080 | 1.2954–2.032 |
| Suggested nominal CAD thickness (assumption) | .065 | 1.651 |

This smaller washer fits within the earlier 25.4-mm OD envelope and avoids a
38.1-mm fender washer. That is only a clearance advantage: reduced wood-bearing
area, washer bending and crushing still need resistance checks. Use the maximum
OD for collision checks and a physical minimum bearing annulus, not a solid
disc covering the bolt hole. Plain bolt plus zinc-plated ordinary nut/washer is
the indoor procurement basis; supplier thread-fit and corrosion suitability must
be confirmed rather than inferring outdoor suitability.

## Existing candidate grip mapping

Read from `transition_frame.connections()`: 114 bolts, 114 nuts and 228 washers,
before spares. Length is measured **under the bolt head**, not including it.
The physical grip excludes both washers and the nut. These catalog selections
retain the existing nominal bolt lengths; geometry integration is separate.

| Physical grip mm | Connections / count | Conquest catalog length | Nominal projection mm | Conservative dimensional projection mm |
| --- | --- | --- | --- | --- |
| 38.1 | `leg_stitch_*`, 6 | [2-1/4 in / 57.15 mm](https://www.fastenersplus.com/products/3-8-16-x-2-1-4-conquest-a307-grade-a-hex-bolt-plain) | 7.1882 | 5.4102 |
| 44.1 | top-wall/top-beam and cross-wall angles 20; rib-angle beam sides 24; transition seam/top/kicker-bottom 12; total 56 | [2-1/2 in / 63.5 mm](https://www.fastenersplus.com/products/3-8-16-x-2-1-2-conquest-a307-grade-a-hex-bolt-plain) | 7.5382 | 5.7602 |
| 69.5 | `angle_rib_*_rib_*`, 24 | [3-1/2 in / 88.9 mm](https://www.fastenersplus.com/products/3-8-16-x-3-1-2-conquest-a307-grade-a-hex-bolt-plain) | 7.5382 | 5.2522 |
| 76.2 | `analysis_leg_wall_bolt_*`, 8 | [3-3/4 in / 95.25 mm](https://www.fastenersplus.com/products/3-8-16-x-3-3-4-conquest-a307-grade-a-hex-bolt-plain) | 7.1882 | 4.9022 |
| 82.2 | `transition_main_*_bolt_*` and `transition_kicker_*_bolt_*`, 8 | [4 in / 101.6 mm](https://www.fastenersplus.com/products/3-8-16-x-4-conquest-a307-grade-a-hex-bolt-plain) | 7.5382 | 5.2522 |
| 94.9 | `angle_{left,right}_cross_*_beam_*`, 12 | [4-1/2 in / 114.3 mm](https://www.fastenersplus.com/products/3-8-16-x-4-1-2-conquest-a307-grade-a-hex-bolt-plain) | 7.5382 | 4.2362 |

Computed projection is `length - grip - 2*washer_thickness - nut_height`.
Nominal values use 1.651-mm washers and the conservative 8.5598-mm maximum nut.
The conservative column uses 2.032-mm washers, maximum nut, and bolt underlength
of .04 in through 2.5 in, .06 in through 4 in, and .10 in above 4 through 6 in,
from the [manufacturer's ASME bolt-length tolerance table](https://www.portlandbolt.com/technical/faqs/bolt-length-tolerance/).
These are nominal wood grips: stock/grip tolerances are not silently included.

Require at least two thread pitches of geometric projection: **3.175 mm**.
All six dimensional stacks meet that at the stated nominal grip, but two
**complete** exposed threads are not guaranteed by tip projection alone: end
chamfer/runout consumes usable thread. Inspect the delivered end geometry and
actual stack for full nut engagement and two complete exposed threads. If it
fails, select the next catalog length and recheck projections/collisions; do not
remove washers or bury the nut to make the length work.

## Thread-bearing and CAD consequences

With 25.4 mm of reference thread, nominal unthreaded length is `L - 25.4`.
For these stacks approximately **7.65–8.00 mm of the nut-side physical grip is
threaded**, before runout/tolerances. Even these partially threaded bolts cannot
be credited as smooth shanks through every wood/steel bearing plane. Short/full
thread substitutions can increase that exposure. Model or conservatively assess
threaded bearing/shear explicitly; do not reuse full-diameter smooth-shank
resistance blindly. Nut must not bottom on the thread runout before seating.

The current generic `box_frame.Connection.components()` uses 2-mm washers,
9-mm-thick cylindrical nuts and 6-mm cylindrical heads. Selected-product CAD
must locate head/washer/grip/nut from one consistent bearing datum, rebuild
bores only where actually needed, and rerun seating, bolt-hole, socket, adjacent
hardware and floor checks using the tolerances above. The maximum 9.8552-mm bolt
body leaves only 0.1448 mm diametral clearance in a nominal 10-mm bore; hole
manufacturing/alignment allowance is a separate decision, not a proven fit.

No split lock washer, jam nut, threadlocker or torque value is implicitly
selected. Locking/inspection practice and wood-tightening limits remain an
explicit installation decision. None of these catalog selections changes the
failed/unqualified FEA evidence or establishes joint capacity.
