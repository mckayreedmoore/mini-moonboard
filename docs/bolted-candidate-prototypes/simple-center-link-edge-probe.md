# PB-02 link-bolt X-edge reserve: solid ripped side cleat

Status: **positive nominal reversible 4D X-edge reserve in both cleats**;
geometry lead only, not stock-qualified fit. This follows the
[post/rear-cleat pose](simple-center-edge-reserve-probe.md). It does not
select bolts, classify NDS loading, establish strength, or release drilling.

## Exact nominal pose

The post, backer, both kicker outlines and inner edges, 66 fixed panel/kicker
screw axes, and post bolts remain as in the preceding pose. The post occupies
X=88.75…177.65, Y=−175.7…−86.8, Z=0…238.9 mm; post-bolt axes remain
X=140.00 at Z=110/190 mm. The rear cleat remains one uncut 2×4 section,
88.9 × 38.1 mm, at X=89.05…177.95, Y=−213.8…−175.7, Z=0…460 mm.

One geometric stock change makes the upright-side cleat a **single solid
nominal 4×4 blank ripped along its 183 mm length** to a finished
88.9 mm X width × 56.8 mm Y depth. Its modeled bounds are X=89.05…177.95,
Y=−175.7…−118.9, Z=277…460 mm. Its left X face still contacts the
inclined upright. The separate cleat-link axis moves to X=133.50,
Z=370 mm. Its nominal Y-axis bore crosses 38.1 mm of rear cleat plus
56.8 mm of side cleat. The upright X-axis through-bore at Y=−147.3,
Z=350 mm now spans X=50.95…177.95 mm, reaching the new exposed side-cleat
face. The old X=139.85 mm right bolt end would be buried by the wider cleat;
the illustrated 127 mm wood grip is **not** a selected purchased bolt length.
No pocket, half-lap, lamination, panel change, or custom steel is modeled.
The blank's nominal 88.9 mm Y dimension must lose 32.1 mm in total to reach
56.8 mm, **including saw kerf**. No blade kerf or offcut width is assumed;
for a measured kerf `k`, the nominal offcut would be `32.1−k` mm if the
delivered blank were exactly 88.9 mm. A full-length straight rip through
solid 4×4 stock must be feasible with available tooling and a safe workholding
plan. The cut face, squareness, straightness, actual delivered X/Y dimensions,
and final fit/contact would require measurement. This probe does not qualify
the blank, cutting process, or any delivered tolerance.

| Conditional centerline X-edge screen | Left/right distances, mm | Minimum beyond 4D=25.4 mm |
| --- | ---: | ---: |
| Post bolts in solid 4×4 post | 51.25 / 37.65 | **+12.25** |
| Post bolts in rear cleat | 50.95 / 37.95 | +12.55 |
| Separate link bolt in rear cleat | 44.45 / 44.45 | **+19.05** |
| Separate link bolt in side cleat | 44.45 / 44.45 | **+19.05** |

For the two nominal 88.9-mm cleat X sections, the common link-axis interval
that reaches 4D on both sides is X=114.45…152.55 mm. The centered X=133.50
axis has 19.05 mm nominal centerline reserve to either limit. This is a
useful design allowance for later tolerance allocation, **not a delivered
tolerance**: stock width and placement, drilling location, bore diameter,
joint movement, and installation error have not been measured or budgeted.
The post-bolt minimum remains +12.25 mm. All distances are from bore centers
to idealized rectangular edges, with the same illustrative 6.35-mm bolt
and conditional 4D screen as the predecessor.

## Geometry screen and limits

The CAD screen retained 48 panel plus 18 kicker screw axes, both inner
kicker-edge supports, full receiving portions of the four center kicker
screws, zero post/backer X gap, 9,102.09 mm² nominal post/backer X-face
contact, and positive post/rear-cleat face contact. It found no positive-volume
new-wood overlap, fixed-screw hit, unintended wood bore hit, or bore-pair
hit. All four illustrative bores were fully received by their intended wood
pairs. Eight 20-mm-diameter washer disks had full nominal bearing, and
20-mm-radius × 20-mm straight outward tool cylinders at all eight ends
cleared modeled wood when the upright right end was moved to X=177.95.
The post front still clears the installed kicker by 50.8 mm. These checks
use idealized cylinders; actual washers, heads, nuts, wrench travel,
bolt shank/thread distribution, installation order, and future access are
unverified. Face contact alone is not a fastened load path.

The reversible X-edge 4D marker has **not** been adopted as the applicable
NDS classification. Force direction and sign, member role, grain direction,
end and edge classification, upright oblique cut, spacing, group action,
splitting, net sections, and complete joint resistance remain open. Positive
nominal fit provides no strength or load rating. Delivered stock and
manufactured bolt dimensions require measurement and an explicit tolerance
budget before any drill coordinates can be set. Access with the ripped
cleat and the longer upright bolt remains a modeled straight-cylinder
clearance only; confirm real hardware, tools, and assembly sequence after
stock preparation.

The old `clip_split_base_center_right` and
`clip_split_header_center_right` stations and their screws still collide
with the proposed wood and are displaced. Their base, header, and upright
duties still need a complete replacement load path and verification.
The selected baseline and its evidence are unchanged. **No cutting or
drilling release follows from this probe.**

Reproduce with `.venv/bin/python scripts/simple_center_link_edge_probe.py`,
`.venv/bin/python -m pytest -q tests/test_simple_center_link_edge_probe.py`,
and `.venv/bin/ruff check scripts/simple_center_link_edge_probe.py
tests/test_simple_center_link_edge_probe.py`.
