# Plywood identity search — attempt07 public manufacturer/certifier records

**Disposition: the new Roseburg/APA routes still do not cross-reference Lowe’s item 12235/model 119055.** This append-only attempt searches new public Roseburg and APA-controlled routes for a manufacturer code, species/construction/grade, or applicable product-specific design-property record. It preserves the earlier T05 packets and does not treat matching thickness, face description, grade, or ply count as a model identity.

The APA manufacturer directory publicly identifies Roseburg as an APA participant and lists plywood production, sanded panels, certified mills Coquille #367 and Riddle #482, and applicable product-report entries. It states that certified-product APA mill numbers appear on the APA trademark. Its Roseburg plywood report rows name PR-C302 for DuraTemp siding and PR-E710 for multi-company qualified wood structural panels with low formaldehyde emissions. The separate PR-E710 record confirms that low-emissions report scope and names Roseburg among participating manufacturers. Neither record cross-references Lowe’s identifiers or names the AC sanded retail item. The APA exact-ID queries returned no search results; this is a bounded search result, not proof of source absence.

Roseburg’s public Literature Library route now renders without an account and lists search/filter categories for technical data sheets, code reports, certifications, and Softwood Plywood / Exterior Core. Its extracted public search-results area was blank, so it supplied no model-specific record in this retrieval. The direct Roseburg AC option page likewise displays only an AC sanded-plywood category and a “Where to Buy” control in the captured lines.

A separate current Roseburg-hosted brochure adds a useful ambiguity boundary: its Exterior Core AC schedule includes 23/32-in, five-ply AC and 23/32-in, seven-ply Structural I AC options at 24-in on-center. It gives option-family face/core/back descriptions and a core-gap reference to APA PS-1. It does not show item 12235/model 119055 or any Lowe’s-to-Roseburg product code. The brochure’s OCR-rendered table label is recorded as rendered; it is not used to infer exact veneer species, exact sheet layup, or a Lowe’s crosswalk. The brochure gives no numeric structural design-property table for the Lowe’s listing.

Exact routes, queries, page locators, retrieval failures, and scope limits are in `route-observations.json`. `source-byte-register.json` hashes the local attempt06 predecessor packet and records that no new live external bytes were available to hash. The rendered APA PR-E710 PDF direct URL returned 404 on open; its APA landing page and indexed PDF text are preserved as separate evidence with that access limit.

## Evidence boundary

The certifier record shows Roseburg has APA-certified plywood mills and manufactures sanded panels, but a mill listing is not a crosswalk for a Lowe’s item. The product-report list is not evidence that PR-E710 supplies mechanical properties for this AC product; the report is specifically a multi-company low-formaldehyde qualification. Roseburg’s own option table proves that similar 23/32-in AC descriptions can represent both a five-ply non-Structural-I option and a seven-ply Structural-I option within its product family. No reviewed source joins either option to Lowe’s item 12235/model 119055.

No exact manufacturer product code, model-specific species/construction/layup, model-specific grade stamp/standard edition, applicable model-specific design-property record, physical-sheet identity, or lot link is established. Material values, axes, solver properties, readiness, and criteria disposition remain unset. No vendor was contacted, no account-gated content was used, and no purchase or physical inspection was performed. Shared queue/status/manifest/authority files and geometry were not changed.

## Next executable action

After parent review, search or request the exact Roseburg product code/cross-reference for Lowe’s item 12235/model 119055 and the applicable product/grade/design record. If later evidence is based on APA marking, it must include the actual panel or package mark and manufacturer/plant/standard/category data; this packet does not inspect or assume such a mark.

## Integrity

On 2026-09-28, the two JSON files parsed, all three attempt07 checksum entries passed, all four attempt06 predecessor file hashes matched, and attempt06's own `SHA256SUMS` passed. The local predecessor file digests and attempt07 files are listed in `source-byte-register.json` and `SHA256SUMS`. Run `sha256sum -c SHA256SUMS` in this directory to verify the attempt07 packet.
