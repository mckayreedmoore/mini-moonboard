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
| Main board | 2438.4 x 2438.4 mm actual v1 stock route at 40 degrees from vertical | Two factory-edge 48-in panels each direction; official dimensions remain nominal |
| Kicker | 225 mm total | 150 mm official active zone + user-estimated 75 mm blank extension |
| Main-surface top | 2092.9 mm above floor | Derived from the fixed kicker, 48-in panels, and official angle |
| Exterior legs | Two, one per board side | User direction |
| Leg bend | Main-grid row 8 | Fifth T-nut row down from row 12 |
| Leg upper end | Main-grid row 10 | Two T-nut rows above the bend |
| Lower-leg angle | 60 degrees to the descending board line | User estimate |
| Lower-leg endpoint centre datum | 1500 mm behind kicker face and 31.4 mm above floor | Derived provisional geometry; wood member meets the CAD floor plane but finished feet/contact detail remains unresolved |
| Support member | Two nominal-3/4-in plywood laminations, modelled as 36 mm total | User direction; actual thickness unknown |
| Face rails | Four outer/intermediate rails plus a center-seam rail, board-parallel, 180 mm nominal width | Video supports four lines; center-seam backing is added for panel attachment; width is provisional |
| Panel-joint braces | Three full-width board-parallel braces, 180 mm nominal width | Video plus Moon joint-bracing guidance; width is provisional |
| Rear ties | Three rows of two 1255.2 mm halves, center-spliced | Video supports transverse ties; splice is provisional |

The model keeps a **54 mm provisional gap** behind the panel face for T-nut,
LED, and cable clearance. It includes four conservative LED-string routing
envelopes and one controller envelope in the STEP model. They are routing and
clearance aids, not measured component geometry; do not reduce the gap or
mount hardware without a physical clearance check against the supplied kit.

### Structural-coordinate datum

The connection schedule uses CAD datum **O**: the intersection of the board
centreline (`X=0`), the vertical plane of the kicker front face (`Y=0`), and
the finished-floor plane (`Z=0`). Positive X is to the right while facing the
climbing surface, positive Y is rearward, and positive Z is upward. Each CSV
coordinate is the centre of a provisional structural-bolt clearance hole; the
bolt axis is X. The exterior face rails start behind the board at `Y=54 mm`;
each listed bolt is offset 18 mm along the rail normal to its 36 mm-thick
mid-plane.
This datum is for audit transfer only, not authorization to drill.

## Generated deliverables

Run the following from the repository root to regenerate every deliverable:

```bash
uv run python -m mini_moonboard.export
```

| File | Purpose |
| --- | --- |
| [`mini_moonboard_v1_concept.step`](../exports/mini_moonboard_v1_concept.step) | 3D CAD assembly: panels, legs, face rails, braces, and rear ties |
| [`mini_moonboard_v1_front.svg`](../exports/mini_moonboard_v1_front.svg) | Panel-facing dimensional plan |
| [`mini_moonboard_v1_concept_side.svg`](../exports/mini_moonboard_v1_concept_side.svg) | Side plan: leg datums and 60-degree assumption |
| [`mini_moonboard_v1_isometric.svg`](../exports/mini_moonboard_v1_isometric.svg) | Isometric visual review render of the assembled geometry |
| [`mini_moonboard_v1_rear.svg`](../exports/mini_moonboard_v1_rear.svg) | Rear plan: five face rails, braces, and tie/splice intent |
| [`mini_moonboard_v1_cut_list.csv`](../exports/mini_moonboard_v1_cut_list.csv) | Lamination-expanded provisional plywood cut list |
| [`mini_moonboard_v1_drill_schedule.csv`](../exports/mini_moonboard_v1_drill_schedule.csv) | 132 main T-nut, 132 LED, and 10 kicker-hole center records |
| [`mini_moonboard_v1_connection_schedule.csv`](../exports/mini_moonboard_v1_connection_schedule.csv) | Eight provisional leg-to-board structural-bolt datums |
| [`mini_moonboard_v1_bom.csv`](../exports/mini_moonboard_v1_bom.csv) | Provisional purchasing BOM, separate from plywood cuts |

