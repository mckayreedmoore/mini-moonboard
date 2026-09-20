# Independent-bolt HL33 front backing: one bounded A revision

**Rejected nominal pose.** This is one kerf-right geometry and access screen,
not a connector rating or drilling plan. Regenerate the paired JSON with:

`uv run python -m scripts.hardware_first_hl33_backing_revision --output docs/bolted-candidate-prototypes/hardware_first_hl33_backing_revision.json`

The [Simpson C-C-2026 catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
(HL33, PDF p. 315) supplies the nominal 82.55-mm legs, 63.5-mm bend length,
31.75-mm along-bend hole position, 50.8-mm vertical-leg hole position, and
88.9-mm minimum bolted wood thickness. Its horizontal-leg hole inset is not
dimensioned; this screen assumes 50.8 mm. Ideal 4.55-mm plates and
14.2875-mm wood bore envelopes are diagnostic only. The outside-face screen
assumes 25.4-mm washers, 8/12-mm head/nut cylinders, and a 40-mm-diameter by
25-mm-long tool sweep. None is a delivered-hardware or drill specification.

The rear structural core is one 240 × 90.47 × 238.9-mm solid. One separate,
full-width front backing is 240 × 114.23 × 238.9 mm before two shallow
factory-plate slots. Its front face remains at the fixed kerf-right kicker
rear plane. Two HL33s attach core front face to backing outer faces, at
staggered Z bases of 80 and 150 mm. Each angle has its own through-core Y
bolt and its own transverse X bolt through **only the backing member**.
There is no bolt shared by the two brackets and no wing–tongue–wing stack.
The core and backing are separate, touching solids; the factory bracket bolt
paths provide the proposed attachment, while face contact is not counted as
one. One lower HL33 and two outward upper HL33s retain the center/header
concept. The changed header and all six inner rail endpoints are modeled; no
rail-to-center factory bracket is established. No lap or custom steel is used.

The four backing bolts each intersect exactly one wood receiver: the two
core-face bolts each pass through 90.47 mm of core, and the two independent
side bolts each pass through 240 mm of backing. The lower core is 90.47 mm;
the lower/upper header and upper principals are each 88.9 mm. Thus no modeled
HL33 receiver falls below the nominal minimum. This checks thickness and
occupied paths, **not** catalog applicability or connection resistance for
the installed angle orientation.

All six panel outlines and all 66 protected panel/kicker screw axes are fixed.
No screw loses its modeled receiving wood; each of the four center kicker
screws retains 438.127 mm³ of occupied overlap with the new backing. That
full-width backing and the raised header cover both inner kicker edges across
the modeled seam height. No plate, bore, or bolt path intersects a protected
panel or screw. Hold and LED voids are inherited from the unchanged panel
geometry but are not individually represented by solids in this screen.

The required two-ended access **fails**. The lower core bolt and both
backing-to-core bolts have their illustrative nut-side washers, nuts, and
tool sweeps inside the front backing. Each nut-side tool intersection is
31,415.927 mm³. Upper principal/header head or nut tools intersect the
bottom rails; one upper principal nut body also enters a bottom rail.
The independent backing transverse bolt stacks themselves have no recorded
panel, wood, or plate obstruction. The JSON gives all 60 washer/head/nut/tool
envelopes and clash volumes. A different pocket, bracket station, bolt
orientation, or rail detail would need another checked pose; this result
does not infer access from installation order.

The [Lowe's 4×12×12-ft #2 Better Douglas-fir green listing](https://www.lowes.com/pd/Douglas-Fir-Lumber-Common-4-in-x-12-in-x-12-ft-Actual-3-562-in-x-11-5-in-x-12-ft/1000028845)
gives 90.4748 × 292.1 × 3657.6 mm actual. It contains the core's
axis-aligned envelope by only 0.0048 mm in the 90.47-mm direction, with no
machining margin, and **does not contain** the backing's 114.23-mm Y depth.
The ordinary-stock gate is **open**: this Lowe's/Home Depot class of 4×12
lead does not contain both one-piece members. No larger ordinary big-box blank
is verified here. Delivered dimensions, drying, grade suitability, local
availability, straight yield, and machining allowance remain unknown. The
listing is not approved stock.

The [corrected local-axis audit](hl-load-axis-audit.md) places the outward
upper HL F1 reach along signed global X and the rearward lower HL F1 reach
along −Y; the transverse directions are unlisted. It assigns no capacity to
this installation or to the vertically bent backing angles. Reversible load
paths, F2, moment, independent backing action, bolt resistance, wood edge/end
distance, and the six rail connections remain open. No cutting, drilling, or
rating follows.
