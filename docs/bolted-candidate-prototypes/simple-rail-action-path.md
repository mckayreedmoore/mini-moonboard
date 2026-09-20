# PB-01 lower-right rail: action path to be solved

Status: free-body bookkeeping only. No new candidate load, joint resistance,
connection selection, or drilling release is established here. The companion
[`simple-rail-joint-comparison.md`](simple-rail-joint-comparison.md) owns
physical pose and access findings; this sidecar addresses actions only.

## Common datum and sign convention

The representative historical station is `clip_horizontal_lower_right_1`,
between `base_rail_service_lower_right` and
`base_principal_center_right`. Use the same world XYZ axes as the archived
model: +X toward the right rail's outer end, +Y toward the rear, +Z up;
positive moments follow the right-hand rule. The rail grain is +X, while
the principal grain rises approximately along (0,0.642788,0.766044).

For comparison, take one common origin O at the old angle-station origin,
(89.05,616.914452,1199.968456) mm. This is a reporting datum, not a new
bolt center or a claim that the candidate joint acts there. Report each
simultaneous six-component wrench as (Fx,Fy,Fz,Mx,My,Mz) about O. A force
F applied at P contributes (P-O) × F to moment at O; therefore
M_O = M_P + (P-O) × F. State whether each wrench is **on the rail** or
**on the principal**; their interface actions must balance with opposite
signs after all contact and fastener actions are included. Do not compare
moments about different origins or compare independently maximized force
and moment components as though they occurred together.

## Candidate free bodies

For a full-section face overlap, isolate the rail and principal separately.
At their shared face, resolve the bolt-group lateral and axial forces,
bolt-group couples, and compression-only timber contact. The offset between
the rail and principal centrelines adds an eccentric moment to the joint;
it cannot be discarded because both full sections remain uncut. Sum all
tractions and bolt actions about O on each member, then check equal and
opposite transfer at the interface and equilibrium of each member.

For a rectangular solid-timber cleat, isolate three bodies: rail, cleat,
and principal. The rail-to-cleat bolt group and principal-to-cleat bolt
group are serial interfaces. Transfer the rail-side wrench through the
cleat's own bending, shear, torsion, bearing, and any compression-only
contacts before reaching the principal-side group. Both groups need their
own force/moment demands about O and local bolt-group centroids. Their
capacities cannot be added, and assuming equal bolt force or a frictional
clamp would require separate evidence. A retained rail/principal butt
contact can carry compression when closed; it cannot transmit tension
or an unsupported shear/couple by assumption.

At either pose, identify each contact normal and gap. Contact pressure
must be nonnegative in compression and zero when open. Resolve shear
through a documented mechanism; do not silently use friction or glue.
Track which contact patches carry load in each case and whether closure
changes the effective lever arm, local slip, or rotation.

## Historical diagnostics versus new demand

The frozen selected-baseline six cases are `a12-left`, `a12-rear`,
`a12-forward`, `k12-right`, `k12-rear`, and `a1-rear`. Their old ML24Z
flange force/moment records may identify directions, reversals, and
troublesome states to investigate. For example, the archived station
record has a common `origin_mm` and separate `beam` and `upright` flange
wrenches; its moment-capacity fields are null. These are historical
responses of the old angle/SDS topology, not rated bolt-group demand.

The six external case definitions, load assumptions, coordinate convention,
and protected panel-axis layout can seed a new calculation if unchanged.
Old flange reactions, screw forces, contact sharing, frame stiffness,
member stress, and case pass/fail cannot be transferred to either timber
joint. Changing members or connections can change the global contact
active set, including the difficult forward case. The selected archive
also predates a later source edit to center header clips; the documented
source mismatch must not be hidden by changing an evidence hash.

For every new candidate case, recover simultaneous Fx,Fy,Fz and Mx,My,Mz
at O on each side of this joint; contact normal force, gap, and active
patch; and the complete rail, cleat (if used), and principal equilibria.
Then shift each wrench to its actual bolt-group centroid and contact
patch, retaining eccentricity. Resolve each bolt's lateral demand against
both members' grain directions, plus its axial tension/compression,
washer bearing, and combined action. Record slip/rotation and the effect
on adjacent panel-screw receivers and member load paths. These are input
requirements, not numerical predictions or a joint rating.

## Exact historical source locations

- [`current-candidate.json`](../../current-candidate.json) identifies the
  selected model and the six frozen `flush-checks.json` assessments.
- [`floor-runner-mvp-angle-demands.json`](../floor-runner-mvp-angle-demands.json)
  has `cases[case].angles["clip_horizontal_lower_right_1"]`, including
  `origin_mm`, `flanges.beam/upright.force_xyz_n`, and
  `flanges.beam/upright.moment_xyz_nmm` for all six archived cases.
- [`floor-runner-mvp-evidence.json`](../floor-runner-mvp-evidence.json)
  indexes the six-case evidence and angle-demand ledger.
- `fea/results/floor-runner-mvp/<case>/report.json.gz` contains native
  `angle_stations`, `physical_connection_forces`, `connector_forces`,
  contact and equilibrium diagnostics. The same directory's
  `flush-checks.json`, `manifest.json`, and `sources.zip` provide the
  historical check decision and provenance for each named case.
- [`connection-axes.csv`](../floor-flush-construction-kerf-right/connection-axes.csv)
  records the fixed kerf-right panel axes and the old station's six SDS
  axes. It is an old-geometry reference, not a candidate bolt schedule.
- [`stock-profiles.json`](../floor-flush-construction-kerf-right/stock-profiles.json)
  records current kerf-right member shapes used to locate the butt joint.
- [`bolted-candidate-baseline-audit.json`](../bolted-candidate-baseline-audit.json)
  records the source/evidence revision discrepancy; old case acceptance
  does not authenticate a changed bolted candidate.

No native solve or physical receiving inspection is represented by this
sidecar. The complete new case actions and resistance checks remain open.
