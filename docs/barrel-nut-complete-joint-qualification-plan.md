# Barrel-nut complete-joint qualification plan

Prepared 22 September 2026 for
`compact-floor-flush-bolted-development`. This plan covers only failure modes
that the candidate's documentary mechanics and controlled product evidence
cannot close. It does not authorize a physical test, supplier contact,
fabrication, installation, climbing, or release. It does not select a proof
factor, allowable-value divisor, statistical coefficient, specimen count, or
load magnitude.

The selected `compact-floor-flush-development` angle frame remains the project
authority. Results produced under this plan would apply only to the frozen
barrel-nut candidate revision, tested materials, declared conditioning, and
supported assembly/reassembly scope.

The current [selected qualification stack](barrel-nut-selected-hardware.md)
uses STAFAST `JCD14201606NL ZN` barrels and CDE `1456BHT5` / `1472BHT5` /
`1480BHT5` / `14104BHT5` fully threaded Grade 5 bolts,
and Fastenal `33857` hardened washers. Selection fixes test articles only. It
does not close the missing barrel, lot, fit, stiffness, or joint-strength
evidence and does not authorize purchase or testing.

## 1. Purpose and qualification boundary

The qualification program must answer two different questions:

1. What complete-joint resistance is supported for each applicable failure
   mode and geometry-critical variant under the candidate's signed combined
   actions?
2. What clearance, seating, stiffness, opening, slip, rotation, unloading,
   and reassembly behavior may be used in the six-case response model?

Qualification is a last evidence route, not a substitute for missing geometry,
unknown demand, or readily applicable calculations. Before specifying a test,
the resistance ledger must assign each mode at each station to one of:

- applicable published evidence;
- geometry-specific mechanics using controlled inputs; or
- this complete-joint qualification route.

Constituent tests may diagnose a mode, but only a complete joint containing the
actual wood cuts, contact faces, bolt, barrel, washer, thread engagement, fit,
grain directions, and eccentricities may qualify the unresolved complete path.
A hardware tensile test, isolated barrel pull, ordinary lateral-bolt result,
single exploratory peak, or full-frame proof does not replace this program.

The current modes most likely to need qualification are:

- female and male thread engagement as installed, barrel wall/net-section
  behavior, local thread loading, and barrel flexure;
- barrel-to-wood bearing, splitting, edge/end breakout, shear-out, and
  interaction with the insertion bore, bolt bore, head pocket, and nearby
  service cuts;
- head/washer seating, wood crushing, pull-through, pocket breakout, and
  interaction with thin residual wood;
- combined tension, shear, bending, eccentric moment, contact opening, and
  unequal sharing within two-row joints;
- the single-bolt principal/header joint's signed moment and twist path;
- seating, hole play, slip, rotation, residual set, and stiffness in each
  relevant direction;
- damage or loss of fit, engagement, stiffness, or resistance over the exact
  declared disassembly/reassembly scope; and
- the complete kicker-backing transfer path where the four unchanged kicker
  screws feed the two center posts and their post/header barrel joints.

If controlled product evidence or applicable calculations later close a mode,
remove that mode from the test scope with a dated evidence-ledger entry. Do not
reduce specimen coverage after seeing favorable test results.

## 2. Preconditions before a qualification program is issued

No qualification load schedule may be finalized until all of these inputs are
frozen:

1. Candidate source commit, source hashes, assembly hash, station register,
   units, exact cut solids, and machine-readable configuration fingerprint.
2. All six signed candidate cases: A12 left, A12 rear, A12 forward, K12 right,
   K12 rear, and A1 rear, including application points, gravity/equipment,
   stand-off, dynamic assumptions, and the no-slip analytical floor condition.
3. A converged response and signed-action ledger for all 24 interfaces and 46
   barrel pairs. Conditional stiffness sweeps may bracket demand, but old angle
   forces and preliminary component scales may not set qualification loads.
