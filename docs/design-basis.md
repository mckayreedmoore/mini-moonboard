# Design basis and readiness gates

This document is the decision boundary between the official reference model
and the future buildable frame. A value marked **unresolved** must not be
invented from the photograph or video.

## Current design basis

| Design item | Current value | Status |
| --- | --- | --- |
| Use | Indoor personal bouldering/training wall | Confirmed |
| Structure | Freestanding A-frame | Confirmed design target |
| Building attachment | None intended | Provisional; stability review may require revisiting |
| Board | Mini MoonBoard, 40 degrees from vertical | Confirmed |
| Main surface | 2440 x 2440 mm (8 x 8 ft nominal) | Confirmed reference envelope |
| Panels | Fabricated birch plywood | Confirmed approach |
| Units | Millimetres canonical; metric and imperial documents | Confirmed |
| Active Mini MoonBoard kicker | 150 mm (5.9 in) | Confirmed official geometry |
| Total custom kicker | Greater than 150 mm | Unresolved |
| Crash pad | Make, deployed size, thickness, and joining method | Unresolved |
| Exposed kicker above pad | Required clearance | Unresolved |
| Available room | Width, depth, ceiling height, and obstructions | Unresolved |
| Fall/impact area | Plan dimensions and impact-attenuation system | Unresolved |
| Frame stock | Laminated nominal 3/4 in birch plywood | Provisional concept |
| Connections | Geometry, bolts, screws, plates, and adhesive | Unresolved |
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

## Gate 1: inputs complete

Before detailed frame modelling begins:

- measure the installation envelope and floor condition;
- select and measure the deployed crash-pad system;
- set total kicker height and exposed active-kicker clearance;
- record actual plywood species, grade, sheet size, and measured thickness;
- decide whether the structure must be demountable; and
- identify the project jurisdiction and qualified reviewer.

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
- a dry-fit or prototype records deviations and corrective changes;
- inspection and maintenance checklists are complete; and
- the approved commit is tagged so later edits cannot be mistaken for the
  reviewed release.

