# Eight-bolt, zero-spacer development candidate

`v11-zero-spacer-eight-bolt-v1` retains **114 bolts, eight bolts at each affected joint and zero spacers**. This is an owner-authorized evaluation; the selected development model and selected baseline retain their separate authority. No purchase, drilling, fabrication or climbing release is granted.

[Local results viewer](http://127.0.0.1:8767/?model=eoere-v11-zero-spacer-preview&view=rear&holds=off) · [geometry receipt](geometry-receipt.json) · [six-case bank](response-bank.json) · [current reference summary](current-reference-summary.json) · [provisional hardware and marking-template packet](planning/README.md).

Only four cleat-post Grade 5 bolts change from 7 to 6½ inches; their four ½-inch spacers are removed and nuts move inward. All 114 axes, timber and cleat profiles, holes, fitting poses, heads and washer seats remain fixed. The frame retains standard actual 88.9 × 139.7 mm top and side rails, paired ½-inch upper-rear bolts, 24 angles and 66 Hillman axes. Each straight-sided cleat remains two glued nominal ¾-inch leaves, with 36.5 mm credited combined thickness. No wood packers or 102-bolt omission scheme is introduced.

The [conditional profile contract](hardware-profile-contract.json) specifies the four shorter bolts' body/root/runout requirements; it does not identify a qualified supplier SKU. The proposed profile has 4.166 mm of threads in each 88.9 mm post and threads throughout its steel flange. Both washers remain. Four compact nut approaches clear, but 100 mm approaches encounter perpendicular header hardware after 39.2875 mm; actual tools and assembly/service sequence remain unqualified.

## Completed conditional calculations

All six fresh cases and twelve independent replays pass the unchanged gates under 250 lb × 2 downward, 300 N horizontal, 25 kg accessories and CD = 1. Maximum gradient is 8.352509e-6 against the retained 1e-5 gate. One right-rear warm attempt failed recovered-wrench closure and remains rejected; its separately bound default-cold retry uses identical physical inputs and passes all body/global checks and both replays. No old force field is relabeled current.

| Reference component | Maximum |
| --- | ---: |
| Timber net shear/torsion, left side | 0.948106 |
| Timber normal/stability | 0.815913 |
| Cleat perimeter | 0.415393 |
| Separate elastic shaft steel | 0.411393 |
| Rear contracted common-work reference, 36 states | 0.775013 |
| Mixed contracted bearing, 144 states | 0.456194 |
| Four shorter post bolts: bearing / bending-hinge reference | 0.318308 / 0.193471 |

These are demand/reference comparisons within their stated component methods. They are not measured capacities or complete NDS joint acceptance. The perimeter worksheet checks all 255 nonempty subsets of each eight-bolt cleat; its governing seven-bolt subset does not remove the eighth bolt. The full eight-bolt subset is also checked. The new group interpretation preserves all signed forces and moments; legacy signature-based 1/n diagnostics remain historical comparisons, not adopted connection factors.

## Remaining flags and limits

The [mixed common-work check](mixed-common-work-summary.json) retains three rows above one under its generic A574 45 ksi Fyb scenario:

| Bolt | Case | Index |
| --- | --- | ---: |
| `v11_cleat_left_side_1` | a12-forward | 1.236622 |
| `v11_cleat_left_side_1` | a12-left | 1.199268 |
| `v11_cleat_right_side_1` | k12-right | 1.186203 |

The governing required Fyb is 55.647989 ksi. The separate full N/V/T/M elastic calculation requires Fy ≥ 332.318 MPa under its Fy/2 comparison. These are distinct properties; neither is inferred from the A574 proof minimum. Actual Fyb, Fy, Cg and Cdelta remain unassigned. The [twelve-cleat Grade 5 option](hardware-option-twelve-grade5.json) is review-only and unimplemented. Its saved held-force comparisons use the parent bank; a head/profile change requires its own matched evaluation.

The retained outer-top Table-D interpretation requires 47.625 mm between rows versus 41.275 mm available: a **6.35 mm shortfall** in the actual perpendicular a1-rear load allocation. Near-end comparisons retain flags at four new cleat-post axes and two top-beam axes. These details remain on hold; passing member sections or a favorable group factor does not waive geometry. Bolts 068/069 retain the net-away near-edge correction, with separate oblique/eccentric/splitting checks.

Three optional weak-edge rear-foot scenarios reach 1.004509, 1.089866 and 1.092722. Their signed alternatives and local couples remain recorded; the envelope flags are not blanket physical-failure findings. The [complete current summary](current-reference-summary.json) distinguishes these scenarios, the 216 connected parallel-transfer comparisons and unresolved coupled splitting/compatibility. The [fitting, washer and bond component summary](component-reference-summary.json) completes all 192 distinct coarse fitting states and two current governing fine comparisons, with maximum sampled fine stress 62.410 MPa. It also checks all 1,368 washer-end/case states; the minimum-thickness static construction requires up to 170.308 MPa washer Fy. The four direct-nut radii are corrected to 6.43509 mm; the former spacer radius is not retained. These are declared component constructions, with actual material, prying and complete-joint behavior still unqualified. The [independent arithmetic audit](error-audit.json) reproduces the bolt and geometry comparisons without a new numerical error.

The hardware packet contains 114 nuts, 228 washers, no spacers and 156 physical receiver rows. Twenty sawn members, four physical cleat leaves and six panels retain 30 profiles; five existing marking-prototype STLs are reused by hash. Actual/Disposition cells stay blank. Physical hardware, plywood/bond, contact, support and complete connection behavior remain unqualified; panel-screw resistance stays deferred by owner direction. Numerical consistency and packet completion do not grant physical release.

## Next authorized comparison

The owner has [authorized a separate 106-bolt trial](../owner-four-bolt-outer-top-evaluation.json): four bolts per outer top corner using the existing far-row holes, eight per cleat, four per center-top connection and zero spacers. Its three affected timber solids restore eight planned bores while retaining all exterior profiles. It requires its own mass, contact, six-case/replay and component calculations. The completed 114-bolt evidence above is preserved; no result or material change transfers automatically and neither trial is selected.
