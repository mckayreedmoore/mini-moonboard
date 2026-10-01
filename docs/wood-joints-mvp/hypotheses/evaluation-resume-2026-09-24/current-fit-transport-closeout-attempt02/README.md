# Current fit, service, and transport closeout — attempt02

**Status:** source-bound operation review; no installation, reversible removal,
service, or full-member transport operation is cleared. Geometry and hardware
selection are unchanged. This note consolidates the current fit and motion
evidence; it does not repeat the CAD calculations.

The reviewed geometry revision is
`led-clearance-2x6-runner-seated-blocks-v1`. The pinned attempt04 full-frame
input manifest contains 20 source timbers, 24 separate candidate block bodies,
and six panel identities. It carries 92 candidate bolt axes, 12 retained frame
bolt axes, and 66 panel/kicker screw axes. The
[machine-readable evidence register](evidence-register.json) stores the exact
three ID arrays and a per-axis status row for all 170 fastener operations.
Every row hashes its exact manifest record and its matching operation-coverage
record; candidate and retained rows also link their axis-specific CAD screen.
Those arrays establish inventory identity only. CAD envelope findings remain
diagnostic, while delivered fit, actual tool access, installation/removal,
support/capture, and integrated transport remain unresolved for every row.
Run
`python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-fit-transport-closeout-attempt02/prepare.py --check`
from the repository root to verify the pinned input hashes, ID joins, and
generated register.
Primary inputs are the [92-axis exact-component report](../access-screen-attempt03-exact-components.json),
[12-axis retained-bolt report](../retained-access-attempt03/access.json),
[focused tool-route findings](../step6-operation-coverage-attempt01/tool-route-feasibility-attempt01/tool-route-feasibility.json),
and [attempt04 member-export review](../current-retained-bolt-access-attempt01/parent-export-attempt04/independent-review.md).

## The six nut and washer slide hits

The latest exact-component report finds six solid intersections on four of 92
candidate axes. Two center-block axes hit both the nut and nut washer; two
outer-block axes hit the nut only. The exact IDs, blocker IDs, and intersection
volumes are in the register. These are exact sweeps of the supplied CAD BReps,
not measured delivered hardware.

The [captured-nut motion probe](../captured-nut-motion-attempt02/motion.json)
provides one local geometric escape per affected axis: after assumed in-place
unthreading, capture, and head-side bolt withdrawal (151.368 mm including its
diagnostic 1 mm terminal allowance), move the captured nut/washer laterally
past the blocker and then 25 mm along the declared nutward direction. All four
local CAD routes have no reported external-scene intersection. Lateral moves
are axis-specific and recorded in the register. This means the direct axial
slide hits do not by themselves prove physical impossibility.

That alternate path still ends only at a local 25 mm segment, not a reachable
hand-held or restrained staging location. The probe assumes thread-compatible
unthreading and unchanged coaxial shaft/boreless-nut display overlap; it does
not model thread release, actual wrench/counterhold, capture, support transfer,
tool/hand clearance, tolerance, full extraction, or reverse installation. The
other proposed bypass—removing the four adjacent blocker blocks first—has no
screened block-fastener access, body extraction, support, or replacement
sequence. Thus the six geometric hits are **locally bypassable in the CAD
diagnostic, but remain unresolved as reversible operations**.

The available 7/16 in FACOM wrench and 7/16/3/4 in Wera profiles are published
manufacturer profile comparators, not selected tools or fit results. Current
hardware records do not select the 92 candidate bolt/nut/washer products or
provide their delivered dimensions. The 1/4-20 class-pair travel note is an
ideal conditional comparator, not proof of active full-thread engagement at
these axes. No torque or counterhold procedure is established.
See the [current hardware schedule](../../../current-hardware-schedule.md),
[conditional thread-fit note](../../../current-thread-fit-travel.md), and
[nut/washer property boundary](../../../current-ordinary-nut-washer-property-basis.md).

## The four retained leg-bolt / wire conflicts

The retained-access screen reports 12 modeled sweep intersections across four
`lumber_leg_bolt_{left,right}_{1,2}` stacks. The left pair intersects modeled
span `wire_010_A10_A11`; the right pair intersects `wire_130_K10_K11`. Each
head, head washer, and shaft sweep intersects its corresponding modeled wire.
The per-stack volumes are in the register. These fixed-wire solid intersections
do **not** prove that a real flexible cable blocks withdrawal, nor do they
establish physical cable clearance.

The retained-wire note describes a candidate state that stages string 1 and
the installed portion of string 3 while retaining string 2. It would need
reversible service at the existing `wire_050_E2_E3` and `wire_100_I4_I5`
boundaries and reconciliation of the PWR1 branch and third-string unused
tail. The [retained-wire note](../../../current-retained-wire-sequence.md) also
records a modeled 18-LED unused tail where the manufacturer material describes
16 spare LEDs; reconcile that inventory before assigning a staging state. The
wiring model has no clips, strain reliefs, slack, or bend behavior;
the manufacturer installation material does not document reversible
whole-string removal. Do not suppress these spans from a clearance model or
cut/splice them to manufacture a pass. Until the actual kit, boundary parts,
PWR1 route, attachments, and documented reversible service method are bound,
keep all four retained-stack removals and reverse insertions unresolved.

