# Bottom-center same-side pair — detached owner-layout trial

This trial concerns only `clip_horizontal_bottom_left_2` and
`clip_horizontal_bottom_right_1`. It does not edit the selected frame, PB02,
PB06, or their evidence. The approved X ±180 mm center-post placement and
separate kicker-edge backers are included as layout context, not accepted
joint design. The two bracket duties remain identifiable; the twelve target
SDS axes are historical, not part of a selected through-bolt installation.
This first trial conservatively included PB02's historical right side cleat;
the later unified 24-duty assembly intentionally excludes that cleat and
rear-return chain. Its cleat result does not define unified-assembly topology.

Each proposed ordinary full-section block is 139.7 mm in local X, 57.15 mm
in local T, and 139.7 mm in local N, at the original same-side rail/principal
butt. Two generic 6.35 mm through-bolt paths cross each principal and block;
two cross each bottom rail and block. The local block N rows are 50 and
89.7 mm, while the rail row is 69.85 mm. Rail X rows are 50 and 85 mm from
the actual butt. This differs from the PB06 300/295 mm-long trial: shortening
local N physically removes its upper/front reach into the historical right PB02
`upright_side_cleat`. The right cleat intersection is **0 mm³** in this
trial. However, moving the second rail row to 85 mm did **not** solve the
left bore: its nominal core lies wholly outside finished
`base_rail_bottom_left` (0% rail coverage, 100% block coverage). It is not
a through-bolt path.

The screen uses finished kerf-right timber, retaining old target SDS voids
conservatively, and checks nominal contacts, all eight full core bores,
same-station bore intersections, unrelated timber and panels, and generic
outward tool/host paths. It screens candidate blocks, bores, generic hardware,
and tools against the shared finite protected inventory: 142 modeled T-nuts,
142 provisional 50.8 mm rearward hold-hole/bolt envelopes, 132 LED bodies,
131 wire solids, 66 panel screw shafts, and 12 frame bolt shafts. The
protected solids are nonzero-length; any reported hit is a revise finding.

The finite screen also found substantial protected-volume collisions. The
left block intersects the E1 T-nut by **736.888367 mm³**, its provisional
50.8 mm hold path by **4926.938504 mm³**, and `wire_049_E1_E2` by
**820.94328 mm³**. The right block intersects the G1 T-nut by
**804.105091 mm³**, its provisional hold path by **4926.938504 mm³**, and
`wire_073_G1_G2` by **820.94328 mm³**. Additional candidate bore, shaft,
and generic tool envelopes hit provisional hold paths or wires. These are
physical revise findings, not small discrepancies to waive. Neither block
nor its bores/tools hit the modeled 66 panel-screw or 12 frame-bolt shafts.

The delivered hold-bolt length, wiring bend/routing, purchased 63.5 mm panel
screw full-length envelopes and heads/driver access, frame-bolt heads/nuts
and tools, selected candidate bolt
lengths/tools, retained bracket/SDS installed solids, and other developmental
corner-block interactions remain **unverified**. The right PB02 side cleat
is protected as its full nominal blank, which is conservative relative to
its drilled shape. Old PB02/PB06 results do not transfer. No native solve,
mechanics verdict, cut list, drilling, fabrication, or structural release.

Disposition: **REVISE**, unselected. Reproduce with
`python -m scripts.owner_layout_bottom_center_pair` and its focused test
after obtaining the shared CAD test slot. The first focused run yielded two
passes and one failure because the initial test demanded a geometry advance;
the assertion now expects the observed REVISE witnesses and awaits a
serialized rerun. No fabrication or drilling follows.
