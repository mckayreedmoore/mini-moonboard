# Barrel-nut candidate receiving and offcut checklist

This checklist records the physical BN-1 and BN-2 inputs that cannot be
established from CAD or retail pages. It applies only to
`compact-floor-flush-bolted-development`, using the integrated kerf-right
46-pair barrel-nut pose with the approved N = 42 mm left center-rail rows and
the current four 2 mm top-outer machine-bore extensions. The selected 5 in and
6 1/2 in bolt stacks require further blind-bore corrections before the
qualification geometry can be frozen.

This is a measurement form and an unloaded sacrificial-fit plan. It is **not**
a purchase list, drilling schedule, fabrication release, joint rating, proof
test, or permission to climb. Do not drill a candidate frame member from this
document. The selected `compact-floor-flush-development` angle frame and its
shop checklist remain separate.

All **Actual** and **Disposition** cells below are intentionally blank. Fill
them only from direct observation. Attach photographs and raw measurements;
do not replace item-level records with a remembered range.

Use this form with the [validation plan](barrel-nut-validation-plan.md),
[criteria](barrel-nut-criteria.md),
[selected qualification hardware](barrel-nut-selected-hardware.md),
[hardware evidence ledger](barrel-nut-hardware-evidence.md),
[integrated stack audit](bolted-candidate-prototypes/owner-barrel-integrated-stack-audit.md),
[owner review](bolted-candidate-prototypes/owner-barrel-integrated-owner-review.md),
and [load-test readiness note](bolted-candidate-prototypes/owner-barrel-load-test-readiness.md).
Those records control scope and evidence limits; this form does not supersede
them.

## 1. Record identity and rules

| Field | Record |
| --- | --- |
| Candidate source revision / dirty-tree identity |  |
| Station-register revision |  |
| Hardware lot or package identities |  |
| Lumber lot / grade-stamp identities |  |
| Plywood sheet identities |  |
| LED kit model / revision |  |
| Observer and date |  |
| Ambient temperature / humidity |  |

Use these rules throughout:

1. Give every physical part a unique ID before measurement. Preserve its
   package, labels, grade stamps, and intended station assignment.
2. Record instrument ID, range, resolution, and the check standard used that
   day. Instrument display resolution is not measurement accuracy.
3. Measure in millimeters. Preserve any source inch value too; do not round a
   measurement to a nominal catalog size.
4. Record minima and maxima only after retaining all raw values. A small sample
   does not establish a product tolerance or material minimum.
5. Do not infer steel grade, proof strength, thread class, barrel resistance,
   wood grade, or moisture condition from fit or appearance. Physical
   dimensions do not close the missing resistance evidence in
   [`barrel-nut-hardware-evidence.json`](barrel-nut-hardware-evidence.json).
6. If no predeclared acceptable range exists, use `PENDING ENGINEERING` in
   Disposition. “It fits” is not an acceptance limit.
7. Stop the affected trial for a forced fastener, cross-thread, bottoming,
   split, check growth, breakout, tear-out, unsupported washer, damaged wire,
   hidden interference, or unrecorded substitution. Do not ream, elongate,
   deepen, relocate, lubricate, grind, or trim to make a result pass.

### Measurement equipment register

| ID | Instrument / gauge | Required use | Verification before use | Actual | Disposition |
| --- | --- | --- | --- | --- | --- |
| EQ-1 | Outside caliper or micrometer | Bolt, barrel, washer, lumber, and plywood dimensions | Check against a traceable or identified standard spanning the used range |  |  |
| EQ-2 | Depth micrometer, depth rod, or rigid depth gauge | Blind-bore, pocket, thread-axis, and tip-gap dimensions | Check at zero and against an identified length standard |  |  |
| EQ-3 | Pin gauges or identified gauge pins | Finished bore diameters at entry and depth | Record actual pin sizes; do not use a bit shank as an unmeasured gauge |  |  |
| EQ-4 | Square, straightedge, angle fixture, and feeler gauges | Bore drift, perpendicularity, seating, stock straightness, and face gaps | Check square and straightedge against a known reference |  |  |
| EQ-5 | Thread gauges / optical measurement method | 1/4-20 identity and complete-thread endpoints | Record gauge standard, class, and calibration or metrology method |  |  |
| EQ-6 | Species-corrected moisture meter | Lumber condition | Record meter check and DF-L correction method |  |  |
| EQ-7 | Camera and part labels | Trace each observation to a physical item and orientation | Confirm labels are legible in each image |  |  |

