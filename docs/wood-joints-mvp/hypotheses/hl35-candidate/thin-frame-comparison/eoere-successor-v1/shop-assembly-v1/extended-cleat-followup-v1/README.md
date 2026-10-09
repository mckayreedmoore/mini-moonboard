# Extended-cleat frame construction development

This packet describes `eoere-base-side-edge-cleats-v1`, using the reviewed
`eoere-midpoint-ready-frame-v3` axes with the optional extra grid **off**.
It updates the construction coordinates and stock plan for the shifted right
principal, three longer right rails and two extended exterior cleats. It
preserves 22 timbers, six panels, 22 angles, 100 through bolts, 100 nuts,
200 washers and 66 purchased Hillman 42605 panel/kicker screws. No model,
fastener policy or panel remedy changes here.

The usable result is a coherent nominal cutting, layout, inventory and
operation-planning packet for this revision. Four cleat/post stations have an
unresolved clearance conflict under the maximum-hole scenario; drilling those
stations remains held. Tools, delivered parts, fabrication tolerances and
current joint strength remain separate inputs. No parts have been inspected,
cut or qualified by these tables. This packet supplies no fabrication or
climbing release, physical-test prerequisite or transferred historical pass.
Start with the maintained [development summary](../../../../../../README.md)
and [joint ledger](../../../../../../completion-ledger.md).

## Current coordinates and drawings

| Record | Coverage |
| --- | --- |
| [Members](members.csv) and [profiles](current_profiles.json) | All 28 wood/panel datums, local frames, nominal blank envelopes and current saved BREP identities. |
| [End datums](member-end-datums.csv) | Raw profile vertices and end planes, including the two sloping cleat tops. Recesses and service cuts are separate. |
| [Receiver holes](receiver-holes.csv) | 120 receiver occurrences for 100 shafts; current world axes and local entry/exit coordinates. Multiple receiver rows do not mean extra bolts. |
| [Panel screw datums](panel-screw-datums.csv) | 66 axes, including the ten right-side moves from the raised-rail packet. The earlier four raised lower stations stay where they were. |
| [Panel machining](panel-machining.csv) | 142 hold/T-nut, 132 original light and 66 screw model datums. Occupied diameters are not a released bit list. |
| [Bolt stacks](bolt-stacks.csv) | Every current stack identity, receiver/fitting ownership, preserved length/shank/thread comparison and blank receiving fields. |
| [Access sides](access-sides.csv) | Current head/nut positions and directions for all 200 sides; tool and removal clearance remains unverified. |
| [Stock nesting](stock-nesting.json) | Every timber once in the same 13-stick purchase scenario, with more useful remaining lengths. |
| [Result](result.json) and [inputs](inputs.json) | Source binding, arithmetic checks, nominal mass/cost and unresolved inputs. |

The four member plates are dimensioned projections, not marking templates:
[1](member-projections-1.svg), [2](member-projections-2.svg),
[3](member-projections-3.svg), [4](member-projections-4.svg).
They show raw L/V sections; U is out of the page, so a projected target alone
does not locate a drill entry. Panel front-face L/U layouts are
[plate 1](panel-layout-1.svg) and [plate 2](panel-layout-2.svg).
Use the tables for exact point, face, axis direction and feature identity.
Drawing precision is for reproducibility; it is not a woodworking tolerance.

World coordinates are `datum + L*l + U*u + V*v`. L follows nominal timber
grain; the panel frames are geometric and do not establish observed veneer
direction. Raw end-plane equations use `normal dot local_point = offset`.
An end-plane angle is not automatically a saw setting. The source-point order
is not necessarily boundary order. Service cutters stay at their fixed world
routes when a raw rail is extended or translated.

The current finished sources compose the aligned-wire timber records, seven
v3 timber/three panel overrides and the two extended-cleat overrides. Saved
receiver interval lengths are reused only after checking each shaft's unchanged
receivers, direction, grip, diameter, plates and hardware recipe. Their positions
are translated onto the current axes, then reprojected into current member
frames. This is a nominal coordinate derivation, not a fresh BREP bearing query
or a tool sweep. The current mechanical audit retains its own evidence limits.

## Cut and stock plan

Use solid DF-L No. 2 stock under the recorded G=0.50 reference, with actual
identity, grade, seasoning and usable dimensions recorded at receipt. This
does not replace those observations. The nominal purchase scenario remains:
six 2×6×8-ft sticks, three 2×6×10-ft sticks, two 4×6×8-ft sticks and two
4×6×10-ft sticks: 13 sticks and 150 nominal board feet. Actual sections are
38.1 × 139.7 mm (1½ × 5½ in) and 88.9 × 139.7 mm (3½ × 5½ in).

