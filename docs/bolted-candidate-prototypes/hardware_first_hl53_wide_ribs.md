# Wider HL53 ribs: partial header fit and isolated rail-seat probes

Status: **620 and 660 mm give partial nominal header fits; the connected
assembly is incomplete.** At 700 mm, a fixed screw axis meets modeled
hardware, so that spacing has a nominal clash. This is a geometry comparison
only. The full record is `hardware_first_hl53_wide_ribs.json`.

The three cases keep the prior screen's eight nominal HL53 header links and
move the separated rib centers to X = ±310, ±330, and ±350 mm. The kerf-right
panels, all 66 panel/kicker screw axes and receivers, and central kicker seam
support stay fixed. The six side rails end 15 mm beyond each rib's outer
face: |X| = 369.45, 389.45, and 409.45 mm respectively. The 620 and 660 mm
header-link brackets, bores, modeled bolts, washers, and short tool envelopes
clear the screened wood, panels, and fixed hardware. Their rail ends still
lack factory connections, so neither is a connected assembly. At 700 mm,
the second lower rib/header bore on each side meets a protected
`kicker_header_*_1` screw envelope by 0.228 mm³. That clash is classified
independently of the open rail connections.

One **bottom-right rail-to-rib** HL53 joint is modeled at 660 mm only. The
rib outer face is X = 374.45 mm and the rail begins at X = 389.45 mm. The
rail is locally deepened as one continuous machined solid, with no ply, lap,
or custom steel. Four ideal
1/2-in bolts cross their own HL53 hole corridors and receiving wood. The
two rib axes have 88.9 mm of wood along the bolt direction; both rail-seat
axes have 100.0 mm, above the HL53 88.9-mm minimum. All four modeled bores
are contained. The isolated rib/rail/panel CAD screen finds no bracket,
bolt, washer, panel, protected screw, or straight tool-cylinder clash.
The original rail screw
receivers retain wood, and the sampled rail remains one solid. **This is
only isolated bolt geometry:** a thin CAD contact slice shows that the
first 15 mm of the 146.05-mm horizontal flange has no wood beneath it.
Contact spans 131.05 mm of reach, or 8321.675 mm² over the nominal flange
width. No rated allowance for that gap is adopted, so the 15-mm-gap joint
has no catalog-applicable installation verdict.

A separate **zero-gap probe** starts the same one-piece rail at the rib's
X = 374.45 mm outer face. The full 146.05-mm seat reach has modeled wood
contact (9274.175 mm²). CAD finds no rib/rail or bracket/rail volumetric
collision, and the four bolt, washer, panel, and short tool checks remain
clear within that isolated probe. Neither probe was screened against the
changed parent header and front carriers, other original wood members, or
the eight parent header-link brackets and their bolt/tool envelopes. Thus
the zero-gap result is not a parent-neighbor or full-assembly fit claim. It
also does not establish manufacturer installation applicability, actual
stack access, or the other five rail connections.

The minimum-*area* sampled one-piece rail blank envelopes are **737.675 ×
102.7942 × 145.1394 mm** for the 15-mm gap and **752.675 × 102.7942 ×
145.1394 mm** for zero gap (X extent plus a Y/Z rectangle sampled at 0.1°).
Minimum area is not the right test for a square stock cross-section. For the
zero-gap rail, a separate 0–90° scan at 0.001° steps minimizes the *maximum*
Y/Z extent. At 4.885° about X, the sampled extents are **125.8675 ×
125.8684 mm**, with **752.675 mm** required X length. This is a sampled
geometry envelope, not a cut plan or a guaranteed minimum after tolerances.

A nominal dimensional comparator is Lowe's [6×6×8-ft #2 Better Douglas Fir
Green Lumber, model 637643](https://www.lowes.com/pd/6-in-x-6-in-x-8-ft-douglas-fir-lumber-common-5-652-in-x-5-652-in-x-8-ft-actual/1000009798).
Its listed actual dimensions are 5.652 × 5.652 in × 8 ft, or **143.5608 ×
143.5608 × 2438.4 mm**. Those listed dimensions enclose the sampled zero-gap
rail envelope. Local availability, delivered dimensions, moisture and drying,
grade verification, machining allowance, defects/straightness, and suitability
of its listed anti-stain treatment remain open. No blank has been inspected;
this is **not stock acceptance**, nor does it change the isolated-fit or
catalog-applicability limits above.

The washer and tool models are approximate 25.4-mm washer and 38.1-mm by
30-mm straight access cylinders. Their lack of a collision is **not** an
actual head/nut stack or full tool-access pass. Delivered HL53 dimensions,
bolt lengths, full hardware stacks, catalog installation applicability,
wood joint checks, and the other five rail-to-rib connections remain open.
The [corrected HL load-axis audit](hl-load-axis-audit.md) is separate; this
screen makes no load-axis or capacity verdict. No rating, fabrication, or
drilling is released.
