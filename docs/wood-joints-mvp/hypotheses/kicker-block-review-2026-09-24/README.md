# Kicker block model review, September 24, 2026

The local [3D viewer](http://localhost:8765/wood-joints-wj24-viewer.html) now
shows `outer-rim-inner-frame-blocks-v1`. This is an owner-review geometry
revision of `compact-floor-flush-wood-joints-development`. Joint evaluations
remain paused until the owner signs off on this model. No joint mechanics,
native solve, capacity calculation, or physical work was performed for this
revision. Selected-baseline authority and historical evidence remain unchanged.

## Model changes

- Preserve the middle corner blocks below their rails and the bottom rear
  support 5 mm above the first T-nut flange row.
- Move the two center kicker uprights to the exterior sides of the central
  kicker T-nuts, with 5 mm nominal flange clearance. Move four kicker screws
  onto those uprights. Remove the two adjoining center backers and their four
  header-bolt stacks.
- Replace the central principal/header cleats with plumb solid blocks,
  88.9 × 139.7 × 139.7 mm, seated flat on the existing header. Move their four
  cross-bolts and four vertical header bolts; the latter clear the moved posts.
- Add an interior block at each outer 4×6 rim. Extend the existing two side
  bolts per side through exterior block, rim, and interior block. Add one
  downward vertical bolt through each interior block and the kicker header.

The model retains 66 panel/kicker screw axes: eight moved (four in this
revision, four in the earlier bottom-support revision) and 58 unchanged.
Panel outlines and the purchased screw policy are preserved. Twelve starting
frame bolts remain. There are 28 candidate parts and 102 candidate bolt axes;
this count is separate from the twelve starting frame bolts. Longer bolt
solids are occupied CAD envelopes, not purchased-length or shank selections.

## Verification and open details

[Geometry checks](geometry-checks.json) record positive raw receiver occupancy
and cleared finished holes for all 14 newly added or restationed bolt axes.
Their hardware has no positive solid intersection with the modeled timber
or with other hardware among those 14 axes. The central blocks touch their
principals and header without solid overlap. The outer block helper checks
both seat interfaces. These are nominal geometry checks, not installation
access or complete joint evaluations. The earlier [kicker screw checks](../kicker-posts-outside-tnuts-2026-09-24/geometry-checks.json)
verify the moved screw receivers and removal of the old holes/backer bolts.

The fresh neighboring-solid screen finds the existing provisional G6
hold-bolt overlap, G2 light overlap, and ten wire crossings at the bottom
rails. The taller right central block adds a crossing of the F1–G1 wire.
Wire routing and those clearances remain open. Lower panel edge support and
the kicker center seam after backer removal require a complete detail; no
backing or load-transfer acceptance is inferred from the model.

The exporter regression tests pass (3 tests), and Ruff passes on the changed
helpers, exporter, and test. Browser results and images are stored alongside
this record. The scene contains 559 overlay solids and 536 visible baseline
assets. The viewer validates the source and report hashes before rendering.

[Revision](revision.json), [scene snapshot](scene.json.snapshot),
[verification](verification.json), helper snapshots, and the focused check and
export scripts preserve this checkpoint. The revision nests its immediate
predecessors; their claims remain historical. The source-bound scene is the
review artifact. The temporary export script consumes already-built live CAD
objects and is not a standalone baseline recomposition recipe.
