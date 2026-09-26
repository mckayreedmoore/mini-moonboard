# Ordinary-joint response method

Status: conditional method proposal for the actual WJ16 right inner full-stock
G7 family, 2026-09-24. This is a response-model path, not a solved joint,
capacity result, material inspection, or release. It does not describe the
active narrow-x95.25 trial.

## Current WJ24 first-patch method decision, September 26

For the owner-reviewed `led-clearance-2x6-runner-seated-blocks-v1` revision,
the first current ordinary joint is the bottom-center right, defined in the
[current criteria coverage](current-criteria-coverage.md): three full timber
members, four bolt stacks, and three finite timber contacts. Keep the direct
contact model as the selected method for this bounded characterization. It
represents the load-transfer mechanisms in question directly: bolt/bore
clearance and contact, timber faces that can open, the separate direct seat,
and the explicitly assumed bolt/nut axial-engagement route. Engagement is a
model scenario only; delivered hardware has not been inspected.

No current reduced connector law has supported applicability bounds for those
mechanisms. A generic end-connected beam bolt omits interaction between its
shank and bore surfaces, so it cannot supply the clearance-sensitive transfer
result on its own. The documented static-rank probe also did not produce a
unique response by prescribing one coordinate; holding that coordinate during
response adds an actuator load path. Do not adopt either shortcut to obtain a
converged result. A reduced model may be reconsidered only after it preserves
the same required load paths and demonstrates bounded response against the
direct patch.

The current diagnostic reached the first reported cleat-bore contact at
accepted state 39 (0.0195 s) and one complete following state 40. This is a
bounded, authenticated contact-event observation. It does not close whole-joint
equilibrium, time/mesh/contact sensitivity, physical engagement, bolt/wood
resistance, or current full-frame demands. Its next method gate is to set
source-backed equilibrium and response-comparison tolerances, then compare the
same frozen patch under the declared timestep/mesh/contact and engagement
sensitivities. A new run or instrumentation branch must state which of those
decisions it will settle and what executes next.

## Bound geometry and current evidence

The source-bound input report covers five wood bodies: the lower and upper
right service rails, `base_principal_center_right`,
`wj04_lower_full_stock_cleat`, and
`wj04_upper_g7_crosscut_full_stock_cleat`. Eight unique physical bolts serve
four wood-to-wood interfaces, with two bolts at each interface and 127 mm of
wood grip per bolt. Each physical stack has five CAD component roles (shaft,
head, two washers, nut), giving forty modeled hardware shapes; those shapes
are not forty purchased fasteners. The report authenticates axes, ordered
receivers, grain vectors, and contact-plane datums. It records cleat planar
areas of 10,552.972707 mm² at each lower interface and 7,637.052707 mm² at each
upper interface, but these do not establish the two-face overlap, active
pressure patch, surface gap, or contact stiffness. See the [full-stock input
report](hypotheses/wj16-full-stock-mechanics-inputs/README.md) and the
[criteria method map](criteria-method-map.md).

The composed 7.5 mm axes are CAD occupancy geometry, not a drill instruction.
The provisional 1/4-20 Grade 5, 6-inch K.L. Jack bolt candidate has a 127 mm
minimum smooth-body length and a 133.35 mm maximum thread-gage length. The
first full-form thread location and delivered parts are not authenticated.
Each modeled stack has two provisional Type-A-wide washers with catalog
thickness bounds of 1.2954–2.032 mm. Because the wood grip begins after the
head-side washer, the equality of minimum smooth-body length and wood grip is
not a smooth-shank coverage margin. Keep bolt engagement, washer-seat
behavior, contact pressure, and fresh signed loads open as recorded in the
[input report](hypotheses/wj16-full-stock-mechanics-inputs/README.md).

## Conditional response formulation

