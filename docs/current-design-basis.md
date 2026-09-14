# Current design basis and decision log

The preferred development candidate is **compact-spliced-knee-development**, selected September 13, 2026.
See the [spliced-knee study](compact-splice-study.md) for its current verification status.
This document records the project's design choices and the scope of its
calculations. It does not establish an approved climber weight limit.

| Item | Current decision |
| --- | --- |
| Geometry | The published candidate has no custom steel base shoes. Its main climbing face begins at a datum 277 mm above the floor. |
| Pad allowance | The design provides 150 mm of exposed kicker above a 127 mm (5-inch) pad covering the entire lower front section across the full board width. Timber feet bear directly on the floor; the pad carries no structural load. |
| Support legs and outer rims | Each support leg and outer rim uses a single nominal 4×6 member. Outer rims sit flush with panel edges; affected horizontal rails are shortened. The header and posts use nominal 2×6 stock with a 139.7 mm front-to-back depth. No doubled vertical members are introduced. |
| Base connection | The rims bear directly on the timber header. Two restored ML24Z angles each use six specified SDS screws. |
| Leg connection | Each leg uses two centered ½-inch upper bolts at 56 mm pitch. Four independent unnotched diagonal 2×6 pieces form two knees; each side has four ⅜-inch splice bolts and two ⅜-inch bolts at each endpoint. Total: 20 complete bolt stacks. No composite action is assumed across the lap. |
| Panels and hold attachment | The accepted plywood and T-nut construction remains the design basis. Additional testing or an upgrade requires a specific identified deficiency. |
| Material calculations | The calculations use published values for the specified species and grade. The lumber basis is dry, unincised Douglas Fir–Larch No. 2. |
| Supports | Timber contact with the floor can carry compression, and the feet are assumed not to slide. Physical floor-friction testing is outside the agreed scope. |
| Vertical loading | The calculations retain the 250 lb one-climber design inquiry and include a 150 lb comparison. Static loads and loads with twice the downward force are evaluated separately; neither represents a verified impact spectrum. |
| Horizontal loading | The initial cases apply either zero or 300 N horizontally along one axis. An additional analytical envelope covers every horizontal direction at 300 N. These scenarios do not represent every possible climbing action. |
| Weight | Current geometry determines the modeled volume, which is converted to mass using stated material densities. A separate 25 kg equipment allowance is evaluated at the locations defined in the equilibrium report. |
| Completion endpoint | Engineer-unreviewed DIY documentation; independent engineer sign-off is not required. Unresolved calculated limitations remain explicit. |
| Design changes | Members or hardware should be enlarged only when a justified calculation identifies a governing shortfall. |

For other pad heights, follow the coordinated geometry changes in the
[current construction package](current-construction-package.md#adapting-to-a-different-pad-height).
The main-face datum must equal pad height plus 150 mm to preserve the exposed kicker.

## Preserved baseline evidence and remaining decisions

The following September 12 evidence describes `no-shoes-development`, not the
new compact 4×6 candidate. It is retained for traceability; no acceptance transfers.

Geometry and browser checks are complete. The
[whole-body equilibrium calculation](current-frame-equilibrium.md) evaluates
support reactions and overturning. The
[base connection review](current-base-connection-basis.md) identifies the
manufacturer's published load directions and the limits of applying them to
this installation. These results do not establish internal joint forces or
member strength.

The [assembled-frame response calculation](current-frame-response.md) now
provides internal member forces, joint moments and deflections for selected
cases. Its numerical checks pass, but the demanding upper-left case exceeds the
leg joint's conditional bolt reference. The 2×6 leg's gross-section comparison
is below its reference. Selected panel-screw comparisons and base-angle
applicability also remain unresolved.

An [independent leg-response audit](current-leg-response-audit.md) reproduces
the joint moment from both bolt forces and the floor/leg free body. It found no
coordinate or explicit support-clamp error that would justify removing that moment.

The [bounded replacement screen](current-leg-revision-screen.md) identifies
larger exploratory layouts using current stock boundaries and saved joint
resultants. It does not select an upgrade: the changed assembly must supply its
own demands, and the screen does not establish that larger stock is necessary.

The selected spliced-knee assembly supersedes those historical connection
trials. Its current decision is recorded in the [completion record](current-diy-completion-record.md)
and [study](compact-splice-study.md), with matching [build instructions](compact-spliced-build-package.md).

A targeted physical test would be appropriate if a remaining uncertainty affects
the design decision and cannot be resolved adequately through calculation or
published evidence. Such a test is not an automatic requirement.

## Maintaining this record

Record the date and reason whenever a design decision changes. Superseded
designs and calculations belong in [the historical archive](history/README.md).
An older report's different assumptions do not, by themselves, justify reopening
a settled material choice.
