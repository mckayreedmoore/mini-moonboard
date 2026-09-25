# Common blocks, added sandwich bolts and bolt orientation

The owner directed implementation of the seven-design consolidation, a second
vertical bolt through each interior sandwich block and the kicker header,
and bolt heads facing outward at the frame exterior or toward greater
head-side room at interior joints. The current viewer revision is
`common-blocks-two-inner-bolts-oriented-v1`.

Open the [local viewer](http://localhost:8765/wood-joints-wj24-viewer.html).
The model has **24 blocks in seven finished designs, 92 candidate bolt axes,
460 candidate hardware roles and 505 overlays**. It preserves the 66 existing
panel/kicker screw axes and twelve starting frame bolt arrangements.
Selected-baseline authority and all 725 baseline asset hashes are unchanged.
This is an owner-directed geometry revision, not joint or fabrication approval.

## Common block pattern

Fifteen blocks share one 88.9 × 88.9 × 119.7 mm blank and drilling pattern.
Seven blocks and 24 bolt axes changed from the preceding model. The associated
receivers were rebuilt from raw stock and retained cuts, removing the old
holes rather than adding a second unused pattern. The rebuilt finished blocks
match the earlier comparison's transformed common template within 0.03 mm³
symmetric difference. Moved shafts retain their modeled raw-timber grip and
clear their newly bored receivers. See [geometry checks](geometry-checks.json)
and the [seven-design grouping](block-designs.json).

The owner proposed three families, then clarified to standardize drilling
where it fits and retain necessary exceptions. A [separate body-only trial](three-family-body-trial.json)
finds no added timber/protected-object collisions for three common blank
families; it does not establish shared bore patterns or hardware clearance.
Those larger blanks are not adopted. The short G7 block and the differing
tall-node arrangements retain their patterns. The [stock review](../../corner-block-stock-review-2026-09-24.md)
maps every current blank to common 4×4 or 4×6 lumber.

## Second vertical bolts

Each interior sandwich block now has two vertical through-bolts into the
header, at global Y = −62.35 and −155.70 mm: 93.35 mm apart. The second
axis is 20 mm from the opposite Y edge of its block. That is a geometry
datum, not accepted edge-distance resistance. The new shafts pass through
both intended receivers and have no installed collision with the checked
timber, hardware, panel screws, LEDs, T-nuts, wires or provisional hold
envelopes. Both new stacks also clear the stated 30 mm diameter, 50 mm long
head/nut axial-access probes. Their modeled occupied lengths are inherited
from the first stacks; no purchased length or delivered shank is selected.

## Heads outward and interior head-side room

The [orientation audit](orientation-audit.json) covers all 92 candidate axes.
Fifty complete stacks reverse about their wood-bearing faces. Exterior side
bolts put heads on the outward X face; top-edge rail bolts put heads above
the top rail. Interior bolts choose the side with greater nominal axial
space, retaining their orientation when the difference is at most 5 mm or
both sides clear the 350 mm probe limit. The probe is 30 mm in diameter and
includes the modeled floor boundary. This is a bounded straight-access screen,
not a complete wrench sweep or assembly/removal sequence proof.

Reversals preserve each hardware solid's volume and bolt occupied length,
each bore solid and every block pattern. Bore receiver order is updated to
follow the new head-to-nut direction. The final combined-state
[orientation validation](orientation-validation.json) checks the reversed
stacks against the complete updated hardware arrangement, and checks retained
raw-timber grip. The existing twelve frame stacks remain unchanged.

## Findings retained for review

- The two bottom-center rail-bolt tails still reach the tall central header
  blocks. The earlier 3 mm shorter-tail sensitivity is preserved as evidence;
  a suitable purchased bolt length and delivered shank remain unresolved.
- At **G1**, the tall central principal/header block on model-right backs
  onto the 13 mm LED-hole projection beginning 16.706 mm behind the panel.
  It clears the modeled LED body but obstructs deeper axial access.
- At **G2**, the bottom-center member block on model-right begins 10 mm
  behind the panel and overlaps the modeled LED body by 56.797 mm³. This is
  an actual modeled occupancy conflict, not only a deeper-hole projection.
- Existing panel-edge support, wire routing, G6 and G12 provisional hold-bolt
  clearance findings remain open. The [LED-hole review](led-hole-review.json)
  distinguishes the LED body from the hypothetical 50.8 mm hole-axis probe.
- The 491-site midpoint report still describes the preceding
  `outer-rear-bridges-under-header-links-removed-v1` model. It has not been
  rerun after the drilling and hardware revisions; its page now labels that
  historical scope explicitly.

The [hardware budget](../../hardware-budget-2026-09-24.md) allows $150–200
before tax and shipping for all 104 structural bolt assemblies, including
the twelve frame stacks. Purchased Hillman screws add no new spending.
Unresolved long-bolt sourcing is an allowance, not a selected substitute.

The [revision report](revision.json), [scene snapshot](scene.json.snapshot)
and [verification hashes](verification.json) bind this viewer state. Producer
and check-script snapshots preserve the incremental procedure; they consume
the parent's already-composed CAD and are not standalone reconstruction
commands. No native solve or joint evaluation ran. Joint evaluations remain
paused pending the owner's explicit model sign-off.

The [Chromium check](browser.json) rendered the updated 24-block, 92-axis
scene with all baseline assets verified and no page errors or failed requests.
The historical midpoint page still displays five maps and 491 points with its
screened revision identified, including at mobile width. This checks browser
rendering and report identity; it does not rerun the midpoint geometry screen.
