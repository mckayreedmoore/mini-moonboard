# Current compact bolted-frame builder plan

Use this guide with the [revision index](development-revisions.json),
[combined geometry receipt][combined] and [member/receiver coordinates](builder-layout.md).
It describes **`eoere-single-leg-bolts-header-angles-v3`**, extra grid off.
The [viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-leg-header-frame-development&view=rear)
shows one bolt at each long-leg joint, two additional under-header angles,
single plywood cleats and the retained enclosed LED passages.
The retained post detail comes from `eoere-4x6-front-posts-v1`; the enclosed
passages come from `eoere-centred-enclosed-passages-v1`.

These are conditional nominal planning records. Changed joint/member strength,
physical stiffness/restraint, installation and actual tools/stock/floor remain
unqualified. Fresh conditional calculations do not constitute a fabrication
or climbing release. Leave all Actual/Disposition cells blank until observed.
The selected screw/ML24Z baseline and historical plans keep separate authority.

## Controlling records

| Operation | Use | Superseded instruction |
| --- | --- | --- |
| Raw blanks, datum faces and angled ends | [Current profiles][profiles], [members][members] and [layout](builder-layout.md); retained [end datums][ends] and [projections][projections] for unchanged members | The two old solid-timber cleats become factory plywood leaves. Other member lengths and sections are retained. |
| Through-bolt coordinates | [112 current receiver rows][holes] and [96 drilling rows][drilling] | Omit `lumber_leg_bolt_left/right_2` and `rail_rear_bolt_left/right_2`. Do not drill the old Z200 cleat row. |
| Two new under-header angles | [Combined receipt][combined] and [96 stack selections][hardware] | Install one beneath the header beside each outer post. Share its header pair and its lower cleat/post pair; do not add a separate third cleat row. |
| Plywood and shared lower pair | [Material basis](plywood-cleat-material-basis-v1.json), [profiles][profiles] and [layout](builder-layout.md) | Use four holes per leaf: two at Z342.0875 and two at Z173.8125. The rejected six-hole proposal is inactive. |
| LED passages and panel holes | [32 retained passage datums][passages], [section](enclosed-passage-study.svg) and retained [panel datums][panels] | All front-open notches are superseded by enclosed Ø38.1-mm passages. F1–G1 stays shifted 40 mm along its receiver. |
| Panel/kicker screws | The retained 66 world axes in the [combined receipt][combined] and original [support table][screws] | No screw is added by this revision. The 98-screw comparison is separate and unadopted. |
| Access and assembly support | Current [engineering ledger](../wood-joints-mvp/completion-ledger.md#single-bolt-leg-joint-review) and retained [installation study][installation] within its source limits | The old 200-side access table does not qualify the changed plywood, under-header plates or new outward stacks. |

## Parts, stock and hardware

The installed inventory is **20 sawn members, two plywood cleats, six climbing
panels, 24 Eoere angles, 96 bolts, 96 nuts, 192 washers, 24 factory spacers and
66 Hillman 42605 screws**. Hold/T-nut hardware, lights and cables retain their
separate specifications. Six existing four-packs supply all 24 angles.

All raw blank dimensions below are **millimetres**, using the current US stock.
Preserve the given geometry; decimal places are not machining tolerances.
An angled raw blank can be longer than its final grain-axis extent.

| Member IDs / group | Quantity | Raw length × depth × thickness |
| --- | ---: | ---: |
| `base_floor_left/right` runners | 2 | 1815.646483 × 139.7 × 38.1 |
| `base_header` | 1 | 2435.225 × 139.7 × 38.1 |
| `base_post_center_left/right` | 2 | 238.9 × 139.7 × 38.1 |
| `base_post_outer_left/right` | 2 | 238.9 × 139.7 × 88.9; solid 4×6 |
| `base_principal_center_left/right` | 2 | 2532.626012 × 139.7 × 38.1 |
| Left bottom/lower-service/upper-service rails | 3 | 1041.25 × 139.7 × 38.1 |
| Right bottom/lower-service/upper-service rails | 3 | 1077.275 × 139.7 × 38.1 |
| `base_rail_top` | 1 | 2257.425 × 139.7 × 38.1 |
| `base_side_left/right` sloping sides | 2 | 2570.726012 × 139.7 × 88.9 |
| `lumber_leg_left/right` long support legs | 2 | 2028.462988 × 139.7 × 88.9 |
| `eoere_cleat_left/right` factory plywood leaves | 2 | 609.6 × 203.2 × 28.575; strength axis along 609.6 |
| Four main climbing panels | 4 | 1217.6125 width × 1219.2 height × 18.25625 |
| Two whole kickers | 2 | 1217.6125 width × 277 height × 18.25625; retain the miter |

Cleat plywood is **APA Rated Sturd-I-Floor 48 oc PS 1, at least five plies**,
with the recorded Group 1 bearing basis. Proposed minimum actual thickness is
27 mm; the material is unobserved. The 18.25625-mm climbing-panel material is
a different specified part and does not supply these cleats.

Retain the outer posts' **9.525 × 9.525-mm, 45° full-height corner bevel** for
kicker T-nut clearance. Its local corner is (U88.9,V139.7) on the left and
(U0,V139.7) on the right, through L0–238.9. The old square-post projections
omit this cut. Retain the long legs' existing **1:12 rear recesses** and soles.

The existing sawn-stock allocation is 13 sticks / 150 nominal board feet:
six 2×6×8-ft, three 2×6×10-ft, two 4×6×8-ft and two 4×6×10-ft. The two outer
posts remain allocated to the long-leg offcuts. Removing the timber cleats
creates additional unused 2×6 material; it does not authorize shorter members
or a smaller purchase without a revised nesting record. Two factory plywood
cleat blanks are additional material. No actual usable-stock survey is recorded.

Use [all 96 stack selections][hardware]. The twelve revised stacks are:

| Duty | Quantity | Nominal bolt underhead | Nut-side factory spacers |
| --- | ---: | ---: | ---: |
| Upper side/plywood cleat shafts, axes 067/070/071/074 | 4 | 177.8 mm (7 in) | Two 12.7-mm pieces each |
| Lower angle/post/plywood shafts, `cleat_post_bolt_*` | 4 | 177.8 mm (7 in) | Two 12.7-mm pieces each |
| Shared upper/lower header shafts, axes 081–084 | 4 | 88.9 mm (3½ in) | One 12.7-mm piece each |

Four retained front stacks use one further 12.7-mm spacer each, giving 24
pieces overall. Keep each bolt's own head washer, nut washer and matching nut.
Do not replace spacer lengths with extra washers. Partial-thread Grade 5 bolts
are the basis; nominal length is not a delivered smooth-shank measurement.
Catalog dimensional windows do not verify actual thread runout, seating or tools.
The preceding dated hardware basket excludes these substitutions, four omitted
leg bolts, added angles/spacers and cleat plywood; it is not a current total.

The single-bolt section calculations assume fresh stock without the four
omitted bores. Previously bored members require their own net-section check.

The owner-selected **SendCutSend sourcing fallback** remains if the primary
[Amazon Eoere listing](https://www.amazon.com/dp/B0C7V7VS89) disappears. Its
October 14 representative 22-angle quote is historical, not a 24-part quote
or a qualified drawing for the current eight-hole angle. Factory angles remain
primary; custom fallback geometry/material and complete-joint checks stay open.

## Layout and supported assembly

1. Label every member and datum face before transferring marks. Use the
   [per-member L/U/V layout](builder-layout.md); L follows timber grain or
   the cleat plywood strength axis. The header uses U across its 139.7-mm
   depth and V across its 38.1-mm thickness. Do not mirror the unequal left
   and right rails or the right principal's retained 39.2-mm shift.
2. Retain the original angled ends, whole kickers, T-nut clearances and
   [recess profiles][recess]. Support both sides of cuts and use independent
   clamping and positive registration. The retained 4×6 saw-access route uses
   a pull saw; actual tools and cut accuracy remain unobserved.
3. Use the current bolt table, not old hole drawings. Retain only `*_1` at
   each upper long-leg and leg/runner joint. The left leg enters at U=50.8 and
   exits at U=0; the right leg enters at U=38.1 and exits at U=88.9. Register
   the actual recessed face. Paired receivers share one supported, clamped
   setup; a single axis still needs aligned receivers.
4. The two lower angles use the same nominal 88.9-mm-leg, 6.35-mm-thick
   factory-angle scenario as the other angles. Seat their horizontal legs
   under the header and vertical legs against the inner outer-post faces.
   Use their far factory holes and the shared axes in the layout. Leave near
   factory holes unused. The lower plywood/post pair is at Z173.8125, with
   heads at the inner plate and nut/spacers outward beside the plywood.
5. The structural bolt bore choices remain 13/32 in for 3/8-in bolts and
   17/32 in for 1/2-in bolts. CAD occupied diameters and modeled shaft lengths
   are analysis envelopes. Use the selected stack lengths and keep observation
   cells blank. The new angle/plywood tool, guide, counterhold and removal
   paths still need their own installation conclusion.
6. Feed the intact harness through the retained enclosed passages before
   closing obstructing assembly stages. Do not add the old open notches,
   splice the harness or move endpoints. The route budget is a nominal
   geometric result; physical feeding has not been verified.
7. Retain the 66 Hillman screws and their purchased-screw/owner-selected
   pilot-plus-countersink policy. Use the [existing screw record][screws]
   with the retained world axes. Do not transfer another brand's resistance
   or installation rules to Hillman or add insert pilots.
8. Keep temporary support and bracing until both side frames, runners,
   header, all permanent joints and panels are secured in the intended order.
   One bolt supplies no independent rotational fixing. Do not rely on an
   incomplete side frame or loosen a loaded connection for assembly/service.

A failed adopted criterion, missing load path, incompatible part or contradictory
instruction holds the affected operation. Read the [current engineering status](README.md)
before interpreting these nominal records as a build decision. No cut, drilling,
load test, inspected floor or climbing release is supplied by this guide.

[combined]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/geometry.json
[profiles]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/current_profiles.json
[members]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/members.csv
[hardware]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/hardware-selection.csv
[holes]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/receiver-holes.csv
[drilling]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/drilling-requirements.csv
[passages]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/enclosed-passages-v1/passage-datums.csv
[ends]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/member-end-datums.csv
[projections]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/README.md#current-coordinates-and-drawings
[recess]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/rear-recess.svg
[panels]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/panel-machining.csv
[screws]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/README.md#matching-current-records
[installation]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/README.md
