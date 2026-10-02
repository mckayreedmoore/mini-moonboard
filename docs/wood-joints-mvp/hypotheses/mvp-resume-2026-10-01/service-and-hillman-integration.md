# Service-joint and Hillman evidence integrated

The owner directed ingesting the service-joint worker's left-joint work and
the previous Hillman work on October 1, 2026. The parent has read the latest
worksheets, joined their saved receipts, and checked 203 distinct source
files against their recorded SHA-256 bindings. The
[ingestion record](service-and-hillman-ingestion.json) preserves those
bindings and the decision inputs. No worker file was changed or study rerun.

The practical development decisions are to retain the left service geometry,
include the plywood/screw path in the right-corner calculation, and leave
stronger hardware unselected while the complete joint is resolved. These
decisions do not adopt complete-joint acceptance or change the reviewed scene.

## Left service joint

Use the worker's latest
[coupled frame-clearance worksheet](../upper-left-service-frame-clearance-2026-10-01/README.md).
The joint is `left_service_outer_upper_cleat`, duty
`clip_horizontal_upper_left_1`, between `base_rail_service_upper_left` and
`base_side_left`. Retain its 88.9 × 88.9 × 119.7 mm cleat, four quarter-inch
bolts and 33 mm pitches for development.

The worker calculated 252 states: three recorded rear cases, seven saved
increments, three clearance choices and four lateral stiffness choices.
Its load scale is twice the recorded proportional gravity-plus-climber load.
At the frozen lateral stiffness:

| Relative clearance | Peak bolt shear | Peak bolt tension | Peak local rail/side movement | Peak local rotation |
| --- | ---: | ---: | ---: | ---: |
| 0 mm | 67.616 N | 114.420 N | 0.0943 mm | 0.0567° |
| 0.50 mm | 12.513 N | 10.871 N | 0.5560 mm | 0.0891° |
| 1.15 mm | 9.376 N | 12.814 N | 0.5575 mm | 0.1054° |

Peaks in a row need not be simultaneous. These coupled results supersede
using the earlier independent-interface motion estimates to decide whether
the geometry needs changing. The recorded 1 mm / 0.5° targets remain
provisional development comparisons, not adopted limits or a joint rating.

The worker's saved-vector audit checks laws, compatibility, equilibrium,
floor signs, world-port moments and force-bearing rigid rank 300 in all
252 states. Exact response-vector replay matched; report differences were
limited to last-bit condition estimates. This ingestion checks the saved
bindings; it does not launch another review or software test round.

The worksheet retains conditional Hillman springs, zero clearance at other
bolted joints, source floor masks and an explicit zero-force extension at open
contacts beyond the negative table endpoint. It covers three cases and does
not close finished timber resistance, splitting, washer/bolt interactions,
installation/removal, or complete-joint acceptance. The joint remains HOLD.

## Previous Hillman work reused

The [receiver-transfer packet](../current-panel-receiver-transfer-2026-10-01/README.md)
supplies all 66 current receiver/station identities: 58 unchanged and eight
previously directed moves. Its three-case, seven-increment join preserves
1,386 simultaneous screw states and 4,158 scalar components, including both
lateral directions and axial withdrawal. The physical-body endpoint mapping
has no force or moment refusals. Preserve the separate refused mapping that
continued through support elimination; it is not a receiver-load result.

These station/receiver identities match the current model exactly. Both the
original and isolated corrected parent frames retain all 132 lateral screw
components and 66 tension-only screw components. Therefore the earlier bolt
demands already included a conditional panel path; the new calculation makes
its redistribution with bolt clearance explicit.

The upper-right panel has twelve screws: four into the center principal,
two into the top rail, four into the right side and two into the service rail.
The six top-rail/side screws directly link those two corner hosts through
the plywood. The remaining connections also participate through the frame.
Do not add an independent screw capacity to bolt resistance after the frame
has already distributed the same actions through those screws.

