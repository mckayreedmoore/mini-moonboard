# Matching rear-bolt development trial

This **unselected 114-bolt trial** adds one matching ½-13 × 8½-inch Grade 5
bolt at each upper rear-leg joint. The two new stacks use the existing
G0340956 bolt, 2573 nut and two 15025 washers, with no additional spacers.
The reviewed timber and glued ¾-inch cleat outlines, all 112 existing axes,
24 fittings, 66 panel screws and four retained spacers remain unchanged.
Four modeled timber bores are added; no physical holes are claimed.

[Open the separate public trial viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-v11-matching-rear-bolts-preview&view=rear&holds=off) · [local viewer](http://127.0.0.1:8767/?model=eoere-v11-matching-rear-bolts-preview&view=rear&holds=off).
Publication passed [CI](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/40450848490) and [Pages](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/40461971018); five public viewer files match commit `1e366c6d2f1b` byte for byte.

The [geometry receipt](geometry-receipt.json) records 1,099 occupied parts,
114 stacks and 228 washers. The [fresh response bank](response-bank.json)
admits all six cases and twelve independent replays. Its maximum residual is
2.246134e-6 against the unchanged 1e-5 gate. Loads remain 250 lb × 2.0
downward, 300 N horizontal, 25 kg accessories, self-weight and CD = 1.
This establishes numerical consistency under the specified assumptions.

The [source-bound reference results](reference-completion.json) retain:

| Conditional reference | Maximum |
| --- | ---: |
| Timber vector shear/torsion | 0.946179 |
| Timber normal/stability | 0.833916 |
| Glued-cleat perimeter | 0.410813 |
| Independent elastic steel | 0.409168 |
| Generic45 / conditional92 force-only bolt references | 0.644472 / 0.509443 |
| Rear projected-bearing witness, Fe/5 and Mp/4 | 0.682571 |

All 36 rear bolt/case witness states are below one, with every saved signed
force, moment, axial force and torque retained. The continuous necessary
bearing bound peaks at 0.676721 across 72 receiver cases. These calculations
replace the earlier 1.279062 rear witness only for this changed trial; the
earlier 112-bolt evidence remains preserved.

The [affected connection components](affected-connection-components.json.gz)
recalculate 16 groups on the four newly bored members. Eligible reduced-depth
references peak at 0.736173; the separate foot planar reference is 0.652992.
Terminal interactions stay below 0.115. Supported Appendix E components remain
below one; 14 rows, 18 directional paths and two cleat cores remain excluded,
including the upper-rear side groups. Three optional both-edge foot envelopes
remain above one, maximum 1.093377. These method exclusions and envelopes
remain separate from full connection capacity.

The 35 bearing and 16 N/M flags remain fresh legacy-method diagnostics
for the unsupported signature-based group reduction. The 21 raw-port and
eight individual upper-bound flags remain inconclusive. Actual Cg/Cdelta,
complete joint capacity and structural acceptance remain unqualified. These
different scenarios are not added together as physical failures.

The new pins have only about **0.145 mm nominal margin** under the full 4D
edge and principal 5D row screens; the separate 2 mm allowance is not met.
The [fresh signed geometry/row inventory](geometry-applicability.json) covers all
140 wood actions and 156 physical leaf/wood stations per case. Bolts 068/069
still load away from their nearest edges in all six cases; their separate
oblique/eccentric/splitting checks remain open. Sloped-end and actual row-rule
applicability remain unresolved.
The top-grid interpretation, near washer/bend compatibility, complete fitting
and prying behavior, physical hardware, plywood/bond and no-slip support
assumptions also remain open. Contact-response work is separate; the saved
112-bolt contact findings are not transferred as new 114-bolt results.
Panel-screw resistance remains owner-deferred.

The provisional hardware delta is two bolts, two nuts and four washers.
The [112-bolt build-planning packet](../shorter-bolts/build-package/README.md)
does not include the two new upper-rear drilling positions. This trial is
available for review, with no purchase, cutting, drilling, fabrication or
climbing release. It does not replace the selected screw-and-bracket baseline
or automatically select a new development model.

Raw inputs, commands, all six fields, failed preparation/execution attempts
and reference recovery evidence remain active under
`fea/generated/v11-matching-rear-bolts-v1/`. No archive or prune was performed.

The [placement review](placement-review.svg) is a separate, unselected proposal
over the current 112-axis frame; its [coordinates and source limits](placement-review.json)
do not revise this solved trial. Moving each existing upper-rear axis 6.509 mm
and adding a matching ½-inch axis gives a 2.336 mm conditional edge/row margin.
The corresponding signed principal-end screen has 15.017 mm minimum margin.
The 48 saved rows from this solved trial supply direction context only: all
leg-host net grain projections point away from the nearby short positive-grain
end. Sloped-end, oblique/couple and actual group applicability stay open; no
Cdelta is adopted. A full 7D envelope at both ends is retained as a stronger
comparison rather than an actual failure finding.

The owner has now [authorized evaluation of those moved positions](owner-relocated-pair-evaluation.json)
as separate candidate `v11-relocated-rear-pair-v1`. This lifts the axis/hole
freeze only for the two specified existing upper-rear holes and their two
matching added companions. It assumes undrilled locations or suitable fresh
stock. The relocated trial now has its own
[checked geometry](../relocated-rear-pair/geometry-receipt.json),
[six-case bank](../relocated-rear-pair/response-bank.json) and
[conditional review](../relocated-rear-pair/reference-completion.json).
Its contracted rear reference is 0.775020 with zero of 36 states above one.
The [fresh mixed reference](../relocated-rear-pair/mixed-common-work-summary.json)
retains three generic 45 ksi bending flags, maximum 1.236282. This earlier trial's
bank and 0.769859 contracted reference do not transfer. Timber/cleat outlines, fittings, all other axes and the four
spacers remain fixed. Evaluation does not select or release either trial.
