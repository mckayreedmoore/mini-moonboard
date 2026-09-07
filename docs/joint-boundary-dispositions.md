# Joint boundary dispositions: all current frame connections

This is a finite review inventory for **top-joint-development**, not a claim
that all margins have been measured or accepted. It covers the 278 frame
connections in the [exported schedule](../exports/top-joint-development/top-joint-development_connections.csv).
Holds, insert retainers and electrical mounting hardware are separate inventories
in [hardware-fit dispositions](hardware-fit-dispositions.md). **No construction
or capacity approval follows from this table.**

## Connection-family inventory

Anchored regular expressions classify the current exported names, not future
names or permissible new geometry. Each current connection must match exactly
one row; counts total 278. Word-token wildcards do not authorize substitutions.

| Family | Count | Anchored ID regex |
| --- | ---: | --- |
| panel | 64 | `^panel_[1-9][0-9]?$` |
| kicker | 16 | `^kicker_[a-z]+_[a-z]+_[0-3]$` |
| edge | 12 | `^analysis_edge_screw_[a-z]+_[1-6]$` |
| ribfront | 12 | `^rib_[1-3]_[a-z]+_[a-z]+_front$` |
| cheeksplice | 8 | `^cheek_splice_[a-z]+_[1-4]$` |
| legwall | 8 | `^analysis_leg_wall_bolt_[a-z]+_[1-4]$` |
| stitch | 6 | `^leg_stitch_[a-z]+_[1-3]$` |
| topcrossangle | 32 | `^angle_[a-z]+_[a-z]+(?:_[1-3])?_[a-z]+_[1-2]$` |
| ribangle | 48 | `^angle_rib_[1-3]_[a-z]+_[a-z]+_[a-z]+_[1-2]$` |
| transitionbolt | 20 | `^transition_[a-z]+(?:_bottom)?_[a-z]+_bolt_[1-2]$` |
| transitionscrew | 20 | `^transition_[a-z]+(?:_bottom)?_[a-z]+_screw_[1-2]$` |
| clip | 32 | `^clip_[a-z]+_[a-z]+_[a-z]+_[a-z]+_[1-2]$` |

## Evidence shared by the families

The current [top-joint audit](top-joint-development.md) records nominal
solid-clearance, receiving-bore, reserved-service and minimum washer-annulus
checks. The 24 retained tool obstructions are access dependencies, not an
approved erection sequence. None establishes timber or steel edge resistance.

The [axial report](top-joint-engagement.json) covers all 114 bolts and 164 screws:
catalog-stack bolt projections exclude measured grip tolerances; screw-tail
overlap includes the point and only centerline material. It does not establish
effective embedment, screw-head bearing or full-circumference thread support.
The [plywood profile report](top-joint-ply-profiles.json) covers only eight
independent leg/splice prisms and their 60 incident bore positions, excluding
head seats. Do not transfer that coverage to other members.

| Family | Involved member roles | Recorded geometry / remaining disposition |
| --- | --- | --- |
| panel | Main face skins to perimeter/seam/mid backing | Fixed hold/LED axes, receiving paths and nominal axial overlap checked. Finish face-edge, neighboring relief and real R4 head-seat deductions; reconcile measured purchased thickness and strength axis. |
| kicker | Kicker skins to top/bottom battens | Grid, receiving paths and nominal axial overlap checked. Finish skin/batten edge and relief margins plus actual flush-seat detail; verify stock and hold hardware at this interface. |
| edge | Side rims to horizontal panel rails | Nominal shaft/head clearance and axial overlap recorded. Four tools are blocked by legs: install before legs. Measure net wood edges/end distances and nearby bores/reliefs under the selected GRK detail; resolve actual driver/seat and load direction. |
| ribfront | Front backing battens to solid ribs | Axial material recorded; twelve tools require skins absent. Finish batten/rib net edge and relief checks and real head seats. Confirm remanufactured rib grade and grain direction; no glued-rib substitute or unqualified withdrawal credit. |
| cheeksplice | Through both plywood splice plies into the side rim or kicker cheek | Exact splice profile and neighboring circular-bore ligaments recorded; axial overlap is in the final receiver, not the clearance plies. Finalize head-seat deductions, receiver net boundaries, delivered ply thickness/strength direction and joint resistance; no adhesive/friction load-sharing credit. |
| legwall | Timber side rims to both independent leg plies | Leg-side profiles and neighboring bores recorded; minimum washer-annulus fit and nominal bolt stack checked. Finish rim-side net boundaries and mixed load classification; assess each ply and threaded bearing planes independently. |
| stitch | Independent inner/outer leg plies | Exact leg outline and neighboring bores plus nominal bolt/washer geometry recorded. Determine load allocation, grain-dependent resistance and tightening/inspection practice without composite or clamp-friction credit. |
| topcrossangle | Custom angles joining side rims to top cap/rear crossmembers | Nominal bores, hardware and washer-annulus fit checked. Finish both wood-member and steel-leaf edge/spacing/net-section measurements, bend/weld geometry and threaded bearing review. Select fabrication/material basis; this is not the revised perimeter top-angle family. |
| ribangle | Custom angles joining solid ribs to rear crossmembers | Nominal bores, hardware and washer-annulus fit checked. Finish rib, beam and steel boundaries including nearby holes and reliefs; confirm rib grain/grade and custom steel fabrication before assigning resistance. |
| transitionbolt | Custom perimeter angles to rims or two-ply cheek splices | Revised top-rim end distances are 110.4/70.4 mm with 40 mm spacing; steel extension remains unqualified. Splice profiles expose a **14.0671 mm minimum kicker-bolt center-to-outline distance**, only 8.5108 mm clear ligament: explicitly unresolved, not an approved plywood edge distance. Review this local detail and all remaining rim/steel boundaries, plus two-ply load allocation and extended-leaf bending/prying. |
| transitionscrew | Custom 6 mm steel angles to horizontal main/kicker rails | Project Ø7 steel bores and SDS axial tails checked; points included. Finish steel lands/edges, receiver edges/reliefs and actual SDS head/tool fit. Select fabrication tolerances and qualify the thick-steel joint separately; no US A21 approval transfers. |
| clip | Eight mid-batten clips joining battens and horizontal rails | Nominal proxy-body/hardware clearance and screw axial material checked. Resolve **US A21 versus UK hole/bend proxy**, delivered SD fit and manufacturer arrangement first; then finalize member edge/spacing/relief deductions. Do not alter purchased clip holes or assume a direction-independent catalog rating. |

## Finite handoff decisions

1. Resolve the short kicker/splice boundary and extended top steel detail with
   the reviewer; retain the current geometry/evidence until a named revision is
   justified. A positive ligament is not sufficient resistance.
2. Complete the remaining timber/steel boundary dimensions and real head-seat
   deductions identified above; preserve explicit unknown load/grain categories.
3. Close the [product-fit checklist](hardware-fit-dispositions.md), then review
   connection resistance and unanchored stability using qualified demand data.
   Rejected FEA force recovery cannot supply those demands.

This classifies all frame connections for review; it does **not** complete their
dimensional, installation or structural acceptance.
