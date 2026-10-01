# Independent rigid-reference review

Date: 2026-09-27. Read-only math/source review of the offline rigid-limit
Newmark reference. I did not change its producer, mass data, geometry, or any
solver input, and did not build or run a native job.

## Finding

The polar/Newmark update is mathematically sound for the stated **discrete
position-constrained rigid-body problem**: fixed reference consistent mass
matrix M, zero initial state, average-acceleration Newmark, and endpoint load
f[n+1] = M (c t[n+1] W (x0-p)). It includes the body’s full anisotropic mass
distribution. It is not the exact trajectory of the fixture’s free, elastic
C3D10 body, so it is a bounded reference for the rigid limit and a secondary
check, not a stand-alone exact oracle for every native nodal result.

## Discrete derivation and implementation audit

Write the constrained nodal positions as x_i = C + R s_i, where s_i are
mass-centered reference coordinates, R is in SO(3), and
S = sum_ij M_ij s_i s_j^T. For alpha=0, the pinned solver sets beta=1/4 and
gamma=1/2. The average-acceleration Newmark predictor and acceleration are

    R_p = R_n + h V_n + (1/4) h^2 A_n
    A_(n+1) = (R_(n+1) - R_p) / (beta h^2)

Projecting M A_(n+1) = f_(n+1) onto rigid position variations is the
stationarity condition for

    Pi(R) = (x - x_p)^T M (x - x_p) / (2 beta h^2) - f_(n+1)^T x

The centroid translation separates because the centered first mass moment is
zero. The remaining orientation term is equivalent to maximizing

    trace(R^T (R_p + beta h^2 c t_(n+1) W) S)

When S is positive definite and the argument has positive determinant, its
unique proper orthogonal maximizer is the polar factor of
(R_p + beta h^2 c t_(n+1) W) S. The producer uses exactly this update, then
uses the Newmark acceleration and velocity recurrences. Its matrices V and A
are discrete affine coefficients; they should not be reinterpreted as exact
continuous angular velocity/acceleration or assumed tangent to SO(3) at
finite step size.

For the first-order single-axis limit, the same recurrence gives
omega_n = c t_n^2/2 and theta_n = c (t_n^3/6 + t_n h^2/12), with
W(x-p) = (z-p_z, 0, -(x-p_x)). The signs, time level, and centroid translation
in the producer agree with those formulas. At the terminal state the JSON
reports theta=2.01e-7 rad, omega=6.0e-5 rad/s, centroid displacement
(9.6503611e-6, 0, 2.87e-13) mm, maximum R-I-theta W coefficient difference
2.02e-14, and maximum V-omega W difference 1.19e-11 per second.

The implementation derives S from the quadrature inertia about the specified
pivot and shifts it to the mass centroid; it checks symmetry and positive
principal minors/determinant. Its scaled Newton polar iteration preserves the
polar factor, and the script checks a rational-rotation/SPD control, inverse
control, per-state orthogonality/determinant, and symmetric stationarity
matrix. Running parent-rigid-reference.py in check mode reproduced
parent-rigid-reference.json and passed those assertions. The 80-digit
arithmetic applies after loading the mass reference: geometry, quadrature
accumulation, and serialized covariance originate in binary64, so this is not
an 80-digit physical mass calculation.

The pinned 2.23 source supports the method assumptions. nonlingeo.c derives
the stated beta/gamma values at alpha zero (904-906); its initial-acceleration
path uses M + beta (t_inc/10)^2 (1+alpha) K (1260-1285). With zero initial
displacement, zero internal force, and f(0)=0, that path has zero right side
and is consistent with A_0=0. The usual Newmark predictor coefficients are
visible in prediction.c (46-47). e_c3d.f selects four integration points for
C3D10 (308-310) and assembles mass from density, shape functions, Jacobian,
and quadrature weight (988-1004); mafillsm.f transforms those matrix terms
through MPC coefficients (386-430). The mass is formed from reference co
coordinates. Thus the global reference M is fixed, while the equivalent
spatial inertia of a rotated rigid body changes as R I_C R^T. The full
S-weighted polar step retains that orientation dependence; replacing it with
only the scalar I_yy would not.

