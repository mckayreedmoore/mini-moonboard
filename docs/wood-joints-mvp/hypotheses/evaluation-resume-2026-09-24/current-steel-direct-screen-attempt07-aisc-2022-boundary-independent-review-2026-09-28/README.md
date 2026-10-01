# Independent review — AISC attempt07 boundary packet

**Verdict: supported within the stated source boundary, with one minor heading
mismatch.** The packet’s local integrity checks pass, and its main conclusion is
appropriately limited to what the reviewed sources establish. I found no basis
to turn this source gap into proof that no independently justified method
exists.

## Scope and result

Reviewed the append-only attempt07 README, source observations, verifier,
terminal hashes, and `SHA256SUMS`; reran its verifier; and checked the cited
AISC edition, errata, scope, clause-title, and example records against official
AISC material or the packet’s retrieval record. Direct opens of the full
360-22 and 303-22 PDFs remained blocked. No standard PDF bytes or external
source hashes are claimed here.

The source boundary is sound: AISC 360-22 is the issued edition identified in
AISC publication materials on 2026-09-28; the September–October 2026 360 draft
was still a public-review draft. The errata list and 303 scope cross-reference
support the stated edition and applicability limits. AISC’s example and
comparison support the description of §J3.8 as a bearing-type tension/shear
interaction. The conclusion remains “not established by these sources.”

One documentary correction: the exact §J3.7 title is **“Tensile and Shear
Strength of Bolts and Threaded Parts.”** The attempt07 README and two
`source-observations.json` entries instead say “Tension and Shear Strength.”
Both AISC’s 360-22 comparison and its authorized publication preview give the
“Tensile” wording. This title discrepancy does not change the packet’s
substantive description of the separate tension and shear provisions.

The reviewed claim does not establish complete timber-grip bolt N+V+M design,
bolt bending resistance, timber limit states, or whole-joint acceptance. No
capacity was calculated, no method or candidate was adopted, no criterion or
method map was changed, and no solver/native work was performed. The original
attempt07 packet was left unchanged.

## Integrity

The attempt07 verifier returned `PASS: attempt07 local artifacts, context pins,
and status checks`. Its `SHA256SUMS`, terminal manifest, and read-only context
pins reproduced. Input file digests are recorded in
[`review-record.json`](review-record.json). This review’s README and record are
bound by [`terminal-hashes.json`](terminal-hashes.json) and
[`SHA256SUMS`](SHA256SUMS); raw external AISC bytes are not hashed.

## Official source checks

- [AISC Steel Construction Manual / current publication materials](https://www.aisc.org/aisc/publications/steel-construction-manual/) identify Part 16.1 as ANSI/AISC 360-22 and Part 16.3 as ANSI/AISC 303-22. [AISC’s standards-under-review page](https://www.aisc.org/aisc/publications/standards-under-public-review/) lists the 360 draft for September 11 through October 26, 2026. The draft is not treated as an issued replacement.
- [AISC 360-22 to 360-16 comparison](https://www.aisc.org/media/myzl4doa/2022-to-2016-spec-comparison.pdf) gives the §J3.7 and §J3.8 headings and says those sections were unchanged. [AISC’s authorized 360-22 preview](https://store.accuristech.com/products/preview/2564477) confirms the “Tensile and Shear” title and locators for §J4.5. These sources support the heading mismatch noted above.
- [AISC Example J.3](https://www.aisc.org/globalassets/aisc/university-programs/teaching-aids/first-semester-design-examples---v16.0.pdf) demonstrates §J3.8 for combined bolt tension and shear in a bearing-type steel connection; it does not demonstrate timber-grip applicability or bolt bending.
- [AISC’s 303/IBC cross-reference](https://www.aisc.org/aisc/publications/current-standards/aisc-303/303ibc/) states that 360-22 §A1 refers to 303-22 §2.1. The [official 303-22 errata](https://www.aisc.org/globalassets/aisc/publications/revisions-and-errata/errata_303-22_1st-printing_01.23.2025.pdf) corrects §1.12 on p. 16.3-7 only; the viewer text was accessible during this review.
- [AISC’s 360-22 errata listing](https://www.aisc.org/aisc/publications/revisions-and-errata/) and [January 2025 errata PDF](https://www.aisc.org/globalassets/aisc/publications/revisions-and-errata/errata_360-22_1st-printing_01.23.2025.pdf) support the packet’s correction-page list. Search-index text was available, while direct PDF opening returned HTTP 403.

The official AISC 360-22, 303-22, comparison, and design-example PDFs could not
be opened directly in this review; AISC search-index extracts and the
attempt07 source record were used within their stated limits. No third-party
mirror was used to establish an engineering provision.
