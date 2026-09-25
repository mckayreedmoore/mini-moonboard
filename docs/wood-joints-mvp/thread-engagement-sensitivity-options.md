# Thread-engagement stiffness sensitivities for the WJ24 bottom-center patch

Status: conditional response-sensitivity method for the current WJ24 local
patch, 2026-09-24. It covers the three timber bodies
`bottom_center_right_cleat`, `base_rail_bottom_right`, and
`base_principal_center_right`, plus four provisional bolt stacks:
`bottom_center/clip_horizontal_bottom_right_1/{rail_1,rail_2,principal_1,principal_2}`.
An elastic bolt model, rigid finite nut, and explicit axial spring/no-slip
branch can explore how response depends on assumed axial thread restraint
without first building a helical thread mesh or testing the same product. The
result remains a declared sensitivity: it is not measured thread stiffness,
hardware fit, a conservative complete-joint bound, capacity, or acceptance.
Keep physical transfer status `UNRESOLVED_AXIAL_ENGAGEMENT`; label the
equality-row branch `STIFF_LIMIT_SENSITIVITY_ONLY` and any finite analyst-set
spring sweep `PARAMETRIC_SPRING_SENSITIVITY_ONLY`.

## Scope and current evidence

The four axis identities and ordered receivers are recorded in the
[WJ24 composition](hypotheses/wj24-integrated-static/composition.json); the
[WJ24 hardware inventory](hypotheses/wj24-hardware-inventory/inventory.json)
classifies their hardware as provisional CAD envelopes with no SKU or
delivered part selected. The current reviewed geometry revision is
[`led-clearance-2x6-runner-seated-blocks-v1`](hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/README.md).
At mechanics freeze, bind the three wood solids, four stack axes, receivers,
datums, contact surfaces, and bolt/nut envelopes to that revision's exact
source hashes. The earlier integrated composition is an identity reference;
do not reuse its geometry hash as the current revision's fingerprint.

No WJ24 product schedule or delivered thread profile is established for these
four axes. WJ24's separate [center-axis length screen](wj24-bolt-length-screen.md)
covers its named 16 center axes; its conditional 4.75-, 5.75-, and 7.5-inch
classes and 3.175 mm projection screen do not assign a product or length to
this bottom-center patch. The WJ04 6-inch K.L. Jack `25C600HCS5Z` / `25CNFH5Z`
pair discussed in the [historical WJ04 thread method](thread-engagement-method.md)
is an example for that older patch only. Do not transfer its product identity,
thread bounds, or assumed engagement to WJ24.

