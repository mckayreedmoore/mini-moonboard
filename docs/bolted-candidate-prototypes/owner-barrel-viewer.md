# Owner-review barrel-nut viewer — integrated center-post trial

The [integrated owner decision sheet](owner-barrel-integrated-owner-review.md)
summarizes all 24 modeled connections, the partial cost scale, and the next
physical-layout approval. This longer note preserves the supporting scene
history and geometry limits.

The [interactive rear view][scene] is a kerf-right *comparison concept*, not a
cut, drilling, purchased-hardware, fabrication, or structural release. Two
seam-side 88.9 × 139.7 mm modeled base-center posts replace the former X =
±180 mm posts **and** both separate kicker backers. Those two wood-colored
posts receive the four fixed center kicker screws. The original 66
panel/kicker screws and 12 frame bolts retain their axes. The scene hides the
24 historical angles and 144 SDS fasteners and displays 46 diagnostic 1/4-20
bolt paths with 46 provisional Hillman 880543-shaped barrel envelopes. No
corner-block or separate-backer solids remain. The historical angle assembly
remains the selected baseline, not a release for this candidate.
The [integrated backing trace](../../scripts/owner_barrel_integrated_backing.py)
ties those four purchased-length kicker screws to the two widened posts and
each post to two modeled post/header barrel pairs. This closes the *geometric*
receiver inventory, not screw holding capacity, post/header resistance,
or the complete backing load path.
The modeled post section is **not** a verified delivered 4×6 size: the
[ordinary retail leads](owner-barrel-center-post-retail.md) list green
approximately 90.5 × 142.9 mm stock, and local price, grade stamp, moisture,
cuttable offcuts and finished dimensions remain unconfirmed.

The [source-bound scene](../../scripts/export_owner_barrel_scene.py) is a
reviewed snapshot. Its published JSON is checked against the source-built
scene and page digest. The integrated revision also passed a local headless
browser render on 22 September 2026; this is a display check, not a physical
fit check. Barrel and bolt paths are diagnostic X-ray overlays;
red means `REVISE`, not a strength rating. Hide panels in
the visibility controls and zoom in to inspect crowded joints. Alt-click
selects an internal joint for its warning. Each bolt warning shows both the
fully-threaded geometric ceiling and a separate **19.05 mm nominal end-thread
comparator**; the latter comes from a documented Grade 5 bolt family, not
from the unverified retailer bolts in the price basket. The family-specific
trial lengths give positive nominal body overlap at all 46 pairs in that
comparator, but not verified usable engagement. It is a purchase/fit alert,
not a delivered-hardware verdict. This
scene is generated independently of the corner-block assembly.
The viewer now replaces all 16 timber meshes that contained old angle/SDS
holes with source-built visual timber. The 144 old SDS bore cuts are excluded;
66 fixed panel-screw receiver cuts, eight retained frame-bolt receiver cuts,
and inherited service cuts are replayed where they affect those timbers.
All 98 modeled barrel drilling paths are now represented by trial cuts in
the replacement timber, including the outer-header and center joints. A
path may cut more than one member; the source report records each host and
checks that it matches its intended entry/receiver members. The F1–G1
passage shown in the right
principal is provisionally 25.4 mm at the inherited axis, not the selected
baseline's 38.1 mm. Bolt and barrel hardware remains an X-ray overlay. These
display solids are not a shop machining model or wood-strength approval.
The complete cut inventory exposes two additional `REVISE` intersections:
the lower-left and upper-left *center* rail-station machine bores intersect
inherited service bores `..._054` and `..._055` in their respective left
rails, about 320.5 mm³ each in the nominal solids. These are actual
candidate-cut/service-void overlaps, not a claim of electrical fit or a
complete wood-section failure. The affected rail joints need a revised path
or a justified wood/service treatment before any drilling schedule.

