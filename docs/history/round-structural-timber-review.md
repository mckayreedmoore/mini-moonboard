# Current structural-screw candidate: timber and leg-joint review

**Status: geometry quantified; member and leg-joint resistance not released.** This review applies to `round-structural-development`, with structural panel screws and 38.1 mm LED passages. It does not transfer a strength result from the historical screw or insert designs. No physical floor testing is requested; the structural review still needs explicit assumed supports and loads.

## Pre-centering passage sections (comparison only)

The pre-centering inventory contained 32 passages, all in nominal 2x6 members. Each crossed the 38.1 mm thickness perpendicular to grain, at local depth N = 35 mm in 139.7 mm deep stock. The current revision moves these axes to N = 69.85 mm; the centered-section calculation below applies to that revision. The following off-center figures are retained only for comparison. Their diameters are 38.1 mm. The 25.4 mm rule for other stock remains in the implementation, but no such passage occurs in this inventory.

| Member | Passage centers along grain, mm | Count |
|---|---|---:|
| `base_principal_center_left` | S = 2219.2 | 1 |
| `base_principal_center_right` | S = 19.2 | 1 |
| `base_rail_bottom_left` | X = −989.2, −789.2, −589.2, −389.2, −189.2 | 5 |
| `base_rail_service_lower_left` | Same five left X positions | 5 |
| `base_rail_service_upper_left` | Same five left X positions | 5 |
| `base_rail_bottom_right` | X = 210.8, 410.8, 610.8, 810.8, 1010.8 | 5 |
| `base_rail_service_lower_right` | Same five right X positions | 5 |
| `base_rail_service_upper_right` | Same five right X positions | 5 |

These are wiring-path positions, not a claim that the holes mirror left/right. Within each rail the clear distance between passage edges is 161.9 mm. Principal bottom ends are level bearing cuts, not square ends at S = 0; the S = 19.2 passage must be checked against that actual end geometry.

At the center section perpendicular to grain, a transverse circular bore removes a **38.1 × 38.1 mm rectangle**, not a circular area. The existing [`bore_section`](../fea/round_member_connection_assessment.py) gives the following exact isolated-passage geometry:

| Quantity | Value |
|---|---:|
| Front / rear ligament | 15.95 / 85.65 mm |
| Gross / net area | 5322.57 / 3870.96 mm² |
| Retained area | 72.7273% |
| Net centroid measured from front N = 0 | 82.91875 mm |
| Centroid shift behind gross centroid | 13.06875 mm |
| Strong-axis second moment | 6,056,572.413 mm⁴ |
| Weak-axis second moment | 468,260.354 mm⁴ |
| Minimum strong-axis section modulus | 73,042.254 mm³ |
| Weak-axis section modulus | 24,580.596 mm³ |

For a simultaneous section wrench at the **net centroid**, a nominal elastic normal-stress envelope in N/mm² is bounded by

`abs(N)/3870.96 + abs(Mstrong)/73042.254 + abs(Mweak)/24580.596`.

This is an arithmetic stress diagnostic, not a design acceptance equation. Tension/compression signs, biaxial interaction and stability must be checked separately. If actions are recovered at the gross centroid, shift the moment by the force cross the centroid offset first. Fastener holes and oblique ends can reduce the section further. Local bore stress concentration, shear flow around the opening, torsion and splitting are excluded.

## Shortest defensible timber design route

[NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf), §3.1.2, requires deductions for removed material and consideration of load eccentricity. Use its bending, shear, bearing, stability and combined-load provisions with the applicable material adjustments. Its connection-induced shear provisions do not furnish a blanket service-hole approval. A net-area ratio alone is insufficient.

