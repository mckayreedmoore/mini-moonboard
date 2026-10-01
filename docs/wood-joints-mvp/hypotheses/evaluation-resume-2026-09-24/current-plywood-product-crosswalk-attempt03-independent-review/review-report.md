# Independent review: plywood product crosswalk attempt03

**Review date:** 2026-09-28  
**Disposition:** **Pass within the requested bounded scope.** Hashes and the verifier pass; the corrected conditional PS 1-09 Table 4 statement matches the official standard; model-specific material and readiness fields remain unset.

## Scope and checks

I reviewed `current-plywood-product-crosswalk-attempt03/` read-only. The attempt verifier passed. All 31 source pins, all six terminal artifact hashes, the status-declared owner-record, full-frame manifest, Table 4 excerpt and six STEP hashes, predecessor snapshot hashes, and the three pinned attempt02 review artifacts match their declared values. The README's six geometry digests match the status records and full-frame manifest. Exact expected and recomputed hashes are recorded in `integrity-manifest.json`.

I independently opened the official NIST PS 1-09 PDF and checked the excerpt against Section 5.8, Table 4. The standard's Exterior A-A/A-B/A-C/B-B/B-C row group places the 23/32 performance category in “over 1/2 through 7/8”; that cell pair requires at least **5 plies and 5 layers**. The attempt03 excerpt reproduces those relevant cells, its digest matches the status and source-register declarations, and the corrected statement in the README and status JSON is accurate. [NIST Voluntary Product Standard PS 1-09](https://www.nist.gov/document/docps1-09structuralplywoodpdf)

## Null and readiness boundary

The six body bindings identify the pinned modeled STEP files only. The attempt leaves each panel's physical-sheet ID, Lowe's-model crosswalk, layup, global principal axes, orthotropic properties, and solver assignment null. Received-panel marks and product-specific layup, axes, properties, material card, body/element/DOF maps also remain unset. Material assignment, solver-card creation, solver assignment, native run, physical receiving, inspection claims, `inputs_ready`, and release change remain false. The Table 4 minimum is explicitly conditional; it is not assigned to model 119055 or to any STEP body.

## Applicability limits

The Table 4 rule applies only if the relevant PS 1-09 Exterior A-C grade and 23/32 performance category are confirmed for the material in question. Lowe's listing assertions do not establish those marks on delivered sheets. The excerpt records one bounded part of Table 4; it is not a complete saved copy of PS 1-09. The NIST PDF was independently checked live on the review date, while the attempt does not save byte-captured copies of Lowe's, Roseburg, NIST, or APA web pages. This review therefore confirms the requested NIST correction and local integrity chain; it does not establish a retailer-to-manufacturer product-code crosswalk, received-sheet identity, exact veneer schedule, physical condition, sheet-to-body orientation, full orthotropic material card, solver readiness, or construction acceptance.

No solver, physical receiving, inspection, geometry, criteria, or candidate-readiness change was performed.
