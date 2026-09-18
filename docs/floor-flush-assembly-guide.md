# Flush floor-beam candidate: workshop planning guide

**Current selected-development draft; not a fabrication release.**
The [build-package status](floor-flush-build-package.md) controls this guide.
Six fresh no-slip cases pass all 36 frozen adopted checks, and nominal FR-3
CAD/shop geometry is complete. The [shop checklist](floor-flush-shop-checklist.md)
is the staged cut/drill/assembly handoff. Delivered hardware and fabricated
work still require inspection. Catalog-unlisted ML24Z/SDS actions are disclosed
limits, not additional capacity passes. This proposed sequence does not
authorize fabrication. See the [completion ledger](floor-runner-mvp-completion-ledger.md).

## Use one matching model

Open the local viewer with `?model=compact-floor-flush-development&view=rear`.
The preserved [parts inventory](../site/hybrid/compact-floor-flush-development/parts.json)
and [artifact manifest](../site/hybrid/compact-floor-flush-development/manifest.json)
identify the current geometry. Earlier `floortaper` construction sheets have
**different runner ends, leg tops and all three bolt-pair layouts**. They are
historical references, not current drilling templates. The [current draft construction packet](floor-flush-construction/) supplies
member-local cut/bolt sheets. Verify its manifest, scale-verification marks and
profile annotations before treating any drawing as a template; draft sheets
do not close delivered-item inspection or fabrication-allowance conditions.
The [shop checklist](floor-flush-shop-checklist.md) maps each operation to those
sheets. Occupied CAD diameters stay in `modeled_diameter_mm`; finished bolt-hole
range, purchased Hillman length and SDS wood-lead-hole rules are the `shop_*`
columns.

Assembly coordinates are millimetres: X spans the board, Z is height above the
floor, and Y runs front to rear. X = 0 is the board centre. Label left/right,
inside/outside and floor ends before laying out mirrored parts. Assembly Y/Z
coordinates must be converted to each actual member's marked datums; do not
use them as distances from a sawn end.

## Stock planning inventory

These quantities come from the selected floor-flush model. Listed lengths are model blank
envelopes, without saw kerf, trimming allowance or a lumber cutting optimization.
In particular, rim and leg envelope lengths are inherited blanks, not the new
flush finished lengths. Lumber species, grade, condition and minimum finished
sections must match the final calculation basis; nominal stock names alone do
not establish those properties.

| Quantity | Member | Nominal stock / model cross-section | Blank envelope length, mm |
| ---: | --- | --- | ---: |
| 2 | Outer side rims | Solid 4×6 / 88.9 × 139.7 mm | 2570.726 |
| 2 | Rear legs | Solid 4×6 / 88.9 × 139.7 mm | 2028.463 |
| 2 | Centre principals | 2×6 / 38.1 × 139.7 mm | 2532.626 |
| 1 | Header | 2×6 / 38.1 × 139.7 mm | 2438.4 |
| 1 | Top rail | 2×6 / 38.1 × 139.7 mm | 2260.6 |
| 6 | Bottom and service half-rails | 2×6 / 38.1 × 139.7 mm | 1041.25 |
| 4 | Outer and centre posts | 2×6 / 38.1 × 139.7 mm | 238.9 |
| 2 | Floor runners | 2×6 / 38.1 × 139.7 mm | 1815.646 maximum finished outline |
| 4 | Main panels | Owned 23/32 CAT plywood, modeled 18.25625 mm | 1219.2 × 1219.2 |
| 2 | Whole kicker panels | Same plywood | 1219.2 × 277 |

There are 20 timber pieces and six plywood pieces. No doubled vertical stock,
custom steel shoe, raised knee or kicker notch belongs to this candidate.
Retain the accepted panel/T-nut construction; do not substitute a new plywood
purchase specification based on a historical comparison.

## Consolidated hardware inventory

This is a count and specification reference, not an assertion of supplier stock
or delivered-lot suitability. The twelve joints use one nut and two washers
per bolt, with heads inward and nuts/threaded tips outward.

