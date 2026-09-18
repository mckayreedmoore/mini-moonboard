# Floor-runner shop checklist

**Conditional engineer-unreviewed DIY shop handoff. Not a fabrication release,
manufacturer qualification, inspected build or climber rating.**

Use this sheet with the [assembly guide](floor-flush-assembly-guide.md) and the
[current construction packet](floor-flush-construction/). It consolidates
existing cut, drill, assembly and inspection instructions. It does not add
criteria, hardware, geometry or load cases. Six authenticated no-slip cases
passing 36 adopted checks does not mean every failure mode is qualified.

| Field | Value |
| --- | --- |
| Candidate | `compact-floor-flush-development` |
| Packet identity | [`current-candidate.json`](../current-candidate.json) |
| Construction manifest | [`docs/floor-flush-construction/manifest.json`](floor-flush-construction/manifest.json) |
| Viewer manifest | [`site/hybrid/compact-floor-flush-development/manifest.json`](../site/hybrid/compact-floor-flush-development/manifest.json) |
| Authority | [build package](floor-flush-build-package.md); [MVP master plan](floor-runner-mvp-master-plan.md); [working set](selected-working-set.md) |
| Shop date | |
| Builder | |

Leave every **Actual** and **Disposition** cell blank until the owner or
builder records a physical observation. CAD, software and this form cannot
fill those cells.

## How to use this packet

One current packet. Do not mix older `floortaper`, spliced-knee, flush-top or
2x12 sheets. Assembly Y/Z coordinates are not distances from a sawn end.
Convert every layout to the member-local physical corner, along-grain **A**
and signed cross-grain **C** on that part's sheet.

| Work | Controlling record | Do not use as |
| --- | --- | --- |
| Blank lengths | [`stock.csv`](floor-flush-construction/stock.csv) | Finished cut length, kerf or nesting |
| Finished timber profiles | [`stock-profiles.json`](floor-flush-construction/stock-profiles.json), [`profile-corner-datums.csv`](floor-flush-construction/profile-corner-datums.csv), eight `*-bolt-sheet.svg` | Image scale, mirrored opposite-hand jig |
| Runner ends | [`runner-end-geometry.json`](floor-flush-construction/runner-end-geometry.json), `base_floor_*-bolt-sheet.svg` | Square rear crosscut |
| Lower rim ends | `outer-rim-end-trim.svg`, `base_side_*-bolt-sheet.svg` | Old 7 mm rear-reserve sheets |
| Leg tops and 1:12 recess | `lumber_leg_*-bolt-sheet.svg`, `lumber_leg_*-taper-sheet.svg`, [`leg-taper-cuts.csv`](floor-flush-construction/leg-taper-cuts.csv) | Old 18 mm leg-top projection sheets |
| Bolt layout | [`bolt-member-datums.csv`](floor-flush-construction/bolt-member-datums.csv), matching bolt sheet | Occupied CAD diameter as a bit catalog number |
| Bolt stacks | [`bolt-hardware.csv`](floor-flush-construction/bolt-hardware.csv), [half-inch assessment](compact-half-inch-hardware.md), [runner hardware](floor-runner-recess-hardware.md) | Empty CSV thread columns as “no thread”; catalog length as delivered shank |
| Angle screws | 24 ML24Z at documented stations; 144 specified SDS25112; [ML24Z reference](ml24z-qualification.md) | Hillman deck screws; predrilled CAD wood holes in place of the purchased angle |
| Panel/kicker screws | [`panel-attachment-axes.csv`](floor-flush-construction/panel-attachment-axes.csv); [purchase record](current-panel-screw-purchase.md) | SPAX length, pilot, drive or resistance; CSV `modeled_length_mm` 50.8 mm |
| Hold and LED panel holes | [`panel-hole-axes.csv`](floor-flush-construction/panel-hole-axes.csv); [hold hardware](moonboard-hold-hardware.md); [LED routing](led-wiring-reference.md) | Moon 1/2-inch T-nut bore in place of the selected Escape 7/16-inch bore |
| Timber LED passages | [`timber-passages.json`](floor-flush-construction/timber-passages.json) | A machining release; the JSON still records `qualified_for_machining: false` |
| Hold bolts | [Moon/Escape hold instructions](moonboard-hold-hardware.md) | 142 T-nuts as 142 extra through-bolts or a per-hold length schedule |

