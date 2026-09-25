# Independent review: 16 side-axis hardware option

**Reviewed:** 2026-09-25. **Result:** no material correction needed in the
axis binding, dimensional arithmetic, or conditional sourcing interpretation.
This review records a source and calculation check; it selects no hardware,
establishes no delivered fit, and changes no current authority.

## Pinned inputs and exact axis scope

The reviewed [conditional option](../current-side-hardware-option.md) is
SHA-256 `19906c7d8eba3aa035a36de9d6e936cdca222c8e24fde6325863585ecc145522`.
Its frozen [attempt 02 grip-screen JSON](evaluation-resume-2026-09-24/grip-screen-attempt02.json)
is `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`;
the [current hardware schedule](../current-hardware-schedule.md) is
`47a1de21705570cfd23fb493c640d8983945ee410623e15484cf53ed7596bffa`.

I matched every listed ID to its JSON row. There are exactly 16: four each
from `bottom_outer`, the lower and upper side bolts in the
`left_service_mirrored_inner_outer_hypothesis`, `top_outer`, and the lower and
upper side bolts in `wj06_outer_pair`. Each row reports a 6.35 mm unthreaded
CAD shaft envelope, a 203.2 mm modeled under-head-to-tip length, and 177.8 mm
of unioned wood grip across the two receivers. These rows are the exact
current modeled axes; the field values do not describe delivered hardware.

## Stack and standard-bound arithmetic

Using the source-bound grip, the K.L. Jack Type A Wide washer interval
1.2954–2.032 mm on each side, and the B18.2.2 finished-nut interval
5.3848–5.7404 mm, the option's endpoints reproduce:

| Quantity | Recomputed value |
| --- | ---: |
| Far wood face | 179.0954–179.832 mm |
| Nut bearing plane | 180.3908–181.864 mm |
| Far nut face | 185.7756–187.6044 mm |
| ASME `LG,max` / `LB,min` for conditional 1/4 in × 8 in cap-screw comparison | 177.8 / 171.45 mm |
| Latest far nut face plus 3.175 mm physical-tip projection | 190.7794 mm |
| Minimum-length screen, 7.82 in | 198.628 mm |
| Minimum-length physical tip past latest far nut face | 11.0236 mm |
| Physical-tip margin beyond the 3.175 mm minimum | 7.8486 mm |
| Minimum standard length short of 203.2 mm modeled endpoint | 4.572 mm |

The earliest nut-bearing plane is 2.5908 mm beyond `LG,max`; the far wood
face is 7.6454–8.382 mm beyond `LB,min`. These are favorable standard-gage
coordinate comparisons under the stated standard-conformance condition. They
do not locate an actual first full-form thread, establish an actual body to
last-scratch boundary, or prove full functional engagement with the nut.
The option treats that difference correctly and leaves actual fit open.

The two length tests are distinct. The 3.175 mm value is the inherited
physical bolt-tip projection in the WJ24 occupancy screen, not a full-thread
requirement. A standard-conforming 8 in item at the 7.82 in minimum meets
that physical-tip projection by 7.8486 mm, yet can end 4.572 mm before the
203.2 mm CAD cylinder endpoint. The option correctly calls the latter a
modeled endpoint, not a received-part measurement or purchase-length rule.
If later analysis depends on the full endpoint, delivered length must be
measured or the parent must revise that analysis basis. No such revision is
implied here.

## Supplier facts, packages, and conditional thread class

The [Lawson FA21103 listing](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103)
supports a 1/4-20 × 8 in, Grade 5, bright-zinc cap screw, UNR partial thread,
listed one-inch minimum thread length, and a 25-piece package. The Lawson
page says dimensions to ANSI B18.2.1 and SAE J429 Grade 5 properties; it does
not name the bolt's external thread class or give its part-specific thread
transition. Sixteen required bolts fit one pack with nine remaining. The
listed page requires account access for price and presents a check-availability
control, so the option appropriately reports no public bolt price, stock
count, or delivery date.

K.L. Jack's [25CNFH5Z nut listing](https://www.kljack.com/products/25cnfh5z/)
supports the stated 1/4-20, Grade 5, zinc-plated, ASME B18.2.2 / SAE J995,
internal UNC Class 2B nut, 7/32 in nominal thickness, 100-piece box, and
$4.71 displayed box price. One box covers 16 nuts with 84 remaining. Its
[25NWUS washer listing](https://www.kljack.com/products/25nwus/) supports a
100-piece box of 1/4 in plain/light-oil, low-carbon-steel Type A Wide USS
washers, 0.312 in ID, 47/64 in OD, and 0.051–0.080 in thickness, displayed at
$3.47. One box covers 32 washers with 68 remaining. The $8.18 sum is just
those two displayed boxes; bolt price, tax, shipping, and the finish choice
remain open. The washer listing gives no strength rating, and the note does
not infer a bearing capacity from it.

The intended `2A` external / `2B` internal thread pairing is conditional:
Lawson identifies the thread as UNR and the dimensions as B18.2.1, while the
nut explicitly lists 2B. The option makes application of the standard's 2A
default contingent on confirming the bolt's conformity and checking the
delivered zinc-coated thread gauge. This does not prove that a delivered
matched pair fully engages over the nut's functional thread interval; that
remains an explicit fit condition. The product and package facts support a
candidate route, not actual stock, part identity, or acceptance.

## Status

The option's conclusion is appropriately limited to a dimensional sourcing
candidate. It does not establish full functional nut engagement, washer
support, hardware resistance, signed demand adequacy, delivered stock, or
assembly. The reviewed note needs no material correction before publication
within that conditional scope, and it changes no geometry or current
authority.

The controlling dimensional references are the cited [ASME B18.2.1
record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws),
[ASME B18.2.2 record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts),
and [ASME B1.1 record](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form),
read with the frozen source and the option's named supplier pages. The
[current WJ24 bolt-length screen](../wj24-bolt-length-screen.md) documents
the inherited physical-tip input and expressly separates it from thread
engagement.
