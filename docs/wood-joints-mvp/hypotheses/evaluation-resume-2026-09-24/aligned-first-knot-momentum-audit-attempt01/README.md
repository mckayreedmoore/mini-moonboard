# Aligned 100 N first-knot cleat momentum audit — attempt 01

This post-processes the immutable first-knot snapshot at `t=0.001 s`. The
FRD parser verified complete 116,162-node `DISP` and `VELO` blocks, while the
mass integration used only the current W00 cleat's 5,157 C3D10 elements and
9,369 owned nodes. It used the frozen 600 kg/m³ elastic timber density
scenario and the source-reconstructed CalculiX 2.21 four-point reference
mass. No solver or CAD was run.

The exact deck supplies 100 N per side before the piecewise-linear `RAMP_N`
factor. At the first knot the amplitude is `0.000298`, giving `0.0298 N` on
the cleat. The native Newmark endpoint-trapezoid impulse is `1.49e-05 N·s`;
the sampled-ramp integral is `1.49e-05 N·s` for this first linear segment.
The paired global resultant is near zero, but this audit does not assign
either side's force to any particular contact.

| Cleat-only quantity | Four-point result |
| --- | ---: |
| Integrated mass | 0.558187221 kg |
| COM displacement along N | 1.33467773171e-05 mm |
| COM velocity along N | 0.0266935530687 mm/s |
| COM momentum along N | 1.49000002129e-05 N·s |
| Momentum minus known cleat external impulse | 2.1292953769e-13 N·s |
| Mean unaccounted N-force term over the increment | 2.1292953769e-10 N |
| Newmark free-cleat endpoint displacement | 1.33467763436e-05 mm |
| Work-weighted pair coordinate q | 2.31868661241e-05 mm |
| Frozen snapshot q observation | 2.3186867121e-05 mm |
| Relative rigid-fit translation contribution | 1.45761175881e-05 mm |
| Relative rigid-fit rotation contribution | 6.61436787382e-06 mm |
| Relative nonrigid residual contribution | 1.99638066218e-06 mm |

`q` is reconstructed from the exact nodal CLOAD distribution and FRD
displacements, then normalized by the per-side resultant. It is a relative
actuator coordinate, not W00 COM translation. The cleat momentum agrees with
its known discrete first-step external impulse to `2.13e-13 N·s`; the
signed residual divided by the full increment duration is a mean unaccounted
N-force term. It aggregates internal contact/constraint transfer and
solver/output residuals; it is not an instantaneous or contact-assigned force.

The optional decomposition uses the existing infinitesimal rigid-motion
fitter on every unique C3D10 node with equal geometric node weights, not mass
weights. The residual is the fitted-node displacement remainder projected
through actuator load weights; it is a kinematic split only. The principal
block's scaled-design infinity-norm condition estimate is about `8.8e4`, so
its fitted components deserve extra caution. Each fit is referenced at that
body's consistent-mass COM, but the translation/rotation allocation depends
on the chosen origin and equal-node fit. It is not the mass-weighted COM
displacement. The reported COM displacement and momentum come from consistent
C3D10 mass integration, and the fit pieces are not a unique physical
translation/rotation/deformation partition.

Hashes and full numeric details are in [`report.json`](report.json), and the
reproducible bounded script is [`audit.py`](audit.py). The report pins the
local mass, mesh-parser, FRD/CLOAD, and rigid-fit helper source hashes as well
as the snapshot and generated-run inputs. Whole-patch momentum and energy were
omitted because no serialized whole-patch mass operator cache was available
for this distinct snapshot.

Post-generation synchronization changed only README prose, the audit-script
self-hash, and the residual-force field label/interpretation. No numeric
results or source inputs changed, and mass integration was not rerun.
