# Plywood product identity search — attempt06

**Disposition: no direct retailer-to-manufacturer identity link surfaced in the reviewed public-source set.** This append-only packet searches public Lowe's and Roseburg records for Lowe's item **12235** / model **119055**, and checks whether the visible product descriptors resolve to a Roseburg product code, exact wood species/construction/layup, applicable grade or standard, or product-specific engineering properties.

The exact Lowe's listing page associates item 12235/model 119055 with the retail title “23/32-in x 4-ft x 8-ft Douglas Fir Square Sanded Plywood.” Lowe's specifications list Douglas fir, 23/32-in thickness, the `PS1-09` product-standard value and `23/32 CAT` performance-category value. These are Lowe's page assertions for this listing. The page does not expose a manufacturer product code, UPC, exact layup, or mechanical property values in the inspected content. The “Roseburg” word in one historical page URL/search result and the image alt text do not constitute a manufacturer-controlled cross-reference.

Roseburg's directly opened Exterior Core page currently presents an AC Sanded Plywood option and an option card with 23/32-in, five-ply, 24-in on-center, and sanding descriptors. Its family text describes western-wood veneers; its AC section supplies face-grade details, while manufacturer literature supplies AC-family core/back grade and construction details. Roseburg's general softwood plywood page states APA/PS 1 compliance at the family/site level. None of these reviewed records names Lowe's item 12235 or model 119055, and the literature library route did not render in the web retrieval tool. Descriptor similarity is not treated as identity.

The official Roseburg brochure's 23/32-in Exterior Core packaging row reports a five-or-seven-ply range. That family/packaging record remains distinct from the AC option card's five-ply statement. Neither establishes a model-specific veneer schedule. No exact ply-by-ply species, thickness, sequence, grade stamp or product-specific engineering property set was found in the reviewed pages. Lowe's `PS1-09` field and Roseburg's broader APA/PS 1 statement are recorded as separate source claims; no exact model-level manufacturer declaration ties them together.

Search scope and exact rendered locators are in `search-observations.json`. `source-byte-register.json` records hashes only for local bytes actually available. The currently rendered public pages were not saved as bytes; their external-byte hashes are null. Previously retained Roseburg HTML/PDF snapshots are hashed and explicitly marked historical, not fresh captures of today's pages.

## Evidence boundary

The reviewed public records support that Lowe's assigns its own item/model identifiers and lists the above descriptors, and that Roseburg publishes an apparently similar AC Sanded Exterior Core option. The reviewed record set does **not** prove that Lowe's item/model is that Roseburg option. It does not establish a Roseburg product code for the retailer item, exact species for that model, exact veneer layup, applicable model-specific grade/stamp/standard, structural design values, delivered-sheet identity, or lot linkage. No conclusion is drawn that such a cross-reference or product record does not exist elsewhere.

All material, physical-sheet, panel/body, axis, property, and solver assignments remain null. No material values were assigned; no readiness, criterion disposition, or acceptance is claimed. No vendor was contacted, no account-gated page was used, no purchase/order was made, and no geometry or coordination file was changed.

## One next executable action

After parent review, obtain a Roseburg-controlled public document or written manufacturer cross-reference naming Lowe's item 12235/model 119055 and the corresponding Roseburg product code, applicable species/construction/grade-standard record, and any product-specific design properties. This packet does not perform or authorize vendor contact; if no public record is located, any later contact decision remains with the parent/owner.

## Integrity checks

On 2026-09-28, both JSON files parsed and all three attempt06 `SHA256SUMS` entries passed. The eight local source/predecessor file digests listed in `source-byte-register.json` matched. Attempt05's own two-file checksum and its independent-review checksum both passed. These checks establish local byte integrity only; they do not freeze the current external pages.

Run `sha256sum -c SHA256SUMS` from this directory to verify the packet files.
