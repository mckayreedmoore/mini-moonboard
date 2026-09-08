# Threaded inserts and repeated disassembly

Research checked 2026-09-08. This is an options review, not a hardware substitution
or structural approval. No CAD, drilling schedule or purchased hardware changes
are implied.

## Recommendation

Keep the current through-bolts for removable legs and base gussets. They already
provide reusable metal threads without repeatedly driving screws into wood.
If holding the rear nut is inconvenient, investigate a **retained conventional
nut and washer** before changing the structural connection to a screw-in insert.
Retention should prevent loss/rotation; it must not replace the washer's bearing
on sound wood or obstruct inspection and replacement.

Screw-in inserts are most attractive for lightweight removable wiring covers or
other nonstructural accessories. Using them for structural panel removal could
be worthwhile if frequent removal is genuinely needed, but it is a new joint
design, not a drop-in durability upgrade.

## Concrete manufacturer examples

| Product | Published dimensional example | Relevance and limit |
| --- | --- | --- |
| E-Z LOK E-Z Hex 903816-13 | 3/8-16 internal thread; 13 mm (0.51 in) length; 15/32 in (11.906 mm) pilot; 10 mm hex drive | Zinc, flanged, intended for softwood and wood-based materials. The same catalog lists 20 and 25 mm lengths. Material compatibility does not establish structural resistance. |
| E-Z LOK E-Z Knife 400-6 | 3/8-16; 5/8 in (15.875 mm) length; 33/64 in (13.097 mm) pilot; DT-6 driver | Brass knife-thread family marketed for hardwood. Not the default choice for the purchased Douglas-fir framing/plywood. |
| RAMPA SKD330 M10 family | Manufacturer handling sheet lists 18.5 mm (0.728 in) outside diameter and 10 mm hex drive | Steel, zinc-plated option with guided entry. Select a specific length/article and its matching drilling sheet before modeling; the storefront selector alone is not a complete SKU drawing. |

