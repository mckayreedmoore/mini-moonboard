# Conditional 8 in Grade 5 hardware option for the 16 WJ24 side axes

**Checked:** 2026-09-25. **Status:** a dimensional supplier route is identified
for review; no bolt/nut set is selected, received, or qualified. This note
covers only the 16 side axes currently modeled at 203.2 mm overall length and
177.8 mm wood grip. It does not change geometry or establish a resistance,
fabrication, or assembly result.

## Exact axes and geometry input

The source is the frozen
[attempt 02 grip-screen JSON](hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json),
SHA-256 `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`,
also rendered in the [current grip-screen report](current-grip-screen.md).
Every axis below has the same 6.35 mm unthreaded CAD shaft envelope, 203.2 mm
modeled under-head-to-tip length, 177.8 mm wood grip, and one washer on each
side of the wood stack followed by one nut. The CAD cylinder is an occupancy
envelope, not a delivered bolt dimension or purchase-length instruction.

| Exact axis IDs from the source | Count |
| --- | ---: |
| `bottom_outer/clip_horizontal_bottom_left_1/side_1`, `bottom_outer/clip_horizontal_bottom_left_1/side_2`, `bottom_outer/clip_horizontal_bottom_right_2/side_1`, `bottom_outer/clip_horizontal_bottom_right_2/side_2` | 4 |
| `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/lower_side_1`, `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/lower_side_2`, `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_1/upper_side_1`, `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_1/upper_side_2` | 4 |
| `top_outer/clip_single_top_left_1/side_1`, `top_outer/clip_single_top_left_1/side_2`, `top_outer/clip_single_top_right_2/side_1`, `top_outer/clip_single_top_right_2/side_2` | 4 |
| `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/lower_side_1`, `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/lower_side_2`, `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/upper_side_1`, `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/upper_side_2` | 4 |
| **Total** | **16** |

## One named supplier route