Calipers and a successful mating trial cannot locate the first and last
**complete** internal threads reliably. If EQ-5 or controlled product evidence
cannot do that, leave those dimensions unresolved.

## 2. New bolt, barrel, and washer receiving

The selected qualification inventory is 46 nominal 1/4-20 pairs: 4 CDE
`1456BHT5` 3 1/2 in bolts, 26 CDE `1472BHT5` 4 1/2 in bolts, 4 CDE
`1480BHT5` 5 in bolts, and 12 CDE `14104BHT5` 6 1/2 in outer-rail bolts; 46
STAFAST `JCD14201606NL ZN` barrels; and 46 Fastenal `33857` hardened USS/Type A
wide washers. These are qualification identities and counts, not an approved
order or fabrication release. The rejected 6 in outer-rail comparator is not
part of this receiving inventory.

### Dimension definitions

Use one coordinate convention in the raw log:

- Bolt coordinate `x` starts at the underside head-bearing plane and increases
  toward the tip. Record actual length `L`, first complete male thread
  `x_m0`, last complete male thread `x_m1`, body/thread transition, incomplete
  runout, and tip chamfer separately.
- Barrel coordinate `u` starts at the marked insertion end. Record body length
  `B`, maximum/minimum OD, transverse thread-axis center `u_axis`, and which
  end was inserted. Record the complete female-thread interval on the bolt
  axis relative to the barrel axis; do not assume the body is threaded through
  merely because a retail description says so.
- Washer thickness is measured at no fewer than four clock positions. Record
  OD, ID, dish/warp, burrs, and the actual face placed against wood.
- In an assembled stack, translate complete male and female intervals to the
  same datum. Their usable geometric overlap is
  `max(0, min(x_m1, x_f1) - max(x_m0, x_f0))`. This is not adequate engagement
  until the resistance method supplies a required minimum.
- Measure bore-cap coordinate `x_cap` from the seated underside head-bearing
  plane along the actual bolt axis. Physical tip gap is `x_cap - L`. Keep head
  seating, washer thickness, member grip, barrel-axis location, and bore depth
  as separate measurements so the result can be recomputed.

### Part-level measurement requirements

For a final receiving decision, measure every part assigned to a critical
stack. The selected 6 1/2 in rail family needs 10.4408 mm more blind-bore
depth merely to reach zero adverse modeled tip clearance; the provisional
2 mm reserve requires 12.4408 mm. The selected 5 in adverse stack retains
only 0.1204 mm before machining error, so it also needs a controlled deeper
blind bore. These open corrections are too sensitive for a spot-check. A
preliminary sample may be logged as exploratory, but cannot establish the
unmeasured pieces.