The integrated assembly shows 24 former-angle direct-bore *trials*, not 24
accepted joints. Provisional head and washer solids accompany all 46 bolts.
These are modeled envelopes, not
controlled retail dimensions or verified seats.
This scene now illustrates four bounded geometry revisions: the two
right-center rail stations use a 50/92.25 mm row pair found in the
[rail-position probe](owner-barrel-rail-clearance-probe.md); both
center-principal/header stations now use the
[single-centered-barrel candidate](../../scripts/owner_barrel_center_single_layout.py)
with two 3½ in post/header bolts and one centered 4½ in principal/header bolt
per side. The latter uses a 19.05 mm trial washer envelope and recessed,
50° header-rear entry. A single barrel's moment transfer depends on the
connected contact/load path and is not yet verified. These are unselected
hardware dimensions, not drilling instructions. The two outer-base
stations move their bolt axes [10 mm inward](owner-barrel-outer-base-clearance-probe.md).
The four outer-header bolts use the
[conditional recessed-head trial](owner-barrel-outer-header-recess-probe.md):
the rear row remains at Y = −135 mm and the forward row is provisionally at
Y = −85 mm in this viewer. The default producer still uses Y = −75 mm.
Their shaft starts are 6.651 mm lower, with provisional head and washer
envelopes inside magenta wireframe counterbores. The candidate visual timber
for `base_header` and both outer posts is cut-derived; its trial bores and
header counterbores are subtracted. The source baseline timber and fixed axes
are unchanged. The 25.4 mm diameter and 6.651 mm depth are not drilling
dimensions. The installed side rim no longer overlaps the modeled
stack, but still blocks the modeled driver. The
[rim-first sequence probe](owner-barrel-outer-header-sequence-probe.md)
finds a possible dependency order, not a verified physical removal route.
The [rail-to-rim service screen](owner-barrel-rim-rail-service-probe.md)
finds no nominal straight-path obstacle at the six bottom/lower/upper outer
stations with rims installed; it does not verify delivered heads, barrel
extraction or a real tool sweep.
The historical [top/outer-base service screen](owner-barrel-rim-outer-top-service-probe.md)
used the 48-pair outward-post scene. Re-running the same finite operations
against the **current 46-pair integrated assembly**, with provisional heads
and washers at every row, finds no modeled straight-path obstacle at those
four rim-attached stations. The outer-base barrels have 46.449 mm nominal
entry recesses and still need a real insertion, alignment, retention and
removal method.
For conditional removal, unload and independently support the board and panels.
Per rim, temporarily undo eight rim-receiver panel screws, two original leg/rim
frame bolts, and ten trial bolts at the five rim-touching stations. Withdraw
the rim, then operate the recessed header/post bolts. Conditional installation
reverses this order: operate the header/post bolts with the rim absent, fit the
rim, then reconnect on the original fixed axes. The
[historical retained-hardware rim-withdrawal screen](owner-barrel-rim-withdrawal-hardware-probe.md)
used the outward-post composition. The **integrated 46-pair rerun** finds no
intersection at 33 isolated positions on either side after the specified
temporary fastener removals. Its retained inventory includes 36 barrels and
108 bolt-stack solids per side, including all modeled heads and washers.
The [current swept-box certificate](../../scripts/owner_barrel_rim_withdrawal_hardware_probe.py)
also bounds **every intermediate straight-line pose** from 0 to 160 mm.
On both sides, that conservative box is disjoint from all retained barrels,
bolt stacks, and protected fixed envelopes after the specified removals.
It overlaps other timber bounding boxes, so it cannot certify continuous
wood-to-wood clearance; the 33-position wood intersection test remains only
sampled evidence. The viewer therefore still records `sampled_nominal_only`,
not an operational pass. Delivered hardware, tools, barrel extraction, safe
support, wood sweep and repeated service remain unverified.
Actual delivered hardware, repeatable access and header net-section capacity
remain open. The head, washer and recess colors distinguish diagnostic parts,
not approved hardware.
The [detached nominal cut-solid screen](owner-barrel-outer-header-cut-integrity.md)
finds the header and outer posts remain single solids after the modeled
recess/bores. The viewer exports the header's finite continuity and nominal
edge/floor stock diagnostics beside its cut-derived mesh: one valid connected
solid, 6.35 mm minimum radial edge stock and 31.449 mm counterbore floor.
These are geometry measures, not net-section resistance or cut approval. The
outer-post bores are also visible in the candidate cut-derived timber.
The current Y = −85 mm forward row leaves a measured 12.706 mm
between each post cut and the nearest fixed kicker screw envelope. This
nominal gap is a `REVISE` finding, not clearance or wood-strength approval.
The [forward-row sensitivity](owner-barrel-outer-header-row-shift-probe.md)
uses the current Y = −85 mm viewer as its source and compares Y = −75,
−80, and −90 mm alternatives. The current pose has 24.600 mm between
counterbores; it remains provisional and `REVISE`.
The [connector inventory](owner-barrel-native-connector-inventory.md)
now defaults to this integrated 46-pair pose; the
[standalone installed-stack note](owner-barrel-installed-stack-audit.md)
still defaults to the superseded outward-post pose. The integrated scene exporter
passes its own assembly into the same axial-audit helper and finds all 46
tips reach an *assumed* barrel center with no modeled bore overruns. The eight formerly overrun
center-rail bores now have 16.7 mm nominal tip clearance after an owner-approved
depth revision and a shorter trial shaft, as do the four recessed outer-header bores. All 46 have provisional
heads and washers; delivered thread span, usable engagement, bore-tip
clearance, and complete joint resistance remain open.
The [current 46-pair reach table](owner-barrel-integrated-stack-audit.md)
separates nominal reach from physical fit: four top-outer tips end at their modeled bore
caps with zero nominal clearance; 12 outer-rail tips pass the assumed axis
by only 1.849 mm. Earlier service probes also used the older 48-pair pose.
The earlier two-row center [conditional numerical screen](owner-barrel-integrated-center-prelim.md)
is historical component sensitivity, not a rating for the single-row joint.
The [current integrated two-joint screen](owner-barrel-integrated-preliminary.md)
reports conditional rail and single-center component numbers without
claiming complete joint resistance or new-topology demand.
The [current retail hardware leads](owner-barrel-integrated-center-hardware.md),
[partial cost](owner-barrel-integrated-cost.md), and
[load-test readiness gates](owner-barrel-load-test-readiness.md) are separate:
none closes the barrel/thread, wood breakout, tolerance, or global-demand gaps.
The detached [6/7 in length screen](owner-barrel-outer-rail-bolt-length-probe.md)
finds 6 in still short and a 7 in nominal tip 12.2452 mm past the modeled
barrel's far wall. Neither is selected hardware; a longer bore and tip
clearance would need separate verification.
The [60 mm setback screen](owner-barrel-outer-rail-setback-probe.md)
led to the depicted six-rail provisional revision: twelve 6 in shaft paths
reach their assumed axes by 1.849 mm, with head/washer envelopes now shown.
Thread, tolerance, service, and capacity checks are still open.
The older 5 in center bolt broke out of receiving wood; its 22 mm washer
trial is superseded. The subsequent two-row integrated replan reported
`CLASH`: the inherited 38.1 mm service bore intersected center hardware,
and a 20 mm driver did not fit its 19.05 mm header pocket. That pose is
preserved for comparison, not displayed. The current centered single-row
candidate and provisional 25.4 mm passage remove the modeled collision;
the principal has 14.046 mm nominal barrel X-edge ligament. The header
pocket has only 2.092 mm nominal edge stock and the barrel recess exceeds
41 mm. Actual LED-strand feeding, barrel placement/orientation, full-thread
engagement, wood strength, moment transfer and reassembly remain open. The
viewer is not a complete joint verdict or drilling plan.

