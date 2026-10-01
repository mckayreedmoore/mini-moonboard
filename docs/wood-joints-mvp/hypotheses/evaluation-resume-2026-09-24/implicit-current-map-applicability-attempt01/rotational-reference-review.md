# Rotational current-map reference review

Date: 2026-09-27. Read-only assessment of the proposed one-axis current-map
known answer. I did not change the terminal README, inputs, geometry, or solver
source, and performed no build or native run.

## Finding

A physical-load rotational fixture can use a defensible **linearized discrete
Newmark reference**, but it is not an exact trajectory of the finite-rotation
`NLGEOM` model. The proposed `f(t)=M a(t)` load is fixed from reference
coordinates and omits the rotating tangent direction and centripetal
acceleration of a finite rigid rotation. The current 5e-6 relative threshold
therefore has limited margin at the proposed amplitude. The primary mapping
test should be direct-versus-mapped physical-node parity under the same loads;
the analytic linearized answer should be a separate oracle with an explicit
finite-rotation allowance.

One numerical value in the terminal README's proposal needs correction before
it becomes an expected answer: for `alpha_y(t)=c*t`, zero initial acceleration,
and average-acceleration Newmark, the terminal angular velocity is
`0.5*c*T^2 = 3.00000e-5 rad/s`, not `3.00005e-5 rad/s`. The stated discrete
angular displacement `1.00005e-6 rad` is consistent with Newmark.

## Discrete reference

Let `d_i = e_y × (x_i - p)` for each positive-density bolt/shaft node, and
construct the assembled consistent mass matrix `M` from the pinned C3D10
quadrature. Apply the physical load vector `f(t_n)=M*(c*t_n*d)` to every
physical node. This uses the same discrete mass matrix that the solver
assembles, including its four-point tetrahedral integration; a continuum
inertia tensor or a lumped approximation is not interchangeable here.

For the free rigid coordinate under this compatible load, the alpha-zero
Newmark values at `t_n=n*dt` are

```text
alpha_n = c*t_n
omega_n = omega_(n-1) + dt/2*(alpha_(n-1)+alpha_n)
        = c*t_n^2/2
theta_n = theta_(n-1) + dt*omega_(n-1)
          + dt^2/4*(alpha_(n-1)+alpha_n)
        = c*(t_n^3/6 + t_n*dt^2/12)
U_i,n = theta_n*d_i
V_i,n = omega_n*d_i
ELKE_n = 0.5*omega_n^2*(d^T*M*d)
```

The pinned `nonlingeo.c` derives `beta=1/4` and `gamma=1/2` when `alpha=0`
(lines 904–907). With `dt=0.001 s`, `T=0.1 s`, and the proposed
`c=0.006 rad/s^3`, the discrete endpoint is `theta=1.00005e-6 rad`,
`omega=3.00000e-5 rad/s`, and `alpha=6.00000e-4 rad/s^2`. The `5e-11 rad`
displacement correction from the continuous integral is 50 ppm relative to
the continuous result, so an analytic continuous-time `theta(T)=c*T^3/6`
oracle would fail the stated 5 ppm tolerance. Use the discrete recurrence at
every output state.

The current source computes implicit C3D10 mass from shape-function products,
density, and quadrature weight in `e_c3d.f` (lines 986–1005); `gauss.f`
supplies the four `gauss3d5` tetrahedral points (lines 142–147). The
underintegrated matrix is still a valid discrete reference if the load vector
is formed as that same matrix times the nodal rigid-mode acceleration. The
mass assembly transforms terms through MPC coefficients in `mafillsm.f`
(lines 386–430). Thus the intended comparison is algebraically well-posed in
the linearized model: `T^T f = T^T M T qdd` when the sampled rigid field is
represented by the actual map `T`.

The carrier is a distinct, finite-rotation path: pinned `rigidmpc.f` forms
`RIGID` constraints from the REF/ROT controls and current orientation terms
(lines 78–107). The shaft fit rows remain fixed linear `*EQUATION` rows. The
carrier check should therefore compare carrier fiducials to an exact single-
axis rotation, while shaft nodes use the first-order field above.

I checked the rotation-control parameterization in pinned `nonlinmpc.f` rather
than assuming an Euler convention. The RIGID branch reads the three current
ROT-node DOFs into `w(1:3)`, takes `ww=|w|`, and constructs the rotation matrix
with `cos(ww)`, `sin(ww)/ww`, and `(1-cos(ww))/ww^2` (lines 94–120; repeated
when creating new knots at 264–288). This is a total axis-angle rotation
vector: its norm is the angle, not three Euler angles or an incremental
rotation. With only global `w_y=theta` nonzero, Rodrigues reduces exactly to
`R_y(theta)`, with first-order displacement `(+theta*z, 0, -theta*x)` about
the pivot. The README's single-axis carrier formula is therefore the correct
parameterization for this case.

## Finite-rotation and tolerance boundary

