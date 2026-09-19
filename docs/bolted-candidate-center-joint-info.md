# RS-2: fixed-member center-joint information package

Status: information package only. No connector, bolt row, drilling position, capacity,
or structural acceptance is selected. Keep the center principal and post in their
current positions, the physical `kerf-right` panels, and all 66 panel/kicker screws.
Factory connectors only; no custom cut-and-drilled steel. See the
[owner inputs](bolted-candidate-owner-inputs.json),
[panel contract](bolted-candidate-panel-contract.json), and
[G1 decision](bolted-candidate-g1-decision.json).

## Representative assembly and source drawing

Use the left center pair: `clip_split_base_center_left` (inclined
`base_principal_center_left` to `base_header`) and
`clip_split_header_center_left` (`base_post_center_left` to the same header).
The raw CAD solids and grain-parallel side edges are the geometry source:
[frame model](../mini_moonboard/compact_floor_flush_frame.py),
[center-fit script](../scripts/bolted_candidate_ab205_center_fit.py), and its
[record](bolted-candidate-prototypes/ab205-center-fit.json). The
[shared-axis sheet](../exports/rs2-center-joint/rs2-ab205-shared.svg),
[staggered-axis sheet](../exports/rs2-center-joint/rs2-ab205-stagger.svg), and
[drawing notes](bolted-candidate-prototypes/rs2-center-joint-sheet-notes.md)
show the two local, non-drilling hypotheses and protected nearby screw starts.
The 38.1 mm header
lies between an upper principal-side angle and an underside post-side angle.
The principal is inclined; its grain follows its length and meets an oblique
cut at the header. The post grain follows its length. The header grain follows
the header length. Do not measure the principal's end distance as if its cut
were square to grain. The record's 26.940 mm grain ray is a diagnostic from a
nominal hole center to the raw oblique end, not an accepted bolt end distance.

Schematic section, **not to scale or a drill drawing**:

```text
inclined principal (grain along member, oblique end)
       | vertical leg of upper factory angle
       + horizontal leg / possible upper header holes
wood header, 38.1 mm thick (grain along header)
       + horizontal leg / possible underside header holes
       | vertical leg of underside factory angle
center post (grain along member)
```

The proposed fitting for this bounded geometry screen is an unmodified ABB
AB205 with its short leg vertical and long leg on the header. ABB's nominal
fitting dimensions are **not** a timber-joint rating or verified delivered-part
tolerances. Simpson A66 remains a separate information lead: its two 3/8-in
bolts per leg are listed, but controlled factory hole centers and bolted F1/F2
ratings are unavailable. See the [G1 decision](bolted-candidate-g1-decision.json).

The proposed AB205 hole arrangement has two nominal holes in each vertical
leg and two in each horizontal leg. The opposed trial has six unique raw-wood
bore axes: two in the principal, two in the post, and two through the header
shared by the angles. These are **trial axes**, not drilling coordinates.
Existing frame-bolt axes and all 66 protected screw axes are in the
[kerf-right connection-axis export](floor-flush-construction-kerf-right/connection-axes.csv)
and [panel contract](bolted-candidate-panel-contract.json). The
[center-fit record](bolted-candidate-prototypes/ab205-center-fit.json) reports
no nominal retained-axis intersection for that shared trial, including a
63.5 mm purchased screw-length probe. That probe still uses the legacy
occupied diameter, so it cannot establish physical screw clearance. The
actual screw shaft envelope, head tolerance and installed seating projection,
stack, and tool clearance remain unresolved. A
[retailer-listed nominal 42605 head diameter](bolted-candidate-hillman-42605-dimensions.json)
is now recorded as a sensitivity input, not a verified physical envelope. The
[access record](bolted-candidate-prototypes/center-access.json) includes panel
and kicker solids but uses idealized probes.

## Two alternative hypotheses

**Shared bolt.** Upper and underside header holes coincide. At each of two
axes, one bolt passes through both steel flanges and the wood header. The
[fit record](bolted-candidate-prototypes/ab205-center-fit.json) has six unique
wood bore axes and no nominal retained-axis hit under that mixed-dimension
screen. The header bolt is one
steel/wood/steel stack with possibly unequal side actions; see the
[method gate](bolted-candidate-prototypes/center-shared-bolt-method.md).

**Front/back stagger.** Keep the top angle row fixed in the trial; move only
the underside row on the fixed post. Header bolts are distinct. The
[stagger screen](bolted-candidate-prototypes/center-y-stagger.json) finds a
conditional parallel-load row-spacing interval, but no perpendicular-load
interval within its assumed 4D band. Its midpoint is an investigation pose.
The [access screen](bolted-candidate-prototypes/center-access.json) finds one
nominal approach per row, not full assembly access.

