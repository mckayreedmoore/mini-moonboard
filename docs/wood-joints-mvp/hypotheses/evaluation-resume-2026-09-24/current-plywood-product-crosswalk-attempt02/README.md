# Plywood product crosswalk — attempt02

**Disposition: partial descriptor match; exact model crosswalk and panel material assignment remain unresolved.** Fresh primary-source review found Roseburg's current 23/32-in AC Fir Plywood option and a product-page ply count of five. Its public page does not identify Lowe's item 12235/model 119055, so the model-specific layup remains null. No product-specific orthotropic property record or exact solver assignment was found.

This is a new source-evidence attempt. It preserves attempt01 and the attempt04 full-frame manifest. It does not edit geometry or authority files, claim physical receiving or inspection, set `inputs_ready`, create solver cards, or change a release state.

## What the records support

| Field | Supported record | T05 crosswalk result |
| --- | --- | --- |
| Owner-designated product identity | Lowe's identifies brand Roseburg, item 12235, model 119055. The owner's purchase record says “AC fir plywood” and points to that item. | The retail procurement identity is supported. No delivered sheet, lot, mill, or physical sheet-to-body identity is established. |
| Thickness, grade and rating | Lowe's lists 23/32 CAT, PS1-09, Douglas fir, A face/C back, one-side sanded, and Exterior exposure. | Supported as retailer listing assertions. No actual sheet-mark transcription is available. The listing gives no span rating, species-group mark, or Structural I mark. |
| Roseburg product record | The current Roseburg Exterior Core page lists “AC Fir Plywood” / “AC Sanded Plywood,” 23/32 in, 5 ply, O.C. 24 in, with an A face sanded and C back touch sanded. | Strong descriptor alignment, but the page does not name Lowe's item 12235/model 119055 or give a code that cross-references it. Treat the Roseburg option as a candidate match, not the verified model record. |
| Layup | The Roseburg page's AC option supports a five-ply count for that option. Its March 2026 brochure gives 23/32-in Exterior Core as a 5- or 7-ply family/packaging range. PS 1-09 Table 4 conditionally requires at least 5 plies and 3 layers if the panel is confirmed as Exterior A-C at 23/32 category. | `model 119055 exact layup = null`; veneer species by ply, veneer thicknesses, and sequence are null. None of the records maps an exact layup to the owner's Lowe's model and delivered sheets. |
| Principal material axes | APA says a panel's strength axis is its long dimension unless otherwise marked. | Generic convention only. No actual stamp/axis mark or physical sheet-to-STEP orientation is recorded, so all six global axes remain null. |
| E_L, E_T, G_LT, Poisson ratios, strengths and density | No Roseburg/Lowe's-model-specific property record was located. APA D510 covers recommended panel design capacities and design methods. | All requested product-specific values remain null. The reviewed design tables do not supply a complete 3-D orthotropic material card for model 119055. |
| Solver assignment | No material card or body/element/DOF map was produced for these panels. | Null for every body. |

The Lowe's page and Roseburg's manufacturer page align on the brand, AC description, category thickness, and face/back finish. That is useful corroboration, but it does not provide a direct product-code crosswalk. The brochure's broader 5/7-ply range also cannot identify which construction, if any, applies to model 119055. This attempt therefore does not transfer the Roseburg page's five-ply statement to the Lowe's model or to the six STEP bodies.

The PS 1-09 reference on Lowe's is retained as listed. NIST currently lists PS 1-22 as the current standard and PS 1-09 as superseded. PS 1-09 covers plywood requirements, construction, marking, and tests. Its Table 4 has a five-ply/three-layer minimum for an Exterior A-C panel in the 23/32 category, if those grade and category conditions are confirmed; that is a minimum rule, not the exact veneer schedule. The standard's requirements do not identify the Lowe's model's veneer sequence or provide the complete orthotropic constants needed for a 3-D solid material assignment.

## Exact geometry bindings

The six body IDs and STEP digests below are copied from full-frame manifest attempt04 and rehashed. They identify modeled geometry only. `crosswalk-status.json` preserves nulls for physical sheet IDs, exact model crosswalk, layup, principal axes, orthotropic properties, and solver assignment for every body.

| Current body | STEP SHA-256 |
| --- | --- |
| `main_lower_left` | `78e2bd7b3a3f4cb6f70a1a2156ae3143cb936b29e5560dd6fd0cf6142aac6270` |
| `main_lower_right` | `408d8ed97edf27954fa63221096af25da56a5aab02d53f77ecccbcfafb5b5d90` |
| `main_upper_left` | `4be26c61e59ca3c74f370989097f4bff9edf337fa4de1a30d7e5de9eb7ef52f7` |
| `main_upper_right` | `2791dca8f42b86a49b9e685f0f85d896642cbe9975a89bf1524bed89eddfea8f` |
| `kicker_left` | `4740a18f46b8e8ecc2c01c80f7966228c498e35a09f10d7ccb32b08ea3cd8691` |
| `kicker_right` | `d70c1fedf1c18304818a0f3adefdef0f64204f055a18d941ecd2b91a8dfe32b5` |

## Sources and reproduction

Fresh primary sources were reviewed on 2026-09-28. Direct URLs, retrieval dates, field observations, and local-copy status are in `source-register.json`. The current Lowe's, Roseburg and standards pages were not saved locally; their external-content hashes are therefore null. The old attempt01 source snapshots are preserved and their hashes are listed in both `source-register.json` and `source-pins.sha256` as predecessor evidence, not as the fresh web capture.

The principal sources are Lowe's' [model 119055 record](https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973), Roseburg's [Exterior Core product page](https://www.roseburg.com/softwood-plywood/exterior-core/) and [March 2026 Sanded Plywood brochure](https://www.roseburg.com/wp-content/uploads/2026/03/SandedPlywood_Brochure.pdf), NIST's [PS 1-09 standard](https://www.nist.gov/document/docps1-09structuralplywoodpdf) and [current-standard list](https://www.nist.gov/standardsgov/voluntary-product-standards-program), and APA's [plywood guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/) and [D510 description](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/).

From the repository root, verify the pinned source inputs and six body bindings with:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-plywood-product-crosswalk-attempt02/verify_crosswalk.py
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-plywood-product-crosswalk-attempt02/source-pins.sha256
```
