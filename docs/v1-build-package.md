# V1 provisional build package

This is a complete *pre-audit* package for the user-directed indoor,
freestanding Mini MoonBoard v1. It supplies a reproducible 3D assembly,
drawings, cut/drill schedules, a purchasing estimate, and a build sequence.
It is deliberately not an approved structural design or authorization to
build or climb. Every guess below is tagged **provisional** and appears in the
human-audit list at the end.

## Controlled geometry

| Item | V1 value | Basis |
| --- | ---: | --- |
| Main board | 2436.0 x 2436.0 mm actual v1 stock route at 40 degrees from vertical | Two 1218.0 mm panels per direction leave 2.4 mm total rip allowance in a 96-in sheet; official dimensions remain nominal |
| Kicker | 225 mm total | 150 mm official active zone + user-estimated 75 mm blank extension |
| Main-surface top (climbing face) | 2092.9 mm above floor | Derived from the face-aligned kicker/main seam, 48-in panels, and 40-degree angle |
| Exterior legs | Two, one per board side | User direction |
| Leg bend | Main-grid row 8 | Fifth T-nut row down from row 12 |
| Leg upper end | Main-grid row 10 | Two T-nut rows above the bend |
| Lower-leg angle | 60 degrees to the descending board line | User estimate |
| Lower-leg endpoint centre datum | 1389.6 mm behind kicker face and 0 mm above floor | CAD-derived; the overlong lower member is trimmed at the finished-floor plane, producing a full flat bearing face |
| Leg knee | Lower and upper segments meet at row-8 bend | 450 x 450 mm two-ply exterior knee plate; four 3/8-in through-bolts per leg, 70 and 220 mm along each member from the bend; provisional load path |
| Support member | Two nominal-3/4-in plywood laminations, modelled as 36 mm total | User direction; actual thickness unknown |
| Support-side rails | Four outer/intermediate rails plus one shifted center-seam rail, board-parallel, 180 mm nominal width | Rails sit on the true support side of the underside climbing face |
| Rail bearing blocks | 20 two-ply 60 x 80 mm blocks | CAD-contacted from panel to rail across the service gap; projected clearance from all bores is tested |
| Kicker/main gussets | Two exterior 36 mm-thick triangular side gussets | Each touches the vertical kicker and first 400 mm of the inclined main-panel side edge; four provisional screws per panel edge require human audit |
| Leg cross ties | Three rows of two 1309.2 mm halves, center-spliced and board-normal | Tie solids terminate at leg faces and do not overlap other frame solids |
| Rail cross ties | Three rows of two 1309.2 mm halves, center-spliced and board-normal | Each half touches three rails; the rail grid transfers through outer rails to the leg-bolt path |
| Rail splices | Five 36 mm-thick, 400 mm-long outer cover plates | Each physically bridges its lower/upper rail pair; fastener pattern remains a human-audit item |

The model keeps a **36 mm provisional board-normal service gap** on the
support side, opposite the underside climbing face, for T-nut, LED, and cable
clearance. Twenty discrete bearing blocks bridge this gap; their projected
edges maintain a tested 20 mm clearance beyond every CAD bore. This remains a
geometry check, not proof that the purchased T-nut flange, LED body, cable,
and fasteners fit; verify those items on an offcut.

Every long support-side rail is modelled parallel to the board: 40 degrees
from vertical. The support-side elevation depicts those rails straight-on, so
they appear vertical there; use the side plan or STEP model to judge their
actual 40-degree orientation.

### Structural-coordinate datum

The connection schedule uses CAD datum **O**: the intersection of the board
centreline (`X=0`), the vertical plane of the kicker front face (`Y=0`), and
the finished-floor plane (`Z=0`). Positive X is to the right while facing the
climbing surface, positive Y is rearward, and positive Z is upward. Each CSV
coordinate uses the midpoint of the modeled leg-and-rail bolt stack for X and
the clearance-hole centerline for Y/Z; the bolt axis is X. The exterior
support-side rail center plane is 54 mm along the transformed support normal
from the main-panel support plane (36 mm service gap plus 18 mm rail half-thickness).
This datum is for audit transfer only, not authorization to drill.

## Generated deliverables

Run the following from the repository root to regenerate every deliverable:

```bash
uv run python -m mini_moonboard.export
```

