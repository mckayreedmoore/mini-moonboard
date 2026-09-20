# MiTek B88 / Home Depot UB88 drawing follow-up

Checked 2026-09-20. This is a factory-hardware research note for the separate
bolted candidate, not a connector selection, joint rating, shopping order, or
drilling release. No manufacturer was contacted and no item was purchased.

## Product identity and public sources

- [MiTek's Home Depot conversion chart](https://images.thdstatic.com/catalog/pdfImages/2f/2f1009db-047c-4da8-a283-bcda2c494ebe.pdf)
  maps Home Depot store SKU `1005468437`, retail part `UB88`, to MiTek part
  `B88` (`A88` is the comparison/reference number). This is the direct
  manufacturer/retailer model cross-reference, not a substitution based only
  on a similar product photo. The chart warns that comparison references are
  not automatic substitutes.
- [Home Depot's exact UB88 page](https://www.homedepot.com/p/313507573)
  was live and listed internet item `313507573`, model `UB88`, store SKU
  `1005468437`, G90 finish, and 12-gauge steel. The page required a store
  selection; it did **not** verify a local quantity, pickup date, or delivery.
  Targeted searches found no exact B88/UB88 Lowe's product page. That is not
  evidence that Lowe's never stocks it.
- [MiTek's B-series product page](https://www.mitek-us.com/products/angles-straps/framing-angles-and-plates/b/)
  offers the B88 [DXF](https://www.mitek-us.com/wp-content/uploads/files/Drawing%20Library/B88_3view.dxf),
  [DWG](https://www.mitek-us.com/wp-content/uploads/files/Drawing%20Library/B88_3view.dwg),
  and [PDF](https://www.mitek-us.com/wp-content/uploads/files/Drawing%20Library/B88_3view.pdf)
  as public factory three-view drawings. The PDF depicts three holes per leg
  but has no printed hole-center dimensions. The DXF has millimeter model
  units (`$INSUNITS = 4`) and six circle entities, so its native geometry can
  be measured; it is not a tolerance-controlled fabrication drawing.

## Hole layout: published dimensions versus CAD extraction

[MiTek's B/BL load table](https://www.mitek-us.com/wp-content/uploads/2020/12/B_-BL.pdf)
specifies the B88 as a nominal 2-in-wide × 8-in-long brace with six 3/8-in
bolts. It does **not** print hole-center offsets. The following are measured
from the manufacturer's DXF circle entities in model space, not dimension
callouts or measurements of delivered UB88 pieces. Each leg's three circles
are on its width centerline. Offsets run along the leg from its *free end*
toward the bend, using the free-end outline in that same view as the datum.

| Leg/view | Hole centers from free end, mm | Across-width center, mm | Adjacent pitch, mm |
| --- | --- | --- | --- |
| Horizontal leg / top view | 28.6, 92.2, 155.8 | 25.4 | 63.6 |
| Vertical leg / side view | 29.0, 92.6, 156.2 | 25.4 | 63.6 |

The two view-derived offset sets differ by about 0.4 mm. The DXF's modeled
width is about 50.9 mm, close to catalog 2 in (50.8 mm); its length from
bend center to free end is about 203.4 mm, close to catalog 8 in (203.2 mm). Those
checks support use of the DXF as a **nominal CAD fit input**, not treatment
of the decimal coordinates as factory tolerances. The modeled circle diameter
is about 10.3 mm; it is not a wood-drill-bit instruction. No source inspected
states the manufacturing hole-position tolerance, bend-radius tolerance,
delivered-part variation, or required wood-hole diameter for this assembly.

## Current listed application and load conditions

[MiTek's B/BL table](https://www.mitek-us.com/wp-content/uploads/2020/12/B_-BL.pdf)
and [current catalog](https://www.mitek-us.com/wp-content/uploads/MiTek-Structural-Connector-Catalog.pdf)
list 12-gauge G90 B88, **six 3/8-in bolts total** (three per leg), bolts at
least ASTM A307, minimum 3-in wood-member thickness, and DF/SP single-brace
allowable loads of 620 lbf F1 and 305 lbf F2. Its loads already include the
60% wind/seismic duration increase, with no further increase permitted.
For F1 resistance in both directions, braces are required on both sides.
MiTek says all specified fasteners must be used. The
[ICC-ES ESR-3455 Table 3 and notes](https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf)
independently show the same B88 dimensions, fastener count, 620/305 lbf
values, 3-in minimum, and `C_D = 1.6`. The report requires at least ASTM
A307 Grade A bolts with minimum `F_yb = 45,000 psi`, and explicitly says
these allowable loads **do not apply to other load durations and may not be
adjusted to them**. Neither source supplies a complete rating for a MoonBoard
joint wrench, separation, independent flange moments, or the actual member
and bolt arrangement.

The same ESR's Section 3.29.1 and Table 29 identify B-series base steel as
ASTM A653 Structural Steel Grade 40, G90, with **0.099 in minimum base-steel
thickness** for 12 gauge. These are published conditional inputs for a
separate formed-bracket/bolt/wood calculation, not a finished B88 resistance.
That calculation would still need the actual installed load path, hole and
bend section geometry, combined actions, and applicable design standard.
Do not infer a usable `C_D = 1.0` B88 value by dividing the barred `C_D =
1.6` table values or treating flat-sheet yield as a bracket rating.

## Disposition

**Enough for a reversible nominal-geometry trial, not enough for fabrication
or structural acceptance.** The official DXF supplies a six-center CAD pattern
and the manufacturer chart ties the available retail UB88 model to B88.
Such a trial must still check full steel/bolt/washer/tool envelopes, the
minimum 3-in receiving-wood thickness, every protected panel/kicker screw
and kerf-right kicker edge, wood edge/end geometry, and load directions.
Before any drilling, reconcile the CAD model with a verified factory
dimension/tolerance source or a received-part measurement and complete the
installed-joint checks. Do not import the 620/305-lbf wind/seismic values
as board capacities or assume local Home Depot stock.
