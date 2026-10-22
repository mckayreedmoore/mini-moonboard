# Current compact bolted-frame builder plan

Applies to **`eoere-paired-frame-retained-2x6-A574-v2`**, extra grid off.
Use the [revision index](development-revisions.json), [current receipt](paired-frame-v2/geometry.json),
[member/receiver coordinates](builder-layout.md) and [current engineering disposition](README.md).
The [viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-retained-2x6-frame-development&view=rear)
shows the retained 2×6 frame, paired cleats and the current 102 bolt stacks.

These are conditional nominal design and shop-planning records. The declared
[conditional frame evaluation](paired-frame-v2/engineering-evaluation.json) is complete. Panel/Hillman strength work is explicitly deferred and unresolved;
that decision supplies no panel, screw or whole-wall strength pass. Actual stock,
hardware, tools, cuts and floor remain unobserved. No fabrication or climbing release
is established. The selected screw/ML24Z baseline retains its separate authority.

## Controlling records

| Operation | Current record | Required interpretation |
| --- | --- | --- |
| Timber blanks, datums and ends | [Members](paired-frame-v2/members.csv), [profiles](paired-frame-v2/current_profiles.json), [layout](builder-layout.md) | Current US stock; all cutting/layout dimensions in millimetres. Angled raw blanks include the retained cutting allowance. |
| Through-bolt holes | [130 receiver rows](paired-frame-v2/receiver-holes.csv), [102 drilling rows](paired-frame-v2/drilling-requirements.csv) | Use each member's own L/U/V frame and its actual finished entry face. The first four omitted second-leg axes stay omitted. |
| Upper long-leg joints | `lumber_leg_bolt_left_1` and `lumber_leg_bolt_right_1` in the current layout | These axes are 15 mm higher in world Z than the preceding 106-bolt study. Use the revised member coordinates. |
| Exterior cleats | Current profiles and receiver rows; [material basis](plywood-cleat-material-basis-v1.json) | Four separate leaves, three holes per leaf, no composite/glue credit. `eoere_bolt_067/070` stay omitted. |
| Bought hardware | [102 selected stacks](paired-frame-v2/hardware-selection.csv) | Ten ASTM A574 bolts use matching Grade 8 nuts; retain each length-specific body limit, washer and spacer. |
| LED passages | [32 unchanged passage datums][passages], [section](enclosed-passage-study.svg), [LED reference](../led-wiring-reference.md) | Enclosed Ø38.1-mm holes at N69.85; F1–G1 retains its 40-mm shift. Endpoints/harness remain fixed. |
| Panels and 66 screws | Current profiles, [66 world axes](paired-frame-v2/axes.json), retained [panel machining][panels] and [purchased-screw record](../current-panel-screw-purchase.md) | Keep panel outlines, purchased Hillman 42605 screws, existing axis count and owner-selected pilot/countersink policy. Strength is deferred. |
| Unchanged recesses and angled ends | [Retained 1:12 recess detail][recess], current profile coordinates and [retained end projections][projections] | The long support legs keep their recesses and soles. Earlier hole marks and shorter top-rail dimensions do not apply. |

The principal fittings retain only `eoere_bolt_072/073`; omit `068/069`.
The upper returns retain only `outboard_angle_left_eoere_bolt_010` and
`outboard_angle_right_eoere_bolt_013`; omit their `006/009` companions.
At each short front post/runner connection, use two pins at **Y=80 mm from the
common front end**, **Z=50 and 100 mm above the runner sole**. Use the member
sheets to transfer these world positions into each local datum. Both principal
members and the flat header remain single 2×6s; all 24 sawn lengths are unchanged.

## Parts and raw blanks

Installed: **24 sawn members, four plywood cleat leaves, six climbing panels,
26 Eoere angles, 102 bolts, 102 matching nuts, 204 washers, 34 factory spacers
and 66 Hillman screws**. Hold/T-nut hardware, lights and pads retain their own records.
Seven four-packs supply 28 angles, leaving two spares; 26 are installed.

