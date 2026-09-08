# Connection qualification ledger

**The frame is not structurally qualified or build-ready.** This ledger covers
`wide-principal-development`: 24 through-bolts, 18 ML24Z angles with 108
separately purchased SDS25112 screws, and 56 panel machine-screw/insert pairs.
Geometry checks establish modeled fit, not resistance or a climber weight rating.

The [current bracket-axis audit](wide-bracket-axes.md) maps all eighteen angles
and 108 screws to named members: twelve bend axes follow board-normal N and six
header bend axes follow world Y. This resolves placement bookkeeping, not the
loaded-member installation classification, mixed-axis rule or joint forces.

The [current fastener-fit audit](current-fastener-fit-audit.md) now verifies all
48 washer support planes against actual machined CAD and checks the 24 nominal
bolt stacks with dimensional tolerances. Those checks do not qualify resistance.

An additional SDS thread-envelope check covers the published 6.5024 mm nominal
major diameter, larger than the simplified 6.35 mm viewer shaft. All 108 current
SDS envelopes and the relocated-end trial's 116 envelopes clear other hardware
and fit their raw designated wood receivers. This is not a tolerance-qualified
maximum, a wood pilot specification or a resistance check; see the fit audit.

## Finite remaining checks

| Family | Established information | Missing demand or resistance | Next bounded check |
| --- | --- | --- | --- |
| Eight leg-to-board bolts | 76.2 mm grip through one rim and two leg plies; selected 3/8-inch hardware envelopes | Existing timber FEA combines rim and panel-edge transfer; it does not give individual bolt loads or independent-ply sharing. Plywood bearing/splitting resistance is unqualified. | Isolate the intended leg/rim load path, then recover its wrench and evaluate the bolt group with actual ply properties. Do not divide the aggregate result by four. |
| Six leg-ply stitch bolts | 38.1 mm two-ply grip; existing geometry/mesh tools describe interfaces | Differential ply force, slip, bearing and composite action are not established. | Define independent-ply behavior and recover transfer demands before evaluating stitches. No glue or clamp-friction credit is assumed. |
| Eight base-gusset bolts | 57.15 mm grip through 38.1 mm timber and 19.05 mm assumed plywood | Gusset force/moment distribution, timber/plywood dowel bearing, splitting, net section and washer behavior | Recover a gusset free body, then check its four-bolt group and both connected materials. Confirm actual gusset thickness and grade. |
| Two lower-backing bolts | Recessed 3/8-inch bolts; 127.668 mm modeled net grip; widened principal provides 44.45 mm side-edge distance | No isolated backing wrench. Axial washer/wood resistance, counterbore ligament and combined lateral loading remain unknown. | First derive a conditional axial-separation resistance envelope; subsequently compare it with a defensible backing-joint demand. |
| Eighteen ML24Z angles / 108 SDS25112 screws | Manufacturer nominal geometry, required screw schedule and directional connection values; current per-member bend/flange axes mapped | Actual loaded-member assignment, per-joint demands, installation classification and mixed-direction treatment | Use the completed axis schedule to classify each loaded-member installation and its signed demands; resolve unlisted or combined directions with the manufacturer/reviewer. |
| Fifty-six panel inserts and machine screws | Selected product geometry, nominal reach and pilot reservations | Effective engagement, insert withdrawal/rotation, panel pull-through, lateral/cyclic behavior and torque are not qualified | Confirm usable thread engagement and installation details, then obtain supplier-supported application testing or select a suitably rated alternative. |

The nominal leg/gusset plywood thickness is not the purchased face plywood's
23/32-inch category thickness. Do not silently interchange these materials.

The [current NDS plywood-bolt source check](plywood-bolt-resistance-basis.md)
also excludes direct use of Table 12.3.3B for these 3/8-inch bolts: that table
covers diameters at most 1/4 inch. The follow-up AWC TR12 Appendix A source
supplies 5,600 psi plywood dowel-bearing strength for larger bolts. That resolves
the bearing input, not the resistance calculation. Member-specific threaded
bearing, yield modes and the other joint limit states still require evaluation;
do not use solid-lumber properties or equate bearing stress with a joint rating.

The [conditional two-member yield calculation](two-member-bolt-yield.md) now
provides reference values of about 512 N per stitch bolt and 615 N per gusset
bolt under explicit root-diameter, material and zero-gap assumptions. These are
not adjusted group resistances and do not supply actual individual-bolt demands.

The [gusset two-interface calculation](gusset-group-envelope.md) now separates
the upper rim pair from the lower post pair and includes their 90/240 mm centroid
offset. Its conditional reference scales are 344 N FY, 538 N FZ or 49 N·m MX,
separately applied at the upper centroid. These cannot be added or used as an
actual group capacity; signed force/moment combinations and load-path demands
remain necessary.

The [current gusset mesh audit](gusset-load-path-audit.md) confirms additional
shared degrees of freedom with the header and kicker boundary, besides rim and
post. A recovered bonded-gusset resultant therefore cannot be treated as the
two-bolt-pair load path without separating those interfaces and their physical
contact assumptions. Neighbor-node counts are overlapping, not summed areas.

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

The [current backing-leverage calculation](wide-backing-leverage.md) now
evaluates the six real attachment X positions against the two central bolt
axes. Under its explicitly projected two-support model, an outer attachment
produces up to 7.024 times its outward load as positive retention reaction and
an opposing compression reaction. This is not actual bolt demand or a bound;
finite housing contact, panel sharing and off-axis torsion remain unresolved.

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

The [conditional bearing envelope](backing-bearing-envelope.md) now records
the 2024 NDS material assumptions and a reproducible calculation: approximately
997 N dry or 668 N with the stated wet-service adjustment per bearing plane.
These are wood-bearing-only values, not qualified connection resistances.
Both washers act in series, and assembly preload also consumes bearing pressure.

The subsequent [isolated retention ceiling](backing-retention-envelope.md)
combines those conditional per-bolt caps with the relaxed housing geometry.
Outer attachment dry-case ceilings are approximately 245 N left and 230 N right,
with force/moment and primal/dual checks. These are not actual panel demands or
whole-frame capacities; they keep end retention/load transfer a priority rather
than treating wider central principals as a completed connection solution.

The [aggregate base-action recovery](timber-base-demand.md) now covers six original
and 216 asymmetric cases on the preserved timber mesh. It identifies fixed
kicker-bottom support as well as post support. It does not split those actions
among gussets, backing bolts or the header's bearing contacts.

## Achievable next stage and human gates

The current wider candidate now has its own
[nine-basis, 216-scenario asymmetric evidence](wide-asymmetric-results.md),
including reconstructed leg and eleven-member base ownership. This closes the
previous lack of candidate-specific aggregate actions; it does not supply the
isolated bolt, gusset, backing or angle demands listed above. The 300 lb
maximum-displacement case has approximately −561 N net vertical base reaction
in the no-gravity fixed-floor model, emphasizing that these constrained actions
cannot be used as the actual unanchored support state.

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

The subsequent [current-wide floor equilibrium screen](wide-floor-screen.md)
includes gravity and balances yaw with compression-only frictional reactions.
All 1,296 sampled cases are feasible at assumed coefficients 0.2 and 0.4;
613 are polygon-infeasible at 0.1, including 504 necessary aggregate sliding
bound violations. This supports retaining the current footprint for joint
development, not actual floor acceptance or an individual joint-demand allocation.