| Quantity | Item | Location / local specification |
| ---: | --- | --- |
| 4 | ½-13 × 8-inch partially threaded SAE J429 Grade 5 bolts | Upper rim/leg joints; Bolt Depot 407 reference |
| 4 | Matching ½-13 Grade 5 nuts | Bolt Depot 2573 reference |
| 8 | ½-inch Grade 5 USS washers | Bolt Depot 15025 reference |
| 4 | ⅜-16 × 4-inch partially threaded Grade 5 bolts | Front runner/post joints; Bolt Depot 367 reference |
| 4 | ⅜-16 × 4½-inch partially threaded Grade 5 bolts | Rear runner/leg joints; Bolt Depot 368 reference |
| 8 | Matching ⅜-16 Grade 5 nuts | Bolt Depot 2571 reference |
| 16 | ⅜-inch Grade 5 USS washers | Bolt Depot 15023 reference |
| 24 | Simpson ML24Z angles | All retained commercial timber connections |
| 144 | Specified SDS25112 screws | Six per ML24Z; no generic substitution |
| 66 | Fas-n-Tite/Hillman 42605 #10 × 2-1/2-inch deck screws | 48 main-panel screws and nine per kicker; accepted panel scope only; CSV `modeled_length_mm` 50.8 mm is not this length |
| 142 | Modeled owned-type Escape T-nuts | Accepted panel basis; not 142 additional through-bolts |
| 2 | Crash pads, each 48 × 72 × 5 inches | Side by side; front-to-back centre seam; separate from structural support and frame mass |

The [half-inch hardware assessment](compact-half-inch-hardware.md) and
[runner hardware assessment](floor-runner-recess-hardware.md) contain catalog
references, washer dimensions, material assumptions and delivered-shank checks.
Nominal bolt length is not enough: actual shank, thread runout, wood grip,
washers and nut height must let the nut tighten with complete threads extending
past it while meeting the adopted thread-bearing limit. The rejected 5-inch
rear-bolt/minimum-thread stack is not an alternate purchase option.

Before installation, inspect delivered hardware against the recorded budgets:
minimum full smooth-body lengths to the first thread transition are 158.928 mm
(upper), 69.317 mm (front) and 78.842 mm (rear); extra thread/runout budgets are
1.600, 5.359 and 7.518 mm; and shortest-stack tip budgets beyond the nut are
2.743, 10.033 and 9.017 mm. Measure actual shank, runout, wood grip, nut height
and thread beyond the nut. Verify the maximum washer envelopes still have full,
flat seating on sound timber: upper washer thickness may be 3.3528 mm with the
catalog radius 0.0635 mm above modeled, and smaller washers may be 2.6416 mm
with catalog radius 0.381 mm above modeled. Reject incompatible or rocking stacks; do not
elongate holes or improvise spacers.

Hold bolts are not installed geometry in this model. Retain the accepted
hold-system instructions and owned kit; do not infer bolt lengths per hold
from T-nut counts. LED wiring remains a separate service assembly; retain its
harness and connector clearances, with no invented electrical shopping list.

## Cut geometry to review before shop work

- The runner front plane is Y = −175.7. Each runner rear end follows the rear
  leg face: Y = 1639.946483 at floor Z = 0 and Y = 1605.538528 at Z = 139.7.
  Thus its bottom edge is 1815.646483 mm long and top edge 1781.238528 mm long.
  This is an inclined end across the runner depth, not a square rear crosscut.
- The lower side-rim plane also ends at Y = −175.7. Its remaining normal depth
  is 102.805 mm. The historical projected-seat scalar is a non-adopted
  sensitivity. The adopted fresh-case and nominal shop checks pass; cut only
  after actual stock, saw setup and finished tolerances satisfy the controls.
- Leg tops terminate on the rim rear face; the previous 18 mm normal projection
  is removed. Both upper bolt axes have moved. A previous leg sheet cannot be
  shortened and reused for drilling.
