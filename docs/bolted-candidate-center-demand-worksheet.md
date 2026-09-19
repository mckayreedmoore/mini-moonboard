# Center-joint demand worksheet — diagnostic, no capacity or drilling release

The fixed-member left center principal and post connect to the same header.
Two unselected AB205 arrangements are under study: coincident shared-header
bolts, or distinct top and underside header rows. This worksheet defines the
actions required to size either arrangement. It does **not** assign them a
numeric value, a load rating, or an accepted connector. Read with the
[joint detail](bolted-candidate-center-joint-info.md) and
[shared-fastener method gate](bolted-candidate-prototypes/center-shared-bolt-method.md).

## Applied cases and available evidence

The retained case names and applied-load definitions are
[`scripts.clear_space_batch.CASES`](../scripts/clear_space_batch.py). The
[candidate native-input contract](bolted-candidate-native-input.json) plans
six cases at the physical kerf-right width, but its candidate-specific
mesh/contact adapter is not ready and zero candidate cases have run. Preserve
the applied loads; do not scale them to make a connector fit.

The [archived angle ledger](floor-runner-mvp-angle-demands.json) concerns the
selected screwed baseline, not this bolted candidate. In particular the
archived principal-side center angle origin is displaced 10.1 mm in Y from the
current one; the post-side origin is unchanged. Its separately listed peak
force and peak moment occur in different
cases. Even a same-case archived wrench is only a diagnostic example of the
old load path. Translating its moment to a current point does not turn it
into a new-candidate demand. The
[representative blockers](bolted-candidate-representative-blockers.json)
record that boundary.

| Required current input, for each of six cases | Present status |
|---|---|
| Force and moment on principal at its present header interface, with origin | Missing |
| Force and moment on post at its present header interface, with origin | Missing |
| Header contact forces and moments, including other connected members | Missing |
| Consistent sign convention and same-case equilibrium residual | Missing |
| Connector pose, confirmed hole centers, bend, grip, and contact surfaces | Nominal trial only |
| Contact/slip stiffness or a justified range for each interface | Missing |

The global applied case load alone cannot uniquely determine the local
principal/post split: the header, its other attachments, bearing/contact and
connection stiffness provide multiple parallel load paths. A simple free-body
calculation is useful once its boundary actions are supported; it cannot
recover those unknown reactions merely by summing the global applied load.

## Per-case free-body and translation

Use one frame-global right-handed XYZ basis in millimeters, newtons, and
newton-millimeters. Record a distinct same-case wrench for the principal and
post, including whether it is member-on-connector or connector-on-member.
For each leg, translate a reported wrench to the proposed connector reference:

`F_joint = F_report`;
`M_joint = M_report + (p_report - p_joint) × F_report`.

This is implemented and unit-tested by
[`shift_wrench`](../mini_moonboard/bolted_joint_mechanics.py). The shift changes
the reference point only; it does not correct a changed structural model.
Project onto a verified right-handed local basis before classifying bolt
shear, bolt-axis tension, angle flange action, and wood load-to-grain angle.
The existing `to_local` helper rejects a left-handed or non-orthogonal basis.

For either angle, resolve its *same-case* local wrench into two actual bolt
forces, steel/wood contact, and any supported direct bearing or other force:

`F_joint = Σ F_bolt,i + F_contact + F_other`;
`M_joint = Σ (r_bolt,i × F_bolt,i) + M_contact + M_other`.

Include the actual point of every contact and other force. The existing
[`equilibrium_residual`](../mini_moonboard/bolted_joint_mechanics.py) checks
these sums but does not determine the unknown forces. Show its residual for
each case and connection. Treat opening contact as inactive; if friction is
claimed, state its physical law and sensitivity, not an unexplained rigid tie.

### Shared-header hypothesis

At each of two coincident header axes, a **single** physical bolt receives
actions from both steel side flanges and the wood middle member. Keep both
leg actions simultaneous. Express forces from both outside steel flanges
**on the same bolt** in one common direction. Ordinary symmetric double shear
requires applicable geometry/material symmetry and equal, same-direction
outside lateral actions, balanced by the middle timber action. For example,
outside actions `(+100, +100) N` and middle action `-200 N` have that force
pattern; `(+100, -100) N` outside and `0 N` middle do not. Force balance alone
does not establish the method's other applicability conditions. Adding two
full-header single-shear ratings double-counts one bolt and one wood bearing
zone. Unequal or opposing outside actions need a method applicable to that
whole-fastener loading. The equal-and-opposite action/reaction on either side
of one interface remains a separate check. Bolt-axis tension, washer bearing,
and prying are additional, not substitutes for lateral equilibrium.
See [AWC TR12 Table 1-1 and Figure 2-2](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
for the ordinary double-shear force directions and yield-mode idealization;
this mechanics example does not select the NDS edition for resistance design.

### Distinct-row hypothesis

The top and underside header bolt groups have separate axes. Resolve each
angle's action and its own steel-to-wood path, then check the *combined*
header: local bearing, row interaction, net section, splitting, and contact.
The conditional parallel row interval in the
[stagger screen](bolted-candidate-prototypes/center-y-stagger.json) cannot be
adopted until the actual reversible load direction and oblique end have been
classified. Separate holes do not imply independent timber capacities.

## Diagnostic sensitivity, not an acceptance case

An authorized diagnostic may use the six unchanged applied load definitions
and a separate output directory, with clearly provisional contact and slip
properties. Compare at least plausible open/closed contact and soft/stiff
connection assumptions; neither single setting is automatically the upper
bound on all bolt forces. Check global and local equilibrium, record the
assumption set beside every action vector, and do not merge the output into
candidate passing cases. A native diagnostic still needs an explicit
candidate adapter and cannot be produced by relabeling baseline results.

No numeric required local action is established here. The next admissible
number is a **same-case, current-geometry** principal/post action with a
traceable free-body or diagnostic model; only then can the per-bolt and
contact allocations be calculated and compared with complete wood, steel,
fastener, and serviceability resistances. G1, G2, and drilling remain closed.
