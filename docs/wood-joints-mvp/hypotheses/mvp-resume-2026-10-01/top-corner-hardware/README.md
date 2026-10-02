# Hardware for the isolated 4×6 top-corner proposal

**Observed on 2026-10-01. Status: catalog options and conditional inputs;
no hardware, joint, or release accepted.** This packet covers four 5/16-18
side bolts and four 1/4-20 rail bolts, all nominally 8 inches long with
177.8 mm wood grip. [Machine inputs](hardware-inputs.json) bind the eight
axes to the [proposal](../top-corner-correction/proposal.json). Parent owns
whole-frame integration; the upper-left service joint remains separate.

## Concrete options and cost

Use **Bolt Depot 28650, SAE J429 Grade 8**, as the ordinary-stock side-bolt
option for the next conditional calculation. Its listing explicitly identifies
B18.2.1, partial thread, and the exact size. Pair it with J995 Grade 8 nuts
and USS washers below. Retain **Lawson FA21103** as the source-backed rail
bolt option; its price is hidden. These parts have compatible nominal sizes
and thread series; exact thread profiles and complete installed fit remain
unresolved. Prices exclude shipping and tax. USD denotes the US storefront
currency; the pages display `$`, without an explicit ISO currency field.

| Duty | Exact catalog item | Needed / listed purchase quantity | Observed price and extended cost |
| --- | --- | ---: | --- |
| Side bolts, preferred Grade 8 scenario | [Bolt Depot 28650](https://boltdepot.com/Product-Details?product=28650), 5/16-18 × 8, yellow zinc | 4 / 4 individual pieces | USD 3.05 each; **12.20**. A 25-piece bag is 54.50 and is unnecessary for four. |
| Side nuts, Grade 8 | [Bolt Depot 2583](https://boltdepot.com/Product-Details?product=2583), 5/16-18 | 4 / 4 | USD 0.08 each; **0.32** |
| Side washers, low-carbon steel | [Bolt Depot 2995](https://boltdepot.com/Product-Details?product=2995), 5/16 USS, zinc | 8 / 8 | USD 0.06 each; **0.48** |
| Rail bolts, retained source lead | [Lawson FA21103](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103), Grade 5, bright zinc | 4 / one pack of 25; 21 surplus | Login required; **unknown** |
| Rail nuts, Grade 5 | [Bolt Depot 2569](https://boltdepot.com/Product-Details?product=2569), 1/4-20 | 4 / 4 | USD 0.07 each; **0.28** |
| Rail washers, low-carbon steel | [Bolt Depot 2994](https://boltdepot.com/Product-Details?product=2994), 1/4 USS, zinc | 8 / 8 | USD 0.06 each; **0.48** |

The Lawson combination is **USD 13.76 plus one unpriced 25-bolt pack**.
A nominally equivalent priced rail alternative is
[Motion MI 11706127 / manufacturer 79458915](https://www.motion.com/products/sku/11706127):
1/4-20 UNC × 8, partial thread, Grade 5, zinc, B18.2.1/J429. Its indexed
supplier page lists USD 3.48 each, so four add 13.92 and give an **eight-stack
listing subtotal of USD 27.68**, with no surplus. Motion's indexed page was
crawled about 1.3 years earlier; direct retrieval returned 403. This is a
recorded listing estimate, not a current stock or checkout quotation.

The Grade 5 side alternative is
[K.L. Jack 31C800HCS5Z / supplier 31128CH50](https://www.kljack.com/products/31c800hcs5z/):
the exact page explicitly lists J429, B18.2.1, UNC Class 2A, partial thread,
1-1/8-inch thread length, and 92/120/85 ksi yield/tensile/proof stress.
Its indexed product price is **USD 111.52 per box of 50**: four required,
46 surplus. Four [Grade 5 nuts 2570](https://boltdepot.com/Product-Details?product=2570)
cost 0.44. With the same washers and four Motion rail bolts, the package
subtotal is **USD 127.12**. Direct K.L. Jack retrieval returned 403; an older
category result also shows 105.21 per 50. Neither is a live quote. The
original [Grainger Canada EBP22TC01 / U01200.031.0800](https://www.grainger.ca/en/product/CAPSCREW-GR-5-ZP-UNC-5-16-18X8--5-PK/p/EBP22TC01)
is another conforming Grade 5 size/standard lead, five per pack; its readable
page says unavailable and supplies no price. No CAD price is invented.

## Steel property and test basis

[STS's J429 2014-05 table](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j429-technical-data)
and [Bolt Depot's own strength table](https://boltdepot.com/fastener-information/Materials-and-Grades/Bolt-Grade-Chart)
give these steel minima for the relevant diameter bands:

| Conditional conforming material | Tensile yield Fy | Ultimate Fu | Proof stress Fp |
| --- | ---: | ---: | ---: |
| J429 Grade 5, 1/4–1 inch | 92 ksi | 120 ksi | 85 ksi |
| J429 Grade 8, 1/4–1-1/2 inches | 130 ksi | 150 ksi | 120 ksi |

The supplier table identifies tensile yield at 0.2% permanent set.
[SAE's standard record](https://saemobilus.sae.org/standards/j429_201405-mechanical-material-requirements-externally-threaded-fasteners)
identifies the material/mechanical specification; the exact listings claim
J429 conformance, without providing lot results or a test-method edition.
[NDS-2024 §12.3.6.2](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf),
printed p.95, permits an ASTM F1575 bending-yield basis or an
[ASTM F606 tensile-yield basis](https://store.astm.org/standards/f606).
[ASTM F1575/F1575M-24](https://store.astm.org/f1575_f1575m-24.html) describes
the static bending route. No test observation is supplied here.

The proposed analysis input is **conditional Fyb = 130 ksi**, using the
NDS tensile-yield route and explicitly assuming J429 Grade 8 material with
the applicable F606 yield basis. Parent owns adoption of that method/input;
the JSON keeps adopted Fyb null and formal product verification remaining.
Grade 5's analogous conditional input is 92 ksi. The prior **106 ksi Grade 5
estimate remains unadopted**.

The parent reports the corrected whole frame passes six cases under its
recorded panel assumptions. Its redistributed side-2 peaks are **1304.116 N,
A12-left**, and **1507.523 N, K12-rear**. Reused six-mode reference ratios
reported by the parent are:

| Steel input | Left | Right | Scope |
| --- | ---: | ---: | --- |
| Grade 5 hypothetical Fyb 106 ksi | 0.934 | 1.080 | Unadopted estimate; right exceeds one |
| Explicit Grade 5 tensile yield 92 ksi | 1.003 | 1.159 | Does not hold the redistributed side demands |
| Conditional Grade 8 tensile yield 130 ksi | 0.844 | 0.975 | Below one before other adjustments; no complete-joint acceptance |

These are parent-reported calculations, not new runs in this packet. The
earlier isolated right-corner requirement of 91.746 ksi and 0.99862 ratio at
92 ksi remain historical inputs; their 0.14% margin does not describe the
redistributed frame. Parent retains full joint, washer and splitting checks.
Neither a grade label nor a higher steel minimum is a complete-joint pass.
Conditional calculation does not require a new physical qualification test.
No generic 46 psi property or historical candidate pass is transferred.

The [J995 supplier table](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j995-technical-data)
supports finished-hex UNC nut proof-stress scenarios of 150 ksi for Grade 8
and 120 ksi for Grade 5. Bolt Depot nuts identify J995/B18.2.2; internal
thread class and active chamfers are not listed. The USS washers identify
low-carbon steel and B18.21.1, **without numeric Fy**. Bolt-grade properties
do not apply to them; supported wood annulus and washer metal transfer remain
separate checks.

## Dimensions, full body, and engagement

Side bolt heads are 1/2 inch across flats and 0.195–0.211 inch high; rail
heads are nominally 7/16 inch across flats and 5/32 inch high. Side nuts are
0.258–0.273 inch high; rail nuts are 0.212–0.226 inch high. Side washers are
ID 0.370–0.390, OD 0.868–0.905, thickness 0.064–0.104 inch; rail washers
are ID 0.307–0.327, OD 0.727–0.749, thickness 0.051–0.080 inch. Side
washer nominal OD/ID are 7/8 and 3/8 inch. These are catalog dimensions.

NDS §12.3.7.2 permits full-body D only when threaded bearing is **≤ one
quarter of the bearing length in each member holding threads**. Count all
wood after declared body end LB as threaded, including transition. Do not
compare threaded length with one quarter of the combined 177.8 mm grip.
The [existing B18.2.1 correction](../../../bolt-dimension-source-correction.md)
distinguishes LB from grip gage LG and full-form thread engagement.
The [supplier Table 6 reproduction](https://www.nickel-systems.com/wp-content/uploads/2025/01/Hex-Head-Cap-Screws-Dimensioning-Table.pdf)
agrees with the inspected standard: over-six-inch LT is 1.125 inch for
5/16 and 1 inch for 1/4; transition Y is 0.278 and 0.250 inch respectively.
Using `LG = Lnom − LT; LB = LG − Y` gives the explicit profiles below.
They are **conditional profile scenarios**, not guaranteed delivered bodies;
[Bolt Depot warns that threads can exceed the listed minimum](https://boltdepot.com/fastener-information/Bolts/US-Thread-Length).

| Family, head → nut receiver order | Declared LB / LG, mm | Worst threaded wood at maximum head washer | Quarter-bearing limit | Required LB for this order |
| --- | ---: | ---: | ---: | ---: |
| Side: 88.9 mm side host → 88.9 mm cleat | 167.5638 / 174.625 | 12.8778 mm in cleat, 14.49%; none in host | 22.225 mm | ≥158.2166 mm |
| Rail: 38.1 mm rail → 139.7 mm cleat | 171.450 / 177.800 | 8.3820 mm in cleat, 6.00%; none in rail | 34.925 mm | ≥144.9070 mm |

These declared profiles meet the full-body exception. Applying the same
declared LT/Y at the −0.18-inch length minimum gives LB 162.9918 mm side
and 166.8780 mm rail, with 19.63% and 9.27% threaded cleat bearing. Those
conditional profiles also meet the limit; longer-than-minimum threads remain
unbounded by the listing. A fully threaded
[Grade 5 tap bolt](https://www.mfsupply.com/5_16_18_X_8_Hex_Tap_Bolt_Steel_Zinc_p/hh51cx8g5-tap.htm)
does not: it has 100% threaded bearing and is incompatible with this
full-body calculation. Root-diameter resistance would require its own input.

An eight-inch B18.2.1 length scenario has a minimum tip coordinate of
198.628 mm (−0.18 inch). At maximum washers/nut, the side stack ends at
190.0174 mm and the rail stack at 187.6044 mm. A declared three-pitch tip
allowance leaves respectively **4.3773 and 7.2136 mm** length margin. That
allowance is a scenario, not a new universal installation rule. Full-form
male threads must separately cover the nut intervals: conservative envelopes
**181.0512–190.0174 mm side**, **180.3908–187.6044 mm rail**, measured
from under the head. Minimum thread length and LG alone do not prove this.
The side nut maximum is 0.1873 mm taller than the correction producer's
nominal side-nut assumption; parent should use the catalog maximum for fit.

## Remaining fit gaps and active evidence

Parent still needs an explicit usable body/full-form-thread profile for the
chosen SKU scenario; actual head/nut bearing footprints and washer strength;
installed turning, withdrawal, and nearby hardware clearance; and remaining
joint adjustments and strength under the redistributed actions. Full-thread
products, mismatched pitch,
and the contradictory Zoro G2613856 rail listing (8-inch fastener but
3-1/4-inch overall-length fields) cannot silently substitute. Washer numeric
yield is unknown. CAD holes remain occupancy envelopes, not bit instructions.
The rail washer catalog nominal OD/ID, 18.653125/7.9375 mm, also differs
slightly from the contact model's 18.6436/8.0 mm annulus. Catalog tolerance
and thickness ranges do not inherit the nominal-annulus pressure or stiffness
results.

Keep this packet active for integration. Preserve all older sources and the
[2026-09-30 hardware/material packet](../../hardware-material-specification-2026-09-30/README.md).
The existing `hypotheses/.gitignore` ignores `*.json`; the machine file exists
on disk and needs explicit retention when the parent integrates this packet.
The [local contact results](../top-corner-contact-checks.md) retain historical
conditional original-frame demands, including the unresolved panel withdrawal
assumption. The parent's corrected-frame report supersedes those lateral
demands for integration and retains its recorded panel assumptions.
This task changed only these two new files. No source downloads, tests, native
solves, review rounds, other agents, physical work, purchases, vendor contacts,
staging, commits, or archive/prune operations were performed.
