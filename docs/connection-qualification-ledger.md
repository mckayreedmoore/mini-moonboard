# Connection qualification ledger

**The frame is not structurally qualified or build-ready.** This ledger covers
`wide-principal-development`: 24 through-bolts, 18 ML24Z angles with 108
separately purchased SDS25112 screws, and 56 panel machine-screw/insert pairs.
Geometry checks establish modeled fit, not resistance or a climber weight rating.

## Finite remaining checks

| Family | Established information | Missing demand or resistance | Next bounded check |
| --- | --- | --- | --- |
| Eight leg-to-board bolts | 76.2 mm grip through one rim and two leg plies; selected 3/8-inch hardware envelopes | Existing timber FEA combines rim and panel-edge transfer; it does not give individual bolt loads or independent-ply sharing. Plywood bearing/splitting resistance is unqualified. | Isolate the intended leg/rim load path, then recover its wrench and evaluate the bolt group with actual ply properties. Do not divide the aggregate result by four. |
| Six leg-ply stitch bolts | 38.1 mm two-ply grip; existing geometry/mesh tools describe interfaces | Differential ply force, slip, bearing and composite action are not established. | Define independent-ply behavior and recover transfer demands before evaluating stitches. No glue or clamp-friction credit is assumed. |
| Eight base-gusset bolts | 57.15 mm grip through 38.1 mm timber and 19.05 mm assumed plywood | Gusset force/moment distribution, timber/plywood dowel bearing, splitting, net section and washer behavior | Recover a gusset free body, then check its four-bolt group and both connected materials. Confirm actual gusset thickness and grade. |
| Two lower-backing bolts | Recessed 3/8-inch bolts; 127.668 mm modeled net grip; widened principal provides 44.45 mm side-edge distance | No isolated backing wrench. Axial washer/wood resistance, counterbore ligament and combined lateral loading remain unknown. | First derive a conditional axial-separation resistance envelope; subsequently compare it with a defensible backing-joint demand. |
| Eighteen ML24Z angles / 108 SDS25112 screws | Manufacturer nominal geometry, required screw schedule and directional connection values are available | Actual loaded-member orientation, per-joint demands, installation classification and mixed-direction treatment | Map each installed angle to the manufacturer's load axes and installation figure; resolve unlisted or combined directions with the manufacturer/reviewer. |
| Fifty-six panel inserts and machine screws | Selected product geometry, nominal reach and pilot reservations | Effective engagement, insert withdrawal/rotation, panel pull-through, lateral/cyclic behavior and torque are not qualified | Confirm usable thread engagement and installation details, then obtain supplier-supported application testing or select a suitably rated alternative. |

The nominal leg/gusset plywood thickness is not the purchased face plywood's
23/32-inch category thickness. Do not silently interchange these materials.

## What the supplier information can establish

The [selected bolt/nut/washer record](selected-bolt-hardware.md) identifies
dimensions, thread engagement concerns and stack tolerances. The
[Conquest bolt specification](https://www.fastenersplus.com/cdn/shop/files/CQ-Hex-Head-Bolts-Spec-Sheet.pdf?v=17509241941931126534)
does not, by itself, rate the assembled wood connection. Washer material,
bending and local timber behavior still require a resistance basis.

The [Simpson ML24Z engineering letter](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
provides single-connector directional allowable loads with all six specified
screws. Those values cannot be multiplied by the frame's connector count or
transferred across installation/load directions. See
[the existing reference and limitations](ml24z-qualification.md).

[E-Z LOK's testing policy](https://www.ezlok.com/testing) does not provide Hex
Drive application capacities. Product dimensions are not withdrawal or lateral
resistance data. Likewise, the previous SPAX plywood-fastener references do not
apply to a zinc insert and a different machine-screw head. The
[insert selection record](panel-insert-selection.md) preserves these unknowns.

## Backing bolts: distinguish axial and lateral questions

The widened principals add approximately **23.68 kg** in the current comparison
and resolve a particular transverse edge-distance geometry condition. That
does not establish that this mass increase is structurally necessary. A purely
axial board-normal bolt force is a different check from lateral cross-grain
loading toward the principal's side edge. The narrower predecessor remains
unqualified for the latter condition; it is not automatically qualified for
the former either.

A useful next calculation can treat axial separation force **T** as an input
and determine the applicable resistance limits without claiming that T is the
actual frame demand. It must address bolt/nut threads, washer bending, bearing
under both washers and local wood failure around the recessed head.

For illustration only, the selected washer's minimum outside diameter is
20.447 mm, from the [supplier-linked SAE dimensional sheet](https://cdefasteners.com/sites/default/files/product-specs/washerssae.pdf).
Using the modeled 11.1125 mm wood bore, an ideal fully supported annular area is:

`A = π/4 × (20.447² − 11.1125²) = 231.372 mm²`

An assumed 1 kN axial force would therefore produce average pressure
`1000/A = 4.322 MPa`. **This is a geometric pressure calculation, not an allowable
force or a pass.** It assumes the annulus remains fully supported and does not
account for washer flexibility or nonuniform pressure. The front counterbore
also leaves only `38.1 − 12.032 = 26.068 mm` of backing thickness locally.
Widening a principal does not enlarge this washer annulus or thicken that
backing ligament.

Actual adjusted compression-perpendicular-to-grain properties, local splitting
and net-section behavior, and washer bending resistance must be established
before using a conditional axial limit. Lateral/axial interaction and prying
remain separate. Assigning half the board force to each bolt is not a proven
upper bound on joint demand.

## Achievable next stage and human gates

The next analytical milestone is a source-backed **conditional connection
envelope**, starting with the backing's axial load path, plus a clearly isolated
leg/rim demand model. Existing free-body and bolt-group arithmetic can assist,
but old contact/bearing studies cannot transfer capacities to changed stock,
holes or hardware. Preserve both lightweight and widened variants until the
comparison has a defensible connection basis.

Human inputs are finite: verify lumber/plywood grade stamps and actual sections,
inspect complete screw/insert engagement, identify washer material and tools,
and establish the real floor condition/friction. Supplier or professional input
is needed where installation classifications or allowable resistances remain
unpublished. A structural reviewer must reconcile load combinations, connection
behavior, unanchored stability and the physical validation procedure before
construction or climbing approval. Physical tests need a planned, controlled
setup; no person should serve as a proof load. The crash pad remains separate
from the structural model.