4. One coherent hardware specification for each bolt-length family, barrel,
   and washer, including the features that receiving inspection must measure.
   The selected STAFAST barrel has nominal geometry but no public controlled
   tolerance, internal-thread, material-minimum, or resistance basis.
   Qualification therefore remains lot-specific and cannot support untested
   replacement lots or silent substitutions. CDE certificates and Class 2A
   confirmations and the Fastenal washer MTR must also be tied to tested lots.
5. Wood specification and receiving rules: species, grade, moisture/service
   condition, treatment/incising status, minimum actual sections, grain
   orientation, excluded defects, and any permitted defect distribution.
6. Drill, counterbore, insertion-bore, washer-seat, and assembly tolerances,
   including the actual fit range rather than the viewer's zero diametral
   insertion allowance.
7. Intended installation endpoint and inspection method. Torque alone may not
   be treated as known clamp force unless a supported torque/preload relation
   is part of the frozen method.
8. Numerical acceptance limits for strength, slip, rotation, opening,
   permanent set, damage, engagement, and reassembly. These limits must come
   from the frozen demand and serviceability basis, not observed results.
9. A named statistical/design-value method, target population, confidence and
   reliability basis, duration/service adjustments, and specimen count derived
   prospectively from that method.
10. A frozen control mode, loading/unloading rate or time history, holds,
    post-installation dwell, test duration, and rules prohibiting unplanned
    retightening. These must support any proposed duration adjustment.
11. An independent test-safety and fixture review. The guarded execution
    requirements in
    [owner-barrel-load-test-readiness.md](bolted-candidate-prototypes/owner-barrel-load-test-readiness.md)
    remain applicable.

If any item is absent, method-development work may be planned, but specimens
remain exploratory and cannot support `bn_complete_joint_test_acceptance`.

### 2.1 Exploratory response stage before qualification-load freeze

The response inputs and demand-derived qualification loads must not be defined
from each other circularly. Before finalizing the qualification load schedule,
run a separate, nonqualifying response-characterization stage under its own
reviewed protocol, or establish a conservative action envelope that does not
depend on an assumed candidate joint response.

The exploratory stage must:

1. cover every geometry, fit, installation, conditioning, action direction,
   and reassembly state that may govern response, including the
   principal/header, 5 in top-outer, and 6 1/2 in outer-rail exceptions;
2. use staged force-controlled paths with prospective fixture, instrument,
   damage, and travel stop limits; initial loads must come from an independent
   safe test bound, not from the unresolved candidate demand;
3. measure deadband, seating, opening/reclosure, row sharing, coupled
   stiffness, unloading/reloading, residual set, and specimen variability;
4. derive predeclared adverse lower and upper response envelopes without
   strength or qualification credit, then rerun all six candidate cases with
   both bounds; and
5. expand the characterized action range under a revised exploratory protocol
   if any resulting candidate action or deformation lies outside it. If safe
   expansion is not supported, the response and affected demands remain
   `UNRESOLVED`.

As an alternative, a prospective mechanics bound may set qualification loads
only if it envelopes all physically admissible stiffness, clearance, contact,
and row-sharing states without using preliminary component scales or legacy
angle-frame forces. Document why every omitted state is bounded. Freeze the
resulting signed action histories before fabricating strength-qualification
specimens. Exploratory specimens and results do not count toward the required
qualification population, and favorable exploratory behavior may not reduce
the frozen strength or serviceability envelope.

## 3. Critical geometry and action variants

The frozen station register must map every station to a tested variant or to a
written, conservative equivalence demonstration. Similar bolt diameter or wood
section alone is not equivalence. The comparison must cover grain direction,
cut geometry, edge/end distances, row pitch, contact lever arm, load direction,
thread engagement, fit, eccentricity, and failure-mode opportunity.

At minimum, the variant census must address these current exceptions:

