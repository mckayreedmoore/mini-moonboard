# Independent source-method review: washer response and contact

**Reviewed:** 2026-10-01. **Reviewed artifact SHA-256:**
`20e85755030d56d14779bca0598aa3c057a58e8a188aa77693b8b3219bc85bf0` for
[`source-method-review.md`](source-method-review.md). This review is read-only
with respect to that artifact and all model/source inputs. No native analysis
was run.

## Findings and disposition

The central method conclusion is supported: 3D nonlinear contact between the
washer, fastener bearing part, and a finite orthotropic timber receiver is a
defensible method family for conditional washer response. Teranishi et al.
(2021) model a bolt, square washer, and Japanese cedar with surface contact,
steel von-Mises plasticity, and orthotropic elastic-plastic wood. They compare
embedment load-displacement response for nine washer geometries against tests.
The reported mean errors (18% lower initial stiffness and 14% higher yield
load) are correctly summarized in the reviewed artifact and do not support a
one-sided correction. This validates assembly embedment response for that
study's setup; it does not directly validate washer stress/plastic-strain
recovery, or the round, much smaller WJ24 washer and its different steel/wood
inputs. The updated source-method review now states this distinction directly;
that clarification is accurate and resolves the earlier scope concern.

The review correctly preserves the ordinary 25NWUS boundary. Its conditional
supplier description is low-carbon steel and Type A Wide dimensions without a
numeric yield minimum; ASTM F844-19(2024) describes unhardened general-use
washers and does not publish a washer-on-timber resistance. The 25NWUS8Z
hardness entry cannot be converted into yield here. The local option note for
254 SMO provides a 310 MPa conditional material-yield input for an explicitly
hypothetical solution-annealed washer, but does not bind that value to the
baseline 25NWUS or a dimensionally confirmed delivered part. Elastic response
scenarios can use declared elastic inputs; a plastic/yield scenario needs its
own declared stress-strain input. None of this creates a design resistance.

The partial-seat treatment is supported. The source-pinned geometry packets
cover 184 candidate outer seats, with 183 meeting their stated footprint gates
and the nut-side seat at `center_principal_right_2` remaining a distinct
exception. A full-ring or axisymmetric pressure assumption must not be carried
over to that seat; a separate 3D model needs the actual saved receiver cut and
declared contact/material branches. The ASTM D8633-26 scope statement is also
quoted with the right limit: its phrase concerns partial bearing through the
product thickness. That public wording does not itself classify a clipped
plan-view washer footprint, so it neither resolves nor independently rules
the partial seat in or out.

Conditional model analysis does not require a new physical test or receipt of
hardware when geometry, actions, and material/contact values are explicitly
declared as assumptions or ranges. A test or product record becomes relevant
when the claim is about physical applicability, delivered-part conformance, or
a product/assembly resistance. Such evidence must match that claim; a test is
not an added blanket prerequisite for conditional response calculations.

