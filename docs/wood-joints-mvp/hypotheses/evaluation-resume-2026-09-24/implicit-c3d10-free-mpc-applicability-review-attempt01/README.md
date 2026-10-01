# Implicit C3D10 free-MPC inertia applicability review

Date: 2026-09-27. This is a read-only, source-bound applicability review. No
native job, build, or fixture preparation was performed.

## Finding

The existing evidence does **not** qualify pinned CalculiX 2.23 implicit
free/homogeneous-MPC inertia for the current C3D10 physical-pivot constraints.
It does contain a passing 2.23 dynamic free homogeneous-controller test for a
specific C3D8 average-face equation. That is useful evidence for that C3D8
pattern, not a transfer to quadratic C3D10 mass or the nut's physical-pivot
map.

The distinction matters because the existing C3D8 port coupon tests a single
generic average equation, `u2+u3+u6+u7-4*q9=0`. It does not map every solid
node through the current physical-pivot constraint coefficients. The
prescribed-average-motion dynamic case fails on C3D8, while the separate
force-driven free-controller C3D8 case passes. These are different loading
paths; the former is not evidence that all free MPCs fail, and the latter does
not verify the current C3D10 map.

## Existing evidence inspected

- [`port-reaction-known-answer-attempt01`](../port-reaction-known-answer-attempt01/README.md)
  originally ran with CalculiX 2.21. Its dynamic prescribed average-MPC C3D8
  result differs from the full-inertia reference by `0.00560773 mm`; an
  independent reference omitting prescribed-motion inertia matches to
  `4.96723e-9 mm`. The record explicitly limits the mesh/audit to C3D8.
- [`calculix-2.23-upgrade-attempt01`](../calculix-2.23-upgrade-attempt01/README.md)
  reruns the unchanged C3D8 fixtures with the unmodified upstream 2.23 source.
  The prescribed-MPC result is unchanged. Its separate dynamic
  [`force_mpc.inp`](../calculix-2.23-upgrade-attempt01/force/force_mpc.inp)
  uses the same average-face equation, leaves `q9` free, and applies the
  generalized force there. It passes against direct balanced nodal forces:
  maximum displacement error `4.98731e-10 mm`, and applied-work minus elastic
  plus kinetic energy `1.47240e-12 N mm` over 100 increments. That is a narrow
  C3D8 free-coordinate pass, not a C3D10 or physical-pivot pass.

The evidence records pin these artifacts: port `RESULTS.md` SHA-256
`3b244cee7e3d39cefbe5215f053ea7214701dcafa2fde8951d2861561ed18c75`, port
`input-freeze.json` `b0d897b70a3f6849d38b7796e2c68f2d86de3a52af65847d4290d8231c878fa8`,
2.23 `build_manifest.json` `496efd407abd71c8ced12e3631ea2d223dee1fe6ec1b1b757a2e5e28dfb19e66`,
2.23 `force_mpc.inp` `abbf0e83d71e6548ef408dc8588e757d15ea2a5660c26ea0ba7f9aa54eea70d2`,
and `force_mpc-execution.json`
`f5ae935aa4099850fd195aacf92e4ac6b89caa9efdc616cfcfd46a8f18fbeeae`. The
2.23 README pins the separate executable SHA-256
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`.

## Pinned 2.23 mass path

The inspected source is the exact upstream archive SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`, also
pinned in the 2.23 build manifest.

- `e_c3d.f`, SHA-256
  `d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc`,
  recognizes the ten-node C3D10 topology (`nope=10`, lines 146–149). For
  implicit mass it integrates `rho*N_i*N_j` into the element matrix `sm`
  (lines 986–1005), rather than the explicit-only mass-lumping sum. This is a
  consistent quadratic-element mass path.