| Variant | Current critical features | Required coverage |
| --- | --- | --- |
| Single-bolt principal/header | One angled CDE `1472BHT5` 4.5-inch bolt per side; 2.092 mm nominal head-pocket edge stock; 588.180 mm² of cut contact face behind the bolt line; shifted STAFAST barrel recessed more than 41 mm; isolated face-normal twist mode | Both mirrored stations unless equivalence is demonstrated; both signed opening/twist senses; actual contact face, 25.4 mm candidate service passage, head pocket, Fastenal `33857` washer, and full shifted barrel insertion path |
| Center post/header and kicker transfer | Two CDE `1456BHT5` 3.5-inch rows at 35 mm pitch per post; two fixed kicker screws enter each post; unequal row action depends on screw location and face contact | Complete screw-to-post-to-header assembly; governing individual screw action and combined screw actions; both signed moment senses and contact states; actual post grade, section, cuts, and grain |
| Recessed outer header/post | Two CDE `1472BHT5` 4.5-inch rows at 50 mm pitch; 6.35 mm nominal pocket side stock; rim-first access sequence | Left and right or proved mirror equivalence; both moment senses; minimum residual pocket stock and unfavorable Fastenal `33857` washer tolerances; assembled contact and service sequence |
| 6 1/2-inch outer-rail rows | Twelve CDE `14104BHT5` rows across bottom, lower, and upper outer-rail duties; selected axial screen covers the modeled barrel body, but needs 10.4408 mm added bore depth for zero adverse tip clearance or 12.4408 mm for the provisional 2 mm reserve; final clearance and usable STAFAST female engagement remain unknown | Each distinct grain/contact/action orientation or a conservative equivalence; minimum usable engagement; unfavorable axial fit, final deeper blind bore, and positive tip clearance; both shear signs and combined moment sharing |
| N = 42 mm left center-rail rows | Lower-left and upper-left first rows moved beside former service conflicts; 6.641 mm nominal gap | Actual adjacent service cut and blind bores; changed net sections and ligaments; signed action that loads the reduced side; tolerance-extreme geometry |
| Top-outer rows | Four CDE `1480BHT5` 5-inch bolts; the current 2 mm nominal extension leaves only 0.1204 mm adverse clearance before machining error and a deeper blind bore remains to be frozen | Longest permitted bolt and shallowest permitted final bore combination; bottoming and far-wall/thread exit behavior; governing tension/shear/contact action |
| Remaining two-row families | Base-center, base-outer, bottom/lower/upper center, top-center, and other outer-rail duties not bounded above | Family-specific grain, row pitch, edge/end distance, cuts, engagement, bearing face, and signed combined-action envelope; omission allowed only through documented conservative bracketing |

Tolerance specimens must deliberately represent adverse permitted combinations,
including largest permitted wood removal, smallest residual ligament, smallest
usable thread engagement, greatest allowed hole clearance, least favorable
barrel-axis position, and washer-seat eccentricity. Nominal specimens alone
cannot qualify a tolerance range. Impossible or mutually exclusive tolerance
combinations must be handled by a documented tolerance study, not assembled as
an artificial worst case.

Any later hardware, bore, washer, bolt-length, member, service-cut, or station
revision requires an applicability review. A change outside the tested
envelope reopens the affected qualification row.

## 4. Specimens, lots, fabrication, and conditioning

### 4.1 Population and lot control

Define the population before procurement. Record manufacturer, exact SKU,
production/packaging lot, markings, coating, dimensions, material evidence,
and source for every bolt, barrel, and washer. Record lumber supplier, species,
grade stamp, moisture, section, growth orientation, and visible defects for
every wood component.

The statistical plan must calculate specimen count from its predeclared
one-sided population-bound method and target confidence/reliability. It must
also state how many independent hardware and lumber lots it needs and how each
variant is blocked across those lots. Replicates cut from one timber or one
hardware package are not automatically independent. If available material
cannot satisfy the derived count or lot coverage, the result remains an
exploratory, lot-limited dataset.

Define the population cells before deriving that count. Geometry variant,
hardware and lumber lot, conditioning, installation/preload state, clearance
state, reassembly state, and action history can each define a different
population. Each state claimed directly must receive the replication required
by the selected method. A prospectively specified covariate, factorial, or
hierarchical model may share information across states only when its form,
minimum cell coverage, interactions, and validation checks are frozen before
testing. One adverse-tolerance or reassembled specimen cannot establish a
population value by itself. Sparse or unsupported state cells remain
`UNRESOLVED`.

