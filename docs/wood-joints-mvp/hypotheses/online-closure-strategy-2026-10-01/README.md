# Online evidence strategy for completing the wood joints

Prepared October 1, 2026 for the primary mini moonboard agent, following the owner's request for extensive online research and practical ways to resolve the resistance, corner detailing and missing load-case blockers.

**Recommendation:** prioritize exact hardware evidence and experimental method benchmarks, while the primary continues its existing solver precision preparation. Two newly located experimental sources and a mixed-load fracture model offer useful routes beyond generic material assumptions. None establishes resistance for the reviewed candidate today. No complete joint or additional response case is accepted by this memo.

This is an additive research handoff for `compact-floor-flush-wood-joints-development`, reviewed model `led-clearance-2x6-runner-seated-blocks-v1`. It changes no model, axis, material input, criterion, selected-candidate authority or shop instruction. No native solve, purchase, physical test or external correspondence was performed. The selected baseline and its historical passes remain separate.

## Current evidence and the next decisions

The primary's [integration record](../mvp-integration-2026-10-01/README.md) reports 47 pending criteria and three authenticated rear diagnostic exports. Forward, left and right response cases remain unresolved. Its current owners already cover the isolated STI17 build/coupon preparation, washer crop/mesh preparation and receiver/retained-bolt work. This memo proposes additions to those scopes, not duplicate runs.

| Priority | Proposed action | Concrete useful result | Remaining boundary |
| --- | --- | --- | --- |
| 1 | Finish exact bolt, nut and washer source binding. | Per-SKU evidence for mechanical properties, shank/thread transition and bearing land; an explicit unsupported-input list. | A material certificate does not establish timber joint resistance. |
| 2 | Add a numerical error budget to the existing STI17 coupon plan. | Separate export rounding, solution error, force-output rounding and differences between operators/states. | A smaller residual alone cannot unlock a response case. |
| 3 | Use the washer experiments already transcribed locally. | A declared material/contact model tested against assembly load–indentation data before extrapolation. | Candidate partial support, shared receiver, actual steel yield and wood properties still need evidence. |
| 4 | Recover the new Douglas-fir embedment study and the corrected open connection dataset. | Small, reproducible experimental benchmark packets, with source scope and uncertainty retained. | Neither supplies adopted DF-L No. 2 quarter-inch joint capacities. |
| 5 | Assess a fracture method for the corner's combined actions. | A documented applicability decision, candidate crack paths and required data for splitting and group behavior. | In-plane research does not cover the complete six-component corner wrench. |
| 6 | Revisit missing cases after reference reproduction and branch admissibility pass. | Candidate-specific gravity-settle and directional load histories with authenticated contact states. | Online evidence cannot substitute for those response histories. |

Priorities reflect expected information gained per unit of work, not a promised completion date. Source retrieval and contract clarification are the easiest immediate tasks. Fracture calibration and complete joint applicability remain substantive work.

## Newly located experimental sources

### Douglas fir embedment with declared clearance

