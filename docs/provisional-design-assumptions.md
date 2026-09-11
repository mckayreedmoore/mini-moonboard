# Provisional design assumptions — independent verification handoff

Status: **provisional; not a construction release or an achieved user-weight rating**.
Prepared September 11, 2026 for the historical `horizontal-service-development`
diagnostic; retained during development of `round-bore-service-development`.

This is the entry file for the next agent. It distinguishes numbers already used
in the diagnostic from published reference values and proposed replacements.
The online references do not retrospectively qualify the existing calculations.
Record the accepted value, source/table, applicable adjustments and resulting
reruns against each ID below. Do not silently replace a value in an old result.

The current round candidate retains the owned Roseburg plywood, uses enclosed
25.4 mm wiring passages and has 56 panel/kicker screws. The table below describes
the archived grooved-frame diagnostic; its geometry, demands and resistance
references do not qualify the revised frame. See the
[round-service plan](round-service-build-plan.md) for the current package and gates.

## Values already used in the historical diagnostic

| ID | Quantity | Current value and meaning | Verification needed |
| --- | --- | --- | --- |
| L01 | User-weight design target | Previously recorded owner requirement: one climber, 250 lb maximum. 300 lb remains a sensitivity case. **Neither is an achieved rating.** | Preserve that distinction; confirm governing load combinations and permitted use. |
| L02 | Downward climber load | Twice body weight: 2.224 kN at 250 lb; 2.669 kN at 300 lb | The factor 2 is an analyst-selected dynamic scenario, not a published bound on dyno/catch forces. Verify its adequacy. |
| L03 | Additional horizontal load | 300 N; global Y in coupled-frame cases; eight azimuths in the floor screen | Analyst-selected scenario, not a manufacturer load rating. Check transverse and asymmetric cases. |
| L04 | Hold standoff and applied patch | 100 mm from the panel face; 20 × 20 mm patch, with the moment transferred to the panel midplane | Neither dimension is a measured hold-seat interface. Small-patch stresses must not be treated as verified plywood failure. An 80 mm C10 patch sensitivity is separate. |
| M01 | Lumber and plywood elastic model | Both isotropic: E = 7,000 MPa; Poisson ratio = 0.30; implied G = 2,692 MPa | These are screening assumptions. In particular, isotropic shear stiffness is not a verified wood/plywood property. Review the directional replacements below. |
| J01 | Connection stiffness | 1,000 N/mm per modeled translational spring; 100 and 10,000 N/mm sensitivities | Not a measured SPAX, SDS, bolt or complete-bracket stiffness. Separate lateral slip, axial withdrawal, group effects and service/ultimate stiffness. |
| J02 | Bearing penalty | 1,000,000 N/mm, with compression-only active-set contact | Numerical penalty, **not wood bearing resistance or measured contact stiffness**. Check penalty sensitivity and bearing stress separately. |
| B01 | Foot restraints in coupled model | Entire bottom member cross-sections clamped | A diagnostic restraint. It does not represent the unanchored floor or establish resistance to sliding/uplift. |
| B02 | Member geometry in coupled model | Uniform retained rectangular sections derived from grooved timber; fastener bores/local notch stresses excluded | Check local residual sections, stability and actual joint behavior independently. |
| D01 | Mass density | Wood/plywood 600 kg/m³; modeled steel 7,850 kg/m³ | Assumed, not measured. Current floor mass includes modeled hardware; coupled-frame gravity omits hardware and holds. |
| F01 | Floor friction | μ = 0.10, 0.20 and 0.40; mass factors 0.8 and 1.0 | Sensitivity values, not a certified coefficient for the eventual feet/floor pair. |
| E01 | Inter-LED cable length | User reports approximately 12 in = 304.8 mm, bulb base to bulb base | Approximate path budget, not a guaranteed minimum. Check the shortest segment, bends and extra slack. |
| E02 | LED/wire envelopes | Provisional 4 mm cable; 12 mm rear bulb projection; 8 mm clearance band around wire paths, boxed into 12 mm-deep front-open grooves | Finished groove widths vary with the curved route: use the exported cut bounds, not an assumed 8 mm cutter pass. Actual kit dimensions remain to be measured; surplus cable and external controller leads are not placed. |

Implementation: [coupled model](../fea/horizontal_panel_frame.py),
[case matrix](../fea/horizontal_frame_batch.py),
[floor screen](../fea/horizontal_service_floor.py), and
[wiring model](../mini_moonboard/horizontal_service_wiring.py).
The [diagnostic findings](horizontal-frame-diagnostic.md) and
[stress limitations](horizontal-frame-stress.md) describe what has actually been run.

## Published load/serviceability reference