STAFAST `JCD14201606NL ZN` lots must not be pooled merely because the product
number matches. Either establish exchangeability from measured features and
material evidence using the predeclared rule, or derive separate lot-specific
results. The same trace rule applies to each selected bolt and washer lot.
Weak specimens and unfavorable lots stay in the dataset unless a documented
fixture or instrumentation fault invalidates the run.

### 4.2 Specimen geometry and fabrication record

Each specimen must reproduce enough connected member length and boundary
condition to develop every applicable split, breakout, group, contact, and net
section mode without fixture reinforcement. Preserve actual:

- member sections, grain directions, end/edge distances, row spacing, and
  eccentricities;
- bolt bore, barrel insertion bore, blind depth, counterbore/head pocket,
  washer seat, service passage, and nearby structural cuts;
- contact-face dimensions and surface preparation;
- bolt length, body/thread location, barrel orientation and internal-thread
  span, washer stack, and measured engagement; and
- drilling jig, bits, entry face, installation tools, sequence, and permitted
  field inspection method.

Assign unique IDs before fabrication. Preserve as-built measurements, photos,
material/lot traceability, deviations, and disposition. Qualification
specimens use the proposed DIY process, not precision machining unavailable to
the builder, unless the eventual packet requires and controls that process.

### 4.3 Conditioning

Freeze the candidate's claimed service condition first. Condition wood to the
declared moisture/environment range and verify stable specimen mass or another
predeclared equilibrium criterion. Record temperature and relative humidity
during conditioning, fabrication, assembly, and test. Place geometry variants
and material lots across conditioning blocks rather than confounding one
variant with one condition.

If the design claim covers more than one moisture or temperature condition,
test or otherwise support each bounding condition. Do not apply an unstated
adjustment to extrapolate from laboratory-dry specimens. Hardware corrosion or
coating exposure belongs in scope only if the intended service claim includes
it and a predeclared conditioning method exists.

Separate method-development specimens from qualification specimens. Pilot
results may refine fixtures and instrumentation, but may not enter the
qualification population. Freeze the final procedure and analysis script
before testing qualification specimens.

## 5. Installation, preload, clearance, and reassembly states

Record before loading:

- actual bore diameters, locations, angles, depths, runout, and surface damage;
- barrel OD/length, thread-axis position, usable female span, and orientation;
- bolt length, body/thread transition, usable male thread, tip geometry, and
  measured engagement without counting incomplete threads or chamfers;
- washer ID/OD/thickness, pocket diameter/depth, bearing support, and seat
  eccentricity;
- free clearance in each relevant translation and rotation before seating;
- installation tool, sequence, turns engaged, endpoint, and any measured
  torque, bolt elongation, or direct preload; and
- initial face gaps and contact state.

Use the exact intended installation rule. Qualification must include the low
and high installation/preload states permitted by that rule, plus unfavorable
allowed clearance states. If preload cannot be measured or bounded, results
must retain installation endpoint as a categorical variable and the response
model may not assume clamp friction.

Hole play and seating are response, not data cleanup. Capture deadband before
engagement, direction-dependent pickup, contact closure/opening, hysteresis,
and residual offset after unloading. A tightened specimen may not be described
as zero-clearance unless measurements show that behavior under the relevant
signed action.

Freeze the exact reassembly claim before testing: permitted number of
disassemblies, which components may be reused, whether bolts/barrels/washer
positions may be swapped, inspection/rejection rules, and installation
endpoint after each assembly. Derive reassembly cohorts and sequence from that
claim. Include virgin and maximum-claimed-reassembly states without using one
damaged specimen to stand for statistically independent replicates. Record
thread damage, bore enlargement, crushing, splits, lost engagement, preload
change, stiffness/slip change, and extraction difficulty after every cycle.
No result supports more cycles than the frozen tested scope.

## 6. Signed actions and combined loading

Use one common local datum and axis convention between the native model,
station register, fixture design, and result files. For every station and load
case, retain the signed interface tuple

`(N, V1, V2, M1, M2, M3)`

plus individual bolt/barrel row forces, contact resultants, and the location at
which they are reported. Preserve signs; absolute maxima assembled from
different cases are not a physical load combination.