| ID | Part / quantity | Required observation | Method / record | Acceptance basis | Actual | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| H-1 | STAFAST `JCD14201606NL ZN` barrel, each of 46 | Package and SKU; end marking; `B`; OD at both ends and two axes; roundness; `u_axis` from the identified slotted datum end; slot geometry and which end leads during insertion | Label each `BR-01`…`BR-46`; retain item-level values and photographs | Exact selected identity; nominal 10.0076 mm OD, 16.002 mm body, and 5.9944 mm slotted-end axis are identification targets, not tolerances; every measured dimension must lie inside the later frozen input envelope |  |  |
| H-2 | Barrel, each of 46 | 1/4-20 identity; whether the cross-thread is open through both sides; first/last complete female threads; lead-ins; obstruction; usable threaded span from each side | Use identified thread gauges or qualified metrology; record method and gauge class. Never force a gauge or candidate bolt | Controlled or measured-lot female interval must support calculated overlap; through-tip families cannot use a blind/obstructed barrel |  |  |
| H-3 | Barrel, each of 46 | Straightness, plating/burrs, damaged threads, slot damage, cracks or seams | Magnified visual inspection and non-forced gauge check | No damage or geometry outside the frozen input basis; appearance supplies no strength value |  |  |
| H-4 | CDE `1456BHT5` 3 1/2 in Grade 5 fully threaded bolt, each of 4 | Product/lot, head marking, `L`, shank diameter, head bearing geometry, `x_m0`, `x_m1`, runout and tip chamfer | Label `B35-01`…`B35-04`; use EQ-1/EQ-5 | Exact identity and dimensions within frozen stack and SAE J429 / ASME B18.2.1 / IFI-199 basis; manufacturer certificate and Class 2A confirmation required |  |  |
| H-5 | CDE `1472BHT5` 4 1/2 in Grade 5 fully threaded bolt, each of 26 | Same fields as H-4; verify the fully threaded form rather than assuming it | Label `B45-01`…`B45-26` | Same |  |  |
| H-6 | CDE `1480BHT5` 5 in Grade 5 fully threaded bolt, each of 4 | Same fields as H-4; verify the fully threaded form rather than assuming it | Label `B50-01`…`B50-04` | Same; the accepted deeper bore must also leave positive worst-case tip clearance |  |  |
| H-7 | CDE `14104BHT5` 6 1/2 in Grade 5 fully threaded bolt, each of 12 | Same fields as H-4; preserve each bolt's assignment to an outer-rail station | Label `B65-01`…`B65-12` | Exact identity and dimensions within frozen stack; manufacturer certificate and Class 2A confirmation required; complete male/female overlap and accepted positive tip clearance required after bore correction |  |  |
| H-8 | Fastenal `33857` hardened USS/Type A wide washer, each of 46 | Exact product, lot, material evidence, OD, ID, four-point thickness, flatness, burrs, and face orientation | Label `W-01`…`W-46`; map to station and bolt | ASTM F436/F436M / ASME B18.21.1 identity and lot MTR; 7.7978–8.3058 mm ID, 18.4658–19.0246 mm OD, and 1.2954–2.0320 mm thickness; full supported finished seat; later bending, wood-bearing, and pull-through checks |  |  |
| H-9 | Dry-mated pair before wood | Finger-start, rotations to first full engagement, smooth travel, obstruction/bottoming, and non-damaging removal | Use only mapped bolt/barrel pairs; no power driver or lubricant; retain pairing in raw log | Diagnostic only. Cannot replace complete-thread dimensions or resistance evidence |  |  |
| H-10 | Material / conformity evidence | Bolt standard/grade, barrel material minimum, washer material, lot trace, and any certificates or controlled drawings | Archive exact document and tie it to package/lot IDs | Must satisfy the frozen resistance method; retailer category or finish is insufficient |  |  |

### Family stack summary

Enter item-level extrema only after assigning actual parts to stations. Do not
average away the shortest engagement or smallest clearance.

| Family | Count | Selected nominal bolt length | Critical modeled condition to recheck | Assigned part IDs | Minimum complete-thread overlap | Minimum tip gap | Actual | Disposition |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| Base center | 2 | 114.3 mm | 17.653 mm fully threaded tip span to modeled barrel near wall |  |  |  |  |  |
| Base outer side | 4 | 114.3 mm | 9.553 mm maximum modeled body overlap |  |  |  |  |  |
| Bottom center rail | 4 | 114.3 mm | 9.553 mm maximum modeled body overlap |  |  |  |  |  |
| Bottom outer rail | 4 | 165.1 mm | Selected 6 1/2 in family needs 10.4408 mm added bore depth to zero adverse tip clearance; provisional 2 mm reserve needs 12.4408 mm |  |  |  |  |  |
| Center posts to header | 4 | 88.9 mm | 70.508 mm maximum selected shifted barrel insertion depth |  |  |  |  |  |
| Outer header to outer posts | 4 | 114.3 mm | Recessed seat and rim-first service access |  |  |  |  |  |
| Lower center rail | 4 | 114.3 mm | Approved N = 42 mm left first row |  |  |  |  |  |
| Lower outer rail | 4 | 165.1 mm | Same selected 6 1/2 in adverse stack and bore correction |  |  |  |  |  |
| Top rail to center posts | 4 | 114.3 mm | 9.553 mm maximum modeled body overlap |  |  |  |  |  |
| Top rail to outer posts | 4 | 127.0 mm | Selected 5 in family requires a deeper blind bore and positive adverse tip clearance |  |  |  |  |  |
| Upper center rail | 4 | 114.3 mm | Approved N = 42 mm left first row |  |  |  |  |  |
| Upper outer rail | 4 | 165.1 mm | Same selected 6 1/2 in adverse stack and bore correction |  |  |  |  |  |

