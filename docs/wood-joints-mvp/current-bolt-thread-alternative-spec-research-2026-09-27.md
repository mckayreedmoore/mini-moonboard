# Alternative manufacturer and nut thread-boundary source check

**Checked:** 2026-09-27. **Result:** no newly located public drawing gives a
part-specific underhead interval for complete usable male threads, a thread
length tolerance, or an exact smooth-shank length for the current 1/4-20
Grade 5 bolt rows. No nut drawing gives the matched nut's active-thread
height. This is a source search against the frozen screen, not a hardware
selection, fit qualification, purchase, or geometry change.

## Scope and comparison basis

The nine geometry rows, axis counts, and grip/nut-plane coordinates below
come from the pinned [catalog screen](hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/catalog-screen.json)
and [grip screen](current-grip-screen.md). The modeled CAD shaft is an
unthreaded envelope. The comparator `LG,max` is the current standard-class
gage coordinate, and `margin` is earliest nut-bearing plane minus `LG,max`.
Neither value is a delivered bolt thread-start coordinate.

| Geometry row | Axes | Wood grip (mm) | Earliest nut bearing (mm) | Existing class comparator: `LG,max` (mm); margin (mm) |
| --- | ---: | ---: | ---: | --- |
| Outer post | 4 | 76.2 | 78.7908 | 4 in: 82.550; −3.759 |
| Center principal | 4 | 122.0 | 124.5908 | 5.5 in: 120.650; +3.941 |
| Center post | 4 | 127.0 | 129.5908 | 5.75 in: 127.000; +2.591. 6 in alternative: 133.350; −3.759 |
| Ordinary | 48 | 127.0 | 128.5908 | 6 in: 133.350; −4.759 |
| Center post header | 4 | 167.0 | 169.5908 | 7.5 in: 165.100; +4.491 |
| Center principal header | 4 | 172.8 | 175.3908 | 7.5 in: 165.100; +10.291 |
| Knee inner header | 4 | 177.1 | 179.6908 | 7.75 in: 171.450; +8.241. 8 in alternative: 177.800; +1.891 |
| Side | 16 | 177.8 | 180.3908 | 8 in: 177.800; +2.591 |
| Knee outer side | 4 | 215.9 | 218.4908 | 9.5 in: 215.900; +2.591 |

The current [thread-boundary screen](current-bolt-thread-boundary-screen-2026-09-27.md)
already records the ASME class `LG`/`LB` comparisons. Its per-row bearing
margins are unchanged by this research. For 1/4 in cap screws, the reviewed
technical tables repeat `LT = 0.750 in` for lengths through 6 in and
`LT = 1.000 in` above 6 in; `LT` is a calculation reference. The tables
also show `Y = 0.250 in`, a reference dimension intended for calculation that
includes incomplete-thread and grip tolerances. The tables do not provide an
item-specific full-form thread interval. The 9.5 in
class comparison is not transferred to Ro-Brand HC5127, whose current listing
does not establish B18.2.1 cap-screw conformity.

## Manufacturer and catalog sources checked

- [Nucor Fastener Cap Screws Technical Data Sheet, TDS-009B, dated
  2008-02-15](https://cdn.thomasnet.com/ccp/01024953/118079.pdf), accessed
  2026-09-27. The document identifies Nucor Fastener as the manufacturer and
  says its cap screws are controlled to ASME B18.2.1, with traceability and
  shipment certifications. Its dimensional table reproduces general
  B18.2.1 `LT`, `Y`, `LG`, and `LB` data; it does not name a current row's
  exact part number or specify a lot's first full thread, last full thread,
  thread-length tolerance, or smooth-shank length. This dated generic sheet
  does not establish conformance to the current B18.2.1 edition. The copy
  examined here is hosted on ThomasNet.
- [BrightonBest Grade 5 catalog](https://www.brightonbest.com/download/catalogs/usa/BBI_USA_G5.pdf),
  accessed 2026-09-27. It lists 1/4-20 Grade 5 B18.2.1 product/length codes,
  including 4 in (847030), 5-1/2 in (847033), and 6 in (847034) in its
  Zinc CR+3 inch-series table. Those are catalog identities and length
  offerings only; the listing table has no underhead thread-start drawing,
  usable-thread bounds, or part-specific thread-length tolerance. Its
  separate dimensional sketch/table is not an item drawing for those codes.
- [AllFasteners Hex Cap Screws TDS, version 2025-09-19](https://ddrp1nim4cnld.cloudfront.net/media/sparsh/product_attachment/HexCapScrewsTDS.pdf),
  accessed 2026-09-27. This product-family sheet lists partial-thread zinc
  Grade 5 availability and a generic ASME B18.2.1 dimensional table. It gives
  the same reference `LT` rows and general thread-class notes, but its Grade 5
  ordering table does not identify a 1/4-20 part at the current long lengths.
  It provides no axial thread-transition tolerance or exact shank length.

The current [ASME B18.2.1 record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
lists B18.2.1-2012 (R2021) as in effect. The manufacturers' `LT` and `Y`
tables are standard reference dimensions, not a new tolerance for a named
bolt SKU.
`LG,max` and `LB,min` remain standard gage/body criteria. They do not locate
the thread's complete-form start or the nut's full functional internal-thread
interval. Therefore none changes the class-only comparisons above or the
screen's 0/92 fit-qualified disposition.

## Matched nut boundary

The pinned screen has one nut lead: K.L. Jack [25CNFH5Z](https://www.kljack.com/products/25cnfh5z/),
supplier P/N AFH5Z0250C. Its catalog record says 1/4-20 UNC Class 2B,
Grade 5, ASME B18.2.2, and nominal 7/32 in thickness. The product page was
rechecked 2026-09-27 but timed out; those fields remain the previously
retrieved public listing, not an item drawing or lot record.

ASME's official [B18.2.2 record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts)
lists the 2022 edition as in effect. A public full-text copy of that edition
was reviewed at [StudyLib](https://studylib.net/doc/27188368/asme-b18.2.2-2022);
the edition/title were cross-checked against ASME's record. The standard
provides the finished-nut outer thickness envelope (0.212–0.226 in for a
1/4 in nut), double-chamfer geometry, and limits for the thread-entry
countersink. Those exterior/entry limits do not specify axial countersink
depth or the actual nut lot's active unchamfered thread height. No product
drawing or matching-lot internal-thread gage result was located. Thus the
nut's active-thread interval cannot be overlaid on any of the nine nut
intervals from public dimensions alone.

## Source access record

ASME B18.2.1 and B18.2.2 edition/status records, the BBI catalog, and the
AllFasteners TDS were directly accessible on 2026-09-27. The Nucor TDS was
accessible through its ThomasNet-hosted PDF on that date. The K.L. Jack nut
page timed out on the recheck; the part fields above retain the pinned
catalog-screen observation. The full B18.2.2 text was consulted through a
third-party copy, with edition/status taken from ASME's official page. No
vendor contact or inventory check was made.
