# T06 steel-direct source applicability screen — attempt03

**Reviewed 2026-09-28.** This is a bounded, read-only follow-up to attempt02.
It identifies the apparent NDS-2024 Chapter 11 References 39–41 and checks
the official RCSC/AISI text and accessible AISC publication material for a
method for one through-bolt in solid timber under simultaneous axial force,
shear, and bolt bending. No method is adopted; no capacity is calculated; no
hardware is selected; and no criterion, method map, candidate, geometry,
solver state, or release state is changed. No solver/native run was performed.

## Finding

The source review strengthens the bounded method-gap conclusion. The official
RCSC 2009 edition—the apparent NDS Reference 39—has a combined shear-and-tension
check, but its Commentary expressly places material other than steel in the
bolt grip outside the Specification. The timber stack is such a non-steel grip.
RCSC 2025, checked as current-version context, retains that scope boundary and
its §5.2 interaction is also tension plus shear; it does not add bolt bending.

The apparent Reference 41, AISI S240-20, is a cold-formed-steel framing
standard. It directs bolted cold-formed-steel connections to AISI S100 Chapter
J, and separately says fasteners from cold-formed steel framing to wood are to
follow the applicable building code or approved construction documents. AISI
S100 J3.4 supplies bolt tension/shear provisions for its cold-formed-steel
connection scope. Its J7 provisions address cold-formed steel attached to
other materials, including wood, and point to the NDS and product documents;
they do not state a bolt-level N+V+M interaction rule for a wood-to-wood
through-bolt.

ANSI/AISC 360-22 is scoped to structural-steel systems. Its bolt interaction
provision is distinct from its affected-element/member flexure and combined
force provisions. The AISC-published February 2024 thermal-break article
describes a special steel end-plate/TBP approach that combines bolt tension,
shear, and bending by analogy to AISC provisions. It is a professional
practice article for a different joint, not a normative general timber-bolt
method. Neither the cited steel standards nor that article supplies an
explicit transfer basis to this solid-timber connection.

The NDS References 39–41 have been recovered as a **provisional bibliographic
transcription**, not as an authenticated AWC list. AWC's official NDS resource
page confirms that the full standard has a free view-only option, but its
bibliography was not available through the official page in this review. The
number-to-title assignment below appears in a non-AWC mirror of the 2024 NDS;
the three standard identities/editions were cross-checked separately against
their issuing-body materials where available. Do not treat the mirror as
primary evidence that AWC assigned those exact numbers until an official AWC
copy of the bibliography is reviewed.

| NDS ref. | Provisional bibliography identity | Separate official identity check | Status |
|---|---|---|---|
| 39 | *Specification for Structural Joints Using High-Strength Bolts*, RCSC, 2009 | RCSC's official archive lists its December 31, 2009 edition; the official 2009 PDF cover matches that title/date. | Title and edition are verified at RCSC; assignment to NDS ref. 39 remains mirror-only. |
| 40 | *Specification for Structural Steel Buildings*, ANSI/AISC 360-22, AISC, 2022 | AISC's current-standard and Manual materials identify ANSI/AISC 360-22; an AISC-hosted 2022-to-2016 comparison confirms §J3.8 is the combined tension/shear-in-bearing-type-connection provision. | Title and edition are verified at AISC metadata; assignment to NDS ref. 40 remains mirror-only. |
| 41 | *North American Standard for Cold-Formed Steel Structural Framing*, AISI S240-20, AISI, 2020 | The public AISI S240-20 PDF identifies the 2020 edition and exact title. | Title and edition are verified in the standard; assignment to NDS ref. 41 remains mirror-only. |

The combined source evidence supports **an applicability gap for this timber
through-bolt, not proof of absolute method nonexistence**. In particular,
RCSC's stated scope exclusion means its bolt tension/shear interaction cannot
be presented as an applicable N+V+M method for a bolt through timber. Other
engineering approaches may exist, but none reviewed here establishes the
missing timber applicability, bolt bending section model, complete N+V+M
interaction, and design resistance basis.

## Source-bound applicability matrix