The shared trial's short-vertical orientation has only a 9.774 mm nominal
common reversible 4D edge band before tolerances. The stagger trial retains
the same top row and has an underside conditional 4D band from -124.9 to
-86.8 mm; its greatest row separation is 29.518 mm. The conditional NDS
distinct-row minimum is 19.05 mm for the assumed parallel case and
39.688 mm for the assumed perpendicular case with 38.1 mm lesser wood bearing.
These [screen values](bolted-candidate-prototypes/center-y-stagger.json) do
not classify actual load direction, end distance, or a viable installed joint.
Neither hypothesis may shift the support members or the protected screws.

The conditional midpoint also sets a *requirement to verify*, not an allowed
shop tolerance. The fixed top row is 4.886949 mm from either end of its
nominal 4D band. The underside row is 5.233974 mm from the lower post 4D
boundary and 5.233974 mm beyond the conditional parallel row-spacing
minimum. If independent worst-case Y errors on the two rows are each bounded
by `t`, the spacing screen needs `2t < 5.233974 mm`, or `t < 2.616987 mm`;
the individual wood-edge screens, oblique end, real hole dimensions, and all
other tolerances still have to pass. Factory hole, fitting pose, timber cut,
drill placement, and service effects must share this budget. The
perpendicular-row screen has no feasible interval even at zero tolerance.

## Input and evidence ledger

- **Geometry:** Raw CAD members, oblique principal end, nominal ABB dimensions,
  and conditional bore/edge screens are known. Need delivered hole/bend/edge
  dimensions and tolerances; bolt/washer/nut envelopes; full bore, edge,
  oblique-end, contact, net-section, and adjacent-hardware geometry.
- **Material:** The [wood reference](bolted-candidate-material-basis.json) is a
  calculation basis; ABB describes hot-rolled carbon steel. Need actual lumber
  grade/condition, bolt grade and thread exposure, guaranteed fitting strengths
  and minimum base-metal thickness. Do not borrow another fitting's steel grade.
- **Resistance method:** The
  [shared-stack gate](bolted-candidate-prototypes/center-shared-bolt-method.md)
  and [single-shear helper](../mini_moonboard/bolted_steel_wood_yield.py) have
  limited scope. Classify load/grain directions and the oblique end. Analyze
  unequal shared actions as one fastener, or justify symmetric double shear.
  For stagger, check each distinct steel-to-wood path. Both need wood yield,
  splitting, net sections, steel holes/bend/prying, bolt axial/lateral
  interaction, contact, and slip checks.
- **Actual demand:** [Representative blockers](bolted-candidate-representative-blockers.json)
  contain archived wrenches only. A
  [first shared-bolt topology diagnostic](bolted-candidate-center-design-convergence.md)
  now gives simultaneous
  principal/post and shared-bolt actions for `a1-rear` at three provisional
  stiffnesses, but not qualified bolt demands. Need the other unchanged cases,
  supported slip/contact assumptions and equilibrated installed-group actions. The
  [demand worksheet](bolted-candidate-center-demand-worksheet.md) defines
  the per-case recovery. A [kerf-right numerical reference](bolted-candidate-center-design-convergence.md)
  now reports old-connector proxy actions for five converged cases, not
  new-bolt demands or a numeric required capacity.
- **Installation/access:** [Ideal access probes](bolted-candidate-prototypes/center-access.json)
  and preserved panel axes exist. Need actual grip, washers, head/nut side,
  socket/hand clearance, tightening sequence, withdrawal path, installed-panel
  service access, and tolerances without moving protected screws.

Qualified **bolted-connection** actions remain unavailable. Their derivation is:
take the same-case new-candidate force `F` and moment `M` at each present
principal/post interface; translate moments to each actual connector reference
by `M_connector = M + r × F`; solve simultaneous flange contact and bolt-group
equilibrium for each hypothesis; then check each bolt's lateral and axial
actions and the supporting wood/steel limit states. Preserve load definitions
and vary provisional contact/slip assumptions where they affect distribution.
The archived separate force and moment maxima in the
[blockers](bolted-candidate-representative-blockers.json) may be from different
cases and origins; they cannot be combined or reused as proven new demand.

## Decision boundary

Reject a **specific trial immediately** if a verified factory pattern cannot
fit the fixed raw members and protected axes with required tolerances, the
actual load-direction/end/row rules cannot be met, required hardware cannot
be installed or removed, or a supported resistance check fails. The present
conditional perpendicular-row failure rejects that stagger *under that load
classification*, not every possible joint. Unavailable material properties
or actions leave the trial open, not passed.

A complete local calculation needs a dimensioned installed detail and
material basis, same-case current-geometry actions, justified load-sharing
method, all relevant wood/bolt/steel/contact/serviceability checks, and a
verified assembly sequence. An applicable manufacturer installation could
provide a different evidence route only within its stated conditions. This
package does not release fabrication or whole-frame acceptance.