The plan charges 3.175 mm (⅛ in) per output piece and 12.7 mm (½ in) trim
at **each** purchased stick end. To avoid the previous 2.649-mm tight nest,
the four posts move to the header and two split-rail sticks; the model and
finished post dimensions stay unchanged.

| Stick allocation | Nominal length | Remaining after blanks, kerfs and trims |
| --- | ---: | ---: |
| Each 4×6 side | 3048 mm / 10 ft | 448.699 mm / 17.665 in |
| Each 4×6 leg | 2438.4 mm / 8 ft | 381.362 mm / 15.014 in |
| Each 2×6 principal alone | 3048 mm / 10 ft | 486.799 mm / 19.165 in |
| Header + both outer posts | 3048 mm / 10 ft | 100.050 mm / 3.939 in |
| Top rail | 2438.4 mm / 8 ft | 152.400 mm / 6 in |
| Each runner + its exterior cleat | 2438.4 mm / 8 ft | 229.817 mm / 9.048 in |
| Bottom rail pair + left center post | 2438.4 mm / 8 ft | 46.050 mm / 1.813 in |
| Lower service rail pair + right center post | 2438.4 mm / 8 ft | 46.050 mm / 1.813 in |
| Upper service rail pair | 2438.4 mm / 8 ft | 288.125 mm / 11.344 in |

The three right split rails now require 1077.275-mm (42.412-in) blank
envelopes, 39.2 mm (1.543 in) longer than their predecessors. Their inward
ends move with the right principal; the outboard ends remain fixed. The
right principal and center post shift 39.2 mm toward the left. Header and
top-rail raw profiles stay the same; their hole positions change. Use the
current table rather than combining old holes with new holes.

Both [extended cleats](extended-cleats.svg) need a maximum grain blank of
361.186 × 139.7 × 38.1 mm (14.220 × 5½ × 1½ in). Their common Y/Z outline
is `(-175.7,139.7), (-36,139.7), (-36,500.886083), (-175.7,334.398106)` mm.
Their bottom seats on the runner at Z=139.7 mm. The rear edge is
194.698 mm (7.665 in) high and front edge 361.186 mm (14.220 in) high;
the top follows the sloping side edge. The left X band is
−1257.3 to −1219.2 mm; right is 1216.025 to 1254.125 mm.
Do not replace that sloping top with the old 289.7-mm square-ended blank.

The six existing panel outlines and CAT 23/32 model thickness
18.25625 mm remain unchanged. Actual nominal-¾-in panels are unmeasured.
The modeled main width is 1217.6125 mm (47 15/16 in), rather than
1219.2 mm (48 in); reconcile the owner's already cut panels before relying
on their edge offsets. The old three-sheet scenario does not order new
plywood. Keep whole kickers and their recorded miter/seam profiles.

## Rear recess and hand-tool method

The [dimensioned recess section](rear-recess.svg) and
[two source-bound definitions](rear-recesses.json) retain the existing
38.1-mm (1½-in) maximum removal and 457.2-mm (18-in) return. For each leg,
L starts at rear foot heel B and increases along grain. Full-depth removal
ends at L=180.342661 mm (7.100105 in); the taper ends at
L=637.542661 mm (25.100105 in). Depth is 38.1 mm below the first station,
`(637.542661-L)/12` between the stations, and zero beyond the return.
The 88.9-mm stock retains 50.8 mm (2 in) at full depth.

The left inner face is X=−1219.2 mm, with removal toward −X. The right
inner face is X=1216.025 mm, with removal toward +X. The right source cutter
already includes the −3.175-mm width correction: do not shift it again.
The recorded Z=141.7 mm is the clearance height used to establish the
taper start, **not** a horizontal plane that clips the taper. The analytic
prismatic removal agrees with each saved 2,085,056.566251-mm³ recess volume
within 0.000005 mm³. That arithmetic checks the definition, not an actual cut.