Nominal CAD dimensions are modeled geometry. Adopted limits are the
acceptance rules next to each check. The modeled 2 mm runner-top gap and the
3 mm analysis boundary allowance are not shop cutting tolerances.

Mark left/right, inside/outside, floor end, grain direction and the physical
minimum-X datum on each piece before layout. Left and right have their own
minimum-X datums; do not mirror a datum convention.

---

## 1. Before cutting

Receive, identify and mark stock. Do not cut until the matching packet is
frozen and the rows below are accepted or an explicit stop is recorded.

| ID | Part | Requirement and source | Observation method | Accept / reject | Actual | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| C0 | Packet | Same candidate, construction manifest and these instructions. Choose **official Mini 4×4** or **4×8 kerf-right** and stay on that packet. [Width option](floor-flush-width-option.md); [assembly guide](floor-flush-assembly-guide.md) step 1. | Official: `docs/floor-flush-construction/`. Kerf-right: `docs/floor-flush-construction-kerf-right/` (1/8 in on K / right, pads in front). | Reject mixed official/kerf or historical sheets. Stop cutting. | Official ☐  Kerf-right ☐ | ☐ accept ☐ stop |
| C1 | Lumber | Dry, unincised, grade-stamped DF-L No. 2 or better. [Current design basis](current-design-basis.md). Nominal 4×6 actual 88.9 × 139.7 mm for legs/rims; nominal 2×6 actual 38.1 × 139.7 mm for header, posts, rails, principals and runners. | Read grade stamp; measure actual section at connection regions. | Reject STUD, appearance-only, Hem-Fir, SPF, DF-L(N), treated, incised or finger-jointed stock, or a finished section below the modeled size, pending reassessment. Nominal names are not properties. | | ☐ accept ☐ stop |
| C2 | Face plywood | Owned Roseburg 23/32 CAT AC exterior PS 1, modeled 18.25625 mm. [Purchased materials](purchased-materials.md). Verify usable width before the fixed 1219.2 mm grid. | Measure thickness and usable sheet size; identify stamp/strength axis. | Category thickness is not a measurement. Stop the grid cut if usable width or thickness cannot support the layout. | | ☐ accept ☐ stop |
| C3 | Blanks vs profiles | `stock.csv` lengths are blank envelopes without kerf. Rim/leg envelopes 2570.726 mm and 2028.463 mm are inherited blanks, not flush finished lengths. Runner blank follows the 1815.646 mm maximum finished outline. | Compare purchased lengths to blanks, then lay out finished profiles from the current sheets. | Do not cut a finished profile from an older candidate length. | | ☐ accept ☐ stop |
| C4 | Runner ends | Front plane Y = −175.7 mm, flush to the outer-post plane. Rear end follows the leg back face: bottom Y = 1639.946 mm at Z = 0, top Y = 1605.539 mm at Z = 139.7. Bottom edge 1815.646 mm, top edge 1781.239 mm. [Assembly guide](floor-flush-assembly-guide.md); `runner-end-geometry.json`. | Dry-mark from the member-local corners on `base_floor_*-bolt-sheet.svg`. | Inclined rear end, not a square rear crosscut. Stop if the marked profile is taken from a square-end sheet. | | ☐ accept ☐ stop |
| C5 | Lower rim ends | Lower rim ends at Y = −175.7 mm (post/header plane). Remaining modeled normal depth 102.805 mm. Old 7 mm reserve is removed. `outer-rim-end-trim.svg`. | Identify the finished end on `base_side_*-bolt-sheet.svg` and the trim sheet. | Do not restore the 7 mm reserve or use a previous rim sheet. | | ☐ accept ☐ stop |
| C6 | Leg tops | Leg tops terminate on the rim rear face. Previous 18 mm normal projection is removed. Upper bolt pair is relocated. | Use `lumber_leg_*-bolt-sheet.svg` only. | Do not shorten a previously drilled leg. Fresh stock. | | ☐ accept ☐ stop |
| C7 | 1:12 recess layout | Inner-face open-bottom cut. Max removal 38.1 mm from 88.9 mm, leaving 50.8 mm nominal thickness. Runout 457.2 mm along grain, 1:12. Starts at A = 180.343 mm, full stock at A = 637.543 mm, measured from the lowest raw grain station, not vertically from the floor. `leg-taper-cuts.csv`. | Mark both faces from the two-face taper sheet on the bevel-footed leg. | A is along grain. Stop if the layout uses floor height as A. | | ☐ accept ☐ stop |
| C8 | 2 mm / 3 mm | Modeled runner-top clearance is 2 mm CAD gap. Geometry screening uses a 3 mm inward boundary allowance. [Assembly guide](floor-flush-assembly-guide.md); [fabrication review](floor-flush-fabrication-review.md). | Confirm the intended gap on the drawing; do not add either value to a saw setting. | Neither value is a blanket shop tolerance or permission to deepen the recess. | | ☐ accept ☐ stop |
| C9 | Kickers | Whole 1219.2 × 277 mm outlines. No kicker notches. | Check the panel blanks against `stock.csv`. | Reject a notched or shortened kicker as a substitute. | | ☐ accept ☐ stop |

