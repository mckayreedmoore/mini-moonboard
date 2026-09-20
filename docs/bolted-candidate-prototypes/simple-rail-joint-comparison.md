# PB-01: first actual rail-joint comparison

Status: **in progress, no selected joint or drilling release.** This compares
two simple through-bolted concepts at the same physical kerf-right duty,
`clip_horizontal_lower_right_1`. It replaces neither the baseline nor
the other 23 old angle duties. The [companion geometric screen](simple_rail_joint_comparison.json)
tests nominal poses only; all dimensions below are model datums, not shop holes.

## Shared actual duty

The historical ML24Z with six structural SDS axes connects
`base_principal_center_right` to `base_rail_service_lower_right`.
The current two full-section 2×6 pieces meet at **X = 89.05 mm**:
the principal occupies X = 50.95–89.05 mm and the rail starts at X =
89.05 mm. Each has a nominal actual 38.1 × 139.7 mm section. The rail
grain runs along X; principal grain follows the panel slope, approximately
`(0, 0.643, 0.766)` in global X/Y/Z. The end is presently a butt contact,
not a direct through-bolted overlap.

The fixed `round_panel_lower_right_center_4` screw lies at X = 70 mm,
**19.05 mm inboard** of the butt plane; it must still enter a proven
principal/backer receiver. The two fixed service-rail panel screws lie at
X = 435.075 and 835.075 mm. All three start at Y/Z =
711.246/1145.683 mm and point in `(0, -0.766044, 0.642788)`; the purchased
Hillman screws are 63.5 mm long. The other 63 panel/kicker axes and all
panel outlines remain fixed. A surface or axis intersection alone is not
adequate screw embedment or edge support.

In local panel-tangent coordinate `T = (0, 0.642788, 0.766044)` and
panel-normal coordinate `N = (0, -0.766044, 0.642788)`, the lower service
rail spans T = 1315.774–1353.874 mm and the next upper service rail starts
at T = 1459.824 mm. Their nominal **105.95-mm tangent gap** leaves only
17.05 mm beyond an 88.9-mm cleat, too little for the tested nut-side tool.
This is not, by itself, a wood edge-distance or complete-joint verdict.

## Candidate A — full-section face overlap

The rail would extend across the X = 89.05 mm butt plane and one member
would move into a neighboring hidden plane, with broad full-section
faces touching. No member is half-lapped. The offset enters the bolt grip,
eccentric action and panel-receiver map. Moving the rail's full 139.7-mm
panel-normal depth away from its present panel-support plane leaves **zero
intersection** between that rail and both fixed service-rail screw axes in
the tested pose. The offset rail does not collide with adjacent timber or
panels, but its trial bolt-head washer and tool envelope hit the fixed
lower panel. This particular overlap pose is rejected. An added front receiver
would need its own positive structural attachment, cost and transport
operation. The overlap length, bolt count/centers, accessible washer/nut
faces, edge/end distances and load-to-grain angles remain unselected.

## Candidate B — rectangular solid-timber corner cleat

Keep the present butt arrangement and put one plain rectangular solid-wood
cleat against accessible rear/inside faces. Use separate through-bolt
groups for principal-to-cleat and rail-to-cleat; the groups transfer load
**in series**, and orthogonal bores must not intersect. Show both ends of
each bolt, washers, nuts, tool approach and assembly order. A cleat may
remain bolted to one principal transport member. Its stock species/grade,
grain, section, length and group positions are design variables. A nominal
2×2 is only a dimensional comparator; a larger plain 4×4-sized block is
not automatically sufficient. The first 88.9-mm tangent-side cleat pose
preserves all 66 screw axes and has complete, non-crossing trial bores,
but the rail-side nut's 40-mm straight-tool envelope intersects the upper
service rail. That 88.9-mm pose is rejected. Trimming the tangent-side
dimension to 57.15 mm leaves 48.8 mm to the upper rail and **6.3 mm
nominal clearance beyond the tested 40-mm straight-tool envelope**.
The 57.15-mm pose leaves all 66 fixed screw axes, both complete trial
bores, their washers and tools clear in this local solid-intersection
screen. This is a *geometry-only* finding: there is one trial bolt per
interface, no tolerance or actual socket specification, and the trial
upright bolt runs along the cleat grain. Its 28.575-mm tangent-side
center-to-edge distance is not an NDS qualification. The 2024 NDS has a
specific dowel-bearing provision for a bolt axis parallel to wood fibers;
its application here, group behavior and fabrication still need proof.
This pose is deprioritized in favor of the simpler transverse-axis screen,
not declared structurally impossible. Cleat shear, bending, splitting and both
interface deformations must be checked as one joint.

