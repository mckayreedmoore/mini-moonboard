# Current ordinary hardware basis for the 48 WJ24 127 mm-grip axes

**Prepared:** 2026-09-24. **Status:** source-bound supplier screen and fit
gap. This note covers the 48 current candidate axes whose modeled length is
152.4 mm (6 in) and wood grip is 127 mm. It records potential catalog parts,
their packaging, and the facts needed to settle full-height nut engagement.
It selects no hardware, changes no CAD, and is not a purchase list, strength
check, machining instruction, or fabrication release.

## Scope and current model envelope

The axis identities come from the frozen
[attempt 02 grip-screen source](hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json),
SHA-256 `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`.
The [current hardware schedule](current-hardware-schedule.md) counts 92 WJ24
candidate axes overall; 48 have the 152.4 mm under-head-to-tip cylindrical
occupancy and a two-member, 127 mm wood grip. Each of these rows has one
modeled nut and two washer roles. The 6.35 mm CAD shaft is an unthreaded
analysis envelope. It does not encode a delivered bolt body, thread start,
thread end, or functional nut fit.

The dimensional screen below retains the previously documented 1/4-20
ordinary hardware envelope only for comparison. Each modeled wood member is
screened at ±0.5 mm as a planning allowance, and the washer and nut extrema
are taken from the cited standard dimensional ranges. The wood allowance is
not a stock acceptance tolerance. Coordinates are measured from the bolt's
under-head bearing plane.

| Stack quantity | Conservative screen value | Source or meaning |
| --- | ---: | --- |
| Head-side wood member | 88.9 ± 0.5 mm | Current frozen receiver interval |
| Nut-side wood member | 38.1 ± 0.5 mm | Current frozen receiver interval |
| Each 1/4-in Type A Wide washer | 1.2954–2.032 mm thick | ASME B18.21.1 Type A Wide dimensional envelope |
| Finished hex nut | 5.3848–5.7404 mm thick | ASME B18.2.2 finished-hex envelope |
| Earliest nut bearing face | 128.5908 mm | Min head washer + 126 mm wood + min nut washer |
| Farthest nut face | 137.8044 mm | Max head washer + 128 mm wood + max nut washer + max nut |
| Modeled bolt-tip target (not a thread endpoint) | 140.9794 mm | Farthest nut face + 3.175 mm inherited modeled tip projection |

The 3.175 mm projection is inherited from the WJ05 center-node model's
`THREAD_PAST_NUT_MM` constant and carried into WJ24 as a physical bolt-tip
envelope. The WJ05 source adds this value to `full_length` for an unthreaded
cylindrical shaft; WJ24's length screen preserves the allowance, and the
current WJ24 grip report describes its CAD shaft as an unthreaded occupancy
envelope. The value is 0.125 in, 2.5 pitches at 1/4-20, or 0.5 bolt diameter
(D = 6.35 mm). Neither source makes it a published minimum-engagement rule or
requires full-form thread through the extension beyond the nut. With no wood
allowance and the modeled 2.032 mm washer / 5.7404 mm nut stack, the nut spans
131.064–136.8044 mm and the corresponding modeled tip target is 139.9794 mm.

## Current supplier candidates and package quantities

Stripe Directory was attempted before supplier-page search; it returned no
matching listing. The installed CLI did not expose the Directory command, so
the documented public-source fallback was used. Pages were checked
2026-09-24. No vendor was contacted and no purchase was made.

Würth Canada lists a concrete 6 in bolt candidate, matching nut, and USS
washer. Product quantities and dimensions below are catalog facts, not a
selected or received set. The bolt thread data conflicts across Würth's own
public sources; therefore the 6 in bolt is **not cleared for the modeled nut
stack**.