For each variant, preserve the full analysis loading history that produces each
same-case tuple: installation/preload, gravity and equipment seating, then the
case action and any reversal. Build an action envelope from all mapped
stations, cases, histories, and accepted stiffness/clearance bounds for
screening, but do not assume its convex hull bounds a path-dependent joint.
Test each distinct governing history or a predeclared history shown to be
conservative for it. Include actual interior tuples where clearance pickup,
contact opening/reclosure, row sharing, preload loss, or prior damage can make
an envelope vertex nonconservative. Include:

- axial separation and compression/contact seating where applicable;
- shear in both relevant local directions and both signs;
- both moment senses about axes that alter row sharing or open the face;
- simultaneous force and moment at their same-case ratios;
- reversed action where clearance, damage, or one-sided contact changes the
  path; and
- the governing kicker-screw force and moment transfer for the center backing
  assembly.

Do not qualify combined action by testing each component independently and
adding capacities. Do not apply all component maxima simultaneously unless
that tuple is an actual case or a predeclared conservative envelope point.
Do not replace the gravity-first case history with a proportional ramp to the
same final tuple unless a frozen mechanics demonstration establishes that the
path is conservative.
Fixtures must introduce loads through the same members and lever arms as the
candidate without bypassing the barrel path, bracing a possible split, or
creating uncredited face clamping. Measure parasitic actions and include them
in the signed action tuple.

Strength specimens must reach the predeclared endpoint needed by the chosen
statistical/design-value method, including controlled loading beyond the
acceptance action when destructive response is required. Serviceability
specimens follow predeclared load steps, holds, reversals, and unload/reload
paths tied to candidate demands. Freeze actuator control mode, ramp rate or
time history, time-to-target, hold duration, unload rate, interval between
cycles, post-assembly dwell, and total test duration. Record relaxation during
the dwell; do not retighten unless retightening is an explicit frozen step in
the proposed DIY procedure. No climber is a test load.

## 7. Instrumentation and data acquisition

The instrumentation plan must resolve applied actions and local joint behavior
independently of actuator crosshead travel. At minimum provide:

- calibrated force measurement over the used range and fixture geometry or a
  multi-axis transducer sufficient to recover all applied force and moment
  components;
- synchronized displacement measurements on both members to obtain local
  normal opening, two in-plane slips, and relative rotations at the interface;
- local measurements that distinguish bolt/head/washer seating, barrel motion,
  wood embedment, and gross member/fixture compliance where those components
  affect the intended stiffness model;
- a preload measurement or the frozen installation endpoint and its recorded
  observables;
- continuous time, force, displacement, and environmental records at a rate
  able to capture sudden slip and brittle failure; and
- scaled photographs or video of both faces, pockets, bore regions, contact
  gaps, cracks, and permanent deformation before loading, at declared holds,
  after unloading, and after disassembly.

Digital image correlation, extra displacement channels, strain gauges, acoustic
monitoring, or instrumented fasteners may be required where the base channels
cannot separate row sharing, narrow-strip contact, hidden barrel motion, or
split initiation. Their need must be resolved in pilot work before procedure
freeze.

Document calibration/verification, range, resolution, uncertainty, alignment,
sampling rate, filtering, zeroing, channel synchronization, and raw-data
retention. Apply fixture-compliance correction only through a predeclared,
independently measured method. Preserve both raw and corrected data.

## 8. Test sequence and observations

For each frozen specimen cohort:

1. Verify identity, conditioning, as-built geometry, engagement, tip reserve,
   barrel orientation, washer seating, initial damage, and fixture alignment.
2. Apply a low-load fixture/path check below the predeclared qualification
   range. Confirm equilibrium and absence of unintended restraint or contact.
3. Measure unloaded play and seating response in every action direction needed
   by the specimen's signed path.
4. Apply the frozen service sequence, including holds, reversals, unloading,
   and reloading. Record slip, rotation, opening, stiffness, hysteresis,
   residual set, row sharing, contact changes, and damage observations.
