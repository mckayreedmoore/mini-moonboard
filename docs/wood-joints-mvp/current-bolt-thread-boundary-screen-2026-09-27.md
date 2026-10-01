# Current 1/4-20 thread-boundary source screen

**Checked:** 2026-09-27. **Status:** conditional catalog/standard comparison
only. This does not qualify a bolt, nut, washer stack, delivered lot, or axis.
No SKU is selected. No purchase, contact, geometry change, or fit criterion
is assigned.

## Scope and source basis

This screen covers the nine rows and 92 axes in the
[current bolt catalog screen][catalog01]
for `led-clearance-2x6-runner-seated-blocks-v1`, cross-checked against the
[current grip screen](current-grip-screen.md). The exact axis IDs and pinned
source records are in the [catalog-screen JSON][catalog01-data].
CAD models a 6.35 mm unthreaded shaft envelope; it supplies no delivered
thread coordinates.

The official [ASME B18.2.1 record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
lists edition B18.2.1-2012 (R2021) as in effect. The published
[STS Industrial 1/4-20 × 5-1/2 in Grade 5 cap-screw page][sts]
identifies item HHP50250550-I, SAE J429 Grade 5, B18.2.1 dimensions, and UNC
Class 2A. Its table gives 1/4 in cap-screw LT values of 0.750 in through 6 in
and 1.000 in over 6 in, with Y = 0.250 in. That page calls usable thread
length under 6-1/4 in an approximation: `2 × diameter + 1/4 in`. This is a
supplier's general approximation and a separate item record, not a dimension
or certificate for any SKU in the nine-row screen.

[Portland Bolt's thread-runout note](https://www.portlandbolt.com/technical/faqs/thread-runout/)
defines runout as the transition beyond usable thread and reports the B18.2.1
1/4 in cap-screw Y value as 0.25 in. The standard's Y value is a reference
calculation that includes incomplete thread, rolled-thread extrusion angle,
and grip-length tolerances. It does not give a particular catalog part's
actual runout profile or the axial interval of complete thread. See the
existing [ASME dimension and clause screen](current-ordinary-hardware-spacer-option.md)
for the local B18.2.1 text and its limited applicability to the modeled stack.

Current product listings remain records of advertised attributes. For
example, [Lawson FA21103][lawson]
lists an 8 in, Grade 5, partial-thread 1/4-20 cap screw, UNR form, minimum
thread length 1 in, and dimensions to B18.2.1/J429. The 1 in minimum does
not locate the first complete thread, last scratch, point, or transition.
[Fastener SuperStore 412254](https://www.fastenersuperstore.com/products/412254/hex-cap-screws)
lists a 7-1/2 in, partial-thread, Grade 5, 1/4-20 cap screw but no transition
dimensions. No delivered identity or lot conformance has been checked.

## Conditional gage-plane comparison

For a standard-conforming 1/4 in partial-thread cap screw, the catalog screen
uses `LG,max` as the class's maximum gage-length limit coordinate measured
from the underhead bearing face. It is neither the actual first-full-thread
coordinate nor a delivered-part transition limit. The table compares that
reference coordinate with the earliest nut bearing-plane coordinate already
recorded for each geometry row. `margin = bearing plane − LG,max`; it is only
arithmetic on catalog-class and CAD dimensions, not an acceptance result. For
alternative lengths, the comparison uses that alternative's standard
cap-screw class value.

For each row, `margin = bearing-plane coordinate − LG,max`. The compared class
values are conditional references, not fit results.

- **Outer post (4 axes, 4 in):** `LG,max` 82.550 mm; bearing plane
  78.7908 mm; margin −3.7592 mm. HiStrength lists 3/4 in thread length;
  no item transition drawing.
- **Center principal (4 axes, 5-1/2 in):** `LG,max` 120.650 mm; bearing
  plane 124.5908 mm; margin +3.9408 mm. HiStrength's 3/4 in field matches
  the class reference; Tanner gives no thread interval.
- **Center post (4 axes, 6 in alternative):** `LG,max` 133.350 mm; bearing
  plane 129.5908 mm; margin −3.7592 mm. No 5-3/4 in listing verified here;
  6 in leads omit thread location.
- **Ordinary (48 axes, 6 in):** `LG,max` 133.350 mm; bearing plane
  128.5908 mm; margin −4.7592 mm. Two McMaster 91201A029 spacers add
  6.096–6.604 mm, moving the plane to 134.6868–135.1948 mm. This is the
  existing conditional spacer geometry only.
- **Center post header (4 axes, 7-1/2 in):** `LG,max` 165.100 mm; bearing
  plane 169.5908 mm; margin +4.4908 mm. HiStrength lists 3/4 in versus the
  over-6-in 1 in LT reference; Fastener SuperStore gives no standard claim.
- **Center principal header (4 axes, 7-1/2 in):** `LG,max` 165.100 mm;
  bearing plane 175.3908 mm; margin +10.2908 mm. Same source limits as the
  center-post header; minimum length is only 0.1486 mm beyond the tip target.
- **Knee inner header (4 axes, 8 in alternative):** `LG,max` 177.800 mm;
  bearing plane 179.6908 mm; margin +1.8908 mm. No 7-3/4 in listing
  verified here. HiStrength lists 3/4 in versus the >6-in class value;
  Lawson states minimum 1 in only.
- **Side (16 axes, 8 in):** `LG,max` 177.800 mm; bearing plane
  180.3908 mm; margin +2.5908 mm. Lawson's standard claim and 1 in minimum
  support a class comparison, not actual coordinates or matched-nut fit.
- **Knee outer side (4 axes, 9-1/2 in lead):** `LG,max` 215.900 mm;
  bearing plane 218.4908 mm; arithmetic margin +2.5908 mm. Ro-Brand does not
  establish a partial-thread B18.2.1 cap screw; do not apply this class value.

The positive margins identify rows where the geometry's earliest nut face is
outboard of that nominal class limit coordinate, if the exact part conforms to
that class. They do not show the full thread interval through the nut. Negative
margins place the earliest bearing plane headward of the class limit
coordinate. These rows need a separate dimensionally supported arrangement or different source
evidence before even this boundary comparison changes. See the existing
[ordinary spacer screen](current-ordinary-hardware-spacer-option.md) and
[side hardware screen](current-side-hardware-option.md) for their full stack
envelopes.

## Exact evidence still missing

No current SKU can be fit-qualified for any axis from the public dimensions
reviewed. A matched public hardware route has useful envelope data:
[K.L. Jack 25CNFH5Z](https://www.kljack.com/products/25cnfh5z/) lists 1/4-20
UNC Class 2B, Grade 5, B18.2.2, and 7/32 in nominal thickness;
[K.L. Jack 25NWUS](https://www.kljack.com/products/25nwus/) lists a 1/4 in
Type A Wide washer with 0.312 in ID, 47/64 in OD, and 0.051–0.080 in
thickness. The public nut record does not give the actual unchamfered active
thread height or entry/exit chamfer dimensions. The washer record gives no
strength grade or per-axis supported-bearing acceptance. The
[McMaster 91201A029 page](https://www.mcmaster.com/product/91201A029/)
provides a 0.281 in ID, 0.625 in OD, 0.120–0.130 in thick, Rockwell B84
spacer washer; those dimensions support the ordinary-row offset arithmetic
only.

For a defensible item-and-axis fit record, the missing source/receiving
contract is:

- Exact manufacturer part number and standard edition for each bolt; external
  1/4-20 UNC class, coating condition, full-length tolerance, and traceable
  evidence that the delivered lot conforms to the named cap-screw dimensions.
- Underhead coordinates or guaranteed gage bounds for first complete
  full-form thread, last thread scratch, transition/runout profile, and tip
  point/chamfer. A catalog `Thread Length`, `LT`, `LG,max`, `LB,min`, or `Y`
  alone is not an actual delivered interval.
- Matched nut lot's internal class/gage result and functional unchamfered
  thread interval, plus entry and exit chamfers. Nominal 7/32 in nut height
  alone cannot establish overlap with the bolt's usable thread.
- Actual washer/spacer ID, OD, thickness, and position for each axis. For
  wood-bearing washers, also establish the required supported footprint and
  material basis; those are not inferred from catalog geometry.

The exact axis lists, grip intervals, and modeled hardware-role intervals stay
in the [pinned catalog JSON][catalog01-data] and [grip JSON][grip02].
The catalog artifact's disposition remains 0/92 fit-qualified axes.

[catalog01]:
  hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/README.md
[catalog01-data]:
  hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/catalog-screen.json
[grip02]: hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json
[sts]: https://www.stsindustrial.com/products/0-25-20x5-5grade-5-hex-cap-screw-plated
[lawson]: https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103
