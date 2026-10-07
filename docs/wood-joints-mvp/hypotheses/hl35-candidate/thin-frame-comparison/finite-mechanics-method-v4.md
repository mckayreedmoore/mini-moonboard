# Objective finite mechanical adapter

The new [mechanical adapter](../../../../../scripts/thin_bolted_finite_mechanics.py)
provides objective timber/shaft element energies, objective condensed fitting
energies, and exact interpolated point/director jets over an existing assembly.
Its [27 small fixtures](../../../../../tests/test_thin_bolted_finite_mechanics.py)
and Ruff pass. The [method certificate](finite-mechanics-method-v4.json) retains
the failed finite shaft material-roll gauge explicitly. No current candidate
assembly, whole-case response, CAD rebuild or native run was performed.

`FiniteMechanicsAdapter(assembly, common_system, source_sha256=pins)` reads the
existing timber element blocks, fitting condensed matrices and common-shaft
stations. It does not mutate their indices, matrices or source objects. The
reviewed model supplies 20 timber members, 36 fittings and 70 shaft bodies; the
small certificate uses one member, one fitting and one two-element shaft.
Panel energy and panel ports belong to the separate finite panel adapter.

Existing timber/fitting coordinates remain world
`q=(u_mm,1000*theta_rotation_vector)`. Shaft coordinates remain in each shaft's
frozen proper basis, whose columns map local vectors to world. One omitted
first-node twist coordinate is appended for each shaft, preserving every old
index and allowing finite rigid rotations to be represented. `prolong_state`
appends zeros as an initial guess. It does not select a finite gauge.

`response(q,tangent=True)` returns `energy_nmm`, `gradient_n` and `hessian_csr`
for mechanical elasticity. The frozen corotational beam primitive and its
local Timoshenko stiffness are reused. Timber/shaft segment refinement remains
a discretization choice. At an interior material station `t`, the center
interpolates current nodal centers linearly and the material rotation is

```text
R(t) = R0 Exp(t Log(R0.T R1))
x(t,p) = (1-t)*(c0+u0) + t*(c1+u1) + R(t)*(p-((1-t)*c0+t*c1))
```

The spatial angular Jacobian differentiates this relative-rotation
interpolation, including the exponential-map Jacobians. It preserves both
common rigid motion and a superposed world rotation of a deformed state.
[SO(3) exp/log and work transformations](https://arxiv.org/pdf/1812.01537)
support these conventions. Relative-rotation interpolation also follows the
construction in [Meier et al., Appendix A.4](https://arxiv.org/pdf/1611.06436).

`port(body,point,q,flange=None,tangent=True)` returns `position_xyz_mm`,
`J_csr` and three `H_xyz_csr` matrices, plus compact support indices and local
jets. `director(body,point,q,reference_vector,flange=None,tangent=True)`
returns `current_vector_xyz` with the same derivative fields. A unit material
vector retains unit length. Fitting directors require a specific flange;
their material direction is not inferred from an averaged pair of flanges.
The floor port and director stay fixed. Caller-owned normal signs and material
ownership remain explicit.

Point force work uses `J.T@F`. Rotation-coordinate duals require the SO(3)
Jacobian to recover physical spatial moments; they are not generally physical
moments divided by 1000. The port Jacobian is analytic. Port Hessians and
element/fitting tangents use local central derivatives at `1e-3` coordinate
mm, corresponding to `1e-6` rad for a rotation coordinate. No hidden
symmetrization or whole-assembly differencing is applied. `tangent=False`
omits Hessians. Near-pi global charts and 90° neighboring/fitting relative
director turns raise errors rather than being clamped.

Each fitting reuses its frozen two-flange condensed strip matrix. Its first
flange pose serves as a moving coordinate anchor. The relative translational
deformation is `R0.T*(x1-x0)-(p1-p0)` and its relative rotation is
`Log(R0.T*R1)`. Their unchanged quadratic matrix supplies energy; both flange
states remain free. The adapter rejects a matrix whose rigid modes are
clamped. This construction recovers the original reference matrix and gives
zero energy under finite common rigid motion of the non-collinear L-strip
geometry. Actual bend/heel/hole compliance and connector stiffness remain
unqualified.

The synthetic combined reference matrix differs from the frozen linear
matrix by 2.58e-10 in relative Frobenius norm. At 20° and 73° rigid motion,
maximum energy is 1.20e-22 N·mm and maximum point error is 7.14e-14 mm. The
deformed energy changes by 3.24e-14 relative under superposed rotation.
Directional gradient/tangent errors are 4.55e-10 and 2.77e-10. Internal world
force and moment balance residuals are 2.28e-11 N and 5.28e-9 N·mm. The largest
point/director J and H directional errors are 7.96e-11 and 4.58e-9. Separate
fixtures check deformed interior-port/director covariance and force-dual work
under an arbitrary 20° world rotation, with nonzero relative nodal rotations.

The distinct two-element circular test fails exact common material-roll
invariance. Its initial energy is 2,068,966.517 N·mm; the common right-roll
generator performs −166.643 N·mm/rad of internal coordinate work. A 20° roll
changes energy by −1.819e-5 relative. This is a proxy-method result, not a
candidate bolt torque. It establishes neither an exact finite unloaded twist
nullspace nor permission to reuse the fixed first-component linear gauge.
All shaft coordinates remain present, and the adapter adds zero numerical or
physical twist constraints.

The smallest follow-up method to evaluate is an isotropic, shear-deformable
Simo–Reissner shaft energy with objective relative-rotation interpolation.
Body translational and rotational strains must transform consistently under
common material roll, with equal transverse bending/shear coefficients for
the circular section. [The primary beam study](https://arxiv.org/pdf/1611.06436)
distinguishes shear-deformable rods from its more restricted torsion-free
reduction. No replacement energy or reduction is adopted here. Reference
stiffness, axial/torsion/both cantilever answers, bent common-roll null work,
objectivity, locking and refinement would need their own fixtures before
changing the shaft method or imposing a gauge.

Straight element chords also shorten a physically unstrained curved
centerline. For a 120 mm circular arc of radius 1000 mm, the expected bending
energy stays 4800 N·mm. Spurious axial energy is 215.922, 13.4988 and 0.843731
N·mm for one, two and four segments, matching exact chord shortening and
decreasing approximately 16-fold with each halving. This discloses the
arc-induced axial approximation; it does not establish a candidate-specific
local-turn or refinement pass.

The [certificate producer](../../../../../scripts/check_thin_bolted_finite_mechanics.py)
pins the four reused frozen primitives and all new code/fixtures, reuses the
small fixture factory and refuses to overwrite evidence. The adapter,
fixtures, compact certificate and method note stay active for parent-owned
integration/readiness review. Contact/load integration, continuation and
candidate equilibrium remain unexecuted. All physical release flags remain
false. No raw native output or extra manual copy was created, and no
archive/prune operation occurred.
