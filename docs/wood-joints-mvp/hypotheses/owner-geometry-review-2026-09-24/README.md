# Owner geometry review, September 24

The current local review model incorporates two owner-directed changes:

- Four lower middle service-rail cleats and their 16 bolt stacks are reflected
  below the rails. Six adjoining hosts are remachined from raw timber and the
  current cut maps.
- The two bottom support rails, their four cleats and 16 bolt stacks move
  200 mm up the climbing surface. Four lower-panel Hillman axes move with them.
  Both lower panels are remachined, restoring the old screw openings and
  cutting the new ones. The screw count remains 66 and panel outlines remain
  unchanged.

Open the [local model](http://localhost:8765/wood-joints-wj24-viewer.html) and
[kicker connection sketches](http://localhost:8765/wood-joints-kicker-options.html).
The sketches compare a deeper header with direct timber seats against enlarging
only the upper center blocks. Neither connection alternative is selected or
incorporated into the model.

The parent ran the two incremental geometry helpers against the retained WJ24
CAD object. The first took 0.762 seconds and the second 6.013 seconds. Focused
geometry checks confirm eight bottom-block receiver contacts without solid
overlap or a gap, unchanged lower-panel bounds, material restored at all four
old screw openings, and clear new screw openings. The source baseline remains
unchanged. The final display has 568 overlay solids; 390 parent overlay rows and
all 725 baseline asset hashes remain identical. Four existing screw visuals
have explicit translations. See [verification.json](verification.json) and
[focused-checks.json](focused-checks.json).

Nine focused tests pass and the six new Python files pass Ruff. Browser smoke
verified the final scene, three camera buttons, five layer toggles and a
390-pixel mobile view with no page or request errors. See
[browser/result.json](browser/result.json). The later plain-language finding
captions leave the geometry unchanged.

The focused neighborhood check found provisional hold-bolt envelope overlaps
at G2 and G6, and ten existing wire segments crossing the raised rails. These
are recorded in [neighbor-hits.json](neighbor-hits.json). Lower-panel edge
support, wire passages or routing, hold-bolt clearance, and complete hardware
access remain open design details. The check does not establish a complete
installation or assembly path.

The [revision report](revision.json) is the current geometry record; the
[lower-block report](lower-blocks.json) records its preceding step. Reproduce
the geometry by calling `build_wj24_lower_blocks_below(g24)`, then
`build_wj24_bottom_support_up_one_row(lower_geometry, lower_report)`. The
incremental exporter consumes the resulting geometry and cumulative report,
using the preserved WJ24 scene snapshot as its parent. The current viewer uses
a separate design-review schema and carries no historical static or mechanical
passes forward. Force calculations remain on hold for owner design review.