All dimensions below are **millimetres**. Decimal places retain nominal geometry;
they are not manufacturing tolerances. The coordinate layout identifies each datum.

| Member/group | Quantity | Raw length × depth × thickness |
| --- | ---: | ---: |
| `base_floor_left/right` runners | 2 | 1815.646483 × 139.7 × 38.1 |
| `base_header` | 1 | 2435.225 × 139.7 × 38.1 |
| `base_post_center_left/right` | 2 | 238.9 × 139.7 × 38.1 |
| `base_post_outer_left/right` short kicker posts | 2 | 238.9 × 139.7 × 88.9; solid 4×6 |
| `base_principal_center_left/right` | 2 | 2532.626012 × 139.7 × 38.1 |
| Left bottom/lower-service/upper-service rails | 3 | 1041.25 × 139.7 × 38.1 |
| Right bottom/lower-service/upper-service rails | 3 | 1077.275 × 139.7 × 38.1 |
| `base_rail_top` | 1 | 2765.425 × 139.7 × 38.1 |
| `base_side_left/right` sloping sides | 2 | 2570.726012 × 139.7 × 88.9 |
| `lumber_leg_left/right` long support legs | 2 | 2028.462988 × 139.7 × 88.9 |
| `outboard_knee_left/right` upper returns | 2 | 1468.033399 × 139.7 × 38.1 |
| `outboard_leg_packer_left/right` | 2 | 200 × 139.7 × 38.1 |
| `eoere_cleat_left/right` and their `_outer` leaves | 4 | 609.6 × 203.2 × 28.575; strength along 609.6 |
| Main climbing panels | 4 | 1217.6125 width × 1219.2 height × 18.25625 |
| Whole kickers | 2 | 1217.6125 width × 277 height × 18.25625; retain the miter |

Cleat plywood must meet **APA Rated Sturd-I-Floor 48 oc, PS 1, at least five plies,
Group 1 bearing basis**, with **at least 27 mm actual thickness**. Preserve the
sheet's strength direction and material identification when cutting the four leaves.
The two adjacent leaves are separate parts. Do not substitute ordinary thin panels
or treat the pair as a glued laminate.

The outer kicker posts retain the 9.525 × 9.525-mm longitudinal T-nut-clearance
bevel introduced in `eoere-4x6-front-posts-v1`. Current receiver positions supersede
that predecessor's hole marks. Use the current profile and its own face labels. The old square-post outlines
omit that bevel. The climbing panels, whole kickers and all 66 screw axes remain fixed.

## Stock allocation

Nominal purchase allocation: **14 sticks / 162 nominal board feet**:
**five 2×6×8-ft, five 2×6×10-ft, two 4×6×8-ft and two 4×6×10-ft**.
This changes the raw-stock allocation. Finished member lengths and sections stay fixed.
The header uses a 10-ft blank to leave end-trimming allowance around its 2435.225-mm
cut; the old near-exact 8-ft fit need not be used.

| US stock | Sticks | Allocation |
| --- | ---: | --- |
| 2×6×8 ft, nominal 2438.4 mm | 2 | One runner and one 200-mm packer from each stick. |
| 2×6×8 ft | 3 | One left/right rail pair per stick: 1041.25 + 1077.275 mm. |
| 2×6×10 ft, nominal 3048 mm | 2 | One center principal and one 238.9-mm center post per stick. |
| 2×6×10 ft | 1 | Header; retain end-trimming allowance. |
| 2×6×10 ft | 1 | 2765.425-mm top rail. |
| 2×6×10 ft | 1 | Both 1468.033399-mm upper returns. |
| 4×6×8 ft | 2 | One long support leg and one 238.9-mm outer post per stick. |
| 4×6×10 ft | 2 | One sloping side per stick. |

