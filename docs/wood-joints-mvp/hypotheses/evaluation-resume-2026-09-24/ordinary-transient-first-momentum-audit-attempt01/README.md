# First transient cleat momentum audit — attempt 01

This post-processes only the immutable native03 first-converged snapshot at
`t=0.0025 s`. It hashes and checks the frozen current mesh/deck/materials,
then integrates the W00 cleat's C3D10 mass and the raw FRD `DISP`/`VELO` fields.
It runs no solver and imports no CAD. The Gmsh use is mesh-only quadrature.

The mesh contains 5,157 cleat C3D10 elements and 9,369
owned nodes. The frozen wood density is 6e-10 tonne/mm³ (the 600 kg/m³
elastic scenario). The source-CAD reference centroid is
`133.491556566, 42.906713057, 486.256132289 mm`;
the source volume is `930304.310237 mm³`.

The applied cleat force is the serialized CLOAD patch's `0.001915 N`
endpoint resultant along N. The exact Newmark endpoint-trapezoid impulse for
this increment is `2.39375e-06 N·s`; the exact integral of the
sampled piecewise-linear input ramp is `1.66475e-06 N·s`.
Those differ because the native step spans amplitude knots. Compare the
firstpoint body momentum against the **discrete** impulse plus contact/reaction
impulse corrections; do not treat the continuous-ramp integral as the native
one-step balance target.

| Mass operator | Mass (kg) | COM N displacement (mm) | COM N velocity (mm/s) | COM N momentum (N·s) |
| --- | ---: | ---: | ---: | ---: |
| CalculiX 2.21 source-reconstructed four-point | 0.558187221259 | 5.36054467808e-06 | 0.00428843564751 | 2.39374997763e-06 |
| Physical consistent C3D10 Gauss8 | 0.558187221398 | 5.36054467855e-06 | 0.00428843564788 | 2.39374997843e-06 |

For a free cleat with zero initial motion, the four-point mass and the first
Newmark endpoint force predict `0.00428843568759 mm/s` and
`5.36054460948e-06 mm` at the endpoint. The loaded pilot is not a
free body: all omitted contact impulse enters its body balance, and the initial
wood-face normals (X/T) suppress N only as long as those planar normals remain
unrotated. Bore-wall or rotated/deformed contact normals can contribute N.
The observed four-point COM momentum differs from the discrete applied impulse
by `-2.23706e-14 N·s`. This firstpoint
net closure does not show that individual contact impulses are zero; they may
cancel and require the separately recorded contact-force audit.

The serialized `q` is an actuator patch observation, not the cleat COM motion.
The reported center-of-mass fields integrate the actual C3D10 interpolation
with element mass matrices; no equal-node averaging is used. The nodal
actuator projection for the full force pair is `6.98974409398e-06 mm`;
its firstpoint endpoint-trapezoid work is `6.69267996999e-09 N·mm`
(`5.2986855165e-09 N·mm` from the cleat-side loads). This is the
actual serialized CLOAD shape applied to FRD U, separately from COM motion.

The native four-point operator follows the CalculiX 2.21 source reconstruction
recorded in [`dynamic-momentum-qualification.md`](../../../../history/dynamic-momentum-qualification.md).
Its archived controls do not qualify transformed contact mass for this model;
the physical Gauss8 result is deliberately reported separately. Hashes and
full values are in [`report.json`](report.json); the executable method is
[`audit.py`](audit.py).
