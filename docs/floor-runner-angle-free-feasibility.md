# Floor-runner angle-free feasibility

## Decision

Removing all 24 ML24Z angles is a mechanically distinct, plausible investigation,
but is not presently a supported replacement. The existing panel screw network
provides identifiable paths between members; there is no justification for
declaring the assembly unstable merely because the angles are removed. Conversely,
accepted panel construction does not establish capacity for these changed loads.
No angles, screw axes, drilling, or viewer selection are changed by this note.

The smallest useful next experiment is an **angle-free connection topology and
load-transfer screen**, preserving all 66 SPAX screws, 12 complete leg/runner
bolt stacks, independent panel seams, and explicit compression-only timber
contacts. Run that screen before six expensive nonlinear cases. Do not retain
angle constraints or replace them with bonded timber interfaces.

## What remains connected

The current `floor-flush-construction/panel-attachment-axes.csv` establishes:

| Subassembly | Retained positive connection |
| --- | --- |
| Each main panel | Four screws to its outer rim, four to its separate center principal, two to each applicable horizontal rail |
| Each kicker | Two screws to its outer post, two to its center post, five to the header |
| Each side support triangle | Two upper rim/leg bolts, two front post/runner bolts, two rear leg/runner bolts |
| Upper left/right frame halves | Shared top rail; no bonded center panel seam |
| Lower left/right base halves | Shared header through separate kicker screw groups |

Panel membrane action can transfer load from a center principal to the outer
rim and into the bolted side support. Kicker membrane action can connect the
header to floor-supported posts. Rim/header and principal/header bearing can
carry compression only. A principal lifting from the header needs its panel
screws to carry the changed resultant. The horizontal and vertical main-panel
seams remain independent, even where a continuous timber member bridges them.

This is a path inventory, not a strength calculation. In particular, plywood
used as a structural diaphragm must have its actual membrane forces recovered;
calling the accepted face panel a diaphragm does not supply diaphragm capacity.

## First mechanisms to check

The six short horizontal battens each have two collinear screw positions. The
top rail's four screws also lie on one line. Point translational springs alone
cannot restrain rotation about that line. Distributed panel/timber contact can
resist rocking when compression develops on the appropriate side; it cannot
be silently replaced by bilateral rotational restraint. Existing end contacts,
dead weight, contact opening and physical screw-head seating all matter.

The kicker's two collinear screws into each post create the same local question
when other restraints are absent. The outer posts retain their runner bolts;
the center posts do not. Check center-post rocking and header separation rather
than inferring stability from a connected graph.

The lightweight screen should form the rigid-member/finite-panel connection
stiffness and inspect unconstrained modes with contacts open and with admissible
contacts active. Recover any null-mode shapes; distinguish harmless batten
spin from a frame or panel mechanism. A final nonlinear calculation still needs
contact consistency and finite panel/member stiffness.

## Available screw basis and its limits

The selected product is SPAX XFT08P-2000. Its published evaluation supplies
product dimensions, steel strengths, withdrawal and head pull-through data,
subject to its installation conditions. Its plywood lateral table is for SPF,
so the repository uses a separate DF-L/plywood dowel-yield calculation. Do not
transfer the SPF table to DF-L without its stated applicability.
[SPAX TER 2010-02](https://www.drjcertification.org/report/download/1936).

The current `fea/reinforced_fastener_checks.py` and applicability ledger use:

| Conditional per-screw reference | N |
| --- | ---: |
| Lateral, explicit root-diameter yield calculation | 235.680 |
| Withdrawal, 133 lbf/in × 1.24 in embedded thread | 733.601 |
| Head pull-through, adopted lower plywood reference | 533.787 |

These are existing assumptions, not new angle-free acceptance. The old 943 N
head reference in the earlier structural-screw result is not the currently
adopted head comparison. For each changed connection recover simultaneous
shear and withdrawal; apply the existing wood interaction, head bearing, steel
component and combined-steel checks. Check real embedded length, countersink,
edge/end distances, split paths and group load distribution. Four screws do
not automatically receive one quarter of a group force.

The saved angle-connected A12-left case contains individual angle-screw shear
as high as 733 N. It cannot be assigned to the nearby SPAX screws, but its scale
shows why deleting the angles is not a negligible response perturbation.
Retain the stated 250 lb inquiry, actual case-specific downward multipliers,
300 N horizontal scenarios, dry unincised DF-L No. 2, accepted plywood/T-nuts,
and floor support assumptions. No floor test or generic panel qualification
campaign is introduced; changed connection and membrane demands still need
their applicable comparisons.

## Local plywood gusset fallback

A useful local candidate is a plywood side gusset joining each outer rim to
its **outer post**, bypassing the unsupported complete-wrench ML24Z detail.
Both receivers expose side grain to a screw normal to the YZ gusset plane.
The current left rim and outer post have the same nominal exterior X face,
−1219.2 mm, so a flat exterior gusset can seat on both without a spacer. Its
lower extent must clear the outboard runner and front bolt/washer envelopes.
Retain explicit header/post and rim/header bearing and the kicker/header screws.
This bypass does not by itself replace center or rail connections.

A superficially similar gusset attached directly to the **header end** would
drive screws parallel to the header's X grain. It therefore does not inherit
the side-grain withdrawal route. The rim/post version avoids that specific
obstacle.

Begin with a separate 23/32-inch plywood plate, at least two noncollinear rows
in each receiver, and catalog lag screws with identified steel grade, actual
thread/root geometry and washers. Select the lag length from the 38.1 mm post
thickness as well as the 88.9 mm rim width; a lag long enough for the rim can
exit the post. No diameter, count, plate outline or drilling is released here.
The first sizing exercise must include eccentric fastener-group shear and
withdrawal, plywood net section/block tear-out and bending, washer bearing,
wood splitting, screw bending, penetration and installation requirements.
Single-sided gussets introduce an offset; their plate bending and withdrawal
cannot be discarded by assuming an in-plane-only truss joint.

AWC TR12 explicitly supports calculation with actual lag shank/root geometry
and varying bearing lengths; it assumes applicable placement provisions and
does not qualify the entire joint by itself.
[AWC TR12, examples 3.2–3.3](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf).

## Assembly implication and completion boundary

A supported horizontal fixture can locate loose timber while panels and all
retained screws are installed. Temporary blocking and lifting restraints must
remain through erection until the complete load path is present. This makes
an angle-free assembly sequence conceivable; it does not establish service
strength or permit raising a partially connected panel/frame.

No complete passing candidate is established by this bounded review. The next
decision is finite: either the unchanged 66-screw network survives the explicit
mechanism and local-demand screen, or its governing transfer identifies where
one targeted gusset/fastener group is required. Whole-frame solving follows
that supported local path, not a presumption that removal of proprietary
connectors removes all connection checks.
