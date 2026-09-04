# Design basis and readiness gates

This document is the decision boundary between the official reference model
and the future buildable frame. A value marked **unresolved** must not be
invented from the photograph or video.

## Current design basis

| Design item | Current value | Status |
| --- | --- | --- |
| Use | Indoor personal bouldering/training wall | Confirmed |
| Structure | Freestanding A-frame | Confirmed design target |
| Building attachment | None | Confirmed v1 constraint; no anchoring allowed |
| Board | Mini MoonBoard, 40 degrees from vertical | Confirmed |
| Main surface | 2440 x 2440 mm (8 x 8 ft nominal) | Confirmed reference envelope |
| V1 stock-controlled main surface | 2436.0 x 2436.0 mm | Provisional: two 1218.0 mm panels leave 2.4 mm total rip allowance in a 96-in sheet; verify official-template calibration |
| Panels | Fabricated birch plywood | Confirmed approach |
| Units | Millimetres canonical; metric and imperial documents | Confirmed |
| Active Mini MoonBoard kicker | 150 mm (5.9 in) | Confirmed official geometry |
| Total custom kicker | 225 mm (8.86 in): 150 mm active zone + 75 mm blank extension | Provisional v1; derived from the official kicker bolt-center datum |
| Crash pad / fall surface | Separate element; excluded from v1 board/frame scope | Explicitly out of scope, not approved or designed here |
| Frame assemblies | Board/kicker plus two exterior hockey-stick legs | Confirmed v1 concept |
| Climbing-face orientation | Underside of the overhanging board; climber is below it | CAD-controlled: main-panel climbing face is local +Y/downward; rails and wiring live on opposite local -Y support side |
| Leg upper datum | Reaches two T-nut rows below top; bend/connection five rows below top | Provisional v1 geometry datum; not a structural fastener pattern |
| Leg lower angle | 60 degrees to the descending board line | Provisional v1 geometry |
| Frame stock | Every support member is two laminated nominal 3/4 in birch plywood sheets | Provisional concept; actual thickness and glue quality need audit |
| Connections | Four schedule-only structural-hole datums per leg into the exterior outer rail; 3/8-in Grade-5 bolt length unresolved | Provisional; bolts are intentionally absent from the collision-audited STEP assembly; do not substitute climbing T-nuts for structural connections |
| Design loads | Dead, climbing, impact, racking, and incidental loads | Qualified reviewer to establish |
| Portability | Fixed assembly versus demountable joints | Unresolved |

## Standards and professional references

The qualified reviewer must identify the editions and requirements applicable
to the installation location. The repository currently tracks these candidate
references without reproducing their copyrighted text:

- The Climbing Wall Association's [General Specification for Design and
  Engineering of Artificial Climbing Structures](https://www.cwapro.org/design-and-engineering)
  addresses dead and live loads, climbing-surface design, stability with and
  without protection anchors, marking, and conformity for North American
  artificial climbing structures.
- The CWA's [Specification for the Structural Inspection of Artificial
  Climbing Structures](https://www.cwapro.org/products/standards) is the
  candidate basis for commissioning and periodic structural inspections.
- The CWA [Industry Practices, Fourth Edition](https://www.cwapro.org/products/industry-practices)
  addresses impact-attenuating surfaces, bouldering operations, inspection,
  and maintenance. It is operational guidance, not a substitute for structural
  design.
- [EN 12572-2](https://standards.iteh.ai/catalog/standards/cen/38e5fcdb-0e9b-4228-a17f-8e19241648f4/en-12572-2-2017)
  covers bouldering-wall safety requirements and test methods, including impact
  areas, structural integrity, surface elements, and panel inserts. Its
  jurisdiction and current edition must be confirmed before use.

No load magnitude, safety factor, impact-area dimension, or inspection
interval is copied from a summary or inferred here. Those values must come
from the acquired standard, the applicable building requirements, and the
qualified review.

## V1 human-audit checklist

The v1 STEP model is a geometry prototype, not fabrication authority. Audit
these values before cutting, drilling, gluing, or loading it:

- **Kicker:** 225 mm total (75 mm blank + 150 mm official active zone). The
  75 mm extension is a user estimate from the official foothold-center datum,
  not a room or pad measurement.
- **Leg geometry:** the model bends at main-grid row 8 (fifth row down from
  row 12), reaches row 10, and assumes a 60-degree included angle from the
  descending board line. The lower-member endpoint centre is 1389.6 mm behind
  the kicker face at the finished-floor plane; CAD trims its overlong lower
  member to make a full 3448 mm² floor-parallel bearing face per leg. Confirm
  the final floor footprint and foot protection.
- **External-leg connection:** four structural bolts per leg are provisionally
  specified in the connection schedule as 3/8-in Grade-5, 10 mm clearance-hole
  datums. The bolts and bores are intentionally absent from the collision-audited
  STEP assembly; their final length, washer/plate stack, edge distances, and
  load path are not reviewer-approved. The T-nut rows are location datums only;
  no structural bolt may obstruct a required hold, T-nut, LED, cable, or panel
  joint.
- **Laminations:** the model uses a provisional 36 mm member thickness (two
  18 mm layers). Measure the actual nominal-3/4-in sheets, then set thickness,
  adhesive, clamping method, cure, and edge sealing accordingly.
- **Unanchored stability:** inspect the floor bearing, anti-slip feet,
  load-spreading, racking, and overturning resistance under intended use. No
  anchoring is allowed; this must be resolved by the reviewer rather than
  compensated for by an unreviewed dimension change.
- **Climbing/electrical hardware:** test the Escape 3/8-16 screw-in T-nut
  bore and screw clearance on an offcut; verify hold bolts; confirm the Moon
  LED kit's supplied guide, 13 mm holes, rear cable routing, controller access,
  and power protection before production drilling.

## Gate 1: inputs complete

Before structural fabrication or use:

- inspect the floor condition, levelness, and slip resistance where each foot
  bears; this does not authorize anchoring;
- record actual plywood species, grade, sheet size, and measured thickness;
- select all structural connection hardware and adhesive; and
- have a qualified reviewer assess the unanchored load path and stability.

## Gate 2: design review package complete

Before publishing a purchasing BOM or fabrication drawings:

- every load-bearing member and connection exists in the CadQuery assembly;
- the load path, stability, overturning, racking, and floor interface are
  documented;
- panel seams, T-nuts, LEDs, holds, and fasteners have verified clearance;
- every modelled part maps to the BOM and cut list exactly once;
- drawings regenerate from the reviewed model and pass automated checks; and
- the reviewer has enough information to reproduce the calculations.

## Gate 3: build-ready release

The plans may be labelled **build-ready** only after:

- qualified review comments are recorded and incorporated;
- the reviewer and applicable standard editions are identified;
- the final CAD, drawings, BOM, cut list, and guide agree;
- reviewed renders of the completed board assembly are embedded in the README;
- a dry-fit or prototype records deviations and corrective changes;
- inspection and maintenance checklists are complete using
  [`inspection-maintenance.md`](inspection-maintenance.md); and
- the approved commit is tagged so later edits cannot be mistaken for the
  reviewed release.