- Each leg recess opens at the foot on its **inner** face. Maximum removal is
  38.1 mm from 88.9 mm stock, leaving 50.8 mm nominal thickness. The runout is
  457.2 mm along grain, a 1:12 slope. It starts at grain datum A = 180.342661 mm
  and reaches full stock at A = 637.542661 mm. A is measured along the leg grain
  from its lowest raw grain station, not vertically from the floor. Use the
  actual two-face template to locate it on a bevel-footed leg.
- The modeled clearance above the runner is 2 mm. This is a CAD gap, not a
  released cutting tolerance or permission to remove an extra 2 mm everywhere.
  Preserve the 3 mm allowance used in geometry screening as an analysis input;
  it is not a blanket ±3 mm shop tolerance.

- For each mirrored front runner/post pair, use one registered paired-hole
  fixture and inspect finished centres. Accept 39.0–40.0 mm pitch, pair
  midpoint within 0.5 mm of datum, and each hole within 0.5 mm perpendicular to
  the pair line. Practical registration: dry-fit the runner and outer post,
  make a rigid two-hole fixture at 39.5 mm along the sheet pair line, clamp
  through both members, drill from one side with a guide, then measure finished
  centres with pins in the holes (calipers for pitch, rule for midpoint, square
  for perpendicular offset). Reject and reassess any failure; never elongate a
  hole. Apply the corresponding receiver and washer checks to the rear and
  upper pairs; those pairs have no separate 39.0–40.0 mm pitch rule.

- Inspect each 1:12 recess and its transition before drilling. Stock must be
  sound and check-free, the transition smooth and continuous, and the cut free
  of overcut, split, tear-out or damaged bearing surface. Reject or reassess
  defects; do not deepen the recess as a repair.

## Saw choice for the leg taper

A sharp full-size rip hand saw, followed by a plane or sharp chisel for the
last waste, is a practical option for this long, shallow cut. It permits a
controlled stop at the full-stock transition. Mark the profile on both sides,
clamp the timber, and work on the waste side of the line while checking both
marks. This is a workshop recommendation based on the modeled cut, not a
qualification of its structural resistance.

A portable circular saw can assist with waste removal only when its actual
cutting capacity, support and guide arrangement suit the work. The sloping
cut plane spans the leg's 139.7 mm width: **38.1 mm recess depth is not the
through-cut thickness**. Do not assume an ordinary circular saw will make
that plane in one pass. Finishing by hand avoids extending a circular blade's
curved kerf beyond the end of the specified runout. A bandsaw with adequate
capacity and stable long-stock support is another workshop option; a table saw
would need a purpose-made secure taper setup. Tool ownership and a trial in
scrap should decide the method, not an unsupported freehand pass.

