# Structural screws and larger 2x6 passages

The owner selected structural panel screws for the current build, with future
insert space retained. `round-structural-development` preserves both aligned
service-rail rows (1134.2 and 1278.25 mm along the slope), all fixed upper
principal/rim screws, and the 60/140 mm kicker rows. The 56 attachments remain
exactly mirrored. Interior rail-screw columns use absolute X positions 435.075
and 835.075 mm: each shifts 11.6417 mm away from their former midpoint, giving
a 400 mm middle gap and equal 365.075 mm end gaps. Row heights, outer/center
principal screws and upper center screw #4 stay fixed. The change prevents
three original 2-inch screw tips from entering the enlarged LED passages. Historical screw and insert candidates remain separate.

LED routing holes increase from 25.4 to 38.1 mm in nominal 2x6 members only.
Other members retain their 25.4 mm passages. The actual stock cross-section,
not a name prefix, determines which holes enlarge. Panel LED and hold holes
retain their own diameters. Larger holes improve geometric feeding space but
remove more timber; previous member-strength results do not transfer.

## Centered-passage revision and evidence status

The current routing revision moves nominal 2x6 passage centers to **local
N = 69.85 mm**, centered in their 139.7 mm depth. A 38.1 mm passage then leaves
**50.8 mm nominal front and rear ligaments**. Its axis still traverses the
narrow 38.1 mm stock thickness: local S through horizontal rails and X through
center principals. This preserves more strong-axis section geometry than the
previous N = 35 mm route, but it does not restore the removed axial area or
weak-axis stiffness.

There is **zero nominal tolerance margin** for a two-inch edge-clearance basis:
50.8 + 38.1 + 50.8 = 139.7 mm exactly. Actual stock depth, bit diameter and
centering require a dimensional acceptance rule. Conventional joist detailing
is a comparison, not automatic structural approval of this custom frame.
See the [timber review](round-structural-timber-review.md#centered-hole-alternative-what-conventional-detailing-can-simplify).

The centered wiring implementation passes the regenerated
[geometry audit](../fea/results/round-structural-audit-v1.json), including its
SPAX product-geometry gates. All 200 screw tips remain contained in net timber,
all 56 future insert reserves fit, and the tested hardware and electrical
envelopes have no collision failures. All 131 modeled cable routes fit the
304.8 mm nominal spacing budget; the smallest modeled margin is 23.206 mm.
These checks use nominal geometry and provisional harness envelopes, not
manufacturing tolerances or structural capacities. The [build draft](round-structural-build-plan.md)
and [drilling PDF](round-structural-drilling/drilling.pdf) accompany this revision.

The [native structural runner](../fea/round_structural_frame.py) has focused
adapter/provenance tests, but full mesh preparation and native solves remain
unrun. Its retained rear-prism stiffness surrogate discards the intact front
ligament and is not a conservative response bound. Historical ordinary-screw and insert
withdrawal, bracket and member demands do not qualify the revised candidate.
Output recovery now includes CalculiX binary32 conversion before decimal
rounding, replacing an arbitrary tolerance multiplier. Existing archived
reports retain their original recovery metadata; reprocess and authenticate
their reports before relying on them with the revised recovery code.

## Focused reviews and finite release tasks

| Review | What is established | What still closes the release gate |
| --- | --- | --- |
| [Panel fasteners](round-structural-fastener-review.md) | Selected SPAX product, T20 drive, installation basis and conditional individual references | Current signed axial/lateral demands with panel contact; applicable DF-L and plywood resistance, adjustments and combined action; all face and kicker attachments |
| [Base and legs](round-structural-base-review.md) | Actual mounting and unsupported load-direction questions identified | Applicable rated ML24Z detail or a specific calculated replacement; matching simultaneous base/leg demands, bearing, splitting and fastener-group checks |
| [Timber and passages](round-structural-timber-review.md) | Net-section implications and centered-hole detailing comparison | Accepted dimensional tolerances, current global beam/beam-column envelope, bearing and concentrated connection-zone checks |

These reviews narrow the work; they do not release construction. A manufacturer
applicability decision or a defensible calculated connection detail can resolve
the base question without an invented experimental program. Current demands
and compatible adjusted capacities remain necessary even when conventional
member calculations replace additional local FEA.

## Minimum remaining work and further simplification

- Keep the current geometry and fastening pattern; no screw-count or symmetry
  optimization is needed for the next decision.
- Use one specified panel screw and one manufacturer-required bracket screw;
  avoid bespoke insert machining in this build.
- Keep future inserts optional. A clearance reserve is not a promise that a
  particular insert can safely retrofit a worn screw hole.
- Do not require floor measurements or physical floor tests. Record one intended
  installation and explicit analytical stability assumptions, rather than
  claiming measured friction or universal hardwood/carpet/mat acceptance.
- Replace the extensive simulation research program with a focused structural
  assessment where conservative calculations and applicable published ratings
  are sufficient. Resolve unsupported bracket load directions, leg/base load
  transfer, panel fastening and local sections around enlarged passages.
- Use a representative LED feeding check with the actual intact kit instead of
  more detailed cable simulation. The feed arrangement remains part of assembly.

**Not released for construction or climbing.** No floor-strength, frame-strength
or climbing approval follows from geometry
or from removing measurement tasks from the scope. New load/connection evidence
must match this screw-based candidate rather than the preserved insert model.