The project's conditional reference is **US Douglas Fir-Larch No.2**, dry, unincised, normal temperature. [`lumber_leg_resistance.py`](../fea/lumber_leg_resistance.py) records reference Fb = 900 psi, Fv = 180 psi, Fc parallel = 1350 psi, Emin = 580,000 psi, with size factors for nominal 2x6 of 1.3 bending and 1.1 compression. These numbers require the matching grade/species stamp and current [NDS Supplement Table 4A](https://awc.org/resources/2024-nds-supplement/). They are not properties inferred from the owner's fir plywood. The official supplement download was inaccessible during this review; the recorded values have not been independently reverified here. Do not release procurement against an unverified substitute species group.

A useful scale check, **before adjustments and local-hole effects**, is Fb = 900 psi times the section moduli: 453.25 N·m strong-axis and 152.53 N·m weak-axis. These are nominal reference products, not allowable moments. Do not combine them with a load-duration or size increase to declare a pass. Actual capacity also depends on current wrench, support/bracing, net-section interaction and local opening behavior.

The simplest remaining calculation is a conservative current-frame free-body envelope followed by those member checks and one applicable local-opening assessment. It need not be a large FEA research program. Any numerical local-opening model must represent wood direction and a valid failure criterion; a converged isotropic von Mises peak does not establish timber capacity.

An apparently simpler shortcut—discard the front strip and design only the continuous rear 85.65 mm strip—still needs a load-transfer check. The panel screws terminate ahead of that strip, which begins at N = 54.05 mm. Loads entering the front cannot be assumed to appear in the rear strip without accounting for their transfer around the openings.

