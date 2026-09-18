# Ordinary Chat planning handoff: floor-runner MVP

Prepared September 15, 2026. This is a self-contained planning packet for use
in ordinary ChatGPT Chat. It intentionally avoids repository implementation,
CAD generation, native structural solves, tests and release claims. Upload this
file to Chat and use the master prompt below. Return Chat's final decision packet
to Codex for implementation.

## Master prompt for Chat

> Help me complete the owner-controlled planning for the mini-MoonBoard
> floor-runner MVP described in this file. Work only from the frozen design,
> evidence and boundaries stated here. Do not redesign the frame, invent
> engineering capacities or tolerances, require external engineering review,
> reopen rejected alternatives, or claim that an unlisted connector action
> passes. Ask me one high-value question at a time when an owner decision is
> genuinely needed. Otherwise draft the requested checklists and instructions.
> Keep a running decision ledger. At the end, produce the exact structured
> `CHAT_TO_CODEX_DECISION_PACKET` requested near the bottom of this file.

## Project objective

Finish a practical, internally consistent, engineer-unreviewed conditional DIY
package for the selected `compact-floor-flush-development` model. The package
must match the repository's CAD, construction documents and viewer. It must
state its assumptions and limitations honestly. It is not an unconditional
safety rating, manufacturer qualification, inspection of delivered materials,
or verification of the actual floor.

The owner wants a rush-to-MVP path with minimal tangents. Previous designs and
failed investigations stay available as historical evidence, but no additional
frame comparison or alternate-connector search should be proposed unless a
fresh adopted criterion actually fails.

## Frozen physical design

The selected model is `compact-floor-flush-development`:

- four main plywood face panels and two whole kicker panels;
- solid 4x6 rear legs and solid 4x6 inclined side rims;
- single 2x6 center principals, header, top rail, split service rails and posts;
- two outboard single-2x6 floor runners;
- runner front ends flush to the outer-post plane;
- runner rear ends follow the rear-leg inclined back faces;
- lower side-rim ends flush to the post/header plane;
- rear-leg tops flush to the rear faces of the side rims;
- a 1:12 recess in each rear leg where it meets its runner;
- whole kickers, with no runner slots cut through them;
- twelve complete outward-facing bolt stacks;
- 24 Simpson ML24Z angles installed with 144 specified Simpson SDS25112 screws;
- 66 panel/kicker attachment axes; and
- no custom steel, doubled vertical stock, knee braces, floor anchor or
  friction-driven tie.

The main-face datum is 277 mm above the floor. This consists of 127 mm of loose
pad allowance and 150 mm of exposed kicker. The frame remains floor-supported;
the pads do not carry frame load.

## Fixed analysis scope

- Use the owner's explicit no-slip floor-support assumption.
- Normal floor contact may open.
- Do not claim measured floor friction, a qualified floor, or an installed
  anchor.
- The accepted panel and T-nut construction is the design basis. Do not reopen
  a panel campaign or T-nut study.
- Do not request a destructive test, failure-weight search, new whole-frame
  comparison or external engineering sign-off.
- Six fresh exact no-slip load cases remain Codex work. Chat may plan their
  acceptance ledger but may not claim results in advance.

The six planned cases are the established current response set: A12-left,
A12-rear, A12-forward, K12-right, K12-rear and A1-rear. A historical exact
A12-left finite-friction case converged and met 37 of 38 then-implemented
criteria, with a governing bolt lateral ratio of 0.8792 and sampled net-member
ratio of 0.7488. Its only implemented failure was a provisional projected-seat
diagnostic. That archive is comparison evidence only and must not be promoted
as the fresh no-slip result.

## Adopted gate posture

### Rim terminal cut

The historical quarter-depth projected-seat scalar gave a −4.970 mm margin.
Subsequent source review did not establish that its geometric mapping applies
to this supported terminal bevel. It is not evidence of physical failure and
is no longer an adopted release gate. Preserve it as a non-adopted sensitivity.

The current design instead needs exact retained-section, bearing, contact and
gross/net member checks. A missing bearing/contact path or a failed adopted
member/bearing comparison is a real stop. Chat must not invent a new resistance
equation.

### Rear-leg 1:12 recess