Cut feet, flush ends and the continuous recess from the current sheets. Saw
choice for the long shallow recess is in the [assembly guide](floor-flush-assembly-guide.md):
work the waste side of the line; the 38.1 mm recess depth is not the
through-cut thickness across 139.7 mm width. Record the finished-cut rows
below before drilling.

| ID | Part | Requirement and source | Observation method | Accept / reject | Actual | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| C10 | Recess stock | Sound, check-free timber through the transition; smooth continuous slope; no overcut, split, tear-out or damaged bearing surface. [Criteria ledger](floor-runner-mvp-criteria.md) `recess_stock_and_cut`; FR-3. | Visual and tactile inspection of both faces and the runout end. | Reject or reassess defects. Do not deepen the recess as a repair. Stop drilling that leg. | | ☐ accept ☐ stop |
| C11 | Finished profiles | Match the current sheet outlines. Retain modeled remaining sections, including 102.805 mm rim normal depth and 50.8 mm recess thickness. | Measure remaining thickness/depth at the critical stations; compare corners to `profile-corner-datums.csv`. | Modeled remaining section is not an extra fabrication allowance. Overcut: stop and reassess. | | ☐ accept ☐ stop |

---

## 2. Before drilling

### Hole-type vocabulary

| Term | Meaning in this packet | Not |
| --- | --- | --- |
| Bolt clearance hole | Finished wood opening for a bolt. NDS §12.1.3 range below. | A screw pilot; a panel hold hole |
| Screw pilot | A lead hole for a threaded wood screw. Owner-selected for the 66 Hillman axes. | An SDS wood predrill; a bolt clearance hole; a plywood clearance hole |
| Panel clearance / hold hole | Specified plywood opening for a T-nut or LED | A bolt clearance hole |
| CAD occupied-volume diameter | Modeled shaft envelope in CAD/CSV | A drill-bit instruction by itself |

### Operation schedule

#### Upper 1/2-inch rim/leg bolts — 4 stacks

| Item | Instruction | Source and applicability |
| --- | --- | --- |
| Joints | `lumber_leg_bolt_{left,right}_{1,2}`. Pair pitch 56 mm. Pair centre assembly Y = 1134.25 mm, Z = 1761.5 mm, direction (18, 53) normalized; convert to member-local A/C. | [Build package](floor-flush-build-package.md); `bolt-member-datums.csv` |
| Finished hole | Between D+1/32 in (13.49375 mm) and D+1/16 in (14.2875 mm). CAD occupied / CSV `hole_diameter_mm` is **14.2875 mm (9/16 in)**, the upper end of that range. | [NDS §12.1.3](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf), already applied to these same 1/2-inch and 3/8-inch Grade 5 bolts in DF-L in [compact-spliced-build-package.md](compact-spliced-build-package.md). Current CSV diameters match. This is the bolted-wood clearance rule for this hardware, not a new hole size. |
| Bit | Choose a bit that produces a finished hole inside that range. Measure the finished hole, not the bit stamp. | Same. A 9/16 in bit is the CAD upper-end target only if it does not oversize past D+1/16. |
| Registration | Clamp rim and leg in the flush-top geometry. Layout from each member's own datum D. Drill with a guide; back the exit; drill from one side. | [Assembly guide](floor-flush-assembly-guide.md) |
| Inspection | Complete washer seats; edge/end distances on actual timber; bolt enters without being driven. No elongation. | FR-3 receiver/washer rules |

