# WJ-04 ordinary fastener dimensional basis

**Status: source-bound development candidate.** This note defines one
ordinary through-bolt hardware envelope for the current WJ-04 diagnostic
member thicknesses. It does not select a joint, establish a capacity, release
stock or machining, or prove installation and removal access. The candidate
geometry remains 95.25 × 38.1 × 119.7 mm; the proposed 100 × 53.34 mm section
has no matching WJ-04 CAD or mechanics result.

## Preferred catalog candidate

Use the same ordinary 1/4-20 hardware family at both WJ-04 interfaces, with
length selected by actual wood grip:

| Interface | Candidate bolt | Nominal grip | Standard minimum body `Lb` | Standard maximum grip gage `Lg` | Delivered length lower bound |
| --- | --- | ---: | ---: | ---: | ---: |
| Rail to cleat | K.L. Jack `25C375HCS5Z`, 3-3/4 in (95.25 mm), Grade 5, zinc plated, partially threaded | 38.1 + 38.1 = 76.2 mm | 2.75 in (69.85 mm) | 3.00 in (76.2 mm) | 3.69 in (93.726 mm) |
| Principal to cleat | K.L. Jack `25C600HCS5Z`, 6 in (152.4 mm), Grade 5, zinc plated, partially threaded | 95.25 + 38.1 = 133.35 mm | 5.00 in (127 mm) | 5.25 in (133.35 mm) | 5.90 in (149.86 mm) |

The product catalog identifies these as Grade 5 zinc-plated 1/4-20 hex cap
screws to SAE J429 and ASME B18.2.1. K.L. Jack lists each as partially
threaded and gives nominal lengths. The ASME B18.2.1 dimensional table
published by Nickel Systems supplies the `Lb` and `Lg` bounds. Its length
tolerance table gives −0.06/+0.00 in for the 3-3/4 in screw and
−0.10/+0.00 in for the 6 in screw. These are catalog and standard bounds,
not inspection results for delivered fasteners.

K.L. Jack's published 1/4-in hex-cap-screw dimensions give body diameter
0.245–0.250 in (6.223–6.35 mm), head across-flats 0.428–0.438 in
(10.8712–11.1252 mm), across-corners 0.488–0.505 in (12.3952–12.827 mm), and
head height 0.150–0.163 in (3.81–4.1402 mm). The basic wrench size is 7/16 in.
The source table is the manufacturer's [fastener technical data
catalog](https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf).
These are published product-family limits; verify received heads and wrench
fit. Its `LT` basic thread length is a reference value, not a tolerance on
tip-end thread runout. The active CAD collision envelope uses the published
maximum head dimensions. That envelope does not prove received parts conform;
measure the received bolt heads and confirm wrench fit.

Use one K.L. Jack `25CNFH5Z` Grade 5 zinc-plated 1/4-20 finished hex nut and
two 1/4-in plain USS Type A Wide low-carbon steel washers at each bolt. The
washer dimensional basis is Fastenal's published Type A Wide specification;
an exact washer seller SKU is not yet selected. Stack order: bolt head,
head-side washer, first wood layer, second wood layer, nut-side washer, hex
nut. K.L. Jack specifies the nut to SAE J995 and ASME B18.2.2. The nickel
supplier's B18.2.2 table gives 0.212–0.226 in
(5.3848–5.7404 mm) nut thickness, 0.428–0.438 in (10.8712–11.1252 mm)
across flats, and up to 0.505 in (12.827 mm) across corners. The washer is
specified to ASME B18.21.1 Type A Wide. Its listed bounds are:

| Feature | Inch bound | Metric bound |
| --- | ---: | ---: |
| Inside diameter | 0.307–0.327 in | 7.7978–8.3058 mm |
| Outside diameter | 0.727–0.749 in | 18.4658–19.0246 mm |
| Thickness | 0.051–0.080 in | 1.2954–2.032 mm |

Product, standard, and dimensional sources:

- [K.L. Jack 25C375HCS5Z](https://www.kljack.com/products/25c375hcs5z/)
- [K.L. Jack 25C600HCS5Z](https://www.kljack.com/products/25c600hcs5z/)
- [K.L. Jack 25CNFH5Z](https://www.kljack.com/products/25cnfh5z/)
- [ASME B18.2.1 bolt dimensions, length tolerances, and partial-thread `Lb`/`Lg` table](https://www.nickel-systems.com/products/bolts-screws/hex-head-cap/)
- [B18.2.1 partial-thread dimensions by nominal length](https://www.nickel-systems.com/wp-content/uploads/2025/01/Hex-Head-Cap-Screws-Partially-Threaded-Minimum-Body-Maximum-Grip-Gaging-Lengths-1.pdf)
- [ASME B18.2.2 finished-hex-nut dimensions](https://www.nickel-systems.com/products/nuts/finished-hex/)
- [Fastenal Type A Wide plain USS washer dimensional standard](https://www.fastenal.com/content/product_specifications/FW.LC.USS.A.P.00.pdf)
- [ASME B18.2.1-2012 (R2021) standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
- [ASME B18.2.2-2022 standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts)

## Dimensional screen

This comparison treats each nominal wood layer as ±0.5 mm and independently
combines that assumption with the catalog washer and nut extrema. The
±0.5 mm wood allowance is a screen input, not a purchase tolerance or stock
acceptance. Coordinates start at the bolt's under-head bearing plane.

| Result | Rail stack | Principal stack |
| --- | ---: | ---: |
| Min body end needed to keep each member's threaded-bearing portion at or below 1/4 | 69.582 mm | 126.732 mm |
| Published `Lb` minimum | 69.85 mm | 127 mm |
| Remaining body-end margin | 0.268 mm | 0.268 mm |
| Earliest nut bearing face | 77.7908 mm | 134.9408 mm |
| Published latest thread-start bound (`Lg`) | 76.2 mm | 133.35 mm |
| Thread-start location margin to earliest nut face | 1.5908 mm | 1.5908 mm |
| Farthest nut face, with two maximum-thickness washers | 87.0044 mm | 144.1544 mm |
| Minimum delivered bolt length | 93.726 mm | 149.86 mm |
| Tip projection at maximum stack/minimum length | 6.7216 mm | 5.7056 mm |
| Remaining projection after 2.54 mm receiving reserve | 4.1816 mm | 3.1656 mm |

The body check allows the small threaded-bearing fraction on the outer member;
it does not impose smooth shank through all wood. At the standard minimum body
length, the modeled threaded-bearing fractions are 0% / 24.3057% across the
head-side / nut-side members in both stacks. The screen applies the NDS
12.3.7.2 member-specific 1/4 condition; this only screens when full diameter
may be used in a lateral-resistance method. It does not establish resistance.
The actual bearing treatment and resistance must still be checked for each
member. These positive dimensional margins are narrow and do not include
stock variation beyond the stated ±0.5 mm input, washer flatness, hole
angularity, seating, coatings, or bolt straightness.

- [AWC 2024 NDS, Chapter 12 dowel-type fasteners](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
- [AWC 2024 NDS edition information](https://awc.org/resources/2024-nds/)

`Lb` is the minimum body length to the last thread scratch; `Lg` is the maximum
grip-gaging length used to bound the thread start. These standard bounds support
the partial-thread geometric screen. Neither specifies the delivered transition
or end-chamfer geometry. The cited products and standards do not guarantee
full-form thread through the far nut face. Receiving inspection must measure
each delivered bolt lot and verify the matched nut. Require measured bolt
length within the published range (3.69–3.75 in rail, 5.90–6.00 in principal),
body end no shorter than `Lb`, body end no later than the first full-form
thread, first full-form thread no later than the earliest nut bearing face
above, full-form thread continuing at least 2.54 mm beyond the farthest nut
face, and that measured thread end not beyond the measured bolt tip. Verify
functional full-height nut engagement. Tip length alone does not prove usable
threads; the catalog does not promise that end-thread condition.

## Tool candidate and unresolved motion

Preferred access candidate: a pair of FACOM `34.7/16` double-open-end midget
wrenches, one to turn the nut and one to counter-hold the bolt head. FACOM's
official table lists the 7/16 in end, 22 mm head width, 3 mm head thickness,
100 mm overall length, and 15°/75° head offsets. It avoids a socket bore and
ratchet tang over the protruding stud. FACOM publishes no dimensional
tolerance for these values.

- [FACOM 34 inch midget open-end wrench catalog](https://www.facom.fr/products/34-cles-a-fourches-micromecanique-tetes-inclinees-en-pouces)

This selects a real ordinary tool candidate; it does **not** establish the
two-wrench installation pose, regrip angle, handle sweep, hand path, required
turning effort, tool-to-service clearance, or nut-removal route. The tool
access screen must model the actual open jaws and handles in the assembly and
removal sequence. No tightening torque, clamp force, preload, calibrated torque
tool, or accepted tightening procedure is specified. A generic 40 or 50 mm
cylinder is not the selected tool and does not decide bolt length.

## Disposition

Carry `25C375HCS5Z` rail bolts, `25C600HCS5Z` principal bolts, `25CNFH5Z`
nuts, and two 1/4-in Type A Wide washers per bolt as the preferred
**dimensional candidate** for the current 95.25 × 38.1 mm cleat. A preferred
washer seller SKU and delivered lot remain to be selected and received. If a
listed bolt or dimensional condition cannot be obtained or verified, stop and
rescreen; no fallback bolt is selected here. Keep product values separate
from the generic CAD occupancy envelope and actual receipt measurements. No
fastener resistance, wood capacity, clamp force, preload, torque, wrench
clearance, joint acceptance, drilling, or build release follows from this
note.

The calculations are produced from the shared actual member layers and
candidate hardware data in [`WJ04_TRIAL`](../../mini_moonboard/wood_joint_wj04_config.py)
by the [stack screen](../../scripts/wj04_fastener_stack_method.py).