Li, Yang, Qin and Wei's 2026 study reports 13 full-hole embedment series in Douglas-fir glulam: 8–16 mm bolts, load-to-grain angles of 0–90 degrees, thicknesses of 30–40 mm and a fixed 1 mm hole clearance. The publisher's issue page independently confirms that scope. [Article](https://bioresources.cnr.ncsu.edu/resources/embedment-behavior-of-low-to-medium-diameter-bolts-in-douglas-fir-glued-laminated-timber/), [publisher issue entry](https://bioresources.cnr.ncsu.edu/issues/vol21-issue3/page/7/).

**Proposed use:** extract specimen geometry, conditioning, bolt properties, measurement definitions, series means/scatter and curves. Reproduce the nearest documented specimen before treating the paper as a sensitivity reference for the current bearing/clearance model. The current 6.35 mm diameter lies outside the tested range; glulam also differs from the project's solid DF-L No. 2 material. No extrapolation is adopted.

Do not insert measured full-hole connection stiffness directly into a wood foundation law without separating fixture and bolt compliance. Otherwise, a continuous-bolt model can count bolt bending twice. The published setup uses high-strength bolts to minimize bending, which still requires a measurement-level applicability check. The full HTML exceeded this browser's size limit; indexed article passages and the issue entry were retrieved, but the numerical tables and PDF were not authenticated here. They remain a retrieval task.

### Open curves and strain data across connection scales

Palma and Wydler's open Zenodo dataset includes steel tensile and bending curves, wood embedment curves, single- and multiple-fastener connection curves, and digital image correlation strain measurements. It uses spruce LVL without cross layers and 10 mm S235/S355 dowels. **Use version 2, published February 14, 2025:** its LVL moisture/density file corrects the earlier version. The record lists a 109.0 MB ZIP and MD5 `c49a8dbb57b2db7c75ef124605551f7e`, under CC BY 4.0. [Version 2 record](https://zenodo.org/records/14870762), [archive preview](https://zenodo.org/records/14870762/preview/Palma_and_Wydler_2024_Dataset_results_experiments_timber_connections.zip?include_deleted=0).

**Proposed use:** select one embedment specimen, one steel bending specimen and one eccentric connection family with matching material identifiers. Calibrate on the first two; retain the connection curves and strain fields as independent checks of load distribution and crack location. Separate calibration specimens from validation specimens. This could check multiple parts of the method against one coherent experimental campaign instead of mixing unrelated material constants.

The archive listing was inspected, including the bending and embedment folders; the archive was not downloaded and CSV contents were not parsed. Pin the version, verify its checksum and read each folder's README before extracting units or fitting curves. These specimens validate methods only; their material strengths do not transfer to our hardware or timber.

### Douglas fir assembly modeling with measured component behavior

Kaliyanda, Rammer and Rowlands' 2019 Forest Products Laboratory paper models and tests Douglas-fir glulam connections with steel side plates, 12.7 mm bolts, washers and nuts. It includes clearance, contact and progressive damage, and reports auxiliary bolt bending/tension and wood compression measurements. The PDF is available through USDA. [Publication and PDF](https://research.fs.usda.gov/treesearch/61367).

**Proposed use:** inspect its figures and material definitions as a second benchmark for coupled bolt/wood/contact behavior. Its steel-sided, parallel-load topology, diameter and glulam differ from our joints. The paper explicitly uses finger-tight assembly without applied bolt prestress; that provides a useful comparison without inventing a torque-derived clamp force. Do not import its damage law, friction coefficient or measured bolt yield as candidate properties.

## Complete wood and bolt behavior

The present [complete-corner register](../mvp-acceleration-2026-09-28/current-corner-complete-resistance-register-attempt01/README.md) already has useful signed demands and favorable conditional component comparisons. It still lacks complete adjusted resistance, shared timber splitting, continuous three-receiver bolt behavior and axial/lateral interaction. Online research found method candidates, not an off-the-shelf capacity for that topology.

Aquino and colleagues' 2025 paper generalizes a beam-on-foundation and nonlinear connector approach to in-plane multiaxial forces and bending. It evaluates crack onset using stresses averaged along potential failure paths, and compares connection response with experiments. Its stated data availability is by request. [Publisher article](https://www.sciencedirect.com/science/article/pii/S0141029625013781), [institutional PDF location](https://lnu.diva-portal.org/smash/get/diva2%3A1999624/FULLTEXT01.pdf).

**Proposed applicability check:** assess this method against the current corner's simultaneous in-plane bolt actions and member transfer moments. Retain its missing dimensions of applicability explicitly: bolt-axis ties, out-of-plane bending/torsion, end-grain block behavior, washer contact and disconnected ligaments. The publisher abstract and indexed institutional passages were retrieved; complete PDF access timed out. Full method inspection is required before implementation or any capacity claim.

The same group's 2026 open paper demonstrates why elastic load sharing and brittle failure should be evaluated together. Its mean-stress fracture method needs perpendicular tensile strength, shear strength and mode I/II fracture data; it identifies crack initiation, without post-crack redistribution. Material variability and initial-slip tolerances were not evaluated in that study. The paper offers data on request. [Full article](https://link.springer.com/article/10.1617/s11527-026-03157-7).

**Proposed benefit:** spatial stress averaging tied to fracture properties may avoid treating a mesh-dependent contact-edge peak as a splitting resistance result. This is an inference about a useful method route. It still requires applicable fracture data and validation, and must not become an arbitrary averaging length chosen to obtain a pass. Its calibration uses European spruce/M12 configurations, not our timber and bolts. Foreign code comparisons in these papers do not replace the project's adopted NDS basis.

For BG003, preserve one continuous bolt and all three receiver interactions. Two independent two-member checks cannot establish compatibility, load redistribution or steel bending for the assembly. Any research benchmark must match its own topology first; adapting it to ours needs a new explicit contract. Similarly, disconnected finished ligaments need a justified transfer field before using common strain or summed inertia as resistance evidence.

## Hardware evidence with high information value

The project's [quarter-inch source note](../bottom-quarter-inch-resistance-basis-2026-10-01/source-note.md) already distinguishes recognized NDS routes from the unadopted 45 and 106 ksi bending hypotheses. Its inspected NDS 2024 clause permits an F1575 bending route or a tensile-yield route using F606 procedures. The appendix's approximate relation is not an exact-part guarantee. Resolve this source chain before using Grade 5 minima as bending resistance.

[Lawson FA21103](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103) explicitly describes the quarter-inch by eight-inch partial-thread Grade 5 product as conforming to SAE J429 material and mechanical properties. This useful catalog lead is already known locally. It does not qualify another length/SKU or provide its exact delivered shank and bearing-land dimensions.

**Proposed supplier question:** for each exact proposed SKU, request existing test/specification evidence supporting the recognized tensile-yield evaluation route, its test method, diameter band, minimum unthreaded length including thread runout, and head/nut bearing-land or chamfer drawing. Request existing documentation first; a new physical test is not imposed by this memo.

Ordinary F844 washer designation supplies no general mechanical-property minimum unless separately specified; supplier documentation distinguishes that from F436 hardness requirements. F436 hardness alone still supplies no numeric tensile yield for our bending model. [Portland Bolt F844 explanation](https://www.portlandbolt.com/technical/faqs/f844-plate-washers/), [F436 properties](https://www.portlandbolt.com/technical/specifications/astm-f436/).

**Proposed supplier question:** can the actual catalog washer be tied to a specified steel grade, minimum yield value or existing lot/product test, with OD, ID and thickness tolerances? A base-steel certificate needs an applicability review for the finished washer. Do not substitute a hardness-to-yield conversion or generic 250 MPa assumption as an adopted property.

A compact stock alternative exists: [K.L. Jack 25NWSA8Z](https://www.kljack.com/products/25nwsa8z/) declares F436 and OD 0.620–0.640 inch, smaller than the current wide washer envelope. **Hypothesis only:** it may change local clearance and bending behavior. Smaller area can worsen wood bearing, and this search does not establish that it clears the service passage or supplies the missing yield input. Any substitution needs the same geometry/contact/material checks. The existing larger Unistrut/Eaton washer leads have already been investigated locally and are not new discoveries here.

## Washer method and the partial seat

Teranishi and colleagues' 2021 paper supplies experiments and a 3D washer/wood contact model for square SS400 washers on Japanese cedar. It identifies sensitivity to transverse wood properties. Its mean stiffness underprediction and yield-load overprediction are not conservative correction factors. [Full paper](https://link.springer.com/article/10.1186/s10086-021-01973-9).

The primary has already transcribed experimental/model targets in its [washer preflight](../washer-metal-method-preflight-2026-10-01/source-method-review.md). Use that work. The recent affine-annulus and finite-sector fixtures verify numerical mechanics/output behavior; they do not validate wood crushing or metal resistance. A useful next benchmark compares assembly indentation and yield response for a documented experiment, with any reciprocal reconstruction of its printed wood tensor disclosed.

For the candidate, the [current 3D contract](../current-washer-conditional-3d-contract-2026-10-01/README.md) already includes the partial seat and neighboring stack. Keep both stacks and the shared receiver; supported annulus percentage alone is not a stress or capacity bound. Evaluate head/nut load footprint, unilateral contact, wood orientation/law, steel yield and mesh/domain sensitivity together. A uniform annular pressure or perfectly clamped ring does not establish this physical support condition.

The 2017 [circular-washer tightening study](https://www.jstage.jst.go.jp/article/jwrs/63/4/63_162/_article/-char/en) offers a possible second geometry benchmark. Its torque/preload context requires separate inspection; it provides no authority to add friction or pretension to the candidate. A 2024 [damage-model extension](https://www.tandfonline.com/doi/abs/10.1080/17480272.2024.2345191) is already noted in local review and remains a full-text retrieval lead here, not inspected numerical evidence.

## Corner detailing before geometry changes

The latest [BG045 source review](../mvp-acceleration-2026-09-28/current-bg045-edge-splitting-applicability-attempt02/README.md) establishes the conditional 20 versus 25.4 mm comparison, but does not settle which face the current end-grain/oblique actions make the required loaded edge. The review also distinguishes the header's mixed-grain actions from a pure perpendicular-load table case. A favorable component capacity does not resolve this applicability question.

**Immediate source task:** obtain the current NDS 2024 commentary and check the exact edge/end/row language against the signed actions and proposed grain. The [AWC resource page](https://awc.org/resources/2024-nds/) identifies the current package. Current specification PDFs are already pinned locally. A search result headed with a 2024 errata date led to older-edition commentary; it is not current commentary evidence. The advertised 2026 TR12 download was inaccessible in this research, so no indexed excerpt is adopted as a current clause.

**Draft question for a later authorized AWC inquiry:** for an end-grain main member with this two-bolt layout and oblique lateral actions, how is the loaded edge determined, what provision governs the oblique header, and what documented engineering method addresses simultaneous below-center bolt-axis ties? Supply a diagram, source clauses and all signed action directions. Such an inquiry could resolve interpretation; it is not a blanket external-signoff prerequisite and would not establish splitting capacity by itself.

Do not move both axes inward as a quick fix. The existing [proposal](../mvp-acceleration-2026-09-28/current-bg045-symmetric-inward-detail-proposal-attempt01/README.md) reduces the modeled bore web from 7.453 to 2.053 mm. A single-axis move preserves that web but leaves the opposite component sensitivity unresolved and reaches the nominal threshold without tolerance margin. These are already disclosed study results, not new recommendations to modify the reviewed geometry.

## A12 disagreement and the missing response cases

The [latest source discriminator](../a12-source-comparison-next-method-2026-10-01/README.md) retains 27 force-interval failures. Row 1586's interval miss is approximately `8.90e-8 N`; higher-precision arithmetic on the same rounded endpoint coordinates changes its force by only `3.65e-12 N`. The saved native and reduced states differ, so correcting arithmetic at one recovered spring cannot establish common equilibrium.

The pinned [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), section 6.2.42, describes SPRINGA's length-based force and changing direction with NLGEOM. Its behavior must be distinguished from a fixed scalar projection. The local source audit also identifies 14 significant digits in the stiffness export. Neither observation establishes the cause of the remaining discrepancy.

**Proposed diagnostic contract:** associate every failed row with four separate uncertainty terms: matrix export rounding, numerical solution error, native output rounding, and operator/state differences. Native geometric spring force and reduced projection force should first be evaluated at the same declared endpoint state. This supplements the primary's existing STI17 plan rather than presuming higher precision will solve the discrepancy.

[LAPACK DGESVX documentation](https://www.netlib.org/lapack/double/dgesvx.f) distinguishes conditioning, estimated forward error and componentwise backward error, including limits on reliability. A small residual is insufficient evidence of accurate forces in a poorly conditioned system.

**Proposed extension:** a row-focused adjoint sensitivity can estimate how matrix perturbations affect the failing force output. Begin with a small known-answer operator and declared rounding intervals; if strict certification is required, include higher-order and estimation errors rather than labeling a first-order estimate a bound. The existing factorization's conditioning and serialization diagnostics should guide whether such a bounded follow-up is worthwhile. This memo performs no matrix reconstruction or factorization.

Once a reference method reproduces the saved case within its unchanged gates, reuse the verified elastic operator where applicable and track contact events during gravity settling and each directional ramp. Reuse of the wood operator does not imply reuse of the active contact set. The stopped selectors supply no proof of instability or infeasibility.

A symmetry audit could cheaply determine whether any directional result is reusable, but it must map every body, opening, grain assignment, fastener, load and support. The partial service-passage seat already gives reason to expect local asymmetry. Reflection or superposition cannot currently replace a missing case. No online material dataset verifies the physical no-slip floor assumption.

## Creative ways to obtain useful data online

These are proposed data requests or extraction tasks, not messages already sent.

| Route | Specific data to seek | Why it helps |
| --- | --- | --- |
| Versioned repositories | Corrected ZIP, folder READMEs, specimen identifiers and raw curves from the Zenodo campaign. | Keeps steel, embedment and assembly observations traceable within one campaign. |
| Publisher tables and figure digitization | Raw Douglas-fir curves first; otherwise tables and curves with axis calibration and pixel uncertainty. | Provides an independently reproducible target without inventing a material curve from a design allowable. |
| Focused author request | Aquino group: benchmark input deck, mean-stress Python module, crack paths, calibration inputs and their valid scope. | May substantially reduce implementation ambiguity; their articles explicitly offer data by request. |
| Washer authors | Actual reciprocal material card, measured indentation curves, nut contact footprint and material-property measurements. | Addresses the inputs that a graph or nominal washer size cannot recover. |
| Supplier technical files | Existing test report, lot/grade mapping and head/nut/washer dimension drawing for exact SKUs. | Can close a specification gap without starting another mechanics study. |
| USDA archives and cited theses | Original specimen-level bolt/wood curves behind the public reports. | Older experimental data can remain useful when species, geometry and measurement method are documented. |

For any extraction, record source URL/version, units, specimen count, geometry, material conditioning, load history, measurement definition, uncertainty and exclusions. Published mean strength, code design value and numerical yield parameter serve different purposes. Do not pool incompatible tests or call a digitized mean curve a design lower bound.

The search covered code interpretation, hardware specifications, bolt/wood embedment, continuous fastener behavior, washers/contact, splitting/group interaction and solver error. It did not find a published rating for the exact reviewed assembly. Retrieval limits remain explicit above; public scope pages and indexed passages do not replace complete method inspection.

## Lead handoff and delivery status

The short relay is [lead-agent-message.txt](lead-agent-message.txt), for thread `01a0f821-5e03-7781-bb0e-0d15efebcbe2`. Earlier coordination and completed-findings delivery attempts were rejected under the restricted permission profile. After the owner enabled full access, the messaging tool accepted the completed findings on October 1, 2026, at approximately 22:01 UTC and returned the recipient thread ID without an error. The verified relay is 967 UTF-8 bytes, within the tool's 1,000-byte limit. Delivery is confirmed by the tool; the primary's reading or acknowledgment is not independently confirmed. [delivery-status.json](delivery-status.json) records the successful retry and the earlier rejection.