#### Front 3/8-inch runner/post bolts — 4 stacks

| Item | Instruction | Source and applicability |
| --- | --- | --- |
| Joints | `rail_front_bolt_{left,right}_{1,2}`. Nominal pitch **39.5 mm** along normalized assembly Y/Z (1, 1). Centre Y = −91.5625 mm, Z = 84.1375 mm; convert to member-local A/C. | [Build package](floor-flush-build-package.md); `bolt-member-datums.csv` |
| Finished hole | D+1/32 in (10.31875 mm) to D+1/16 in (11.1125 mm). CAD/CSV upper end **11.1125 mm (7/16 in)**. | NDS §12.1.3 as above |
| Fixture rule | Registered paired-hole fixture. Finished pitch **39.0–40.0 mm**; pair midpoint offset ≤ **0.5 mm**; each hole perpendicular offset ≤ **0.5 mm**. | [Criteria ledger](floor-runner-mvp-criteria.md) `front_pair_fixture`; [fabrication review](floor-flush-fabrication-review.md) |
| How to register without changing that rule | 1. Dry-fit runner and outer post in the flush front geometry on a flat support. 2. Identify the physical minimum-X corner on each sheet. 3. Make a rigid two-hole fixture with centres 39.5 mm apart along the sheet pair line. 4. Register the fixture to the pair midpoint datum and clamp through both members. 5. Drill with a guide, backing the exit, from one side only. 6. Put fitted pins or transfer punches in the finished holes and measure centre-to-centre pitch with calipers, midpoint from the datum with a rule, and perpendicular offset with a square to the pair line. Measure finished centres, not pencil marks. | Same fixture rule |
| Reject | Any pair outside those three limits. Never elongate a hole or pull a misregistered joint together with the bolt. | Same |

#### Rear 3/8-inch runner/leg bolts — 4 stacks

| Item | Instruction | Source and applicability |
| --- | --- | --- |
| Joints | `rail_rear_bolt_{left,right}_{1,2}`. Assembly Y/Z (1551, 69) and (1517, 97.5) mm; convert to member-local A/C. | [Build package](floor-flush-build-package.md) |
| Finished hole | Same 3/8-inch NDS range; CAD/CSV **11.1125 mm (7/16 in)**. | NDS §12.1.3 |
| Registration | Clamp runner and recessed leg in the intended contact geometry. Layout from each member's datum. Drill with a guide; one side; back the exit. | [Assembly guide](floor-flush-assembly-guide.md) |
| Inspection | Receiver, edge/end distance and maximum-washer-seat checks. No separate 39.0–40.0 mm pitch rule is adopted for this pair. Do not invent one. No elongation. | FR-3; criteria `receiver_fit` |

No angular-error tolerance is assigned beyond the front-pair perpendicular
0.5 mm rule. Do not guess one.

#### ML24Z / SDS25112 — 24 angles, 144 screws

| Item | Instruction | Source and applicability |
| --- | --- | --- |
| Fasteners | Six specified SDS25112 per ML24Z; 3/8-inch hex; low-speed 1/2-inch drill. No generic or Hillman substitution. | [ML24Z qualification](ml24z-qualification.md); Simpson SDS product page already cited there |
| Wood lead hole | Manufacturer: Type-17 point, install without predrilling wood. ESR-2236: installation may be performed without predrilling wood members. Catalog: **where predrilling is required**, use a **5/32-inch** bit. That is conditional, not a command to predrill every station. | [panel-screw-necessity.md](panel-screw-necessity.md); Simpson SDS / ESR-2236. Applies to SDS25112 in sawn DF-L through this connector. It does not assign unlisted ML24Z capacities. |
| Template | Use the **purchased angle holes** as the template. Do not predrill all wood from CAD coordinates and then hope the angle matches. CAD hole diameter in the steel is 6.731 mm; SDS occupied wood shaft 6.35 mm is not a wood pilot. | [ml24z-qualification.md](ml24z-qualification.md) |
| Seat | Head flush to the angle; do not overdrive. Fill every specified round hole. | ESR-2236 / manufacturer |
| Stop | If wood splits, if a station lacks a physical load path, or if the installed geometry differs from six SDS25112 in the ML24Z, stop that station. Do not substitute another screw. | [Master plan](floor-runner-mvp-master-plan.md) ML24Z gate |