For each row, attach the full tolerance-stack calculation. It must use the
worst compatible combination, not nominal dimensions or independent averages.
The required engagement remains blank until an accepted thread/barrel
resistance method supplies it.

### Twelve retained through-bolt stacks

The retained axes do not transfer the selected frame's fit or utilization to
this changed frame. Use the controlled product identities in
[`barrel-nut-hardware-evidence.json`](barrel-nut-hardware-evidence.json), then
record the candidate's actual grip and delivered hardware.

| ID | Stack family / quantity | Required observation | Actual | Disposition |
| --- | --- | --- | --- | --- |
| RH-1 | 1/2-13 × 8 in upper stacks / 4 | Bolt Depot 407 identity and marking; actual length, smooth body, transition/runout, nut and two washer dimensions; actual candidate grip; complete threads beyond seated nut |  |  |
| RH-2 | 3/8-16 × 4 in front stacks / 4 | Bolt Depot 367 identity and same delivered-stack fields; actual candidate grip and finished-hole fit |  |  |
| RH-3 | 3/8-16 × 4 1/2 in rear stacks / 4 | Bolt Depot 368 identity and same delivered-stack fields; actual candidate grip and finished-hole fit |  |  |

No retained stack receives a disposition of accepted until candidate demands,
receiver geometry, washer support, and resistance are rechecked.

## 3. Lumber receiving

The calculation basis is dry, unincised US Douglas Fir-Larch No. 2 dimension
lumber. Modeled sections are 88.9 × 139.7 mm for the two legs, two side rims,
and two seam-side center posts; the other fourteen timbers use 38.1 ×
139.7 mm sections. A nominal label or a retail substitute does not establish
those properties.

Measure each blank at both ends, mid-length, and every candidate connection or
service-cut zone. At every section record both dimensions in two orientations,
not one nominal width. Map defects by member-local along-grain distance and
face. Do not erase or cut away a grade stamp before its record is accepted.

| ID | Part / scope | Required observation | Method / record | Acceptance basis | Actual | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| L-1 | All 20 timbers | Unique ID, species/group, grade, grading agency, treatment/incising, finger joints, and stamp photographs | Read every stamp; photograph full blank and close-up | Dry, unincised US DF-L No. 2 or accepted better basis; alternatives require recalculation |  |  |
| L-2 | Six modeled 4×6 members | Actual section and length at ends, midpoint, and all connection/cut zones | EQ-1 plus straightedge; retain raw station values | No section below the later frozen geometry envelope; center posts must match their own candidate schedule |  |  |
| L-3 | Fourteen modeled 2×6 members | Same section, length, straightness, twist, cup, and bow record | Same | Same |  |  |
| L-4 | Every timber | Moisture at both ends, midpoint, and each critical joint zone; surface and pin orientation/method | Species-corrected EQ-6; record temperature and correction | Must support the adopted dry-service material adjustments; do not infer core moisture from one surface reading |  |  |
| L-5 | Every connection/cut zone | Grain direction, slope, knots, checks, splits, shake, wane, decay, damage, prior holes, and local growth characteristics | Mark coordinates on a member sketch and photographs | Structural review against actual cut and load direction; no generic appearance pass |  |  |
| L-6 | Center principal/header zones | Stock condition around the modeled 2.092 mm header-pocket edge stock and face behind each bolt line | Full-scale overlay only after frozen geometry; inspect both faces and end grain | Any actual defect or section loss enters the local resistance review; nominal fit alone cannot pass |  |  |
| L-7 | Outer-header zones | Stock condition around the modeled 6.35 mm side stock and recessed seats | Same | Same; no pocket machining until accepted |  |  |
| L-8 | Left lower/upper center rails | Actual section and defects around approved N = 42 mm first rows and adjacent service path | Same | Recheck net section, edge reserve, drill drift, and service clearance with measured inputs |  |  |
| L-9 | Top rail outer rows | Actual section at all four 2 mm-extended machine-bore paths | Same | Positive accepted bore-cap reserve and wood resistance required |  |  |

This inspection cannot turn green, treated, incised, Hem-Fir, SPF,
DF-L(N), appearance-only, or unstamped comparison stock into the stated
material basis.

