# WJ-04 tool access and removal screen

Status: diagnostic_overlap_present. This is a conservative catalog-envelope screen, not a physical access pass or evidence that a real wrench path is impossible.

## Trial and modeled candidates

- Trial: narrow_x95p25_ordinary_bolt_candidate at clip_horizontal_lower_right_1 (kerf-right).
- Trial config SHA-256: d1c63e1fa5617999e8af68d683cc0f3074fb84f518b048a087ec5ed276206c0e; source inventory SHA-256: 07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78.
- Bolts: K.L. Jack 25C375HCS5Z (95.25 mm), K.L. Jack 25C600HCS5Z (152.4 mm). Nut: K.L. Jack 25CNFH5Z; washers: 2 × 1/4-in Type A Wide plain steel washer per stack.
- Wrench: FACOM facom_34_7_16, 7/16 in, 22.0 mm nominal external head diameter, 3.0 mm thickness, 100.0 mm overall length. Source: [https://www.facom.fr/products/34-cles-a-fourches-micromecanique-tetes-inclinees-en-pouces](https://www.facom.fr/products/34-cles-a-fourches-micromecanique-tetes-inclinees-en-pouces).
- These remain modeling candidates; purchase, drilling, fabrication, structural, and physical-access approvals are false.

## Conservative envelope results

| Stack | Head counterhold | Nut stroke and reindex | Two-wrench overlap | Nut and nut washer removal | Bolt withdrawal | Head washer removal |
| --- | --- | --- | --- | --- | --- | --- |
| rail_1 | Overlap in bound | Overlap in bound | Clear in bound | Overlap in bound | Clear in bound | Overlap in bound |
| rail_2 | Overlap in bound | Overlap in bound | Clear in bound | Overlap in bound | Clear in bound | Overlap in bound |
| upright_1 | Overlap in bound | Overlap in bound | Clear in bound | Overlap in bound | Clear in bound | Clear in bound |
| upright_2 | Clear in bound | Overlap in bound | Clear in bound | Overlap in bound | Clear in bound | Clear in bound |

Clear means no intersections in this nominal, deliberately broad envelope. Overlap means that an envelope intersects a modeled obstacle; it does not prove that an actual open-end wrench cannot pass. Rotation paths use continuous-angle boxes computed from analytic corner extrema; translation paths use enclosing boxes. Exact jaw fit, handle profile, and human-hand clearance are not modeled. The 15°/75° values are synthetic planar heading samples, not a verified mapping of the catalog jaw offsets.

Limiting modeled obstacles: finished_parts/wj04_cleat (186740.355213 mm³), panels/main_lower_right (160292.516282 mm³), finished_parts/base_rail_service_lower_right (115128.865089 mm³), panels/main_upper_right (111466.896032 mm³), finished_parts/base_principal_center_right (92143.44054 mm³), other_wood/base_rail_service_upper_right (80369.19461 mm³), protected/lights/light_G7 (3832.767041 mm³), installed_hardware/rail_2/shaft (2464.150137 mm³)

## Removal sequence screened

The model screens a 30° nut-working stroke, an unverified open-end exit proxy over one 22.0 mm head width, detached 60° reindex and reseating; a full-turn tool envelope while the nut advances to clear the nominal bolt tip; nut and nut-washer translation; full bolt-axis withdrawal; then head-washer detachment. The nut washer's source-bounded minimum ID exceeds the modeled shaft maximum, allowing this nominal axial slide screen; thread major diameter and received-part fit remain unverified. Nut/thread fit, full-form threads at the tip, delivered dimensions, tool tolerances, torque, installation sequence, and hand pickup are unverified.

## Reproduction and provenance

Run uv run python -m scripts.wood_joint_wj04_tool_access --write. Producer SHA-256: 8e3af4e66153dd3de183604957db969d3bcb1cfcc5e2ce2505eaa8d9bebc129d. JSON data: [wj04-tool-access.json](wj04-tool-access.json).
