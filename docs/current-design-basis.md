# Current design basis: flush floor-runner development

The selected development is `compact-floor-flush-development`: solid 4×6
legs/rims, a compact single-2×6 base, two outboard 2×6 floor runners, whole
kickers, the 1:12 rear recess, twelve complete outward-facing bolt stacks, 24
ML24Z angles and 66 panel/kicker attachment axes. Runner ends meet the outer
posts and rear-leg faces, lower rim ends meet the post/header plane, and leg
tops meet the rim faces.

The [MVP master plan](floor-runner-mvp-master-plan.md) and [criteria
ledger](floor-runner-mvp-criteria.md) control completion. Six fresh selected-candidate
no-slip cases pass all 36 frozen checks; the [aggregate](floor-runner-mvp-evidence.json)
and [24-angle demand ledger](floor-runner-mvp-angle-demands.json) retain their
source identities and disclosed limitations. The historical A12-left
finite-friction case and every taper/spliced case remain comparison evidence
only. The projected-seat scalar is preserved as a non-adopted sensitivity;
actual retained-section, bearing, contact, gross/net, bolt and listed ML24Z
checks remain adopted. This is an engineer-unreviewed development, not an
unconditional rating or fabrication release.

## Preserved spliced flush-top basis

The preceding `compact-spliced-flush-top-development` package and its six cases
remain preserved history. They do not qualify the floor-runner assembly.

## Preserved preceding design basis

The following is historical. Its references to "current" or "selected" apply
to the candidate described there, not the flush revision above.

# Current design basis and decision log

The selected candidate is **compact-exterior-brace-development**, selected September 14, 2026.
Use the [support study and conditional fabrication packages](clear-space-study.md)
for its current verification status. The floor-rail and inboard spliced-knee assemblies remain preserved references.
This document records the project's design choices and the scope of its
calculations. It does not establish an approved climber weight limit.

| Item | Current decision |
| --- | --- |
| Geometry | The published candidate has no custom steel base shoes. Its main climbing face begins at a datum 277 mm above the floor. |
| Pad allowance | The design provides 150 mm of exposed kicker above a 127 mm (5-inch) pad allowance. This is a clearance datum, not a requirement to cover the full board width with pads. Timber feet bear directly on the floor; the pad carries no structural load. |
| Support legs and outer rims | Each support leg and outer rim uses a single nominal 4×6 member. Outer rims sit flush with panel edges; affected horizontal rails are shortened. The header and posts use nominal 2×6 stock with a 139.7 mm front-to-back depth. No doubled vertical members are introduced. |
| Base connection | The rims bear directly on the timber header. Two ML24Z base angles each use six specified SDS screws, with the corrected placement at Y = −105.85 mm and 19.05 mm header-edge clearances. Unlisted angle separation and independent flange couples remain unqualified. |
| Leg connection | Two ½-inch upper bolts per leg use 64 mm pitch and the specified thicker round washers. Each exterior knee has two ⅜-inch bolts at each endpoint and four at its splice. Total: 20 complete bolt stacks. |
| Exterior knees | Each side uses one solid 4×6 rim-end piece and one solid 2×6 leg-end piece, square-ended and unnotched, with 51 mm splice pitch and extended overlap. All knee wood lies outside the panel edges. No floor rails or leg-foot recesses are part of this candidate. |
| End finish and bolt orientation | Inclined rim ends retain 7 mm rear projection; rear-leg tops retain 24 mm projection normal to the rim rear face. Nuts and threaded ends face outward. Use the [exterior-specific package](clear-space-study.md#candidate-specific-fabrication-packages), not the floor-rail or preceding upper-joint drilling sheets. |
| Panels and hold attachment | The accepted plywood and T-nut construction remains the design basis. Additional testing or an upgrade requires a specific identified deficiency. |
| Material calculations | The calculations use published values for the specified species and grade. The lumber basis is dry, unincised Douglas Fir–Larch No. 2. |
| Supports | Compression-only floor cells can open. Current member and connection calculations use the owner's explicit conditional no-slip tangential support assumption. This does not qualify floor friction or imply an installed anchor. Recorded per-cell Coulomb cases remain historical evidence under their own assumptions; physical floor testing remains outside scope. |
| Vertical loading | All six current cases apply a 250 lb climber with a 2.0 downward multiplier: 2224.1108 N downward. Earlier 150 lb and unmultiplied comparisons do not qualify this assembly; the multiplier is not a verified impact spectrum. |
| Horizontal loading | Each current case adds 300 N along one axis: A12 rear (+Y), forward (−Y), left (−X); K12 right (+X), rear (+Y); A1 rear (+Y). No continuous all-direction envelope is claimed for this candidate. |
| Weight | Current geometry determines modeled timber/plywood and steel self-weight using stated densities. Each current native case also includes a 25 kg equipment allowance at its recorded load locations. Viewer mass estimates exclude equipment; an older whole-body equilibrium envelope does not establish current internal-force acceptance. |
| Completion endpoint | Engineer-unreviewed DIY documentation; independent engineer sign-off is not required. Unresolved calculated limitations remain explicit. |
| Design changes | Members or hardware should be enlarged only when a justified calculation identifies a governing shortfall. |

The selected exterior-brace package uses the stated 127 mm pad allowance. A different
pad height requires coordinated geometry and schedule changes; the main-face datum
must equal pad height plus 150 mm to preserve the exposed kicker. Historical
pad-adaptation instructions do not constitute a checked exterior-brace variant.

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

The selected exterior-brace assembly supersedes those historical connection
trials. Its current decision is recorded in the
[completion record](current-diy-completion-record.md) and
[support study](clear-space-study.md). All six current cases meet their 25 listed
conditional criteria; the separate 5×5 A12-left foot-grid sensitivity also
meets those criteria. This does not demonstrate converged local floor pressure.
The specified hardware/thread conditions, conditional no-slip support assumption
and unqualified commercial-angle actions remain explicit limits. Recorded
Coulomb and earlier floor-rail cases retain their own historical evidence. The
[spliced-knee study](compact-splice-study.md) and
[build package](compact-spliced-build-package.md) remain references.
No acceptance transfers between these assemblies.

A targeted physical test would be appropriate if a remaining uncertainty affects
the design decision and cannot be resolved adequately through calculation or
published evidence. Such a test is not an automatic requirement.

## Maintaining this record

Record the date and reason whenever a design decision changes. Superseded
designs and calculations belong in [the historical archive](history/README.md).
An older report's different assumptions do not, by themselves, justify reopening
a settled material choice.

## Crash-pad viewer arrangement

Two user-specified pads, each 48 × 72 × 5 inches, sit side by side for
96 × 72 inches of coverage. Their center seam is X = 0 and runs front to
back. They rest at Z = 0 and occupy Y = 0–1828.8 mm, behind the kicker/header.
The viewer provides a Crash pads toggle and selectable dimensions. These
objects do not change frame mass, timber supports, contact friction or load
assumptions. The depiction does not establish impact-attenuation performance.
See the [current crash-pad construction record](current-crash-pad-construction.md).
