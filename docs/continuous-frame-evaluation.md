# Continuous-rail frame evaluation

Evaluated 2026-09-07, commit `df2897a2acdc21dd762ddc5743f210c512ff35bb`, model `continuous-lean-frame`. This is a computational design review, not engineering certification or permission to build or climb. No repository design changes were made.

## Conclusion

Continuous top and lower rails resolve the former left/right material discontinuity. Structural adequacy is not yet established. The most actionable findings concern connections and load transfer, rather than a demonstrated need to enlarge every member.

## Findings

1. **Lower-ledge screw edge distance fails the available published mixed-load screen.** Four selected GRK R4 #9 screws enter the continuous lower deep rail at board station 119.05 mm, with rail edges at 100 and 138.1 mm. Available loaded-edge distance is 19.05 mm. For downhill shear perpendicular to the rail's grain, ESR-3201 Table 5 requires 10D or 12D: 43.94 or 52.73 mm for the modeled 4.3942 mm thread diameter. Its axial-only 4D clearance cannot qualify the combined load. This is a failure against the retrieved geometry basis, not a prediction of collapse. The manufacturer-hosted report is dated 2023 and was subject to renewal in July 2025; current qualification must be confirmed.

2. **Central uprights do not initially bear on the lower deep rail.** Uprights start at station 139.7 mm and the lower rail ends at 138.1 mm, leaving 1.6 mm. Downhill load must therefore cross connections or another path, or close that gap. Top-rail bearing into the uprights does not establish uninterrupted bearing to the floor.

3. **Panel attachment is not strength-qualified.** There are 48 nominal 2-inch screws, with about 32.54 mm gross receiver penetration. Product identity, plywood head pull-through, combined shear/withdrawal, and local fastener-group distribution remain unresolved. Eight outer corner positions have only 19.05 mm timber end distance; if specified as R4 #9, this is below that report's 43.94 mm axial end-distance requirement. Plywood capacity must not be inferred from its timber tables.

4. **Clip, leg and kicker connections remain unqualified.** Sixteen ML24Z proxies and 96 connector screws provide modeled connectivity, not verified inclined-joint capacities. Factory hole/bend geometry must replace the assumed layout before catalog resistance is assigned. Leg-bolt bearing, splitting, washer bearing, independent plywood-ply load sharing, kicker splices and lower corner joints still need explicit demand/capacity checks.

5. **F-column concentrated loading needs a separate check.** A 38.1 mm unsupported strip exists along the left panel's central edge. The F-column axis is within this strip. Local drilled plywood bending and T-nut pull-through are not represented by equal load distribution across five holds.

6. **Racking resistance remains dependent on connections and panels.** Full-width rails improve continuity but do not establish diaphragm resistance or weak-axis restraint. An isolated unnotched 2x6 beam calculation illustrates the sensitivity: with E=7000 MPa and the downhill component of a 250 lb load, a simply supported 2438.4 mm span deflects 57.09 mm; a 1181.1 mm span deflects 6.49 mm under the same central point component. These are hypothetical isolated beams, not predicted assembly deflection or strength checks.

## Current-geometry stability screen

Actual drilled CAD volume gives an assumed included mass of 181.622 kg (400.4 lb), with wood density 600 kg/m3 and clip density 7850 kg/m3. Fasteners, holds, LEDs and glue are omitted. This is not a measured build weight.

| Climber weight | Minimum edge-moment factor |
| --- | ---: |
| 150 lb | 1.942 |
| 200 lb | 1.908 |
| 250 lb | 1.876 |
| 300 lb | 1.844 |

All 96 selected cases meet the illustrative 1.5 moment target. The envelope covers 1x/2x downward gravity, 0/300 N horizontal force over all azimuths, 0/50/100 mm hold standoff and 80%/100% included mass with fixed center of mass. It does not establish a user rating, sliding resistance, uneven-floor performance, yaw equilibrium, flexible contact, joint strength or dynamics. Peak aggregate friction demand is approximately 0.143; no floor-friction capacity was established.

Separately, exploratory 1.2 kN board-normal forces at F12 do not pass: outward/downward force produces a -183.8 N kicker-side reaction; inward/upward force produces a -941.8 N leg-side reaction. Negative reactions require tensile floor support and are incompatible with the assumed unanchored contact. These exploratory vectors are not prescribed ordinary climber loads and are not included in the downward envelope. Their applicability needs a defined governing load basis.

## FEA attempt

The current CAD and export regression suite passed all 12 tests in 37.20 seconds. These check continuous material, official hole/service clearances, flat floor faces, nominal body/hardware collisions, receiver paths, export/source correspondence and dimensional schedules. They establish nominal geometry consistency, not connection resistance or strength.

The unchanged geometry was exported into an isolated workspace and attempted with the existing Gmsh/CalculiX pipeline at 60 mm and 40 mm mesh sizes. Both runs failed high-order mesh optimization with negative element Jacobians; neither reached a valid structural solve. No displacement or stress result is accepted for this revision.

Even a successful run of this existing solver would only diagnose optimistic bulk stiffness: undrilled isotropic wood, ideally bonded touching interfaces, fixed floor nodes, no self-weight, and five equally loaded row-12 points. It cannot qualify real fasteners, unanchored support, material strength or single-hold failure. Reported displacement would cover loaded nodes, not necessarily the whole-frame maximum.

## Buildability and next decision

The two unspliced rails eliminate central cuts/splices. Each needs a full 2438.4 mm usable length, including allowance for end squaring. There are still 16 clips and 96 connector screws, inherited profiled parts and substantial joint assembly. Safe temporary erection support is separate from completed-frame stability.

Recommended sequence: resolve lower bearing/ledge geometry; select and qualify actual panel and clip fasteners; check leg/kicker joints and local F-column loading; repair meshing without changing the intended physical load path; then analyze orthotropic members, connection compliance and unilateral floor contact under a reviewed load basis. Qualified structural review remains necessary before construction/use.

## Sources and evidence

- Current CAD: `mini_moonboard/continuous_frame.py`, `lean_frame.py`, `bracket_mvp.py`, `wood_mvp.py`.
- Raw current-geometry stability cases: `fea/results/continuous-frame/stability.json`.
- Frozen FEA inputs and attempted-run contexts: temporary workspace `/tmp/moonboard-evaluation-jFVhIy/fea/generated/square-cut/continuous-lean-frame/` (not committed; both attempts failed).
- [GRK ESR-3201, manufacturer-hosted retrieved edition](https://www.grkfasteners.com/getmedia/302e514d-0dfb-4c6f-b6a9-cd83243f4e46/ESR-3201.pdf).
- [CWA 2022 design specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf): source context for 1.2 kN unroped-climber load and 1.5 overturning screen; applicability and load combinations are not certified here.
- [Simpson connector catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog): actual connector application and installation requirements must govern, not CAD proxies.

