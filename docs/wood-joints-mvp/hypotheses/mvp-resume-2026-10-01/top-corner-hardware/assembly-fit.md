# Conditional assembly and removal fit: top outer corners

**Status: conditional fit and procurement reconciliation only. No hardware is
selected; no physical release or complete-joint acceptance.** This note uses
the parent’s isolated [top-corner correction](../top-corner-correction.md),
its [proposal axes and straight approach results](../top-corner-correction/proposal.json),
the existing [catalog hardware inputs](hardware-inputs.json), and the existing
[contact geometry](../top-corner-contact-geometry.json). It also incorporates
the parent’s published [both-corner solve and component check](../top-corner-component-checks.md)
(commit `77ee4987`). It does not change the reviewed scene or parent-owned
frame integration. The upper-left service joint remains separate.

The parent subsequently added both left outer service-cleat clearances in
the same six-case frame; the latest results are at the start of the linked
component worksheet. Top-corner lateral-reference ratios become 0.7071 left
and 0.8035 right, and the washer strip demand becomes 179.161 MPa. The stack
dimensions, quantities and straight-approach evidence below are unchanged.
The saved fit arithmetic remains the prior two-corner scenario at commit
`77ee4987`; its exact worksheet and producer are retained beside the ignored
JSON as `fit-component-report.md.snapshot` and `fit-reconcile.py.snapshot`.
The maintained generator now refuses existing output and accepts `--output`
for a fresh evidence file.

The reproducible stack/access arithmetic and extracted current component
results are in
[fit-reconcile.py](fit-reconcile.py), with its generated
[fit-reconciliation.json](fit-reconciliation.json). Script verifies source
hashes for the correction and contact inputs before writing results. It also
records the hash of and reads the current component report. JSON files under
`hypotheses/` are ignored by repository rules; parent must explicitly retain
the generated data when integrating this packet.

## Joint layout and hardware counts

Each of two proposed solid 4×6 cleats has two side bolts and two rail bolts.
The receiver order below is bolt-head side to nut side. Both bolt families
have 177.8 mm (7 in) wood grip, excluding washers and nut.

| Connection per corner | Axes per corner | Receiver stack, head to nut | Conditional bolt | CAD bore envelope |
| --- | ---: | --- | --- | ---: |
| Cleat to side host | `side_1`, `side_2` | 88.9 mm base side + 88.9 mm cleat | 5/16-18 × 8 in, partial-thread cap screw | 9.0 mm |
| Cleat to top rail | `rail_1`, `rail_2` | 38.1 mm rail + 139.7 mm cleat | 1/4-20 × 8 in, partial-thread cap screw | 7.5 mm |

Two corners therefore need **4 side bolts, 4 rail bolts, 4 side nuts, 4 rail
nuts, 8 side washers and 8 rail washers**. Put one washer under each head and
one under each nut. The CAD diameters are analysis envelopes, not drill-bit
sizes. Do not transfer old holes to the proposed axes or enlarge an actual
hole from this note.

## Delivered stack and thread requirements

Catalog-bounded maximum stacks use the largest washer thickness and nut height
for each listed family. Under-head bolt length starts at the bearing face
under the head; bolt-head height is outside that length. Side and rail use
different washer and nut bounds.

| Requirement | 5/16 in side stack | 1/4 in rail stack |
| --- | ---: | ---: |
| Wood grip | 177.800 mm | 177.800 mm |
| Washer thickness, each; two washers maximum | 2.6416 mm; 5.2832 mm total | 2.0320 mm; 4.0640 mm total |
| Nut height maximum | 6.9342 mm | 5.7404 mm |
| Maximum under-head length to nut outer face | **190.0174 mm** | **187.6044 mm** |
| Declared three-pitch tip allowance | 4.2333 mm at 18 TPI | 3.8100 mm at 20 TPI |
| Physical under-head length for that allowance | **194.2507 mm minimum** | **191.4144 mm minimum** |
| Full-form male-thread interval required, measured from under-head | 181.0512–190.0174 mm | 180.3908–187.6044 mm |
| Minimum body end `LB` for NDS full-body scenario | **158.2166 mm** | **144.9070 mm** |

