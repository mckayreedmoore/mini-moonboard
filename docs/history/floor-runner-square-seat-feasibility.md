# Square rim end and fitted timber seat: feasibility

## Disposition

A grain-normal square end removes the rim's notch/taper-method ambiguity.
It does not, by itself, produce a qualified joint: its inclined bearing face
requires a positively restrained timber seat, and uplift must bypass that
compression-only interface. A loose triangular wedge is not a completed remedy.

Retain the flat nominal 2×6 header, Z277 main-face datum and solid 4×6 rims.
No custom steel is proposed. This note defines a separate feasibility option;
no selection, model, drilling, source implementation or solve changes occur.

## Exact rim and seat geometry

The lower rim end is one plane normal to its YZ grain vector
`u=(sin40°,cos40°)`. Its side-profile endpoints are:

- Rear/high: `(Y,Z)=(-148.513740,366.797429)` mm.
- Front/low: `(-41.497331,277)` mm.

The rim remains a full 88.9 × 139.7 mm prism up to that plane; there is no
interior shoulder or taper of its longitudinal faces. Existing upper geometry
is unchanged. The end-bearing plane slopes 40 degrees to horizontal.

A minimal triangular seat has those two points and
`(-148.513740,277)` as its side-profile vertices, with the rim's X width.
Its base length is 107.016409 mm and height 89.797429 mm. This fits the
139.7 mm header width Y[−175.7,−36], with rear/front margins of
27.186260/5.497331 mm. A nominal 6×6 blank can contain the profile; a
4×6 blank cannot provide its 89.797429 mm vertical height when its 88.9 mm
dimension is oriented vertically.

Specify seat grain along **Y**, not along the sloping top or assumed parallel
to the rim. Select identified, graded solid stock and its actual moisture,
species and grade properties. A leftover block of unknown grain/grade is not
an equivalent material specification.

### Better fabrication envelope for investigation

Use the header's spare rear footprint for a rectangular seat heel:
Y[−175.7,−148.513740], Z[277,366.797429], followed by the inclined face
already defined. The extra heel has no inclined rim above it and receives no
invented contact pressure. It supplies room for restraint hardware.

Consider physically blunting the thin forward toe, for example at 20 mm
behind the low rim endpoint. That leaves about 16.782 mm minimum seat height
and removes about 26.108 mm of the rim's end-bearing face. This example is
an unselected sizing variable, not released geometry. The rim stays square
ended; its reduced, eccentric contact area must be used. Do not retain the
removed tip as an effective bearing or screw receiver in calculations.

## Load path and checks

For a frictionless rim/seat contact normal resultant `N`, the force on the
seat is `(-N sin40°, -N cos40°)` in YZ. Its horizontal thrust is therefore
`H=0.83910 V`, before other forces or couples. The seat/header contact
supplies compression in Z; a separate connection must supply H. Floor no-slip
assumptions do not create friction between these timber interfaces.

The required local calculation is finite:

1. **Rim end bearing:** pressure acts parallel to rim grain. Check the actual
   compression footprint and eccentricity, splitting/load introduction, and
   adjacent full-section combined forces. A square end removes the taper
   classification, not the need to recover connection-induced local shear.
2. **Seat top bearing:** its normal is 50 degrees to the specified Y grain.
   Use the applicable angle-to-grain bearing resistance and actual contact
   pressure; do not assign the rim's parallel-grain resistance to the seat.
3. **Seat base/header bearing:** Z load is perpendicular to both the seat's
   Y grain and the header's X grain. Check each material and actual compressed
   area separately. An eccentric resultant can leave part of the base open.
4. **Seat shear and splitting:** resolve H into the real restraint fasteners
   and every intervening wood section. Check grain-parallel shear, tension
   perpendicular to grain, net sections, and local fastener splitting.
   The triangular seat is a short loaded block, not automatically a beam
   qualified by the rim's former taper formula.
5. **Sliding, uplift and rocking:** positive fasteners must resist horizontal
   translation and lift of both rim and seat. Include the complete force and
   moment equilibrium, contact opening, restraint eccentricity and withdrawal.
   A compression-only wedge cannot tie an unloaded or uplifting rim down.

[NDS 2024 Chapter 3, §3.10 and Figure 3I](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
provides the distinct grain-direction bearing routes. It does not supply a
universal connection or triangular-block capacity. The
[USDA Wood Handbook, Chapter 9, stress-equation introduction](https://research.fs.usda.gov/download/treesearch/37423.pdf)
explains why ordinary member-resultant stress equations alone do not resolve
local support stress concentrations.

## Commercial attachment options

### Catalog fasteners with a timber/plywood restraint

The strongest next investigation is a structural plywood side cheek connecting
the rim, seat and outer post with individually specified commercial screws or
lags. Their X-directed axes enter side grain in these three members. Bypass
the header end for withdrawal: its grain runs X. Existing commercial angles
may remain only with their own recovered, supported loads.

This is a calculable fastener-group route, not an off-the-shelf rated assembly.
It needs actual diameters, shank/thread lengths, fastener layout, eccentric
group demands, plate bending, plywood tear-out and head bearing, wood edge/end
distances and installation access. One-sided cheeks carry eccentric moments;
two cheeks may reduce eccentricity but need real clearance and cannot assume
equal sharing. The rear rectangular seat heel improves receiver space; the
sloping thin toe is unsuitable for an assumed uniform screw grid.

[AWC TR12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf)
provides a mechanics route for dowel/lag yield with actual geometry; it does
not remove placement, wood splitting or plywood checks. This option avoids
inventing the unlisted combined resistance of an ML24Z/SDS group, while
introducing a new custom **wood** connection requiring its own calculation.

### Direct screws through the seat

A screw normal to the sloping face can be installed before the rim, but its
head must not spoil the fitted bearing face. Recesses alter seat geometry.
The header's 38.1 mm thickness gives only about 49.74 mm gross path along
that axis; actual effective penetration is shorter after tip and clearance
allowances. This is close to the 45 mm minimum associated with the generic
NDS steel-to-wood route in [ESR-2236 §4.1.5](https://cdn-v2.icc-es.org/wp-content/uploads/report-directory/ESR-2236.pdf).
That particular route does not automatically qualify a wood-to-wood seat
joint. Use the exact applicable product provision, not a length-only check.
Seat-to-header screws alone also leave rim uplift unresolved.

### Hurricane ties or existing angles

H3 is not established for this elevated inclined bearing block. Its rafter/
plate relationship, plate fastener positions and exterior-overhang assumption
must match the manufacturer's detail; a wedge cannot be substituted silently
for the specified plate. See [the catalog audit](floor-runner-angle-resolution.md).
Reusing an ML24Z on this altered seat also does not resolve its previously
unlisted separation and complete-wrench actions.

## Buildability and next decision

Make the rim square cut first and template the actual face. Fit the seat with
continuous intended bearing, identified toe relief and no loose stacked shims.
Plan restraint installation before the rim obscures screw heads. Preserve
access to runner bolts, kicker attachments and the header/post interface.

Proceed to CAD only after a local cheek/fastener layout can meet simultaneous
placement and resistance requirements. If no such layout fits, the wedge is
not a supported shortcut. The source ambiguity has been removed from the rim
but replaced by explicitly identified seat and restraint work; six global
solves cannot substitute for that local result.