When a product is selected for these axes, bind the external and internal
thread classes to that exact bolt/nut pair. [ASME B1.1-2024](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
specifies Unified thread form, series, class, allowance, tolerance, and
designation; it does not identify or inspect the delivered WJ24 parts.

The current WJ24 patch has no local response model or source-supported axial
bolt-to-nut law. The earlier WJ04 contact fragment is a method reference, not
the WJ24 contact model: its frictionless projected root-cylinder/bore pair
blocks radial penetration after contact but cannot carry bolt tension. Any
future WJ24 radial root/bore pair has that same limitation. The existing
`ThreadConstraint` record in the
[rigid-mode diagnostic](../../fea/wood_joint_patch_rigid_modes.py) is a
caller-declared kinematic rank row; it supplies no force law, stiffness,
capacity, or evidence of engagement.

## Bounded model choices

Use one continuous deformable bolt body and one finite rigid nut per modeled
stack. The bodies and their geometry profiles remain explicit assumptions
bound to the current WJ24 patch inputs. Keep the nut's finite seat geometry and
compression-only seat contact. Rigidizing the nut removes its compression
and warping compliance, while preserving rigid translation and rotation and
the finite geometry that locates its seat. Keep washer and timber compliance
in their explicit bodies/contact; do not include those terms again in an
engagement spring.

For bolt axis unit vector `a`, bolt-side engagement-band nodes `i`, normalized
surface tributary weights `w_i`, and a nut reference point at the weighted
band centroid's axial datum, the no-slip branch adds one scalar relation:

```text
Σ_i w_i = 1
Σ_i w_i (a · u_i) - a · u_nut_ref = 0
```

Emit it as one explicit `*EQUATION`/MPC row per physical bolt. The band is a
finite patch over the assumed overlap inside the nut, and the centroid used by
the weights must lie on the nut reference point's bolt-axis line. This
first-moment condition makes the row invariant under common rigid translation
and rotation and avoids an artificial couple. Preserve the node/area map and
source station bounds. This row represents infinite axial engagement stiffness
and zero axial slack; it acts bilaterally in both force signs. It leaves
relative radial and tangential motion, nut rotation, and local band deformation
unrestrained by the row. It does not close the radial gap or tie the complete
bolt and nut surfaces. Do not add a high-stiffness penalty spring in parallel.

A finite parametric branch may instead use one scalar axial spring between the
same mean bolt-band motion and the nut reference point:

```text
δ_eng = Σ_i w_i (a · u_i) - a · u_nut_ref
F_eng = K_eng δ_eng
```

Use a bilateral, zero-slack, zero-preload linear law for this sensitivity
branch. `K_eng` is an analyst-selected parameter, not a sourced thread
property. To make a reproducible sweep without implying physical bounds, define
`K_b,ref = E_ref / Σ_j(L_j/A_j)` from the exact frozen bolt-body geometry
between the head-bearing datum and engagement band, using the declared
reference steel input. Freeze this reference calculation and sweep
`K_eng/K_b,ref = 0.1, 1, 10, 100`, then compare with the equality-row stiff
limit. These log-spaced ratios are exploration points only; they are not
confidence limits, likely values, or proof that the actual thread response is
bracketed. Preserve a zero-stiffness/disengaged diagnostic if useful, including
any resulting free mode. Do not tune a spring value to obtain a preferred
joint response.

Implement the scalar spring with an axial-only force direction and a named
finite distribution map to the bolt band. Validate the exact connector and
distribution syntax in the pinned CalculiX build before use. The spring must
not impose transverse compatibility, a bending moment, or a nut-rotation
constraint. If the solver route cannot realize and audit that scalar mapping,
retain only the equality-row stiff limit and the unresolved physical
engagement status. Do not replace a failed spring mapping with whole-ring
kinematic coupling or a cylinder `*TIE`.

The [pinned CalculiX 2.21 manual](../../fea/generated/connection/ccx_2.21.pdf)
has SHA-256
`16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8` (official
[2.21 manual](https://www.dhondt.de/ccx_2.21.pdf)). Its rigid-body, equation,
elastic, and spring cards distinguish finite-body rigid kinematics, linear
MPCs, steel material response, and connector force response. The manual does
not validate this application-specific band map. The local
[rigid-mode MPC record](../../fea/wood_joint_patch_rigid_modes.py) may audit
row direction and participation, but rank is not a force law or signed force
accounting. Recover spring force from its connector output or a verified
section cut. For the equality row, do not infer engagement force from support
reaction totals alone; reconcile the bolt cut force, washer-seat/contact
resultants, and free-body equilibrium.

## Material and geometry branches

The generic elastic-steel reference is `E = 200,000 MPa`, `ν = 0.30`, based on
AISC 360-22 Table B4.1a and a published AISC finite-element study. See the
[local steel scenario and source record](steel-elastic-material-scenario.md).
This supplies a reproducible elastic reference for sensitivity work; it does
not identify a WJ24 bolt, nut, washer, or grade. It also does not carry the
WJ04 hardware scope of the source note into the WJ24 product schedule.

Start with the declared reference card. Run material-property sensitivity when
the response is materially influenced by the selected steel values; the full
nine-point `E`/`ν` Cartesian grid is available but is not a prerequisite for
every diagnostic. If a supported perturbation changes the governing force
path, reported response, or interpretation, retain the result as sensitive or
unresolved and investigate the actual material basis. Neither the generic
modulus nor its sensitivity values assign yield strength, thread area, or
resistance.

The WJ24 CAD bolt/nut envelopes do not locate a delivered first full-form
thread, last full-form thread, thread runout, or nut-fit condition. Keep each
modelled engagement interval explicitly labelled as assumed. The nominal
no-slip branch may assume the full active nut height is threaded solely as a
stiffness sensitivity. If later measurements establish only a partial overlap,
a separate sensitivity may apply the same no-slip or parameterized law only
over that measured full-form portion. It does not pass the product-specific
full-height engagement and projection condition selected for that exact axis.
Do not extend a coupling into unthreaded shank, derive a thread transition
from nominal bolt length, or use a smooth-body/root profile as a physical
lower or upper bound.

For a physical finite thread law, a same-product coupon is one valid route,
not the only route. A directly applicable, source-backed test or validated
model may support a finite law when its thread form, size, class, nut,
engagement length, material, fit, and loading range match the exact selected
hardware and the law excludes bolt-body and clamped-stack compliance already
modelled in the patch. If none applies, keep the physical law
`UNRESOLVED_AXIAL_ENGAGEMENT`; the parametric spring and stiff-limit branches
remain sensitivity-only.

## Interpretation limits

Under a stable linear contact active set, the equality row is the infinite
stiffness endpoint for relative axial engagement motion. The spring sweep can
show whether the local result responds to an assumed engagement-compliance
range. With unilateral opening, clearances, and changing contact there is no
general monotonic ordering of all displacements, member forces, or contact
actions. Added axial restraint can change which face opens and which bolt
carries load. Neither endpoint nor the chosen finite sweep is a conservative
whole-joint stiffness or demand bound.

These branches omit thread backlash, turn-by-turn load sharing, flank
compliance derived from geometry, root/crest contact, helix, nut rotation and
lead coupling, friction, torque, preload, and thread stripping. The separate
radial root/bore pair still has its declared gap and carries normal force only
after closure. An axial-only law supplies no transverse or rotational thread
reaction. If a signed case depends on an omitted action or leaves an internal
mechanism, retain the case as `FREE_MODE_PRESENT` or
`UNRESOLVED_AXIAL_ENGAGEMENT`; do not add constraints to force convergence.

## Minimal calculation and proof obligations

1. Bind the exact three WJ24 wood IDs, four axis IDs, source hashes, ordered
   receiver pairs, axes, current candidate revision, washer/nut geometry, and
   contact datums. No geometry hash from a prior WJ24 or WJ04 revision may be
   silently reused.
2. For every modeled axis, declare the assumed engagement length/profile,
   material scenario, nut rigidity, initial slack, preload, and law choice.
   For finite parametric springs, store `E_ref`, each `L_j/A_j`, `K_b,ref`,
   each dimensionless ratio, units, and emitted connector law. Keep WJ04
   fastener evidence out of the WJ24 product fields.
3. Before the patch, check one deformable straight bolt, rigid finite nut, and
   each selected connector mapping. For a uniform body, compare the bolt
   extension with `δ = F L/(E A)`; for the exact stepped profile compare with
   `δ = F Σ_j L_j/(E A_j)`. Check the spring's sign in tension and compression,
   equal/opposite action, work/energy, and absence of transverse force and
   moment. For the stiff-limit row, verify common rigid translation and all
   three common rigid rotations produce zero row residual and no spurious
   couple. This is an implementation/member check, not a thread coupon.
4. Run the WJ24 local signed response cases with the no-slip endpoint and the
   declared finite spring sweep as separate model branches. Keep the actual
   source-bound wood/contact/material/restraint assumptions frozen. Check
   whether outputs converge toward the stiff endpoint as the parameter rises;
   extend the numerical sweep if they do not. Retain singular, open-contact,
   and failed cases rather than choosing a favorable branch.
5. Report each interface's six signed relative motions, bolt section forces,
   nut/washer and wood contact resultants, spring or MPC ownership, assumed
   overlap, and force/moment residuals at fixed datums. Label all outputs
   `WJ24_THREAD_ENGAGEMENT_SENSITIVITY_ONLY` until product-specific evidence
   supports a physical engagement law.

The response path does not require a thread coupon before these bounded
diagnostics. It does require a one-time solver/member and connector mapping
check before use. A same-product test, directly applicable validated test, or
other adequate product-specific evidence is still required before replacing
the parametric branch with a delivered-hardware stiffness law.

## Capacity stays separate

An elastic stiffness result gives deformation and internal-force distribution
for its declared model state. It supplies no bolt, nut, thread, washer, or
timber resistance. Product grade, proof/yield strength, threaded-section area,
thread stripping, nut proof, washer steel, and complete-joint capacity each
need their own applicable evidence and method. The WJ04
[bolt-resistance basis](bolt-resistance-basis.md) is historical and cannot
populate WJ24 inputs. A no-slip or parametric-spring result cannot close any
capacity check, even if response is insensitive to the chosen elastic-steel
reference.
