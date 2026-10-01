# T06 steel-direct source applicability screen — attempt02

**Reviewed 2026-09-28.** This is a read-only, source-bound review of whether
primary metal-design sources document a route for a through-bolt carrying
simultaneous tension, shear, and bending in the current solid-timber joint.
It does not adopt a method, compute capacity, select hardware, or change a
criterion, candidate, geometry, solver state, or release status. No solver or
native run was performed.

## Finding

The attempt01 conclusion needs a narrower description. ANSI/AWC NDS-2024
§11.2.3 requires metal parts to be designed under applicable metal procedures
for tension, shear, metal-on-metal bearing, bending, and buckling, and points
to References 39–41. The pinned official AWC Chapter 11 text does not itself
name an equation or decide which metal procedure applies to a timber through-
bolt. The official NDS reference-list pages were not available for review in
this search, so this packet does not assert the titles of References 39–41.

There is a **documented, AISC-published N+V+M engineering approach for a
different connection configuration**. The February 2024 *Modern Steel
Construction* article “Thermal Breaks in Structural Steel” describes
steel-to-steel end-plate joints with a thermal-break pad (TBP): it models bolt
shear as single-curvature bolt bending, gives the bolt moment as shear times
pad thickness, points to AISC Specification §J4.5 for that bending check,
and points to Chapter H combined-force equations for the bolt's shear,
tension, and moment. The same article says formal codes do not provide TBP
design guidance and says the cited RCSC commentary excludes TBP connections
and describes them as not intended for primary load-resisting systems. It is
a professional practice article, not a normative standard, and it addresses
steel end plates separated by a pad, not steel bolts bearing through timber.

The article's references list “AISC (2022) ... ANSI/AISC 360-16,” an edition
identifier mismatch. AISC's current-standard materials identify ANSI/AISC
360-22 as the current specification on the review date; AISC 360-27 was open
for public review, not issued as the current standard. I could not read the
full current 360-22 provisions in this search. AISC's official 2022 design
example does demonstrate §J3.8's **bolt tension-plus-shear** interaction in a
steel bearing-type connection. That example does not demonstrate bending.
The available sources therefore show a specialized published N+V+M approach,
but do not establish that its section model, interaction equations, or
resistance basis apply to a through-bolt in this timber joint.

This finding preserves the distinctions in attempt01:

- NDS lateral-yield design and the Fyb property/test route remain lateral
  wood-connection inputs; they do not supply direct axial/shear/bending
  resistance for this bolt.
- ASTM fastener test/property procedures and SAE/ASTM product specifications
  identify or test material properties. They do not, by themselves, provide
  a connection-level interaction rule.
- First-yield stress arithmetic (including a von Mises comparison) is a
  material-level reference only. It is not a design resistance or a timber
  joint acceptance check.

The source-bounded conclusion is **applicability gap, not absolute method
nonexistence**: a steel thermal-break article documents one N+V+M approach,
but current evidence does not establish an applicable and complete design
route for the candidate timber through-bolt. No method is selected here.

## Source-bound applicability matrix