- `mafillsm.f`, SHA-256
  `d6073d5bfd9ad56a03a25b8c79ad1bb2dd178e48e3db3b9dd951f612b0197602`, calls
  `e_c3d` for the element mass (lines 285–300), reads the mass entries and
  passes them through `mafillsmmatrix` (338–355), and applies MPC coefficients
  while assembling dependent terms (406–430). `mafillsmmatrix.f` is pinned at
  `5790af603df9ba61699bb67aa6552d6e89057202dd0c3b50637cf478ec4899a3`.
- `nonlingeo.c`, SHA-256
  `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f`, enables
  mass for implicit dynamics (`nmethod==4`, lines 810–813) and calls the
  assembled residual path. `calcresidual.c`, SHA-256
  `9f8b0528c2b7853df4b779d142808c74115318e315979dda2b0f3bef1e3af1a7`, forms
  the implicit acceleration vector from active independent DOFs (`nactdof>0`,
  lines 56–76) before multiplying by the reduced mass matrix. The source shows
  a generic reduced-mass route; it does not replace an element-and-constraint
  known-answer test.
- `gauss.f`, SHA-256
  `aed2d48b6a63e30894e747a531f6edc32e3cd921338e370902dfb62d8e304df2`,
  provides the pinned tetrahedral quadrature used by the element routines.

The prescribed-motion C3D8 result concerns how dependent prescribed
acceleration enters the implicit residual. It is not a test of a free
homogeneous coordinate whose mass has been reduced through MPCs. Conversely,
the passing C3D8 free-controller result does not establish the C3D10 shape
integration or the current nut pivot's coefficient/offset map. C3D10 contact
diagnostics and explicit runs do not close this gap.

## Smallest useful C3D10 known answer

Add a C3D10 version of the existing coordinate-invariance comparison using
one straight-sided tetrahedron, positive density, no contact, and zero initial
velocity. In both decks keep all ten physical U1 DOFs active and constrain
physical U2/U3 to zero. The direct deck has the ten physical U1 coordinates.
In the mapped deck use the single homogeneous equation
`u1+u2+u3+u4-4*q=0`, with physical corner node 1 U1 dependent, and free `q`;
the other nine physical U1 DOFs remain independent. This is an invertible
coordinate change like the existing average-face fixture, not a rigid tie of
all ten nodes to one pivot. Apply the identical physical nodal load vector in
both decks, including its dependent-node force, so the test also exercises
load transformation through the MPC. Compare all physical-node U/V values
and kinetic energy over the same implicit increments.

For a unit-acceleration target `a` and tetra volume `V`, the direct consistent
mass reference is `f=M*1*a`, or `f_i=rho*a*integral(N_i dV)`. With standard
quadratic tetrahedral shape functions, the four corner loads are each
`-rho*V*a/20`, and the six midside loads are each `+rho*V*a/5`; their sum is
`rho*V*a`. Use those same ten nodal loads in both coordinates rather than
replacing them with a generalized force at `q`; the latter would not test the
dependent-node load transformation. These are consistent-mass row-sum weights,
not positive diagonal/lumped mass weights. Choose a load history whose initial
acceleration is known (for example, zero load at t=0 with a documented
incremental ramp), and compute the expected states with the pinned implicit
Newmark recurrence using those force values. Check the first increment
explicitly. Do not assume the continuous constant-acceleration formula
`u=0.5*a*t^2` unless the 2.23 startup establishes `a0=a`; when that initial
acceleration is verified, also check `v=a*t`, kinetic energy
`0.5*rho*V*v^2`, and zero elastic energy. Compare mapped and direct motion as
well as the independent discrete answer; do not use `RF` alone as the inertia
oracle.

This translation case would qualify only that C3D10 free average-coordinate
mass and load mapping. If the current physical-pivot relation carries angular
or eccentric-offset terms, the known answer must include those same
coefficients and a rotational/offset mode before claiming the full pivot map
is exercised. Keep the fixture separate from contact and joint acceptance.
This is a future method gate and does not block the current small
output-validation coupons.