The nominal nesting allows a 3.175-mm saw kerf at each separation. Usable stock,
end trimming, defects and the actual saw kerf remain unobserved. Check the allocation
against the usable blank before cutting. Plywood leaves and climbing panels are
separate sheet-stock requirements. Historical 13-stick baskets are not current totals.
The [stock table](paired-frame-v2/stock-nesting.csv) records 6-mm end trim at each
end and a 3.175-mm kerf per separating cut. Four leaves fit one identified 4×4
cleat sheet with the marked strength direction retained; their 609.6-mm lengths
run along that direction. Main-panel sheets are a separate purchase.

## Layout and assembly

1. Label every member and datum face. L follows grain; U/V are member-specific.
   The header uses U across depth and V across thickness. Negative coordinates
   and centered datums on the returns/packers are intentional. Preserve the right
   principal's 39.2-mm shift and unequal left/right rails.
2. Transfer current end/profile marks with independent registration, clamping and
   support on both sides of each cut. Retain whole kickers, T-nut clearances and
   1:12 leg recesses. The retained 4×6 saw-access route uses a pull saw; actual
   tools, stock and cut accuracy have not been inspected.
3. Prepare fresh stock without the omitted holes. Retain only each `*_1` main
   long-leg/runner axis. The foot's left leg enters at U=50.8 and exits at U=0;
   the right leg enters at U=38.1 and exits at U=88.9. Register the recessed face.
   Use the revised coordinates for both upper long-leg pins; old upper marks are
   15 mm lower in world Z and fail the loaded-edge requirement.
4. Clamp paired receivers in their supported installed relation before transferring
   a common shaft line. A single bolt still requires aligned receivers. Wood bore
   choices are 13/32 in (10.31875 mm) for 3/8-in bolts and 17/32 in (13.49375 mm)
   for 1/2-in bolts. CAD occupied diameters and modeled lengths are analysis
   envelopes. Use the drilling table's required guide, backer and bit projection.
   Transfer a small common pilot or centre mark with the joint supported; remove
   the angle before enlarging wood holes. The 13/32-in wood bit must not enlarge
   a nominal 10-mm factory hole. Drill neither omitted stations nor insert pilots.
5. Mark the four plywood leaves from a controlled template or measured datum.
   The lower row is nominally 34.1125 mm from the grain end; the required minimum
   is 33.3375 mm. The 0.775-mm margin does not permit a generic ±1-mm layout
   tolerance. Register one rigid template to the actual finished grain end and
   side, and transfer all three centres from it. Before accepting each lower bore,
   measure its centre-to-end at both faces, using clear edge distance plus half
   the measured bore diameter. Require **at least 34.0 mm measured**, with a method
   uncertainty **no greater than 0.25 mm**. This retains a true minimum 33.75 mm;
   the [fixed-action sensitivity](paired-frame-v2/critical-dimensions.json) remains
   below reference. A failed dimension stops that operation; no slotting or plug
   repair is established. Keep the strength axis along the 609.6-mm direction.
6. Assemble the header, short posts, side frames and their angles with temporary
   support. The four cleat angles retain the shared header/lower shafts and
   Y−4.7625-mm outer assembly shift. Use all current stations, including the
   upper returns and packers; the paired-cleat geometry is not a leaf-only swap.
7. Use six 3/8-16 × 203.2-mm **ASTM A574 socket-head** cleat bolts and four
   3/8-16 × 152.4-mm **ASTM A574 socket-head** front-pair bolts, with ten matching
   **SAE J995 Grade 8 nuts**. Use a **5/16-in hex key** or short straight bit.
   [Hardware basis](paired-frame-v2/A574-hardware-basis.json): long bolts require
   smooth body at least **163.5125 mm**; front bolts require at least **106.172 mm**.
   The front strength calculation retains its threaded root regions. Do not use
   the long-bolt shank floor for the front bolts. The four shared header bolts
   remain Grade 5, 88.9 mm long. The other 92 bolts retain their listed grades;
   all other stacks retain
   their own selected lengths. Spacers go between the nut washer and nut. Use
   factory 12.7-mm pieces at the listed stations; two pieces give 25.4 mm.
   Do not use loose washers to replace the specified spacers.
