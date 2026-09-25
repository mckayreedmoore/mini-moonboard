# Ordinary patch rigid-motion audit

This note independently checks the algebraic rigid-motion audit in this
directory. It is a kinematic sensitivity result for the current geometry,
not a native contact tangent or an assembled-joint response.

The inputs are pinned to current contact classification SHA-256
`18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13`, current
inventory SHA-256 `70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3`,
and current 19-body mesh SHA-256
`1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07`. The
matrix checked here is SHA-256
`de205bd0b94cde0687f2ae8e666866a1cd2b0323050a89b3de4b373d2588f282`. The
inventory has three wood bodies, four physical bolts, and sixteen separate
metal bodies. The mesh is marked `VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER`;
its independent mesh audit found 807,002 positive Gauss5 determinants and no
nonpositive determinants (audit SHA-256
`fb65d21c5d5b214cfb45549384990d6543d59af8c15e672e64fba2f0d04ee525`). No
solver or contact cards are part of that audit.

The rigid-motion matrix uses three symbolic normal rows for each of the three
wood patches and sixteen metal seats, plus four assumed axial bolt-to-nut
constraints. Its 61 rows over 114 rigid-body coordinates have rank 56 and
nullity 58. Adding six coordinate gauges on the principal body gives rank 62
and nullity 52. No stiffness was added and accessory spins were not removed.
The contact classification remains `response_ready: false`.

The three rows per positive-area planar patch are an algebraic basis, not
contact integration or force samples. For rigid bodies, normal relative
displacement

`n · [(u_a + ω_a × (p - o_a)) - (u_b + ω_b × (p - o_b))]`

is affine in the two coordinates of a plane. Requiring it to vanish at three
non-collinear points therefore spans the same normal-compatibility row space
as requiring it over the patch. All 19 symbolic triplets were coplanar and
non-collinear; arbitrary affine point-row reconstruction error was at most
`2.7e-15`, with maximum plane residual `4.6e-14 mm`. Rebuilding the saved
61-row matrix from its serialized contact and axial-constraint records
reproduced it within `8.9e-16` maximum absolute entry error and gave the same
ranks.

Six scalar wood-relative observables project onto the gauged nullspace: for
both cleat and rail relative to the principal, translations along `T` and `N`
and rotation about `X`. Here `T = (0, 0.642787610, 0.766044443)`,
`N = (0, -0.766044443, 0.642787610)`, and `X` is global X. Their projected
observable matrix has rank four at tolerance `1e-8`; these six affected
observables are not six independent modes. They represent unresolved
load-path motions under the declared rows, not symmetry gauges or proof of
real-joint failure. The 16 individual metal-body axis spins are also null in
this frictionless model; they are only harmless coordinate freedoms for
responses that do not apply or require torque about those axes.

The rank assumes all nineteen planar patches are closed bilateral tangent
equalities, while radial clearances remain open and nut bores are absent.
Actual unilateral opening can remove constraints; finite clearances can
activate bearing after motion. The rank cannot establish active pressure,
force transfer, stiffness, material response, or capacity. The four axial
constraints are an assumed kinematic sensitivity, not physical thread
engagement evidence.

The smallest bounded next step is to define a reduced per-bolt seat/axial-link
idealization for one axial case, stating how its condensed relations represent
seat and bolt axial action. It may remove free washer, nut, and bolt accessory
coordinates only as an explicit model reduction, not by adding artificial
stiffness or silently pinning them. Keep the axial link as a stated stiff-limit
sensitivity and physical engagement unresolved; do not use this branch for
shear or torsion. Broader response requires a justified clearance-bearing and
engagement law, which the current solid nut placeholders do not provide.