The familiar joist-boring rule is not an approval for this custom frame. For comparison only, the [published Oregon joist provisions](https://www.oregon.gov/bcd/codes-stand/Documents/st-14ossc-alladoptedamendments-compilation.pdf) require 2-inch edge clearance; the historical N = 35 mm route had only 0.628 inch at the front. The current centered N = 69.85 mm route has exactly 2 inches on each side, and its rerouting and clearance checks are recorded in the current geometry audit. This geometry change does not qualify the wall under a floor-joist rule. The [new dimensional calculation](round-structural-timber-calculation.md) supplies an actual-dimension acceptance comparison and independently verifies the 1,170 psi conditional bending reference; full member resistance remains open.

## Leg bolts: remaining finite checks

The model retains eight 3/8-inch bolts through two nominal 2x members, with complete head/washer/nut stacks. Existing directional yield calculations provide conditional lateral references, using an assumed 0.298-inch effective root diameter and 45,000 psi bending yield. They do not establish the whole connection.

The [AWC bolted-connection guidance](https://web-media.awc.org/wp-content/uploads/2021/12/17210649/StructureMag-NDS2015-PracticalSolutions-1611.pdf) identifies fastener yield, spacing/edge/end distances and local wood failure as distinct checks. There are two four-bolt groups, one per leg, with eight bolts total; the two rows within each group are not independent two-bolt joints. Finish each complete group's simultaneous shear, axial force and moment, rather than multiplying a single-bolt lateral value by four. The [current group geometry and wrench equations](round-structural-base-resolution.md#the-actual-leg-groups-and-their-minimum-calculation) preserve those distinctions. Check eccentric lap loading, row/group tear-out, splitting and the supporting member section. Do not assign clamp-friction resistance without an applicable design basis.

Axial force also needs bolt tensile strength, nut/thread engagement, washer steel bending and wood bearing. The currently specified thin SAE washer is not a qualified axial-bearing plate. For scale only, nominal OD 20.6375 mm and maximum recorded ID 10.6426 mm give 245.55 mm² annular area; multiplying by the project's 625 psi perpendicular-bearing reference gives 1.058 kN **before** washer bending, tolerances, contact loss or adjustment. This is not an allowable axial connection capacity. If current bolt tension approaches this scale, a specified plate washer is a smaller change to investigate than replacing the leg system. Its actual plate bending, edge clearance and timber bearing still need checking.

## Release conditions

Release this portion only after current-frame demands and verified stock properties establish member bending/shear/axial interaction and stability, local passage resistance, bearing-end integrity, and complete leg-group resistance. Preserve the requested 1.5-inch holes unless a specific failed check requires a revised route or local detail. Neither a hole-collision pass nor these section calculations supports a build-ready label.

## Current centered holes: what conventional detailing can simplify

The code issuer's [CodeNotes discussion](https://www.iccsafe.org/building-safety-journal/bsj-technical/codenotes-cutting-drilling-and-notching/) and its [Figure 1](https://www.iccsafe.org/wp-content/uploads/bsj/CodeNotes-Notching-2.jpg) provide the conventional sawn-lumber boring detail. The figure was inspected directly. [ICC's 2024 education handout](https://www.iccsafe.org/wp-content/uploads/Session-80-and-115-2021-IRC_Structural-Concerns-Braced-Walls.pdf#page=17), printed page 17, slide 65, attributes the beam/joist detail to 2021 IRC Figure R502.8: hole diameter no more than one-third depth, with 2-inch separation from relevant member edges, other holes and notches. The middle-third prohibition shown on the figure concerns **notches**, not round holes.

For the current centered geometry, the project's own section calculation gives:

| Centered 38.1 mm hole in 38.1 × 139.7 mm stock | Result |
|---|---:|
| Hole center N | 69.85 mm |
| Front and rear ligaments | 50.8 mm each |
| Net area | 3870.96 mm² |
| Net centroid | N = 69.85 mm |
| Strong-axis I / S | 8,480,715.297 mm⁴ / 121,413.247 mm³ |
| Strong-axis I relative to unbored stock | 97.9715% |
| Weak-axis I / S | 468,260.354 mm⁴ / 24,580.596 mm³ |
| One-third stock-depth limit | 46.5667 mm diameter |
| Nominal Fb = 900 psi × strong-axis S | 753.40 N·m, before adjustments and acceptance checks |

This alternative preserves much more strong-axis bending geometry than the N = 35 mm route. It does not restore the removed axial area or weak-axis stiffness. The hole axis must remain **through the narrow 38.1 mm thickness**, perpendicular to grain: along local S in horizontal rails and along X in center principals. The protected extreme fibers are at N = 0 and N = 139.7. Drilling front-to-back along N would be a different opening with a different resistance effect; the table would not apply.

A member inclined to the floor is still mechanically a beam when bending acts in its grain/depth plane. For the center principal that is the S–N plane, with strong bending about X. For a horizontal rail it is the X–N plane, with strong bending about S. Thus slope alone is not the reason to reject the conventional analogy. The additional axial load, weak-axis bending, torsion, concentrated connection forces and custom supports are the actions it does not independently settle. Neither the joist/beam detail nor the looser partition-stud rule establishes resistance to all those actions.

The minimum design route to consider is therefore: use the centered conventional geometry as the local detailing basis **where its conditions are accepted as applicable**, calculate the actual global beam/beam-column envelope with net properties, and check the actual fastener and bearing zones separately. A reviewing designer may be able to accept that combination without a dedicated hole stress-concentration FEA study. This review does not claim that the IRC supplies a general engineering exemption for this equipment frame. If the concentrated connection region or combined-load state falls outside the accepted analogy, only that region needs a specific further assessment.

There is **zero nominal tolerance margin**: 50.8 + 38.1 + 50.8 = 139.7 mm exactly. Undersize dressed lumber, an oversize hole, or an off-center drill reduces one clearance below 2 inches. A centered nominal drawing cannot prove both actual clearances. A release adopting this basis needs a dimensional acceptance rule or a detail with real margin. It must also check the passage-to-fastener-hole distances, actual principal bearing cut, and revised wiring path; the 161.9 mm passage-to-passage clearance alone is insufficient.

For a simplified dry-service calculation, require the specified grade/species, unincised lumber and the applicable dry-service moisture condition throughout use, ordinary temperature, verified restraint, and no unearned repetitive-member or impact-duration increase. Retain C_D = 1.0 as the provisional load-duration choice for the stated load envelope. Determine C_L/C_P from real bracing and effective lengths; setting either to one merely because panels exist is not a conservative shortcut. The short net-section calculation above is suitable input to this bounded review; it is not a released strength schedule.
