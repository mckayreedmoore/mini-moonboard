# PB-01: first actual rail-joint comparison

Status: **in progress, no selected joint or drilling release.** This compares
two simple through-bolted concepts at the same physical kerf-right duty,
`clip_horizontal_lower_right_1`. It replaces neither the baseline nor
the other 23 old angle duties. The companion geometric screen is under
development; all dimensions below are model datums, not shop holes.

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

## Candidate A — full-section face overlap

The rail would extend across the X = 89.05 mm butt plane and one member
would move into a neighboring hidden plane, with broad full-section
faces touching. No member is half-lapped. The offset enters the bolt grip,
eccentric action and panel-receiver map. Moving a 38.1-mm-thick rail away
from its present panel-support plane may leave too little of the 63.5-mm
panel-screw length in the rail; this is a **question to calculate**, not
permission to lengthen or move the 66 screws. An added front receiver
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
not automatically sufficient. Cleat shear, bending, splitting and both
interface deformations must be checked as one joint.

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
before adopting connection-adjacent timber shear checks. No bolt diameter
or count is selected by this record.

Retail comparison as of 2026-09-20 is preliminary: Home Depot lists an
[Everbilt 3/8 × 4-in galvanized hex bolt](https://www.homedepot.com/p/204645570)
at $1.84 each; its [100-pack 3/8 nuts](https://www.homedepot.com/p/204274098)
and [100-pack flat washers](https://www.homedepot.com/p/204284545) list
$33.66 and $33.42 respectively. These are **not an adopted structural
bolt specification or a complete purchased stack**. A listed
[Lowe's #2 & Better DF 4×4×8](https://www.lowes.com/pd/4-in-x-4-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-3-562-in-x-8-ft-Actual/1000028905)
is a possible graded cleat-stock lead, but its local price, stock,
delivered grade/dimensions and moisture remain unknown. Compare complete
packs, actual bolt lengths, nuts, appropriate bearing washers, timber
yield, shipping/tax, ordinary cuts, bore directions, and move operations
only after both joint layouts are dimensioned. Do not imply a cost winner
from the price of one shaft.

Next: run one maintained parameterized local fit screen for both concepts,
then calculate applicable component checks and preliminary same-case
actions before choosing the simpler credible detail.