Retain the purchased Hillman 42605 and owner pilot/countersink policy. The
[product applicability note](../current-panel-receiver-transfer-2026-10-01/hillman-applicability.md)
and earlier public-source search supply no adopted product strength or
axial load-slip law. Continue the simpler MVP with explicit conditional
panel assumptions, as directed in the revised goal, and retain those formal
qualification gaps. No SPAX/SDS property is transferred.

The worker's suggested zero-withdrawal screen is already addressed by the
parent's preserved [six-case result](no-withdrawal-frame-checks.md): all six
stop on missing upper-panel normal restraint. The earlier
[both-upper-panel equilibrium bounds](../mvp-acceleration-2026-09-28/panel-screw-group-total-withdrawal-attempt03/README.md)
also establish necessary aggregate withdrawal forces. Those totals are not
individual screw allocations or capacities. They support retaining an
explicit axial path in the working model, rather than repeating its omission.

## Right corner: coupled six-case results

The parent reused the worker's four-disk clearance projection and branch
equations in [right_corner_clearance.py](right_corner_clearance.py), with the
parent's independent six full static scenarios and lumped no-slip floor
assumption. It calculated twelve states for each of two geometries: zero
clearance and the modeled clearance, across all six cases. All 24 meet body
equilibrium, normal and circular-gap laws, floor laws and force-bearing
rigid rank 300. All 66 Hillman axes remain active in the model.

| Analysis geometry / fit scenario | Peak corner bolt shear | Peak tension | Peak local rail/side movement | Peak local rotation | Largest individual lateral ratio, conditional Fyb = 92 ksi |
| --- | ---: | ---: | ---: | ---: | ---: |
| Reviewed 4×4 cleat, quarter-inch bolts, zero gap | 1,280.568 N | 542.437 N | 0.6951 mm | 0.6529° | 1.4855 |
| Reviewed geometry, 1.15 mm relative gap | 1,040.083 N | 688.531 N | 2.9598 mm | 0.8179° | 1.1936 |
| Isolated 4×6 cleat / 5/16 side-bolt proposal, zero gap | 1,507.523 N | 358.561 N | 0.4591 mm | 0.3837° | 1.1593 |
| Isolated proposal, modeled relative gaps | 1,048.566 N | 640.722 N | 2.3276 mm | 0.9645° | 0.7904 |

The proposed side gap is 1.0625 mm; the rail gap remains 1.15 mm. These are
relative CAD bore/shaft scenarios, not observed fit or drilling instructions.
The proposed geometry includes both isolated corner corrections in its
source frame, but only the right corner receives clearance in this comparison.
Other bolted joints remain at zero gap.

The ratios are unadjusted single-bolt references, with normal-duration dry
DF-L No. 2 and the explicit conditional steel input. They do not close group,
splitting, contact/washer, combined steel or complete joint resistance. The
nominal-gap proposed result supports continuing the Grade 5 option; the
zero-gap sensitivity still exceeds one. It does not establish that stronger
hardware is required or that Grade 5 is accepted across unspecified fits.

The panel participation is measurable. In K12-rear on the reviewed geometry,
clearance reduces the corner's maximum bolt shear from 1,280.568 to
1,040.083 N while `round_panel_upper_right_rim_4` screw shear rises from
1,134.144 to 1,237.854 N. The signed current demands, all twelve upper-right
screw actions and both simultaneous host wrenches are retained in each state.
This is load transfer under assumed stiffness, not an increase in a Hillman
product rating.

The right corner has greater returned movement than the worker's left joint.
Keep that result in the compatibility decision; do not transfer the left
joint's favorable motion result or provisional targets as right-joint acceptance.
Maximum local projection-fit residual is 0.02154 mm for reviewed geometry and
0.05167 mm for the isolated proposal. Those residuals limit the local rigid
interface estimates; neither is total panel deflection.

## Final service-worker panel-sharing packet and parent continuation

The owner's final transferred
[panel-sharing packet](../upper-left-service-panel-sharing-2026-10-01/README.md)
has been read and bound into the subsequent parent frame calculation. Its
receipt SHA-256 is
`9b543630412ea9d2be8e832c49547b0ced910f1bd11641475d10b470be53eb5b`;
its comparison SHA-256 is
`73c8c34a867a937fe130b09e7e3276a193c4fa33129cd0d07de966fb09d897e1`.
The worker reused the 21 baseline states and existing 1,386 screw records;
those historical force records were not regenerated.

