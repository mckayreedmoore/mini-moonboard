# Raised-rail nominal hardware and access

This is the hardware and receiving companion for the Eoere raised-rail conditional numerical MVP. The current saved model has 100 physical bolts, 100 heads, 100 nuts and 200 washers: 84 angle shafts, four cleat/post shafts and twelve starting frame bolts. Twenty-two installed angles use 88 factory holes; four shafts pass through two angles. The purchase scenario is six four-packs for 24 angles, including two spares.

[Bolt stacks](bolt-stacks.csv) covers every physical stack, its current receiver and fitting identities, model recipe, nominal length and dimensional receiving comparisons. [Access sides](access-sides.csv) covers all 200 head/nut sides. [Inputs](hardware-inputs.json) and [result](hardware-result.json) bind the saved sources. Actual and Disposition cells are blank; no delivered part or tool has been observed.

## Nominal length allocation

The listed Bolt Depot SKUs and matching Grade5 nuts/USS washers are the frozen comparison basket. They do not replace the saved model's washer, nut or hex envelopes or establish a delivered hardware selection.

The Eoere four-pack reference is [B0C7V7VS89](https://www.amazon.com/dp/B0C7V7VS89). Its drawing-inch and description-metric dimensions remain separate nominal scenarios: 88.9 mm arms/breadth with 6.35 mm thickness, and 90 mm arms/breadth with 6 mm thickness. Delivered dimensions, factory-hole datums/tolerances, formed heel and material remain unverified. Reconcile the listed 10 mm hole with literal 3/8 in (9.525 mm); the latter has zero nominal diametral clearance to a 3/8 in bolt. Keep all eight product holes, including the unused pairs. The saved current fitting placement does not qualify a delivered part.

| Source | Diameter | Nominal length | Quantity | Receiver + plate S | Bolt comparison SKU | Shortest L / maximum catalog stack margin for two tip pitches |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Cleat/post | 3/8 in | 4 in | 4 | 76.2 mm | 367 | 6.858000 mm |
| Angle | 3/8 in | 2.5 in | 60 | 44.45 mm | 363 | 1.016000 mm |
| Angle | 3/8 in | 3 in | 4 | 50.8 mm | 365 | 6.858000 mm |
| Angle | 3/8 in | 4.5 in | 16 | 95.25 mm | 368 | -0.508000 mm |
| Angle | 3/8 in | 6 in | 4 | 133.35 mm | 371 | -0.508000 mm |
| Starting frame | 3/8 in | 4 in | 4 | 76.2 mm | 367 | 6.858000 mm |
| Starting frame | 3/8 in | 4.5 in | 4 | 88.9 mm | 368 | 5.842000 mm |
| Starting frame | 1/2 in | 8 in | 4 | 177.8 mm | 407 | -1.164492 mm |

Twenty-four stacks have a negative worst-case catalog-box comparison: sixteen 3/8 × 4.5 in angle stacks at S = 95.25 mm (−0.508 mm), four 3/8 × 6 in angle stacks at S = 133.35 mm (−0.508 mm), and four 1/2 × 8 in starting stacks at S = 177.8 mm (−1.164492 mm). These flags compare the shortest listed bolt against the maximum matching catalog washer/nut stack; they do not prove that every delivered bolt fails. Nonnegative comparisons do not establish delivered fit. The modeled nut and washer comparison for the four 8 in bolts is a different basis and remains separate.

Model washer allocation is 176 at OD/ID/thickness 26.162/11.1125/2.6416 mm, sixteen at 25.4/11.1125/2.032 mm, and eight at 34.925/14.2875/3.175 mm. Keep one own washer at each end. The model uses 14.2875 mm hex flats for 3/8 in hardware and 22.225 mm for 1/2 in hardware; the catalog reference wrench sizes are 9/16 and 3/4 in. Catalog flats do not silently alter those model envelopes.

## Receiving and assignment

Retain the existing nominal lengths as the proposal. For each identified stack, record delivered underhead length L, seated receiver-plus-plate thickness S, head and nut washer thicknesses w_head/w_nut, nut height h_nut, matching UNC pitch p, and the actual gaged grip/thread/runout. The recorded project target is:

`L >= S + w_head + w_nut + h_nut + 2*p`

The matching nut must run freely to the required washer seat, with full nut seating and the actual threaded end through the nut. The two tip pitches come from this project's frozen geometry scenario. The conservative gaged-grip comparison is `G_actual <= S + w_head + w_nut`; catalog Lg is grip-gaging length, not an observed thread start. Lb and the saved body-to-farthest-bearing target identify separate body/thread-bearing questions; nominal length does not establish delivered shank or resistance.

Apply the cited ASME dimensions only to the applicable full-body hex-cap-screw definition. A generic hex-bolt listing is insufficient for that dimensional guarantee; the standard's dimensions are uncoated, and finished zinc dimensions need the applicable declared agreement. Record matching UNC nut identity, bolt/nut standards and lot information in the receiving record. Keep washer OD seating, ID/fillet/chamfer fit, thickness and material evidence separate. The 1/2 in catalog washer minimum opening is 0.547 in against a 0.550 in maximum bolt fillet, a 0.0762 mm diametral corner requiring actual seating information.

Allocate the 24 flagged stacks individually using measured dimensions. If the tip inequality or free nut/washer seating cannot be met, leave that stack unassigned. Longer stock or thinner washers remain unselected: each change needs its own seat, thread-bearing and applicable strength/geometry disposition, plus current tip/tool/removal clearance. No extra washer packing, cut bolt or full-thread substitute is specified. No torque, preload or friction capacity is supplied.

## Current access disposition

In the current saved model, the head sits on the negative axis side and the nut on the positive side. The CSV names each role, bearing/outboard face and nominal inward approach/outward removal vector in the saved global millimetre coordinates. Head/bolt withdrawal points opposite the positive axis; nut withdrawal follows it. These are axial directions, not a swept clearance or an assembly sequence.

All 200 positions/directions are **NOMINAL_ONLY** and all current tool and removal checks are **UNVERIFIED**. Sixteen absolute stack stations moved. None of the historical 140-side access passes or old tool allowances transfers, including at unchanged stations. Actual socket wall/depth, wrench swing, hand room and withdrawal paths are not supplied. At a nut, the saved tip protrusion is only the nominal free depth beyond the nut required inside a closed socket, before an unquantified tool allowance. Fill the tool and clearance cells only from an observed tool/part disposition; leave incompatible affected installations unassigned.

## Scope and reproduction

This table supplies planning and blank receiving records. It supplies no drilling diameter, machining tolerance, tightening instruction, complete joint resistance or fabrication/climbing release. The six-case numerical exceedances, unknown capacities and unverified rear-leg no-slip floor assumption stay in the [numerical packet](../fixed-floor-numerical-mvp-v1.json). The 66 Hillman panel/kicker screws retain their separate purchased policy; this table specifies no panel remedy.

Run from the repository root:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/hardware.py --check
```

The helper reads and hashes saved records and uses only named pinned scalar functions. `--write` reproduces these four generated companions; it performs no CAD query, tool sweep, candidate preparation or solve.
