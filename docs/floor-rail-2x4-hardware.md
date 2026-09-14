# Quarter-inch hardware for the 2×4 floor-rail trial

Verified September 14, 2026. This is a purchasable hardware family with explicit
installation conditions, not a passing structural decision or measured lot.
The trial uses six front and four rear quarter-inch bolts, plus four retained
half-inch upper bolts: 14 complete stacks. The [upper hardware basis](compact-half-inch-hardware.md)
remains unchanged.

| Quantity | Item | Published dimensions |
|---|---|---|
| 6 | [Bolt Depot 334](https://boltdepot.com/Product-Details?product=334), ¼-20 × 4-inch Grade 5 hex bolt | Length 100.076–101.6 mm; minimum threaded length 19.05 mm |
| 4 | [Bolt Depot 338](https://boltdepot.com/Product-Details?product=338), ¼-20 × 6-inch Grade 5 hex bolt | Length 149.86–152.4 mm; minimum threaded length 19.05 mm |
| 10 | [Bolt Depot 2569](https://boltdepot.com/Product-Details?product=2569), SAE J995 Grade 5 nut | Height 5.3848–5.7404 mm; flats 10.8712–11.1252 mm |
| 20 | [Bolt Depot 15021](https://boltdepot.com/Product-Details?product=15021), Grade 5 USS washer | OD 18.4658–19.0246 mm; bore 7.7978–8.3058 mm; thickness 1.2954–2.032 mm |

The bolts are partially threaded SAE J429, ASME B18.2.1 hex cap screws.
The head height is 3.81–4.1402 mm; published minimum flats are 10.8712 mm
and maximum corners are 12.827 mm. These dimensions and the Grade 5 minimum
92 ksi tensile yield are supported by the [supplier's dimensional/material sheet](https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf).

The simplified CAD stack uses washer OD 19.0 mm, bore 7.9375 mm and thickness
1.6 mm; nut height 5.69 mm; head height 4.1402 mm; circular corner envelope
12.827 mm. These are explicit nominal/envelope choices within published ranges,
not guarantees of supplied dimensions. The 7.9375 mm wood bore is a project
clearance, not a vendor drilling instruction. Washer resistance instead uses
minimum OD **18.4658**, maximum bore **8.3058**, and minimum thickness
**1.2954 mm**, with the retained conditional 33 ksi washer yield assumption.
Catalog Grade 5 washer wording alone does not establish that plate-yield value.
Machine-readable ranges are in [the hardware reference](floor-rail-2x4-hardware-reference.json).

## Thread coverage and a nut-seating constraint

Heads face inward, nuts/tips outward. Front stacks join 38.1 mm post to
38.1 mm rail; rear stacks join 38.1 mm rail to 88.9 mm leg. For the retained
nominal-diameter route, require full body to the first reduced section at least
`grip + head washer − nut-side timber / 4`. Treat transition as threaded.
Using the maximum head washer gives **68.707 mm front** and **106.807 mm rear**.
Actual wood and washer measurements control these requirements.

**The catalog minimum threaded length alone does not ensure that the nut can
seat.** At maximum bolt length and exactly 19.05 mm of thread, the nominal
thread starts at 82.55 mm front and 133.35 mm rear. With two minimum washers,
the nut bearing faces are only 78.7908 and 129.5908 mm from the head. Such bolts
could stop the nut on the shank before clamping the joint. Require usable full
threads to begin no later than the actual nut bearing face, while also meeting
the preceding full-body thresholds. The conservative nominal limits require
at least 22.8092 mm of usable tip-to-start threaded length at maximum bolt
length, rather than relying on the 19.05 mm catalog minimum. Runout must be
accounted for separately; do not count incomplete transition threads as usable.

The model uses **25.4 mm threaded length** for both quarter-inch lengths. This
puts nominal thread starts at 76.2 and 127.0 mm, before the nominal nut bearing
faces at 79.4 and 130.2 mm. The modeled length is a supplied-lot requirement
and simplified display assumption, **not a catalog guarantee**; the catalog
publishes only a 19.05 mm minimum. Actual usable threads and full-body length
must satisfy both gates despite runout and dimensional variation.

These conditions leave a feasible dimensional interval, but must be checked on
supplied stock. Do not infer that a longer standard bolt, extra washers, or a
fully threaded substitute solves this detail. No such substitution is selected.

With minimum bolt length, two maximum washers and maximum nut height, remaining
tip projections are **14.0716 mm front** and **13.0556 mm rear**, exceeding two
20-TPI pitches (2.54 mm). This is a stack-length check only; complete formed
threads, chamfer, usable engagement and nut seating still require inspection.

## Calculation references

The ¼-20 tensile stress area is **0.0318 in²**, independently published in a
[stud manufacturer's thread-area table](https://www.imageindustries.com/products/weld-stud/advanced-process-apa-inch-threaded-aluminum/part-number/APA25-75/mechanical-properties/FTA25/).
Only that geometric area is used; aluminum stud material properties are not
transferred. The thread-root sensitivity uses a **calculated basic external
UNC root reference**, `0.25 − 1.226869 / 20 = 0.18865655 inch`, rounded to
0.1887 inch. This is not a class-specific delivered minor-diameter lower bound.
The washer seat reference remains 95% of the published minimum hex flats,
not the full circular corner envelope. Fresh actual-force checks must use
these quarter-inch references; larger bolt capacities do not transfer.