8. Keep the long legs, runners and upper returns positively supported while making
   their connections. One bolt supplies no independent rigid clamp. Complete
   both side frames and permanent load paths before removing temporary support.
   Do not loosen a loaded joint for assembly or service. The current nominal
   tool and straight insertion/removal envelopes are clear for all 306 nominal
   operations. All 204 supported washer rings are contained, including the
   retained inner bridges over CAD bore envelopes. These checks do not observe
   actual socket fit, ratchet swing, fixtures, bedding or bolt preload. Assemble
   and service frame hardware with the panels and wiring clear of the tool path.
9. Feed the intact LED harness through the enclosed passages before closing
   obstructing assembly stages. Retain endpoints and the F1–G1 shift; no old
   open notch, splice or insert pilot is added. Nominal route clearance does
   not establish actual whole-strand feeding or bend-radius fit.
10. Retain all 66 Hillman screws and the recorded owner-selected lead pilot plus
    face countersink: the owner-selected Kobalt #10 insert uses a 3.175-mm
    (1/8-in) pilot and 9.525-mm (3/8-in) countersink. These are the retained
    [shop-checklist bit choices](../floor-flush-shop-checklist.md#2-before-drilling),
    not Hillman-published installation dimensions. Record an offcut trial
    before the 66 holes. Another
    brand's resistance, stiffness or installation instructions do not qualify
    Hillman. Panel/screw strength remains deferred.

## Required dimensions and actual observations

Leave these cells blank until the relevant item is observed. The hardware-selection
CSV also retains its per-stack observation fields. A failed adopted criterion,
incompatible delivered part or contradictory instruction holds the affected operation.

| Required item | Actual | Disposition |
| --- | --- | --- |
| Dry-service DF-L No.2 stock; full specified sections, usable blanks and retained recess/bevel geometry | | |
| Fresh stock without omitted or abandoned prototype bores | | |
| Identified APA48oc PS1, five-ply minimum, Group1 plywood; actual thickness at least27 mm | | |
| Lower plywood row-to-end at least34.0 mm measured at both faces; uncertainty at most0.25 mm | | |
| Upper half-inch pin loaded edges at least50.8 mm in both receivers | | |
| Each single principal pin, single upper-return pin and vertical50/100-mm front pair matches its current sheet | | |
| Ten A574 bolts, matching Grade8 nuts, distinct163.5125/106.172-mm body floors, plus92 specified Grade5 bolts | | |
| Every catalog-box tip, free seating and full-form nut engagement requirement in the selected stack table | | |
| Washer dimensions/material and angle geometry/material meet the recorded conditional requirements | | |
| Correct factory spacers and complete head/washer/nut seating | | |
| Tools, guide/backer support, nominal access and stable assembly setup fit the actual parts | | |
| Intact harness and nominal passages accommodate the actual light assemblies | | |

The flat header's nominal net shear/torsion comparison is close to reference.
Its full **139.7 × 38.1-mm** section and specified supported profile are required;
undersize stock, deeper cuts or extra holes are not covered. Global actions retain the recorded panel/screw stiffness assumptions. Panel
and screw resistance remains unresolved and is not qualified by this frame evaluation.

Use the retained [main-panel sheet 1][panel-sheet-1] and
[panel/kicker sheet 2][panel-sheet-2] beside the 340-row panel-machining table:
142 T-nut locations, 132 LED locations and the same 66 screw axes. Earlier frame
hole marks on surrounding historical sheets do not supersede this packet.

[panel-sheet-1]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/panel-layout-1.svg
[panel-sheet-2]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/panel-layout-2.svg
[passages]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/enclosed-passages-v1/passage-datums.csv
[panels]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/panel-machining.csv
[recess]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/rear-recess.svg
[projections]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/README.md#current-coordinates-and-drawings