Keep the recess. The saved nominal diagnostic found 0.021506 MPa longitudinal
tension on the cut face and an inferred transverse component of approximately
0.000149 MPa. Sawn-lumber transverse-tension resistance was not established, so
this is an analytical limitation rather than a numerical pass. It is also not a
demonstrated physical failure.

Required practical controls are sound/check-free stock at the recess, a smooth
continuous cut and transition, no overcut, and rejection of splits or damage.
Gross/net member checks and receiver fit still must pass. Chat may improve the
wording and inspection workflow but may not invent an allowable stress.

### Runner/leg interface

Codex must audit the exact contact and bolt-mediated load path once. Contact
must be included when active, or saved/current relative motion must establish
that omission is inactive or conservative. Any required force with no modeled
and physical transfer path is a true stop.

### Commercial ML24Z angles

The design retains 24 ML24Z angles and exactly six specified SDS25112 screws per
angle. Listed catalog force interactions must be at or below 1.0 in every fresh
case. The saved historical floor-flush A12-left maximum listed interaction was
0.475515, but it does not replace the fresh cases.

The catalog does not provide a complete rating for the recovered separation and
force-parallel flange-couple actions. In the historical A12-left case, positive
separation appeared at six bearing-like stations; the largest was 192.549 N.
The largest example force-parallel couple was 12.052 N·m at the left outer base.
These values must be recomputed from the six fresh cases.

A completed catalog search found no drop-in commercial connector pair that
covers the complete wrench at all 24 stations. A34, GA, HGA, tension-tie and
strap alternatives either lacked a moment rating, required incompatible member
thickness/installation, or required a new multi-component load path. Do not
repeat connector shopping.

The owner must make one explicit planning decision: either accept the unlisted
separation/couple as a plainly disclosed, manufacturer-unqualified limitation
of this conditional DIY package, or keep it as the sole fabrication-release
blocker after listed checks pass. Acceptance does not transform the action into
a catalog pass and must not be described that way.

### True numerical stop conditions

Stop implementation only for one of these conditions:

- non-convergence of a required fresh case;
- an adopted demand/capacity ratio above 1.0;
- failed exact receiver, washer-seat, edge/end-distance or retained-section
  geometry;
- a missing physical load path;
- a delivered hardware stack that cannot meet documented body, seating,
  engagement or receiver limits; or
- current model artifacts that cannot be made mutually consistent.

An unsupported local method is not converted into a pass. It is replaced by an
applicable check where one exists or retained as an explicit analytical limit.

## Bolt geometry and hardware

The twelve bolted connections use these nominal stacks:

| Quantity | Nominal bolt | Joint |
| ---: | --- | --- |
| 4 | 1/2-13 x 8-inch partially threaded SAE J429 Grade 5 | Upper rim/leg |
| 4 | 3/8-16 x 4-inch partially threaded SAE J429 Grade 5 | Front runner/post |
| 4 | 3/8-16 x 4-1/2-inch partially threaded SAE J429 Grade 5 | Rear runner/leg |

Each bolt receives one matching Grade 5 nut and two matching Grade 5 USS
washers. The twelve stacks therefore need four half-inch nuts, eight half-inch
washers, eight three-eighths nuts and sixteen three-eighths washers. Nominal
bolt length is not enough to accept delivered hardware.

Existing nominal dimensional budgets are:

| Joint | Nominal grip | Required full body to first transition | Extra thread/runout budget at shortest bolt | Nominal tip beyond nut |
| --- | ---: | ---: | ---: | ---: |
| Upper | 177.800 mm | 158.928 mm | 1.600 mm | 2.743 mm |
| Front | 76.200 mm | 69.317 mm | 5.359 mm | 10.033 mm |
| Rear | 88.900 mm | 78.842 mm | 7.518 mm | 9.017 mm |

These are conditional nominal budgets, not guaranteed delivered dimensions or
released shop tolerances. Actual stock grip, smooth body to first thread/runout,
usable thread start, washer dimensions, nut height and complete thread
engagement must be measured. Increased grip consumes tip projection directly.
No generic steel-joint torque or preload is assigned; tighten snugly without
crushing wood and follow applicable hardware instructions.

## Bolt placement planning

The nominal pair-spacing comparisons are:

| Pair | Nominal pitch | Adopted spacing screen | Nominal margin |
| --- | ---: | ---: | ---: |
| Upper rim/leg | 56.000 mm | 50.800 mm | 5.200 mm |
| Front runner/post | 39.500 mm | 38.100 mm | 1.400 mm |
| Rear runner/leg | 44.365 mm | 38.100 mm | 6.265 mm |

The previous generic independent ±1 mm position radius could reduce the front
pair to 37.5 mm, below its 38.1 mm screen. The mathematical independent-error
ceiling for spacing alone is 0.7 mm with zero remaining spacing margin; it is
not a released shop tolerance. A common paired-hole fixture can preserve pitch,
but completed holes must still be measured for pitch, registration, angularity,
receiver alignment, edge/end distance and washer seating.

Chat should draft a practical jig-and-inspection workflow without selecting a
final numeric tolerance that has not been verified by Codex against the entire
geometry. Use explicit placeholders such as `CODEX_TO_CONFIRM` where the final
CAD-derived acceptance range is still required. Do not suggest elongating holes
or pulling misaligned pieces together with bolts.

## Purchased panel screws

The owner purchased Lowe's item 755741, Fas-n-Tite/Hillman model 42605, UPC
00038902075949: #10 x 2-1/2-inch carbon-steel exterior deck screws with gray
ceramic coating, coarse threads, flat heads and #2 Phillips drive.

Use them at the 66 panel/kicker axes within the owner's accepted panel scope.
They do not replace any of the 144 Simpson SDS25112 angle screws. Public data do
not supply the structural design values needed to transfer SPAX capacity or
stiffness claims. The package must not make that transfer.

The modeled panel thickness is 18.25625 mm. A 63.5 mm screw then has 45.24375 mm
nominal timber penetration. The preceding selected model showed ample receiver
depth, but Codex must verify all 66 exact axes against the floor-runner model
before release. Require flush seating without crushing the face veneer. No
separate countersink or pilot dimension is released from retailer data.

Product record:

- <https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-50-Count/999995042>

## Crash pads

The owner built two portable pads, each 48 x 72 x 5 inches. They sit side by
side and provide a nominal 96 x 72-inch footprint. The seam runs front to back.

Each nominal stack, top to bottom, is:

1. two 0.5-inch layers of black 1.7 lb/ft3 polyethylene foam;
2. one 3-inch 44-ILD polyurethane foam core; and
3. two 0.5-inch layers of the same polyethylene foam.

Purchased material:

- two 36 x 96 x 3-inch polyurethane pieces, Amazon ASIN B071LMCHX3;
- eight 48 x 108 x 0.5-inch polyethylene sheets from ADR Packaging in Utah,
  four sheets per finished pad.

The owner followed the Crag Crafts DIY highball-pad guide:
<https://www.youtube.com/watch?v=_MYbZUr4orU>.

The viewer should show only each finished rectangular footprint and nominal
five-inch thickness. Do not invent cover construction, hinge behavior, internal
foam joints, handles or closures. Do not claim impact attenuation, critical
fall height, seam performance or certification. Pads are not structural frame
supports and are excluded from frame mass.

## Current stock inventory

The saved model inventory contains 20 timber pieces and six plywood pieces.
Dimensions below are model blank envelopes, not optimized purchase lengths or
released finished cutting tolerances.

| Quantity | Member | Nominal stock / modeled section | Blank envelope length |
| ---: | --- | --- | ---: |
| 2 | Outer side rims | Solid 4x6 / 88.9 x 139.7 mm | 2570.726 mm |
| 2 | Rear legs | Solid 4x6 / 88.9 x 139.7 mm | 2028.463 mm |
| 2 | Center principals | 2x6 / 38.1 x 139.7 mm | 2532.626 mm |
| 1 | Header | 2x6 / 38.1 x 139.7 mm | 2438.4 mm |
| 1 | Top rail | 2x6 / 38.1 x 139.7 mm | 2260.6 mm |
| 6 | Bottom/service half-rails | 2x6 / 38.1 x 139.7 mm | 1041.25 mm |
| 4 | Outer/center posts | 2x6 / 38.1 x 139.7 mm | 238.9 mm |
| 2 | Floor runners | 2x6 / 38.1 x 139.7 mm | 1815.646 mm maximum finished outline |
| 4 | Main panels | Owned plywood / 18.25625 mm | 1219.2 x 1219.2 mm |
| 2 | Whole kickers | Same plywood | 1219.2 x 277 mm |