| File | Purpose |
| --- | --- |
| [`mini_moonboard_v1_concept.step`](../exports/mini_moonboard_v1_concept.step) | 3D CAD assembly: underside-face panels, legs, rails, bearing blocks, kicker backing, seam gussets, and rear ties |
| [`mini_moonboard_v1_front.svg`](../exports/mini_moonboard_v1_front.svg) | Underside climbing-face elevation |
| [`mini_moonboard_v1_concept_side.svg`](../exports/mini_moonboard_v1_concept_side.svg) | Side plan: leg datums and 60-degree assumption |
| [`mini_moonboard_v1_isometric.svg`](../exports/mini_moonboard_v1_isometric.svg) | Isometric support-side schematic; use STEP or CAD-derived raster for exact geometry |
| [`mini_moonboard_v1_rear.svg`](../exports/mini_moonboard_v1_rear.svg) | Support-side elevation: five rails, bearing-block service gap, and tie/splice intent |
| [`mini_moonboard_v1_cut_list.csv`](../exports/mini_moonboard_v1_cut_list.csv) | Lamination-expanded provisional plywood cut list |
| [`mini_moonboard_v1_drill_schedule.csv`](../exports/mini_moonboard_v1_drill_schedule.csv) | 132 main T-nut, 132 LED, and 10 kicker-hole center records |
| [`mini_moonboard_v1_connection_schedule.csv`](../exports/mini_moonboard_v1_connection_schedule.csv) | Eight leg-to-rail bolts, eight knee-plate bolts, and forty panel/rail screw datums |
| [`mini_moonboard_v1_bom.csv`](../exports/mini_moonboard_v1_bom.csv) | Provisional purchasing BOM, separate from plywood cuts |
| [`v1-sheet-nesting.md`](v1-sheet-nesting.md) | Ten-sheet purchase and cut layout, including the required 2.4 mm maximum single main-panel kerf |
| [`v1-secondary-joinery.md`](v1-secondary-joinery.md) | Relative-coordinate fastener pattern for rail splices/ties, kicker backing, and seam gussets |
| [`v1-led-installation.md`](v1-led-installation.md) | Source-backed V5 string order, service-gap routing, and received-kit audit |

The CSV drill coordinates are a machine-readable cross-check of the official
metric datums, not drill authority. V1's selected Escape 3/8-16 hardware
requires the official **imperial** Mini template unless the hardware system is
changed under controlled revision. Print that template at 100 percent and
verify its calibration dimensions. The controlled 2436.0 mm V1 blank is not
the published 2438.8 mm imperial template width: before any production
drilling, record calibration marks, final blank trim, center-seam location,
and template-to-blank offsets. Do not combine the PDF template and CSV by eye
or substitute converted values for template dimensions.

The CAD carries the 142 hold/T-nut and 132 LED through-bores, which are the
physical provisions for those systems. It intentionally does not invent the
shape, bolt length, or clearance envelope of a hold that has not been selected,
nor a V5 controller/cable route whose supplied installation guide has not been
measured. Those are installation verification items, not absent panel features.

## Provisional purchasing estimate

This is a quantity estimate, not a release-to-purchase BOM.

| Item | Quantity | V1 assumption / action |
| --- | ---: | --- |
| 3/4-in, 4 x 8 birch plywood | **10 sheets** | See the sheet-by-sheet nesting plan; measure raw stock first and use a single main-panel separating kerf no greater than 2.4 mm. |
| Escape 3-hole screw-in T-nuts, 3/8-16 | 2 x 100 packs | 142 required positions plus spares; use the selected 7/16-in bore only after offcut test |
| 3/8-16 hold bolts | 142 minimum plus spares | Length mix must match the purchased hold set and 18 mm panel thickness |
| MoonBoard LED System | 1, SKU 60-201-V5 | User-selected kit; listing states 200 bulbs including 2 spares and 66 extra on Mini, reconciling to the 132 scheduled LED centres; supplied guide controls installation |
| Insulated screw-mounted cable saddles | 30 plus spares | Provisional 300 mm maximum spacing and every turn; mount to rear rails only after received-wire measurement |
| Leg-to-outer-rail structural bolts | 8 x 3/8-in Grade-5 x 10-in | **Provisional:** four per leg; full X/Y/Z hole-centre datums and a 10 mm clearance-hole assumption are in the connection schedule. Verify the actual washer/plate/nut stack and thread engagement before purchase. |
| Exterior knee-plate structural bolts | 8 x 3/8-in Grade-5 x 4-in | **Provisional:** four per leg clamp the two-ply 450 mm knee plate to the upper/lower leg members. Use the connection schedule; verify edge distances and actual washer/nut stack. |
| Panel-to-rail screws | 40 x #10 x 3.25-in structural wood screws | **Provisional:** two screws per bearing block, installed from rail exterior through block into panel. CAD limits nominal panel embedment to 10.55 mm; verify screw head, pilot, and no-face-breakout on an offcut. |
| Secondary joinery screws | 88 x #10 x 2.5-in and 8 x #10 x 2-in, plus 10% spare | Rail splice, tie, side-gusset, and kicker-backing patterns; see secondary joinery schedule. |
| Lamination adhesive | **unresolved** | **Provisional:** reviewer to select compatible wood adhesive, spread, clamping, cure, and environmental protection |
| Feet / anti-slip / floor protection | **unresolved** | Required because anchoring is prohibited |

