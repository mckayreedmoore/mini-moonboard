# Rotated-rear 2×8: complete nominal geometry and comparison

**Development candidate, not construction approval.** This iteration makes a
2×8-depth layout geometrically coherent without replacing the published plywood,
2×10, 2×12 or [original timber-only 2×8](2x8-feasibility.md) references.
Intended use is one climber up to 250 lb; 300 lb remains a sensitivity, not a
validated user rating. Additional 150 and 200 lb cases examine lighter climbers.
Pads are separate and excluded; no anchoring is credited.

## Inspect the candidate

- [Interactive 2×8 shallow model](https://mckayreedmoore.github.io/mini-moonboard/?model=2x8-shallow)
- [STEP assembly](../exports/shallow-frame/2x8-shallow.step)
- [Parts, metric and imperial](../exports/shallow-frame/2x8-shallow_parts.csv)
- [Nominal connection schedule](../exports/shallow-frame/2x8-shallow_connections.csv)

![Shallow 2×8 climbing side](../exports/shallow-frame/2x8-shallow_front.png)
![Shallow 2×8 rear framing](../exports/shallow-frame/2x8-shallow_rear.png)

The viewer is a representation of nominal drilled CAD and hardware envelopes,
not a rendering of a validated finite-element joint model. The schedules do
not select rated fastener products or authorize purchasing a final build kit.

## What changed

The 2×8 rim remains 38.1 × 184.15 mm (1½ × 7¼ in), with the rear datum
166.15 mm behind the panel-backing datum. The main panels, 225 mm kicker,
40° board slope, hold/LED coordinates and 38.1 mm two-layer plywood legs retain
their previous geometry. The legs are not replaced by solid 2×8 lumber.

Rear 2×4 crossmembers now present their broad face parallel to the board:
88.9 mm uphill and only 38.1 mm normal to the board. That recovers 50.8 mm of
depth and lengthens the short normal ribs from 39.15 to 89.95 mm. Rear/rib
angles move to those new interfaces. Crossmember-to-rim beam bolts spread
across the beam span at its mid-depth; simply retaining the old depth-separated
holes would leave one bolt outside the shallow timber. Bolt lengths/grips and
cheek-splice screw positions also change.

There are **45 timber parts, 20 custom angle envelopes, 88 bolts and 132 screws**.
All rear-crossmember attachments remain bolt-operated. Main panels retain
12 perimeter plus four mid-batten screws each; kicker panels retain eight each.
The steel angles remain unrated sharp-corner envelopes, not catalogue-selected
or fabrication-approved parts. This iteration resolves packaging, not the
complexity of that hardware inventory.

## Geometry audit

The seven shallow-frame tests cover the inherited solid/contact/collision,
hardware/tool, lighting/routing, floor-bearing and crossed-bore gates, plus
rotated dimensions, unchanged reference geometry and rear-member detachability.
An additional independent shaft-clearance test checks every fastener shank
against nonreceiving parts; it found no unintended intersections. Heads,
washers and nuts are checked separately by the inherited gates.

Review caught the misplaced depth-separated crossmember bolt before the
geometry freeze; its placement was corrected and the gates rerun. None of
the relocated connections uses an inherited drilled backing part, avoiding
stale old holes in those reused pieces. These checks establish nominal geometry
only: finite tolerances, timber edge/end distances, tool selection and connection
capacity still require review. Straight wire reservations are not a complete
installed-kit routing or service-access verification.

## Matched bulk FEA

The existing Docker/Gmsh/CalculiX workflow completed six cases at each of two
mesh settings: **12 accepted solves**. All candidates below use isotropic
E=7000 MPa, nu=0.3, perfectly bonded timber interfaces, undrilled bulk timber,
no steel/fastener compliance, no gravity, and fixed floor nodes. Loads are shared
equally over five row-12 nodes near A12/C12/F12/H12/K12. These are equal-property
geometry comparisons, not selected lumber properties or actual joint behavior.

Displacement is the maximum magnitude **among those five loaded nodes**, not
the maximum anywhere in the frame. Values below are millimetres at the 40 mm
mesh setting. The old 2×8 retains its unrotated, incompatible connection layout;
its bulk result is not relabelled as the new candidate.

| Independent load case | Plywood-only reference | Old 2×8 timber-only | 2×10 | 2×12 | New shallow 2×8 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Downward 1.2 kN | 0.36846 | 0.83925 | 0.54483 | 0.38900 | 0.85321 |
| Downward 2.4 kN | 0.73693 | 1.67849 | 1.08966 | 0.77800 | 1.70641 |
| Downward 1.2 kN + outward 0.3 kN | 0.47714 | 1.08137 | 0.70196 | 0.50228 | 1.09994 |
| Downward 1.2 kN + inward 0.3 kN | 0.25996 | 0.59723 | 0.38781 | 0.27587 | 0.60657 |
| Outward/downward normal, exploratory | 0.57011 | 1.28155 | 0.83190 | 0.59742 | 1.30466 |
| Inward/upward normal, exploratory | 0.57011 | 1.28155 | 0.83190 | 0.59742 | 1.30466 |

The new shallow candidate's downward sample displacement is **2.32× the plywood
reference**, but only **1.66% above the old 2×8 counterfactual**. Thus the
packaging redesign has a small additional bulk-stiffness cost relative to the
already shallower model; it does not recover the plywood or 2×12 stiffness.
No allowable-deflection limit, stress capacity or connection capacity is tested.

| New shallow mesh | Nodes | Minimum final Jacobian | Downward 1.2 kN |
| --- | ---: | ---: | ---: |
| 60 mm | 61,948 | 2258.786 | 0.85450 mm |
| 40 mm | 125,615 | 686.391 | 0.85321 mm |

Baseline refinement changes the result by 0.152%; the maximum across six cases
is 0.186%, relative to the finer result. The finer mesh initially produced
element-quality warnings; optimization recovered a positive final minimum
Jacobian before acceptance. This is a two-mesh consistency check, not proof of
stress convergence. Actual deck loads/supports, finite displacement vectors,
force balance within 0.1 N and moment balance within 1 N mm are audited, with
source/deck/result hashes and reaction coordinates in the
[published records and raw DAT outputs](../fea/results/hybrid/2x8-shallow/).

For unchanged downward load location/direction, the linear no-gravity solutions
can be rescaled to the user-weight cases. These are **algebraic rescalings, not
additional FEA runs or dynamic load ratings**:

| Candidate | 150 lb, 667.23 N | 200 lb, 889.64 N | 250 lb, 1112.06 N | 300 lb sensitivity, 1334.47 N |
| --- | ---: | ---: | ---: | ---: |
| Plywood-only reference | 0.20488 mm | 0.27317 mm | 0.34146 mm | 0.40975 mm |
| Old 2×8 timber-only | 0.46664 mm | 0.62219 mm | 0.77774 mm | 0.93329 mm |
| 2×10 | 0.30294 mm | 0.40392 mm | 0.50490 mm | 0.60588 mm |
| 2×12 | 0.21629 mm | 0.28839 mm | 0.36049 mm | 0.43259 mm |
| New shallow 2×8 | 0.47441 mm | 0.63254 mm | 0.79068 mm | 0.94881 mm |

Historical data sources: [plywood](../fea/results/box_audited_40_7000.json),
[old 2×8](../fea/results/hybrid/2x8/box_audited_40_7000.json),
[2×10](../fea/results/hybrid/2x10/box_audited_40_7000.json), and
[2×12](../fea/results/hybrid/2x12/box_audited_40_7000.json).

## One-person stability comparison

The revised drilled-wood/custom-angle inventory gives **195.31 kg** at the
assumed densities, with centre of gravity Y=745.09 mm. Its extreme floor toes
are Y=−159.07 and 1398.25 mm. Fasteners, holds, glue and LEDs remain omitted;
these are modelled quantities, not weighed components. Rotation alone does not
leave assembly mass or centre of gravity unchanged because ribs and connections
also change.

The separate legacy 2D normal-force cases still indicate uplift: −384.88 N at
the kicker in the outward/downward case and −847.55 N at the leg in the
inward/upward case, with moment factors 0.676 and 0.567 respectively. These
exploratory directions are not established governing use loads, but their
failures remain recorded rather than discarded.

The separate [96-case shallow-frame envelope record](../fea/results/hybrid/shallow_user_load_envelope.json)
tests 150, 200, 250 and 300 lb, with all main/kicker hold positions, 0/50/100 mm
hold projection, full/80% modelled mass, static/twice gravity force, and 0/300 N
horizontal force over all azimuths. Only this revised shallow candidate has
this expanded four-weight stability record; the historical comparison
candidates retain their separately published two-weight evidence.
Each resultant acts independently, not at all holds simultaneously. Twice
gravity and 300 N horizontal are illustrative sensitivities, not prescribed
or experimentally verified climbing loads. See the [method](user-load-envelope.md).

| Shallow candidate moment factor | 150 lb | 200 lb | 250 lb | 300 lb sensitivity |
| --- | ---: | ---: | ---: | ---: |
| Full mass, static weight, zero hold projection, 300 N horizontal | 2.004 | 1.969 | 1.936 | 1.903 |
| Worst tested combination at full mass | 1.690 | 1.571 | 1.468 | 1.377 |
| Worst tested combination at 80% mass | 1.352 | 1.257 | 1.174 | 1.102 |
| Combinations below the 1.5 target, out of 24 per weight | 2 | 4 | 6 | 6 |

The worst combinations use twice gravity force, 100 mm hold projection and
300 N toward the climber; row 12 and the leg-side tipping edge govern.
**18 of 96 combinations fall below the 1.5 project moment target.** At full
modelled mass, all tested 150/200 lb combinations exceed 1.5, but some at those
weights fall below it in the 80%-mass sensitivity. None of these 96 cases
reaches a negative net restoring moment, but that does not
resolve the separate legacy uplift cases or establish a safety margin for
actual climbing. The 1.5 target is a screening choice, not complete code
compliance. Friction demand is reported without measured available friction;
sliding, floor unevenness, rocking and yaw equilibrium remain unresolved.

## Decision and remaining gates

Geometric fit makes this candidate eligible for comparison, not automatically
preferable to a deeper frame. Rotating an isolated rear 2×4 reduces its normal
bending stiffness to approximately 18.37% of the original orientation at equal
modulus, while increasing the perpendicular stiffness; whole-frame behavior
also depends on the longer ribs and altered load paths. See the
[five-step plan](shallow-frame-plan.md) for the derivation and acceptance gates.

**Retain the shallow 2×8 as a development option, but do not reduce the rim
again yet.** Its packaging problem is resolved at nominal-envelope level, and
the extra bulk displacement versus the old 2×8 is about 1.7%, not an established
capacity failure. The next useful geometric comparison is a small set of
explicitly modelled leg/footprint adjustments, starting with modest additional
leg-side reach. Recalculate member mass, centre of gravity, leg angles and joint
demands for each option; do not credit a longer support polygon without the
actual structure. Preserve the plywood/2×12 stiffness alternatives and all
legacy uplift cases rather than selecting a footprint solely to pass the new
weight sensitivities. A footprint change cannot resolve unrated joints.

Before reducing depth further or authorizing construction, resolve the
[connection strategy](hybrid-joint-next-steps.md): especially end-grain screws,
real angle details, leg bolt-group action and material/adhesive specifications.
Perfect bonds do not validate these joints. Connection-aware analysis must
release those bonds, allow floor lift-off and explicitly address sliding;
fixed-floor displacement cannot establish unanchored stability. Qualified
structural review and controlled physical verification remain construction
gates, not tasks silently completed by a CAD collision pass.
