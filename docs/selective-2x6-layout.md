# Selective single-stock revision of the 2×6 baseline

This revision addresses the two measured failures in the preserved
[all-2×6 baseline](single-2x6-layout.md): incomplete base bearing and narrow
shared panel-seam fastening. No lumber is paired, laminated or stacked.

[Open the current interactive model](https://mckayreedmoore.github.io/mini-moonboard/?model=selective-2x6-development&view=rear).
[STEP](../exports/selective-2x6-development/selective-2x6.step),
[wood schedule](../exports/selective-2x6-development/wood-parts.csv),
[connections](../exports/selective-2x6-development/connections.csv),
[fit audit](../exports/selective-2x6-development/geometry-audit.json), and
[floor screen](../fea/results/selective-floor-v1.json.gz).

![Selective single-stock frame](../exports/selective-2x6-development/open-frame.png)

## Changes and reasons

| Members | New single stock | Reason |
| --- | --- | --- |
| Center principal, center post, two middle rails | Four 3×6 members, modeled 63.5 ×139.7 mm | Wider fastening face at shared panel joints |
| Flat base header | One 2×10, modeled 38.1 ×234.95 mm | Full nominal coverage of the three sloped-member bearing faces |
| Outer rims, rear legs, top rail, bottom rails, outer posts | Nine 2×6 members | Retained pending resistance analysis |

There is still only one center principal/post and one middle rail per bay.
Eight plywood panels/gussets, 56 panel/kicker screws, 16 bolts, 14 brackets and
84 manufacturer-specified bracket screws remain. No inserts or insert pilots
are installed. Bottom rails remain square-cut and pocket-free; the middle
rails and principal retain hold/LED service pockets. No lower principal housing
is introduced. The outer rims, rear legs and their floor locations are unchanged.

Dry dressed section assumptions follow [NIST PS 20-25, Table 3](https://www.nist.gov/document/ps-20-25-final),
using the imperial dimensions converted exactly to millimeters. A
[nominal 3×6×10 ft Douglas-fir product](https://www.homedepot.com/p/328236044)
is listed, but local availability, actual dry dimensions, moisture and grade
remain procurement checks. This is not a selected or qualified lumber purchase.
Green lumber dimensions differ. The
[source record](selective-stock-reference.json) preserves those distinctions.

Turning a 2×6 flat was rejected for this revision. At equal material, span and
load, gross frame-normal bending inertia would become only
(38.1/139.7)² = 7.44% of the on-edge section, before service cuts. Existing
45 mm service-pocket depth also exceeds the flat member's 38.1 mm depth, and
retained bracket placement would no longer fit. Keeping the load-path depth
and selectively widening a single solid receiver is the simpler fit change.

## Fit analysis

All tested fit gates pass for this candidate, including actual receiver material,
wood overlap, hardware clearance, touching parallel lumber, lower-rail and
changed-framing service clearance, rim/leg bolt edge screens and all 56 nominal
future insert reservations. These are geometric results, not resistance checks.

The 28 shared-seam screws now have a minimum 15.875 mm nominal edge margin,
exceeding the retained preliminary 10.3505 mm screen. Nominal side ligament
beside the 12.1412 mm future insert reservation increases from 3.4544 to
9.8044 mm. This measures ligament to the straight stock side, not the minimum
clearance to every service pocket; reservations fit nominally but pocket and
damaged-wood effects remain unqualified. Screw positions and bracket origins are regenerated around the
wider members; this is not a retrofit drilling pattern.

All three sloped members now have full nominal bearing coverage, as do the
three posts beneath the header. The retained front datum requires a footprint
reaching about 187.86 mm behind it. A 2×8's 184.15 mm depth would still be short;
the 234.95 mm header covers it. The wider header extends 95.25 mm behind the
posts. Its transverse load distribution, bending and local bearing stresses
still require analysis; coverage alone does not establish a load path's strength.

## Remaining work

- Resolve strength and deflection using actual species, grade, moisture,
  panel properties and exact fastener products. Include service-pocket net
  sections, connections, header overhang, leg buckling and racking.
- Retain the unresolved 40 mm lower-panel overhang in the next panel check.
- Establish real floor friction and stability requirements before choosing
  feet, pads, anchorage or ballast; none is installed by this revision.
- Keep insert repairs provisional. The larger solid reservation does not
  qualify worn or damaged wood, insert pull-out, countersinks or repeated repair.

This revision closes the measured fit defects. It is not a completed native
connection/contact analysis or build-ready MoonBoard plan.

## Current-candidate floor screen

The rigid floor screen uses this candidate's drilled CAD and fused fastener
component volumes, rather than inheriting the previous frame's mass. Assumed
wood/plywood density is 600 kg/m³; modeled steel uses 7850 kg/m³. Estimated
included mass is 161.414 kg. Holds, lights and wiring are omitted; this is not a
measured assembly mass or a specified lumber density.

| Assumed floor friction μ | Feasible cases | Polygon-infeasible cases |
| --- | ---: | ---: |
| 0.1 | 508 | 788 |
| 0.2 | 1,296 | 0 |
| 0.4 | 1,296 | 0 |

The 1,296 finite cases combine 150/200/250/300 lb climbers, 1×/2× vertical
load, 80/100% included mass at fixed center of gravity, nine selected holds at
100 mm outward standoff, and zero or 300 N horizontal load in eight directions.
The model assumes a rigid assembly, level floor and compression-only reactions.
Its 16-direction friction approximation lies inside the circular Coulomb cone:
polygon infeasibility alone does not prove circular-cone failure. Feasible
results have independent force, moment, friction and nonnegative-normal checks.
Maximum feasible-witness residuals were below 6e-12 N and 8e-9 N·mm.

These are equilibrium witnesses, not predicted contact pressures or joint
forces. They do not establish elastic response, connector strength, stability
under every hold/load direction, uneven-floor behavior or dynamic safety.
Friction coefficients are assumptions, not measurements. Do not interpret μ=0.2
as a specified safe foot material or a measured minimum. The next stability task
is to establish the actual floor interface and load envelope; the next strength
task remains analysis of the real connections and service-pocketed members.

## Verification and CI limits

Twenty targeted tests passed in 41.40 seconds, covering the new fit gates,
source/artifact integrity, independent floor equilibrium replay, current mass
accounting and retained historical variants. Separate complete hardware/wood
and hardware/hardware collision checks passed.

The preceding commit's [full CI run](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/34432437560)
reported 2,256 passed, 13 skipped and eight failures in historical exact numeric
or deck-text replay comparisons. Inspected differences were in final floating
point digits, and archived source hashes passed. Those unrelated portability
failures are not repaired by this design revision; full repository CI is not
claimed green.

The selector regression also passed. Browser checks loaded all 192 current
entries, exercised the new default and navigation, selected the center member,
verified grid placement and captured desktop/mobile views without request or
browser errors. Independent source review found no remaining substantive issues;
obsolete inherited member descriptions were corrected before final export.
Ruff and diff checks passed.
