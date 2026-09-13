# Current design basis and decision log

The current candidate is **no-shoes-development**, dated September 12, 2026.
This document records the project's design choices and the scope of its
calculations. It does not establish an approved climber weight limit.

| Item | Current decision |
| --- | --- |
| Geometry | The published candidate has no custom steel base shoes. Its main climbing face begins at a datum 277 mm above the floor. |
| Pad allowance | The design provides 150 mm of exposed kicker above a 127 mm (5-inch) pad allowance. The pad carries no structural load. |
| Support legs and outer rims | Each support leg and outer rim uses a single nominal 2×6 member. Other members retain their existing sizes, and no doubled vertical members are introduced. |
| Base connection | The rims bear directly on the timber header. Two restored ML24Z angles each use six specified SDS screws. |
| Leg connection | Each leg retains four modeled ⅜-inch bolt assemblies. The separately proposed Grade 5 catalog bolts require verification of their grip length and complete hardware arrangement before they can replace the modeled bolts. |
| Panels and hold attachment | The accepted plywood and T-nut construction remains the design basis. Additional testing or an upgrade requires a specific identified deficiency. |
| Material calculations | The calculations use published values for the specified species and grade. The lumber basis is dry, unincised Douglas Fir–Larch No. 2. |
| Supports | Timber contact with the floor can carry compression, and the feet are assumed not to slide. Physical floor-friction testing is outside the agreed scope. |
| Vertical loading | The calculations retain the 250 lb one-climber design inquiry and include a 150 lb comparison. Static loads and loads with twice the downward force are evaluated separately; neither represents a verified impact spectrum. |
| Horizontal loading | The initial cases apply either zero or 300 N horizontally along one axis. An additional analytical envelope covers every horizontal direction at 300 N. These scenarios do not represent every possible climbing action. |
| Weight | Current geometry determines the modeled volume, which is converted to mass using stated material densities. A separate 25 kg equipment allowance is evaluated at the locations defined in the equilibrium report. |
| Design changes | Members or hardware should be enlarged only when a justified calculation identifies a governing shortfall. |

## Evidence and remaining decisions

Geometry and browser checks are complete. The
[whole-body equilibrium calculation](current-frame-equilibrium.md) evaluates
support reactions and overturning. The
[base connection review](current-base-connection-basis.md) identifies the
manufacturer's published load directions and the limits of applying them to
this installation. These results do not establish internal joint forces or
member strength.

The next engineering deliverable is a calculation of how the current frame
transfers loads through its members and connections. It must account for bearing
between the rims and header, rotation at the leg joints, and sideways movement
of the frame. Once those forces are established, the governing members and
connections can be checked and a matching set of construction drawings and
schedules can be reviewed.

A targeted physical test would be appropriate if a remaining uncertainty affects
the design decision and cannot be resolved adequately through calculation or
published evidence. Such a test is not an automatic requirement.

## Maintaining this record

Record the date and reason whenever a design decision changes. Superseded
designs and calculations belong in [the historical archive](history/README.md).
An older report's different assumptions do not, by themselves, justify reopening
a settled material choice.
