# Independent review: plywood product crosswalk attempt02

**Review date:** 2026-09-28  
**Disposition:** **Correction required for one standards statement; the unresolved-material and no-readiness boundaries are otherwise supported.**

## Scope and method

This read-only review checks the frozen packet at `current-plywood-product-crosswalk-attempt02/`, its 17 repository source pins, its five terminal-artifact hashes, the manifest-linked panel STEP files, and the hash declarations embedded in its JSON records. The complete recomputed input list is in `integrity-manifest.json`. I also opened the cited Lowe's, Roseburg, NIST, and APA primary pages on 2026-09-28. Those live pages were not saved as local captures, so the browser review has no content hash; this is an explicit reproducibility limit rather than a failed local hash check.

## Findings

### F-01 — Correct the conditional PS 1-09 layer minimum

The attempt says PS 1-09 Table 4 gives an Exterior A-C, 23/32-category panel a minimum of five plies and **three layers**. Table 4's row group for Exterior A-A/A-B/A-C/B-B/B-C places 23/32 in “over 1/2 through 7/8”; the minimum there is **five plies and five layers**. The report's three-layer value is not the applicable minimum and should be corrected wherever it appears, including the README and the conditional constraint in `crosswalk-status.json`. It must remain conditional on the relevant grade and performance category being confirmed. The standard minimum still does not reveal a specific veneer schedule or tie the Lowe's model to a Roseburg construction. [NIST PS 1-09, Table 4](https://www.nist.gov/document/docps1-09structuralplywoodpdf)

This is a documentation correction. The mistake does not cause the attempt to assign a layup: exact model layup, per-ply species and thickness, and the six body layups remain null. It does mean the attempt is not ready to be treated as a fully accurate account of the cited construction rule.

### F-02 — Retailer and manufacturer evidence supports descriptor alignment, not a model crosswalk

Lowe's' current page identifies Item 12235 and Model 119055 and lists the product as 23/32 CAT, PS1-09, Douglas fir, A-face/C-back, one-side sanded, and Exterior exposure. Its displayed actual thickness is 0.718 in and is properly treated as listing data rather than a measurement of the purchased sheets. The owner-purchase record also preserves the owner's Roseburg / item / model identification and the “AC fir plywood” description. [Lowe's product record](https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973), [purchased-material record](../../../../purchased-materials.md)

Roseburg's current Exterior Core page describes its AC sanded option at 23/32 in and five ply, with a fully sanded face and touch-sanded back; the opened page did not identify Lowe's item 12235 or model 119055. Roseburg's March 2026 brochure gives 23/32 Exterior Core packaging as 5 or 7 ply at family level and describes an A face/C-grade core and back for AC sanded panels. Those statements corroborate the product description but do not identify which construction belongs to the retailer model or the delivered sheets. The attempt's null model-to-manufacturer crosswalk and its refusal to transfer the Roseburg card's five-ply count are correct. [Roseburg Exterior Core](https://www.roseburg.com/softwood-plywood/exterior-core/), [Roseburg Sanded Plywood brochure](https://www.roseburg.com/wp-content/uploads/2026/03/SandedPlywood_Brochure.pdf)

The product-page “O.C. 24” option is manufacturer-page context, not a received-sheet stamp or a direct Lowe's model cross-reference. The reviewed Lowe's listing itself does not supply a span-rating mark, species-group mark, or Structural I mark. The attempt keeps those values unset.

### F-03 — The standard-edition, generic-axis, and D510 scope statements are supported

Lowe's lists PS1-09, while NIST currently lists PS 1-22 as current and PS 1-09 as recently superseded. The attempt accurately preserves the older retailer listing instead of silently substituting the current edition. [NIST Voluntary Product Standards Program](https://www.nist.gov/standardsgov/voluntary-product-standards-program)

APA states that a panel's strength axis is its long dimension unless otherwise marked. The attempt applies that only as a generic convention and leaves actual marks, sheet-to-body orientation, and global body axes unset. APA describes D510 as recommended design capacities and methods for wood structural panels made under PS 1, PS 2, and PRP-108; that source is not presented as a model-119055 complete 3-D orthotropic material record. Those limits are reflected correctly. [APA plywood guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/), [APA D510 page](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/)

### F-04 — The geometry-only bindings and unset material/solver state are preserved

All six body IDs and STEP hashes in the attempt match the six plywood-panel rows in the pinned full-frame manifest and the local STEP files. The bindings identify modeled geometry only. For every panel, `physical_sheet_id`, `model_119055_crosswalk`, `layup`, `principal_axis_global`, `orthotropic_properties`, and `solver_assignment` are null. Received panel marks, global axes, product-specific properties, material cards, body/element/DOF maps, and readiness/release flags also remain unset or false. I found no contrary assignment in the reviewed packet. The exact six geometry hashes are:

| Modeled body | STEP SHA-256 |
| --- | --- |
| `main_lower_left` | `78e2bd7b3a3f4cb6f70a1a2156ae3143cb936b29e5560dd6fd0cf6142aac6270` |
| `main_lower_right` | `408d8ed97edf27954fa63221096af25da56a5aab02d53f77ecccbcfafb5b5d90` |
| `main_upper_left` | `4be26c61e59ca3c74f370989097f4bff9edf337fa4de1a30d7e5de9eb7ef52f7` |
| `main_upper_right` | `2791dca8f42b86a49b9e685f0f85d896642cbe9975a89bf1524bed89eddfea8f` |
| `kicker_left` | `4740a18f46b8e8ecc2c01c80f7966228c498e35a09f10d7ccb32b08ea3cd8691` |
| `kicker_right` | `d70c1fedf1c18304818a0f3adefdef0f64204f055a18d941ecd2b91a8dfe32b5` |

## Source-review record

The primary pages opened for this review were:

- Lowe's, model 119055: <https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973>
- Roseburg, Exterior Core: <https://www.roseburg.com/softwood-plywood/exterior-core/>
- Roseburg, March 2026 Sanded Plywood brochure: <https://www.roseburg.com/wp-content/uploads/2026/03/SandedPlywood_Brochure.pdf>
- NIST, PS 1-09: <https://www.nist.gov/document/docps1-09structuralplywoodpdf>
- NIST, current and superseded voluntary product standards: <https://www.nist.gov/standardsgov/voluntary-product-standards-program>
- APA, plywood guidance: <https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/>
- APA, D510 page: <https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/>

The review did not perform physical receiving, inspection, solver setup or execution, geometry changes, criteria changes, or a readiness/release change.