For finite wood faces, represent each of the four actual interface pairs with
unilateral, frictionless normal contact: pressure is compressive only; faces
can open; no tension, bonded transfer, or friction from unverified preload is
credited. Model each member as a finished solid with an explicit orthotropic
elastic tensor and grain orientation. The timber's compression compliance
then comes from its real volume, cuts, grain, and contact patch, rather than an
invented `E A / L_effective` face spring. A flat nominal face and its
zero-gap setup remain assumptions. Surface seating, roughness, growth-ring
orientation, and local crushing are not resolved by linear bulk elasticity.
Tests on timber contact report that contact faces may remain non-flat and
produce a softer local damage zone; the published values are not transferable
to this G7 geometry or its loading direction ([Totsuka, 2025](https://link.springer.com/article/10.1007/s00107-024-02169-w)).
Earlier wood-to-wood compression-joint work likewise shows that bearing
stiffness depends on stress spreading and member geometry; its simple-spring
value should not be imported as a WJ16 property ([Wanninger et al., 2015](https://www.sciencedirect.com/science/article/abs/pii/S0141029615004757)).

One transparent timber material scenario is the NDS mean longitudinal modulus
for DF-L No. 2 dimension lumber, `E_L = 1.6 × 10^6 psi` (11,032 MPa), combined
with Douglas-fir clear-wood FPL ratios `E_R/E_L = 0.068`, `E_T/E_L = 0.050`,
`G_LR/E_L = 0.064`, `G_LT/E_L = 0.078`, and `G_RT/E_L = 0.007`; use explicit
member grain vectors and run radial/tangential swaps where ring orientation is
unknown. The FPL values are species-average clear-wood data, not graded-stock
guarantees, and this combination is a declared model scenario rather than a
measured lumber property ([AWC 2024 NDS Supplement, Table 4A](https://awc.org/resources/2024-nds-supplement/); [USDA Forest Products Laboratory, Wood Handbook, Chapter 5](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/chapter_05_fpl_gtr282.pdf)).
If assumed-property sensitivity changes a governing result, retain the gate as
pending; do not present the scenario points as lower or upper material bounds.

For a simplified lateral service-slip comparison, the repository's published
source index records the 2004+A1:2008 Eurocode 5 Table 7.1 expression
`K_ser = ρ_m^1.5 d / 23` N/mm per fastener per shear plane, with clearance
added separately to deformation. At `d = 6.35 mm`, the existing 460/500/520
kg/m³ scenario points give 2,723.847/3,086.746/3,273.791 N/mm per plane. The
eight bolts here each cross one wood shear plane, so there are two such
physical fasteners per interface, not one spring per mesh cell. The centered
nominal 7.5 mm axis versus 6.35 mm body implies 0.575 mm one-sided geometric
travel only as a comparison; actual hole diameter, shaft, offset, and
assembly tolerance remain unselected. This is a service-slip analogy, not a
strength law or a complete joint model. The cited formula is from the older
Eurocode edition; EN 1995-1-1:2025 is now published, so do not label the older
expression the current Eurocode rule without checking that edition ([EN 1995-1-1:2004+A1:2008, §7.1](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf); [BSI EN 1995-1-1:2025 catalogue record](https://landingpage.bsigroup.com/LandingPage/Undated?UPI=000000000030286965)). The corrected NDS
`γ = 180,000D^1.5` expression belongs to §11.3.6 group-action `C_g`; it is not
a generic slip spring ([AWC 2024 NDS errata](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf)).

For axial behavior, preserve the series compliance structure
`1/K_total = 1/K_bolt + 1/K_clamped_stack`. A first-principles bolt term is
`1/K_bolt = Σ L_i/(E_s A_i)` over the actual smooth and threaded sections;
the clamped-stack term includes both washer seats and compression through the
real timber layers. Published timber-bolt tightening work separates thread
engagement, thread play, bolt cylinder, bolt head, and washer embedment. It
supports the component model but supplies no transferable WJ16 values
([Matsubara and Teranishi, 2022](https://link.springer.com/article/10.1186/s10086-022-02038-1)). Resolve those components in a local solid/hardware model
or keep the unavailable compliance explicit. Do not reuse PB03/PB02 stiffness
numbers or the selected-frame angle/SDS values.

Two lateral representations are possible, but must not be combined for the
same physical compliance: an explicit bolt-to-bore contact model lets the
bolt's bending and wood deformation develop in the solids; a reduced
per-bolt slip connector can use a declared service-slip scenario with an
explicit gap. Either route needs a separate resistance method. Current
evidence supplies neither a DF-L No. 2 dowel-bearing spring law for this
1/4-inch bolt nor the actual thread/seat/preload behavior. The criteria for
stiffness, contact, simultaneous actions, and resistance remain pending.

## Local patch preparation path

The smallest complete representative model is the five full local timber
bodies and their eight physical bolt stacks, not a single isolated bolt or an
inner-cleat-only slice. If trimmed subvolumes are later used, place their
boundary cuts outside the joint influence region and demonstrate response
stability as the cuts move. Prepare the patch as follows:

1. Bind the exact five body IDs, eight `STACK_SPECS`, ordered receiver pairs,
   four face pairs, forty installed-shape roles, inventory hash, family
   producer hashes, and WJ16 composition hash from the input manifest. Export
   separate immutable STEP solids with per-body SHA-256, CAD volume, centroid,
   and bounds. Preserve the distinction between eight purchased bolts and
   their forty modeled CAD roles.
2. Mesh every body independently so coincident points at opening interfaces
   do not share nodes. An unstructured quadratic C3D10 mesh can retain the
   actual crosscut and finished bore geometry. Refine around each of the
   sixteen shaft-to-receiver bore surfaces, the four wood interface patches,
   and the washer seats. Record mesh settings and prove element/node
   ownership, positive Jacobians, and integrated mesh volume/centroid against
   each STEP body. Use at least two refinement levels to check response
   stability; a target element size alone is not evidence.
3. Build a source-bound surface inventory: four actual wood/wood face pairs;
   sixteen bolt-shaft/receiver-bore pairs (eight bolts through two wood
   receivers); and the head-washer, nut-washer, bolt-head, nut, and wood-seat
   interfaces if those components are modeled as solids. Verify true contact
   overlap, opposed normals, face areas, gaps, and identities from finished
   geometry. The cleat planar area alone does not supply the common active
   contact patch. Do not silently omit a seat or introduce a tie to close a
   measured gap.
4. Apply explicit orthotropic timber orientations from the source inventory
   and the declared material scenario. Model the eight actual bolt axes with
   one physical steel member each; join CAD head/shaft roles only as one
   continuous bolt, and represent nut/thread engagement only under a named
   idealization with the thread limitation retained. Include both washers per
   stack or state the exact condensed seat law used. No extra `K_ser` spring
   may be added where explicit bolt/bore and timber solids already supply that
   lateral compliance.
5. Apply compression-only frictionless surface contact at the four timber
   faces and at bolt/bore interfaces, with clearances as explicit geometry
   scenarios. CalculiX's available examples use a linear pressure-overclosure
   penalty. That coefficient controls numerical contact enforcement; it is
   not the material's physical face stiffness. Repeat with changed penalty
   values and mesh refinement, and show stable integrated forces, moments,
   opening, and member response without material penetration. Flatness,
   initial gap, and clamp/preload remain documented scenario inputs.
6. Apply six independent interface unit-wrench cases plus small load steps in
   the application directions needed to capture opening and bolt engagement.
   Keep the restraints remote from the joint and move them in a sensitivity
   check. Record bolt forces, contact pressure/displacements, and signed
   six-component actions for each physical interface at fixed datums. Compute
   moments as `Σ[(r_i-r_0) × F_i]` plus any applied point couples; compare the
   internal force/moment sum to the boundary wrench with equal-and-opposite
   member ownership. A linear small-load matrix is only valid over its stated
   range; it does not define wood yielding, splitting, or capacity.

The patch is a method-development step. It does not require an external
prototype or sign-off as a blanket gate. Sensitivities and open inputs remain
visible in the conditional report; cases that depend on unsupported material,
hardware, contact, or failure behavior remain pending.

## Existing code that can be reused

| Existing code | Reusable part | Scope limit |
|---|---|---|
| [`scripts/wood_joint_wj04_full_stock_mechanics_contract.py`](../../scripts/wood_joint_wj04_full_stock_mechanics_contract.py) | `build_mechanics_contract(g16)` binds the eight physical axes, four interfaces, receivers, grain, datums, and provisional hardware. | It emits inputs, not a response law, capacity, or native model. |
| [`fea/stitch_joint_mesh.py`](../../fea/stitch_joint_mesh.py) | `GMSH_TO_CCX`, `external_faces`, `surface_faces`, `append_body`, and `validate_ownership` support independent C3D10 bodies and quadratic TRI6 exterior ownership. | Its worker accepts a different six-part geometry inventory. A WJ16 patch producer must provide its own body IDs, surfaces, and cut/axis mapping. |
| [`fea/compact_joint_mesh.py`](../../fea/compact_joint_mesh.py) | `cad_surfaces`, cylindrical surface selection, mesh provenance, Jacobian/volume checks, and an explicit interface inventory are good patterns for a multi-body patch. | `geometry`, `worker`, and `interface_inventory` are pinned to a 26-body study, 25 planar adjacencies, and axis-specific hardware; do not call them on WJ16 unchanged. |
| [`fea/panel_contact_coupon.py`](../../fea/panel_contact_coupon.py) | `deck`, `prepare`, and `solve` demonstrate a two-body, frictionless CalculiX surface-contact deck and frozen-deck/source checks. | Its isotropic `7000, 0.3` material and selected penalty are coupon assumptions; its own limits say contact-wrench audit is pending. Reuse syntax/workflow only. |
| [`fea/solve_joint_contact.py`](../../fea/solve_joint_contact.py) | Demonstrates C3D10 pin-to-bore contact surfaces, a declared radial clearance, `*CONTACT PAIR`, and `CDIS/CSTR/CF` output. | It is a single-leg pin coupon with isotropic material and illustrative geometry. It supplies no WJ16 bolt, timber, or force-sharing data. |
| [`fea/current_response_model.py`](../../fea/current_response_model.py), [`fea/current_response_materials.py`](../../fea/current_response_materials.py) | `CurrentStructure.deck` shows CalculiX engineering-constant material cards and per-member orientations; `validate_constants` checks an orthotropic tensor. | The prepared model uses C3D20 frame bodies and point connectors; its existing wood, panel, bearing, and connector constants are not this joint's inputs. `connection_stiffnesses()` includes a 38.1 mm washer-seat analogy and must not be copied. |
| [`fea/current_response_run.py`](../../fea/current_response_run.py) | Source snapshot, immutable preparation, solver invocation, and artifact-retention patterns; `physical_forces` demonstrates signed connector ownership. | `run()`/`assess()` target the shoe-free frame and assume its panels, floor supports, and connector schema. A local C3D10 patch needs its own small runner/postprocessor or a deliberately generalized adapter. Existing functions do not integrate finite wood-face contact into a wrench. |
| [`fea/floor_contact.py`](../../fea/floor_contact.py), [`fea/floor_contact_results.py`](../../fea/floor_contact_results.py) | Surface definitions, `*CONTACT PAIR`, contact-state output, and independent force/moment equilibrium auditing patterns. | This is a floor-contact model with its own friction and boundary assumptions. Its linear pressure-overclosure parameter is a numerical penalty and not transferable face compliance. |
| [`mini_moonboard/bolted_joint_mechanics.py`](../../mini_moonboard/bolted_joint_mechanics.py) | `Wrench`, `shift_wrench`, `to_local`, `equilibrium_residual`, and `require_unique_physical_fasteners` support signed-action accounting. | `compression_only_contact` projects a supplied force; it does not solve face pressure/opening. `clearance_response` is monotonic scalar screening, not a 3D bolt/contact solver. |

The repository does not yet provide a general WJ16 patch mesher, four-interface
contact deck, orthotropic bolt/wood response adapter, or integrated finite-face
contact-wrench postprocessor. The [native adapter readiness plan](native-adapter-readiness.md)
already records that not every bolt hole must be meshed in the whole-frame
model; local finished holes, cuts, contact faces, response law, and net-section
evidence still have to be authenticated. A successful patch solve would
advance method evidence only. It would not replace fresh full-frame actions,
the 24-duty resistance methods, or the conditional release gates.