The four leg bolts are the retained 1/2-13 catalog-reference group. Its current
CAD access proxy is 7/16 in, while the catalog-reference hex is 3/4 in across
flats; the larger correct-size tool has no access or simultaneous-counterhold
screen. Product references do not identify delivered stock. The other eight
retained stacks are not cleared by the absence of this wire hit: their current
component sweeps still assume disengaged threads, and all twelve lack a
selected matched product, complete tool/counterhold operation, capture, and
integrated reversible sequence.

## Individual member and transport coverage

The existing source-pinned motion studies cover only six of the 20 source
timbers, and none supplies a stable staging or supported transport operation:

| Members | Bounded modeled movement | Dependency and limit |
| --- | --- | --- |
| `lumber_leg_left`, `lumber_leg_right` | Straight outward translations of 62.468 mm, respectively −X and +X, with no reported solid overlap above the report threshold. | Each case assumes its four retained frame-bolt stacks, all 92 candidate stacks/bodies, panels and 66 panel screws, holds/T-nuts, and lights are already removed. Modeled wires and other retained roles remain. No positive clearance margin, support, or stable destination is established. |
| `base_post_center_left`, `base_post_center_right` | Straight +Y translations of 140.7 mm; each endpoint has a 1 mm axial BBox gap to `base_header`, with a clear modeled conservative envelope. | Assumes the matching two candidate post axes and the associated kicker/panel screw state are already removed, plus the other declared candidate/panel/service removals. No support or staging is established. |
| `base_floor_left`, `base_floor_right` | 1.0 mm outward separation from the already-butting rail positions. | Minimal separation only, not extraction. Cases assume the associated leg movement and retained front/rear rail-bolt removals. No stable staging is established. |

The other 14 source timbers have no individual movement screen in this bundle.
The 24 candidate block bodies have no integrated insertion/extraction screen;
the four blocks that obstruct nut slides have not been screened as removable
blockers. None of the six panel identities has a current-revision complete
lift/withdrawal-and-return path. The 66 screw axes remain a separate count
(58 unchanged and eight owner-directed moves); axis identity is not proof of
driver access or reversible screw operation. Holds/T-nuts move with panels in
the modeled inventory, while lights/wires are separate service entities.

The D6 BRep bundle contains 20 source timber solids, 60 retained-bolt component
roles, and 131 modeled wire solids. Its post-removal scene assumes the candidate
blocks/stacks, panels/66 screws, holds/T-nuts, and lights are already gone;
the wires stay stationary. Temporary supports and staging surfaces are absent.
It is an input to bounded movement screens, not an all-member route. Preserve
the 20 source timber IDs, 24 block IDs, six panel IDs, all 12 retained bolt
stacks, all 92 candidate stacks, and 66 panel-screw operations as individually
reconciled items in any future operation log. All 170 operation IDs, their
manifest record hashes, and source-reported operation statuses are in the
evidence register. This records which axes and modeled operation screens were
reviewed; it does not clear an operation. Physical fit, tool access, reversible
installation/removal, support, and transport remain unresolved.

## Bounded sequence hypothesis and stop points

The current sequence in
[`transport-operations.md`](../../../transport-operations.md) remains a
hypothesis. A defensible analysis order is:

1. Bind actual candidate and retained fastener identities, delivered thread and
   washer dimensions, and the selected turning/counterhold tools. Define the
   actual wire kit, connector boundaries, PWR1 branch, attachments, slack and
   reversible service instructions.
2. Define supported frame and panel states and named capture/staging locations
   before releasing any connector, panel, retained bolt, or timber member.
3. Screen the four candidate-stack alternatives with selected parts and tools:
   either complete the captured local nut/washer path and its reverse to a
   real staging point, or screen the blocker-removal alternative and its
   reverse. Do not count the current 25 mm local continuation as extraction.
4. If a documented reversible harness state exists, screen both withdrawal
   and reverse insertion of the four retained leg stacks in that state while
   retaining all other physical service parts. Otherwise, stop those four
   operations as unresolved.
5. Build one integrated, dependency-ordered state graph for the 20 source
   timbers, 24 block bodies, six panels, all 104 bolt stacks, and 66 distinct
   panel/kicker screw operations. Include support transfer and stable staging
   for every detached part; do not infer movement for the unscreened members.

For eventual assembly, the high-level hypothesis is frame and retained bolts,
then candidate blocks/stacks, then panels and their 66 screws, then lighting
service. Reverse transport begins with support and service capture, then
lighting/panels, candidate stacks and blocks, retained bolts, and individual
timbers. No within-family order is selected here. No step authorizes physical
assembly, disassembly, cutting, hardware selection, or climbing use.

## Missing source needed to execute the next check

The next executable analysis is a source-bound, current-revision staged access
check—not a geometry change. It requires, without purchasing or assuming a
product: (a) actual candidate and retained bolt/nut/washer item and lot
identities, dimensioned product records or measured delivered dimensions,
including first/last full threads, runout, nut active-thread/chamfer, and
washer ID/OD/thickness; (b) the selected tool profiles for both sides and the
installation/removal procedure; and (c) the actual lighting-kit/connector/PWR1
parts and instructions for reversible whole-string service, with attachment,
slack, bend, and restraint data. Re-run only the affected local paths plus
their reverse paths using those bound parts and complete staged obstacles.
After those operations are evidenced, close the integrated all-member support,
movement, capture, and staging graph. Until then, the exact remaining limits
and source pins are the T07 disposition.
