# Quarter-inch rail washer material and bearing-face product basis

**Checked October 2, 2026, America/Denver. Finite source investigation complete;
washer material resistance and the installed bearing footprint remain unresolved.**

The existing catalog routes establish washer dimensions, a Grade 5 bolt
specification, and a separate Grade 5 nut proof specification. They do not
establish a minimum yield stress for either existing rail washer, or guarantee
the model's concentric, flat, 10 mm head/nut contact circle. No exact catalog
combination found in this bounded investigation supplies a purchasing resistance
basis for the washer under the recorded tension and moment. The missing facts
are identified below; this is not a claim that any physical product failed.

The investigation starts with [hardware engagement](../assembly-package/hardware-engagement.md),
the [top-corner catalog packet](../top-corner-hardware/README.md),
the [bearing-face investigation](../assembly-package/bearing-face-basis.md),
the [washer footprint bounds](upper-right-washer-contact-bounds.md), and the
earlier [ordinary nut/washer property basis](../../../current-ordinary-nut-washer-property-basis.md).
Their product identities and evidence limits are retained. Source links and
saved-byte hashes appear below. There was no supplier contact, purchase,
mechanics execution, CAD/frame run, washer refinement, or hardware/model adoption.

## Scope and unchanged analytical witness

The four corrected top rails use Lawson/FalconGrip `FA21103` as the existing
1/4-20 × 8 in Grade 5 partial-thread cap-screw lead, with Motion `11706127`
/ manufacturer `79458915` as the already-recorded alternative. Their nut and
washer catalog routes are Bolt Depot `2569` and `2994`. The broader quarter-inch
assembly route uses K.L. Jack `25CNFH5Z` nuts and `25NWUS` washers. These are
separate exact product routes; matching nominal sizes do not transfer material
properties or delivered-part evidence between suppliers.

The [upper-right free-edge packet](upper-right-washer-edge.md) records the
unchanged witness `k12-right/top_outer/clip_single_top_right_2/rail_1/host`:
simultaneous tension **709.052842 N** and end moment magnitude
**2292.108528 Nmm (2.292108528 Nm)**. Its finer approximation gives an elastic
plate stress proxy of **512.232 MPa**, using washer OD **18.4658 mm**, ID
**8.3058 mm**, thickness **1.2954 mm**, and a concentric 10 mm pressing circle.
These are respectively catalog minimum OD, maximum ID, minimum thickness,
and a hypothetical contact profile. They are not measured product dimensions.

The proxy belongs to that packet's fixed elastic/contact hypotheses. It is not
an available resistance, a measured product stress, or a manufacturer failure
load. The packet's 250 MPa yield comparison remains hypothetical. Neither
250 MPa nor 512.232 MPa is assigned to a purchased washer here. No other load
state is combined with this witness and no washer calculation is repeated.

## Defensible facts for the existing products