| Source and exact version | What the source supports | Applicability boundary for this joint | Access and pin |
|---|---|---|---|
| ANSI/AWC NDS-2024, Chapter 11, §11.2.3; [official AWC Chapter 11 PDF](https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf) | Metal parts require applicable metal design procedures for tension, shear, metal-on-metal bearing, bending, and buckling; metal strength is not adjusted by NDS factors when it controls. The clause points to NDS refs. 39–41. | It does not specify a bolt-in-timber interaction equation or state that a particular steel-building bolt rule covers this connection. Official bibliography pages were not available here; refs. 39–41 are not expanded in this report. | Official Chapter 11 PDF was inspected from the matching local review copy; SHA-256 is recorded in `source-pins.json`. Direct web fetch was denied (403). |
| ANSI/AWC NDS-2024, Chapter 12, §12.3.6.2; [official AWC Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf) | NDS's dowel-fastener lateral design route references fastener bending-yield property inputs/test routes, including ASTM F1575/F1575M or ASTM F606/F606M. | This supports lateral wood-connection design inputs. It does not supply the direct bolt tension–shear–bending design resistance sought by `steel_direct`. Keep NDS lateral yield and direct steel resistance separate. | Official local copy and its digest were checked in attempt01; direct web fetch was denied. See inherited hash pins in `source-pins.json`. |
| ASTM F1575/F1575M-24; [official ASTM page](https://store.astm.org/f1575_f1575m-24.html) | Current version metadata identifies a test method for bending-yield property of nails, spikes, and dowel-type threaded fasteners. | A test/property input is not a combined N+V+M resistance equation. Its use as a timber lateral-yield input does not make it a through-bolt steel design method. | Official public page/catalog metadata was available; full copyrighted standard text was not reviewed or byte-pinned. |
| ASTM F606/F606M-26a; [official ASTM page](https://store.astm.org/f0606_f0606m-26a.html) | Current version metadata identifies mechanical-property test methods for threaded fasteners and related products; the page describes tensile and single-shear tests and defers property requirements to product standards. | Test methods are not a design interaction rule; no bolt-bending plus tension/shear design resistance was established from this source. | Official active-standard page opened on 2026-09-28. Dynamic page, no byte digest; full standard text not reviewed. |
| ANSI/AISC 360-22; [AISC current-standard page](https://www.aisc.org/aisc/publications/current-standards/aisc-360/), [AISC 16th-edition Manual standards list](https://www.aisc.org/aisc/publications/steel-construction-manual/), and [360-22 errata](https://www.aisc.org/globalassets/aisc/publications/revisions-and-errata/errata_360-22_1st-printing_01.23.2025.pdf) | AISC identifies 360 as its structural-steel buildings/structures specification; its 2022 edition incorporates LRFD and ASD. AISC's 2022 teaching example demonstrates §J3.8 tension-plus-shear treatment for bolts in a steel bearing-type connection. | §J3.8 example is N+V only. The 2024 thermal-break article's §J4.5 / Chapter H proposal is not shown to make a timber through-bolt fall within 360's bolt/member provisions. Full 360-22 text and commentary were not accessible in this screen, so the precise section-to-fastener scope was not independently authenticated here. | Current AISC pages and the official [2022 design-example PDF](https://www.aisc.org/globalassets/aisc/university-programs/teaching-aids/first-semester-design-examples---v16.0.pdf) were indexed; AISC direct PDF/page fetches returned 403. No current-standard equation was copied into a producer. |
| AISC, *Modern Steel Construction*, February 2024, “Thermal Breaks in Structural Steel,” pp. 59–60; [official issue PDF](https://www.aisc.org/globalassets/modern-steel/archives/2024/february2024.pdf) | Documents a design approach for steel-to-steel end-plate/TBP joints: bolt bending under shear, a single-curvature assumption, a shear-times-pad-thickness bolt moment, an AISC §J4.5 bending check, and Chapter H combined forces for shear, tension, and moment. | This is a scoped engineering article, not a general normative method. The article itself identifies the code gap for TBPs and RCSC exclusion; the studied joint is not a steel bolt through timber. Its reference list identifies “AISC (2022)” but says “ANSI/AISC 360-16,” leaving the exact cited edition uncertain. No section properties, interaction equation details, product match, or timber transfer validation were adopted. | AISC-hosted PDF was indexed by the search service; direct open returned 403. Content use is limited to the indexed article passages described here; no PDF-byte SHA. |
| RCSC Specification for Structural Joints Using High-Strength Bolts; [current AISC-hosted RCSC page](https://www.aisc.org/aisc/publications/current-standards/rcsc-standard/) | AISC describes the current RCSC scope as design of bolted joints and installation/inspection of fastener assemblies in structural-steel connections. The AISC 2024 TBP article refers to the 2020 RCSC commentary as excluding thermal-break joints. | Neither the accessible scope statement nor the TBP article establishes a timber through-bolt N+V+M method. The current 2025 full text was not read; the TBP statement is specifically about the cited 2020 commentary. | AISC page identifies the 2025 edition; full RCSC text was not accessible. Current-standard page fetch returned 403. |
| SAE J429_201405; [official SAE Mobilus entry](https://saemobilus.sae.org/standards/j429_201405-mechanical-material-requirements-externally-threaded-fasteners) | SAE lists mechanical/material requirements for inch-series externally threaded steel fasteners used in automotive and related industries. | Product-property standard only; it does not establish a wood-connection design resistance or an N+V+M interaction. Candidate SKU/delivered product is not selected or qualified. | Official SAE entry identifies the revised 2014-05-07 edition; full standard requires access and was not read. |
| ASTM A449-14(2020); [official ASTM page](https://store.astm.org/a0449-14r20.html) | ASTM identifies a general-engineering-use product specification for quenched-and-tempered steel bolts/cap screws/studs with tensile/property requirements. | Product designation/property requirements alone do not provide a timber-joint design method or combined N+V+M resistance. No candidate product has been qualified to this specification. | Official public standard page/indexed abstract; full standard text not reviewed or byte-pinned. |
| ANSI/AISC 360-27 public-review draft status; [AISC standards-under-review page](https://www.aisc.org/aisc/publications/standards-under-public-review/) | On 2026-09-28 AISC listed a 360 draft public-review period from September 11 to October 26, 2026. | A public-review draft is not a replacement adopted standard. This is temporal context only; it supplies no candidate method. | Official page checked 2026-09-28; dynamic page, no byte digest. |

## Exact unresolved requirements before a candidate producer could be defined

1. **Normative basis and scope.** Obtain and review the full applicable 360-22
   and RCSC texts, relevant commentary, and current errata; resolve the
   thermal-break article's edition mismatch; state whether §§J3.8, J4.5, and
   Chapter H can legitimately be composed for an individual through-bolt
   rather than assumed steel members/end plates. Identify the resistance
   format and every provision's scope.
2. **Bolt product/property basis.** Identify a fit-qualified delivered bolt,
   exact product standard/grade, diameter, thread form, actual thread-root and
   shank dimensions, tensile/yield properties, and the governing certified or
   test basis. The catalog screen has no fit-qualified SKU; a Grade 5/A449
   lead is not a selected product.
3. **Section and force model.** Establish the bolt's actual tensile, shear,
   and bending critical sections, including thread runout and each shear
   plane; define whether the bending stress model uses elastic or plastic
   section properties and how threads reduce the section; justify the
   single- or double-curvature span, contact/bearing locations, washer/head/
   nut restraint, and any clamp-force assumptions.
4. **Combined interaction.** Identify one applicable equation or validated
   composition that checks concurrent signed axial force, transverse shear,
   and bolt moment at the critical section. Define areas, section moduli,
   nominal/available strengths, resistance or safety factors, prying/contact
   effects, and separate rupture/yield/buckling limits. Do not treat
   material-first-yield arithmetic or an N+V-only equation as this rule.
5. **Connection demands and sharing.** Produce the signed, simultaneous
   per-bolt N, V, and M demands for each governing load case using a justified
   stiffness/load-sharing model. The pinned full-frame manifest contains
   applied load/wrench cases, not bolt demands; it reports no selected
   structural hardware and no executed native solve.
6. **Timber and whole-joint checks.** Keep the metal bolt check distinct from
   wood embedment/yielding, splitting, net-section/block failure, washer/head
   bearing, local block failure, group effects, and complete load-path checks.
   A bolt-only metal check cannot qualify the timber joint.
7. **Method validation.** Before implementing any producer, provide a
   checkable N+V+M benchmark with known demand distribution and an independent
   reference result that exercises the chosen section, thread, curvature,
   and interaction assumptions. This packet contains no calculated capacity
   and performs no model or solver run.

These are evidence and applicability gaps; this review does not add or change
project criteria. Attempt01 and its independent review remain preserved and
hash-pinned by this packet.

## Review integrity

The exact URLs, versions, access limits, and local digest checks are recorded
in [`source-pins.json`](source-pins.json). The terminal hashes bind this report
and source-pin file. The upstream attempt01 report, source pins, known answer,
terminal manifest, and independent-review report/manifest were checked
against their existing hashes; attempt01's three terminal deliverables match.
The NDS Chapter 11, Chapter 12, and March 2026 errata local copies also match
their pinned SHA-256 values. Dynamic web pages and search-indexed PDFs are
not byte-pinned.