## 4. Owned plywood and fixed panel yield

The earlier integrated candidate preserves kerf-right panel outlines and all
66 panel/kicker screw axes. The owner-directed two-vertical-bolt development
may move necessary screw axes while retaining the 66 purchased screws and
panel outlines; its eventual shop packet must show the revised axes and their
receivers. Current rectangular blank envelopes are 1217.6125 × 1219.2 mm for
each of four main panels and 1217.6125 × 277 mm for each of two kickers, with
modeled thickness 18.25625 mm. These envelopes are not proof that two owned
sheets yield the parts. Two main blanks plus the modeled 3.175 mm shared kerf
consume exactly 1219.2 × 2438.4 mm of each nominal 4×8 sheet, leaving zero
trim allowance. The recorded retail dimensions, 1204.8744 × 2435.0472 mm
(47.436 × 95.868 in), are 14.3256 mm too narrow and 3.3528 mm too short for
that nesting; rotation also fails. Treat that listing as a failed lead, not a
measurement of the owned sheets. The two whole kicker blanks require a
separately verified matching offcut or additional sheet.

| ID | Part / scope | Required observation | Method / record | Acceptance basis | Actual | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| P-1 | Each owned sheet | Unique ID, product/stamp, grade, bond/exposure mark, face orientation, prior storage/wetting, repairs, voids visible at edges, delamination, and damage | Photograph both full faces, all edges, and stamps | Must match the later frozen candidate plywood basis |  |  |
| P-2 | Each owned sheet | Length and width at both edges and center; both diagonal lengths; squareness; usable undamaged boundary | Steel rule/tape checked over full length; square and diagonals | Actual usable polygon must contain the frozen nesting; nominal 4×8 name is insufficient |  |  |
| P-3 | Each owned sheet | Thickness on a nine-point grid clear of edge damage; local thickness at all planned panel screw and hold zones | EQ-1 without crushing veneers | Actual range must be included in panel, fastener, hold, and fit checks |  |  |
| P-4 | Actual cutting process | Blade identity, measured sacrificial kerf at representative feed/orientation, edge tear-out, and trim loss | Trial only on matching scrap before nesting the owned sheets | Frozen nesting must include measured kerf and trim allowance; do not shrink or move panel outlines |  |  |
| P-5 | Six fixed outlines | Source-bound nesting of exact panel profiles, 66 fixed screw axes, hold/LED holes, grain/face orientation, measured sheet polygons, and measured kerf | Produce a dimensioned nesting audit; do not rely only on rectangular areas | All six profiles fit without damaged stock, axis relocation, or mixed packet geometry |  |  |

Stop before cutting if the four main faces and two whole kickers do not fit the
measured sheets. Adding a sheet may fix stock quantity, but does not authorize
resizing a fixed panel. Any approved screw-axis relocation belongs in the
revised candidate drill sheets, not in an improvised plywood nesting change.

## 5. Sacrificial bore and installed-stack trials

Run these trials only on clearly marked sacrificial offcuts or a nonstructural
full-section mockup. Use stock matching the recorded species, grade, moisture,
section, and grain orientation. Reproduce the intended datum, clamping,
drilling guide, bit, speed, feed, backing, depth stop, and cut order. Record
every tool and setup. Do not transfer a result from generic softwood.

No bore diameter in this section is a drill instruction. The model uses a
10.0076 mm barrel body and the same 10.0076 mm insertion bore, giving zero
nominal allowance. A 13/32 in bit is only a prior 10.31875 mm tool lead. Freeze
a proposed finished-hole range and recalculate removed wood before using any
bit in a qualification trial.

For each finished bore record diameter in two directions at entry and the
deepest accessible location, depth, center location from the datum, angular
drift at the far end, surface breakout, tear-out, burnishing, splitting,
barrel insertion force/method, orientation error, retention, bolt start, tip
gap, seating, removal, and post-removal damage.

