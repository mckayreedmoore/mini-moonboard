# Integrated barrel layout: load-test readiness

22 September 2026; source revision `a74c3547`. **No physical load test or
candidate-specific structural pass was found in the inspected source.** This
is a readiness checklist, not a test instruction, drilling schedule, load
rating, or permission to climb.
The selected `compact-floor-flush-development` angle frame remains separate.

## What the present evidence can and cannot do

The [integrated viewer source](../../scripts/export_owner_barrel_scene.py)
models two seam-side 88.9 × 139.7 mm center posts, four fixed kicker screws
received by those posts, 66 unchanged panel/kicker screw axes, 12 retained
frame-bolt axes, and 48 provisional bolt/barrel pairs at 24 former-angle
stations. There are no separate kicker backers. The
[center-joint replan](../../scripts/owner_barrel_center_post_joint_replan.py)
now reports `CLASH`: its initial protected and new-hardware checks missed an
inherited service bore in the right principal and a driver wider than the
modeled header pocket. The 4×6 post screw backing remains modeled, but these
two center-joint conflicts must be redesigned before the layout is a viable
physical test specimen. It explicitly reports no native solve or structural
capacity.

The nominal [installed-stack audit](../../scripts/owner_barrel_installed_stack_audit.py)
can be run with the **integrated** assembly supplied to it; the viewer does so
for 48 pairs. Passing an assumed barrel midpoint and modeled bore cap is only
geometry. The separate [published audit note](owner-barrel-installed-stack-audit.md),
[native connector inventory](owner-barrel-native-connector-inventory.md), and
[two-joint preliminary calculation](owner-barrel-mvp-preliminary.md) describe
the earlier outward-post/backer pose. Their counts, station assignments,
historical force scales, and constituent numbers must not be treated as an
integrated-layout demand or resistance result. New calculations may now
inventory the integrated 24 stations, check exact bore/wood sections and
conditional 2024 material inputs, and plan signed force cases. A positive
CAD gap, constituent estimate, or old ML24Z force is not a proof load.

These remain **exact current blockers**:

- No delivered, traceable bolt/barrel/washer set or controlled Hillman 880543
  barrel thread-axis tolerance, usable internal thread span, material minimum,
  or part-specific resistance. The [retail evidence](owner-barrel-retail-thread-evidence.md)
  concerns the older stack; the revised 4 in post/header and 5 in / 4½ in
  principal/header entries need a new exact-SKU and delivered-stack record.
  The latter nominal tips extend about 20.345 and 7.645 mm beyond the modeled
  barrel's far wall, so the delivered cross-thread must permit that passage;
  a blind internal thread would invalidate the pose.
  Retail grade filters and bolt grade do not rate the buried barrel or wood.
- The [center replan](../../scripts/owner_barrel_center_post_joint_replan.py)
  uses a 19.05 mm trial washer and pocket, but its driver envelope is 20 mm:
  the tool still intersects header wood after that pocket is cut. The right
  principal's inherited `bore_base_principal_center_right_072` overlaps the
  second new barrel. The same replan has an approximately
  1.049 mm barrel recess in each principal receiver. The
  [viewer note](owner-barrel-viewer.md) reports approximately 0.71 mm between
  the closest modeled tool paths. Delivered heads, washers, drivers, bore
  placement, insertion, withdrawal and residual wood have not been checked
  through a tolerance stack or a repeatable assembly operation.
- Modeled 4×6 posts are 88.9 × 139.7 mm; the
  [retail wood leads](owner-barrel-center-post-retail.md) list larger, often
  green stock. Delivered section, grade stamp, moisture, defects and usable
  offcuts are unknown. Nominal support at the kicker seam is not an as-built
  measurement.
- The outer-header [recess](owner-barrel-outer-header-recess-probe.md) leaves
  only modeled residuals; its installed rim blocks the driver. The
  [rim-first sequence](owner-barrel-outer-header-sequence-probe.md) and
  [retained-hardware samples](owner-barrel-rim-withdrawal-hardware-probe.md)
  are conditional, not a continuous, delivered-tool or supported-panel service
  demonstration. The [cut screen](owner-barrel-outer-header-cut-integrity.md)
  reports 6.35 mm header side stock and a 12.706 mm outer-post-cut to fixed
  screw gap, both `REVISE` findings, not strength or tolerance approval.
- No signed, same-case interface forces/moments, load sharing, joint
  resistance/stiffness, or accepted six-case response exists for this
  integrated 24-station topology. The selected baseline's six-case pass and
  any other candidate's native result do not transfer. The
  [NDS applicability review](owner-barrel-nds-applicability.md) explains why
  ordinary lateral-bolt checks do not rate the full axial barrel-to-wood path.

## Gate C: begin **non-climbing, sacrificial joint coupon** work

An exploratory coupon can measure behavior with an *unknown* strength. It
cannot be called a proof or used to accept a joint. Before applying force:

1. Freeze a named joint and purpose: start with the integrated post/header
   and angled principal/header families, then the outer-header and governing
   rail duties. Record revision, member pair, grain direction, face contact,
   full bore/pocket geometry, bolt/barrel rows, eccentricity and installation
   order. Identify all critical failure paths, including bolt and thread,
   barrel wall, barrel-to-wood bearing/breakout, washer seat, split/net section
   and group action. An isolated fastener pull is not a complete two-row joint.
