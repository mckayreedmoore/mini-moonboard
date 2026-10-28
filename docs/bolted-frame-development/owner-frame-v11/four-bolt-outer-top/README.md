# Four-bolt outer-top comparison

`v11-four-bolt-outer-top-v1` is the owner-authorized **106-bolt, zero-spacer evaluation**: four bolts at each outer top corner, eight per plywood cleat and four at each center-top connection. It remains separate from the selected 112-bolt development model and selected baseline. No structural or physical-use release is granted.

[Local results viewer](http://127.0.0.1:8767/?model=eoere-v11-four-bolt-outer-top-preview&view=rear&holds=off) · [owner decision](../owner-four-bolt-outer-top-evaluation.json) · [checked geometry](geometry-receipt.json) · [six-case bank](response-bank.json) · [current references](current-reference-summary.json) · [hardware and marking packet](planning/README.md).

Only eight outer-top near axes and their hardware/planned timber bores are omitted. Three timber solids restore those bores for fresh stock. All exterior profiles, remaining stations, 24 fitting poses and 66 panel/kicker axes stay fixed. Top and both sides remain standard actual 88.9 × 139.7 mm stock, without wood packers. Each cleat retains two glued nominal ¾-inch leaves, with 36.5 mm credited combined thickness. The eight unoccupied steel factory holes remain. This is not a physical hole-repair method.

The geometry has 1,055 occupied parts, 106 nuts, 212 washers and no spacers. All 86 occupied-pair queries pass. The modeled mass decreases 0.779671 kg relative to the 114-bolt parent. The four shorter Grade 5 post bolts remain partially threaded; zero spacers does not select fully threaded hardware.

## Completed conditional calculations

The [matched bank](response-bank.json) and [parent admission](parent-bank-admission.json) bind six fields and twelve independent replays at the unchanged 250 lb × 2 downward, 300 N horizontal, 25 kg accessories and CD = 1. Four cold-case rows remain literal; a12-rear and k12-rear use refinements initialized from their own current iterates. Their physical operator arrays, applied loads, material and geometry are exact originals. Their residuals are 1.117587e-8 and 1.291007e-8; the final six-case maximum is 7.187459e-6 against the unchanged 1e-5 gate. All 1,525 current field-source pins verify.

The [initial six-cold-case bank](response-bank-initial.json) remains preserved. It passed the largest-component frame gate but missed one bolt vector-norm gate and one header construction gate. The [precision controls](precision-software-controls.json) tighten only two internal stopping comparisons to 1e-7. All 636 bolt closure and six header construction checks now pass their original gates. No acceptance gate, physical law or applied load was weakened.

| Conditional reference | Maximum |
| --- | ---: |
| Timber net shear/torsion, left side | 0.907575 |
| Timber normal/stability | 0.794245 |
| Cleat perimeter, 36.5 mm credited wall | 0.412377 |
| Separate nominal-section elastic shaft reference | 0.399838 |
| Rear contracted common-work reference, 36 states | 0.778825 |
| Mixed contracted bearing, 144 states | 0.459658 |
| Four shorter post bolts: bearing / bending-hinge reference | 0.320422 / 0.193181 |

All eight bolts remain installed per cleat. The perimeter worksheet checks every one of 255 nonempty subsets per component/case/thickness branch; its governing six-bolt subset is a critical path, not an omitted-bolt scheme.

The [fitting, washer and bond packet](component-reference-summary.json) and [controls](component-reference-controls.json) complete 192 distinct coarse fitting states and two actual governing 3 mm comparisons. The larger fine sampled stress is 62.666857 MPa, requiring 104.653652 MPa Fy under the declared 1.67 comparison. The two coarse-to-fine changes are about 1.98%; this is not an all-state fine-mesh envelope or continuum peak bound. All 1,272 washer-end/case states are checked: the minimum-thickness static construction requires up to 169.353697 MPa washer Fy. All 24 direct-nut and 24 Style-1-head face sensitivity rows use their corrected radii. Twelve signed bond-plane reductions are included; required transfer is not a qualified adhesive allowable or peel bound.

The current wood packet retains 4,536 full cut wrenches, 456 individual components, 948 supported Appendix E component rows, 216 connected parallel-transfer comparisons and 792 signed wood actions. Unsupported transverse/coupled splitting and applicability stay distinct. The reference controls verify 233 source files; component controls verify 175 source paths (172 distinct content hashes).

## Remaining flags and limits

The generic 45 ksi branch retains these separate bending and full N/V/T/M elastic comparisons:

| Bolt / case | Mp/4 bending | Separate elastic, assumed Fy = 45 ksi |
| --- | ---: | ---: |
| `v11_cleat_left_side_1` / a12-forward | 1.230185 | 1.065769 |
| `v11_cleat_left_side_1` / a12-left | 1.190534 | 1.041425 |
| `v11_cleat_right_side_1` / k12-right | 1.177982 | 1.030881 |

The governing bending requirement is Fyb ≥ 55.358346 ksi. The [separate 60 ksi comparison](material-comparison.json) gives maxima 0.922639 and 0.799327 on the identical fields/profiles, with Grade 5 retained at 92 ksi. That additional conventional-yield/bending assumption is unadopted and is not a product guarantee. The nominal-section steel row above uses a different reference and does not clear these profile/material comparisons. Actual Fy/Fyb, Cg and Cdelta remain unassigned; no proof-to-yield conversion or Grade 5 head substitution is implemented.

Four near-end cleat-post locations remain flagged by the unchanged conditional oblique end method: `v11_cleat_left_post_1`, `v11_cleat_left_post_2`, `v11_cleat_right_post_1` and `v11_cleat_right_post_2`. There are 18 net-action and 16 primitive-action flag rows. Actual coupled applicability/splitting remains unresolved. The [past-arm relocation review](near-post-relocation-review.json) reuses identical local geometry: that option misses both cleat leaves and would leave six bolts per cleat, so it was not implemented.

The old outer-top two-row 41.275-versus-47.625 mm shortfall is absent because only the far-row bolts remain. This does not establish every geometry criterion. Far top-beam end distance is 65.0875 mm versus the separate full 7D marker 66.675 mm, a 1.5875 mm screening shortfall; applicable signed row/end treatment and any reduction remain separate.

Three optional rear-foot weak-edge envelopes remain above one:

| Joint / case | Envelope | Opposite-edge branch |
| --- | ---: | ---: |
| `rail_rear_bolt_left_1` / a12-forward | 1.008876 | 0.602522 |
| `rail_rear_bolt_left_1` / a12-left | 1.093296 | 0.652939 |
| `rail_rear_bolt_right_1` / k12-right | 1.096201 | 0.654674 |

These envelope flags are not blanket physical-failure findings. Legacy receiver-signature 1/n bearing and N/M tables also remain preserved as diagnostics, rather than adopted connection factors. Passing a component reference does not settle complete group, loaded-hole, fitting/contact, bond or splitting behavior.

The [planning packet](planning/README.md) contains 106 hardware and 148 receiver rows, the outer-top far-only mask, and five reused marking-prototype STLs. Delivered body/thread/runout, seating, tools and material properties remain unqualified; four conditional Grade 5 types lack supplier SKUs. Actual/Disposition cells stay blank. Panel-screw resistance remains owner-deferred. No purchase, cutting, drilling, fabrication, climbing or whole-connection release follows.

The [geometry source audit](geometry-source-classification.json) records one stale ancestral helper hash inherited from 114 and separately pins the live import; current solid bytes and mechanics pins verify. Raw inputs, original cold fields, rejected local checks, current refinements and roughly 2.45 GB of fitting output remain active in `fea/generated/v11-four-bolt-outer-top-v1/`, with the unchanged parent and shared mesh dependencies retained. No archive or pruning occurred.
