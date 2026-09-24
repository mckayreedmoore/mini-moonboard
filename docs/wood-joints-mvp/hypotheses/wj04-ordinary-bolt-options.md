# WJ-04 ordinary-bolt option screen

Status: hardware geometry hypothesis only. This screen is for a new WJ-04
full-stock stack with a nominal 127 mm wood grip (88.9 mm cleat plus 38.1 mm
host), one washer under the head, one washer under the nut, and a standard
1/4-20 nut. It does not select hardware, establish capacity, or change the
original twelve frame-bolt basis.

## Standard boundaries

ASME B18.2.1-2012 (R2021) treats ordinary hex bolts in §3.7/Table 2 and hex
cap screws separately in §4.7 and the screw tables. The ordinary-bolt nominal
thread length `LT` is a calculation reference: `2D + 0.25 in` through 6 in
nominal length, then `2D + 0.50 in` over 6 in. For a 1/4-in bolt at 5.5 or 6
in, that is `LT = 0.75 in`. The standard controls the ordinary bolt's grip
gage dimension `LG`; `LG` is an inspection gage plane, not a stated first
full-form-thread coordinate. Do not convert `L − LT` or `LG` into a guaranteed
thread transition for this joint. The current edition is identified on the
[ASME B18.2.1 page](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws).

Hex-cap-screw `LB`/`LG` limits are a separate product-class basis; do not
transfer cap-screw Table 12 body limits to an ordinary hex bolt or the reverse.
For cap screws, `LB` locates the last thread scratch (or rolled-thread
extrusion limit), not the start of full-form threads. The existing K.L. Jack
6-in cap screw `25C600HCS5Z` is listed with 3/4-in thread length, while Würth's
ordinary hex-bolt SKU below is listed with 1-in thread length. Those are
different product-class/catalog entries, not interchangeable standard
guarantees ([K.L. Jack cap-screw listing](https://www.kljack.com/products/25c600hcs5z/),
[Würth bolt listing](https://shop.wurth.ca/fasteners/bolts/hex-bolts-assortments/standard-hex-bolts/1-4-20X6-UNC-HEX-BOLT-GR5-ZN/072.14.6/)).

For NDS lateral-yield calculations, ANSI/AWC NDS-2024 §§12.3.7.1–12.3.7.2
use thread-root diameter `Dr` for threaded fasteners by default. Full-body
diameter `D` is permitted for a threaded full-body bolt only if threaded
bearing is no more than one quarter of the total bearing length in each member
holding threads. A more detailed analysis of threaded bending/bearing is also
permitted. Therefore exceeding the one-quarter condition is not by itself a
geometry rejection: use `Dr` or provide the detailed analysis. This diameter
rule applies to NDS lateral-yield calculations, not bolt tension or shear
areas. See the official [AWC NDS-2024 Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
the [AWC 2024 NDS record](https://awc.org/resources/2024-nds/), and the
repository's [bolt resistance basis](../bolt-resistance-basis.md).

## Stack bounds and catalog leads

The stack screen uses ±0.5 mm on each wood layer, washer thickness 1.2954–2.032
mm, and nut height 5.3848–5.7404 mm. Measured from the under-head bearing
plane, these give:

- earliest nut bearing face: `126 + 2(1.2954) = 128.5908 mm`;
- farthest nut face: `128 + 2(2.032) + 5.7404 = 137.8044 mm`;
- with the chosen 2.54 mm full-form-thread projection reserve: `140.3444 mm`.

The projection reserve is a project criterion, separate from full nut
engagement. The cited NDS and B18.2.1 provisions do not set this exact 2.54 mm
reserve. Full-height nut engagement still requires usable full-form threads
through the farthest nut face.

| Candidate | Source-backed catalog data | Screen result |
| --- | --- | --- |
| 1/4-20 × 5.5 in ordinary Grade 5 hex bolt, Bolt Depot #337 | Length tolerance +0/−0.10 in; minimum thread length 0.75 in; ASME B18.2.1 and SAE J429 listed ([item page](https://boltdepot.com/Product-Details?product=337)). | Minimum overall length is 137.16 mm, 0.6444 mm short of the farthest nut face, before the separate projection reserve. At nominal length, projection beyond that far face is only 1.8956 mm. It cannot guarantee this worst-case stack. Its minimum thread length does not locate the first full-form thread. |
| 1/4-20 × 6 in ordinary Grade 5 hex bolt, Würth SKU 072.14.6 | Supplier lists partial thread and 1-in thread length, but no tolerance or minimum first-full-form-thread location ([item page](https://shop.wurth.ca/fasteners/bolts/hex-bolts-assortments/standard-hex-bolts/1-4-20X6-UNC-HEX-BOLT-GR5-ZN/072.14.6/)). | Conditional catalog lead only. It may provide a longer threaded portion than the selected 6-in cap screw, but its listing alone does not show that full-form thread begins early enough for the whole nut. No fit pass is established. |

For illustration only, treating ordinary-bolt `LT = 0.75 in` as if it located
the first full-form thread on a nominal 5.5-in bolt gives `5.5 − 0.75 = 4.75
in = 120.65 mm`. With the tip host spanning 91.432–130.032 mm in the stated
worst-thickness stack, that hypothetical transition would imply 9.382 mm of
threaded bearing in the 38.6-mm tip member. It is not a delivered thread
measurement or an eligibility result: `LT` is a reference, not the transition
coordinate. The 9.65-mm `D` exception limit (`38.6/4`) therefore cannot be
claimed from that arithmetic. With the actual transition unknown, use `Dr`
for NDS lateral-yield work until actual bearing lengths establish otherwise.

## Required evidence before a fit claim

For either ordinary-bolt lead, record delivered length and verify that the
first complete thread is no farther from the under-head bearing plane than
128.5908 mm, and that complete threads continue through at least 137.8044 mm
so the full-height nut can engage. If retaining the separate 2.54 mm reserve,
complete threads must continue through 140.3444 mm. Apply the applicable bolt
length tolerance when checking these positions; nominal length and nominal
thread-length tables alone do not establish them. If the transition is not
measured or otherwise guaranteed, keep `Dr` as the NDS lateral-yield
diameter. No delivered sample or fit result is recorded here.