A second pose turns the cleat so its **200-mm length follows panel-normal
grain**. Its 88.9 × 57.15-mm cross-section can be cut from nominal 4×4
stock, subject to delivered dimensions and a short rip cut. Both separate
trial bolt axes are transverse to the cleat grain. The local solid screen
finds complete bores, face-seated diagnostic washers, positive contact
at both interfaces in a 0.1-mm solid-perturbation probe, clear 40-mm
straight clearance cylinders, no
intersections with other members, and no intersections with any of the 66
fixed screw axes. The rail-side tool still has 6.3 mm nominal tangent
clearance to the upper rail. This is a **diagnostic pose only**: the real
bolt head, nut, socket, washer specification and assembly sequence are
not modeled or verified. One bolt per
interface is not a reversible load path. The rail bolt lies just 44.45 mm
from its member end, 22.225 mm short of a nominal 7D full-value benchmark
for a 9.525-mm bolt *if the corresponding loading condition applies*.
The actual load direction, applicable 2024 NDS geometry factor, loaded
edge, group, cleat and member resistance all remain open. The old X-grain
pose remains in the JSON as an unselected diagnostic, not an accepted joint.

A third diagnostic pose uses the long face of ordinary nominal 4×6 along X,
keeping the cleat grain panel-normal and its tangent-side rip at 57.15 mm.
With a 139.7-mm X width, the trial rail bolt can move to 70 mm from its
grain-X end, leaving 69.7 mm to the cleat's opposite X edge. That is
3.325 mm beyond the *conditional* 7D benchmark. The modeled face contact,
trial bores, seated washers, clearance cylinders, other parts and all 66
fixed axes remain clear. This removes one specific 4×4 geometric shortfall;
it does **not** establish a full bolt group, 2024 NDS pass, installed
head/nut/socket access, stock cost, or a complete joint. The longer
principal-to-cleat wood grip is 177.8 mm before any washers or nut.

A four-bolt diagnostic layout then tries two ordinary through-bolts on
each serial interface. Extending the 4×6 cleat's grain-normal length to
300 mm with its front at N = 160 mm creates a real **143,332 mm³ clash**
with the fixed lower panel, so that pose is rejected. One adjustment
aligns the cleat front with the rail front at N = 209.841 mm. The adjusted
pose has positive CAD face contact, complete trial bores, face-seated
diagnostic washers, no modeled hardware-to-hardware or part collision,
and no collision with any of the 66 fixed panel/kicker axes. It is still
a diagnostic layout, not a rated four-bolt joint. The first upright bolt
is 55.159 mm from the cleat's grain-normal front. If a full-value 7D
front end, 4D rear loaded edge, and 4D row pitch all apply to its
38.1 × 139.7-mm host section, they leave only 34.925 mm for a 38.1-mm
pitch; that *conditional* combination cannot fit. Actual load directions,
reduced geometry factors, member stresses, group sharing, stiffness,
installed access and wood/bolt strength remain to be determined.

## Preliminary mechanics and cost boundary

For both concepts, derive simultaneous force and moment about one common
origin from the new topology, including the offset between member force
lines and contact that acts only in compression. The old ML24Z reactions
are provisional diagnostics, not current demands. The relevant 2024 NDS
two-member lateral-yield helpers can address a qualifying *individual*
bolt, but not axial separation, group/splitting, washer bearing, whole
cleat action, or frame stiffness by themselves. The existing wood–steel
wrappers are not direct wood–wood joint ratings. PB-04 must reconcile the
[March 2026 AWC 2024-NDS erratum](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)
before adopting connection-adjacent timber shear checks. The
[2024 NDS geometry basis](simple-rail-nds-geometry-basis.md) separates
applicable placement rules from conditional ratios. No bolt diameter
or count is selected by this record.
The [free-body action path](simple-rail-action-path.md) records the common
origin and new wrench/contact outputs required before any capacity comparison.

The [retail source inventory](simple-joint-retail-inputs.md) is preliminary.
Home Depot lists an
[Everbilt 3/8 × 4-in galvanized hex bolt](https://www.homedepot.com/p/204645570)
at $1.84 each; its [100-pack 3/8 nuts](https://www.homedepot.com/p/204274098)
and [100-pack flat washers](https://www.homedepot.com/p/204284545) list
$33.66 and $33.42 respectively. These are **not an adopted structural
bolt specification or a complete purchased stack**. In particular, a
4-in bolt cannot span either tested through-grip (100.25 or 243.1 mm)
with the required washers and nut. A listed
[Lowe's #2 & Better DF 4×4×8](https://www.lowes.com/pd/4-in-x-4-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-3-562-in-x-8-ft-Actual/1000028905)
is a possible graded cleat-stock lead, but its local price, stock,
delivered grade/dimensions and moisture remain unknown. Compare complete
packs, actual bolt lengths, nuts, appropriate bearing washers, timber
yield, shipping/tax, ordinary cuts, bore directions, and move operations
only after both joint layouts are dimensioned. Do not imply a cost winner
from the price of one shaft.

Next: develop full bolt groups in this same local duty, including a
sourceable wider cleat if needed for end/edge geometry, then calculate
applicable component checks and preliminary
same-case actions before choosing the simpler credible detail. A nominal
40-mm tool cylinder is not a guarantee that an actual socket/wrench works.