The two outer-header/post duties had installed-shaft and straight
access clashes with the side rims at the unrecessed pose. The recessed trial
addresses only the installed-shaft clash conditionally. A separate
[outer-header search](owner-barrel-outer-header-clearance-probe.md) found
no clear pose among 24 bounded top, angled, and reverse-entry trials. A
separate [post-shift screen](owner-barrel-outer-header-post-shift-probe.md)
found that the shift needed to clear the rim abandons fixed kicker-screw
and rail-front-bolt receivers, so moving only the posts is not a solution.
A [whole-post section screen](owner-barrel-outer-header-wide-post-probe.md)
likewise found no clear pose among 12 ordinary-lumber trials: a rotated
2×6 loses Y row/receiver support, a 4×6 lacks the modeled tool corridor,
and a 6×6 hits protected kicker hardware.
A physically verified access sequence is still required. An
[exact-frame outer/top screen](owner-barrel-outer-top-protected-probe.md)
and individual producer notes remain relevant to the original poses; do
not transfer their negative collision results to revised geometry without
the revised whole-frame screen.
The revised integrated cross-family screen found no positive-volume **physical**
or drill/access intersections among its supplied finite solids. It is a
limited screen: same-family contacts, protected
hold/T-nut/LED/wire features, the 66 screws and 12 original frame bolts,
delivered head/washer fit at every duty, and actual driver sweeps are not
cleared by this whole-frame test. Individual producer notes record their
own identified conflicts: [rail ten](owner-barrel-rail-layout.md),
[center six](owner-barrel-center-layout.md), and
[outer/top eight](owner-barrel-outer-top-layout.md).
The newer [revised outer/top finite screen](owner-barrel-revised-outer-top-probe.md)
includes provisional heads/washers and the current recessed-header viewer
pose. Its only reported unrelated-wood intersections are the four installed
side-rim/driver paths; absence of other nominal hits is not a delivered-fit
or service release. The [2024 NDS applicability review](owner-barrel-nds-applicability.md)
separates usable wood/lateral-bolt subchecks from the unqualified barrel,
thread, axial and complete-joint paths. A [historical-load ranking](owner-barrel-legacy-demand-priority.md)
prioritizes new analysis without adopting old bracket forces for this frame.

