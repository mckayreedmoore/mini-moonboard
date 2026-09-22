# Owner-review barrel-nut viewer — full inventory, geometry REVISE

The [interactive rear view][scene] is a kerf-right *comparison concept*, not a
cut, drilling, purchased-hardware, fabrication, or structural release. It
replaces the **visuals** of all 24 historical structural angles and 144 SDS
fasteners with 48 diagnostic 1/4-20 bolt paths and 48 provisional Hillman
880543-shaped barrel envelopes. No corner-block fallback solids are in this
scene.
The original 66 panel/kicker screws and 12 frame bolts remain; both original-
width center posts are shown at the owner-approved X = ±180 mm with two
separate kicker screw backers. The backers are not structurally attached by
this concept. The historical angle assembly remains the selected baseline.

The [source-bound scene](../../scripts/export_owner_barrel_scene.py) is a
reviewed snapshot. Its published JSON is checked against the source-built
scene and page digest; the current revision has not yet passed a fresh visual
browser smoke check. Barrel and bolt paths are diagnostic X-ray overlays;
red means `REVISE`, not a strength rating. Hide panels in
the visibility controls and zoom in to inspect crowded joints. Alt-click
selects an internal joint for its warning. This scene is generated independently
of the corner-block assembly; both views share only the original frame and
owner-approved center-post/backer placement.

The integrated assembly shows 24 direct-bore *trials*, not 24 accepted joints.
This scene now illustrates three bounded geometry revisions: the two
right-center rail stations use a 50/92.25 mm row pair found in the
[rail-position probe](owner-barrel-rail-clearance-probe.md); both
center-principal/header stations use the [4 in nominal bolt and 22 mm
trial washer](owner-barrel-center-viewer-revision.md); and the two outer-base
stations move their bolt axes [10 mm inward](owner-barrel-outer-base-clearance-probe.md).
The previous 5 in center bolt broke out of receiving wood. The 22 mm washer
is **not a selected retail product**. Every station remains `REVISE`; the
changed drawings are not complete joints or a drilling plan.

The two outer-header/post duties still have installed-shaft and straight
access clashes with the side rims at the drawn pose. A separate
[outer-header search](owner-barrel-outer-header-clearance-probe.md) found
no clear pose among 24 bounded top, angled, and reverse-entry trials. A
separate [post-shift screen](owner-barrel-outer-header-post-shift-probe.md)
found that the shift needed to clear the rim abandons fixed kicker-screw
and rail-front-bolt receivers, so moving only the posts is not a solution.
A different modeled joint topology or access sequence is required. An
[exact-frame outer/top screen](owner-barrel-outer-top-protected-probe.md)
and individual producer notes remain relevant to the original poses; do
not transfer their negative collision results to revised geometry without
the revised whole-frame screen.
The revised integrated cross-family screen found no positive-volume **physical**
or drill/access intersections among its supplied finite solids. It is a
limited screen: same-family contacts, protected
hold/T-nut/LED/wire features, the 66 screws and 12 original frame bolts,
full hardware heads/washers at every duty, and actual driver sweeps are not
cleared by this whole-frame test. Individual producer notes record their
own identified conflicts: [rail ten](owner-barrel-rail-layout.md),
[center six](owner-barrel-center-layout.md), and
[outer/top eight](owner-barrel-outer-top-layout.md).

The SKU appears at [Lowe's][lowes] and [Home Depot][depot], but the
16.002 mm length, 10.0076 mm OD, and **assumed** 8.001 mm end-to-thread-axis
position are only provisional viewer inputs. The 6–10 mm axis-offset
sensitivity is open. The actual barrel material/grade, internal thread
strength, bolt grade and grip, usable engagement, tip clearance, washer
bearing, wood edge/end/net-section resistance, splitting and group action,
insertion/retention, repeated disassembly, backer attachment, and complete
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

[scene]: https://mckayreedmoore.github.io/mini-moonboard/?model=owner-barrel-layout&view=rear
[lowes]: https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559
[depot]: https://www.homedepot.com/p/202242356
[hillman-answer]: https://www.lowes.com/questions/hillman-880543-specialty-nuts/3012559/0d07d7d4-94c9-59c7-b300-30a2fd0be7bd