#### Hillman 42605 panel/kicker — 66 screws

| Item | Instruction | Source and applicability |
| --- | --- | --- |
| Product | Lowe’s 755741, Fas-n-Tite/Hillman 42605, #10 × 2-1/2 in (63.5 mm), #2 Phillips, ceramic-coated deck screw. 48 main-panel, nine per kicker. | [Purchase record](current-panel-screw-purchase.md) |
| Axes | [`panel-attachment-axes.csv`](floor-flush-construction/panel-attachment-axes.csv). Lower post row Z = 60 mm; upper post Z = 192 mm; header Z = 257.95 mm. Mark the upper post row from the **actual post top** (nominal 46.9 mm below the end). Do not round that row upward. | [Kicker placement](kicker-screw-placement-review.md) for axes only |
| Length vs CSV | Purchased length is **63.5 mm**. `connection-axes.csv` `modeled_length_mm` **50.8 mm** and `modeled_diameter_mm` **4.1402 mm** are historical SPAX occupied envelopes, not Hillman dimensions. | Generated CSV vs purchase record. Do not hand-edit the CSV. |
| Pilot / countersink | Owner-selected: a **lead-hole pilot** along each axis through the plywood into the 2×6, then a **face countersink** so the flat head seats flush. Hillman publishes neither diameter. Occupied CAD 4.1402 mm is not the pilot. Do not transfer SPAX “no lead holes.” This is not a plywood clearance hole: the screw must still form threads. | [Purchase record](current-panel-screw-purchase.md); owner direction 2026-09-17 |
| Offcut trial | Before production, drill/countersink/drive one offcut of the same plywood into scrap DF-L. Record the actual pilot bit, countersink and result in D5. | Same |
| Driving | Drive #2 Phillips; seat the head flush in the countersink without overdriving through the face veneer. | Same |
| Containment | Nominal timber penetration 45.24375 mm; 94.45625 mm remains before the modeled rear face. No tip protrusion. | Purchase record; FR-3 `hillman_66_axes` |
| Stop this operation | Split wood, missed 2×6 receiver, tip protrusion, overdriven head, or a hole large enough that the plywood no longer threads (a clearance hole): **stop**. That would change analyzed geometry. | Same |

The 44.45 mm SPAX loaded-end reference in the kicker review does not transfer
as a Hillman product limit. Keep the modeled axes; verify actual remaining
end distance before driving; do not move the axis.

#### Hold, LED and timber-passage openings

| Family | Finished opening | Source | Note |
| --- | --- | --- | --- |
| 142 hold / T-nut panel holes | 7/16 in = 11.1125 mm | [Hold hardware](moonboard-hold-hardware.md); `panel-hole-axes.csv` | Selected Escape screw-in T-nut bore. Moon’s 1/2-inch branded bore does not replace it. |
| 132 LED panel holes | 13 mm | [LED routing](led-wiring-reference.md); `panel-hole-axes.csv` | Manufacturer Mini hole size. Measure the purchased kit before treating routing as verified. |
| 32 timber LED passages | Modeled enclosed diameter 38.1 mm in these 2×6 members | `timber-passages.json`; selected geometry | JSON `qualified_for_machining` is **false**. This is the dimensional record, not a separate machining release. Do not enlarge past the modeled diameter. Use the JSON entry/exit and local datums, not image scale. |

Hold-bolt lengths are **not** inferred from the 142 T-nut count. Use the
[accepted hold-system instructions](moonboard-hold-hardware.md).

### Drilling checks