| Role for these 48 axes | Würth catalog reference | Published fit details | Package quantity for this scope | Status |
| --- | --- | --- | ---: | --- |
| Bolt | [072.14.6, 1/4-20 × 6 in standard hex bolt](https://shop.wurth.ca/fasteners/bolts/hex-bolts-assortments/standard-hex-bolts/1-4-20X6-UNC-HEX-BOLT-GR5-ZN/072.14.6/) | The product page says Grade 5, clear zinc, partial thread, 7/16 in across flats, 5/32 in head height, and “thread length 1 in.” Würth's [master catalogue](https://assets.wurth.ca/wca/master-catalogue/en/FASTENERS.pdf) maps 072.14.6 to 1/4 in UNC Grade 5 clear-zinc, 6 in, pack 25. | 2 packs = 50; 2 spare | **Thread-length conflict; unresolved.** The same master catalogue's standard-bolt dimension table gives thread length `b = 0.750 in` for 1/4 in diameter at lengths `≤ 6 in`, and 1.000 in only for lengths `> 6 in`. It does not provide an item drawing that reconciles this with the product page's 1 in value. Do not assume either value is a minimum full-form-thread dimension. |
| Nut | [330.14, 1/4-20 UNC Grade 5 hex nut](https://shop.wurth.ca/fasteners/nuts/hexagon-nuts-assortments/standard-hex-nuts/1-4-20-UNC-HEX-NUT-GR5-ZN/330.14/) | Grade 5, clear zinc, 7/16 in across flats, 0.505 in across corners, 7/32 in thickness. The master catalogue lists the 1/4 UNC Grade 5 clear-zinc nut. | 1 pack = 200; 152 spare | Dimensional/material candidate only. The page does not state its internal thread class or functional fit with the bolt lot. |
| Two washers per axis | [408.14, 1/4 × 3/4 × 1/16 in USS Grade 5 clear-zinc flat washer](https://shop.wurth.ca/fasteners/washers/flat-washers/standard-uss-washers/1-4X3-4X1-16-USS-FLAT-WASHER-GR5-ZN/408.14/) | Product page states 3/4 in OD, 1/16 in thickness, steel, Grade 5, clear zinc. Würth's [USS washer size chart](https://pim.wurth.ca/Technical/USS%20WASHER%20SIZE%20CHART.pdf) lists the 1/4 washer ID as 0.312 in +0.015/−0.005, OD 0.734 in +0.015/−0.007, and thickness 0.051–0.080 in. | 1 pack = 100; 4 spare | Published dimensional envelope matches the cited 1/4 in Type A Wide dimensional range. It does not establish bearing support or washer resistance for WJ24 actions. |

Würth pages showed “in stock delivery” and package sizes when accessed;
displayed account-dependent amounts were not used as prices because the page
did not provide a stable currency/price basis. Current availability outside
the displayed Canadian channels, shipment, tax, and delivered-part conformity
remain unverified. No total cost is assigned.

## What the ASME thread dimensions establish

ASME B18.2.1-2012 defines body length `LB` as the under-head distance to the
last thread scratch (or the top of the extrusion angle for rolled threads);
minimum `LB` is an inspection criterion. It defines grip-gaging length `LG`
as the under-head distance to the face of the applicable GO thread ring gage
assembled by hand as far as the thread permits; maximum `LG` is an inspection
criterion. The standard says thread length is controlled by both `LG,max`
and `LB,min`. For dimensions not in Table 12, `LT` is a reference dimension
from the extreme end to the last complete (full-form) thread, used for
calculation; it is not a delivered tolerance. Thus `LG` is a gage criterion,
not a direct drawing coordinate for the first full-form thread, and `LB` is
not a direct full-form-thread start or end dimension.

The 1/4-in long-screw row in Table 12 gives these pairs:

| Nominal length | Minimum overall length | `LG,max` | `LB,min` | Dimensional implication |
| ---: | ---: | ---: | ---: | --- |
| 5.75 in / 146.05 mm | 5.65 in / 143.51 mm | 5.00 in / 127.00 mm | 4.75 in / 120.65 mm | Promising gage-class option: the `LG,max` coordinate is 1.5908 mm smaller than the conservative earliest nut-face coordinate. The body criterion also narrowly meets the separate threaded-bearing screen described below. These table limits do not report the exact first full-form thread on a delivered item. No exact supplier SKU is verified. |
| 6.00 in / 152.40 mm | 5.90 in / 149.86 mm | 5.25 in / 133.35 mm | 5.00 in / 127.00 mm | Leaves ample total length, but the standard gage maximum is 4.7592 mm beyond the conservative earliest nut face. The standard/catalog data do not establish full-height nut engagement for this stack. It does not establish that an individual delivered part will fail; actual gaging/transition can be more favorable. |

For a separate member-specific threaded-bearing screen with no more than
one-quarter of the 38.1 ±0.5 mm nut-side member threaded, the conservative
body-end coordinate is
`2.032 + 89.4 + 0.75 × 38.6 = 120.382 mm`. The 5.75 in table `LB,min` of
120.65 mm exceeds that screen by 0.268 mm. This is a narrow dimensional
margin, not a strength result. The current 6 in table `LB,min` is 127 mm.

The 5.75 in class therefore has a cleaner standard gage envelope for this
stack while retaining enough overall length in the stated screen. No exact
1/4-20 Grade 5 catalog item was verified at 5.75 in. Brighton Best's primary
[Grade 5 hex-cap-screw catalogue](https://www.brightonbest.com/download/catalogs/usa/BBI_USA_G5.pdf)
lists the 1/4-20 Grade 5 zinc CR+3 sizes at 5.5 in (847033) and 6 in
(847034), without a 5.75 in entry. The 5.75 in 847170 entry belongs to the
3/8-16 size group, not 1/4-20. Standard dimensions alone do not imply that a
given length is a stock item.

The K.L. Jack [25C600HCS5Z product page](https://www.kljack.com/products/25c600hcs5z/)
also lists a 1/4-20 × 6 in Grade 5 zinc cap screw and “thread length 3/4 in.”
That matches the nominal `LT = 2D + 0.25 in = 0.75 in` reference for a 1/4 in
screw up to and including 6 in; the standard explicitly calls `LT` a
calculation reference, not a tolerance. K.L. Jack does not publish the exact
thread-transition limits or an actual first-full-thread coordinate on that
page. It therefore does not resolve the current nut-face fit.

## Minimal evidence needed to settle the 6 in fit

For the existing 6 in geometry, an applicable manufacturer drawing/spec or
matched, recorded dimensional check must establish all of the following for
the same bolt/nut lot:

1. Bolt identity and material/finish: 1/4-20 UNC, external thread class,
   Grade 5 evidence, clear-zinc finish, and actual under-head length. For the
   ASME 6 in nominal class the length tolerance gives a 149.86 mm lower bound;
   use the received value for the actual stack.
2. Thread availability at the conservative stack limits: the matched 1/4-20
   nut engages functionally through its full thread height and seats against
   its washer without point/runout interference. Its outer face is no farther
   than 137.8044 mm in this stack. The 140.9794 mm coordinate is the inherited
   modeled bolt-tip target (3.175 mm beyond that face), not a requirement for
   full-form thread through the tail. A product-specific thread envelope may
   establish the actual head-side start, body/thread transition, and thread
   availability at the nut; an `LT` reference or `LG` label alone is not a
   substitute for delivered fit evidence.
3. The measured last-scratch/body boundary is at or beyond 120.382 mm. Record
   the matched nut's internal class/standard and the engagement-check method.
4. Washer identity and actual ID/OD/thickness, plus the supported wood
   footprint and any washer resistance needed by the mechanics check. The
   408.14 dimensions are candidate dimensions only.

The public Würth evidence currently conflicts on the bolt's thread length,
and neither its page nor the general catalogue publishes a bounded
full-form-thread start and end for the exact item. That specific evidence gap
keeps 072.14.6 provisional. If a verified 5.75 in 1/4-20 Grade 5 product is
found, screen its exact dimensions against this stack and re-evaluate the
current 152.4 mm modeled-shaft geometry before using it as an input. No CAD
edit, hardware choice, contact with a vendor, purchase, native solve, or
physical operation is authorized by this note.

## Source trail

- [WJ05 center-node probe](../../scripts/wood_joint_wj05_center_node_probe.py) (`THREAD_PAST_NUT_MM` and `_fastener_shapes`) and [WJ24 bolt-length screen](wj24-bolt-length-screen.md) establish the 3.175 mm inherited tip-envelope input, not a full-form-thread extension requirement; [current WJ24 grip screen](current-grip-screen.md) identifies the shaft as an unthreaded occupancy envelope.
- [ASME B18.2.1 standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws); ASME lists B18.2.1-2012 (R2021) as the version in effect. Local cached text was checked against that edition. Tables 12 and 13; §§1.3, 4.7, and 4.8.
- [ASME B18.2.1 partial-thread dimension table](https://www.nickel-systems.com/products/bolts-screws/hex-head-cap/) and [table PDF](https://www.nickel-systems.com/wp-content/uploads/2025/01/Hex-Head-Cap-Screws-Partially-Threaded-Minimum-Body-Maximum-Grip-Gaging-Lengths-1.pdf).
- [ASME B18.2.2 finished-hex nut dimensions](https://www.nickel-systems.com/products/nuts/finished-hex/).
- [Fastenal Type A Wide washer dimension sheet](https://www.fastenal.com/content/product_specifications/FW.LC.USS.A.P.00.pdf).
- Würth Canada pages and master-catalogue PDFs linked in the table above; accessed 2026-09-24.
- The previous [ordinary-hardware dimensional basis](ordinary-hardware-basis.md) supplies the candidate hardware envelopes, not a selected WJ24 SKU or delivered part.

## Bounded follow-up on a longer-thread 6 in item (2026-09-24)

The Stripe Directory route was tried before public supplier lookup using the
isolated current CLI/plugin. Focused searches for `fastener supplier grade 5
bolt` and `industrial hardware fasteners bolts` returned no listings; the
Directory command documents its results as MPP/provisioning providers rather
than a product catalogue. The public-source fallback was therefore used.
No account credentials or settings were changed.

No defensible 1/4-20, 6 in, partially threaded Grade 5 product drawing was
found that bounds the complete-thread start and body/thread transition for
this stack. The primary/supplier evidence located supports the conventional
pattern or leaves the exact part unbounded:

| Source | What it establishes | Why it does not close this fit |
| --- | --- | --- |
| [CDE Fasteners Grade 5/8 technical sheet](https://cdefasteners.com/sites/default/files/product-specs/capscrewgr5-8.pdf) | The 1/4 in row gives `LT = 0.750 in` as a reference for screws `≤ 6 in`, `LT = 1.000 in` for screws `> 6 in`, and maximum transition `Y = 0.250 in`; it is an ASME B18.2.1 dimensional table. | This is the standard size pattern, not an item-specific drawing or minimum/maximum complete-thread coordinates for a longer-thread 6 in SKU. `LT` is explicitly reference data. |
| [Allied Bolt item 50140](https://alliedboltinc.com/product/1/4-inch-X-6-inch-HEX-CAP-SCREW-GR-5-ZINC-PLATED~50140) | Exact 1/4-20 × 6 in, zinc-plated Grade 5 item; the page states SAE J429 Grade 5 / ASME B18.2.1 and lists 3/4 in thread length. | It matches the ordinary .750 in pattern and publishes no product drawing or thread-transition tolerance. |
| [Würth 072.14.6 product page](https://shop.wurth.ca/fasteners/bolts/hex-bolts-assortments/standard-hex-bolts/1-4-20X6-UNC-HEX-BOLT-GR5-ZN/072.14.6/) and [Würth master catalogue](https://assets.wurth.ca/wca/master-catalogue/en/FASTENERS.pdf) | The item page says 1 in thread length; the catalogue identifies the 6 in Grade 5 bolt and gives the standard-bolt table's 1/4 in thread length `b = 0.750 in` at lengths `≤ 6 in`. | These Würth sources conflict, and neither gives an item drawing or defines a bounded complete-thread-start / last-scratch envelope for 072.14.6. Treat 1 in as an unresolved page/catalogue conflict, not a verified longer-thread construction. |
| [Barnhill Bolt Grade 5 cap-screw length table](https://portal.distone.com/BARNHILLBOLTAPI/Content/PDF/50142510PRODUCTINFO.pdf) | The 1/4 in, 6 in row reports 5.25/5.00 in maximum-grip/minimum-body values and says the table represents standard ASME B18.2.1 cap screws. | It is a generic standard table and expressly distinguishes cap screws from hex bolts; it does not document an altered-thread product. |
| [LH Dottie MB146 product specification](https://lhdottie.com/pdf/product-specification-sheet/MB146) | Exact 1/4-20 × 6 in tap-bolt offering, package 100. | It is Grade A low-carbon steel and fully threaded, so it is not a partially threaded Grade 5 candidate. |

For the existing dimensional screen, the exact product evidence still needed
is a drawing or matched inspection that establishes functional full-height
engagement of the actual nut, leaves the last-scratch/body boundary at or
beyond 120.382 mm, and confirms the physical tip reaches the modeled 140.9794
mm target. If a geometric thread-location bound is used, it must also establish
that usable thread begins early enough for the nut to engage; thread need not
continue through the 3.175 mm modeled tail beyond the nut. These checks answer
separate questions: nut fit, wood-side thread intrusion, and physical tip
envelope. A bare nominal `thread length`, `LT` reference, `LG` gage limit, or
catalogue standard dimension does not supply delivered-part fit evidence.
The 6 in sourcing gap remains open because the head-side `LG,max` coordinate
still extends 4.7592 mm beyond the conservative earliest nut face and the
actual matched nut fit is unverified; no product is accepted and no CAD or
stack change is proposed.