The owner has a circular saw, handheld drill, clamps and pull saw, preferring
the pull saw for 4×6 end cuts. Use the preserved
[left-corner layout sheets](../../../../../../eoere-builder-drilling-guide.md#three-printable-nominal-layout-sheets)
for those unchanged leg/runner/side raw profiles. Mark both broad faces and
the thickness faces from the same datum and retain the waste-side identity.
A rigid fence guides the cut plane; its blade/spine clearance and clamps
must suit the actual saw. The manufacturer's
[guide instructions](https://assets.contentstack.io/v3/assets/blt050573defaf102e3/bltbed03478d9ecadf2/669bdde0d01638d8da39faee/https_assets.leevalley.com_Original_10091_41718-veritas-dovetail-saw-guide-system-c-01-e.pdf?branch=production)
illustrate blade registration and waste-side layout, but their small-stock
guide does not qualify an 88.9-mm timber or this recess.

For the recess, develop supported relief kerfs across the inner face followed
by controlled hand-tool finishing. Support the leg and the entire saw shoe
on coplanar rails; locate and clamp the leg independently of those rails.
Establish the saw's depth setting from its supported reference face, leaving
positive finishing stock above the retained depth plane. At successive taper
stations, reduce the relief depth according to the depth law. Do not replace
the taper with one maximum-depth crosscut or use a tilted, unsupported shoe
to approximate it. Remove relief waste in controlled increments and finish
to the marked plane without cutting below it. A suitable chisel/rasp or plane
is an additional tool input, not an assumed item in the owner's inventory.

Set a rough relief depth from the shallowest retained depth across the entire
kerf footprint, then subtract the controlled depth error and finishing stock.
On the taper, a kerf of width k centered at a marked L extends k/2 upslope,
where the allowed removal is k/24 shallower. A 3.175-mm kerf therefore
consumes 0.132292 mm of depth allowance before other errors. The plotted
stations are finished-plane depths, not saw depth settings. Kerf width,
blade tilt and guide positioning also belong in this footprint budget.

This is a method to develop, not an executable jig qualification. The actual
saw's manual, usable cutting depth, blade/kerf, shoe dimensions, stable
supports, finishing tool and allowed finishing stock remain needed before
specifying kerf spacing or stops. The nominal 2-mm runner-top clearance and
zero transverse fit allowance are model dimensions; neither supplies a
fabrication-error budget. Matched receiver faces must seat without using
bolt tightening to draw an incorrectly cut recess into position.

## Matched drilling and tolerance disposition

The [fixture requirements drawing](paired-drilling-fixture.svg) distinguishes
the 88.9-mm (3½-in) lower runner/recessed-leg path from the 177.8-mm (7-in)
upper side/leg path. The left entry faces are X=−1219.2 and −1130.3 mm,
respectively, drilling toward −X. Both parts need independent support at
their intended contacts, positive locating stops and separate clamps.
Keep the same registered two-hole setup between holes. Drilling entry does
not reverse the installed head/nut sides.

A planning guide thickness of 19.05 mm (¾ in), plus 6.35 mm (¼ in) of
breakout/backer travel, gives usable reach requirements of 114.3 mm
(4½ in) lower and 203.2 mm (8 in) upper. These guide/backer sizes are
proposed fixture dimensions. They are not observed equipment or a statement
that an 8-in overall bit has 8 in of cutting length. Check flute/cutting
length, free projection below the chuck, bushing compatibility and the
complete chuck/clamp path. A controlled matched transfer setup is a separate
route when common-stack reach fails; independent drilling from opposite
faces is not an assumed solution.

For angle connections, register the delivered fitting to its intended faces,
then locate an independent guide. Do not use a factory angle hole as a
qualified drill bushing or drill/enlarge the steel. Four side/cleat shafts,
four cleat/post shafts and the twelve starting shafts have two timber
receivers; the other 80 angle shafts each have one. Shared-angle shafts
still count once. Keep each matched part set and its axis labels together
through dismantling; interchangeability is not established.

The pinned NDS installation basis distinguishes wood clearance holes from
factory steel holes. NDS 2018 §12.1.3.2 specifies a wood-hole oversize range
of 1/32–1/16 in, aligned holes and no forced bolt insertion.
[AWC Chapter 12](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf)
supports that installation requirement; it does not adopt a new code edition,
complete joint capacity or a delivered bit tolerance here. Thus the reference
ranges are 10.31875–11.1125 mm (13/32–7/16 in) for a 3/8-in bolt and
13.49375–14.2875 mm (17/32–9/16 in) for a 1/2-in bolt. The tables retain
each current modeled bore. No field hole is specified solely by that model.

Use a worst-case accumulated error budget, rather than assuming independent
errors cancel: registration, guide clearance/tilt, bit runout/drift, member
seating and fitting-hole variation all consume the available fit clearance.
For a fixed shaft axis the nominal radial allowance is `(bore-bolt)/2`.
The 10-mm factory hole has only 0.2375 mm radial allowance to a nominal
9.525-mm bolt; a literal 3/8-in factory hole has none. Those nominal numbers
are not guaranteed delivered limits. At 177.8-mm travel, even 0.1° of
axis tilt contributes about 0.310 mm of transverse drift before other
errors. A precise printed target does not control this drift.

The dedicated cleat/post shafts remain at Z=200 mm in the reviewed model.
Their nearest kicker screw leaves only **0.340625 mm nominal** between
the modeled bolt bore and screw envelope. At the 11.1125-mm maximum wood
hole, the geometric gap becomes **−0.05625 mm** before marking, drilling
or fitting errors. No positive tolerance allowance resolves that scenario.
Hold these four stations; do not shrink a wood hole below the installation
basis, move a Hillman screw, force a shaft or silently issue the old layout.

The existing unadopted Z=180-mm proposal lowers only the four dedicated
cleat/post bolts by 20 mm (0.787 in), preserving the 50.8-mm pitch and all
66 Hillman axes. Its saved maximum-bore screen gives 3.94375 mm clearance.
It still needs a reported geometry revision, current eight-seat/bore and
tool checks, and its own signed-load/end-distance/joint disposition. It is
not applied here. See the maintained
[clearance disposition](../../../../../../completion-ledger.md) for ownership
and the existing proposal; a geometric remedy is not a capacity result.

Keep the Hillman #10×2½-in policy separate: owner-selected 3.175-mm
(⅛-in) lead pilot, 9.525-mm (⅜-in) face countersink and #2 Phillips drive.
The 5-mm screw voids in the panel-machining table are analysis envelopes,
not screw-shank clearance-hole instructions. No insert pilots, additional
panel fasteners or panel/screw remedies are adopted.

## Hardware, mass and cost

Nominal bolt allocation remains 60×3/8×2½ in, 4×3/8×3 in,
8×3/8×4 in, 20×3/8×4½ in, 4×3/8×6 in and 4×1/2×8 in.
Use one own washer at each head and nut; retain receiver order and the
partially threaded basis. Heads are on the negative axis side, nuts on the
positive side. Shared shafts retain both fitting identities.

For each stack, record delivered underhead length L, seated receiver-plus-plate
thickness S, both washer thicknesses, nut height h and pitch p. The recorded
project target is `L >= S + w_head + w_nut + h + 2*p`. Actual free nut seating,
full-form threads through the nut, smooth-body/runout location, washer/fillet
fit, sound support and counterholding space remain separate. No torque,
preload, extra washer packing or full-thread substitution is specified.

The same 24 worst-case catalog boxes remain short: sixteen 3/8×4½-in,
four 3/8×6-in and four 1/2×8-in stacks. At the recorded maximum catalog
nut/washer stacks, their measured lengths need at least 112.268, 150.368
and 199.792492 mm, respectively. These are dimensional comparison targets,
not observations that every delivered bolt fails. Leave an incompatible
stack unassigned. Longer stock requires its own thread-bearing, seating,
tip/tool and withdrawal checks; nominal extra length does not solve them.

The 200-side worksheet updates the 22 translated bolt stations. Every
tool/removal side remains unverified; previous swept-access passes do not
transfer. Reference wrench sizes are 9/16 and 3/4 in, while saved model hex
envelopes retain their own dimensions. Actual tool wall/depth, handle sweep,
counterholding and full headward bolt withdrawal need an appropriate tool
envelope. Nut removal is nutward; the bolt withdraws toward its head.

Planning mass is **219.115940 kg** (483.068 lb), extra grid off, including
the retained 25-kg accessory allowance and excluding pads. It comprises
108.512512 kg of finished timber, 60.061258 kg of finished panels and
50.542170 kg of retained nominal hardware/service mass and allowance.
Wood density is 500 kg/m³. This is saved-volume bookkeeping, not actual
carried weight or a fresh gravity/load vector. The extended cleats alone
add 0.081687 kg over base v3.

The frozen full bolt/nut/washer basket remains $109.93, giving
`$109.93 + 6*C4 + U`, before shipping/tax. C4 is the unobserved current
four-pack angle price; U includes unpriced wood, existing purchase receipts,
services, pads, holds, tooling and other applicable items. This is the dated
comparison basket, not a live quote. The revised nesting requires no added
nominal timber sticks. Already purchased panels/screws are separate from
future spending, and unknown costs are not zero.

## Assembly and dismantling dependencies

This conditional sequence organizes the current parts. Fixture stability,
actual tools and continuous insertion/removal paths remain unresolved. The
analytical no-slip floor is not an assembly support or a verified floor.

1. Keep each member, matched partner and axis label together. Reconcile the
   current profiles, receiving rows and affected operation holds before
   relying on them. Account for all 22 timbers and six panels.
2. Independently support the runner/leg/side/post relationships at their
   recorded seats. Establish the rear recess and end geometry before matched
   drilling; bolt tightening must not correct an incorrectly seated part.
3. Locate the header, both principals and split rails from current datums.
   The right principal/post shift and longer right rails belong together;
   old and current hole patterns must not be combined.
4. Seat each exterior cleat on its runner and stage it with the sloping side.
   Its two side/angle shafts and two dedicated post shafts are distinct.
   Stage both angles at shared shafts before insertion. The four dedicated
   cleat/post stations retain the clearance hold described above.
5. Stage all 22 angles against their named receivers and preserve far-pair
   factory-hole identities, head/nut roles and two washers per shaft. Keep
   panel-facing work open for hardware, counterholding and harness access.
6. With power off, manage the existing intact harness through its retained
   front-open channels and identified disconnects. Connector dimensions,
   bend radius/slack, electrical details and staging route are unverified;
   no splice or extra-grid lighting system is inferred.
7. Plan kickers before lower main panels to engage the recorded seam, then
   upper panels. Use the current 66 Hillman rows, with their existing pilot
   policy and supported receiver identities. Keep panel/screw remedies paused.
8. Reconcile 100 bolts, 100 nuts, 200 washers, 22 angles, two cleats and
   66 screws. Record hand-starting, seating, alignment and tool observations
   against their own rows; those observations do not establish strength.

For dismantling, remove external loads and support each unloaded part before
releasing its own connections. Manage holds and the powered-off harness;
the harness must not support a released panel. Plan upper panels first,
then lower panels and kickers. The preserved upslope seam-release dependency
is useful, but its old 0.5-mm/100-mm corridors do not qualify current motion.
Stage the harness clear of shaft travel. Work one supported joint at a time:
nut and nut washer first, then headward bolt/head-washer withdrawal. A shared
shaft releases both attached angles. Free cleats only after dedicated and
side/angle shafts are clear, then release the starting frame stacks with
both receiver members supported. Separate 22 timbers, six panels and
22 angles individually and retain labeled hardware sets. No connected
transport assembly, lift capacity or actual carried weight is claimed.

## Exact missing inputs and next actions

| Input or disposition | Needed action | Actual | Disposition |
| --- | --- | --- | --- |
| Four dedicated cleat/post axes | Resolve the maximum-hole conflict; report/review a geometry change before altering this model. | | |
| Drill, circular saw, pull saw and bits | Owner make/model; bit diameter, cutting length and usable chuck projection; saw blade, kerf, shoe and cutting capacity. | | |
| Finishing tool and fixtures | Identify available chisel/rasp/plane; dimension support, bushings, clamps and stops against those tools. | | |
| Cut/hole/seat uncertainty | Allocate measured or controlled bounds against each actual interface; no general tolerance adopted. | | |
| Wood and panels | Actual usable sizes, grade, seasoning, existing panel width/thickness and factory direction. | | |
| Angles and 100 hardware sets | Controlled minimum heel thickness/radius/material; delivered holes, shank/thread/runout, nuts, washers and seats. | | |
| All 200 tool/removal sides | Check complete tool, counterhold and withdrawal envelopes; retain incompatible affected-operation holds. | | |
| Current mechanics | Parent-owned matching response and complete joint method disposition; no historical six-case transfer. | | |
| Harness, mass and prices | Identified existing components/routes and receipts; actual observations stay blank until supplied. | | |

The current-revision construction records stay active with the development
summary and ledger. Earlier shop packets, rejected geometry trials and raw
attempts stay recoverable; this task grants no pruning authority. Bulk browser
captures and interim exports remain in ignored
`fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/current-shop-followup-v1/`.
The permanent companions retain only the reproducible current tables and
SVGs, not copied CAD, meshes, installations or supplier manuals.

## Reproduction

Run the stdlib byte replay from the repository root:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/export.py --check
```

For a separate reproduction use `--out NEW_EMPTY_DIRECTORY`; it rejects an
occupied directory before generating outputs. The helper authenticates source
pins before/after, checks current axis/receiver/grip joins, plane/coordinate
round trips, the analytic recess volume and unique stock coverage. It imports
two pinned existing stdlib datum/drawing helpers and executes no CAD or solve.

`check-drawings.cjs SOURCE_DIRECTORY NEW_CAPTURE_DIRECTORY` renders the nine
saved SVGs through the existing shared Playwright/Gwen runner with Bun, checking
XML, text bounds and source bytes. The default shared dependency is the sibling
`gwen` checkout; `GWEN_BROWSER_ROOT` can select another existing installation.
No browser page-code evaluation or new dependency installation is required.