Sources: [E-Z Hex product](https://www.ezlok.com/ezhex-insert-903816-13),
[E-Z LOK dimensional catalog](https://www.ezlok.com/assets/documents/literature/EZ-LOK%20Brochure%202026.pdf),
[E-Z Knife product](https://www.ezlok.com/ezknife-insert-400-6),
[RAMPA product family](https://www.rampa.com/eu/en/rampa-inserts-type-skd330/420823001010)
and [RAMPA handling instructions](https://www.rampa.com/na/en/rampadownloads/31ecb8775d91433bbf93ef6ea981de93).

These relatively large bores matter on a 38.1 mm-wide framing face, such as
the backing connection into a principal, not the leg bolt axis described below. A centered
18.5 mm insert leaves only 9.8 mm of wood on either side, geometrically; that
is **not** an acceptable-edge-distance finding. A 20 mm-long insert also cannot
be hidden through the thickness of the nominal 18.256 mm face plywood. A shorter
insert fitting within the thickness does not establish adequate pullout capacity.

## Specific removable-leg option

The current leg bolts run across the rim thickness, along X. The rim provides
38.1 mm (1.5 in) of **insertion depth**, not a 38.1 mm-wide radial bearing face.
The four positions on each side are S=1540, 1620, 1740 and 1820 mm, at N=74.075 mm
within the 184.15 mm-deep rim. Thus the nominal axis-to-edge distances in the
rim's depth direction are 74.075 and 110.075 mm. These dimensions describe the
current geometry; they are not an insert spacing or structural-capacity approval.

An insert alternative would reverse the assembly direction: the bolt enters
from outside, passes through the two leg plies totaling 38.1 mm, and engages an
insert installed in the rim's outside face. For example, a 20 or 25 mm E-Z Hex
3/8-16 insert is shorter than the nominal rim thickness. That alone does not
establish that its required pilot depth, usable internal thread and bolt tip
clearance fit. Bolt length must cover the leg thickness, selected washer and
required thread engagement without bottoming; no bolt length or engagement
requirement is selected for this unqualified concept. Pilot diameter/depth,
installation torque, remaining back thickness and actual product tolerances
must be resolved before cutting.

This is geometrically more plausible than inserting into the narrow principal
face, but it changes the leg joint from a through-bolt/washer connection to one
dependent on insert retention in Douglas-fir. Combined lateral/axial loading,
wood bearing and splitting, insert pullout, and repeat-disassembly behavior need
application-specific qualification. The preferred access improvement remains a
conventional nut retained on the **inside face of the rim**, preserving the
through-bolt and washer bearing arrangement rather than introducing a new
wood-thread anchorage. No leg CAD or hardware schedule is changed here.

## What the load evidence actually says

E-Z LOK explicitly does not provide Hex Drive testing results because installation
variables affect performance. Its separate Knife table lists typical 400-6
pullout forces of 870 lbf in spruce and 1,895 lbf in white oak. Those are not
allowable working loads, contain no Douglas-fir or plywood entry, and do not
establish cyclic, combined shear/tension or close-edge performance here.
[Testing policy](https://www.ezlok.com/testing),
[Knife pullout table](https://www.ezlok.com/assets/documents/testing/KnifeThreadPullOutSpecs.pdf).

RAMPA's published SKL330 load table references ETA 12/0481, but concerns specified
glulam/CLT lifting applications, installation direction, distances and vibration
conditions. It is not a rating for a different SKD330 furniture insert, a narrow
solid-lumber member or AC plywood. The existence of rated insert applications
therefore does not qualify this frame. Request the exact applicable assessment
and material/joint conditions before assigning any resistance.
[RAMPA SKL330 load table](https://www.rampa.com/media/80/56/6e/1671462070/RAMPA_Lasttabelle_SKL330_EN.pdf).

## Installation and assembly effort

For E-Z Hex, use the selected product's pilot and hex/installation tool, not the
bolt's clearance drill. The manufacturer describes installation with a drive
tool or bolt and jam nut. [E-Z Hex data sheet](https://www.ezlok.com/assets/documents/data_sheets/Data%20Sheet_Wood_Hex_D.S.130.pdf).

RAMPA calls for clean holes, pilot depth at least insert length plus 2 mm,
controlled alignment and a maximum 175 rpm for SKD330. Pilot diameter and torque
must come from the selected size/material instructions; do not extrapolate the
sheet's M6 example to M10. Excess torque can damage the substrate.
[RAMPA handling instructions](https://www.rampa.com/na/en/rampadownloads/31ecb8775d91433bbf93ef6ea981de93).

Our integration would additionally need bolt engagement without bottoming,
accessible installation, clearance from hold/LED reservations, and checks for
splitting, pullout, shear and loosening after repeated cycles. These are reasons
not to blanket-convert the frame while structural joints remain unqualified.

| Approach | Cutting/assembly effort | Appropriate next use |
| --- | --- | --- |
| Existing through-bolt, nut and washers | Straight drilling; two-sided wrench access; inspectable and replaceable | Preferred removable leg/base connection concept, subject to existing capacity checks |
| Conventional nut retained against rotation/loss | Adds a retainer or pocket; preserve bearing area and replacement access | Access improvement where a rear nut is inconvenient; retention detail still needs design |
| Cross dowel / barrel nut | Intersecting bores require accurate position and alignment; reduces net wood section | Possible purpose-designed corner/end joint, not an automatic stronger replacement |
| Screw-in wood insert | Larger controlled pilot, careful installation and new resistance qualification | Nonstructural covers first; structural use only after application-specific evidence |

RAMPA's [Type Q cross-dowel family](https://www.rampa.com/eu/en/rampa-cross-dowels-type-q/0201070010100)
includes M10 options and describes frame/corner use. Its barrel bears within
the wood instead of relying on an insert's external screw thread; this changes
the failure mechanism, not the obligation to check bearing, splitting and net
section. No Type Q size or capacity is selected here.

Do not substitute inserts/machine screws into the ML24Z angles while retaining
their published SDS25112 capacity claims. Do not replace climbing-hold T-nuts,
or assume inserts solve the backing bolts' existing 2D edge-distance concern.
For this board, convenient repeatable disassembly is best pursued at the already
bolted transport joints before making every panel or brace removable.
