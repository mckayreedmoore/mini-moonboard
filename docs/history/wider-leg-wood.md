# Local wood checks for wider single-stock legs

The geometry-driven calculation is in
[`fea/wider_leg_wood_checks.py`](../fea/wider_leg_wood_checks.py). It accepts the
final member geometry, individual bolt forces and joint moment. Results from
an earlier bolt pattern do not qualify a subsequently moved pattern.

## Material and member calculation

The material basis is dry, unincised, grade-stamped US Douglas Fir–Larch No. 2,
actual 38.1 × 184.15 mm stock, normal-duration factor 1.0; permanent-load-only NDS cases use 0.9. The NDS 2024 size
factors for nominal 2×8 are 1.2 for bending and tension and 1.05 for compression.
The prior 2×6 size factors must not be carried forward.

Each transverse hole is conservatively replaced by a full-diameter square in
the member plane. The section sweep includes every square boundary and every
interval between boundaries. Thus staggered holes with overlapping grain
stations are removed together; holes are not assumed to affect only one section
each. Overlapping depth strips are unioned to avoid subtracting the same void
twice. The calculation derives net area, centroid shift and both section moduli.

The leg member check applies each conservative net section over the full supplied
supported length. The aggregate transports the joint-centroid moment to the leg stock centerline
with the conservative additional allowance `P × abs(q_joint)`, where the current
group offset is 3.279785 mm. The member check then includes that full supplied
sagittal moment, axial
force acting through the net-centroid offset, 19.05 mm face eccentricity for
single-lap transfer, and the entire transverse component of member weight
concentrated at midspan. Pin-ended column stability and a bending effective
length twice the supported length enter NDS 2024 equations 3.9-3 and 3.9-4.
No intermediate bracing or short-duration strength increase is credited.

## Parallel-grain local stresses

Actual bolt coordinates establish the rows independently in each member.
NDS nonmandatory Appendix E equation E.3-2b is implemented as
`n × Fv′ × thickness × critical_spacing` for each row, where critical spacing
is the lesser of the two end distances and the spacings in that row.
Every row demand is the sum of absolute parallel-grain forces in that row.
This avoids cancellation under joint moment.

Every contiguous group of at least two rows is also checked with equation
E.4-1: half the two bounding-row tear-out capacities plus the interior net
parallel-tension capacity. The interior area conservatively removes one complete
hole diameter for each interior row and half a diameter at each bounding row,
even where staggering prevents simultaneous full-hole cuts. The full member net
tension check uses the swept minimum area and the absolute sum of parallel
bolt-force components. These are local connection checks, not a determination
of the outer rim's entire longitudinal force/moment diagram.

## Cross-grain splitting

The supplemental EC5 comparison follows the primary references recorded in
[the splitting research](leg-splitting-research.md):
`F90,Rk = 14 b sqrt(he/(1 − he/h))`, reduced by `kmod/1.3`.
Medium-term `kmod = 0.8` and an additional 1.5 demand factor are explicit.
Permanent-load-only cases must instead use `kmod = 0.6`.

For each force direction separately, the calculation sums the positive
cross-grain components of every bolt force. It measures `he` from that
**loaded edge** to the most distant fastener in the connected group. Reversing
the member force reverses the loaded edge. This avoids assuming symmetric
placement or reusing the old rim-only axial splitting result after moving the
six-bolt group. The comparison supplements NDS §3.8.2; it is not an invented NDS
perpendicular-to-grain tensile design value.

## Inputs required for a final case

Supply current CAD hole coordinates relative to the member centerline, actual
member ends, actual leg mass and supported length, and individual forces on
that member. The rim receives the opposite bolt forces from the leg. Any nearby
LED passage or other opening intersecting a checked member section must be
included or separately shown outside the local load-transfer region. The module
does not infer whole-frame load sharing or silently qualify an unexamined rim
opening from a passing leg calculation.

Five focused tests cover simultaneous staggered holes, void union/centroid,
member sensitivity to joint moment, actual rows, force reversal and edge
containment. Numeric final-case evidence belongs to the source-bound assembly
assessment that calls this module.

## Current raw geometry extraction

The current `wider_leg_frame.py` places the group at +27 mm along the leg and
+4 mm along the rim from the former four-bolt center, with 66/84 mm pitches.
This differs from the preliminary feasibility pattern. The raw leg blank is
1863.960 mm long; its grain-station ends are −1663.960 and +200.000 mm relative
to the original leg datum. Its depth direction matches the normal used by the
wood-check functions. The supported column length must come from the foot and
actual joint location, not the full stock extension beyond the joint.

The raw rim has depth 184.15 mm with its panel-facing plane retained. Its
centerline datum is the model's `b.point(0,0,0) + b.normal()*92.075`, with grain
station bounds −157.190 to 2438.400 mm. The structural round-bore schedule has
no LED passage entry in either outer rim. Existing fastener openings still
require the final CAD clearance witnesses; absence of LED bores is not a claim
that the member contains only the six new bolt bores.
