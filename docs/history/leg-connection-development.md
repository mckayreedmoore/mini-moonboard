# Two-sheet leg: explicit connection development candidates

Research and geometry checked 2026-09-06. Retain the original `2x8-foot100`
CAD and its bonded results. Prefer a documented qualified lamination of the
two requested 19.05 mm sheets if an appropriate fabricator can supply it.
The separate **`foot100-independent-bolts-3station`** concept below is a
geometrically feasible, no-adhesive-credit candidate to analyze if that process
is impractical. Its three new bolts per leg are **an experiment layout, not a
verified fastener schedule or instructions to drill the existing legs**.

Neither route currently has verified member/connection resistance or a climber
rating. This note makes the next comparison concrete; it does not select a
construction-ready assembly. The [material recommendation](material-selection-recommendation.md)
and [load basis](load-contact-basis.md) still apply.

## What the existing experiment resolves

The [current drilled-leg experiment](../fea/results/independent_leg_response/README.md)
found 3.9223 times the bonded reference's out-of-plane compliance for evenly
loaded independent plies, with less than 0.04% in-plane change. Loading only
one ply approximately doubles the independent compliance. These results
justify resolving actual sharing and lateral response. They do not show that
three stitches restore composite action or establish a buckling capacity.

Both sheets of the real right leg occupy X=1257.30–1295.40 mm, split at
1276.35 mm; the left leg is mirrored. The rim touches only the inner sheet.
Consequently the four rim bolts join **three timber layers**: a 38.1 mm rim,
an inner 19.05 mm ply and an outer 19.05 mm ply. This is not the symmetric
double-shear arrangement of a main member between two matching side plates.
Existing 10 mm bores and nominal 9.525 mm bolts leave 0.475 mm diametral
clearance. Actual bearing engagement and the bolt's deformation determine
sharing, rather than an imposed 50/50 split.
[Current geometry preflight](independent-leg-test-plan.md).

The upper bore stations are board-local S=1540/1620/1740/1820 mm, giving
80/120/80 mm spacings along the upper centreline. The upper profile runs from
S=1480 at the knee to S=1880 at its end. Its outermost hole is therefore
60 mm from that end along the centreline; this is a geometry measurement,
not an adopted loaded-end allowance for an unidentified plywood layup.

## Mechanical candidate specification

Use two continuous, matching cut profiles per leg with no scarf or butt joint
at the knee. Retain the 180 mm profile width, rounded knee, four upper holes
and level floor cut of `footprint_frame.parts(100, drilled=True)`. Both sheets
are separately load-carrying structural plywood. Request actual 19.05 mm
thickness and directional product data; an offered nominal 3/4-inch category
is not a guarantee of that dimension. Any actual thickness change requires a
separately updated geometry, floor inventory and bolt grip check.

For the first material-aware comparison, align both sheets' documented panel
strength axes with the straight lower-member centreline. This is a project
orientation candidate, not an assertion that it is optimal. A single cut
sheet's axes do not turn through the knee: the upper segment must be checked
at its actual 60.891228-degree angle to those axes. Retain a 90-degree panel-orientation
sensitivity if product data make that choice consequential. Do not assign
Metsä properties to the unidentified Swaner C-3 stock.

| Interface | Explicit candidate | Credit and outstanding constraint |
| --- | --- | --- |
| Rim to leg | Preserve all four existing X-axis bolt stations; select actual bolt/nut/washer products against the 76.2 mm timber grip | Model bearing in the rim and each ply separately, plus bolt bending and clearance. Existing 95.25 mm overall envelopes do not specify thread extent or prove adequate nut engagement. |
| Ply to ply, lower member | Three additional X-axis 9.525 mm through-bolts per leg, at the centreline stations below; nominal 10 mm analysis bores | Transfer through mechanical bearing and bolt action only. Three stations are a bounded first comparison, not a spacing rule or sufficient connection count. |
| Bolt heads and nuts | Flat bearing washers on both exposed faces; no countersinking or embedded heads in the initial candidate | A 30 mm diameter face envelope is screened below; washer thickness, grade, hole, local bending and panel pull-through remain product/design inputs. No washer capacity is assumed. |
| Between the two sheets | Separate contacting faces with no adhesive or interface-friction credit | Allow tangential slip and opening, prevent penetration with compression-only contact. Head/nut restraint requires its own bearing model. |
| At the floor | Each ply retains its own floor-bearing face | No common rigid shoe, pad support, or forced equal floor reaction. Seating error, opening and local floor friction remain separate inputs. |