2. Obtain and log the **actual test lot**: exact SKUs and lot/packaging,
   bolt grade marking and material evidence (or their absence), head/shaft/thread runout and
   delivered length; barrel OD/length, hole/axis offset, internal-thread
   location and usable depth; washer ID/OD/thickness and material; lumber
   species/grade stamp, moisture, dimensions and defects. Measure the worst
   fit specimens and record bore/pocket and assembly tolerances. If grade or
   barrel strength remains undocumented, label this lot *exploratory only*;
   do not infer a qualified minimum from a retailer label. Reject specimens
   that cannot be assembled with documented measured thread engagement and
   without bottoming, breakout or an unrecorded substitution.
3. Prewrite the coupon matrix and load path. Include axial separation,
   lateral actions in the relevant grain directions, reversed directions,
   and combined/eccentric force plus moment where the two-row station needs
   it. Use actual bearing faces and holes; fixture reactions must enter the
   same members and must not bypass the barrel or add uncredited clamping.
   Record specimen count, conditioning, installation/reassembly cycles,
   loading rate, increments, holds, maximum machine travel/force, and the
   intended failure observations **before** seeing results. Exploratory
   machine limits are rig-safety limits, not joint acceptance values.
4. Use a rated, restrained fixture with captured fragments and a remote
   operator, guarded exclusion zone, overload/travel limits, and a way to
   unload after a split or sudden release. Verify the machine/fixture load
   path at low force without a specimen failure. Calibrate/verify the force
   channel over the used range, and measure relative joint slip and each
   member's motion independently of crosshead travel. Photograph and record
   holes, seating, splits and fastener deformation before, during and after.
   [ASTM D5652][d5652] is a useful *method comparison* for complete wood
   connections, but its smooth-shank single-bolt scope does not qualify this
   two-row barrel joint; [ASTM E4][e4] addresses testing-machine force
   verification. No standard is asserted as adopted for this custom coupon.
5. Predeclare aborts: any fixture movement or unintended restraint, load-cell
   or displacement-channel failure, unplanned barrel rotation/pullout,
   cracking or sudden slip, fastener bottoming, unanticipated member contact,
   or approach to rig limits stops the run.
   Quarantine failed parts and preserve force–displacement traces and photos.

For a **demand-representative or proof coupon**, add a frozen integrated
same-case action envelope, justified specimen/lot sampling and statistics,
and written numerical acceptance values for strength, slip, permanent set,
damage and repeated assembly **before testing**. Derive the test force and
method from those demands and a stated safety/adjustment basis; do not choose
a multiplier here. Test results and apparent peak loads are not design values
without that method, the complete joint, and the governing failure modes.

## Gate F: begin a **non-climbing full-frame** proof test

Gate C's exploratory results alone are insufficient. Unloaded fit/rig checks
may proceed earlier; begin a loaded full-frame proof only after:

1. Freeze one complete as-built frame, hardware and cut schedule. Inspect and
   record every actual member, grain/grade/moisture/defect, joint location,
   bore and pocket, washer bearing face, bolt and barrel engagement, retained
   frame bolt, all 66 fixed screw axes, panel/hold protection, LED/wiring
   clearance, and repeatable assembly/service access. Resolve failed fits;
   no unmeasured field reaming or hardware substitution.
2. Obtain a source-bound integrated response for the six adopted case
   identities (A12 left/rear/forward, K12 right/rear, A1 rear), with their
   actual signed vectors, application points, gravity, contact and load
   combinations. Resolve the new station forces/moments and weakest complete
   joint in each case; account for unequal row sharing, clearance and
   opening/contact. Qualify all 24 joint duties and wood cut sections with
   appropriate calculations or relevant complete-joint evidence. Recheck the
   retained 12 frame bolts and the unverified floor support/stability path.
   Old angle-case forces or a single nominal coupon must not set this load.
3. Issue a written frame test plan **before rigging**: case sequence, force
   vector/application fixture, load steps and holds, maximum force/travel,
   unloading and inspection points, repeats, and numeric limits for joint
   slip, residual deformation, frame drift, panel/hold movement, opening,
   uplift and floor movement. State the analysis-to-test comparison and
   acceptance method. No magnitude, duration, factor or rating is supplied
   by the current viewer.
4. Use dead weight or a controlled actuator, **never a climber**. Support the
   rig and restrain falling/overturning pieces independently; guard the area
   and operate remotely. Measure applied load and direction, key joint slips,
   frame deflections/racking, floor reactions/uplift and catch/restraint load.
   A safety catch must be slack in a valid free-standing stability test; if it
   engages, record a failed/invalid free-standing case rather than claiming
   the catch as unseen floor resistance. Verify instrument range/calibration,
   synchronized recording and fixture equilibrium before the first increment.
5. Stop immediately for crack/split, sudden slip or permanent drift beyond
   the predeclared limit, bolt/barrel/head/washer movement or damage,
   unexpected contact or loss of floor bearing, catch engagement, failed
   sensor/fixture, exceeded rig limit, or divergence from the planned load
   path. Unload and inspect; do not resume by merely increasing a threshold.

Passing a non-destructive frame proof on one specimen would establish only
the documented setup and tested actions. It would not establish a population
rating, fatigue/repeated-demounting life, all hold configurations, or a
fabrication/structural/climbing release.

## Shortest path from this revision

Resolve the inherited service-hole/barrel and driver/pocket conflicts first.
Then freeze the integrated source and per-station stack list; obtain and measure
one coherent hardware/wood lot; close its tolerance and service sequence;
write a guarded, sacrificial two-row center-joint coupon plan and run
exploratory tests. In parallel, calculate signed actions for the **new**
24-station topology and close all joint/wood/floor paths. Only then set
coupon proof values and a non-climbing full-frame protocol. Until these gates
are met, preparation and preliminary calculations may continue, but physical
proof claims and all release flags remain **closed**.

[d5652]: https://store.astm.org/d5652-21.html
[e4]: https://store.astm.org/standards/e4