At the README's `r_max=135.3563 mm` and `theta≈1.00005e-6 rad`, the omitted
second-order finite-position term is about `6.77e-11 mm`, or `5.00e-7` of the
first-order rotational displacement. The fixed reference-direction load also
omits a radial acceleration from the rotating tangent term of approximately
`alpha*theta*r`; the centripetal term is `omega^2*r`. At the endpoint their
ratios to tangential acceleration are about `1.00e-6` and `1.50e-6`,
respectively. Their combined scale is roughly `2.50e-6` of the tangential
acceleration. These are scale estimates, not a bound on elastic high-frequency
response in the full finite-element model. Exact finite-rotation loading
would require the state-dependent acceleration
`alpha × (R(theta) r) + omega × (omega × (R(theta) r))`, not the proposed
fixed `M*(alpha × r)` nodal force.

The recorded DAT format has seven significant digits (`*.E` values such as
`2.500000E-10` in the passing translation fixture), giving about `5e-7`
relative half-unit rounding for nonzero tokens. A 5e-6 tolerance is therefore
above print resolution, but at the proposed amplitude it is only about twice
the estimated omitted finite-rotation acceleration scale, before other
nonlinear response. It is a provisional threshold, not a source-guaranteed
error bound. A useful margin is to reduce the target angle by about fivefold
(`c≈0.0012 rad/s^3` at the same step and duration). The discrete endpoint then
has `theta≈2.0001e-7 rad`, `omega=6.0e-6 rad/s`; the maximum first-order nodal
signal remains about `2.71e-5 mm`, well above DAT rounding, while the estimated
nonlinear acceleration scale falls to about `5.0e-7`. The first-order oracle
and all tolerances must still be evaluated from printed-token resolution.
Use componentwise absolute floors derived from the printed token precision
where the expected vector component is zero or close to zero; relative-only
gates are undefined for those components. For a direct-versus-mapped comparison,
account for one rounding unit from each record rather than assuming their
printing errors cancel.

The three-case arrangement is useful if all six reference/rotation controls
remain free: direct physical body, current equations without the carrier, and
current equations with the zero-density carrier. The compatible load makes
the reference-point acceleration zero while allowing the body's center of
mass to move. Pinning reference translations would be compatible only if the
projected load and mass coupling are exact; it narrows the scope and can hide
errors in those translation-map terms, so it should not be part of the primary
six-coordinate comparison. Compare direct and mapped physical `U/V` histories
under identical loads as the primary mapping test. Check the linearized
Newmark field separately, and check the rigid carrier against its finite
rotation matrix at a few carrier fiducials. Do not compare carrier coordinates
to the infinitesimal shaft field beyond the stated small-angle allowance.
`ELKE` and body mass are useful scalar checks, but cannot replace directional
`U/V` because an incorrect axis or sign can preserve kinetic energy.

The current A00 six equation rows mention 251 physical nodes and the two
reference/rotation controls. Writing U/V for all 11,348 positive-density-body
nodes for 100 states in both DAT and FRD would be on the order of hundreds of
megabytes, far beyond the 16 MiB-per-case cap used by nearby method fixtures.
For a bounded test, output the union of nodes in the six actual equation rows
(all 251 physical terms plus controls in DAT), the carrier controls and a few
carrier fiducials, and total body `ELKE/EMAS/EVOL/ELSE`. That captures the
equation support without a full-body field dump; enforce an output cap in the
future runner.

A 5e-6 threshold only detects map errors larger than that threshold plus the
finite-response and output-rounding budget. It cannot prove that every
sub-threshold coefficient error is absent. Before native use, an offline
negative control should perturb a rotational coefficient enough to create a
known, e.g. 1e-4 relative, physical-field error and demonstrate that the
verifier rejects it. Hashing the actual map input remains necessary. The
fixture would still qualify only one axis and one small rotational mode, not
the four-axis current map, finite rotations, contact/thread behavior, or joint
capacity.

## Evidence pins

| Evidence | SHA-256 |
|---|---|
| Current `nut-coupling.inp` | `af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903` |
| Current `rigid-carriers.inp` | `a15eebb0537a4a3f096531f2c4e48ecd26b6ec53908d61178ead7dfe3bc27815` |
| Current `materials.inp` | `e0063d0ebc2232b6699f020488944617b1f44f7bfa38f931f47907d08202a3bb` |
| Current `mesh.inp` | `117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803` |
| Pinned CalculiX 2.23 source archive | `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7` |
| `e_c3d.f` | `d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc` |
| `gauss.f` | `aed2d48b6a63e30894e747a531f6edc32e3cd921338e370902dfb62d8e304df2` |
| `mafillsm.f` | `d6073d5bfd9ad56a03a25b8c79ad1bb2dd178e48e3db3b9dd951f612b0197602` |
| `nonlingeo.c` | `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f` |
| `nonlinmpc.f` | `a9331e1895c9bcea10c405bb05f75788f4d3a6b45022e54e6a338b69850f4036` |
| `rigidmpc.f` | `3156cf6eaf43fd6b7a945a8dfae3b47ac49c550892be4ba8f81bcfa7e6c5ab8e` |
| Passing C3D10 translation DAT example | `cf7dc4fbf6e88cbddd7b3799c32ed35d7962a650a9307046673062330549b5b6` |
