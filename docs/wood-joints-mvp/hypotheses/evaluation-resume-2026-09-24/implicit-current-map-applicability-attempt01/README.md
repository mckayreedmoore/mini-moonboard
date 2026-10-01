# Implicit current nut-map applicability review

Date: 2026-09-27. Read-only source and input audit. No input, geometry, or
solver source was changed; no build or native run was performed for this
review.

## Finding

The passing 100-state C3D10 translation fixture validates its tested uniform
translation mass row sum and dependent-load transformation. It does not
validate the current A09 nut map's six-degree-of-freedom offset/rotation
terms. The current map has a useful algebraic rigid-motion audit, but its
native reduced-mass path under a nonzero rotational mode remains untested.
The current A09 `response_n_plus.inp` is a static response deck, while the
current mesh record explicitly has `native_solve_run=false`; there is no
current-map dynamic history to transfer into this finding.

The current map has six weighted-fit equations per nut, with six independent
translation/rotation controls and six dependent bolt-shaft DOFs. The four
equation groups contain 754, 775, 763, and 778 terms per row. The map report
records rank six and affine rigid-motion reproduction residuals below
`4.92e-15` for all four axes. Its rotation controls encode infinitesimal
`theta` in radians; the report explicitly excludes exact large-rotation and
physical-thread claims.

The four nut C3D10 NSETs are separately tied to their corresponding
REF/ROT controls by `*RIGID BODY`. I parsed those NSET memberships against the
24 current dependent shaft DOFs in the parent incidence audit: no dependent
shaft DOF lies on a rigid-carrier node. The carrier sets contain 1,107, 1,101,
1,160, and 1,156 nodes (4,524 total), and each set exactly covers the nodes
of its nut C3D10 element set. This avoids a direct duplicate dependent DOF in
the current ordering. It does not validate the assembled dynamic map.

The source's mass retention across iterations does not introduce another
positive-mass map dependency here. The current shaft-fit equations are linear
with fixed coefficients; nonlinear RIGID coefficient updates are confined
to the zero-density carrier nodes. Since their element mass matrix is exactly
zero and their DOFs do not overlap the 24 dependent shaft DOFs, those updates
cannot change the positive-mass shaft reduction through a carrier mass
contribution. The remaining applicability limit is geometric: the fit is
infinitesimal while `*RIGID BODY` supports finite rotation. A useful known
answer should quantify and keep that difference very small.

## What the zero-density carriers do

The current materials assign the four nut ELSETs `NUT_ZERO_MASS_RIGID_CARRIER`
with density exactly zero and elastic modulus 200000 (`materials.inp` lines
41–49). The metal bolt/shaft uses density `7.85e-9` and a solid-section
assignment (`materials.inp` lines 5–6 and 25). The rigid-body input ties every
listed carrier node to its REF/ROT pair. In pinned CalculiX 2.23,
`rigidbodys.f` generates the NSET's nodal constraints, and `rigidmpc.f` labels
them `RIGID`, with each carrier-node translation expressed using the
reference translation and rotation controls. `e_c3d.f` forms the implicit
C3D10 mass entries as `rho * N_i * N_j * weight`; with `rho=0`, every carrier
mass entry is zero. `mafillsm.f` applies the MPC coefficients when assembling
element mass. A linear reduction cannot create inertia from that zero matrix.

The comments at `materials.inp` lines 37–40 say these nut sets have no elastic
section, but the actual `*SOLID SECTION` cards at lines 46–49 assign all four
sets. The input cards are the active definition: these are zero-density,
elastic C3D10 elements constrained as rigid carriers, not element-free control
sets.

Thus the carrier nodes have no independent inertia, and the zero-density nut
elements contribute no translational or rotational inertia to their control
nodes. The control pair may still acquire reduced inertia from the positive-
density bolt/shaft solids through the current nut-fit equations. The nut
elements retain elastic stiffness in the input, but compatible rigid-body
motion has no strain; this source observation does not prove a stable or
accepted response for a complete joint. `*RIGID BODY` also implies geometric
nonlinearity, so any comparison with the map's infinitesimal rotation should
use a sufficiently small angle.

## Smallest useful remaining known answer