Chat may turn this into receiving and labeling checklists. Do not infer saw
kerf, stock optimization, purchase lengths, actual grade or actual moisture
condition without asking the owner.

## Known member geometry useful for planning

- Runner front plane: assembly Y = -175.7 mm.
- Runner rear face at floor Z = 0: Y = 1639.946483 mm.
- Runner rear face at Z = 139.7 mm: Y = 1605.538528 mm.
- Runner bottom outline: 1815.646483 mm.
- Runner top outline: 1781.238528 mm.
- The rear runner end is inclined across its depth, not a square crosscut.
- Each leg recess removes at most 38.1 mm from 88.9 mm stock, leaving 50.8 mm
  nominal thickness.
- Recess runout is 457.2 mm along grain at 1:12.
- Recess grain datum runs from A = 180.342661 mm to A = 637.542661 mm, measured
  along the leg from its lowest raw grain station, not vertically from floor.
- The modeled runner clearance above the recess is 2 mm. This is CAD geometry,
  not permission for additional cutting.
- All assembly coordinates must be converted into member-local shop datums by
  Codex-generated sheets. Chat must not treat assembly coordinates as dimensions
  from a sawn end.

## Planned assembly logic

Chat should refine this sequence for usability without changing engineering:

1. Freeze one revision and verify that model, manifest, drawings and guide agree.
2. Receive, inspect and label stock and hardware.
3. Mark left/right, inside/outside, floor/top and grain datums.
4. Make verified profiles before drilling joint holes.
5. Dry-assemble the header, posts, runners, rims and legs on flat temporary
   support; confirm flush faces, direct bearing and the 277 mm face datum.
6. Drill paired connections using verified fixtures and inspect every finished
   hole before inserting bolts.
7. Install complete bolt stacks and all 24 angles with their six specified SDS
   screws each.
8. Add rails, principals, panels and kickers; install all 66 Hillman screws at
   verified axes.
9. Route services clear of bolt tips and preserve LED access.
10. Place the two loose pads side by side with the seam front to back.
11. Record final geometry, hardware and condition inspection; reassess rather
    than improvising any departure.

Chat may ask about available saws, drill guides, clamps, work area, lifting help
and measuring tools because those answers improve the practical guide. It may
not choose unsafe freehand methods, defeat guards, assign bolt torque or turn a
CAD occupied diameter into a drill-bit instruction.

## Planning work that Chat should complete

### 1. Owner decision ledger

Ask only questions that change the package. At minimum, settle:

- whether the ML24Z unlisted separation/couple is accepted as a disclosed DIY
  limitation or retained as the sole fabrication-release blocker;
- which saw, drilling guide/jig, clamps and measuring tools are actually
  available;
- whether lumber and bolts are already purchased and can be measured before
  final instructions;
- how many capable people and what temporary support are available for assembly;
- whether unknown pad-cover/internal-joint details should remain intentionally
  omitted from the viewer and structural package; and
- preferred inspection-record format: printable checklist, phone-friendly list,
  or both.

Do not ask preference questions whose answers cannot affect implementation.

### 2. Fabrication workflow draft

Produce a concise workflow for labeling, template preparation, paired drilling,
profile cutting, dry fit and rejection/rework. Mark every unresolved numerical
limit `CODEX_TO_CONFIRM`. Never recommend slotting, oversizing or redrilling a
failed structural hole without reassessment.

### 3. Receiving and measurement sheets

Create printable tables for:

- lumber identity, nominal/actual section, grade stamp, visible checks/splits,
  twist/cup/bow, moisture if the owner has a meter, and acceptance status;
- bolt nominal size, actual overall length, smooth body to first transition,
  thread/runout start, usable threads, washer dimensions, nut height, assembled
  grip, tip projection and acceptance status;
- ML24Z and SDS part identification and count; and
- Hillman screw identity, count, coating condition and seating trial.

Do not invent acceptance numbers beyond those supplied here. Use
`CODEX_TO_CONFIRM` or `OWNER_TO_MEASURE` as appropriate.

### 4. Assembly and inspection checklists

