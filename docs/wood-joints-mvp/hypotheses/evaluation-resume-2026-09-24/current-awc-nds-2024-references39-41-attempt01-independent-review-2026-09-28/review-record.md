# Independent review record

**Review date:** 2026-09-28  
**Reviewed packet:** `current-awc-nds-2024-references39-41-attempt01`  
**Review scope:** packet integrity, recorded direct-access routes, official-versus-mirror boundary, and claims about NDS-2024 References 39–41 and a timber-grip combined axial tension + shear + bolt-bending (`N+V+M`) method.

## Result

The packet passes this bounded review for integrity and claim discipline. Its core conclusion remains unresolved: the actual AWC NDS-2024 References 39–41 were not retrieved or directly authenticated. The review does not authenticate the mirror's proposed mapping, establish a method, or evaluate a connection.

The packet's `verify_source_packet.py` returned `PASS: 3 packet files match SHA256SUMS`. Independently recomputed hashes match all three entries. All eight predecessor-file hashes listed in `source-observations.json` also match their files. See [`integrity-checks.json`](integrity-checks.json).

## Direct-access routes independently checked

1. **AWC 2024 NDS resource page** — opened `https://awc.org/resources/2024-nds/`. The AWC page text identifies the 2024 NDS and says ANSI approved it on October 16, 2023. It exposes “Free View-Only Option” as a rendered button, without a callable destination in the extracted page. The page text contains no References 39–41. This supports edition identity, not bibliography identity.
2. **AWC-attributed LinkedIn announcement** — opened `https://www.linkedin.com/posts/american-wood-council_2024-nds-activity-7140391133813088258-ghIB`. The retrieved post identifies ANSI/AWC NDS-2024 and provides `https://bit.ly/48dnXdB` as its free-view link. The post does not reproduce the reference list.
3. **AWC viewer shortlink** — direct open of `https://bit.ly/48dnXdB` returned “not accessible via this tool.” Clicking the shortlink from the retrieved post returned a LinkedIn redirect `Cache miss`. Neither result identifies the redirect destination or shows that the AWC viewer is unavailable.
4. **AWC page button follow** — the independently retrieved resource-page extraction does not expose the button as a callable hyperlink. The packet records a prior attempt to click rendered marker `52` as invalid arguments. This is an extraction/tool limit, not a failed AWC viewer session.
5. **AWC-hosted 2024 NDS Chapter 11 PDF route** — direct open of `https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf` was inaccessible in this review. The packet labels its §11.2.3 cross-reference observation as inherited from earlier review packets and correctly says the chapter excerpt does not identify the bibliography entries.
6. **AWC-domain search** — independently searched AWC-scoped queries for 2024 NDS References / reference 39. Results exposed AWC’s NDS resource page and related AWC items, but no 2024 References page or entry text. Search non-retrieval is not evidence that the pages are absent. The packet's exact recorded queries were:

   - `site:awc.org/wp-content/uploads "NDS2024" "References" AWC`
   - `site:awc.org "NDS2024" "Reference 39"`
   - `site:awc.org "AWC_NDS2024" References pdf`
   - `site:web-media.awc.org NDS2024 References`
   - `site:awc.org/pdf/codes-standards/publications/nds AWC NDS 2024 ViewOnly`
   - `site:awc.org "NDS2024-ViewOnly"`
   - `site:awc.org/pdf/codes-standards/publications/nds "NDS-2024"`

   I also ran four independent queries: `site:awc.org 2024 NDS "References" "39"`; `site:awc.org/wp-content/uploads 2024 NDS references PDF AWC`; `site:awc.org "NDS2024" "References" AWC`; and `site:awc.org/resources/2024-nds "Free View-Only Option"`. These are index searches, not direct publication retrieval.
7. **AWC press-release route** — direct open of `https://awc.org/about/press/awc-2024-design-standards-available-online/` returned HTTP 403. Search-index text identifies the announcement and says the 2024 NDS was available for free viewing; it does not reproduce References 39–41. The packet labels this index-only evidence and does not promote it to direct page text.
8. **Accuris/Techstreet preview route** — direct open of `https://store.accuristech.com/products/preview/2922442` returned HTTP 403. This is a non-AWC host, and the packet limits its search-index metadata to an access lead. It is not used to authenticate AWC's bibliography.

The packet's prior mirror transcription points to `https://studylib.net/doc/28419537/awc-nds2024-withcommentary-20250328-abdi-electronic`. The packet labels the mapping `UNAUTHENTICATED_MIRROR_TRANSCRIPTION`, identifies it as non-AWC, and does not present it as primary authority. This review did not reopen or validate that mirror. The mapping therefore remains provisional and cannot be reported as AWC-confirmed.

## Method claim boundary

The packet marks `directly_authenticated_reference_identities` and `new_combined_N_plus_V_plus_M_method_observed` as false. Its narrative says it establishes no applicable timber-grip through-bolt N+V+M method and does not re-adjudicate the steel standards. The packet does not claim direct authentication of References 39–41 or a timber-grip N+V+M method.

## Limits

This review checks the access record and its claims; it is not a source-content review of the unseen References pages. No native solver, capacity calculation, candidate, hardware, or geometry work was performed. See [`raw-source-byte-limits.md`](raw-source-byte-limits.md) for the retrieval boundary.
