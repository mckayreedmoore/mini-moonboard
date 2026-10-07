# Objective finite-motion plate method readiness

The new [standalone API](../../../../../scripts/thin_bolted_finite_plate.py)
removes the false strain caused by applying small-displacement formulas to
common rigid rotation. Nine cheap coupons pass, including exact 20° and 73°
tilts, superposed arbitrary rotation, stretch, cylindrical bending and analytic
derivative checks. The [method certificate](finite-plate-method-v4.json)
records hashes, commands and measured errors. No assembled candidate response,
CAD rebuild, whole-case solve or native run occurred. All release flags remain
false; the preceding frozen panel/frame helpers and evidence are preserved.

This answers the concrete geometry-method question raised by the previous
upper-left panel's affine-removed slope of 0.087. It does not correct that
saved response or establish finite-motion adequacy for the whole frame.

For the flat reference midsurface `r0=(x,y,0)`, physical material coordinates
`x,y` are measured in mm. Displacements use the retained three coefficient
blocks `[u,v,outward_w]` and the existing cubic C2 tensor basis:
`r=(x+u,y+v,w)`. The exact midsurface metric strains are

```text
Exx   = u_x + (u_x² + v_x² + w_x²)/2
Eyy   = v_y + (u_y² + v_y² + w_y²)/2
gamma = u_y + v_x + u_x*u_y + v_x*v_y + w_x*w_y
n     = (r_x cross r_y)/|r_x cross r_y|
kappa = (-n dot r_xx, -n dot r_yy, -2*n dot r_xy)
```

`gamma=2Exy`; the third curvature component uses the corresponding engineering
twist convention. Reference curvature is zero. Curvatures remain covariant in
the reference material coordinates, without dividing by current tangent
lengths. Their sign reproduces the frozen `Mx=-EI_x*w_xx` convention at small
displacement. A proper rigid rotation preserves all dot products, rotates the
normal with the surface and gives zero strain/curvature for the flat sheet.
The normalized normal, surface metric and offset director geometry follow the
[primary shell formulation, sections 2–3](https://arxiv.org/html/2008.05254v2).
The [original isogeometric Kirchhoff–Love research](https://portal.fis.tum.de/de/publications/isogeometric-shell-analysis-with-kirchhoff-love-elements/)
supports using a sufficiently continuous displacement basis without independent
rotation degrees of freedom.

The reference-area energy proxy is
`0.5*(EA_x*Exx² + EA_y*Eyy² + GA*gamma² + EI_x*kappa_x² + EI_y*kappa_y² + Dtwist*kappa_xy²)`,
where `Dtwist=GA*t²/12`. It reuses only the conditional APA Group 1 CAT23/32
section targets and owner horizontal strength direction from the
[frozen panel methods](panel-mechanics-v4.md). Material axes stay attached to
the flat reference coordinates; energy integrates over reference area. Poisson
terms and membrane/bending coupling remain zero proxies. The method matches
the frozen linear energy tangent at zero displacement.

Objectivity of this geometry does not qualify an actual plywood laminate,
large-strain material response or an exact through-thickness constitutive law.
The primary [full-metric research](https://arxiv.org/html/2008.05254v2) identifies
nonlinear thickness strain and evolving curvature as potential limitations of
reduced shell constitutive models. This quadratic section proxy omits those
higher thickness-metric terms. It cannot establish local holes, conical seats,
rolling-shear rupture, actual hold footprints or Hillman resistance.

`APAProxy.local_energy()` accepts five three-vectors
`[r_x,r_y,r_xx,r_xy,r_yy]` and returns measures, conjugate resultants, energy
density, the analytic 15-component gradient and full 15×15 Hessian. The Hessian
includes both material and geometric terms, including second derivatives of
the normalized normal. It need not remain positive definite away from the
unloaded reference configuration.

`FinitePlate.point_energy()` maps this kernel through the existing basis to
coefficient derivatives. `FinitePlate.energy()` integrates caller-provided
reference-area quadrature. A caller must retain the existing aperture, bevel
and seat stiffness scenarios consistently and establish quadrature/basis
convergence; the API supplies no local opening-boundary qualification.

`FinitePlate.point_port()` returns world position, Jacobian and Hessian for
`r(x,y)+z*n(x,y)`. `z` is the complete signed offset from the midsurface:
the retained hold point uses `t/2+100=109.128125 mm` exactly once. Constant
orthogonal world embeddings may use either handedness; local `+z` maps to
the recorded outward panel director. This preserves the current left-handed
panel-frame convention. The port derivatives allow a later coupled method to
differentiate dead-load work and moving contact points consistently; no such
assembled response is solved here.

The [tests](../../../../../tests/test_thin_bolted_finite_plate.py) pass. At the
20° tilt, maximum Green strain is 2.22e-16, curvature 9.48e-17/mm and offset-port
position error 3.19e-14 mm. Relative central-difference errors are 1.04e-11 for
the local energy gradient and 2.43e-12 for its full Hessian; port Jacobian and
Hessian errors are 2.92e-10 and 1.07e-10. The reference tangent differs from
the frozen linear plate tangent by 2.04e-16 in relative Frobenius norm. The
cylinder coupon returns zero midsurface strain and signed curvature −1/R;
the stretch coupon matches `E=(lambda²−1)/2` and its exact energy derivatives.
Ruff passes. The executable
[certificate producer](../../../../../scripts/check_thin_bolted_finite_plate.py)
reproduces these small coupons and refuses to overwrite existing evidence.

The API, tests, method note and 3.5 kB certificate stay active for the parent's
finite-motion readiness decision. No native output or extra reference manual
copy was created, and no archive/prune operation occurred.
