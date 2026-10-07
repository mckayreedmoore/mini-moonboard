# Circular shaft finite-motion method

The new [shaft primitive and adapter](../../../../../scripts/thin_bolted_isotropic_shaft.py)
passes 25 focused fixtures and Ruff. Its [source-bound receipt](isotropic-shaft-method-v4.json)
records reference stiffness, analytic force derivatives, finite rigid motion,
bent two-element material-roll invariance, spatial wrench work and the original
350 metal load-centroid audit. This is a numerical method result. No candidate
response, CAD reconstruction, geometry change, strength acceptance or physical
release follows from it.

The earlier [finite mechanical adapter](finite-mechanics-method-v4.md) stays
frozen. Its failed bent-shaft material-roll coupon remains failed evidence.
The new adapter changes only the circular shaft elastic law. Timber beams,
objective condensed fittings, global indices and the seventy appended first
twist coordinates remain unchanged. `response(q)` returns shaft energy,
gradient and sparse Hessian only; `replacement_response(q)` includes frozen
timber and fittings once and the new shaft energy once. Ports and directors
reuse the frozen mechanical adapter. No old shaft elasticity is included in
that replacement response.

For a reference length L and proper reference triad B, each world node state is
`q = (u_mm, 1000 theta_rad)`. With current positions x_i and material triads
R_i = Exp(theta_i) B, the declared element uses

```
Omega = Log(R_0^T R_1)
R_mid = R_0 Exp(Omega/2)
v = R_mid^T (x_1-x_0) / L
epsilon = v_x-1; gamma = (v_y,v_z); kappa = Omega/L
S_eff = 12 EI / [L^2 (1 + 12 EI/(k GA L^2))]
U = L/2 [EA epsilon^2 + S_eff |gamma|^2
         + GJ kappa_x^2 + EI (kappa_y^2+kappa_z^2)]
```

The circular section uses A = pi D²/4, I = pi D⁴/64 and J = pi D⁴/32.
The existing shaft parameters provide E, Poisson ratio, diameter scaling and
the conditional circular shear factor. The primitive rejects a mismatch with
the frozen reference element matrix rather than accepting different properties.

[Meier et al., section 2.2.1 equations 6–8](https://arxiv.org/pdf/1611.06436)
supports material axial/shear and bend/twist strain energy. The condensed
midpoint expression above is a separate finite extension; that source does
not qualify it as an exact element for large curvature. The SO(3) composition
and derivative conventions follow
[Solà et al., Appendix B](https://arxiv.org/pdf/1812.01537).

At reference, gamma_y = delta u_y/L - average theta_z and
gamma_z = delta u_z/L + average theta_y, while kappa = delta theta/L.
Writing phi = 12 EI/(k GA L²), expansion gives the closed Timoshenko
bending coefficients 12 EI/[L³(1+phi)], 6 EI/[L²(1+phi)],
(4+phi) EI/[L(1+phi)] and (2-phi) EI/[L(1+phi)]. Axial and torsional
blocks retain EA/L and GJ/L. Six coupons covering 15, 50 and 120 mm with
two reference bases give a maximum analytic matrix relative error
1.887e-16. The two small tip-cantilever planes recover
F [L³/(3 EI) + L/(k GA)] to relative error 1.11e-16; separate axial
and torsional known answers also pass.

The residual is analytic. Nodal angular increments use the left Jacobian;
the relative rotation increment is
`dOmega = J_l(Omega)^-1 R_0^T (domega_1-domega_0)`.
The midpoint increment includes the first-node spatial increment and the
relative exponential increment. Differentiating v and Omega then gives the
force dual of the scalar energy. The local tangent is a centered difference
of that analytic residual, using a 0.001 mm scaled-coordinate step by default.
A separate directional coupon gives gradient/tangent relative errors
2.276e-10/2.121e-10. The tangent is not artificially symmetrized.

An exact common world rotation transforms both material triads and positions
and leaves v and Omega unchanged. The 20° and 73° rigid coupons have maximum
energy 2.98e-23 N mm. For a common RIGHT material roll Q_x, applied at every
node, Omega becomes Q_x^T Omega and v becomes Q_x^T v. Their axial
components and transverse norms are unchanged, proving the stated circular
energy symmetry even when consecutive chords are non-collinear. Three finite
rolls of the deformed two-element coupon give maximum relative energy change
1.518e-15. Rotation-gradient covariance also passes. Material-roll virtual
work is -1.717e-9 N mm/rad; internal force closes exactly in the saved coupon
and spatial moment closes to 7.47e-9 N mm.

The minimal director representative chooses the shortest rotation taking the
first reference axial vector to its current axial director. Its local rotation
vector has zero x component. The remaining orientation is a right material
roll, removed identically at every shaft node. This preserves all axial
directors and the circular energy; it introduces no torque support. The
full global representation remains available. A later reduced solve must use
the compensating common roll in the world rigid-motion generator. Dropping
the first rotation coordinate from the old generator is insufficient. The
implemented quotient generator holds the representative's first local x
increment at zero and reproduces full spatial external-wrench work to
7.57e-12 in the bent coupon. Full spatial duals are recovered before that
quotient map.

Axis ports and axial directors share the symmetry. The source audit tests all
seventy actual shaft intervals and all 350 original metal centroids in a
declared synthetic finite pose. It preserves their original decimal
coordinates: no centroid is projected. Their maximum radial offset is
4.372e-10 mm; maximum gauge-induced position change is 1.531e-10 mm and
axial-director change is 1.475e-16. The sum of absolute gravity-work changes
is 3.884e-10 N mm. These are precision bounds for the recorded source points,
not evidence from a candidate solved state. A deliberate 5 mm off-axis port
and radial director fail invariance, as expected. Real off-axis loads,
orientation-specific contact, or applied material torque must be assessed
before using this unrestricted gauge.

Curved-arc refinement remains necessary. An unstretched arc yields
v_x = sinc(|Omega|/2), creating artificial axial strain approximately
-|Omega|²/24. The 120 mm arc of radius 1000 mm has exact bending energy
2412.743 N mm. One, two and four elements add artificial axial energies
217.069, 13.5705 and 0.848211 N mm. Refinement reduces this error by about
sixteen per doubling, but no candidate local-curvature convergence is
established by that coupon. The method rejects local director turns at or
above 90°, collapsed chords, near-pi absolute rotation charts and the
antiparallel minimal-director chart instead of clamping them.

Reproduce the receipt with the commands recorded in its JSON, writing to a new
unused output path. The producer reuses the frozen small-assembly fixture and
JSON source inputs; it does not assemble or solve the candidate. Its pins
retain the unchanged mechanical, common-shaft, frame, steel, corotational,
layout, native-geometry and timber-resistance inputs. The new source, tests,
producer and receipt remain active integration inputs; the failed older roll
coupon remains retained evidence. Nothing is pruned or archived here.
