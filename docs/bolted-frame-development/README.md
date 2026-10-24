# Compact bolted frame development

This is the main entry for `compact-bolted-frame-development`.
The current geometry is **`v10-standard-4x6-top-and-sides-development-v1`**.
The [owner constraint](owner-frame-v10/owner-standard-side-4x6-v1.json) is implemented: top and both sides are **standard nominal 4×6, actual 88.9 × 139.7 mm**.
Fresh geometry, all six cases and both replays, net sections, grips, rear-joint geometry and clearance are complete. The old deeper-side results and bound group scenarios remain history.
Lengths around 2539.8 mm remain provisional; custom packers are **not approved**.
No purchase, fabrication, climbing or structural release. Failed probes and older evidence remain preserved.

[Preserved C13 viewer](http://127.0.0.1:8767/?model=eoere-current-frame-development&view=rear) ·
[Selected 4×6 local viewer](http://127.0.0.1:8767/?model=eoere-standard-4x6-top-and-sides-preview&view=rear&holds=off) ·
[preserved C13 layout](owner-frame-v10/layout.md) ·
[4×6 geometry receipt](owner-frame-v10/standard-side-stock/geometry-receipt.json).

The selected development model contains **1,151 occupied parts**, 116 bolts and nuts,
232 washers and 44 spacer pieces. Each cleat is two nominal **12.7 mm leaves
bonded into a 25.4 mm pair**; the perimeter reference credits only 23.8 mm.
The plywood hypothesis is PS 1 APA Group 1 sanded plywood, Other category,
with strength axis along local vertical Z. The actual product and bond remain unqualified.
Current vector indices: **left side 0.998500, right side 0.951121, top 0.575366, header 0.586700**.
The additional scalar peak-sum screen is **1.014932**; both calculations and their unchanged scopes are retained in the matched evaluation. This is not a physical safety margin.
There are **15 bearing diagnostic rows / eight bolts**; actual Cg and complete connection acceptance remain unresolved.

The [selected screw-and-bracket baseline](../../current-candidate.json) retains
separate authority and remains the viewer's no-query default. This integration
does not publish the local changes to the hosted site.

## Active builder reading path
| Need | Current record |
| --- | --- |
| Current model and changed members | [Selected 4×6 evaluation](owner-frame-v10/standard-side-stock-evaluation.json) · [geometry receipt](owner-frame-v10/standard-side-stock/geometry-receipt.json) |
| Material, hardware and operation holds | [Preserved C13 readiness](owner-frame-v10/candidate13/packet-13-complete/readiness.json) · [current scope and preserved instructions](builder-plan.md) |
| Buying list and catalog fit | [Current provisional wood plan](owner-frame-v10/standard-stock-planning.md) · [current planning CSV](owner-frame-v10/buying-list-current.csv) · [historical catalog basket](owner-frame-v10/buying-list.md) · [historical source check](owner-frame-v10/catalog-check.json); old 4×8 side allocation is superseded |
| Timber/profile planning | [Preserved C13 32-profile cut plan](owner-frame-v10/candidate13/packet-13-complete/cut-plan.csv); not updated 4×6 cutting instructions |
| Receiver coordinates | [Preserved C13 158-row drill plan](owner-frame-v10/candidate13/packet-13-complete/drill-plan.csv); not updated 4×6 drilling instructions |
| Own forces and references | [4×6 six-case response bank](owner-frame-v10/standard-side-stock/response-bank.json) · [component review](owner-frame-v10/standard-side-stock/reference-review.json) |
| All current trial flags | [15 case rows / eight component maxima](owner-frame-v10/standard-side-stock/diagnostic-inventory.json); preserved C13 retains 26/13 below |
| Applicable methods and remaining work | [Current connection methods and remaining work](owner-frame-v10/standard-side-stock/connection-method-evaluation.json) · [initial physical-row mapping](owner-frame-v10/standard-side-stock/connection-review.json) · [historical deeper-side comparison](owner-frame-v10/standard-top-stock/group-row-comparison-v1.json) · [read-first edge correction](owner-frame-v10/candidate13/paper-audit/center-principal-correction-13-v1.txt) · [corrected C13 completion](owner-frame-v10/candidate13/paper-audit/completion-index-v3.json) · [preserved audit](owner-frame-v10/candidate13/paper-audit/candidate13-paper-audit-summary-v1.txt) · [joint inventory](owner-frame-v10/candidate13/joint-applicability-13-canonical-wsl.json) · [task ledger](../wood-joints-mvp/completion-ledger.md#current-v10-candidate13) |
| Provenance and preservation | [Revision index](development-revisions.json) · [portable source mapping](../../site/eoere-v10-candidate13-provenance.json) · [frozen delivery manifest](owner-frame-v10/candidate13/delivery-bundle-13.json) |

The [frozen builder plan](owner-frame-v10/candidate13/packet-13-complete/builder-plan.md)
is a conditional planning packet. Buying structural stock/hardware, cutting,
drilling, structural assembly and climbing remain on hold. Actual/Disposition
cells remain blank. Availability and non-structural layout do not clear those holds.

## Preserved Candidate 13 changes

The top rail is actual **50.8 × 139.7 mm**, with its upper face retained.
Four top angles gain eight near beam-flange bolts; their near post-flange holes
remain omitted. The outer top angles move 50.8 mm inward onto solid packers.
Both sloping sides become actual **88.9 × 152.4 mm**, adding material behind
the retained front faces and bolt grips. The center-principal upper ends are
trimmed 12.7 mm to retain the top seat.

Each cleat outline is **410.3 × 215.9 mm** and gains three direct wood bolts.
The original steel-crossing pairs and four lower cleat/post stacks remain.
Fourteen cleat stacks have revised grips/spacers. Upper rear-leg joints retain
two nominal ½-inch Grade 5 bolts per side, revised diagonal stations and
50.8 mm added rear-leg end material. Four shared header bolts are added;
the lower rear-foot stacks use nominal ½-inch Grade 5 hardware.
The six wall panels and 66 Hillman screw policy remain.

These actual dimensions need appropriate larger solid stock. Earlier nominal
4×6 stock cannot yield the side depth, and nominal 2×6 stock cannot yield the
top thickness. The optional 9.525 mm center-principal back-depth envelope and
alternative top-grid patterns in the paper audit have not been modeled or adopted.

## Preserved Candidate 13 six-case results at 250 lb

The retained recipe is **250 lb × 2.0 downward**, 300 N horizontal action,
self-weight, 25 kg accessories and CD = 1. The six cases are a12-forward,
a12-left, a12-rear, k12-right, k12-rear and a1-rear. Each has two admitted
independent replays. Maximum normalized gradient is **2.713029e-6**, below
the unchanged 1e-5 gate. This verifies the conditional model's consistency,
not a physical strength rating or complete bouldering-impact envelope.

| Conditional reference | Candidate 13 maximum |
| --- | ---: |
| Legacy group-reduced N/M diagnostic | 0.997005 |
| Separate direct elastic steel reference | 0.422766 |
| Timber net shear/torsion, top rail | 0.931580 |
| Sloping-side vector shear/torsion | 0.899491 |
| Timber normal/stability envelope | 0.821212 |
| Cleat perimeter, credited 23.8 mm | 0.669241 |
| Wood bearing with retained trial group factors | **1.960159** |

All **26 trial bearing case flags across 13 components remain recorded**.
The 1/n signature penalties are not established NDS load-aligned rows or
adopted Cg values. The 0.997005 diagnostic does not establish a physical
0.3 percent margin. Its local formula and the bearing screen do not replace
the minimum of all applicable NDS yield modes or a compatible complete
force-and-moment connection assessment. No Cg or Cdelta is waived or adopted.

The average sawn-wood washer-face subcheck reaches **0.151452** on the declared
Fc-perpendicular basis. It excludes steel/plywood seats and does not qualify
preload, pressure peaks, washer bending/fit or full axial transfer.
Computed timber-node movement reaches **25.233992 mm / 2.220044 degrees**;
these are model diagnostics, not measured displacement or an adopted movement limit.
Screw withdrawal reaches **1,573.098 N with 573.319 N simultaneous lateral action**;
no Hillman resistance or force-slip index is qualified.

## Engineering work and source boundaries

The [continuation](owner-frame-v10/continuation-evaluation.json) preserves C13 work.
The active criteria use physical rows/shear planes and complete force/moment transfer.
Signature 1/n remains diagnostic only. Historical row benchmarks are not transferred; the fresh equal-EA scenario remains conditional;
actual Cg, the cleat three-media factor and complete connection acceptance remain null.
Panel-screw work is deferred and the agent review loop is suspended.

The [center-principal correction](owner-frame-v10/candidate13/paper-audit/center-principal-correction-13-v1.txt)
controls earlier summaries: 068/069 act away from the near edge in all six
cases. The idealized near-unloaded 1.5D/opposite-loaded 4D screen clears.
Both-edges 4D is optional conservatism, not an established NDS violation;
local pressure reversal does not automatically change that classification.
The [group/relocation handoff](owner-frame-v10/candidate13/paper-audit/wsl-group-and-relocation-handoff-v1.txt)
calls for a justified physical-group replacement for 1/n, preserving forces
and couples. Cross-standard efficiencies are comparisons only. Translating
an angle cannot fix its internal top-grid pitch; no relocation is adopted.
All 116 axes now have six-case signed-wrench coverage and conditional same-field material references; complete capacity remains unresolved.
The current washer mean-pressure index is 0.152000. The top-grid perpendicular endpoint has a conditional 6.35 mm shortfall; actual applicability remains open.
The [cleat input interpretation](owner-frame-v10/standard-side-stock/cleat-input-interpretation.json) proves stale labels did not affect solved geometry, mass or half-inch stiffness. Verify product
body/root/grip/washer/spacer assumptions, actual plywood/bond, the 66 screw
connections, and finite-motion/contact/support applicability. Numerical
convergence alone cannot close those checks. No floor test or blanket new
external sign-off prerequisite is introduced.

The 57 imported artifact roots retain their original bytes or decoded hashes;
six large JSON files use lossless gzip. The unique compressed scene is about
1.19 MB and shares the unchanged V9 mesh chain. Raw case/operator banks and CAD
remain in the retained isolated source package; portable checks do not claim
they were copied or re-solved. Historical stage/status fields remain frozen;
the current revision index and additive provenance map identify this integration.

<a id="current-96-bolt-results-at-250-lb"></a>
## Preserved V9 and earlier results

[Preserved V9 viewer](http://127.0.0.1:8767/?model=eoere-owner-frame-v9-development&view=rear) ·
[V9 response bank](owner-frame-v9/response-bank.json) ·
[V9 component review](owner-frame-v9/reference-review.json) ·
[V9 criterion correction](owner-frame-v9/criterion-scope-review.json) ·
[V9 testing audit](../wood-joints-mvp/completion-ledger.md#current-v9-testing-audit).
V9 retains 96 bolts and glued nominal ¾-inch leaves; its results do not transfer to V10.

<a id="revision-map"></a>
<a id="revision-map-and-retention"></a>
The [revision index](development-revisions.json) preserves V9 and every earlier
viewer/receipt. Earlier 92/94/102/106-bolt evaluations retain their exact scope.
Selected-baseline passes do not qualify this development candidate. Current V10,
V9, earlier dependencies, rejected candidates and source packets remain active
and recoverable. No archive, pruning, physical inspection or release is performed.