One precision qualification prevents calling the offline quadrature
bit-identical to the source rule: pinned gauss.f stores each four-point
tetrahedron weight as 0.041666666666667 (339-341), while the mass producer
uses 1/24. The source literal is about 8.0e-15 larger. Since all four source
weights share this same rounding, it uniformly rescales the assembled
mass/covariance by that amount. This is immaterial beside printed native
precision and does not change the polar orientation, but it is a quantified
source-rounding difference.

There is a second tiny input-representation difference: the mass producer
parses complete coordinate tokens from mesh.inp, while pinned nodes.f reads
only characters 1–20 of each coordinate field (140, 150, 160). An independent
token comparison finds 18 affected coordinate tokens, including five nodes
in the M00 target body and three M03 nut nodes; the maximum absolute change is
8e-18 mm at node 66508. Thus the quadrature coordinates are not textually
identical to what the native parser retains, although this measured shift is
negligible at the fixture scale. Together with the rounded source quadrature
weight, these are the limits on the word “matched,” not evidence of a
material geometry or mass change.

## Applicability and remaining bound

The actual positive-density bolt/shaft body is assigned elastic steel
properties and remains deformable. The rigid reference restricts its nodal
motion to centroid translation plus R s_i; the unconstrained elastic FE body
has additional deformation modes. At infinitesimal rotation the load pattern
M c t W(x0-p) is compatible with a rigid acceleration. At finite rotation,
the continuous rigid acceleration would contain
alpha cross (R s) plus omega cross (omega cross (R s)), whereas the applied
pattern is based on reference coordinates. At the endpoint the omitted terms
have the rough scale theta + omega^2/alpha = 2.01e-7 + 3.00e-7 = 5.01e-7
of tangential acceleration. This is a scale estimate, not an error bound for
the discrete solver or its elastic response.

The centroidal inertia eigenvalues derived from the pinned mass data are
approximately 2.7724e-4, 9.6632e-2, and 9.6632e-2 tonne mm^2, a condition
ratio of about 349. A residual torque directed along the low-inertia
principal axis can therefore produce a much larger angular response than its
unprojected force/acceleration ratio suggests. Multiplying 5.01e-7 by 349
gives only an illustrative worst-direction scale (about 1.75e-4); it is not
a predicted error or a usable gate because the actual residual torque
projection and elastic response have not been computed.

Before using the rigid path as a strict native acceptance oracle, quantify
the elastic correction under the same frozen quadrature, loads, geometry, and
MPC map. One bounded route is to form each rigid-reference step’s unbalanced
nodal residual, project it onto the deformational subspace, and solve or
bound the resulting M/(beta h^2) + K_t response with the actual constrained
operator. Otherwise, use direct-versus-mapped physical-node parity as the
primary mapping check and keep the rigid-limit comparison diagnostic with a
separately justified allowance. No elastic-discrepancy bound, native
verification, contact behavior, or joint acceptance is established here.

## Evidence pins

| Artifact | SHA-256 |
|---|---|
| parent-mass-reference.py | edc8f415a88ea10bafa1ea77b2ec37fe01a85e3773923387feb4733a1c618678 |
| parent-mass-reference.json | 317f7303fcc544ec04133bc72ce9e8768c8de4b39facb1aa14177c5ea1d4d236 |
| parent-rigid-reference.py | 2819f666d40aa094e9a302014e73730143f7b6102b1c4702d972a0a501a1ed00 |
| parent-rigid-reference.json | 16432de37ca83eba6b0b86588db10e75770089fcba66c6edf6c324c0ed2c00e1 |
| Pinned source archive | 9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7 |
| nonlingeo.c | 8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f |
| prediction.c | dfe7d10315342e7a59af6fcfb0f251f1a6f2b1c53e0f20ad402de6422c587525 |
| e_c3d.f | d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc |
| gauss.f | aed2d48b6a63e30894e747a531f6edc32e3cd921338e370902dfb62d8e304df2 |
| nodes.f | 1ac1780555b4f77c11bbfa6b018ee7decc6c6c210b7d48bcc8122e2a2e43e312 |
| mafillsm.f | d6073d5bfd9ad56a03a25b8c79ad1bb2dd178e48e3db3b9dd951f612b0197602 |
