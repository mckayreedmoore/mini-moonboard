# WJ24 center-axis catalog and spacer option

**Prepared:** 2026-09-24. **Status: conditional dimensional option.** This note
checks public availability for the sixteen WJ24 center axes and screens one
separate standard-length-plus-spacer stack. It does not select a supplier or
SKU, approve the new stack, establish strength, or release drilling,
fabrication, purchasing, or assembly.

The [WJ24 inventory](hypotheses/wj24-hardware-inventory/README.md) leaves
these axes without a nominal bolt length: four at 100.915644 mm modeled wood
grip, eight at 127 mm, and four at 167 mm. Axis identities and the original
two-washer stack remain as recorded in the inventory and the separate
[bolt-length screen](wj24-bolt-length-screen.md).

## Catalog check

I first attempted the required Stripe Directory lookup. It was unavailable:
the installed Stripe CLI is version 1.33.0 and reports `directory` as an
unknown command; the parent also confirmed the existing Directory
authentication is expired. Following the authorized fallback, I checked
public supplier product pages read-only. I made no authentication changes,
vendor contact, or purchase.

| Previously screened length | Public listing found | What the listing supports | Disposition for this screen |
| --- | --- | --- | --- |
| 4.75 in, 4 axes | [MF Supply HH14CX4.75G5](https://www.mfsupply.com/1_4_20_X_4_3_4_Hex_Head_Cap_Screw_Steel_Zinc_p/hh14cx4.75g5.htm) | 1/4-20, 4-3/4 in, Grade 5, zinc; page showed in stock, 16 boxes, $378.98 per box. Listed box and piece weights imply 400 pieces per box (inference from 27.664/0.06916 lb). | Exact length is listed, but the box quantity is far above four axes and the page does not publish a thread-transition dimension. Not used in the separate option below. |
| 5.75 in, 8 axes | [Northwest Fastener G2TBP-NC025-0575](https://www.northwestfastener.com/bolts-and-cap-screws/tap-bolts/1-4-20-x-5-3-4-hex-tap-bolt-astm-a307-grade-a-plain.html?limit=100) | Exact 1/4-20 × 5-3/4 in, ASTM A307 Grade A, plain finish. The page says contact for pricing and does not publish stock quantity or thread coverage. | Does not establish the partially threaded Grade 5 dimensional basis used in the screen; no quote or contact requested. Not used. |
| 7.5 in, 4 axes | [HiStrength 104-049](https://histrength.com/104-049) | 1/4-20 × 7-1/2 in, Grade 5, partially threaded, ASME B18.2.1; page showed in stock at $2.54 each. | Page also lists a 3/4-in thread length. That conflicts with the 1-in reference thread length used by the B18.2.1 screen for lengths over 6 in. Treat the 7.5-in listing as unresolved until the supplier specification or received dimensions reconcile it. |

These listings establish catalog presence only. They do not establish a
received part, dimensional conformity, exact quantity availability, or
compatibility with the complete joint.

## Separate 5 / 6 / 8-in plus spacer option

The following is one catalog-listed geometry option to carry for further
review. Each axis retains its two baseline washer positions. Add the listed
McMaster spacer washer or washers between the nut-side baseline washer and
the nut; none goes between the wood members or between a washer and the wood.

| WJ24 axes | Count | Modeled wood grip | Partial-thread bolt listing | Added spacers per axis | Minimum delivered under-head length | Maximum far nut face + 3.175 mm projection | Length margin after projection | Conditional measured body-end to first-full-form-thread window |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `center_principal_header_{left,right}_{1,2}` | 4 | 100.915644 mm | 5 in, [HiStrength 104-040](https://histrength.com/104-040), 1/4-20 Grade 5 plain/light-oil; page showed in stock, $1.39 each | 1 | 124.46 mm | 118.197044 mm | 6.262956 mm | 101.6–105.554444 mm |
| `center_post_{left,right}_{1,2}` and `center_principal_{left,right}_{1,2}` | 8 | 127 mm | 6 in, [HiStrength 104-044](https://histrength.com/104-044), 1/4-20 Grade 5 plain/light-oil; page showed in stock, $1.23 each | 1 | 149.86 mm | 144.2814 mm | 5.5786 mm | 127–131.6388 mm |
| `center_post_header_{left,right}_{1,2}` | 4 | 167 mm | 8 in, [Grainger 38WN88](https://www.grainger.com/product/Hex-Head-Cap-Screw-Steel-38WN88), 1/4-20 Grade 5 zinc, partially threaded, minimum thread length 1 in; listing showed $8.45 per five-pack, stock count unavailable | 2 | 198.628 mm | 187.5834 mm | 11.0446 mm | 171.45–174.6868 mm |

Use [McMaster-Carr 91201A029](https://www.mcmaster.com/product/91201A029/)
for the added flat steel spacers: 1/4-in screw size, 0.281-in (7.1374 mm)
inside diameter, 0.625-in (15.875 mm) outside diameter, and 0.120–0.130-in
(3.048–3.302 mm) thickness. Its public page showed stock in packs of 25 but
did not expose a price. It describes the washer as suitable for use as a
spacer; its steel finish is intended for dry environments because moisture
can cause rust. The added washer's outside diameter is distinct from the
baseline seat washer, and the nut/spacer fit, bearing, environment, tool
access, and local seat geometry have not been checked.

The screening assumptions are the same two baseline washers, each
1.2954–2.032 mm thick; one 1/4-20 finished nut no thicker than 5.7404 mm;
3.175 mm of full-form thread past the far nut face; and ±0.5 mm allowance on
each of the two modeled wood layers. The new spacers add 3.048–3.302 mm each
on the nut side. Minimum delivered length uses the B18.2.1 lower tolerance:
−0.10 in through 6 in and −0.18 in above 6 in. The partial-thread envelope
uses `Lg,max` / `Lb,min` of 107.95 / 101.6 mm at 5 in, 133.35 / 127 mm at 6
in, and 177.8 / 171.45 mm at 8 in. These are standards-based screen inputs,
not measurements of the suppliers' bolts; the
[B18.2.1 source correction](bolt-dimension-source-correction.md) explains
the six-inch table attribution and keeps body length, grip gage, and measured
thread transition distinct.

The receiving window applies the existing conditional member-specific
threaded-bearing screen to each ordered pair of wood receivers. Its lower end
is the greater of `Lb,min` and the member split's body-end bound. Its upper
end is the lesser of `Lg,max` and the earliest possible nut bearing plane,
including the new spacer thickness. All three intervals are positive under
the assumptions above. They only define dimensions to measure on the
received bolts: measure under-head length, last thread scratch/body end,
first full-form thread, full-form thread through the complete nut, and at
least 3.175 mm of full-form thread beyond the far face. Confirm nut fit and
that the measured thread end does not exceed the actual tip. Nominal length
does not specify delivered shank length.

The listed 5-in and 6-in HiStrength items display per-piece prices and also
list package quantity 50; exact minimum order increments were not verified.
At displayed one-piece prices, those model quantities are $5.56 and $9.84.
The Grainger eight-inch listing is a five-pack; one $8.45 pack covers four
axes and leaves one extra bolt. Its page identifies an eight-inch fastener
but also has a conflicting `Overall Length` field of 3-1/4 in, and it does
not show a stock count. Resolve that catalog conflict before treating the
item as order-ready. These are page snapshots, not quotes. The twenty
McMaster spacers require one pack of 25 if the pack is the selling unit; the
public price is unavailable. Thus the known bolt-price context is $23.85
before spacer cost, shipping, tax, and package/order constraints; it is not
a complete option cost.

This separate option adds 20 physical washers: 4 × 1, 8 × 1, and 4 × 2.
The sixteen center axes therefore go from the inventory's 32 washer pieces
to 52; the all-layout screen would go from 216 to 236 if every other quantity
stayed unchanged. The inventory's 216 remains the baseline count. This is a
changed stack and needs a parent recheck of access, local clearances, seats,
and complete-joint mechanics; no zero-change geometry claim is made.

## Open gates

No vendor SKU or stack is selected. The catalog pages do not show received
dimensions or guarantee actual first-full-form-thread location. Confirm the
spacer's intended purchase price and order unit, all bolt and nut dimensions,
thread fit, delivered under-head length and transition, spacer/nut fit,
finish compatibility, and environmental suitability before carrying this
option forward. Recheck changed nut stand-off, wrench and tool access, nearby
members, washer seating, and complete joint behavior in the parent workflow.
No capacity, structural acceptance, cut/drill instruction, fabrication
release, or assembly release follows from this dimensional screen.