| ID | Part / joint | Requirement and source | Observation method | Accept / reject | Actual | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | Front pairs L/R | Pitch 39.0–40.0 mm; midpoint ≤0.5 mm; each perpendicular ≤0.5 mm. `front_pair_fixture`. | Pins in finished holes; calipers, rule, square. | Fail any limit: reject, do not elongate, stop assembly of that joint. | | ☐ accept ☐ stop |
| D2 | Upper and rear pairs | Layout matches member-local A/C; finished hole in the NDS range; complete washer seats. | Measure finished diameter and centre vs sheet datum; trial washer. | Hole outside NDS range, missed datum, or unsupported washer: stop. | | ☐ accept ☐ stop |
| D3 | All 24 bolt receivers | Mating holes align; bolt enters without driving; no elongation or improvised spacers. | Trial bolt before final stacking. | Forced assembly: stop. | | ☐ accept ☐ stop |
| D4 | Hillman axes | 66 axes marked; upper post row from actual post top. | Compare marks to `panel-attachment-axes.csv`. | Do not move an axis to suit a bit. | | ☐ accept ☐ stop |
| D5 | Hillman pilot / countersink | Owner-selected lead hole + face countersink. Record actual bits. Occupied CAD diameter is not the bit. Offcut trial required before the 66 production holes. | Write the bits below; drive one offcut. | Split, overdriven head, or a clearance-sized hole: stop. Do not invent a diameter in this packet. | Pilot bit: ______  Countersink: ______  Offcut: ☐ pass ☐ stop | ☐ accept ☐ stop |

---

## 3. Dry assembly and hardware installation

Temporarily support the incomplete frame against movement. Panels and crash
pads are **not** structural props. Do not describe the incomplete frame as
safe to lean on.

Heads toward the board centre; nuts and threaded tips outward (negative X on
the left, positive X on the right). Twelve complete stacks: one nut and two
specified washers per bolt.

| ID | Part / joint | Requirement and source | Observation method | Accept / reject | Actual | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | Dry geometry | 277 mm main-face datum; flush runner/post, runner/leg and rim/leg faces; intended runner-top gap; whole kickers. [Assembly guide](floor-flush-assembly-guide.md) step 4. | Measure datum from the floor; inspect bearing faces and the 2 mm CAD gap as an intended clearance, not a cut allowance. | Missing intended contact or a closed service clearance: stop and reassess. | | ☐ accept ☐ stop |
| A2 | Upper stacks | ½-13 × 8 in Bolt Depot 407; nuts 2573; USS washers 15025. Full smooth body to first transition ≥ **158.928 mm** at modeled grip and max head washer. Extra thread/runout budget 1.600 mm; shortest tip beyond nut 2.743 mm. | Calipers on delivered shank, runout, actual wood grip, washer OD/ID/thickness, nut height, threads past the nut. | Catalog length is not delivered shank. Fully threaded substitutes are not qualified. Reject incompatible hardware; no spacers. | | ☐ accept ☐ stop |
| A3 | Front stacks | ⅜-16 × 4 in Bolt Depot 367; nuts 2571; washers 15023. Full body ≥ **69.317 mm**. Extra thread/runout 5.359 mm; tip 10.033 mm. | Same measurements on actual parts and actual grip. | Same reject rule. | | ☐ accept ☐ stop |
| A4 | Rear stacks | ⅜-16 × 4½ in Bolt Depot 368. Full body ≥ **78.842 mm**. Extra thread/runout 7.518 mm; tip 9.017 mm. The rejected 5-inch/minimum-thread stack is not an alternate. | Same. Recalculate thresholds if actual grip or washer thickness differs. | Same reject rule. | | ☐ accept ☐ stop |
| A5 | Washers | Complete, flat seating of the maximum catalog envelope on sound timber. Upper thickness may be 3.3528 mm, catalog radius 0.0635 mm above modeled; smaller washers 2.6416 mm, catalog radius 0.381 mm above modeled. | Try the delivered washer on the finished seat; check concentricity and rocking. | Rocking, partial, or unsupported seat: reject. No improvised spacers. | | ☐ accept ☐ stop |
| A6 | Nut seating | Usable thread begins before the nut bearing face; complete threads extend beyond the nut; snug without crushing timber. No steel-joint torque is assigned. | Visual/thread engagement; wrench snug only. | Runout in the nut seat or crushed wood: stop. | | ☐ accept ☐ stop |
| A7 | 24 ML24Z + 144 SDS | All six SDS25112 in each angle; physical load path present; Hillman is not an SDS replacement. Outer angle centres remain at Y = −105.85 mm. | Count and identify markings; confirm each flange bears on its timber. | Missing screw, wrong product, or a station without a path: stop. | | ☐ accept ☐ stop |
| A8 | 66 Hillman | All 66 driven on the recorded D5 bits; heads flush in the countersink; no tip protrusion; receivers contained. | Count; rear-face check; flush-seat check against the offcut. | Split, overdrive, missed receiver, or clearance hole: stop. | | ☐ accept ☐ stop |
| A9 | Interfaces / services | Preserve intended bearing faces, gaps, LED passages and harness clearance from bolt tips. | Visual; do not force parts that close a modeled gap. | Damaged passage or blocked service: stop. | | ☐ accept ☐ stop |