5. For the assigned cohort, perform the frozen disassembly/reassembly sequence,
   repeat the prescribed measurements, and record all fit or damage changes.
6. Apply the frozen combined-action strength path to its declared endpoint.
   Do not change the load ratio in response to observed weakness.
7. Unload when safe, quarantine the specimen and all hardware, inspect hidden
   surfaces and threads, and assign observed failure modes without discarding
   secondary damage.

Record first seating, first visible damage, first crack, proportional-limit or
other predeclared stiffness transitions, service-limit crossing, peak action,
action at required displacement/rotation points, residual deformation, and
test termination. For destructive cohorts, state before testing which specimen
events are measurements through which controlled loading may continue, the
terminal failure definition, and the safety conditions that override that
endpoint. Define treatment of right-censored and safety-aborted results in the
statistical plan. Definitions and extraction algorithms must be frozen before
qualification data are opened.

## 9. Acceptance and statistical derivation

### 9.1 Predeclared specimen acceptance

Each valid specimen must meet the frozen, demand-derived requirements for:

- same-case combined strength;
- service slip, rotation, opening, and residual set;
- absence of prohibited cracking, splitting, thread damage, washer/pocket
  failure, barrel movement, or engagement loss below the applicable action;
- required unloading/reloading behavior; and
- required post-reassembly fit and performance.

A run stopped by genuine specimen cracking, sudden slip, hardware movement, or
other joint behavior is a result, not an invalid test. Only a documented
fixture, control, instrumentation, or specimen-identity error may invalidate a
run. Replacement rules must be written before testing.

### 9.2 Population resistance

Before testing, select a recognized statistical framework suited to the design
format and target population. For each unpooled critical variant and failure
mode:

1. define the strength metric and any censored-result treatment;
2. derive sample size from the chosen one-sided confidence/reliability target;
3. freeze distributional assumptions and goodness-of-fit checks, or select a
   nonparametric order-statistic method and its required count;
4. account for hardware and lumber lots through the predeclared blocking or
   random-effects method;
5. calculate the lower population bound without deleting weak valid results;
6. apply only documented duration, moisture, service, normalization, and
   resistance/allowable-format adjustments that are applicable to this joint;
   and
7. record both raw population bound and final candidate resistance with every
   adjustment and source visible.

The numerical coefficient and specimen count belong in the later signed
protocol after its statistical authority is chosen; this plan intentionally
does not invent them. A sample mean, minimum divided by an arbitrary factor,
or selected peak is not an allowable resistance. Pool variants only when the
predeclared equivalence and statistical tests support pooling; otherwise use
the weaker separately derived result for the mapped stations.

Candidate resistance passes only when its documented design/allowable value
exceeds the governing same-case demand under compatible units and design
basis, so utilization is at most 1.0. No favorable average may override a
predeclared individual damage or serviceability limit.

### 9.3 Stiffness, clearance, and reassembly derivation

Retain full action-displacement histories. Derive model inputs over the actual
candidate demand range, not from a secant to peak load. For each needed action
direction and assembly state, extract:

- free-play/deadband bounds and engagement points;
- seating branch, engaged loading branch, unload/reload branches, and residual
  offset;
- normal, two-direction shear, and rotational stiffness or a coupled response
  surface where independent springs are not valid;
- contact opening/reclosure thresholds and row-sharing evolution;
- specimen, lot, conditioning, fit, preload, and reassembly variability; and
  correlations needed to avoid impossible combinations of bounds.

Use a predeclared population-bounding method to produce lower and upper
response envelopes. Feed both adverse bounds into sensitivity cases; do not
replace them with a mean spring. If data show pinching, degradation,
directionality, or coupled action, implement that behavior or retain a
conservative envelope that bounds it. Any extrapolation beyond tested action,
geometry, condition, or reassembly range remains `UNRESOLVED`.

## 10. Stop, invalidate, and revision rules

Stop the current run immediately for these rig, control, or containment events:

- fixture movement, unintended restraint/contact, loss of alignment, or a
  reaction path that bypasses the intended joint;