The three-pitch allowance is a declared fit scenario, not a universal installation
rule. Physical tip length alone does not prove full-form thread through the
active nut. The listed bolt products do not guarantee the actual full-form
thread interval or thread runout. Delivered screws must also have the stated
UNC diameter and pitch, usable body end at least the value above, and full-form
thread covering the nut interval. Nut active chamfers and internal thread class
are not supplied in these catalog observations.

The calculated full-body scenarios fit the geometry if their conditional
B18.2.1 thread profiles describe delivered parts. For the side pair, the
declared profile gives `LB=162.9918 mm` at the 7.82 in length sensitivity,
leaving at most 17.4498 mm threaded in the 88.9 mm nut-side cleat; the
per-member quarter-bearing limit is 22.225 mm. For rail bolts, the same
conditional length sensitivity gives `LB=166.8780 mm` and 12.954 mm threaded
in the 139.7 mm cleat; its limit is 34.925 mm. These comparisons count the
thread transition as threaded. The catalogs do not guarantee those `LB`
values, and the supplier warns actual threads may extend farther toward the
head. If delivered thread extends beyond the limits, this full-body scenario
does not apply; a separate root-diameter basis would be needed.

The [Bolt Depot Grade 8 side screw](https://boltdepot.com/Product-Details?product=28650)
lists 5/16-18 × 8 in, B18.2.1, partial thread, and an under-head length range
of 198.628–203.2 mm. At its listed minimum, the maximum side stack plus the
declared three-pitch allowance leaves **4.3773 mm** length margin. Its catalog
minimum thread length does not establish `LB` or full-form thread position.
The [K.L. Jack Grade 5 side screw](https://www.kljack.com/products/31c800hcs5z/)
lists the nominal 8 in length and 1.125 in thread length, but the recorded
catalog inputs contain no delivered under-head minimum or guaranteed thread
profile. For this scenario, delivered under-head length must be at least
194.2507 mm and the body/thread requirements above still apply.

The [Motion Grade 5 rail screw](https://www.motion.com/products/sku/11706127)
and [Lawson Grade 5 rail screw](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103)
are listed as nominal 8 in partial-thread cap screws. The recorded listings
give no exact delivered length minimum for either. A conditional B18.2.1
7.82 in length profile gives **7.2136 mm** margin over the maximum rail stack
plus three pitches, but is not a product guarantee. Require delivered
under-head length of at least 191.4144 mm and verify the actual thread interval
and `LB` separately.

## Current both-corner component evidence

The parent’s current coupled solve uses modeled relative clearances of
1.0625 mm for each side bolt and 1.15 mm for each rail bolt. These remain CAD
clearance scenarios; catalog inputs do not establish delivered clearance.
With Grade 5 tensile-yield input `Fyb=92 ksi` on both bolt families, the
reported adjusted individual lateral ratios are **0.7012 left** and
**0.7992 right** for this modeled-gap case. Maximum local rail/side movement
is 2.3447 mm left and 2.3227 mm right; maximum rotation is 0.8108° left and
0.9852° right. Parent’s preserved zero-gap right-corner individual reference
is 1.1593. Favorable modeled-gap ratios do not establish Grade 5 adequacy for
unspecified or tighter delivered fits. The steel input remains conditional,
not delivered-product evidence. These results select no bolt grade.

The parent’s washer radial-strip calculation gives a **178.403 MPa bending
stress demand, peaking at rail_1**, at catalog minimum washer thickness. It
uses an idealized uniform annulus and declared head/nut bearing circles of
10 mm at rails and 12 mm at sides. All sixteen maximum washer envelopes have
full modeled wood support in that report. Actual head/nut bearing footprints
and applicable washer-metal resistance basis remain unknown. The supplier
lists washers as low-carbon steel without numeric yield strength. The
178.403 MPa result is demand from a conditional model; it supplies no washer
capacity or pass/fail. Bolt grade contributes no washer property.

## Wrench sizes and access evidence

Catalog head and nut dimensions indicate these nominal wrench sizes:

| End | Catalog across-flats range | Nominal wrench/socket size |
| --- | ---: | ---: |
| 5/16 in side bolt head and nut | 0.489–0.500 in | 1/2 in |
| 1/4 in rail bolt head and nut | 0.428–0.438 in | 7/16 in |

Rail maximum across-flats is 0.0005 in above the nominal 7/16 in size. Actual
tool opening and delivered fastener dimensions must be compatible. The
existing proposal checked sixteen straight approach enclosures: one at each
end of each of eight bolts. Each enclosure is **25.4 mm diameter × 50 mm long**;
all have zero reported volume intersection with proposed wood/panels and the
other candidate shaft envelopes. Side head approaches come from the outer
side-host faces along ±X, with nut approaches from the opposite faces. Rail
head approaches follow the proposal’s ±(0, 0.6428, 0.7660) direction, with
nut approaches opposite. The exact axis records remain in the parent proposal.

This establishes only the recorded straight approach envelope. It does not
establish an actual socket’s outside diameter, wrench engagement, handle swing,
full-turn sweep, simultaneous head-and-nut counter-hold, or clearance to
installed heads, nuts, washers, retained frame bolts or hold hardware. The
50 mm probe also does not establish bolt insertion or full shaft extraction.

## Conditional assembly sequence

This sequence describes the isolated proposal only. It is suitable for a
future fit operation only after parent integration resolves remaining geometry
and joint criteria; it is not a build or climbing release. Do not force
misaligned holes, substitute a drill size from the CAD envelope, add preload,
or infer a torque from the fastener grade.

1. Support the side host, rail and cleat in their intended relative positions.
   Place cleat with its rail-touching face fixed as shown in the proposal and
   its full 139.7 mm section extending down the frame. Align proposed side and
   rail axes without forcing the members.
2. At each corner, place a side washer on the head side of `side_1`; insert the
   5/16 in bolt from the base-side exterior through the 88.9 mm side host and
   into the 88.9 mm cleat. Put the second washer and matching nut on the cleat
   side. Repeat for `side_2`. Receiver order is base side → cleat.
3. Place a rail washer on the head side of `rail_1`; insert the 1/4 in bolt
   from the rail exterior through the 38.1 mm rail and into the 139.7 mm
   cleat. Put the second washer and matching nut on the opposite cleat face.
   Repeat for `rail_2`. Receiver order is rail → cleat.
4. Hand-start all four nuts at each corner. Keep pairs seated without drawing
   misaligned members together. Verify the intended washer/nut order and the
   three-pitch tip scenario only after delivered length and full-form threads
   are established. No tightening torque or preload is specified here.
5. Stop before load-bearing use until parent resolves delivered fastener
   profiles, tool turning and withdrawal, washer transfer, and remaining
   simultaneous joint checks under the corrected frame demands.

The head end must be held while the nut end turns. Straight access exists in
the proposal’s limited model; turning both tools in place remains unproven.

## Conditional removal and member transport

For the top-corner connections, each cleat is attached by two side bolts and
two rail bolts, with nuts and washers. To separate a cleat from both adjoining
members, support the members, remove the two rail nuts and nut-side washers,
then withdraw `rail_1` and `rail_2` toward their head sides; remove the two
side nuts and washers, then withdraw `side_1` and `side_2` toward their head
sides. Retain hardware by axis and keep cleat orientation identified. To
release only a rail from the two cleats, the top-corner count is four rail
bolts; to release side hosts at both corners, it is four side bolts. These
counts exclude other frame connections elsewhere.

The through-bolted detail has removable fasteners in principle, but physical
member separation is not yet demonstrated. Reverse withdrawal needs roughly
one bolt length of clear travel at each head side (about 0.20 m), plus room to
hold and handle the bolt. The recorded 50 mm approach check did not test this
stroke. Installed-hardware collisions, actual shaft travel and member
transport sequence remain open. Do not treat the individual-member transport
goal as proven until those paths and all other member connections are resolved.

## Catalog quantities and observed price reconciliation

Prices below reuse the [2026-10-01 catalog observations](README.md). They are
listing estimates, not live quotes; tax and shipping are excluded. USD is
inferred from US storefronts showing `$`. Motion price was from an indexed
supplier page last crawled about 1.3 years before the observation; K.L. Jack
price was from an indexed supplier listing after direct access returned 403.

| Conditional package | Purchased lines for 2 corners | Surplus | Observed subtotal |
| --- | --- | ---: | ---: |
| Grade 5 side + Grade 5 Motion rail | 50 [K.L. Jack side bolts](https://www.kljack.com/products/31c800hcs5z/) $111.52; 4 [Grade 5 side nuts](https://boltdepot.com/Product-Details?product=2570) $0.44; 8 [side washers](https://boltdepot.com/Product-Details?product=2995) $0.48; 4 [Motion rail bolts](https://www.motion.com/products/sku/11706127) $13.92; 4 [rail nuts](https://boltdepot.com/Product-Details?product=2569) $0.28; 8 [rail washers](https://boltdepot.com/Product-Details?product=2994) $0.48 | 46 side bolts | **$127.12** |
| Grade 8 side + same Grade 5 Motion rail | 4 [Bolt Depot Grade 8 side bolts](https://boltdepot.com/Product-Details?product=28650) $12.20; 4 [Grade 8 side nuts](https://boltdepot.com/Product-Details?product=2583) $0.32; 8 side washers $0.48; 4 Motion rail bolts $13.92; 4 rail nuts $0.28; 8 rail washers $0.48 | None | **$27.68** |
| Grade 8 side + Lawson Grade 5 rail | Side bolts, nuts and washers plus rail nuts and washers | 21 of 25 Lawson rail bolts | **$13.76 plus unpriced Lawson pack** |

The first two package totals reconcile to four bolts of each diameter, eight
nuts and sixteen washers. They remain listing-cost scenarios. Current Grade 5
lateral ratios apply to the specified modeled-gap case; preserved zero-gap
right reference remains 1.1593, and actual delivered clearance is unknown.
Neither result selects Grade 5 or a stronger bolt. Complete joint acceptance
remains open. Washer entries are low-carbon steel with no numeric yield value
in the listing. Bolt grade, including Grade 8, supplies no washer strength.

The existing contact calculation’s nominal washer areas are also not carried
over as delivered washer capacity. Side catalog USS washer OD/ID is
22.0472–22.987 mm / 9.398–9.906 mm; rail washer OD/ID is
18.4658–19.0246 mm / 7.7978–8.3058 mm. The rail catalog nominal OD/ID
(18.6531/7.9375 mm) differs from the contact model’s 18.6436/8.0000 mm.
Catalog thickness, supported wood annulus, washer metal transfer and local
wood pressure remain distinct. Neither the existing contact result nor bolt
grade qualifies washer strength.

## Remaining evidence and blank shop record

No part, stock, bore, installed tool fit or transport path was observed for
this task. Keep `Actual` and `Disposition` empty until the stated item is
observed or supported by an accepted source. These fields are not passes.

| Item to resolve | Required evidence or bound | Actual | Disposition |
| --- | --- | --- | --- |
| Four side bolts | Delivered under-head length ≥194.2507 mm; `LB` ≥158.2166 mm; full-form thread covers 181.0512–190.0174 mm; diameter/pitch and nut engagement compatible |  |  |
| Four rail bolts | Delivered under-head length ≥191.4144 mm; `LB` ≥144.9070 mm; full-form thread covers 180.3908–187.6044 mm; diameter/pitch and nut engagement compatible |  |  |
| Nuts and washers | Delivered dimensions/threads, nut engagement, bearing faces and actual washer-supported wood footprint; washer metal transfer remains separate from bolt grade |  |  |
| Tool operation | Exact 1/2 in and 7/16 in tools clear installed hardware and complete turning/counter-hold motion |  |  |
| Bolt insertion and removal | Shaft insertion and roughly 0.20 m reverse withdrawal stroke clear at each axis |  |  |
| Assembly procedure | Compatible delivered stack; approved installation method and torque/preload basis, if required by parent’s accepted joint model |  |  |
| Joint and frame acceptance | Parent-owned complete wood/group and combined bolt resistance, washer transfer, applicable splitting/finished-section checks, and remaining adjustments |  |  |
| Member transport | Each intended member separates after releasing its connections, including connections outside these corners |  |  |

Until these items are resolved, the sequence remains conditional guidance for
the isolated top-corner proposal. No bolt strength, washer strength, actual
timber condition, cut, hole, hardware fit, physical inspection, floor support
or climber rating is asserted here.