Unlisted ML24Z separation and independent force-parallel flange couples have
**no assigned catalog capacity**. Installing the angles does not make those
actions manufacturer-qualified.

---

## 4. Final assembled-work inspection

| ID | Part / joint | Requirement and source | Observation method | Accept / reject | Actual | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | Hardware counts | 12 outward complete bolt stacks, 24 ML24Z, 144 SDS25112, 66 Hillman 42605, 20 timber, 6 plywood. | Count against this packet. | Wrong count or mixed historical hardware: stop. | | ☐ accept ☐ stop |
| F2 | Front pairs as built | Repeat D1 on the assembled joints. | Same fixture measurements. | Same reject rule. | | ☐ accept ☐ stop |
| F3 | Seats and wood | Full washer seats; no split receivers; no crushed faces; intended contacts remain. | Visual after snug-up. | Split, crush, or lost contact: stop and reassess. Do not elongate. | | ☐ accept ☐ stop |
| F4 | Pads | Two 48 × 72 × 5 in pads side by side, front-to-back centre seam. 127 mm thickness is a clearance datum, not a support. [Crash-pad record](current-crash-pad-construction.md). | Layout only. Pads are excluded from frame mass and structural support. Not impact-certified. | Do not use pads as temporary frame props. | | ☐ accept ☐ stop |
| F5 | Floor | Analytical no-slip support remains an **unverified assumption**. No anchor or friction test is required by this packet. | Record the actual floor as observed; do not convert the assumption into a measured result. | Changed support (tie, anchor, or a calculation that needs one): reassessment, not a silent field fix. | | ☐ accept ☐ stop |
| F6 | Departures | Record every departure against this packet. | Written note plus the affected ID. | Do not silently modify a joint. | | ☐ accept ☐ stop |

Recheck loose hardware, split wood or crushed seats after initial settling,
relocation or unusual impact. That is ordinary assembly care, not a
proof-load with a person.

---

## Operations that wait on missing evidence

These are not filled with typical values.

| Operation | Missing specification | Who / when |
| --- | --- | --- |
| Hillman 42605 production holes | Product-published pilot/countersink diameters (none). Owner method is selected; **actual bits** are still a D5 measurement, not a packet diameter. | Owner/builder on the offcut **before** the 66 production holes. |
| Any hole that would change analyzed geometry (bolt oversize past NDS, elongation, Hillman clearance hole, relocated axes) | A revised CAD/resistance check and affected cases | Design revision; not a shop discretion |
| Delivered shank, runout, washer size, nut engagement, finished hole centres, recess stock, actual lumber section | Physical measurement of the delivered/fabricated item | Owner/builder at receiving and fabrication. Instructions exist; results do not. |
| Unlisted ML24Z separation / flange-couple capacity | Manufacturer listed values (none found for this MVP) | Disclosed limitation. Not a shop measurement. |
| Floor friction or an installed anchor | Out of current scope | Do not add a test as a release gate |
| Hold-bolt length at each T-nut | Per-hold recess/seat mapping | Use [hold hardware](moonboard-hold-hardware.md); do not invent lengths from T-nut counts |

---

## Disclosed analytical limitations (unchanged)

Do not treat these as extra shop measurements or as new analysis tasks.

- Endpoint remains engineer-unreviewed conditional DIY under recorded 250 lb
  inquiry, DF-L No. 2, catalog hardware and no-slip floor assumptions.
- Listed ML24Z force interactions passed in the six cases; unlisted
  separation and independent flange couples are disclosed without capacity.
- Full-thread-root bolt sensitivity is non-adopted and exceeds 1.0.
- Nominal rear-leg cut-face stress inference remains a local-fracture method
  limit paired with C10.
- Historical projected-seat scalar (about −4.970 mm) is a non-adopted
  sensitivity.
- Viewer pads and this checklist do not inspect actual wood, hardware or floor.