One useful source update was not in the reviewed artifact: Teranishi and
Matsubara's publisher abstract for “Progressive damage analysis of embedment
of metal washer into timber” (published online 2024; journal issue 2025, DOI
[10.1080/17480272.2024.2345191](https://doi.org/10.1080/17480272.2024.2345191))
reports an explicit dynamic model with timber plasticity/damage, comparisons
for three species, and stated errors of 12%, 16%, and 7% for initial
stiffness, second stiffness, and yield load. It also reports loading-rate,
mesh, contact-stiffness, and damage-constant studies. The publisher's full
text was not accessible in this review, so these are abstract-level source
facts only. This is not a contradiction of the 2021 paper: it is a relevant
later method lead with different model and validation scope. It should be
inspected before selecting a published benchmark or solution procedure; none
of its reported errors transfers to WJ24.

I also independently checked the new benchmark packet against the local
primary PDF (SHA-256
`a68a303250ab4ad43576eed7b3f60f35d98335da5b3d7ca5adb060779e08ad6f`). The
three Table 4 response pairs, Table 2 steel values, Table 3 printed wood
constants, setup, contact definitions, and output definitions match. The
packet correctly withholds an executable tensor. In particular, the three
printed Poisson pairs fail conventional orthotropic reciprocity with the
printed Young's moduli; the article does not disclose how its Abaqus input
reconciled the six values. This is a material reproduction limit, not a
transcription error. See the separate
[benchmark review](benchmark-review.md).

For local stress recovery, refine the reviewed artifact's “stress/strain
convergence” instruction: ideal sharp washer edges or abrupt contact boundaries
can produce mesh-sensitive local peaks. Bind a finite washer/head/nut edge
profile for each conditional scenario and assess contact force balance,
load-deflection response, contact extent, and plastic-zone development under
refinement. Treat an unresolved peak as a limitation rather than a converged
yield conclusion. The updated source-method review now binds a finite edge
profile and retains unresolved peaks as limitations, which is the appropriate
disposition. This does not change the chosen 3D contact method.

## Supported next method-preflight sequence

1. For each covered role/case, select the applicable source-bound signed
   outer-seat action from the existing primary-corner, upper-cohort, or
   remaining-54 three-case joins and bind it to a declared
   washer/head-or-nut/receiver scenario. This uses the existing action records;
   it does not imply another demand solve or a six-case envelope. Keep
   baseline 25NWUS material separate from any alternate such as the
   conditional 254 SMO input. Include finite bearing-land/chamfer and
   edge-profile assumptions, timber grain axes, cuts, friction branch, and a
   finite receiver domain. Any assembly preload, head/nut tilt, or prying effect
   outside those source joins must remain an explicit scenario branch rather
   than being inferred from the signed tie scalar.
2. Before an assembly model, verify the pinned solver's solid response and
   contact/load extraction on small known-answer fixtures: elastic washer
   deformation, compression-only contact, opening/reopening, and a rigid
   bearing part applying a known resultant. Check reaction balance and
   sensitivity to mesh/contact enforcement. The existing MIT clamped-annulus
   result remains a plate-kernel check only.
3. As an additional method-validation route, reproduce a fully specified
   published washer-embedment case, preferably Teranishi et al. (2021), with
   that study's square geometry, cedar and SS400 inputs, boundary conditions,
   friction, and measured load-displacement comparison. Record the reproduced
   error without fitting or transferring a correction factor. Inspect the
   2025 follow-up's full methods first if it is to be the benchmark. This
   replication is evidence for method applicability; it is not a prerequisite
   to a clearly hypothetical conditional scenario.
4. After the solver's small known-answer checks, a conditional round-washer
   WJ24 seat may be evaluated with finite head/nut contact and compressible
   wood contact. Expand the domain, refine the contact region, and branch
   unresolved material, friction, and profile inputs. Keep response and
   sensitivity claims separate from product conformity or resistance.
5. Evaluate `center_principal_right_2` nut-side as its own non-axisymmetric
   case with the saved service-passage cut. Do not use the 183-seat support
   count or an annular-area average to stand in for its traction field.

## Sources inspected and unclosed dependencies

Local pinned files and hashes were checked against the reviewed artifact:
the ordinary nut/washer property basis, ordinary-washer yield-option note,
bolt resistance basis, upper and remaining washer-seat geometry packets,
primary-corner support packet, existing washer-bending method review, annular
plate benchmark/helper records, and cited CAD/helper source files. All hashes
quoted for these reviewed files match their current local contents. The primary
2021 *Journal of Wood Science* PDF, new benchmark input note, and three-row
CSV were also hashed and independently checked; their hashes are recorded in
[benchmark-review.md](benchmark-review.md). Primary sources inspected were
the full public 2021 article, the publisher abstract for the 2025 follow-up,
ASTM F844-19(2024) and D8633-26 public scope pages. The licensed ASTM clauses
were not used to infer capacity.

The action-scope clarification was checked against the existing three-case
source joins: the [primary corner axial-seat register](../mvp-acceleration-2026-09-28/current-corner-three-case-axial-seat-register-attempt01/README.md),
the [upper outer action record](../upper-outer-load-path-2026-10-01/actions.md),
and the [remaining-54 signed outer-seat action packet](../remaining-candidate-washer-demands-2026-10-01/README.md).
Their applicable seat actions can be joined to a local conditional stack
without another demand solve. These are three-case records, not a six-case
envelope or a physical preload/prying model.

Still open are the exact delivered washer and bearing-part profiles/properties,
the contact and material scenario chosen for each role, timber constitutive
inputs, and applicability of the selected solver formulation. Existing
three-case source-bound action joins cover the primary-corner, upper, and
remaining candidate cohorts; their applicable signed seat actions need to be
matched to the local scenario. They do not supply a six-case envelope or
physical preload/prying effects outside their scope. The partial seat
additionally needs its own supported response case. These remain
conditional-model inputs and evidence boundaries; they do not imply another
demand solve or impose a blanket physical-test or external-approval gate.