Use the saw's operating instructions and functioning guards. OSHA's
[handheld-saw guidance](https://www.osha.gov/etools/machine-guarding/saws/handheld)
identifies the upper/retracting lower guards and directs the blade away from
nearby people. No step here calls for defeating a guard. Recorded FR-3 rules
govern nominal fit and fixture acceptance; actual stock, saw setup, finished
cuts and hardware still require the documented shop observations.

## Proposed assembly sequence subject to recorded installation controls

1. **Freeze the packet.** Record the selected model identifier and manifest;
   verify all cut sheets, hardware schedule and instructions describe that same
   revision. Choose official Mini 4×4 sheets or the 4×8 kerf-right sheets
   ([width option](floor-flush-width-option.md)); do not mix them. Confirm the
   matching case evidence and apply the documented stock, cut, hole and
   delivered-hardware controls on the
   [shop checklist](floor-flush-shop-checklist.md) before cutting stock. Official
   six-case evidence applies only to the 4×4 presentation.
2. **Receive and label stock.** Check actual sections against the documented
   minimums, identify grain direction and damaged connection regions, and label
   the mirrored member faces. Lay out from the final member-local datums.
3. **Make profiles before joint drilling.** Cut the feet, proposed flush ends
   and continuous recess tapers from the matching current sheets. Check the remaining
   sections and end geometry before placing holes. Retain full kicker outlines.
4. **Dry-assemble the base and side joints on a flat support.** Locate the
   header/posts, rims, legs and outboard runners. Verify the 277 mm main-face
   datum, flush faces, actual bearing interfaces and intended runner-top gap.
   Temporarily support the frame against movement while it lacks its complete
   connections; panels and crash pads are not temporary structural props.
5. **Lay out all twelve bolts from the current sheets.** Verify edge/end
   distances on actual timber, washer-seat clearance and drilling access. CAD
   occupied diameters are not bit catalog numbers. Finished bolt holes follow
   [NDS §12.1.3](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf):
   D+1/32 to D+1/16 inch. The CSV/CAD values 14.2875 mm (½-inch) and
   11.1125 mm (⅜-inch) are the upper end of that range. Measure the finished
   hole. Apply the paired-hole acceptance rule above. Do not elongate holes to
   pull misaligned parts together. The staged schedule is in the
   [shop checklist](floor-flush-shop-checklist.md).
6. **Install complete bolt stacks and all angle screws.** Confirm smooth-body
   coverage, usable nut threads and full washer seating. Seat snugly without
   crushing the timber; no generic steel-joint torque is assigned. Existing
   outer angle centres remain at Y = −105.85; listed-force checks pass, but
   unlisted separation and flange-couple demands have no catalog capacity.
   Drive SDS25112 with a 3/8-inch hex on a low-speed 1/2-inch drill. Clamp each
   purchased ML24Z and predrill the wood with a **5/32-inch** bit through the
   existing steel holes (Simpson’s catalog bit where a wood predrill is used).
   Occupied CAD 6.35 mm is not that bit. Do not independently predrill from CAD
   and then offer the angle up. Do not enlarge the steel holes. Hillman screws
   are not SDS replacements.
7. **Complete rails, principals and panel installation.** Keep the split centre
   service corridor, accepted T-nut construction, and independent panel seams.
   Use all 66 panel/kicker screws. The lower post kicker row is Z = 60 mm;
   retain the upper-post and header rows. Mark the upper post row from the
   actual post top; do not round it upward. Axis coordinates remain those in
   the [placement review](kicker-screw-placement-review.md); SPAX lead-hole,
   drive and end-distance product rules do not transfer to Hillman 42605.
   Confirm all 66 Hillman 42605 axes are contained in their receivers and no
   tip protrudes. The owner-selected installation is a lead-hole pilot plus
   plywood-face countersink so the flat head seats flush. Use the owner-chosen
   Kobalt 80277 / Lowe’s 1208451 **#10 insert (1/8 in pilot, 3/8 in
   countersink)**. Confirm on an offcut before the 66 holes. Occupied CAD
   diameter is not the pilot. Do not open a plywood clearance hole. Do not use
   that 1/8 in insert for SDS. `connection-axes.csv`
   `modeled_length_mm` 50.8 mm is a historical occupied envelope, not the
   purchased 63.5 mm length.
8. **Route services and install pads.** Keep the harness clear of bolt tips and
   preserve LED passages. Place two 48 × 72 × 5-inch pads side by side, spanning
   96 inches across by 72 inches in floor depth, with the centre seam running
   front to back. Their 127 mm thickness leaves 150 mm exposed kicker; they
   carry no frame load and are excluded from structural mass.
9. **Record the final inspection.** Check hardware counts, flush faces, retained
   sections, hole locations, washer seating, intended contacts/gaps and wiring
   access against the matching current packet. Record departures for assessment
   rather than silently modifying the joint. Recheck loose hardware, split wood or
   crushed seats after initial settling, relocation or unusual impact.

The endpoint remains conditional, engineer-unreviewed DIY under the documented
loads, material and explicit no-slip floor support assumption. Normal floor
contact may open. This assumption does not qualify floor friction or imply an
installed anchor; earlier per-cell Coulomb cases remain historical evidence.
The [fabrication review](floor-flush-fabrication-review.md) records the current
dimensional budgets and the historical independent-error counterexample; the
adopted paired-fixture rule is in the criteria ledger and FR-3 shop checks.
This sequence adds no floor-friction test, panel requalification campaign or
external signoff requirement.
