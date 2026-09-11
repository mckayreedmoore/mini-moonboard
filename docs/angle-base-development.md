# Direct base angles instead of plywood gussets

This revision replaces both `timber_base_gusset` plates and their eight bolts
with two Simpson Strong-Tie ML24Z angles. Each angle connects an outer rim's
side face directly to the horizontal header top, using six specified SDS25112
screws: three into each member. The short posts and full nominal timber bearing
remain. No plywood gusset is concealed or retained in this candidate.

The user's replacement direction is implemented as development geometry.
**The new joints and whole frame are not strength-qualified or build-ready.**
A purchased bracket's catalog values do not automatically replace the removed
gusset assembly's stiffness or resistance.

## Current package

- [Interactive model](https://mckayreedmoore.github.io/mini-moonboard/?model=angle-base-development&view=rear)
- [Open-frame render](../exports/angle-base-development/open-frame.png)
- [Outer base angle detail](../exports/angle-base-development/base-connection.png)
- [Bolt-end cutaway](../exports/angle-base-development/bolt-ends-cutaway.png)
- [STEP](../exports/angle-base-development/angle-base-development.step)
- [Wood schedule](../exports/angle-base-development/wood-parts.csv)
- [Connection schedule](../exports/angle-base-development/connections.csv)
- [Current fit audit](../fea/results/angle-base-audit-v1.json)
- [Current floor screen](../fea/results/angle-base-floor-v1.json.gz)

## Connections and machining

The angles sit on the inside faces of the outer rims, at X±1181.1 mm,
Y−135 mm and Z225 mm. Their flanges meet perpendicular side/header planes;
the bracket is not forced against an inclined face. Exact hole axes and
directions are supplied by the current connection schedule and STEP.

The model retains all 151 panel/kicker screw axes from the infill candidate
and all eight leg bolts. Twelve angle screws replace the eight removed gusset
bolts. Existing header-to-post brackets remain; the new angles do not pretend
to be a rigid connection between rim and post.

This is a fresh-build machining model. Former gusset-bolt locations remain
solid where no current hardware requires a hole. It is not a repair procedure
for timber already drilled for the old gussets; no hole filling or restored
strength of previously drilled stock is assumed.

Inventory is 32 wood/plywood parts, 36 angles, 216 angle screws, 151 panel/kicker
screws and eight complete leg bolts. Five selectable meshes per bolt give
475 viewer entries. Both the viewer and this revision's CAD renders show
ordinary bolts in steel gray. An explicit clearance-failure flag remains red
in the viewer; color is not a strength-test result. Heads, nuts and both washers
are modeled and separately selectable.

## Load path and limits

The old direct fastened path was outer rim → gusset → outer post. The new path
is outer rim → ML24Z → header → existing header/post connection. Timber bearing
can carry compression, but it does not supply arbitrary tension or frictional
shear. The legs still connect to the outer rims through their retained bolts.

Applicable bracket directions, simultaneous loads, rim/header bearing,
cross-grain stresses, screw resistance, slip, uplift and whole-frame racking
remain to be checked using current forces. Do not sum catalog capacities,
assume rigid angles or credit an unverified plywood diaphragm. The
[manufacturer ML product information](https://www.strongtie.com/decks_decksandfences/ml_angle/p/ml)
and [recorded reference](ml24z-reference.json) define the selected product;
neither is an analysis of this climbing frame.

The separate [panel-spacing diagnostic](infill-panel-development.md) uses the
same face panels and panel screw axes. The angle-base audit checks that exact
panel geometry and connection equivalence. This supports reuse only of the
stated independent, ideally restrained panel problem. Changing the base joint
can change real framing compliance and panel loads, so no whole-frame forces,
gusset resistance or actual panel acceptance transfers.

The current floor screen must use this candidate's own drilled bodies and
complete hardware mass. Floor/foot materials remain unknown. Rigid equilibrium
with assumed friction is not an actual-floor or structural qualification.

## Recorded checks

The current fit audit passes all tested geometry and product-fit gates, including
receiver engagement, hardware collisions, complete bolt stacks, removal of the
eight obsolete gusset bores, and 151 nominal future-insert reserves. Those reserves
do not qualify an insert product or its resistance.

Current calculated mass is 192.660 kg under the recorded density assumptions.
Of 1,296 rigid floor cases at each assumed friction coefficient, all are feasible
at 0.2 and 0.4. At 0.1, 650 are feasible and 646 fail the polygon screen; 504 of
those failures also violate an analytic circular-friction bound. The remaining
142 are polygon-screen failures without that stronger proof. These are assumed
floor cases, not a measured coefficient or a frame strength result.

The unchanged independent panel diagnostic remains a build-readiness blocker.
Its fine-mesh F3 ideal tension scales to 1,725.586 N for the stated 250 lb case,
versus a conditional unadjusted screw-withdrawal reference of 733.601 N. The
controlling reaction passes refinement, but other individual reactions in six
hold cases do not, so overall reaction acceptance remains false. These forces
are not verified physical joint demands. See the [panel diagnostic](infill-panel-development.md)
for the model limits and conditional product applicability.

The next connection revision should investigate a load-spreading panel attachment
with qualified panel bearing, plate bending and timber fastening, then resolve
current base-angle forces and whole-frame compliance. Simply enlarging screws or
replacing gussets does not establish an adequate climbing frame.

Verification includes 19 focused model, full-fit and artifact tests across the
new revisions and preserved hardware exports. The browser check loaded all
475 current meshes, selected complete bolt hardware, verified newest-first
menu ordering, and retained red precedence for explicit clearance failures.
Independent correctness, testing and consistency reviews found no remaining
substantive implementation defects after the solver-provenance guard was fixed.
These software checks do not release the design for construction.
