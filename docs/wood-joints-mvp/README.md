# Wood-joint development

This is the active development lane for the Mini MoonBoard project:
`compact-floor-flush-wood-joints-development`. Start here for the current
engineering record. The selected screw-and-bracket baseline remains a separate
[preserved reference](../../current-candidate.json); its passes do not transfer.

## Current disposition

The **conditional model/shop packet is complete within its recorded scope**.
**Complete structural acceptance remains unresolved: all 47 formal criteria
remain pending and all eight release flags remain false.** Read the
[joint disposition](hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/mvp-joint-disposition.md)
for completed comparisons, their applicability and actual remaining limits.
Current work is the main-coordinated numerical assessment of the complete
joint system: record passing, failed and unsupported checks to decide which
model changes are needed. The completed conditional packet is its starting
record, not completion of that assessment.

| Record in this lane | Structural bolts / nuts | Washers | Governing scope |
| --- | ---: | ---: | --- |
| Reviewed 104-axis basis | 104 / 104 | 208 | Reviewed authority and preserved analytical/shop record |
| [Knee-bridge working packet](hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-working-package.md) | 108 / 108 | 216 | Complete conditional four-bolt proposal; **unadopted** |

Both retain 24 blocks, 44 timber blanks, 50 transport bodies and 66 purchased
Hillman panel/kicker screws. The proposal adds two transverse bolts in each
outer knee spine. Its forces, geometry and order are identified separately;
it does not replace the reviewed [candidate contract](../../wood-joints-candidate.json).

Use the [reviewed WJ24 viewer](https://mckayreedmoore.github.io/mini-moonboard/wood-joints-wj24-viewer.html)
for the recorded layout. Its [scene](../../site/owner-wood-joints-wj24-scene.json)
is the reviewed basis, not the later shop corrections or 108-axis proposal.
Current corrections are in the [joint addendum](hypotheses/mvp-resume-2026-10-01/assembly-package/current-joint-addendum.md);
the proposal has its own [drawing](hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-proposal.svg).

## Engineering reading order

| Question | Maintained record |
| --- | --- |
| What completed, and what remains unresolved? | [Joint disposition](hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/mvp-joint-disposition.md) |
| Which actions apply to the 104-axis basis? | [Working force register](hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/working-joint-register.md) |
| Which actions and parts apply to the proposal? | [108-axis packet and source index](hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-working-package.md) |
| What is known about splitting? | [All-joint demand/path assessment](hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/README.md) |
| What does the panel model assume? | [Panel path](hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-path-reconciliation.md), [material fidelity](hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-material-fidelity.md), [attachment comparisons](hypotheses/mvp-resume-2026-10-01/panel-attachment/README.md) |
| What are the formal acceptance boundaries? | [Completion ledger](completion-ledger.md), [47-criterion register](current-criteria-coverage.md), [criteria](criteria.json) |

Loads retain six cases with **250 lb × 2 downward, signed 300 N horizontal,
original 100 mm hold lever**, recorded gravity and the proportional 25 kg
accessory allowance. The 50 mm comparison and incomplete lighter-climber
branches are historical sensitivities, not selected loading envelopes.

Current physical top-rail comparisons are complete under the documented
placement, sharing and duration assumptions. The all-joint assessment covers
30 duties, 44 timber sides and 528 states; it supplies demands and candidate
paths, **not complete splitting resistance**. Panel head demand remains about
1871 N against the stated 930–984 N nominal references. Neither comparison
is an observed physical failure. Material/contact hypotheses, global
compatibility and stability, no-slip support and actual hardware remain explicit
limits. Permanent-load evidence retains its original force scope.
The disposition links each result to its own forces and method.

## Conditional operations and purchasing

The [assembly package](hypotheses/mvp-resume-2026-10-01/assembly-package/README.md)
and [shop guide](hypotheses/mvp-resume-2026-10-01/assembly-package/shop-guide.md)
join assembly/removal, individual-member transport, hardware and costs.
Use the [44-blank list](hypotheses/mvp-resume-2026-10-01/assembly-package/blank-cut-list.md),
[hardware specification](hypotheses/mvp-resume-2026-10-01/assembly-package/hardware-engagement.md)
and [washer census](hypotheses/mvp-resume-2026-10-01/assembly-package/washer-coverage.md)
for the reviewed record; the proposal's [shop delta](hypotheses/mvp-resume-2026-10-01/assembly-package/knee-bridge-shop.md)
and [order](hypotheses/mvp-resume-2026-10-01/assembly-package/knee-bridge-order.md)
identify its four additional stacks. Actual/Disposition cells remain blank.
No physical build, floor or delivered parts have been inspected.

## History and evidence recovery

Earlier work orders and method checkpoints are historical reading, not the
current task queue. The [design-history catalog](../history/design-history.md#archive-reading-groups)
keeps layouts, successes, failures and writeup material together. The
[previous landing-page snapshot](../history/wood-joint-development-summary-before-navigation-cleanup.md)
preserves its earlier numerical summaries and panel-comparison addition.

Published sources and notes retain their original evidence paths. Some frozen
arrays, geometry copies and receipts are ignored local inputs. Use the
[archive/recovery record](../repository-cleanup-evaluation-2026-09-28.md)
before replaying from a fresh clone or moving an older packet. Older geometry
and helpers can remain current dependencies; their dates do not establish
that they are disposable. Work on `master`, coordinate owned paths, and update
this entry rather than adding another routine checkpoint.
