# Removable panel insert candidate

Checked 2026-09-08. **Geometry-development selection only: panel retention is
structural, and this insert connection has no established allowable capacity.**
Keep ML24Z/SDS connections and structural through-bolts unchanged. This candidate
replaces only panel-to-timber wood screws in a separately reviewed variant.

## Selected commercial pair

- **E-Z LOK 801420-13:** flush, die-cast zinc, 1/4-20 internal thread. The
  manufacturer's D-S.72 Rev2 drawing gives length 0.512 in (13.0048 mm), outside
  diameter 0.453 in (11.5062 mm), a 6 mm hex drive and general dimensional
  tolerance ±0.025 in (±0.635 mm). Its pilot recommendation is 23/64 in
  (9.128125 mm); the adjacent metric column rounds this to 9 mm. These are not
  exact equivalents. Use the inch recommendation as the initial geometry datum,
  not a universal approved drilling instruction.
  [Product](https://www.ezlok.com/ezhex-insert-801420-13),
  [manufacturer drawing](https://www.ezlok.com/assets/documents/dimensional_drawings/Dimensional%20Dwg%20-%20HexDriveFlush.pdf).
- **L.H. Dottie FMDD14114:** zinc-plated carbon-steel 1/4-20 × 1-1/4 in
  Phillips/square flat-head machine screw. Manufacturer lists head diameter
  0.442–0.477 in (11.2268–12.1158 mm), reference head height 0.153 in
  (3.8862 mm), and #3 drive. It is a currently listed product, not a local-stock
  or purchase confirmation.
  [Product and linked technical drawing](https://lhdottie.com/14-20-flat-head-squarephillips/fmdd14114).

The manufacturer-linked IFI sheet specifies an 80–82° head, nominal overall
length 31.75 mm with minus 1.524 mm tolerance, and external major diameter
6.11632–6.32206 mm. The head height is a reference dimension, not an independent
guaranteed maximum. Use a nominal 82° countersink concept and verify the mating
profile; do not combine every maximum into an allegedly exact head solid.
The sheet's advisory 5.3 N·m torque is **not** an installation torque for this
wood/zinc-insert assembly.
[IFI sheet supplied through Dottie's product page](https://axjajfi6s7ed.objectstorage.us-phoenix-1.oci.customer-oci.com/p/GErcQA5fiECdu1FFc-U2mTY4wqjfsz5LctKiDPhxcB0pBfgP4Jsw2lB6qNKPIySv/n/axjajfi6s7ed/b/Magento/o/TechnicalDataSheets%2FFMDD14114.pdf).

## Fit arithmetic and intentionally unresolved details

Install the insert flush with the **timber receiver surface**, not inside the
face plywood. At the modeled 18.25625 mm face/kicker thickness, a flush-seated
screw reaches nominally 13.49375 mm into the receiver, or 11.96975 mm at its
published minimum length. This is **gross reach, not effective thread engagement**:
the insert's internal hex/recess depth, complete thread length and screw-tip
runout have not been specified by the retrieved drawing. The product page lists
minimum full thread depth as unavailable. Do not assume thirteen millimeters
of usable internal thread.

For an inspectable CAD trial, reserve a 17 mm-deep pilot/tip-clearance volume
from the receiver surface and a 7 mm panel clearance bore. Both are **project
geometry assumptions**, not manufacturer-approved drilling dimensions. Resolve
drill-point depth and bottoming from the actual selected parts before manufacture.
A nominal 38.1 mm receiver depth would retain 21.1 mm beyond that assumed pilot.
On a centered 38.1 mm-wide receiver, maximum insert OD 12.1412 mm leaves
12.9794 mm geometric side ligament. Neither calculation qualifies splitting,
loaded-edge distance, withdrawal or net-section resistance. Actual receiver
positions and service pockets still require individual checks.

## Qualification gate

E-Z LOK does not publish Hex Drive testing results because installation variables
affect performance. No pullout, lateral or cyclic allowable load is assigned here.
[Manufacturer testing policy](https://www.ezlok.com/testing).

Before this becomes a build specification, resolve complete thread engagement,
seating and installation torque; insert withdrawal/rotation in the actual
Douglas-fir receiver; panel-head pull-through and countersink damage; splitting,
edge/end distances, combined load and repeated assembly. The insert's zinc
material and screw's metal strength do not establish wood-joint capacity.

Use the manufacturer drive tool 9000 or appropriate 6 mm hex for insert
installation. The manufacturer warns that pilot requirements depend on material
and tooling and recommends application testing. Do not silently bypass that
qualification by calling a nominal geometric fit a successful test.
[Installation guidance](https://www.ezlok.com/e-z-hex-drive-insert-installation),
[dimensional drawing and pilot caveat](https://www.ezlok.com/assets/documents/dimensional_drawings/Dimensional%20Dwg%20-%20HexDriveFlush.pdf).

Machine-readable facts and unknowns are in
[`panel-insert-reference.json`](panel-insert-reference.json). No vendor CAD or
PDF is copied into the repository, and no hardware has been purchased.