The SKU appears at [Lowe's][lowes] and [Home Depot][depot], but the
16.002 mm length, 10.0076 mm OD, and **assumed** 8.001 mm end-to-thread-axis
position are only provisional viewer inputs. The 6–10 mm axis-offset
sensitivity is open. The actual barrel material/grade, internal thread
strength, bolt grade and grip, usable engagement, tip clearance, washer
bearing, wood edge/end/net-section resistance, splitting and group action,
insertion/retention, repeated disassembly, center-post joint resistance, and complete
changed-topology load cases remain unverified. A nominal bore intersection
does not imply a usable or load-bearing joint. Do not drill or buy
construction hardware from this scene.

A bounded public-source check found [Hillman's answer on Lowe's listing][hillman-answer]
for the nominal OD, length and 1/4-20 thread, but no controlled end-to-thread-
axis dimension, tolerance, material minimum, or part-specific load test.
Home Depot calls this SKU [“Not Graded”][depot]. Other ordinary retail
lengths and cross-dowels did not supply the missing controlled geometry *and*
joint-relevant resistance together. This is a limit of the public material
checked, not proof that no unpublished drawing or test exists; no manufacturer
was contacted. A different product's drawing or tensile value cannot be
transferred to this wood joint.

The [two-concept comparison](owner-two-concept-comparison.md) is for choosing
which *development direction* to study next, after viewing both scenes. A
choice would not authorize fabrication or climbing.

An inactive original-post trial kept X = ±70 mm and omitted the backers.
Those posts receive the four fixed center kicker screws and avoid the
KICK5/KICK6 T-nut steel, but leave 49–53 mm between their inner edges and
the kicker seam. Its inherited center/header bolt stacks intersect opposite
timber, and a barrel-tool path intersects the provisional hold-bolt rear
projection at KICK5/KICK6. It is not the active layout or a support solution.

[scene]: https://mckayreedmoore.github.io/mini-moonboard/?model=owner-barrel-layout&view=rear
[lowes]: https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559
[depot]: https://www.homedepot.com/p/202242356
[hillman-answer]: https://www.lowes.com/questions/hillman-880543-specialty-nuts/3012559/0d07d7d4-94c9-59c7-b300-30a2fd0be7bd