- load, displacement, synchronization, or environmental-channel failure;
- approach to machine, fixture, guard, travel, or instrument limits;
- unplanned barrel rotation/pullout, bolt bottoming, washer escape, or member
  contact that lies outside the frozen specimen endpoint;
- fragment release, loss of control, or any crack, split, sudden slip, or load
  loss that reaches a predeclared rig-safety threshold; or
- any condition in the approved test-safety plan requiring shutdown.

During a destructive strength cohort, an expected crack, split, slip, barrel
movement, or loss of joint resistance is recorded as specimen behavior and may
be followed only to the frozen terminal endpoint when the approved fixture,
guarding, travel, and control plan explicitly permits it. Serviceability and
non-destructive cohorts stop at their first prohibited specimen event. Safety
always overrides data collection.

After a stop, unload safely, preserve raw data and parts, photograph the state,
and classify the event. Fixture/instrument faults trigger root-cause review and
the frozen replacement rule. Joint behavior remains a valid failure unless
evidence proves the setup invalid.

Pause the whole qualification program when:

- an unanticipated failure mode appears;
- as-built measurements fall outside the frozen candidate or test envelope;
- action/reaction or moment balance falls outside the predeclared tolerance;
- a hardware or wood lot lacks required identity;
- a result challenges the assumed fixture equivalence or response-model form;
  or
- an interim review is required by the predeclared statistical plan.

Do not loosen acceptance limits, change load ratios, pool variants, add
specimens opportunistically, or modify exclusion rules after results are
known. A changed method starts a named revision; state whether previous data
remain applicable before combining them.

## 11. Feeding results into candidate mechanics

Qualification output must be source-bound and machine-readable. For every
specimen preserve identity, geometry, lots, conditioning, installation state,
action path, raw channels, processed response, observed modes, validity, and
analysis-script version. The signed report must then update:

1. **Resistance ledger:** mode-by-mode characteristic/test basis,
   design/allowable derivation, adjustment sources, applicability envelope,
   mapped station variants, and governing utilization.
2. **Joint behavior law:** clearance, tension/contact engagement, coupled
   stiffness bounds, unloading/reloading, residual set, row sharing, and the
   supported reassembly state.
3. **Geometry and inspection limits:** bore, pocket, engagement, barrel axis,
   tip clearance, washer seat, wood condition, and rejection thresholds that
   the DIY packet must control.
4. **Evidence ledger:** exact files and hashes closing each applicable row in
   [barrel-nut-criteria.md](barrel-nut-criteria.md), especially
   `bn_stiffness_clearance_basis`, `bn_complete_joint_evidence_route`,
   `bn_complete_joint_test_acceptance`, and the affected complete-joint modes.

Insert the supported behavior law into the candidate solver and rerun all six
signed cases. Because stiffness, clearance, contact, and row sharing change
demand, repeat the resistance comparison until the frozen demand/resistance
iteration is stable under the predeclared rule. Rerun mesh/contact and behavior
bounds. Recheck all twelve retained frame bolts and every affected timber
section under the new demands; their old passes do not transfer.

If any modeled action or deformation leaves the qualification envelope, the
affected result is `UNRESOLVED`, not capped at the largest tested value. A
passing coupon program still cannot close unrelated floor support, member,
panel stock, LED passage, tool access, or delivered-build observation gates.

## 12. Required qualification deliverables

Before any result can be considered in candidate acceptance, retain:

- frozen protocol and amendments, signed before qualification testing;
- candidate/station/variant coverage matrix;
- hardware, lumber, fabrication, conditioning, and installation records;
- fixture drawings, free-body diagrams, calibration and uncertainty records;
- raw synchronized data, photos/video, and quarantined-part inspection records;
- immutable processing scripts and independently reproducible result tables;
- statistical report with exclusions, invalid runs, lot effects, assumptions,
  and sensitivity checks;
- resistance and behavior-law files with explicit applicability limits; and
- independent mechanics and test-method reviews with dispositions.

Until these deliverables exist and all affected criteria pass, status remains
`UNRESOLVED`. No physical test, hardware purchase, candidate promotion,
fabrication release, or climbing claim follows from this planning document.
