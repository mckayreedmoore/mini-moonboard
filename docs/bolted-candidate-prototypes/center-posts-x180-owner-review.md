# Kerf-right center posts at X ±180 mm — owner-review layout only

The owner approved X = ±180 mm as the proposed center-post position for the
viewer concept. This is still a detached geometry trial, not a change to
selected or historical PB02 source. Do not cut, drill, purchase against, or
use it as a load rating.
The reproducible screen is `scripts/center_posts_outward_owner_layout.py`.

The two original 38.1 mm-wide posts move outward 110 mm (4.331 in) each:
left X −199.05…−160.95 mm and right X +160.95…+199.05 mm. Their original
Y and Z extents are unchanged. At 25.4 mm modeled flange diameter, KICK5
spans X −137.66…−112.26 mm and KICK6 +110.90…+136.30 mm. Nominal X
clearance from the moved posts is 23.29 and 24.65 mm, respectively.

All 66 panel/kicker screw starts, directions, and purchased lengths are read
unchanged from the kerf-right construction axes. Four screws at X ±70 mm,
Z 60/192 mm no longer enter the moved posts. Two nominal 88.9 × 88.9 mm
4×4 backers, from Z 0…238.9 mm, meet at the actual kicker seam X −1.5875 mm.
Their X extents are −90.4875…−1.5875 and −1.5875…+87.3125 mm; Y is
−124.9…−36 mm. Each backs its own inner kicker edge and the two fixed
center screw axes on that side. With the purchased 63.5 mm Hillman screw
length and recorded start, each modeled screw path enters 45.24375 mm of
backing wood and stops 43.65625 mm before its rear face. The modeled shaft
diameter is only the historical occupied envelope, **not** a measured
Hillman diameter or pilot specification. The backers meet the existing
header underside without overlap and receive **no structural-post credit**.

The 24 original bracket station identities, 144 SDS rows, and 12 frame-bolt
axes are preserved as an unchanged *duty ledger*, not as working connections
for the moved-post layout. At `clip_split_header_center_left` and
`clip_split_header_center_right`, all three original upright-side SDS axes
miss their moved post. Those two interfaces need a source-distinct bracket
placement and full joint check before any mechanical claim. The backers also
lack a qualified frame attachment; screw landing and nominal edge contact
alone do not establish a load path. Other hardware clearances, tolerances,
timber strength, and assembly order have not been checked. Disposition:
**REVISE / owner review only; no drilling release or native solve.**

Protected viewer-first 3D gates remain **unverified**, with no clearance
number assigned: every hold/T-nut and unused hold hole (not just KICK5/6),
installed hold-bolt protrusion, LED bodies and wiring, all 66 installed panel
screws (the fixed axes alone are not full hardware), and all 12 retained
frame-bolt stacks. The KICK5/6 numbers above are X projections only, not
an overall assembly clearance or tolerance result. No barrel-nut whole-frame
expansion is included.

Sources: `docs/floor-flush-construction-kerf-right/stock-profiles.json`,
`docs/floor-flush-construction-kerf-right/connection-axes.csv`,
`mini_moonboard/panel_grid_v2.py`, and `mini_moonboard/model.py`.