| Primary source/version and exact provisions | What the text establishes | Boundary for the timber through-bolt | Access, hash, and source URL |
|---|---|---|---|
| ANSI/AWC NDS-2024, Chapter 11 §11.2.3; [official Chapter 11 PDF](https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf) | The clause sends metal parts to applicable metal design procedures for listed metal limit states and directs the reader to References 39–41. It does not itself name a bolt-in-timber N+V+M equation or identify which cited steel provision applies. | The clause is a general direction, not a demonstrated transfer rule for AISC/RCSC/AISI bolt and steel-member provisions to a timber-grip bolt. | The matching official AWC Chapter 11 local review copy is `/tmp/AWC-NDS2024-Chapter11.pdf`, SHA-256 `774d13c8a92cb8bfa876c45044fc40e8c3a90b1e3513075ed64626d5988f027d`. Direct web fetch returned 403. The official reference-list pages were not available. AWC edition/viewing access is described at [2024 NDS](https://awc.org/resources/2024-nds/). |
| RCSC, *Specification for Structural Joints Using High-Strength Bolts*, December 31, 2009, §1.1 and Commentary to §1.1; §5.2; [official RCSC PDF](https://mail.boltcouncil.org/files/2009RCSCSpecification.pdf) | §1.1 covers specified high-strength fastener assemblies in structural-steel joints. Its Commentary excludes cases where non-steel material is included in the grip. §5.2 checks combined bolt tension and shear. | A timber through-bolt has wood in its grip, so the cited edition expressly excludes this joint. §5.2 is N+V only and supplies no bolt-bending interaction. | The official RCSC archive lists the 2009 edition at [RCSC documents](https://mail.boltcouncil.org/documents.html). The official PDF was readable through the web PDF viewer; exact version, page/section, and URL are pinned. The viewer did not expose source bytes for a SHA-256 digest; no local PDF copy was made. |
| RCSC, *Specification for Structural Joints Using High-Strength Bolts*, June 5, 2025, §1.1 Commentary; §5.2; [official RCSC PDF](https://mail.boltcouncil.org/files/2025RCSCSpecification.pdf) | The current edition says collateral grip materials within its scope are steel and keeps non-steel grip materials outside its provisions. §5.2 remains a combined tension-and-shear check. | This is current-context confirmation, not the edition cited in apparent NDS ref. 39. It gives no N+V+M interaction for timber. | Official RCSC archive lists the 2025 edition. PDF text was reviewed in the official RCSC-hosted browser viewer; source bytes were not downloaded and have no SHA-256 digest. |
| ANSI/AISC 360-22, §A1; §J3.8; §J4.5; Chapter H; [AISC 360 current-standard page](https://www.aisc.org/aisc/publications/current-standards/aisc-360/), [official 2022 comparison](https://www.aisc.org/media/myzl4doa/2022-to-2016-spec-comparison.pdf), [AISC design examples v16.0](https://www.aisc.org/globalassets/aisc/university-programs/teaching-aids/first-semester-design-examples---v16.0.pdf) | AISC identifies 360 as the structural-steel buildings/structures specification. §J3.8 is titled combined tension and shear in bearing-type connections; §J4.5 concerns flexural strength of affected/member/connecting elements. AISC's published example demonstrates bolt N+V in a steel bearing-type connection, not bolt bending. | The review found no explicit provision making a timber-grip through-bolt an AISC structural-steel connection/member or authorizing composition of §J3.8, §J4.5, and Chapter H into a timber-bolt N+V+M resistance. The clauses are not a single combined bolt interaction just by being cited together. | AISC-hosted full-standard and teaching-aid PDF opens returned 403. Edition and clause titles were checked through AISC search-indexed official materials and an authorized publication preview; no official AISC full-PDF bytes were locally pinned. AISC's [current standards list](https://www.aisc.org/aisc/publications/current-standards/) says current standards are publicly downloadable. |
| AISC, *Modern Steel Construction*, February 2024, “Thermal Breaks in Structural Steel,” pp. 59–60; [official issue PDF](https://www.aisc.org/globalassets/modern-steel/archives/2024/february2024.pdf) | The article describes single-curvature bolt bending for a steel-to-steel end-plate thermal-break pad, and an engineering approach using AISC §J4.5 and Chapter H for concurrent bolt shear, tension, and moment. It also describes the thermal-break code-guidance gap. | This is an engineering article for steel end plates and thermal-break pads, not a normative timber through-bolt method. Its section model, interaction, and product/connection assumptions were not validated for wood. Its reference list has an AISC edition-name mismatch, as documented in attempt02. | Official AISC-hosted issue PDF is indexed, but direct fetch returned 403. No PDF-byte digest. The report treats the method as a scoped published approach, not a standard. |
| AISI S240-20, *North American Standard for Cold-Formed Steel Structural Framing*, A1.1, B1.5.3, B1.5.6; [public AISI PDF](https://www.buildusingsteel.org/wp-content/uploads/2023/06/AISI-S240-20.pdf) | A1.1 scopes the standard to cold-formed-steel light-frame members/connections. B1.5.3 sends bolted CFS connections to AISI S100 Chapter J. B1.5.6 directs fasteners connecting CFS framing to wood or other materials to the applicable building code or approved construction documents. | The referenced standard is not a direct N+V+M method for a wood-to-wood through-bolt; its wood-attachment clause points elsewhere instead of extending the steel-to-steel bolt provisions. | Official AISI-hosted PDF was readable in the browser PDF viewer; source bytes were not downloaded and have no SHA-256 digest. It includes AISI copyright/redistribution restrictions; only paraphrase and clause identifiers are recorded. |
| AISI S100-16 (Reaffirmed 2020) with Supplement 3 (2022), A1.1; B3.4; J3 and Appendix A §J3.4; J7.1.2–J7.1.3 and Commentary J7.1; [AISI PDF](https://www.buildusingsteel.org/wp-content/uploads/2023/06/AISI-S100-16-2020-wS3-22.pdf) | A1.1 scopes the specification to cold-formed-steel members. J3 bolt criteria are for steel-to-steel cold-formed-steel connections within stated thickness scope; the U.S./Mexico Appendix A §J3.4 interaction combines bolt tension and shear. J7 addresses connections from covered steel components to other materials, requiring bearing/tension/shear transfer and referring fastener and embedment strengths to applicable product documentation. Commentary J7.1 points cold-formed-steel-to-wood bolt/screw connections to NDS and manufacturer technical reports/catalogs. | The J3 N+V rule is scoped to CFS connections and does not include bolt bending. J7 is a CFS-to-other-material connection boundary and does not define a three-component metal-bolt interaction for a wood-to-wood timber joint. Its mention of bending moment addresses load transfer/pull-out awareness, not a steel bolt bending resistance equation. | Official AISI PDF is readable in the browser PDF viewer; source bytes were not downloaded and have no SHA-256 digest. Copyright/redistribution notice applies; only short clause IDs and paraphrase are recorded. |

## Requirements still open

1. **Authenticate the NDS numbering.** Review the official AWC NDS-2024
   References pages and verify the exact text and assignment of refs. 39–41.
   The current report's number-to-title mapping is provisional because its only
   readable complete bibliography came from a non-AWC mirror.
2. **Establish applicability for AISC provisions.** If proposing AISC-based
   treatment, provide a source-supported reason that each clause applies to
   this bolt/connection and that any composition of bolt N+V and steel-element
   flexure/combined-force checks is valid for a timber grip. RCSC's express
   non-steel-grip exclusion must be resolved rather than silently bypassed.
3. **Define one full bolt N+V+M resistance method.** State the force and moment
   interaction, strength format/factors, critical cross-sections, thread-root
   or shank properties, bending restraint/span, curvature, washer/head/nut
   effects, and rupture/yield/buckling limits. No method or equation is adopted
   in this report.
4. **Supply applicable demands and validation.** A future producer would need
   signed simultaneous per-bolt N, V, and M from a justified force-sharing
   model and an independent N+V+M benchmark. This packet contains no bolt
   demands or solver results.
5. **Keep whole-joint checks separate.** A metal-bolt check would not qualify
   timber bearing, splitting, net-section/block failure, washer/head bearing,
   group effects, or the complete timber load path.

These are evidence gaps for the existing `steel_direct` obligation; they do
not amend the criteria or method map.

## Distinctions preserved

- NDS lateral-yield design and the fastener bending-yield property input
  `Fyb` are for the wood connection's lateral-yield route. An ASTM test/property
  standard that supplies `Fyb` is not a metal-bolt N+V+M interaction rule.
- RCSC, AISC, and AISI provisions are steel joint/member design text with the
  scopes stated above. A product specification or fastener-property test is
  not itself a complete connection design method.
- Material first-yield arithmetic (including a von Mises comparison) is a
  material-level reference, not a design resistance or joint acceptance check.
- This screen computes no resistance or capacity and selects no bolt product.

## Preservation and integrity

Attempt02 is preserved and hash-pinned by `source-pins.json`. Its report,
source pins, integrity manifest, and terminal hashes all match their prior
digests. Attempt01, its known-answer packet, the independent review, and the
NDS-2024 Chapter 11/12 and March 2026 errata local copies also match their
existing hashes. The criteria/method map hash matches attempt02. This packet
was written only under the new attempt03 directory.

The terminal hashes bind this report, `source-register.json`, and
`integrity-manifest.json`. External browser-viewed PDF bytes are not represented
as hashed files: the browser exposes extracted text but no byte stream, and
direct AWC/AISC requests were blocked. Their exact issuer URL, edition,
clauses, and access limit are pinned above and in the source register.

## Commands used

- Read-only discovery: `find ... -maxdepth 1 -type d -name 'current-steel-direct-screen-attempt*'`.
- Local digest verification: `sha256sum` over attempt01, attempt02, independent-review, and local NDS PDF deliverables; exact resulting values are in `source-register.json`.
- Packet validation: `python3 -m json.tool` over the JSON files, followed by `sha256sum` over the attempt03 deliverables.
- No solver, native analysis, geometry, physical, candidate, criteria, method-map, hardware, or release command was run.
