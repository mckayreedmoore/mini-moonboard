# Independent review — retained 3/4-in tool geometry source gap

**Decision:** supported with a scope limit. The source-gap disposition is justified for the four retained #407 axes: the reviewed Wera record supplies nominal size and selected family dimensions/features, but it does not bind a complete full-profile 3D model or dimensioned full-profile drawing. The conclusion is about the evidence in this packet and reviewed public sources; it is not proof that Wera has never issued or authorized CAD.

The four #407 axes are the only retained axes tied to the preserved 1/2-13 bolt reference with a 3/4-in head across flats. Marking those four `NOT_RUN_SOURCE_GAP` is justified because the missing jaw, head, neck, handle, and ring contours cannot be reconstructed reproducibly from published scalar dimensions and product illustrations. No tool motion or clearance was inferred.

The remaining eight retained axes map to Bolt Depot #367/#368. Those are 3/8-16 bolt references with 9/16-in heads across flats, so a 3/4-in tool comparator is the wrong size for them. Their `NOT_TARGETED_DIFFERENT_SIZE_REFERENCE` disposition is appropriate for this attempt, and it means inventory scope only. T07 still records every retained axis as identity-bound with operation clearance unresolved; T08 identifies these as preserved selected-baseline catalog references, with delivered identity unverified, current-candidate recheck required, and no wood-joint selection.

The exact-part Wera-attributed datasheet I located independently repeats the catalog dimensions and feature descriptions but contains no full-profile dimensioned outline or CAD geometry. Olander’s listing advertises a CAD model, but this review retrieved no model bytes or model identity metadata to establish Wera authorship/authorization, revision, datum, units, or hash. It remains an unverified lead.

## Verification

The source attempt’s verifier passed: all 18 pinned repository inputs and all four terminal artifacts match their recorded SHA-256 values. The detailed expected/actual digests, twelve axis dispositions, and public-source notes are in [independent-review.json](independent-review.json). The review did not alter the attempt, candidate inventory, or operation records. No geometry, solver, or physical-clearance work was run.

## Public sources reviewed

- [Wera 6000 Joker Imperial family page](https://www.wera.de/en/tools/6000-joker-ratcheting-combination-wrenches-imperial)
- [Exact-part Wera-attributed datasheet hosted by TestEquity](https://assets.testequity.com/te1/Documents/pdf/weratools/wera-tools-05073287001-6000-joker-ratcheting-combination-wrenches-datasheet.pdf)
- [Bolt Depot #407](https://boltdepot.com/Product-Details?product=407), [#367](https://boltdepot.com/Product-Details?product=367), and [#368](https://boltdepot.com/Product-Details?product=368)
- [Olander 05073287001 listing](https://www.olander.com/items/05073287001), treated only as a CAD lead