First test one representative axis, `M00_A00` / `M03_A00`, using its actual
six physical-pivot equation rows and actual zero-density rigid carrier. Keep
the positive-density C3D10 bolt-head/shaft body for that axis, its nut C3D10
carrier, the original pivot controls, and the current equations. Omit the
other bodies and all contact, wood, preload, and joint-strength claims. This
is a reduced method fixture, not an A09 response analysis.

Use a free small rotation about the axis-0 pivot's global Y axis. The current
reference/rotation controls share the pivot
`(134.5, 1.178456090256, 410.856889078727) mm`. One actual dependent node,
61518, is at `(134.67849377443846, 3.6038812275776877,
408.8157867374458) mm`; its pivot offset is
`(0.17849377443846, 2.4254251373217, -2.0411023412812) mm`. A positive
`theta_y` must therefore produce nonzero dependent `U1` and `U3`:
`U1 = theta_y * (-2.0411023412812 mm)` and
`U3 = theta_y * (-0.17849377443846 mm)` to first order. This directly exercises
the offset and two dependent components that the translation check leaves
untouched.

Apply the same physical nodal load vector to the direct physical-node and
current-map cases, calculated as `f(t) = M a(t)` for the positive-density
C3D10 bolt/shaft nodes. Set `a_i(t) = alpha_y(t) * e_y x (x_i - x_pivot)`.
Derive `M` and the discrete reference from the pinned 2.23 C3D10 quadrature,
not the continuum-exact arbitrary-mode mass: `e_c3d.f` uses a four-point
tetrahedral rule for this element, which underintegrates arbitrary quadratic
mass modes. A linear ramp `alpha_y(t) = c*t`, with `c` chosen for a final
rotation near `1e-6 rad`, gives zero initial acceleration and keeps the
finite-rotation difference below the intended first-order oracle. Compare
every physical-node U/V state and kinetic energy to that discrete rigid-mode
reference. Do not use a generalized load only at the controller; that would
skip the physical-load reduction being tested.

For a concrete scale, the hashed M00 C3D10 body has 5,490 elements and 11,348
nodes; its farthest node is 135.3563 mm from this pivot. With 100 increments
of `dt=0.001 s`, choose `c=0.006 rad/s^3`; the zero-initial-acceleration
Newmark reference reaches `theta_y=1.00005e-6 rad` and
`theta_dot_y=3.00005e-5 rad/s` at `0.1 s`. The omitted finite-rotation
position term is bounded by approximately
`0.5 * theta^2 * r_max = 6.8e-11 mm`; the terminal centripetal acceleration
is about `1.50e-6` of the tangential angular-acceleration term. Together,
these effects are about `2e-6` of the nonzero rotational response at this
amplitude. A preliminary tolerance of `5e-6` relative for nonzero rotational
U/V and kinetic-energy values leaves a small margin for the source's
finite-RIGID/infinitesimal-fit difference. Treat this as a fixture proposal
for parent review alongside DAT precision, not a source-derived solver-error
bound. This small-angle allowance cannot support larger-rotation claims.

Include three cases in this first-axis check: direct free physical nodes;
current pivot equations plus the zero-density carrier and its rigid-body
card; and the same current pivot equations without the carrier. Require the
current-map physical U/V and kinetic energy to match the independent reference
and direct case, and require adding the carrier to leave those quantities
unchanged. Separately check that the carrier follows its REF/ROT rigid motion
while adding no mass or kinetic energy. Use DAT for precision-sensitive
values; FRD may serve state/time coverage. C3D10 mass underintegration means
this test qualifies the chosen rigid mode only, not arbitrary quadratic
inertia modes.

That first-axis fixture would establish a bounded offset/rotation and
zero-density-carrier result for one actual coefficient set. The four axes
have distinct coefficients, so a claim covering the complete A09 map still
needs the same mode check for the remaining three sets, or one reduced run
that independently excites all four actual map/carrier pairs. Even that
would establish only the small-rotation kinematic map and its implicit
inertia transformation. It would not qualify thread engagement, contact,
joint load path, resistance, or the complete A09 response.

## Evidence pins

The A09 source inputs inspected are:

| Artifact | SHA-256 |
|---|---|
| `ordinary-port-motion-attempt09-common-map/nut-coupling.inp` | `af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903` |
| `ordinary-port-motion-attempt09-common-map/nut-coupling.json` | `568ade2437181bc8e9398f64a2818bbf8bd3f46a64dae9639bf363cb68bec960` |
| `ordinary-port-motion-attempt09-common-map/rigid-carriers.inp` | `a15eebb0537a4a3f096531f2c4e48ecd26b6ec53908d61178ead7dfe3bc27815` |
| `ordinary-port-motion-attempt09-common-map/materials.inp` | `e0063d0ebc2232b6699f020488944617b1f44f7bfa38f931f47907d08202a3bb` |
| `ordinary-port-motion-attempt09-common-map/mesh.inp` | `117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803` |
| `ordinary-port-motion-attempt09-common-map/mesh.json` | `1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07` |
| `ordinary-port-motion-attempt09-common-map/response_n_plus.inp` | `57c59a8d84694d74c2dd7b0de559e425d5d28ea81453addb68fece4d682f8720` |
| `explicit-current-coupling-feasibility-attempt01/parent-dependency-audit.json` | `842737f5141d850c1ed5846f91808377111900d9204075265c7ae92d5f85cbf9` |
| `fea/wood_joint_current_nut_pivot.py` | `e03c53c5d679c7758a984591aa71ed39b1630bf7f784e0c7465e93d3cf3da370` |
| original controller-first `ordinary-nut-coupling-attempt02/nut-coupling.inp` | `afd1211978cda9eb5d46bdbac5b723f2c8ada727ed2f6666c3ccedcdd58992e7` |
| original controller-first `ordinary-nut-coupling-attempt02/nut-coupling.json` | `21c36e4f6a06f8c90cd4decbba794790d28eb88428adfdc71266b9993f694009` |
| implicit C3D10 translation `implicit-c3d10-mpc-known-answer-attempt01/verifier.json` | `13fca5e2c9d823f95a8758de437b54e8e416482455130f20dec335e577050d2e` |
| implicit C3D10 translation `implicit-c3d10-mpc-known-answer-attempt01/input-freeze.json` | `b9e74647a23fbf5e458c0d2873eb491a0428c5bbae341ce72ff25f399db8036c` |
| implicit C3D10 translation `implicit-c3d10-mpc-known-answer-attempt01/output/execution.json` | `918d43a5a6da7591f2b724004596ed7393eec11846725cd4d90359b8b8afbcec` |

The pinned CalculiX 2.23 source archive is
`ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2`,
SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
Relevant member pins and line ranges:

- `e_c3d.f`, SHA-256
  `d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc`, lines
  986–1005: implicit C3D10 consistent mass integration multiplies the shape
  functions by density and quadrature weight.
- `gauss.f`, SHA-256
  `aed2d48b6a63e30894e747a531f6edc32e3cd921338e370902dfb62d8e304df2`, lines
  17 and 142–147: `gauss3d5` is the four-point tetrahedral rule used by the
  C3D10 integration path.
- `mafillsm.f`, SHA-256
  `d6073d5bfd9ad56a03a25b8c79ad1bb2dd178e48e3db3b9dd951f612b0197602`, lines
  386–430: mass assembly accounts for dependent MPC terms and their
  coefficients.
- `nonlingeo.c`, SHA-256
  `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f`, lines
  929–950 and 1458–1462: implicit dynamics updates nonlinear MPCs before
  matrix assembly and retains the assembled mass matrix for later iterations;
  this is non-blocking here because only zero-density carrier DOFs have
  changing RIGID coefficients.
- `rigidbodys.f`, SHA-256
  `53c44c6aeb6cc08912ad9538cf592957ea13c44ba1bbe407a4adb94ee12d68ea`, lines
  58–65 and 313–338: rigid bodies imply geometric nonlinearity and an NSET
  generates node constraints.
- `rigidmpc.f`, SHA-256
  `3156cf6eaf43fd6b7a945a8dfae3b47ac49c550892be4ba8f81bcfa7e6c5ab8e`, lines
  19–24 and 63–107: each constrained carrier node uses `RIGID` equations
  involving the REF and ROT controls.

The passing translation `verifier.json` and `input-freeze.json` are immutable
result/freeze pins. That packet's declared scope explicitly excludes current
pivot offsets, rotation, and zero-density carrier behavior.
