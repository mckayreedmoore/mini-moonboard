# Round-passage insert development: evidence and remaining decisions

The `round-insert-development` candidate replaces the preceding round-frame
panel wood screws with 56 modeled E-Z LOK 801420-13 inserts and Dottie FMDD14114
machine screws. It retains twelve attachments per main panel, four per kicker,
the enclosed wiring passages, and the structural bracket and leg connections.
It is not released for construction or climbing. A modeled insert is not a
verified installed connection.

Use the matching [build draft and tools](round-insert-build-plan.md),
[drilling references](round-insert-drilling/drilling.pdf),
[hardware schedule](../exports/round-insert-development/panel-insert-schedule.csv)
and [viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=round-insert-development).
The [preceding screw model](round-service-analysis.md) and its native evidence
remain historical; their screw capacity references do not apply to inserts.

## Attachment geometry and product information

The [assembled geometry audit](../fea/results/round-insert-audit-v1.json) passes
all its tested gates: 56 actual insert bodies and machine screws, maximum
insert envelopes and blind reservations contained in their receivers, no tested
hardware/electrical collision, and clearances to all 142 hold-service
reservations. It also checks the retained eight bolt stacks, 24 brackets with
144 SDS screws, 32 passages, 132 lights and 131 wire routes. These are fit
results, not installed strength or machining approval.

The [current hardware reference](round-insert-hardware-reference.json) records
the manufacturer sources and distinguishes their dimensions from project
assumptions. Dottie's screw head has an 80–82 degree product range. The displayed
head uses the largest diameter and the 80 degree limit as a clearance envelope;
the previous SPAX 90 degree seat is not retained.

The nominal 0.25 mm receiver recess, 7 mm panel clearance and 17 mm receiver
depth are provisional CAD reservations. They are not released drill dimensions.
At that recess, the maximum insert length plus an idealized 118 degree drill
point leaves about 0.368 mm for additional bottom clearance. Received parts,
actual recess, drill geometry and machining tolerances must be reconciled.
Gross screw reach is not effective thread engagement: insert drive-recess depth,
usable internal threads and screw thread runout remain unknown.

E-Z LOK does not publish Hex Drive insert test results because performance
depends on installation variables. Its [testing policy](https://www.ezlok.com/testing)
does not provide an allowable withdrawal or lateral resistance for this
assembly. A larger insert diameter, clearance pass or finite-element equilibrium
pass cannot fill that missing resistance value.

## Load model and panel connections

The [load and attachment review](round-insert-load-analysis.md) evaluates the
assumptions behind the earlier withdrawal flag. A crucial distinction is contact:
the earlier model gave the panels only discrete fastener springs, including in
compression. The new diagnostic considers compression-only panel-to-timber
contact, with no frictional panel support or connection across independent seams.
Connection stiffness, contact sampling and penalty stiffness remain numerical
assumptions rather than measured product properties.

Five native cases completed; the high attachment-stiffness probe stopped on a
DAT/FRD displacement consistency failure, leaving two subsequent probes unrun.
The completed stiffness comparison changes peak withdrawal substantially, so
these are diagnostic demands, not calibrated hardware demands. The
[APA AC-family bounds](round-ac-plywood-bounds.md) provide a conditional material
basis, but the current isotropic shell does not reproduce its separate axial
and bending stiffnesses.

Retain the twelve-per-panel development layout while those uncertainties and
actual resistance are resolved. Neither reducing assumed loads to obtain a pass
nor increasing fastener count alone establishes a safe fastening schedule.

## Timber, brackets and leg bolts

The [current insert member and connection assessment](round-insert-member-connections.md) separates
recovered force demands from applicable resistance. The native retained timber
prism is not the actual local section around a round passage. Net-section
arithmetic does not resolve hole-edge stress concentration, splitting or the
interaction of insert machining with local wood behavior.

Bracket product ratings require matching installation, load direction and
material conditions. A rated single force direction does not automatically
provide a resistance to the free moments or combined forces recovered from a
frame model. Leg-bolt fit likewise does not establish wood bearing, splitting,
group action or resistance under the actual floor reactions.

## Floor and lighting

The [floor and harness verification notes](round-floor-harness-verification.md)
separate rigid-floor feasibility and geometric route length from physical fit.
The actual floor material, foot treatment, friction, support contact and finished
mass remain unverified. The [fresh insert-floor report](../fea/results/round-insert-floor-v1.json.gz)
integrates 167.598 kg of modeled wood and structural hardware, including zinc
inserts. It independently checks 3,125 feasible force witnesses. At assumed
friction 0.1, 763 of 1,296 polygon cases fail, including 720 proven impossible
under the stated circular-friction necessary condition. At assumed friction
0.2 and 0.4, all 1,296 finite cases have feasible witnesses. These remain
rigid-floor feasibility results with assumed densities and friction, not actual
contact reactions, a continuous load envelope or a measured floor rating.

The [surface scenarios](round-floor-surface-assumptions.md) cover hardwood,
carpet and horse stall mats with 25,920 new solves under explicit assumed
friction and contact loss. All nominal sampled cases have feasible witnesses;
degraded friction and loss of either rear foot produce failures.
The [material and current LED-kit review](round-material-led-verification.md)
retains the owned AC fir plywood and distinguishes 132 modeled active lights
from unused bulbs, external leads and the supplemental power branch.

The owner's 12.7 mm maximum harness diameter and approximate 304.8 mm bulb pitch
are useful inputs, but do not establish the shortest interval, connector length,
bend radius or feeding access after panel installation. An intact-strand routing
check on the actual assembled passage geometry remains required.

## Evidence needed from the physical build

| Unresolved item | Evidence needed before release |
| --- | --- |
| Delivered wood and owned Roseburg plywood | Actual thickness, grade/species stamps, strength axis, condition and applicable material properties |
| Insert seating and engagement | Received screw and insert dimensions, usable thread intervals, recess and blind-hole clearance |
| Connection resistance | Applicable assembly-specific resistance or a qualified test basis for withdrawal, lateral and combined/cyclic loading; include plywood head bearing |
| Local drilled members and joints | Applicable local-section, splitting and connection checks using current force demands and delivered material |
| Actual floor | Verified support contact and surface/foot properties under the intended installation conditions |
| Intact LED strand | Actual connector/body dimensions, shortest pitch, permitted bend geometry, installation slack and successful unpowered feed check |

No person-load experiment is authorized by these calculations. Tests used to
establish structural resistance need a suitable fixture, instrumentation and
acceptance basis; a successful assembly or one successful loading is not a
climbing qualification.
