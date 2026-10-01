# Plywood product crosswalk — attempt04

**Disposition: descriptor match narrowed to Roseburg’s named AC Fir option; Lowe’s model crosswalk remains unresolved.** A fresh review of the current official Lowe’s listing and Roseburg product page finds that the Roseburg page names an AC Fir Plywood option at 23/32 in, five ply, with an A-face sanded and C-back touch-sanded finish. The same page lists distinct 23/32-in BC Plugged and CCPTS options with seven-ply descriptions. This gives the owner-designated Lowe’s item a specific Roseburg option-level descriptor match. Neither page supplies a shared manufacturer identifier or explicitly states that Lowe’s item #12235/model #119055 is that Roseburg option.

This is a bounded source-observation successor to attempt03. It records current live-page detail and access limits; it does not amend attempt03, the T05 queue, a manifest, candidate geometry, a method map, or an artifact manifest. It assigns no sheet layup, properties, axes, solver material, or receiving identity. Readiness, release, and criteria remain false.

## Source-backed boundary

| Record | Official source observation | What it supports | What it does not support |
| --- | --- | --- | --- |
| Lowe’s item #12235/model #119055 | Lowe’s displays the retail item and model identifiers and lists 23/32 CAT, PS1-09, Douglas fir, Exterior exposure, A-face/C-back, and one-side sanding. | The owner-designated retail identity and its listing descriptors. | A Roseburg product/SKU code, manufacturer catalog number, supplied-sheet identity, or exact veneer schedule. |
| Roseburg Exterior Core page | Roseburg names “AC Fir Plywood” at 23/32 in, five ply, with an A-face sanded and C-back touch-sanded finish. Its current page also lists BC Plugged and CCPTS at 23/32 in with separate seven-ply descriptions. | A specific current Roseburg option with strong descriptor alignment; the visible options distinguish other same-thickness constructions. | An explicit cross-reference to Lowe’s #12235/#119055, an exact ply schedule, or proof that the owner’s sheets are this option. |
| Roseburg Sanded Plywood brochure | The March-path brochure’s AC Sanded section describes its family and lists 23/32-in Exterior Core packaging as “5 & 7 ply.” The document labels the relevant section “AC SANDED 013026.” | Family/packaging-level range and the fact that the brochure does not resolve which construction belongs to Lowe’s model. | Mapping the 5/7-ply range to the retail model or delivered sheets. |

The most specific defensible statement is: **Lowe’s listing descriptors align with Roseburg’s named AC Fir option, which Roseburg currently describes as five-ply; the public sources reviewed do not join Lowe’s model 119055 to that option.** A descriptor match is not an authenticated model crosswalk. The brochure’s 5/7-ply family range does not negate the current AC product-card description and does not identify which construction, if either, applies to model 119055.

## Missing link and next source action

The exact missing link is a shared manufacturer-controlled identifier or an explicit Roseburg statement mapping Lowe’s item #12235/model #119055 to Roseburg’s AC Fir Plywood option and its applicable construction record. The current accessible Lowe’s page shows its retail item/model identifiers; the current Roseburg product page shows option names and descriptions. The reviewed text exposes no common Roseburg SKU, manufacturer part number, UPC, packaging code, or model reference.

Next, obtain written confirmation from Roseburg technical/customer support that explicitly names Lowe’s item #12235/model #119055 and identifies the corresponding Roseburg product code and construction record; retain the response and any referenced current specification. Separately, when physical sheets are available for receiving, transcribe or photograph their complete panel stamps and package/lot labels and link those records to the owner’s purchase record. Neither action is represented as completed here.

## Scope and limits

The sources were directly opened or searched on 2026-09-28 using the official Lowe’s and Roseburg domains. The live retailer and manufacturer pages have no stable edition date visible in the reviewed text. Their full web responses were not saved as local page captures, so no external page-content hash is claimed. The brochure was opened as an official eight-page PDF; the URL path includes `/2026/03/`, and the AC section carries the printed code `013026`. The local attempt01 brochure snapshot is predecessor evidence, not a new capture of this retrieval.

Exact identifiers `119055` and `12235` were searched on Roseburg’s official domain. The search did not return a Roseburg cross-reference, but search indexing is not exhaustive and this is not proof that no private/distributor record exists. Roseburg’s linked dynamic Literature Library was reachable, but the browser text view exposed the library controls and a Search Results heading without document results; that rendering limit is not treated as evidence that the library contains no relevant record. Lowe’s linked product-image resources returned cache-miss errors through the browsing interface and were not inspected for panel marks.

No physical receiving, panel inspection, layup assignment, property assignment, solver-card or body/element/DOF assignment, native run, geometry or criteria change, readiness change, or release change was made. Attempt03’s null fields and its independent review remain the controlling prior record for exact panel/body assignments.

## Reproduction and integrity

This packet contains `source-observations.json`, a bounded transcription and comparison of the official-source observations. It intentionally does not claim byte capture or checksums for live external pages. Verify packet integrity with:

```sh
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-plywood-product-crosswalk-attempt04/SHA256SUMS
```

