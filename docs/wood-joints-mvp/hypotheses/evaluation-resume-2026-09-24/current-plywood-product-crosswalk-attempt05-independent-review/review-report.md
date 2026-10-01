# Independent review: plywood product crosswalk attempt05

**Review date:** 2026-09-28  
**Disposition:** **Pass within the requested scope.** Attempt05's two-file checksum list passes; its recorded attempt03 and attempt04 predecessor hashes match the files reviewed here; current Roseburg wording and the family-level brochure distinction are correctly bounded.

## Integrity and predecessor checks

`sha256sum -c SHA256SUMS` passed for attempt05. The attempt03 verifier passed with 31 source pins and six terminal artifact hashes; its independent-review checksum passed as well. Attempt04's `SHA256SUMS` passed for both listed files. Attempt05's declared predecessor digests match the current attempt03 and attempt04 files. Exact expected and observed values, including the hash-list files themselves, are recorded in `integrity-manifest.json`.

| Frozen file | SHA-256 |
| --- | --- |
| Attempt03 `source-pins.sha256` | `6d438d30d4f9b3034b5a6c13f208d5c903349a2a346034db77989686fedca27c` |
| Attempt03 `terminal-hashes.sha256` | `874492312a7627742c9363e649d0ae89392a74a13b13773aca5ddbf81323739a` |
| Attempt03 independent-review report | `00e33c3fd36d9c678ac7cdc4119801dbb2000b5a4a864c1939398db3f70eeac4` |
| Attempt03 independent-review manifest | `1af52acf69033f2eb05fdd392893414a3ad2a5fe2834a3ec4ab23669b81b5842` |
| Attempt04 `SHA256SUMS` | `ea84b9912b7675236719dd97b5d2dfdff1b1819a4987e03b149a7c2c8247613c` |
| Attempt04 README | `6d0d3ebf5977b29b0473f5142b3603c9b4e97a9f42320a2d9bb7acaedc03e0ab` |
| Attempt04 `source-observations.json` | `11dbae6d11b2010cca54a5c68602f6da1c0826ef19517136ba34b057852b3c3b` |

## Current manufacturer and retailer evidence

I opened the current official Roseburg Exterior Core page on 2026-09-28. Its card is titled **AC Sanded Plywood** and states 23/32 in, five ply, a fully sanded face, and a touch-sanded back. The page's family description says Exterior Core panels use western-wood veneers. It does not identify Lowe's item 12235 or model 119055; searches of the rendered page for both identifiers returned no match. The attempt05 correction from “AC Fir Plywood” to the current card wording is accurate. [Roseburg Exterior Core](https://www.roseburg.com/softwood-plywood/exterior-core/)

Roseburg's official brochure has an **AC SANDED** section with an “Exterior Core Panels” specifications and packaging table. Its 23/32 row reads “5 & 7 ply.” That is a family/packaging range and supplies no Lowe's item/model cross-reference. It is properly kept distinct from the current website card's option-level “5 Ply” statement; neither is assigned to model 119055 or received sheets. [Roseburg Sanded Plywood brochure](https://www.roseburg.com/wp-content/uploads/2026/03/SandedPlywood_Brochure.pdf)

Lowe's currently displays Item 12235 / Model 119055 and lists Douglas fir, AC sanding, and 23/32-in thickness. Those are retailer listing claims. The Roseburg page does not join either Lowe's identifier to its card. Thus attempt05 correctly keeps the manufacturer-product crosswalk, exact model species, exact layup, per-ply species/thickness/sequence, physical-sheet identity, and lot link null. The statement that Lowe's lists Douglas fir remains distinct from a manufacturer-confirmed species for an identified Roseburg option. [Lowe's product record](https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973)

## Readiness and applicability limits

The observation record leaves sheet-to-body mapping, panel axes, orthotropic properties, material card, and solver body/element/DOF assignment null. It keeps `inputs_ready`, `criteria_accepted`, and `release` false. Its change-boundary flags also state no predecessor, queue, manifest, geometry, method-map, artifact-manifest, or material-assignment change; no receiving, inspection, or solver run occurred. I found no readiness or acceptance claim that contradicts those boundaries.

The live Roseburg and Lowe's pages were not saved as byte captures, so this review confirms their rendered content as observed on the review date rather than pinning future page revisions. The brochure's row is not an exact model-specific layup; the website's five-ply option is not linked to Lowe's model. The Lowe's species field does not authenticate the delivered sheets or establish their veneer species ply-by-ply. This review establishes no physical receiving, inspection, solver readiness, or candidate acceptance.