The CSV drill coordinates are a machine-readable cross-check of the official
metric datums. For production, choose the official **imperial** Mini template,
print it at 100 percent, and verify its calibration dimensions. Do not combine
the PDF template and CSV by eye or substitute converted values for template
dimensions.

## Provisional purchasing estimate

This is a quantity estimate, not a release-to-purchase BOM.

| Item | Quantity | V1 assumption / action |
| --- | ---: | --- |
| 3/4-in, 4 x 8 birch plywood | **unresolved** | User-selected stock; the cut list is deliberately not a nesting plan. Purchase quantity must follow an audited sheet-by-sheet nesting layout and actual stock measurement. |
| Escape 3-hole screw-in T-nuts, 3/8-16 | 2 x 100 packs | 142 required positions plus spares; use the selected 7/16-in bore only after offcut test |
| 3/8-16 hold bolts | 142 minimum plus spares | Length mix must match the purchased hold set and 18 mm panel thickness |
| MoonBoard LED System | 1, SKU 60-201-V5 | User-selected kit; listing states 200 bulbs including 2 spares and 66 extra on Mini, reconciling to the 132 scheduled LED centres; supplied guide controls installation |
| Leg-to-outer-rail structural bolts | 8 | **Provisional:** 3/8-in Grade-5 through-bolts; length is unresolved until the reviewer approves the washer/plate/nut stack and thread engagement. Full X/Y/Z hole-centre datums and a 10 mm clearance-hole assumption are in the connection schedule. |
| Panel-to-rail screws | **unresolved** | **Provisional:** select only after panel/rail test assembly establishes required edge distances and penetration |
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
2. Print and calibrate the official imperial template. Drill and test a sample
   panel with an Escape T-nut, matching 3/8-16 bolt, representative hold,
   Moon LED, and the proposed panel-to-rail screw. Confirm rear clearance.
3. Cut panel and support blanks only after the fit test passes. Keep the full
   75 mm blank kicker extension below the official active kicker zone.
4. Glue and clamp each two-ply support member to the audited adhesive schedule;
   do not treat the 36 mm CAD thickness as an actual measured thickness.
5. Dry-fit the two side legs, five face rails, kicker
   seam/bottom backing, three panel-joint braces, and split rear ties on a
   level protected floor. Check the 60-degree leg angle, rear-foot position,
   racking, and all panel/LED/T-nut clearances.
6. Have the structural connection and unanchored-stability review completed
   before drilling structural bolt holes or joining any load-bearing member.
7. Assemble the rear support frame flat where practical, raise it with at
   least two people, and fasten panels only to the reviewed support layout.
8. Drill final hold and LED holes using the calibrated template. Install and
   test the LED strings/controller before final rear access is obstructed.
9. Complete a non-climbing inspection of all connections, wiring protection,
   panel seams, feet, and the separate impact-surface plan before any use.

## Human-audit gate

The following items prevent release as a build-ready design. The project may
continue as a geometry prototype while they are unresolved.

- Verify sheet stock is suitable and record actual min/mean/max thickness.
- Verify every 7/16-in Escape bore, screw, T-nut, hold bolt, LED, and cable on
  an offcut; the model does not prove physical clearance.
- Select and calculate/approve structural bolt, washer, nut, plate, adhesive,
  splice, panel-screw, and foot details. In particular, prove the center splice
  in each rear tie and the four-bolt leg connection.
- Check all structural bolt locations against the final hold, T-nut, LED,
  wiring, and panel-seam layout; the T-nut rows locate leg geometry but are not
  structural-fastener locations.
- Assess unanchored overturning, sliding, racking, floor bearing, anti-slip,
  and load spreading for intended use. No anchor may be added without a
  controlled revision.
- Confirm the selected Moon LED kit's supplied guide, controller mounting,
  switch access, power routing, and protection.
- Separately establish the impact surface/crash-pad arrangement before climbing;
  it is intentionally excluded from this board/frame package.
