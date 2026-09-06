# Revised candidate: hardware completion audit

This audits `screw-spacing-development`, not a purchasing schedule or approval.
The [connection CSV](../exports/screw-spacing-development/screw-spacing-development_connections.csv)
contains **226 frame connections: 132 screws and 94 bolts**. The generic bolt
geometry adds two washers, one head and one nut per connection: 188 washers
and 94 nuts. These counts do not include hold hardware or T-nut fixing screws.

## Repeated families still requiring product closure

| Family | Modeled inventory | Remaining product/detail decision |
| --- | --- | --- |
| Panel/kicker screws | 80 × Ø4.826 × 50.8 mm | Product, head/drive, thread extent, countersink and installation machining. |
| Other wood screws | 8 × 63.5 mm and 24 × 88.9 mm, Ø4.826 | Same dimensions plus applicable receiving-grain and withdrawal rules. |
| Front-rib screws | 12 × Ø4.826 × 88.9 mm | SDWS16312 remains a lead, not the modeled product. Its conservative published thread/head envelope is Ø5.4864/11.43 mm, larger than the generic model. |
| Mid-batten end screws | 4 × 138.9 mm and 4 × 189.7 mm, Ø4.826 | These are calculated geometric lengths, **not selected catalog products**. Resolve an obtainable fastener and permitted connection detail before purchasing or assigning resistance. |
| Through-bolts | All Ø9.525 mm; counts and length/grip below | Real head, nut, washer, thread transition, full nut engagement, tolerances and end projection for each stack. |

| Bolt count | Nominal length / grip, mm |
| ---: | ---: |
| 6 | 57.15 / 38.1 |
| 44 | 63.5 / 44.1 |
| 24 | 88.9 / 69.5 |
| 8 | 95.25 / 76.2 |
| 12 | 114.3 / 94.9 |

The [hardware implementation](../mini_moonboard/box_frame.py) uses solid washer
cylinders Ø25.4 × 2 mm, cylindrical head/nut envelopes Ø18 × 6/9 mm, and a
generic Ø10 × 3 mm conical screw head. It does not model washer bores, real hex
flats, underhead nibs or manufacturing tolerances. Nominal Ø36 × 25 mm socket
approaches and straight withdrawal checks do not prove actual counterhold,
tool access or the complete assembly sequence. The twenty custom angles also
need material, bend radius, fabrication tolerances and finish specified.

The [front-rib product screen](front-rib-fastener-selection.md) records the
published dimensional/seating uncertainty; its old 8.0044 mm close-screw finding
belongs to the predecessor. The revised candidate moves that group. Its tight
row screen is now 26 mm against 25.4 mm, leaving only 0.6 mm before tolerances.
The [short stitch-bolt lead](leg-connection-development.md) establishes an
obtainable nominal length, not a fully checked bolt/accessory stack.

A further [Simpson Australia SDWS16 technical sheet](https://strongtie.com.au/sites/default/files/technical_data/T-F-SDWS16-AU23_11.12.23.pdf)
lists rounded SDWS16312 dimensions: 89 mm length, 51 mm thread length,
11.2 mm head, 4.0 mm shank, 5.5 mm major and 3.7 mm minor diameter. It still
does not give axial head/nib geometry. These regional, rounded values are not
a tolerance envelope or permission to substitute the product or its resistance
tables into this design. The head-seating decision remains open.

## Supplied insert and LED measurements are retained

The [measured constants](../mini_moonboard/model.py) already retain the T-nut
flange Ø25.4 × 1.86 mm, 12.7 mm body depth and Ø3.2 mm flange screw holes, and
the LED body/dome dimensions and 75° dome angle. No repeat measurements or
offcut fit test are requested by this audit.

The legacy BOM calls for 142 three-hole T-nuts with included fixing screws:
that implies up to 426 retaining screws if all three holes are used. Their
installed screw/head/tool geometry and hold-specific bolts are not in the
226-connection frame schedule. Likewise, current LED clearance tests use a
simplified Ø12.7 × 31 mm body and straight wire corridors, not a complete
installed harness with angled dome, bends, connectors, strain relief,
controller and extraction path.

## Next closure order

1. Obtain the front-rib product's axial head/nib geometry and definitive seating
   instruction; it determines panel-face seating and batten machining.
2. Resolve the eight long end-screw details with obtainable products and
   applicable connection rules; do not round their lengths silently.
3. Select one real 3/8-inch bolt/nut/washer family and check every length/grip
   stack, thread engagement, projection, tool and counterhold envelope.
4. Add installed insert fixing hardware and the remaining LED harness provisions,
   using the measurements already supplied.

Actual structural plywood, lumber grade/species, moisture and fabrication
process remain separate resistance inputs. No generic hardware envelope,
appearance-grade plywood label or successful geometry test supplies them.

## Washer-bore model correction identified by the quiet control

The isolated [free-hardware control](moving-hardware-control.md) exposes a
problem with the nominal washer model: its bore was cut to exactly the 9.525 mm
shank diameter. That zero-clearance assumption is not a selected washer product.
The quiet numerical test develops bore-contact energy and cannot yet qualify;
this is not evidence for increasing timber size or a hardware strength failure.

One manufacturer-backed geometry lead is [L.H. Dottie FW38, 3/8-inch USS flat
washer](https://lhdottie.com/pdf/product-specification-sheet/FW38), checked
2026-09-06. Its published bounds are:

| Dimension | Imperial | Metric |
| --- | --- | --- |
| Bore diameter | 0.433–0.453 in | 10.9982–11.5062 mm |
| Outside diameter | 0.993–1.030 in | 25.2222–26.1620 mm |
| Thickness | 0.064–0.104 in | 1.6256–2.6416 mm |

The sheet identifies unhardened carbon steel with zinc plating. These dimensions
provide at least 0.7366 mm nominal radial clearance against the modeled
9.525 mm shank. The current 25.4 mm OD and 2 mm thickness lie within the
published bounds, but are not guaranteed dimensions of a purchased washer.

Next, use an explicitly identified catalog-consistent washer geometry and
tolerance envelope, then recheck bearing area, nut/head contact, grip stack,
projection and tool clearances. Do not silently enlarge the bore just until a
solver passes. Product selection and washer/wood/bolt resistance remain open;
the catalog geometry does not establish suitability for this joint. Preserve
the original zero-clearance trial as a rejected numerical model.
