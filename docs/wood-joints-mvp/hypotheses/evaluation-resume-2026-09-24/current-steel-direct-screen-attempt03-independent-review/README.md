# Independent review — steel-direct source screen, attempt03

Reviewed 2026-09-28. Verdict: **SUPPORTED_WITH_SCOPE_LIMIT**. The attempt03
conclusion is appropriately bounded: the reviewed standards and publications
do not establish an applicable, complete bolt tension + shear + bending
resistance method for a through-bolt in solid timber. This is an applicability
and evidence gap, not proof that no engineering method exists.

The official RCSC 2009 Commentary to §1.1 expressly excludes a non-steel
material in the bolt grip; its §5.2 interaction covers tension and shear. The
official RCSC 2025 Commentary retains that general boundary, while §5.2 also
covers tension and shear rather than bolt bending. The 2025 Commentary cites a
narrow low-modulus-material research result for snug-tight, shear-only joints;
it does not establish a timber-grip, simultaneous tension/shear/bending rule.
Both editions also discuss alternative-design provisions. Those points make
the conclusion about RCSC's prescribed provisions narrower than a claim that
RCSC rules out every separately justified method.

The AISI S240-20 source supports the stated cold-formed-steel scope: B1.5.3
routes bolted CFS connections to AISI S100 Chapter J, while B1.5.6 routes
fasteners connecting CFS framing to wood or other materials to the applicable
building code or approved construction documents. AISI S100's J3.4 includes a
bolt tension/shear interaction within its cold-formed-steel connection
provisions. J7.1 and its Commentary address CFS attachments to other materials,
including wood, and point to applicable codes, NDS and manufacturer documents;
they do not state a wood-to-wood bolt N+V+M interaction.

AISC's official material scopes ANSI/AISC 360 to structural-steel buildings
and other structures. AISC §J3.8's combined bolt tension/shear provision is
distinct from steel-element flexural/member-force checks. The February 2024
AISC thermal-break article describes a special steel end-plate/pad approach
that includes bolt bending, but it is a nonnormative method for another joint
type. Attempt03 appropriately does not use those separate provisions as an
unsubstantiated transfer rule for a timber-grip bolt. Its disclosure that the
full AISC 360-22 PDF was not available for direct clause-level review is
material and should remain attached to the claim.

The NDS References 39–41 assignment matches the transcription visible in the
identified non-AWC NDS-2024 mirror: 39 = RCSC 2009, 40 = ANSI/AISC 360-22, and
41 = AISI S240-20. AWC's official NDS page confirms the 2024 edition and a
free view-only option, but the official bibliography assignment was not
independently authenticated here. Keeping that mapping explicitly provisional
is correct. The attempt03-pinned official Chapter 11 file digest matches its
manifest; this review could not independently extract text from that local PDF.

Hash verification passed for the three attempt03 terminal artifacts, all 22
unique file entries in its integrity manifest, and the listed attempt01 and
attempt02 terminal deliverables and recorded digests. The current
`criteria-method-map.md` bytes match attempt03's pinned SHA-256
`2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`.
The criteria/method map remains the authority; this review makes no changes to
it or to criteria, methods, geometry, hardware, candidates or solver state.

## Source trail

- RCSC 2009, §1.1 and Commentary; §5.2: [official PDF](https://mail.boltcouncil.org/files/2009RCSCSpecification.pdf).
- RCSC 2025, §1.1 Commentary; §5.2; current archive listing: [official PDF](https://mail.boltcouncil.org/files/2025RCSCSpecification.pdf), [RCSC documents](https://mail.boltcouncil.org/documents.html).
- AISI S240-20, A1.1, B1.5.3 and B1.5.6: [AISI-hosted PDF](https://www.buildusingsteel.org/wp-content/uploads/2023/06/AISI-S240-20.pdf).
- AISI S100-16 (reaffirmed 2020), Supplement 3 (2022), J3.4 and J7.1: [AISI-hosted PDF](https://www.buildusingsteel.org/wp-content/uploads/2023/06/AISI-S100-16-2020-wS3-22.pdf).
- AISC scope and 360-22 context: [AISC 360](https://www.aisc.org/aisc/explore-aisc/aisc-360/), [Steel Construction Manual](https://www.aisc.org/aisc/publications/steel-construction-manual/). Thermal-break example: [AISC Modern Steel Construction, February 2024](https://www.aisc.org/globalassets/modern-steel/archives/2024/february2024.pdf).
- AWC edition/viewing page: [2024 NDS](https://awc.org/resources/2024-nds/). Provisional mapping lead only: [non-AWC mirror](https://studylib.net/doc/28419537/awc-nds2024-withcommentary-20250328-abdi-electronic).

Binary hashes are available for the local NDS Chapter 11/12 and errata copies
listed in the attempt03 integrity manifest. The external issuer-hosted RCSC,
AISI and AISC PDFs were reviewed through browser-extracted text or official
metadata; their raw bytes were not available for hashing. The detailed digest
record and primary-source boundaries are in `review-record.json`.