| Component and exact catalog route | Published facts | Material/resistance limit |
| --- | --- | --- |
| Rail washer, [Bolt Depot 2994](https://boltdepot.com/Product-Details?product=2994) | Zinc-plated low-carbon steel USS washer; ASME B18.21.1. ID 0.307–0.327 in (7.7978–8.3058 mm), OD 0.727–0.749 in (18.4658–19.0246 mm), thickness 0.051–0.080 in (1.2954–2.0320 mm). | No numerical yield, tensile strength, hardness, steel grade/UNS designation, or heat condition is stated. Its dimensional standard does not establish a numerical yield input from the available evidence. |
| Other quarter-inch washer route, [K.L. Jack 25NWUS](https://www.kljack.com/products/25nwus/) | Plain/light-oil low-carbon steel; ASME B18.21.1 Type A Wide, regular series. Nominal ID 0.312 in, OD 47/64 in, thickness 1/16 in; thickness limits 0.051–0.080 in. The existing project packet supplies the Type A Wide ID/OD envelope above. | No numerical yield, tensile strength, hardness, or named steel grade/condition is published. The listing does not independently print the full ID/OD tolerance range, so those bounds retain their existing conditional standard attribution. |
| Rail bolt, [Lawson FA21103](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103) | Carbon-steel Grade 5, bright zinc, partial thread, 1/4-20 × 8 in, UNR form, nominal 7/16 in across flats and 5/32 in head height. The exact page states SAE J429 material/mechanical conformance, ANSI B18.2.1 dimensions, and 120,000 psi minimum tensile strength. | This supplies a conditional Grade 5 bolt material route. The exact page gives no hardness range or under-head flat contact diameter/profile. Bolt material requirements do not apply to a separate washer. |
| Existing rail-bolt alternative, [Motion 11706127 / 79458915](https://www.motion.com/products/sku/11706127) | Indexed exact listing identifies partial-thread 1/4-20 UNC × 8 in Grade 5 zinc-plated steel, 7/16 in hex, ASME B18.2.1 and SAE J429. | The browser labels this indexed source as crawled about 1.3 years earlier. It is preserved catalog evidence, without a current availability claim. No exact head-bearing profile, numerical hardness, or new product selection follows. |
| Rail nut, [Bolt Depot 2569](https://boltdepot.com/Product-Details?product=2569) | Tempered medium-carbon steel, Grade 5, zinc plated, 1/4-20; ASME B18.2.2 and SAE J995. Across flats 0.428–0.438 in (10.8712–11.1252 mm); height 0.212–0.226 in (5.3848–5.7404 mm). | No exact flat bearing-circle diameter, countersink profile, face-style declaration, or numerical yield/hardness is listed. Flats and nut height describe its envelope, not the installed pressure-bearing area. |
| Other quarter-inch nut route, [K.L. Jack 25CNFH5Z / AFH5Z0250C](https://www.kljack.com/products/25cnfh5z/) | Grade 5 finished hex nut, ASME B18.2.2, SAE J995 Grade 5, ASME B1.1 UNC Class 2B, ASTM F1941 Fe/Zn finish; nominal 7/16 in hex and 7/32 in thickness. | The listing does not specify the actual end-face/countersink profile or numerical yield/hardness. Its 2B class does not prove installed thread engagement or seating. |

For the quarter-inch **bolt only**, the existing J429 basis is corroborated by
[Bolt Depot's own bolt strength table](https://boltdepot.com/fastener-information/Materials-and-Grades/Bolt-Grade-Chart):
the Grade 5, 1/4–1 in band has **92 ksi minimum yield, 120 ksi minimum tensile,
and 85 ksi proof stress**. Lawson's explicit J429 callout supplies the
exact-item catalog link to this conditional specification. These are
conformance assumptions and specified minima, not tests of delivered bolts
or a local head-bearing resistance. No numerical bolt hardness is adopted
from an unspecified material description.

For the **finished hex nut only**, the
[STS J995 supplier technical table](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j995-technical-data)
reproduces **120 ksi proof-load stress** for Grade 5 UNC nuts in the 1/4–1 in
band and **0.0318 in²** tensile stress area for 1/4-20. The already-recorded
conditional proof reference is **3,816 lbf**. Its hardness table gives Grade 5
nuts **32 HRC maximum**, without a numerical minimum. This is a supplier
reproduction of the specification, not a retrieved full SAE standard or a
lot certificate. Nut proof and maximum hardness do not supply nut tensile
yield, a local bearing-pressure capacity, or washer yield; proof also does
not establish stripping resistance for incomplete engagement.

## Why generic washer standards do not close the material gap

The [official ASME B18.21.1 record](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers)
identifies B18.21.1-2009 (R2016) and its consolidation of the older plain-washer
B18.22.1 standard. The record covers several washer types. Its general
description of physical properties and tests is not a specific numerical
yield requirement for either existing Type A Wide product. No full plain-washer
material clause or numerical yield table is represented as newly inspected.

[ASTM's F844-19(2024) public record](https://store.astm.org/f0844-19r24.html)
covers unhardened general-use steel washers and defaults their dimensions to
B18.21.1 Type A, Table 11. It publishes no numerical yield minimum.
[Portland Bolt's own F844 explanation](https://www.portlandbolt.com/technical/faqs/f844-standard-washer-certifications/)
reproduces the clauses that leave chemical composition and mechanical
requirements unspecified unless separately requested. That manufacturer
explanation was written in 2012 and modified in 2014; it is not a newly
authenticated copy of the 2024-reapproved standard. Neither `2994` nor
`25NWUS` claims F844 on its checked product page. Thus F844 supplies neither
an exact-product conformity chain nor a default strength minimum here.

The existing analysis-only hardened lead,
[K.L. Jack 25NWUS8Z / U0014ZD](https://www.kljack.com/products/25nwus8z/),
does publish quenched-and-tempered steel, ASTM F436 material requirements,
and **38–45 HRC core hardness**. Its listed OD lower bound is **0.729 in**,
which differs from the existing ordinary washer's 0.727 in; its ID and
thickness ranges are 0.307–0.327 and 0.051–0.080 in. The
[official F436/F436M-24 record](https://store.astm.org/f0436_f0436m-24.html)
identifies hardness and dimensional requirements, but its public text and
this exact listing provide no numerical yield minimum. This confirms a
defensible hardness/material-class fact for an alternative, without making
a hardness-to-yield conversion or treating its “Grade 8” merchandising label
as J429 bolt strength. No substitution or stronger-washer resistance is adopted.

The earlier [washer yield options](../../../washer-property-options/ordinary-washer-yield-options.md)
and [orderable options](../../../washer-property-options/ordinary-washer-orderable-options-2026-09-25.md)
already screen other material families. They do not assign yield to the
existing products. Repeating that supplier search or a material sweep is not
needed to answer this task's exact-product question.

## What the 10 mm circle is grounded in

**Head.** The existing direct inspection of the pinned B18.2.1-2012 copy,
reported in the [bearing-face basis](../assembly-package/bearing-face-basis.md)
and [footprint source review](../../washer-bearing-footprint-inputs-2026-10-01/source-review.md),
gives Table 6 quarter-inch across-flats limits of 0.428–0.438 in. Section 4.3
makes the washer-face diameter equal to the maximum across flats with a
negative 10% tolerance. The resulting **10.01268–11.1252 mm** circular
dimension is measured **0.004 in (0.1016 mm) toward the head from the bearing
plane**. Washer-face thickness is 0.015–0.025 in (0.381–0.635 mm).
These are conditional standard dimensions for a conforming cap screw,
not an inferred circular footprint from the hex envelope.

The specified offset plane leaves the actual outer radius/transition at the
flat bearing plane unestablished by the reused inspection. The gage-circle
minimum exceeds 10 mm by only **0.01268 mm** at its own plane. It does not
guarantee a centered 10 mm flat annulus at the contact plane. The existing
long-screw fillet discussion also distinguishes the Style 1 maximum radius
0.025 in and Style 2 maximum transition diameter 0.300 in (7.6200 mm)
for quarter-inch screws; the chosen underside profile and bore alignment
still matter. The [official B18.2.1 record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
confirms the 2012 (R2021) edition but does not expose these numerical clauses.
This note reuses the previous direct inspection and verifies its file hash;
it does not claim a new full-PDF or rendered-figure review.

**Nut.** The prior [source review](../../washer-bearing-footprint-inputs-2026-10-01/source-review.md)
and [parent disposition](../../washer-bearing-footprint-inputs-2026-10-01/parent-review.md)
already record B18.2.2-2022 clause information. Their conditional default is a
double-chamfered quarter-inch nut: §3.3.2 gives a chamfer-circle diameter of
maximum across flats minus at most 10%, again **10.01268–11.1252 mm**;
§3.4 gives a maximum countersink diameter of **0.280 in (7.112 mm)**.
The countersink is smaller than the washer's minimum 7.7978 mm bore in a
concentric interpretation. These facts provide a plausible conditional nut
end-face annulus; the nut's outer boundary is distinct from the head's
offset gage measurement.

Their provenance remains limited: the worker used indexed original-standard
text on a third-party host, and the parent checked a third-party full-text
transcription. Neither record authenticates a complete standard PDF/figure.
The [official B18.2.2-2022 record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts)
confirms the edition but exposes no numerical bearing-face table. The exact
product pages newly checked here confirm flats, height and standard identity;
they add no bearing-circle guarantee. The conditional nut-clause evidence
must therefore remain visible without being promoted to an authenticated
exact-product contact guarantee.

The same parent disposition records a **0.222504 mm maximum radial offset**
under its interpretation of the nut's 4%-of-maximum-flats diametrical
true-position zone, and **0.015 in (0.381 mm) FIM** bearing-face runout for
the relevant proof-stress band. These are allowed geometry, not a prescribed
installed tilt or uniform pressure field. A circle about the nut body is
not automatically centered on the bolt/thread axis.

**Washer play.** The existing [footprint bounds](upper-right-washer-contact-bounds.md)
already calculate **0.97790 mm** washer-only radial play using maximum
8.3058 mm washer ID and nominal 6.3500 mm shank. Enclosing that bore at that
offset would require a **10.2616 mm** circle in that limited geometric
comparison. The model's 10 mm circle does not guarantee such enclosure.
This comparison excludes shank undersize, nut eccentricity and face runout;
it is not evidence of the actual installed offset or failed seating.

Accordingly, the 10 mm footprint has a nearby conditional standard-size
motivation, but remains a **declared concentric flat-face scenario**, rather
than a guaranteed footprint of both existing products. The washer opening
has no metal and must receive no contact-area credit. These distinctions
leave the previously recorded prescriptive washer-detailing route separate
from the analytical bending/contact investigation; this note adds no blanket
yield-test or external-sign-off prerequisite to that route.

## Exact missing facts and finite disposition

| Required input for an exact-product analytical resistance claim | Present disposition |
| --- | --- |
| A numerical minimum yield/proof stress of the finished `2994` or `25NWUS` washer, or an explicitly applicable steel grade, condition and specification edition that guarantees that value at its thickness. | Missing. The product must be tied to that material statement. Low-carbon wording, the bolt's Grade 5 requirements, a hardness value alone, or an unbound sheet/bar datasheet cannot supply it. |
| The actual flat under-head outer/inner bearing profile and transition to the gage plane, with centering/runout bounds applicable to `FA21103` or the existing Motion alternative. | Missing from the exact listings and reused standard inspection. The offset gage circle is not this profile. |
| The installed nut bearing-face style, outer boundary, countersink and alignment/runout envelope for `2569` or `25CNFH5Z`, supported by applicable authoritative clauses or exact-item dimensions. | Conditional historical clause inputs exist; authenticated numerical standard/figure evidence and an exact-product profile declaration remain absent. Installed concentric full-annulus contact is not guaranteed. |
| A contact interpretation compatible with the real washer bore, permitted centering and the simultaneous tension/moment, plus an applicable washer resistance method. | Parent-owned joint work remains open. A new yield fact would fill the material input; it would not validate the existing stress proxy, contact law or complete-joint capacity. |

The finite sourcing task ends with those gaps. No exact purchasing resistance
basis can be issued from the checked existing products. The recorded 512.232 MPa
proxy supplies a benchmark for its unchanged hypothetical elastic branch;
turning that number into a procurement minimum or product capacity would
require a supported interpretation of the joint/contact model. The parent
can use the source facts above when deciding its next bounded step. There is
no supplier inquiry, new order, hardware correction, or further washer run
authorized or performed by this note.

## Receipts and reproducibility

All new receipts are in ignored
[`rawlocal/washer-product-basis/`](rawlocal/washer-product-basis/).
Direct HTTP retrieval of the Bolt Depot and K.L. Jack product pages returned
403; their facts were available through the browser's primary-site text.
The browser's K.L. Jack results were indexed about one to three months earlier;
Motion's result was older as described above. The saved `.browser.txt` files
are extracted page text/excerpts with retrieval provenance, **not original
HTML or manufacturer certificates**. Official ASME/ASTM records and the
Portland Bolt page were saved as original HTTP response bytes. The attempted
Fastenal dimensional-source fetch added no usable evidence and is recorded
only as a retrieval failure. UTC receipt timestamps fall on October 3,
consistent with the October 2 local check date.

The complete [receipt manifest](rawlocal/washer-product-basis/receipt-manifest.json)
records every saved receipt's URL, representation, byte size and SHA-256,
plus all reused source pins. Its SHA-256 is
`1db827a8a1e81283b6f10d9b980f9dacc1d60a5265ab46be0c21c3151be1cd41`.
Hashes identify the bytes read; they do not authenticate product conformity.
The existing 2.11 MB Lawson HTML and 1.11 MB B18.2.1 PDF are referenced in
place rather than copied. The new raw receipt set totals **936,625 bytes**.

| Key primary receipt under `rawlocal/washer-product-basis/` | SHA-256 |
| --- | --- |
| `boltdepot-2994.browser.txt` | `0ebc7d54a993e927138054547746597e3c8c9456223b82fb9f36284541592cfd` |
| `kljack-25nwus.browser.txt` | `975fea5712067dabcbb5a161a77b7a549935f17e10885356380225fd3846b30b` |
| `boltdepot-2569.browser.txt` | `a234c9afb3841e4a703f2e485c09f23d8a8a225f3c176823a9657b7941f2914b` |
| `kljack-25cnfh5z.browser.txt` | `6274730a6569b69234a3274d6393238a1144784bdf71e82602a45e39a5ed7a13` |
| `lawson-fa21103.browser.txt` | `2539f05e259c349c78dc41099600cba79cc13d2849d34b8db7a63fb32f11eeeb` |
| `motion-11706127.browser.txt` | `f573f86913c6b8685ecba1821aa3ff479dc77d69cd07fa43655310e11fb86a0b` |
| `astm-f844-19r24.html` | `6e367dd6054fc0c4971ea68774f76cca98fe1c9667e074552f945763d4fad450` |
| `portlandbolt-f844-certifications.html` | `551079d5df82d8aa946239ba054f2e16a982fda4139ab0d5246d85c14c10cf7f` |
| `kljack-25nwus8z.browser.txt` | `36585e005126a9a681bb052c89ec9c80093bc2a4d6373d50586c2269141bd220` |

| Reused evidence, without copying or modification | SHA-256 at this investigation |
| --- | --- |
| `../assembly-package/hardware-engagement.md` | `76555095149ee70fa7312afa29d2d3e72870cf165f7bc271a437f8c6381066ee` |
| `../top-corner-hardware/hardware-inputs.json` | `a2110d7580621dee92017403345f21c458729612547ac1f7b2eb8068d0c723c7` |
| `upper-right-washer-contact-bounds.md` | `3602bc873eb5f50a740962744f839d130e561e49b197b106b01f93323b03fa1b` |
| `upper-right-washer-edge.md` | `9ac8a73aea1963e7dcc97412069e040801a8976ed2ab234a7a57a70c08e842bf` |
| Existing Lawson HTML in `../../hardware-material-specification-2026-09-30/fastener-source/lawson_fa21103.html` | `f55332f347024e3e73e3334e8e996bb5b6cdfc91bd8fdec6d62395983ec9d0d3` |
| `/tmp/thread-gage-functional-fit/ASME-B18.2.1-2012-mirror.pdf` | `4c7bcb75223b7e89fc27f132bc44e8b422ba672c97f7803259a24fab6bd99ba0` |

The note and its receipts remain active evidence for the parent's material
and footprint decisions. No existing raw run or source is nominated for
pruning, and no shared ledger, model, staging area or commit was changed by
this worker. Evidence handling was limited to reading existing sources,
recording primary-source receipts and checking their hashes; no software
tests or review loop were run.
