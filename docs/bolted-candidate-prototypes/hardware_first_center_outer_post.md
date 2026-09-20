# Outer-post HL35 center: lower-only trial — rejected

This is one bounded kerf-right installed-geometry trial, not a complete
center joint or a drilling plan. Regenerate the paired JSON with
`uv run python -m scripts.hardware_first_center_outer_post --output
docs/bolted-candidate-prototypes/hardware_first_center_outer_post.json`.

**Independent catalog rejection:** Simpson's HL35 3/5 series requires at
least 88.9 mm (3.5 in) of wood thickness at **both** bolt receivers. The
unchanged header is only 38.1 mm thick along its vertical bolt axes. The
common post is 184.15 mm thick along its transverse axes, but that does not
make the header applicable. This pose fails the connector's minimum wood
thickness before any collision or capacity question. The header is retained
only to document this rejected geometry, not as a suitable HL35 receiver.

One front-aligned solid post spans X = −92.075..92.075 mm, Y = −175.7..−36 mm,
and Z = 0..234.35 mm. It supports both kerf-right kicker inner edges,
including their X = −1.5875 mm seam, and preserves the receiving wood at all
66 frozen panel/kicker screw axes. The original full-span, one-piece solid
header remains at Z = 238.9..277 mm. The post is shortened by the assumed
4.55-mm plate thickness so the two inward-facing HL35 seats occupy the gap
under that header. This leaves no direct post/header timber contact in the
seat region; structural action through the brackets is unresolved.

The left and right full nominal HL35 vertical plates lie on the **outer X
faces** of the post, X = −96.625..−92.075 and 92.075..96.625 mm. Each runs
127 mm along Y and reaches 82.55 mm below its bend. The seats occupy
X = −92.075..−9.525 and 9.525..92.075 mm, leaving a 19.05-mm center gap.
Ideal full rectangular plate volumes do not intersect each other, fixed
panels, intended or neighboring timber. All six nominal 14.2875-mm bores
remain inside their receiving wood. The four header bore axes are separated
by 82.55 mm across X at corresponding Y rows, and none overlap. There is no
upper HL35 pair in this trial, so upper/lower header bore spacing is **not
applicable**; the upper principal/header connection is not designed here.

The two left/right vertical-leg hole rows coincide exactly in Y and Z.
They therefore represent **two shared full-width post through-bolt axes**,
not four independent side bolts or an independent 4+4 connection. Their
multilateral fastener action, plate load sharing, grip and bearing are
unresolved. For an illustrative 25.4-mm (1-in) washer outer diameter, the
same-row header washer discs have 57.15 mm clear edge spacing and post rows
have 38.1 mm along-Y clear edge spacing. These are radial spacing
comparators only: washer thickness, actual washer type, head/nut envelopes,
contact, tools and withdrawal paths are not established.

The frozen 50.8-mm occupied screw cylinders do not intersect the plates or
bores, and no screw loses modeled receiving wood. A conservative sensitivity
that treats the purchased 63.5-mm **overall** screw length as occupied shaft
does intersect the second shared post bore at both upper center kicker
screws: 4.629 mm³ per side. Purchased overall length is not verified shaft
occupancy, so this is a conditional collision, not proof of delivered-part
interference. The trial is already rejected by the catalog wood-thickness
rule; no drilling or capacity work follows. No ideal plate or bore intersects
the six panel solids, any other unmodified wood, or the 12 existing frame-bolt
occupied cylinders.
The JSON records every checked intersection and the original receiver
comparison.

The modeled post needs a one-piece 184.15 × 139.7 × 234.35-mm axis-aligned
blank; the unchanged header needs 2435.225 × 139.7 × 38.1 mm. A nominal
6×8 post blank and 2×6×10-ft header blank dimensionally contain them, but
the 2×6 header fails the HL35 minimum receiver thickness. A
2×6×8-ft header would leave only 3.175 mm total length before end trim,
kerf, defects and delivered-length variation, so it is not a production
blank. The earlier [6×8 retail lead](hardware_first_b66_center.md) was
pressure-treated; it does not verify an untreated DF-L No. 2 blank. The
10-ft header and post examples are dimensional envelopes, not confirmed
local inventory, grade, defect-free yield or machining feasibility.

The screen uses ideal 4.55-mm plate rectangles, an assumed 50.8-mm header
hole inset that is not dimensioned in the cited HL35 drawing, nominal
14.2875-mm wood bores, and a hypothetical 1-in washer outer diameter.
Delivered bracket holes/bends/coating, actual fastener stacks and accessible
installation, edge/end distances, upper joint, connector resistance, wood
resistance and complete force path remain unmodeled. The frozen axis cylinders
are analysis envelopes, never fabrication coordinates. The catalog thickness
failure alone rejects this lower-only trial; the conditional screw clash is
a separate diagnostic. Do not cut or drill from this trial.