| ID | Trial geometry | Purpose / required configuration | Required observation | Actual | Disposition |
| --- | --- | --- | --- | --- | --- |
| T-1 | Straight shallow STAFAST barrel bore | Selected proposed fit and slotted-end insertion orientation in representative grain; include the 29.058 mm minimum shifted insertion depth | Finished diameter distribution, barrel insertion/orientation/retention, extraction, and damage |  |  |
| T-2 | Deep blind center post/header bore | Reproduce the 70.508 mm maximum shifted insertion depth in a full 88.9 × 139.7 mm section | Drift, depth control, chip clearing, barrel placement/orientation and non-destructive extraction at depth |  |  |
| T-3 | Intersecting shaft and barrel bores | Reproduce every remaining selected shifted insertion-path class plus its real shaft angle and cut order | Axis miss at intersection, finger-start without cross-thread, complete-thread overlap and repeatable removal |  |  |
| T-4 | Outer-rail 6 1/2 in stack | Full family grip, Fastenal `33857` washer, actual CDE `14104BHT5` bolt, STAFAST barrel, and accepted deeper blind bore at maintained 60 mm setback | Minimum measured reach beyond actual thread axis, usable overlap, far-wall/tip relation, seating and removal |  |  |
| T-5 | Top-outer 5 in stack | Full top-rail section with the final deeper blind-bore correction for CDE `1480BHT5` | Physical bore-cap gap, depth tolerance, barrel overlap, wood remaining at cap, and no bottoming |  |  |
| T-6 | Left center-rail service crossing | Reproduce approved N = 42 mm first row and the actual service-passage envelope in a full section | Minimum clearance between finished cuts, drill drift, remaining wood, and service-feed fit |  |  |
| T-7 | Center principal/header seat | Reproduce real oblique shaft, barrel, washer/head pocket, contact faces, and actual tools in full-section stock | Pocket edge stock, washer support, tool sweep, barrel insertion, bolt engagement, breakout and removal |  |  |
| T-8 | Outer-header recessed seat | Reproduce both rows, full header/post sections, selected washer/head, and rim obstruction mockup | 6.35 mm nominal side-stock sensitivity, seat support, actual driver access, rim-first sequence and service removal |  |  |

Each offcut trial is a fit observation only. It does not establish joint
strength, stiffness, statistical tolerance, repeated-demounting life, or an
acceptable thin ligament. If actual holes differ from the predeclared range,
stop; do not average the failed hole into a passing group.

### Raw offcut record template

Duplicate this table for every specimen.

| Field | Actual |
| --- | --- |
| Specimen ID / source member and distance from its end |  |
| Species, grade, moisture, section, grain orientation, defects |  |
| Hardware IDs and orientations |  |
| Tool, bit, guide, depth stop, speed/feed, clamping, backing |  |
| Intended hole diameters, depths, angles, and datum coordinates |  |
| Finished entry / depth diameters and two-axis values |  |
| Finished depths, centers, far-end drift, and angular error |  |
| Remaining ligaments / cap stock / washer support |  |
| Complete male/female interval overlap and physical tip gap |  |
| Insertion, orientation, finger-start, seating, and extraction observations |  |
| Splits, checks, breakout, tear-out, burnishing, thread or wire damage |  |
| Photographs / measurement attachment |  |
| Disposition |  |

## 6. LED F1–G1 feed trial

The candidate-only right-principal F1–G1 passage is provisionally 25.4 mm,
not the selected frame's 38.1 mm passage. Nominal CAD clearance does not prove
that a prewired LED strand and its connectors can pass.

Use the complete intended LED kit, including the largest molded connector,
strain relief, branch, and wire bundle that must traverse this route. Do not
remove a connector, splice a wire, compress a molded body, or exceed a
manufacturer bend radius to obtain a pass.

| ID | Required observation | Method / acceptance basis | Actual | Disposition |
| --- | --- | --- | --- | --- |
| LED-1 | Exact kit identity, revision, wiring diagram, connector IDs, and manufacturer handling/bend limits | Archive source and label the physical harness |  |  |
| LED-2 | Maximum connector, strain-relief, branch, and bundled-wire dimensions in three axes | Measure without squeezing; photograph measurement orientation |  |  |
| LED-3 | Unloaded feed through a 25.4 mm round, 38.1 mm-long representative passage with candidate entry/exit access | Gentle hand feed only; no tool pulling, disassembly, scraping, insulation damage, or bend-limit violation |  |  |
| LED-4 | Feed through the full local F1–G1 mockup with adjacent barrel/bolt installed and intended sequence | Record sequence, clearances, required service slack, retrieval, and repeat feed without hardware relocation |  |  |
| LED-5 | Electrical condition before and after feed | Use manufacturer check procedure; visual inspection alone is insufficient if an electrical test is specified |  |  |

