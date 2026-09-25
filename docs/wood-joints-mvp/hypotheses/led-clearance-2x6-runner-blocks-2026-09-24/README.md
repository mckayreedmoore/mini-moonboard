# LED clearance and runner-seated exterior blocks

The current viewer revision is `led-clearance-2x6-runner-seated-blocks-v1`.
It implements the owner's thinner tall blocks, small G2 LED move, 2×6 exterior
sandwich blocks, and contact between those blocks and the floor runners.
The [previous consolidation](../consolidated-blocks-two-inner-bolts-2026-09-24/README.md)
is preserved as history. Joint evaluations remain paused for owner model review.

## Geometry changes

Both exterior blocks now use 38.1 × 139.7 × 276.3 mm blanks. Their inner faces
and all eight bolt axes stay fixed. Extending their bottoms down 6.35 mm closes
the gap to the runners. Each has 5,080.635 mm² of modeled contact, zero solid
overlap and a 6.35 mm overhang along Y; this is about 95.5% of its bottom face.
The new bottom strips have no intersections with the checked neighboring solids.
Contact geometry does not establish bearing capacity or a new accepted load path.

The eight exterior heads and head washers move inward 50.8 mm. Shaft envelopes
shorten by the same amount, preserving nut stations and tail ends. Four post
bolt envelopes become 101.6 mm (4 in), and four sandwich envelopes become
241.3 mm (9.5 in). These are modeled lengths, not selected purchased lengths
or verified delivered shanks. The reduced exterior wood grip needs joint review.
The frame's solid 4×6 members are unchanged.

The two tall central blocks are trimmed 5 mm at their exterior X faces and
5 mm at their tops, to 83.9 × 139.7 × 134.7 mm. Their bases and bore axes stay
fixed. Eight associated heads and head washers are reseated 5 mm; their shaft
envelopes move with them, retaining their modeled lengths. The two previously
clashing bottom-center bolt tails now have 2.077 mm minimum clearance.

G2's 13 mm LED hole and light body move 5 mm outward in X, from panel coordinates
(1400, 199.2) to (1405, 199.2) mm. The adjacent two wire endpoints follow that
move. The panel solid contains only the new hole, with unchanged volume to
numerical tolerance; this is a CAD revision, not an instruction to patch an
already drilled panel. G1 and G2 each have a clear 13 mm diameter, 50.8 mm long
rear path and 1.35 mm clearance to the nearby block. Both light bodies clear
the checked wood. This narrow path screen does not prove connector feeding.

## Counts and checks

There remain 24 blocks in seven finished geometric designs, including the
15 common main-member patterns. All 92 candidate bolt axes, the twelve starting
frame-bolt arrangements and the 66 panel/kicker screw axes are preserved from
the previous revision. No new panel fasteners or hold T-nut moves are introduced.
The changed bolt stacks have no installed interference in the focused checks.

The viewer has 508 overlay solids and 533 visible baseline assets. Three
revised electrical visuals replace their baseline instances; the 725 baseline
asset hashes are unchanged. All release flags remain false. Focused exporter
tests and Chromium rendering are checked separately from structural acceptance.

The G1–G2 wire still intersects the bottom-right rail, reduced from 532.196 to
515.757 mm³; G2–G3 has no checked intersection. Other recorded wiring,
panel-edge-support and G6/G12 hold-clearance findings remain open. The earlier
491-site midpoint maps remain historical; a future LED-midpoint review must
use the G2 datum override. No native mechanics or joint evaluations were run.

## Saved evidence

- [Revision report](revision.json), [scene snapshot](scene.json.snapshot) and [verification](verification.json).
- [LED and tail checks](led-and-tail-checks.json), [runner and exterior bolt checks](outer-block-checks.json), and [block grouping](block-designs.json).
- [Browser check](browser.json) and the saved source/driver snapshots in this folder.
- [Updated stock dimensions](../../corner-block-stock-review-2026-09-24.md) and [board weight](../../board-weight-2026-09-24.md).

The saved incremental builders require their recorded predecessor geometry.
The validation/export driver snapshots consume parent-session CAD objects and
are evidence of the executed checks, not standalone rebuild entrypoints.