Draft practical pre-cut, post-cut, post-drill, dry-fit, final-assembly and
periodic-condition checklists. Distinguish:

- design/CAD checks Codex must complete;
- delivered-material checks the owner must perform;
- installation observations;
- stop-work/reassessment triggers; and
- disclosed analytical limitations that are not shop measurements.

### 5. Viewer and documentation acceptance checklist

The current repository still treats the spliced-knee branch as selected until
Codex performs authority promotion. Draft a checklist requiring the final
floor-runner package to show:

- `compact-floor-flush-development` as current default;
- exact full floor runners and whole kickers;
- correct flush end faces and 1:12 rear-leg recesses;
- twelve bolt stacks, 24 ML24Z angles and 144 SDS screws;
- 66 Hillman panel/kicker screws, without a false SPAX capacity claim;
- two 48 x 72 x 5-inch pads, side by side, seam front to back;
- matching counts, weight treatment, identifiers and document links; and
- a visible conditional-development limitation, not a construction-certified
  or manufacturer-qualified label.

### 6. Codex implementation brief

Convert the settled owner decisions and drafted checklists into a short,
unambiguous instruction set for Codex. Do not write source code or patches.
Separate repository actions from owner/shop actions. Preserve the task order:

1. promote floor-runner authority;
2. freeze adopted criteria;
3. close CAD/hardware/fabrication geometry;
4. run fresh no-slip A12-left;
5. run the other five cases;
6. consolidate the six-case and ML24Z ledgers;
7. regenerate viewer and construction package; and
8. run tests, lint, CAD/export/browser checks and independent review.

## Forbidden tangents

Do not propose or investigate:

- spliced-knee restoration;
- floor-uncut, fitted-block or wedge branches;
- 2x12 legs, steel shoes or insert conversions;
- new gussets, straps, angles or commercial connector searches;
- a new panel/T-nut qualification campaign;
- measured floor-friction testing;
- failure-weight or climber-rating calculations;
- crash-pad certification or impact testing;
- speculative lumber enlargement;
- publication, commit or push workflows; or
- treating unsupported capacity as zero or infinite.

If an owner request conflicts with the frozen design, record it under
`SCOPE_CHANGE_REQUESTS` rather than silently modifying the plan.

## Required final Chat output

At the end of the planning conversation, emit one Markdown block beginning with
this exact heading:

```text
# CHAT_TO_CODEX_DECISION_PACKET
```

Use these exact sections:

1. `OWNER_DECISIONS`
2. `UNCHANGED_DESIGN`
3. `ML24Z_RISK_DISPOSITION`
4. `AVAILABLE_SHOP_TOOLS_AND_HELP`
5. `OWNER_MEASUREMENTS_AVAILABLE_NOW`
6. `FABRICATION_WORKFLOW`
7. `RECEIVING_AND_MEASUREMENT_TABLES`
8. `ASSEMBLY_SEQUENCE`
9. `INSPECTION_AND_STOP_WORK_RULES`
10. `VIEWER_AND_DOCUMENT_ACCEPTANCE`
11. `CODEX_IMPLEMENTATION_BRIEF`
12. `CODEX_TO_CONFIRM`
13. `OWNER_TO_MEASURE_OR_CONFIRM`
14. `SCOPE_CHANGE_REQUESTS`

Use explicit statements, tables and checkboxes. Do not hide unresolved items in
prose. Include no numerical structural pass claims beyond evidence stated in
this packet. End with `READY_FOR_CODEX: YES` only if all owner-controlled choices
needed for implementation have answers. Otherwise end with `READY_FOR_CODEX: NO`
and list only the unanswered owner choices.

## Repository work reserved for Codex

The following cannot be completed by ordinary Chat from this packet:

- editing and validating repository authority files;
- checking exact CAD intersections, receivers, washer seats and member-local
  datums;
- establishing the final complete tolerance envelope;
- auditing runner/leg contact from model outputs;
- running and authenticating the six no-slip structural cases;
- calculating the fresh six-case ML24Z ledger;
- generating CAD, drawings, manifests, construction artifacts and viewer files;
- running focused/full tests, Ruff, rebuilds and browser checks; and
- reviewing the final repository diff for internal consistency.

Those tasks should be performed in one concentrated Codex implementation phase
after Chat returns the decision packet.
