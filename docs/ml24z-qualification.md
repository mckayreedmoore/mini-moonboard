# ML24Z connection qualification

The manufacturer now provides enough information to replace the assumed ML24Z
hole pattern and generic SDS screw head with product-backed nominal geometry.
This is progress toward connection qualification, not structural approval.
No manufacturer PDF or CAD file is redistributed here: the source links and
download hashes are recorded in [ml24z-reference.json](ml24z-reference.json).

## Manufacturer evidence

The [ML product page](https://www.strongtie.com/decks_decksandfences/ml_angle/p/ml)
links official 2D DXF and 3D SAT/IFC/STL files. Its drawing disclaimer describes
the geometry as a reasonable approximation, not an exact representation.
Consequently, the precision below identifies the supplied drawing coordinates;
it does not establish manufactured tolerances or authorize predrilling all wood
from these coordinates without checking the selected product.

The [L-C-MLZ25 engineering letter](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
is dated December 23, 2025 and valid through December 31, 2027. It adds lateral
and bearing-installation information to the
[2026 catalog page](https://ssttoolbox.widen.net/content/wrzfhjzbna/pdf/C-C-2026-p323.pdf).
Each ML24Z uses six separately purchased 1/4 × 1-1/2 inch Strong-Drive SDS
connector screws, three in each flange. Other screw families are not equivalent.

## Nominal geometry and coordinate convention

Use two perpendicular **outer wood-contact planes** meeting at a virtual corner.
Measure each flange's hole offset from the other outer contact plane, along the
flange. Measure width coordinates from the midpoint of the 4 inch bend line.
Do not subtract steel thickness from these offsets or confuse the virtual
corner with the inside bend tangent.

| Feature | Manufacturer drawing value |
| --- | --- |
| Bend-line width | 101.6 mm / 4 in |
| Steel thickness | 2.55524 mm / 0.1006 in |
| Outside reach of each flange from the virtual corner | 53.35524 mm / 2.1006 in |
| Inside / outside bend radius | 5.08 / 7.63524 mm; 0.2 / 0.3006 in |
| Hole diameter | 6.731 mm / 0.265 in |
| Hole width stations | −38.1, 0, +38.1 mm; −1.5, 0, +1.5 in |
| Front-view flange offsets at those stations | 42.24274, 35.89274, 42.24274 mm |
| Opposite flange offsets at those stations | 35.89274, 42.24274, 35.89274 mm |

The staggered offsets are 1.6631 and 1.4131 inches. The manufacturer labels the
product nominally 2 × 2 × 4 inches; that label is not the full outside envelope
of the downloaded drawing. The side DXF also includes a roughly 0.00669 mm
coordinate discrepancy at one bend tangent, reinforcing that this is reference
geometry rather than a tolerance-controlled fabrication drawing.

The official SDS25112 drawing has a maximum head envelope of 12.7889 mm
(0.5035 in) diameter and 5.6134 mm (0.221 in) height above the bearing plane.
Under-head length is 38.1 mm (1.5 in). Subtracting the drawn angle thickness gives
35.54476 mm gross wood penetration. This is not an effective threaded-length or
withdrawal-capacity calculation. The
[SDS product page](https://www.strongtie.com/strongdrive_exteriorwoodscrews/sds_screw/p/strong-drive-sds-heavy-duty-connector-screw)
recommends a low-speed 1/2 inch drill and 3/8 inch hex driver; actual socket and
drill access must also be checked in the assembly.

## Published connection loads and their limits

The following are ML24Z allowable loads in pounds-force from L-C-MLZ25, for one
connector with all six specified screws. A dash is **unlisted**, not zero and not
permission to substitute another direction's rating.

| Installation / wood group | F1 | F2 | F3 | F4 |
| --- | ---: | ---: | ---: | ---: |
| Single/end, DF/SP | 595 | 450 | 450 | 750 |
| Single/end, SPF/HF | 450 | 340 | 340 | 540 |
| Bearing, DF/SP | 595 | — | 450 | 750 |
| Bearing, SPF/HF | 450 | — | 340 | 450 |

F1 follows the bend line. F2 and the opposing F3/F4 directions must be mapped
from the letter's installation figures, including which member is loaded.
These ML24Z values do not receive a load-duration increase. The letter also
requires the designer to consider reinforcement where cross-grain bending or
tension cannot be avoided. It supplies no general mixed-axis interaction rule
for this climbing frame. Do not sum all connectors' ratings or divide the load
equally among them without an appropriate load-distribution model.

## Application to the current bearing-frame candidate

The sixteen inherited beam-joint angles have their bend lines along board-normal
N, so F1 corresponds to N. The four new lower-ledge angles have their bend lines
along board-width X, so F1 corresponds to X instead.

For the lower-ledge **bearing-installation analogy**, the flat ledge is the
standing member in plane X/S and the lower rail supplies the base in plane X/N.
The unlisted F2 separation direction therefore lies along S, while F3/F4 lie
along N. The actual ledge extends downhill from the rail: downhill gravity can
pull it away rather than press it into the rail. This is an unresolved
installation-classification and load-direction issue. The single/end F2 rating
cannot simply be transferred to that arrangement. This finding does not prove
physical failure; it prevents claiming qualification from the bearing table.

The frozen bearing-frame model still uses assumed ±34 mm width stations and
18/34 mm flange offsets, 2.7 mm steel, and a sharp bend. Those differ materially
from the official geometry. Its successful collision tests therefore do not
establish that the purchased ML24Z and SDS25112 fit. Existing panel attachment,
kicker/splice, leg, cross-grain wood, racking and unanchored stability limitations
also remain outside this connector-reference update.

## Finite next steps

1. Add a separately versioned product-backed connector implementation, leaving
   source-bound historical models unchanged. Transform the official hole
   coordinates and nominal bent envelope into every installation.
2. Replace the associated SDS head envelope, regenerate receiver drilling, and
   rerun solid intersection, receiver engagement, edge/end distance, face-service
   clearance and tool-access checks for all twenty positions.
3. Record per-joint force vectors and member grain directions. Classify each
   installation against the letter, rather than assigning a common capacity.
4. Resolve the lower-ledge classification and mixed-axis treatment before
   applying connection limits to the structural model; then reassess the
   remaining frame and stability checks.

Suggested manufacturer question, **not sent**: Can an ML24Z with all six
SDS25112 screws connect a 38.1 mm flat ledge to a perpendicular 38.1 mm lower
rail in the rotated arrangement described above, when the ledge extends
downhill and experiences both separation along S and outward load along N?
Which L-C-MLZ25 installation and F2/F3/F4 signs apply, what combined-load rule
and minimum wood dimensions/grain conditions are required, and is reinforcement
needed? Supply the actual joint drawing and calculated force vectors with the
question; the letter lists Simpson engineering at 800-999-5099.
