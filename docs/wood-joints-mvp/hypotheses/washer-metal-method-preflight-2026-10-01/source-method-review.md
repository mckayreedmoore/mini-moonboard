# Washer-on-timber metal method preflight

**Reviewed:** October 1, 2026. **Scope:** identify a defensible method for
washer metal bending/contact on the present wood-joint candidate. This is a
source and method review only. It selects no washer, adopts no capacity,
changes no geometry, and runs no native or heavy mechanics analysis.

## Finding

There is a viable method family: a three-dimensional nonlinear contact model
of the washer, its actual head-or-nut bearing part, and the timber receiver,
validated against measured washer-embedment response. The key primary study
uses that family: it models washer, bolt, and orthotropic timber with surface
contact and elastic-plastic material response, then compares load-embedment
curves for nine washer geometries with experiments. That evidence establishes
feasibility of the method, not a WJ24 result. The study used Japanese cedar and
SS400 steel, found material sensitivity, and reported average model errors of
18% low in initial stiffness and 14% high in yield load. Those errors are not
a one-sided safety bound and must not be transferred as a correction factor
for this candidate. [Teranishi et al., *Journal of Wood Science* 67, 41
(2021)](https://doi.org/10.1186/s10086-021-01973-9).

The study compares assembly load–embedment response. It does not directly
validate local washer stress or plastic-strain recovery, or establish those
results for this candidate's round washer and different material inputs.

The current scalar washer-area and ideal plate formulas cannot bound the
candidate's steel bending. They assign neither the force footprint on the
washer nor its actual timber reaction distribution. For any one washer, force
equilibrium fixes only the resultant `T`; it does not fix the spatial contact
tractions that set the plate moments and local stress. A uniform `T/A`
annular pressure is an average under a stated full-annulus assumption, not a
measured or mechanically derived pressure field. A clamped-ring or
simply-supported plate result is not a conservative substitute for unilateral
wood contact without a proof that its load and support boundaries envelope
the physical problem.

## Current source boundary

The candidate geometry screen covers **184 outer washer seats**. It reports
183 meeting the declared eccentric-annulus geometry gates and one separate
partial-support exception: the nut-side seat of
`center_principal_right_2`. The geometry screen establishes only where a
declared annular footprint intersects the frozen wood solids; it does not
establish physical contact, pressure, metal stress, or wood resistance. The
exception is asymmetric and cannot be folded into an axisymmetric/full-ring
calculation. [Integrated 184-seat result](../upper-washer-eccentric-support-2026-10-01/README.md)
(local SHA-256 `4a28bf7d13f4175e0019feae686496ea38e8236d2e557d24acd633b19b7fb3a6`);
[partial-seat detail](../remaining-candidate-washer-seats-2026-10-01/README.md)
(SHA-256 `9d8c9ebd6f7ba60fedf58e73baa3148aa5c34b55ae607a1889ead9262e2ca770`).

The conditional CAD washer dimensions are 18.6436 mm OD, 8.0 mm ID, and
1.651 mm nominal thickness. Their annular radial width is 5.3218 mm, so the
illustrative thickness-to-width ratio is about 0.31. This is a geometry
warning against presuming thin-plate theory; it is not a code slenderness
limit. The Type A Wide dimensional envelope used in the geometry studies is
OD 18.4658–19.0246 mm, ID 7.7978–8.3058 mm, and thickness 1.2954–2.032 mm.
Those are conditional catalog bounds, not a selected or received part. The
candidate `25NWUS` description is plain low-carbon steel but supplies no
numeric yield minimum. ASTM F844 covers unhardened general-use plain washers;
its public record supplies no washer-on-timber bending rating. The existing
property basis therefore leaves the needed washer yield input unresolved.
[Ordinary nut/washer property basis](../../current-ordinary-nut-washer-property-basis.md)
(SHA-256 `98a151ae040232aa1f2485826ba4c29dc0e0d0fb1ce6ac87ddd9bf062eeb6bcf`);
[ASTM F844 record](https://store.astm.org/standards/f844).

The current [NDS-2024 DF-L No. 2 `Fc⊥` reference of 625 psi](../../bolt-resistance-basis.md)
(SHA-256 `1b5e1a261735f7630c0c45fe505a4755227dd88d52091f112141f0c1332f0d80`)
is a wood design-value reference for a separate bearing comparison. It is not
an orthotropic nonlinear wood constitutive curve and does not determine
washer contact pressure. ASTM D8633-26 now provides cross-grain compression
strength and stiffness test methods, including full-size application tests;
its public scope says those methods assume full support through product
thickness and excludes partial bearing through that thickness. This is useful
for wood material/application characterization, but it is not a washer rating.
That thickness-scope phrase does not itself decide whether a partly clipped
plan-view washer footprint is covered, so it cannot close the named partial
seat.
[ASTM D8633-26 scope](https://store.astm.org/d8633-26.html).

The outer wood footprint is better specified than the inner load footprint:
the candidate hardware packet does not provide an exact bearing-land/chamfer
contact patch for each cap head and finished nut. Their outer envelopes do
not define that patch. Even on the 183 geometrically supported rings, the
load enters through head-or-nut contact and leaves through a deformable,
possibly nonuniform wood contact region; neither is represented by the
area-only result. Keep the partial seat as its own full 3D geometry/contact
case. [Primary-corner support source](../corner-washer-support-2026-10-01/README.md)
(SHA-256 `fc6e1c62fc712866554f85d8e90a8779e84e2ef635581e97e8130383218d7db6`).

## Smallest defensible method path

For each conditional axial scenario, model one local stack in 3D: a declared
washer solid, head-or-nut contact patch, and finite wood receiver with the
modeled bore, edge, and nearby cuts. Use exact product dimensions/materials
when known; otherwise identify hypothetical values or ranges as assumptions,
not delivered-part facts. Apply the signed axial washer action through the
fastener contact geometry, not as uniform pressure on an assumed annulus. Use
compression-only contact at both interfaces, allow separation and local
timber indentation, and do not tie or clamp the washer perimeter to the wood.
Declare grain directions. Demonstrate remote-boundary insensitivity by
expanding the wood block (or match the fixture when reproducing a test).
Use source-supported friction parameters where available and show sensitivity;
frictionless contact is one scenario, not automatically conservative.

Use a 3D continuum washer model for the present thickness/span geometry.
For conditional analysis, state a hypothetical washer thickness/profile,
elastic constants, and yield input (or explicit ranges) and report response
and sensitivity by scenario. The current ordinary-washer source supplies no
numeric yield minimum, so no actual-product steel-yield conclusion follows
without a justified value. Recover von-Mises stress and plastic strain with
contact-edge and mesh-refinement checks. Bind the finite washer/head/nut edge
profile in each scenario: ideal sharp edges or abrupt contact boundaries can
leave local peak stresses mesh-sensitive. Check reaction balance,
load–deflection response, contact extent and plastic-zone development under
refinement; retain an unresolved peak as a limitation. Even with a minimum
yield input, a first-yield comparison is not an allowable/design resistance; the applicable
design format and factor or a separately justified assembly-resistance basis
would still be needed for such a claim. Do not borrow bolt yield, washer
hardness, timber `Fc⊥`, or bolt proof load as the washer's bending strength.

On the timber side, `Fc⊥` alone cannot define the pressure field. For a
conditional numerical scenario, declare the wood law and grain-axis values or
ranges, support/contact assumptions, and sensitivity branches; ASTM D8633-26
tests are one possible source of cross-grain material data, not a prerequisite
for running such a scenario. Its public scope is not a washer/contact
validation. Model the partial seat with its own plan-view footprint and
declared material/contact branches; do not transfer the other 183-seat result
to it. Representative tests are one possible later route to validate
physical applicability if that is the claim being pursued.

## Checks and claim boundary for a candidate model

1. **Numerical plate check:** reproduce the existing MIT OCW clamped-annulus,
   uniform-pressure known answer and boundary slopes with a linear plate
   solution/mesh. The stored normalized value is `W(5)=17.55185416356537` for
   `a=1`, `b=10`, `D=P=1`. This checks the elastic plate kernel only; it does
   not validate contact or support for this assembly. [MIT OCW Recitation 5](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013/resources/mit2_080jf13_recitation5/);
   local [known-answer derivation](../evaluation-resume-2026-09-24/current-washer-plate-response-attempt02-mit-ocw-clamped-annulus-2026-09-28/benchmark-calculation.md)
   (SHA-256 `16fddb9e5a2d6716c0f50ade700815bcee63b846c0331ce306939bd8a6111988`).
2. **Contact/material method validation:** reproducing the published
   washer-embedment load–displacement and reported yield-load/stiffness
   comparisons for its own geometry, SS400/wood inputs, and contact setup is
   a useful available validation route. Do not transfer its mean error as a
   design factor: the study reports materially sensitive predictions and a
   14% high average yield-load result. If a candidate scenario changes those
   materials or geometry, justify the selected parameter values/ranges from
   applicable sources and show sensitivity; do not present the paper's
   comparison as validation of the changed scenario.
3. **Conditional candidate preflight:** a numerical scenario may proceed
   without received parts or a new physical test when its inputs are explicitly
   declared. Bind or branch the washer and head/nut contact patches, steel
   properties, wood material/orientation law, friction, support contact, and
   the actual modeled full or partial seat; check force balance, penetration,
   mesh/domain/load-path sensitivity, and steel stress/strain convergence.
   Missing product-specific inputs remain assumptions or ranges and keep the
   result conditional. This is a modeled response/sensitivity result, not
   proof of delivered-part fit, physical contact, or capacity.
4. **Physical/product claim:** measured representative specimens are one
   possible route to validate physical applicability and correlate model
   response for a later claim about delivered parts or product/assembly-rated
   capacity. Any test result applies to its specimens; a design allowable or
   product-wide resistance still needs its own justified statistical, material,
   and design basis. Such testing is not a prerequisite for conditional
   arithmetic unless an expressly adopted method requires it.

The existing annular helper passes a useful unit benchmark, but its source
case has uniform annular pressure and perfect clamps at both radii. Its own
documentation excludes finite fastener contact, unilateral/partial timber
support, crushing, local shear, and material yield. It must remain a software
check and not the washer method. [Helper implementation](../../../../mini_moonboard/washer_plate_response.py)
(SHA-256 `92b238d95bc8fd090e5c30232269f5d0687b9b27e3ca64ac5d4b63dc3bff30b9`);
[helper scope and test record](../evaluation-resume-2026-09-24/current-washer-plate-response-helper-attempt01-2026-09-28/README.md)
(SHA-256 `999531911630db675291be967e0ce7511089adc521491a59cc73b4d3db27559d`).

## Decision boundary

The current annulus area, force resultant, and catalog exterior dimensions
alone do not establish an unconditional steel-bending demand/capacity result:
they omit the load patch, support traction field, wood contact law, and
numeric yield strength of the ordinary washer. Conditional numerical scenarios
can proceed with explicitly declared assumptions/ranges and verified model
checks; they quantify those scenarios only. Whether those inputs represent
delivered parts and physical contact remains open. Representative testing is
one possible evidence route for physical/product-level claims, not a blanket
precondition for conditional analysis. The current 184-seat geometry screen
remains useful for defining modeled support footprints; it is not a contact
model. `center_principal_right_2` nut-side partial support stays separate. No
washer selection, adopted resistance, criteria disposition, native result, or
joint acceptance follows from this review.

## Source pins and primary literature

The owner's later research relay supplied three paired experiment/FEA targets.
The primary checked the local source PDF's hash and visually verified Tables
2–4; [benchmark-inputs.md](benchmark-inputs.md) and its linked CSV retain the
three rows, printed material constants, setup and output definitions. No
candidate material, tensor, contact method or resistance is adopted by that
numerical transcript.

- [Existing bolt/washer resistance basis](../../bolt-resistance-basis.md),
  SHA-256 `1b5e1a261735f7630c0c45fe505a4755227dd88d52091f112141f0c1332f0d80`;
  [resistance helper](../../../../mini_moonboard/wood_joint_bolt_resistance.py),
  SHA-256 `488e58bbd58fbc2f22af5d4122e734732bae09de79dad71bbf2623eeca60b166`.
- [CAD washer constants](../../../../mini_moonboard/wood_joint_frame.py),
  SHA-256 `77b4a8b28b02088878f1f0e0483610a7918cb85f5694f0551f50cf8888886545`.
- [Current washer bending-method review](../evaluation-resume-2026-09-24/current-washer-bending-method-attempt01-2026-09-28/README.md),
  SHA-256 `f343fc13ab820861f05d56584e3137026631acf14bba17c0d0a576ea16c18cfa`.
- Teranishi, M. et al. (2021), [publisher article and methods/results](https://link.springer.com/article/10.1186/s10086-021-01973-9),
  DOI [10.1186/s10086-021-01973-9](https://doi.org/10.1186/s10086-021-01973-9).
  The paper describes 3D washer/bolt/wood contact and orthotropic elastic-
  plastic timber, reports contact coefficients and SS400 assumptions, and
  compares FEA load–embedment results with tests; its reported average yield
  load overprediction limits use as a conservative predictor.
- Awaludin, A. et al. (2012), [publisher-hosted full paper](https://pure.tue.nl/ws/portalfiles/portal/3633744/731744636991605.pdf),
  *A Finite Element Analysis of Bearing Resistance of Timber Loaded through a
  Steel Plate*, *Civil Engineering Dimension* 14(1), 1–6. It describes 3D
  solid/contact modeling with anisotropic timber and elastic-perfectly-plastic
  washers, and comparison with washer-embedment experiments; its materials and
  specimens are not the present candidate.
- [ASTM F844-19(2024)](https://store.astm.org/standards/f844),
  [ASTM D8633-26](https://store.astm.org/d8633-26.html), and the
  [2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/).
  Public scope pages support only the scope statements above; licensed
  standard clauses were not used to infer a washer design resistance.