All 42 softer-law trials stopped because their source floor bearing/open
pattern changed. They supply no accepted motion or stiffness bound and make
no physical frame-failure claim. The independent outward-equilibrium
certificates require at least 3,528 N total upper-left withdrawal at full 2×
A12-rear and 3,527 N upper-right at 2× K12-rear in the declared geometry.
The saved 2× upper-left edge_2 withdrawal is approximately 3,845 N, with a
5,939 N upper-left group total. These twice-recorded proportional loads are
different from the parent's full-case accessory-load scenario; do not mix
their individual screw peaks or allocations. Hillman resistance, measured
stiffness and head pull-through remain unqualified. Low service-cleat bolt
forces do not close that panel path or complete joint acceptance.

The parent now includes modeled clearance at both proposed top corners in
one frame and allows floor contact branches to change. Its
[same-state component worksheet](top-corner-component-checks.md) contains
all twelve frame states and six-case timber/washer/bolt references. The
largest conditional Grade 5 individual lateral ratios are 0.7012 left and
0.7992 right. All sixteen maximum washer envelopes have modeled wood support;
the largest washer wood-pressure ratio is 0.7101. Returned local movement
reaches 2.3447 mm and rotation 0.9852°. Complete resistance and functional
motion acceptance remain separate. The earlier right-only result is retained
above as its distinct scenario, not silently replaced.

The service worker's new assignment is the lower-left outer service cleat,
`left_service_outer_lower_cleat` / `clip_horizontal_lower_left_1`.
The parent and bounded helpers leave that active packet unchanged.

The worker has now completed and transferred the
[lower-left outer service assessment](../lower-left-service-joint/README.md).
The parent matched its receipt SHA-256
`dbf9cd4b761af02671a0f91d0539ce755607561cdc84d70a32297f1847918991`,
all eight bound artifacts and all four unchanged authority records. Its 84
twice-recorded three-rear-case states meet the recorded laws, floor signs and
rigid rank 300. Peak local movement is 0.78235 mm and rotation 0.1784°;
at 1.15 mm clearance the shear/tension envelopes are about 9.35/16.09 N.
The zero-gap envelopes are 203/142 N. Eight nominal washer seats and 24
modeled component routes are supported/clear within their saved scope.
Its unadjusted lateral-reference ratio is at most 0.3323 under its distinct
45 ksi hypothesis. Turning, counterhold and complete joint remain HOLD.
These completed producer/summary files are transferred unchanged for parent
publication; raw results and the worker's replay under `/tmp` are preserved.
The parent is incorporating both outer service-cleat clearances with the top
corners into the six-case model rather than repeating the worker's 84 states.

## Reproduction and continuation

Frozen reports and response vectors:

- [Reviewed geometry comparison](right-corner-clearance-attempt01/comparison.json),
  [vectors](right-corner-clearance-attempt01/response.npz) and exact producer snapshot.
- [Isolated proposal comparison](right-corner-corrected-clearance-attempt01/comparison.json),
  [vectors](right-corner-corrected-clearance-attempt01/response.npz) and exact producer snapshot.
- [Corrected zero-gap whole frame](corner-frame-attempt01/frame-results.json):
  all six static scenarios meet their balance/law gates, peak fitted body
  translation 4.374 mm. It retains unsupported panel properties explicitly.

The original reviewed-geometry comparison retains its earlier exact producer
snapshot. The current producer adds the corrected-frame option and
diameter-specific bearing arithmetic; use fresh output paths when rerunning.

Continue with the same-state corner wood/group/washer checks and compatibility
of its returned movement, while retaining the left service layout. Grade 8
is a documented hardware option, not a selection. The native A12 raw-H STOP
and missing authenticated cases remain unchanged. All 47 formal criteria
remain pending; every physical release flag stays false. No native solve,
new agent review or software test was performed here. The owner subsequently
authorized incremental commits and pushes; maintained parent sources and
summaries are published while frozen generated evidence remains local.