If MoonBoard-branded T-nuts replace the selected Escape inserts, use Moon's
specified hardware system as a matched set: M10 metric, or its stated 3/8-in
imperial counterpart. Moon's generic build guidance lists a 13 mm / 1/2-in
bore and 10 mm barrel, unlike the selected Escape 7/16-in bore. Purchase the
required fixing screws separately, verify the product dimensions, and rerun
the offcut test; do not reuse this schedule's selected-Escape diameter without
that change record.

## Build sequence (draft for audit)

1. Inspect each plywood sheet; record actual length, width, thickness at
   multiple locations, flatness, damage, and grade. Reserve one offcut sheet.
2. Print and calibrate the official imperial template for the selected Escape
   3/8-16 system. Drill and test a sample
   panel with an Escape T-nut, matching 3/8-16 bolt, representative hold,
   Moon LED, and the proposed panel-to-rail screw. Confirm support-side clearance.
3. Cut panel and support blanks only after the fit test passes. Keep the full
   75 mm blank kicker extension below the official active kicker zone.
4. Glue and clamp each two-ply support member, including the two 450 x 450 mm
   knee plates, to the audited adhesive schedule; do not treat the 36 mm CAD
   thickness as an actual measured thickness. Locate the plate outside each
   leg, mark its four connection-schedule centers, drill 10 mm clearance holes,
   and use the provisional 3/8-in x 4-in Grade-5 bolt stack only after its fit
   and edge distances have been checked.
5. Dry-fit the two side legs, five support-side rails, twenty rail-bearing
   blocks, blank-kicker backing, exterior kicker/main seam gussets, and split
   leg cross ties and rail cross ties on a level protected floor. Check the
   full flat foot bearing faces, 60-degree leg angle, 1389.6 mm rear-foot
   position, racking, and all
   panel/LED/T-nut clearances.
6. Have the structural connection and unanchored-stability review completed
   before drilling structural bolt holes or joining any load-bearing member.
7. Assemble the support-side frame flat where practical, raise it with at
   least two people, and fasten every bearing block with two #10 x 3.25-in
   screws from the rail exterior. Use the connection schedule's 40 head-centre
   datums; test the exact screw on an offcut to confirm its tip does not break
   through the climbing face.
8. Install every remaining rail splice, tie, kicker backing, and side-gusset
   fastener to the relative centers in the secondary joinery schedule. Check
   that each contact face bears flush before fastening.
9. Drill final hold and LED holes using the calibrated template. Install and
   test the V5 strings/controller using the dedicated LED installation plan
   before final rear access is obstructed.
10. Complete a non-climbing inspection of all connections, wiring protection,
   panel seams, feet, and the separate impact-surface plan before any use.

## Human-audit gate

The following items prevent release as a build-ready design. The project may
continue as a geometry prototype while they are unresolved.

- Verify sheet stock is suitable and record actual min/mean/max thickness.
- Verify every 7/16-in Escape bore, screw, T-nut, hold bolt, LED, and cable on
  an offcut; the model does not prove physical clearance.
- Select and calculate/approve the specified structural bolt, washer, nut,
  plate, adhesive, splice, panel-screw, knee-joint, and foot details. In
  particular, prove the center splice in each support-side tie, the 450 mm
  knee-plate load transfer, and the four-bolt leg-to-rail connection.
- Calibrate the official imperial template for the selected Escape 3/8-16
  system, then record panel-blank trim, seam location, and every
  template-to-blank offset before drilling.
- Check all structural bolt locations against the final hold, T-nut, LED,
  wiring, and panel-seam layout; the T-nut rows locate leg geometry but are not
  structural-fastener locations.
- Prove the selected #10 x 3.25-in panel/rail screw on an offcut: the actual
  head must seat on the rail, its pilot must not split the block or panel, and
  its tip must stay clear of the climbing face, T-nut hardware, LED hardware,
  and wiring.
- Assess unanchored overturning, sliding, racking, floor bearing, anti-slip,
  and load spreading for intended use. No anchor may be added without a
  controlled revision.
- Confirm the selected Moon LED kit's supplied guide, controller mounting,
  switch access, power routing, and protection.
- Separately establish the impact surface/crash-pad arrangement before climbing;
  it is intentionally excluded from this board/frame package.