A failed 25.4 mm feed is a design stop. Do not enlarge the passage or move
fixed panel features without new geometry and resistance checks.

## 7. Tool access, assembly, removal, and reassembly

Measure actual tools, not generic cylinders. Record driver/socket OD and
length, bit projection, chuck/body envelope, extension wobble, required
approach, turning or ratchet arc, barrel-orientation tool, depth gauge, and
extraction tool. A tool must reach without bearing on an uncredited thin wood
edge or damaging the LED harness.

Perform only an unloaded, independently supported mock assembly. Support
panels and loose members without using them as structural props. Keep hands
out of pinch paths. This checklist supplies no proof load.

| ID | Joint / operation | Required demonstration | Actual | Disposition |
| --- | --- | --- | --- | --- |
| A-1 | All distinct joint families | Actual drill/guide approach reaches both intersecting bores with the frozen datums and full member sections |  |  |
| A-2 | All 46 barrels | Insert to depth, identify orientation, align threads, retain during mating, start bolt by fingers, and extract without enlarging the bore |  |  |
| A-3 | Center post/header | Reach and recover all four deepest blind barrels with adjacent members represented |  |  |
| A-4 | Center principal/header | Reach the greater-than-41 mm recessed barrel/seat, support the washer fully, and remove bolt and barrel without damaging the 2.092 mm nominal edge-stock zone |  |  |
| A-5 | Outer header/post | Complete documented rim-first assembly on both hands; then remove and reinstall the serviced joint with rim, driver obstruction, and safe member support represented |  |  |
| A-6 | Twelve outer-rail rows | Install/remove actual CDE 6 1/2 in stacks without bottoming, cross-threading, trapped barrel, or blocked tool path |  |  |
| A-7 | Left service rails | Drill-guide, barrel-tool, bolt, and service-feed access coexist at both approved N = 42 mm stations |  |  |
| A-8 | Top-outer rows | Depth control and actual bolt installation preserve the accepted positive tip gap in all four rows |  |  |
| A-9 | Whole sequence | Every individual timber remains removable in the documented order while panels and remaining frame are independently supported |  |  |
| A-10 | Reassembly | Repeat only the predeclared unloaded cycle count; log thread, barrel, bore, seat, washer, and wood condition after each cycle |  |  |
| A-11 | Stuck-fastener recovery | Demonstrate a non-destructive recovery path on the mockup without hidden cutting, field reaming, or damage to fixed panels/services |  |  |

One successful cycle shows only that specimen and sequence. It does not assign
a service-cycle rating. Any final cycle count and damage limit must come from
the accepted qualification plan before results are judged.

## 8. Handoff and closure boundary

| ID | Required handoff | Acceptance rule | Actual | Disposition |
| --- | --- | --- | --- | --- |
| C-1 | Part-level raw log and photographs | Every result traces to one labeled item, lot, station family, instrument, observer, and date |  |  |
| C-2 | Hardware extrema and tolerance stacks | Minimum complete-thread overlap and tip gap computed by family from compatible worst cases; required engagement supplied separately by accepted resistance method |  |  |
| C-3 | Material map | Every member and sheet has identity, condition, dimensions, moisture/defects, and intended cut/station map |  |  |
| C-4 | Offcut records | Every required critical variant has predeclared geometry and an unedited result, including failures |  |  |
| C-5 | LED record | Complete intended harness passes or fails the exact candidate-only mock route without undocumented alteration |  |  |
| C-6 | Access/service record | Actual tools and safe support sequence cover assembly, removal, reassembly, and recovery for every exceptional family |  |  |
| C-7 | Engineering reconciliation | Measured inputs are inside the frozen analysis envelope; cut sections, joint resistance/stiffness, retained bolts, and response are rerun where affected |  |  |

Completion of measurements does not itself make the candidate DIY-ready.
BN-1 remains open if controlled or qualified material and resistance evidence
is missing. BN-2 remains open if any accepted stack, bore, service route, or
tool sequence lacks a complete physical path. Production machining waits for
both gates, the complete-joint and six-case checks, matching construction
documents, and explicit candidate selection.