The candidate pair is a U.S.-catalogued [Lawson FA21103 1/4-20 × 8 in Grade 5
hex cap screw](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103)
and K.L. Jack [25CNFH5Z 1/4-20 Grade 5 hex nut](https://www.kljack.com/products/25cnfh5z/).
For the two washer roles, K.L. Jack's [25NWUS 1/4 in plain USS washer](https://www.kljack.com/products/25nwus/)
is a dimensional candidate. These are exact catalog identities and a
same-size thread-class route; they are not a tested matched lot or an accepted
hardware schedule.

| Role | Catalog item and published facts | Quantity / package screen | Price coverage checked 2026-09-25 |
| --- | --- | --- | --- |
| Bolt | Lawson / FalconGrip **FA21103**: 1/4-20 UNC, 8 in, carbon steel Grade 5, bright zinc, partial thread, minimum listed thread length 1 in, UNR thread form, 7/16 in across flats, 5/32 in head height; page says dimensions to ANSI B18.2.1 and SAE J429 Grade 5 material/mechanical properties. | 16 required; one 25-piece pack; 9 spare. | The product page requires login/register to see price and offers “Check Availability”; no public price, stock count, or delivery date found. |
| Nut | K.L. Jack **25CNFH5Z** / supplier P/N **AFH5Z0250C**: 1/4-20 zinc-plated Grade 5 finished hex nut; ASME B18.2.2; SAE J995 Grade 5; ASME B1.1 UNC Class 2B; 7/16 in hex; 7/32 in listed thickness. | 16 required; one 100-piece box; 84 spare. | Page displayed **$4.71 / 100-piece box**. No lot stock or delivery date was shown. |
| Washers | K.L. Jack **25NWUS**: plain/light-oil low-carbon steel USS washer; ASME B18.21.1 Type A Wide; 1/4 in bolt size; 0.312 in ID, 47/64 in OD, 0.051–0.080 in thickness. | 32 required; one 100-piece box; 68 spare. | Page displayed **$3.47 / 100-piece box**. No lot stock or delivery date was shown. |

The bolt page reports UNR form and 1/4-20 coarse pitch but does not separately
name an external thread class. ASME B18.2.1 §2.5.2 gives Class 2A as the
default standard external-thread class unless otherwise specified, before
coating, when the product conforms to that standard. Lawson says “product
dimensions to ANSI B18.2.1”; it does not provide a part-specific compliance
certificate or an external-thread class field. The conditional intended pair
is therefore external 2A / internal 2B, subject to confirming the bolt's
standard conformity and the delivered zinc-coated thread gauge result. The
nut page explicitly publishes internal Class 2B. The listing data do not prove
the specific bolt and nut will fully engage one another over the nut's
functional internal-thread height.

The washer page identifies dimensions and low-carbon steel, not a washer
strength rating or acceptance of its bearing footprint for these wood faces.
The candidate washer is plain/light oil while the bolt and nut are zinc
plated; the finish/environment decision is open. Do not infer resistance,
surface durability, or wood bearing adequacy from these catalogue entries.

The nut and washer displays total $8.18 for their full boxes, before tax or
shipping; the exact bolt price is unavailable. This is not a complete group
cost or per-axis estimate. The price lines were visible in public catalogue
results on the checked date and can change. No inventory check, vendor
contact, checkout, or purchase was made.

## Axial fit screen from the current stacks

Coordinates below are measured from the modeled under-head bearing datum.
The source geometry fixes the two wood receivers at 177.8 mm total. The
washer and nut intervals use the cited ASME dimensional ranges rather than
the current CAD role thickness alone. No separate wood-length allowance is
added.

| Quantity | Screen interval / value | Basis |
| --- | ---: | --- |
| 1/4 in Type A Wide washer thickness, each | 1.2954–2.032 mm | 0.051–0.080 in. |
| Combined wood grip | 177.800 mm | Frozen axis source. |
| Far wood face | 179.0954–179.832 mm | Head washer plus 177.8 mm wood. |
| Earliest nut bearing plane | 180.3908 mm | 1.2954 mm head washer + 177.8 mm wood + 1.2954 mm nut-side washer. |
| Latest nut bearing plane | 181.864 mm | Both washers at 2.032 mm. |
| Finished 1/4 in hex-nut thickness | 5.3848–5.7404 mm | ASME B18.2.2 limits: 0.212–0.226 in; 7/32 in is the supplier's nominal listing. |
| Latest physical far-nut face | 187.6044 mm | 181.864 + 5.7404. |
| Inherited minimum physical tip projection | 3.175 mm past the nut | Physical bolt-tip envelope only; it does not require full-form thread through the extra tail. |
| Far-nut face plus minimum physical tip projection | 190.7794 mm | 187.6044 + 3.175. |

For a 1/4 in × 8 in cap screw under ASME B18.2.1-2012 (R2021), the table
screen is `LG,max = 7.00 in = 177.8 mm`, `LB,min = 6.75 in = 171.45 mm`,
and minimum overall length `7.82 in = 198.628 mm` (the over-6-in length
tolerance is −0.18 in). Lawson lists its nominal 8 in length and B18.2.1
dimensions, but the delivered item has not been measured. `LG` is a thread
ring-gage reach limit, not an actual first-full-form-thread coordinate;
`LB` is a minimum under-head body length to the last thread scratch, not the
end of a required full-thread tail. The 1 in `LT` in the standard table is a
reference dimension, while Lawson's separate “minimum thread length 1 in”
field does not locate the complete-thread start or runout on the actual part.

The gage-coordinate screen is favorable: the earliest nut bearing plane is
2.5908 mm beyond `LG,max`. The `LB,min` body boundary lies 7.6454–8.382 mm
inside the final 88.9 mm wood receiver across the washer extrema. Those
comparisons make the option worth a matched-part check; neither is a
full-height nut-engagement proof or a capacity check. Confirm that the actual
bolt's usable external threads overlap the matched nut's functional internal
thread interval, with entry/exit chamfers treated according to the actual
parts, and that shank, incomplete thread, point, or runout does not prevent
the nut from seating. No full-form thread is required along the extra 3.175
mm physical tip projection.

At the minimum standard overall length, 198.628 mm, the physical tip extends
11.0236 mm beyond the latest possible far-nut face. That exceeds the
inherited 3.175 mm minimum physical-tip projection by 7.8486 mm; therefore no
nut shift is needed for that minimum-tail screen. It is distinct from the
current CAD cylinder endpoint: 198.628 mm is 4.572 mm shorter than the
modeled 203.2 mm endpoint. The standard length tolerance does not guarantee
that a delivered 8 in bolt reaches the full modeled endpoint. If later
analysis requires that exact endpoint, measure the delivered bolt length
against 203.2 mm or revise the accepted geometry basis through the parent
workflow; this note makes no such decision.

## Conditions that remain open

- Confirm delivered bolt identity, Grade 5 marking/traceability, 1/4-20
  external thread class/gauging after zinc plating, actual under-head length,
  and actual body/thread/runout positions. The Lawson listing does not
  provide an item-specific drawing of those axial transitions.
- Confirm the delivered K.L. Jack nut is Grade 5, internal 2B, and engages the
  actual bolt through its functional thread height while seating on the
  washer. Catalogue size and class alone do not prove the pair's full-height
  fit.
- Measure washer ID, OD, and thickness and verify head/nut seating, clearance,
  and wood-face support for all 16 stacks. Catalogue washer dimensions do not
  supply a washer resistance.
- Resolve the plain-washer / zinc-fastener finish combination for the actual
  environment and obtain a usable price/stock date for the exact bolt pack.
- Evaluate the actual 16-axis load path and signed demands separately. This
  sourcing and dimensional screen assigns no bolt, nut, washer, wood, or
  joint capacity.

The Stripe Directory attempt and permitted public-catalogue fallback are
recorded in the [ordinary hardware basis](current-ordinary-hardware-basis.md#bounded-follow-up-on-a-longer-thread-6-in-item-2026-09-24).
The current hardware schedule remains the quantity authority. The selected
SKU, hole changes, stack movement, drilling, assembly, and physical work are
outside this note.

## Source trail

- Lawson [FA21103 product page](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103),
  checked 2026-09-25; product data and price/availability presentation.
- K.L. Jack [25CNFH5Z nut page](https://www.kljack.com/products/25cnfh5z/)
  and [25NWUS washer page](https://www.kljack.com/products/25nwus/), checked
  2026-09-25.
- ASME [B18.2.1 standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws),
  [B18.2.2 standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts),
  and [B1.1 standard record](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form); editions checked 2026-09-25.
- [B18.2.1 partial-thread dimension table](https://www.nickel-systems.com/products/bolts-screws/hex-head-cap/) and
  [table PDF](https://www.nickel-systems.com/wp-content/uploads/2025/01/Hex-Head-Cap-Screws-Partially-Threaded-Minimum-Body-Maximum-Grip-Gaging-Lengths-1.pdf);
  [finished-hex nut dimensions](https://www.nickel-systems.com/products/nuts/finished-hex/);
  [Type A Wide washer dimension sheet](https://www.fastenal.com/content/product_specifications/FW.LC.USS.A.P.00.pdf).
- Existing [current hardware schedule](current-hardware-schedule.md) and
  [ordinary hardware sourcing follow-up](current-ordinary-hardware-sourcing-followup.md)
  provide the frozen input hash and Directory/fallback sequence.