The official [SIST preview of EN 12572-2:2017](https://preview.sist.si/sist-preview/39968/eb82f102549541eba9b79bad025432c2/SIST-EN-12572-2-2017.pdf),
clauses 4.5–4.7, provides the following limited reference. The
[DIN catalogue](https://www.dinmedia.de/en/standard/din-en-12572-2/255819306)
listed this edition as current when checked. Applicability and the complete
design procedure still need review.

| ID | Published reference | Proposed use and limitation |
| --- | --- | --- |
| L05 | Panel deflection calculation load: 0.8 kN; maximum surface-element deflection l/100, where l is the maximum distance between fixations | Add a dedicated serviceability assessment with the specified support/fixture interpretation. Do **not** compare absolute whole-frame motion under the doubled 300 lb case directly against this panel criterion. |
| L06 | Panel-insert test includes a 0.5 mm deformation limit at 1.2 kN after a specified test step; five panel/insert samples | This concerns the climbing-hold panel insert and its complete test sequence. It is not a 1.2 kN rating for the proposed removable-panel repair inserts. |
| L07 | Structural integrity refers to Annexes A and B and Table A.1 | The inspected preview omits those annexes. Verify the full load combinations, area loads and factors before asserting compliance. No roped-climbing anchor load has been substituted for a bouldering-wall load. |

These excerpts are reference criteria, not evidence that this board complies.
Moon's [build guide](https://eu.moonclimbing.com/build-your-moonboard) explicitly
allows frame requirements to vary with the installation and calls for horizontal
bracing at panel joints. It does not supply a load rating for this custom frame.
Review the lower panel's partly unsupported seam edge against that guidance.

## Provisional material and connection selections

The remaining-lumber purchasing basis is dry, grade-stamped **Douglas Fir–Larch
No. 2 or better**. **Retain the already purchased Roseburg AC exterior PS 1,
23/32-category face plywood**, Lowe’s item 12235 / model 119055, recorded in the
[purchased-material record](purchased-materials.md). Verify the actual lot's
stamp, usable dimensions, thickness and strength-axis orientation.

**APA PS 1 Structural I plywood, 23/32 Performance Category, 48/24, square edge**
remains an optional research/reference alternative. It does not identify the
owned sheets, require their replacement or establish that its reference values
apply to them. Neither product choice turns the archived isotropic model into
an analysis of the delivered materials.

Detailed sourced values and their conditions are maintained in:

- [Material stiffness and resistance assumptions](provisional-material-assumptions.md).
- [Connection stiffness and reference load capacities](provisional-connection-assumptions.md).
- [Floor-friction and density assumptions](provisional-floor-load-assumptions.md).

For review prioritization: the proposed longitudinal lumber E is approximately
11.0 GPa. The plywood reference requires distinct bending and membrane stiffness;
one replacement E is insufficient. Connection slip estimates must also be
direction-specific. None of these proposed inputs has replaced the archived
7.0 GPa / 1,000 N/mm diagnostic.

Review panel retention first: two completed probes produce approximately
1.064 and 0.962 kN withdrawal demand, exceeding the #8 screw's optimistic
unadjusted 0.734 kN reference. The connection appendix records the signed force
extraction, conditional head resistance and adjustment gaps. This is a screening
flag, not an established physical failure or an achieved assembly rating.

Published reference capacities must remain distinct from adjusted design
capacities, characteristic values, ultimate test loads and proof-test loads.
Do not multiply a connection capacity by its screw count without checking group
action, load direction, eccentricity and the manufacturer's prescribed assembly.

## Review record and required decisions

| Review group | Decision the next agent must return | Status |
| --- | --- | --- |
| L01–L07 | Governing use/load cases; serviceability method; full-standard applicability and factors | Open |
| M01, material appendix | Grade/size adjustments, directional elastic properties, plywood bending/rolling-shear properties and admissible failure checks | Open |
| J01, connection appendix | Direction-specific stiffnesses and adjusted withdrawal, lateral and head/panel bearing capacities; identify which values are analogies | Open |
| J02, B01–B02 | Contact/foot restraint validity, penalty sensitivity, local grooves/bores and member stability | Open |
| D01, F01 | Actual mass/CG and justified lower-bound foot/floor friction; unanchored stability | Open |
| E01–E02 | Physical kit envelopes, routed slack, groove dimensions and external leads | Open |

For each accepted or rejected number, record: **ID; old value; accepted value
and units; exact source/table/edition; applicable material/product and direction;
adjustment factors; confidence/remaining gap; affected calculation and rerun;
reviewer and date**. Keep unverified items open. A passed numerical equilibrium
check is not a material or assembly load rating.