There is a concrete bolt procurement lead: Grattan's March 2025 catalog lists
**001063 / BBI 494053, A307 zinc 3/8-16 × 2-1/2-inch hex bolt**. Its 63.5 mm
nominal length is a candidate for the new 38.1 mm ply-only grip, not a
replacement for the longer upper bolts. Obtain the actual grade, dimensional
drawing, thread runout, nut and washer specifications and suitable finish;
the catalog entry does not establish the required assembly resistance.
[Supplier catalog, printed page a.2](https://www.grattanfasteners.com/PDF/Grattan_Product%20Catalog/GRATTAN_HEX%20BOLTS_032025.pdf).

Check the installed stack explicitly: bolt length must accommodate both
washers, both sheets, complete nut engagement and required projection, while
the nut must not bottom on the unthreaded shank. Locate the thread transition
relative to the ply interface and every bearing zone. Portland Bolt publishes
the usual short hex-bolt thread-length relation `2d + 1/4 inch`, but that is
not a drawing or tolerance certificate for the Grattan item; do not infer its
actual grip from the formula alone. No tightening-friction contribution or
high steel-to-steel installation torque is specified here.
[Bolt manufacturer dimensional guidance](https://www.portlandbolt.com/products/bolts/hex/).

The 2-1/2-inch lead is **not selected for CAD**: with the current generic
2 mm washers and 9 mm nut, its nominal projection would be 12.4 mm, exceeding
the existing 3–7 mm projection screen. A 2-1/4-inch (57.15 mm) envelope would
give 6.05 mm under those assumptions, but this catalog's 3/8-inch A307 list
does not show that length. Find a documented compatible shorter product/stack
or redesign the detail; do not silently add loose washers, trim bolts, or
ignore the user's requirement to avoid excessive projections.

A subsequent supplier check found the shorter nominal size: Kimball Midwest
lists [350618, zinc-plated Grade 5 3/8-16 × 2-1/4-inch hex cap screw](https://www.kimballmidwest.com/350618).
Thus 57.15 mm is a catalogued procurement lead, not merely an invented length.
This does not select that product or establish its head profile, thread runout,
tolerances, washer compatibility or resistance in the plywood assembly.
For comparison, [McMaster 95462A031](https://www.mcmaster.com/95462A031/)
is a Grade 5 3/8-16 UNC nut with nominal 9/16-inch width and 21/64-inch
height (14.2875 / 8.334375 mm), not the model's generic 9 mm nut height.
Any product substitution still requires the complete actual stack and
projection check; these catalog leads do not change the published CAD.

## Actual CAD location and fit screen

Define `B = box_frame.point(0, 1480, hybrid.leg_normal('2x8'))` and
`F = footprint_frame.foot_center(100)`. The stations are
`P = B + q(F-B)`, with `q = 0.2, 0.5, 0.8`, on each leg's mid-thickness X.
Thus `B=(0,862.792120,1417.930445)` mm and
`F=(0,1403.998388,0)` mm; the centreline length is 1517.705825 mm.

| Station q | World Y, mm | World Z, mm | Centreline distance from B, mm |
| --- | ---: | ---: | ---: |
| 0.2 | 971.033374 | 1134.344356 | 303.541165 |
| 0.5 | 1133.395254 | 708.965222 | 758.852912 |
| 0.8 | 1295.757134 | 283.586089 | 1214.164660 |

The 455.311747 mm station spacing keeps this first trial small and the new
holes away from the knee and floor ends. It is **not an effective buckling
length or code-approved stitch spacing**. The straight profile's centreline
is 90 mm from either long edge; that geometry alone does not establish
applicable loaded/unloaded edge distances for every force direction.

Read-only CadQuery intersections on the current drilled assembly checked all
six locations. Each full-thickness 10 mm cylinder removes
2992.367003 mm³ of wood, matching `pi*5²*38.1`; a 30 mm diameter surrounding
cylinder also lies fully inside the leg. A 36 mm diameter, 80 mm long X-axis
clearance envelope starting 20 mm before the leg's minimum X was screened
against the other current parts and existing connection hardware envelopes.
No positive-volume intersections were found.
These cylinders are nominal shaft/washer/access envelopes, not actual
hex-head tooling, an assembly sequence or a manufacturer's installation jig.
They do not change the baseline solids or exported drilling schedule.

The following read-only command reproduces the timber checks and also screens
the existing hardware envelopes. It does not create a candidate CAD export:

```sh
uv run python - <<'PY'
import math
import cadquery as cq
from mini_moonboard import box_frame as b, footprint_frame as f, hybrid
parts = f.parts(100, drilled=True)
B = b.point(0, 1480, hybrid.leg_normal('2x8'))
F = f.foot_center(100)
for side in ('left', 'right'):
    leg = next(p.shape for p in parts if p.name == 'leg_' + side)
    x = leg.BoundingBox().xmin
    for q in (.2, .5, .8):
        P = B + (F - B) * q
        for r in (5, 15):
            body = cq.Solid.makeCylinder(r, 38.1, cq.Vector(x, P.y, P.z), cq.Vector(1, 0, 0))
            assert abs(body.intersect(leg).Volume() - math.pi*r*r*38.1) < .01
        clear = cq.Solid.makeCylinder(18, 80, cq.Vector(x-20, P.y, P.z), cq.Vector(1, 0, 0))
        assert all(clear.intersect(p.shape).Volume() < .01 for p in parts if p.name != 'leg_' + side)
        assert all(clear.intersect(s).Volume() < .01 for c in f.connections() for s in c.components())
        print(side, q, P.y, P.z, 'geometry only: pass')
PY
```

## What published fastening guidance does and does not support

Simpson's SDW page describes multi-ply trusses and 45 mm engineered timber;
its shortest listed screw is 66 mm. That is longer than the entire 38.1 mm
stack in a face-normal installation. Its published product description is
not a tested two-19.05-mm-plywood schedule. The separate SDS multi-ply guide
uses LVL/PSL/LSL assemblies and explicitly requires consideration of unequal
side loading and lateral bracing. Those warnings are relevant mechanics;
the beam tables do not certify this bent plywood leg.
[SDW manufacturer dimensions](https://www.strongtie.co.uk/en-UK/products/structural-wood-screw-sdw),
[SDS manufacturer's multi-ply guidance](https://www.strongtie.com/products/fastening-systems/technical-notes/joining-composite-lumber-with-sds-wood-screws).

APA's authored *Fastener Loads for Plywood – Bolts*, E825E, November 1997,
contains actual plywood-to-plywood single-shear tests. It is available here
as a third-party-hosted copy of the primary APA report. Table 4 tested
19/32-inch and 1-1/8-inch panels with specified configurations; it is not a
3/4-inch profiled-leg schedule. Its estimated design loads used 1991 NDS
assumptions, and its bolt grade was unknown. Use it to establish that this
mechanical joint type has test precedent, not to interpolate a capacity or
adopt its historical allowances. Current panel-specific bearing, spacing,
group and service provisions still have to be established.
[APA report, pp. 3–4](https://www.bayarearetrofit.com/PDFs/APA%20Bolts%20in%20Plywood.pdf).

Stitches between two flexible sheets are **internal restraints**. They do
not anchor either sheet laterally to an independent stable structure, and a
single centreline row does not establish torsional restraint. Analyze the
assembly's global sway/twist and each sheet's lateral stability without
replacing stitch locations by fixed supports. The existing independent-ply
linear test has neither geometric imperfections nor a buckling calculation.

## Qualified lamination alternative

Keep the same two continuous profiles and axes, but procure an auditable
face-to-face structural bonding process for the actual panel faces. AkzoNobel's
Grip family includes industrial structural MF/MUF systems and multilayer-board
applications; it supplies a concrete manufacturer to approach through a
fabricator. The public family description does not approve any particular
adhesive/hardener pair for these sheets or provide a workshop recipe.
[Manufacturer application scope](https://woodadhesives.akzonobel.com/en/products-lines/grip-line).

The requested deliverable from that route is a written panel/adhesive match,
service conditions, permitted face preparation, moisture limits, mix/spread,
open/closed assembly times, pressure distribution over the full profile,
temperature/cure, bondline limits and inspection/test acceptance. Decide
whether the fabricator bonds blanks before profiling/drilling or bonds cut
profiles, and qualify the chosen sequence. The finished 38.1 mm target must
account for actual panels and bondline thickness. Panel factory certification
does not certify this new joint. None of these parameters is selected from a
generic glue marketing page, and no temporary clamp/screw pattern substitutes
for the documented pressing process.

## Finite next test and selection gates

1. Obtain the offered panel identity, actual thickness/axes and compatible
   material data, plus one of the two procurement/process packets above.
   This needs supplier/fabricator information; it cannot be recovered from CAD.
2. Model one complete rim-to-two-ply leg interface with four actual bolt
   locations, individual wood bearing/contact, measured clearance and explicit
   bolt/washer behavior. Include reversed in-plane and out-of-plane demands.
   Do not fix both bore surfaces or prescribe equal sharing. Publish per-ply
   and per-bolt resultants with equilibrium checks before using them as demand.
3. Compare the three-station leg against the retained independent and bonded
   controls using identical **external** resultants and fixtures appropriate
   to the question. Report sharing, inter-ply slip/opening, bolt shear/bending/
   axial forces and washer reactions. Vary justified connector-slip bounds;
   a rigid stitch is only an explicitly labeled limiting case. Force-dependent
   sharing can change around the knee and with which floor ply seats first.
4. Check stability and member/connection resistance using actual panel axes,
   net sections, bearing, tear-out/group action, rolling shear and head/nut
   pull-through. Use the complete frame's lateral restraints and seating
   conditions for its global stability conclusion. A successful local
   connection model cannot supply that conclusion by itself.

Select the mechanical route only if its required transfer and stability work
without adhesive, interface friction or unsupported restraint assumptions.
If the three-station candidate fails locally, revise station count/placement
only from the identified demand and spacing constraints. If global lateral
response governs, adding stitches alone is not an established remedy: compare
qualified lamination or an explicitly designed external restraint/leg redesign.
If the bonding process is unavailable, retain mechanical development rather
than crediting an undocumented shop glue joint. If neither route has feasible
products and load paths, switch to a separately designed engineered leg with
permitted cuts/holes. None of these triggers calls for deeper rims unless a
separate rim demand/resistance or agreed serviceability check governs.

Missing human/product inputs are therefore finite: actual panel marks and
dimensions; intended environment and acceptable deflection/use boundaries;
supplier/fabricator bonding capability; bolt/nut/washer drawings and product
properties; actual hole tolerances, seating and floor interface; and the
reviewer's applicable load, connection and stability acceptance basis. No
contact with suppliers, purchase, baseline CAD change or construction approval
is implied by this development note.
