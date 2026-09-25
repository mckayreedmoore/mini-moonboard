# Sourcing follow-up: conditional 1/4-20 hardware for the 48 ordinary axes

**Prepared:** 2026-09-25. **Status:** a named US-catalogue candidate is
documented; matched-nut fit remains unresolved. This follow-up applies to the
48 WJ24 ordinary axes with 127 mm modeled wood grip and 152.4 mm nominal
under-head-to-tip envelope. It makes no hardware selection, CAD change,
strength finding, purchase list, or fabrication release.

The starting geometry and remaining no-spacer gap are in the
[current ordinary-hardware basis](current-ordinary-hardware-basis.md). The
[separate spacer option](current-ordinary-hardware-spacer-option.md) retains
the wood grip and bolt axis, but moves each nut stack outboard; that option is
not adopted here.

## Named conditional supplier scenario

K.L. Jack's current US-facing catalogue lists a matching pair of 1/4-20
fasteners. Its site lists US branch locations and online ordering. The product
pages showed package prices and add-to-cart controls on 2026-09-25, but no
part-specific stock count or delivery date. K.L. Jack's FAQ says it does not
generally post availability dates for out-of-stock items. The listing is
therefore a US supplier lead, not confirmation of stock or delivery.

| Role | K.L. Jack catalogue item | Published class and specifications | Quantity for 48 axes | Page display checked 2026-09-25 |
| --- | --- | --- | ---: | --- |
| Bolt | [25C600HCS5Z, supplier P/N 09487](https://www.kljack.com/products/25c600hcs5z/) | 1/4-20 × 6 in, zinc-plated Grade 5 hex cap screw; partial thread; ASME B18.2.1; SAE J429; external UNC Class 2A under ASME B1.1; 20 TPI; 7/16 in hex; 0.150–0.163 in head height. Product page lists “Thread Length 3/4 in.” | 48 required; 1 package of 100; 52 remaining | $82.14 per 100-piece box; page did not report lot stock or a delivery date. |
| Nut | [25CNFH5Z, supplier P/N AFH5Z0250C](https://www.kljack.com/products/25cnfh5z/) | 1/4-20 zinc-plated Grade 5 finished hex nut; ASME B18.2.2; SAE J995 Grade 5; internal UNC Class 2B under ASME B1.1; 20 TPI; 7/16 in hex; 7/32 in nominal thickness. | 48 required; 1 package of 100; 52 remaining | $4.71 per 100-piece box; page did not report lot stock or a delivery date. |

The listed bolt and nut specify complementary 2A external / 2B internal
thread classes. That identifies the intended standardized thread fit; it does
not establish how far usable full-form thread extends axially on an individual
bolt, whether a particular lot's bolt and nut pass together through the full
nut height, or any WJ24 resistance. The product pages do not provide an
item-specific drawing bounding the bolt's transition and point/runout
relative to the nut. Keep the two Type A Wide washers per axis from the
separate hardware basis as a distinct, unresolved washer specification.

The Stripe Directory route was tried on 2026-09-24 before public catalogue
lookup; the [existing basis note](current-ordinary-hardware-basis.md#bounded-follow-up-on-a-longer-thread-6-in-item-2026-09-24)
records that the CLI searches returned no relevant vendor listing and that
the Directory results did not function as a fastener product catalogue. This
follow-up reuses that route result. No vendor was contacted, no checkout was
started, and no purchase was made.

## Thread and length interpretation

The K.L. Jack product page's “3/4 in thread length” is the only item-specific
axial thread value located for this candidate. The separate K.L. Jack
[technical data and charts](https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf)
identify the 1/4 in cap-screw `LT` as 0.750 in through 6 in and expressly
define basic `LT` as a reference distance for calculation, from the extreme
end to the last complete thread. A reference value is not an item-specific
minimum or maximum coordinate for the full-form thread start, body transition,
or thread/runout end. The catalog's “3/4 in” field must not be treated as a
guarantee of full-height nut engagement.

For a 1/4 in × 6 in cap screw conforming to ASME B18.2.1-2012 (R2021), the
existing dimensional screen uses these standard bounds:

| Bound | Value | Application here |
| --- | ---: | --- |
| Minimum overall length | 5.90 in / 149.86 mm | Measured from under-head bearing plane to extreme point. |
| `LG,max` | 5.25 in / 133.35 mm | Standard grip-gaging limit; not the actual first full-form-thread coordinate. |
| `LB,min` | 5.00 in / 127.00 mm | Standard body/last-thread-scratch limit; not the actual full-form-thread start or end. |
| WJ24 minimum body coordinate for the later nominal-diameter bearing screen | 120.382 mm | `2.032 + 89.4 + 0.75 × 38.6`; the `LB,min` value is 6.618 mm farther outboard if the bolt conforms to the standard. |

The exact basis definitions and limits are recorded in the
[current ordinary-hardware basis](current-ordinary-hardware-basis.md#what-the-asme-thread-dimensions-establish)
and [spacer option](current-ordinary-hardware-spacer-option.md#asme-point-and-thread-end-limit-review).
ASME B18.2.1 defines general bolt dimensions and gaging; ASME B1.1 defines
the thread form, series, class, allowance, and tolerances. The current ASME
records list B18.2.1-2012 (R2021), B18.2.2-2022, and B1.1-2024 as the
applicable current editions when checked.

## Check against the existing unspaced 48-axis stack

For the current modeled stack, the conservative earliest nut bearing plane is
128.5908 mm from the bolt's under-head bearing plane. The maximum far-nut face
is 137.8044 mm and the inherited modeled bolt-tip target is 140.9794 mm. The
standard `LG,max` coordinate, 133.35 mm, is 4.7592 mm beyond the earliest
nut-bearing plane. Meanwhile, the minimum standard overall length of
149.86 mm exceeds the modeled tip target by 8.8806 mm.

Those figures separate axial length from thread availability. Overall length
is ample in the screen, and the standard `LB,min` exceeds the WJ24
body/last-scratch screen. The published limits and K.L. Jack page do not,
however, guarantee that full-form thread begins by the earliest nut bearing
plane or continues through the matched nut's full functional thread height.
The product's “3/4 in” catalog field matches the standard's 0.750 in `LT`
reference, but neither gives the required delivered thread coordinates. The
existing unspaced geometry may be satisfied by an actual bolt whose usable
thread region and matched nut fit meet the stack; the available evidence does
not establish that it will. Do not treat this candidate as a fit pass or a
standard-guaranteed failure.

For a drawing or later receiving evidence to close the unspaced fit, it must
establish full functional thread engagement for the actual matched bolt/nut
pair across the relevant stacks, and show that the nut seats against its
washer without unthreaded shank, incomplete thread, point, or runout
interfering. The overlap check should use the nut's functional internal-thread
interval, with any entry/exit chamfers excluded according to item-specific
dimensions or measurement. A matched-piece check can assess each actual stack.

For a single drawing intended to cover all 48 stack limits, a conservative
sufficient bound is for the external full-form thread region to start at or
before the 128.5908 mm earliest physical nut-bearing plane and continue
through the 137.8044 mm latest possible physical far-nut face. This whole-face
enclosure is sufficient, not necessary: a less extensive thread interval may
provide full engagement when it covers the nut's actual functional internal
threads. In either route, the external thread need not extend through the
additional 3.175 mm physical tip envelope. The actual body/last-scratch
coordinate must be at least 120.382 mm if a later method uses nominal bolt
diameter for the wood-side thread-bearing region. Verify the matched external
2A / internal 2B thread fit and Grade 5 identity, and confirm the delivered
bolt meets the actual stack and physical tip envelope. These are dimensional
receiving conditions, not capacity criteria.

## Bounded geometry alternative already screened

If the unspaced delivered fit cannot be demonstrated, the existing separate
[two-spacer option](current-ordinary-hardware-spacer-option.md) provides a
bounded geometry alternative for later review: two 0.120–0.130 in steel
spacers between the retained wood-bearing washer and the nut. Their combined
listed thickness shifts the nut and modeled tip envelope outward by
6.096–6.604 mm. The earliest nut-bearing plane becomes 134.6868 mm, which is
1.3368 mm beyond `LG,max`; the maximum far-nut face is 144.4084 mm and the
modeled tip target is 147.5834 mm. A 149.86 mm minimum bolt length leaves
2.2766 mm to that target. The two spacers add 96 pieces for these 48 axes;
four 25-piece packs would leave four spare.

This comparison only improves the gage-coordinate screen. It still requires
an actual matched-nut check through full functional thread height and review
of the point/runout at the nut, as well as a future geometry and access check
for the maximum 6.604 mm outward shift on all 48 stacks. No spacer, changed
stack, or CAD geometry is adopted here.

## Evidence trail

- K.L. Jack [25C600HCS5Z bolt listing](https://www.kljack.com/products/25c600hcs5z/)
  and [25CNFH5Z nut listing](https://www.kljack.com/products/25cnfh5z/),
  accessed 2026-09-25. Listings provide product attributes, package quantity,
  and displayed online price; they do not show a current item-specific stock
  count or delivery estimate.
- K.L. Jack [US branch locations](https://www.kljack.com/company/locations)
  and [ordering / availability FAQ](https://www.kljack.com/resources/faq),
  accessed 2026-09-25.
- K.L. Jack [technical data and charts](https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf),
  2009/10 catalog, p. 159; the basic thread length is labelled as a reference
  dimension and defined as the distance from extreme end to last complete
  thread.
- ASME [B18.2.1-2012 (R2021)](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws),
  [B18.2.2-2022](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts),
  and [B1.1-2024](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
  standard records, checked 2026-09-25.
