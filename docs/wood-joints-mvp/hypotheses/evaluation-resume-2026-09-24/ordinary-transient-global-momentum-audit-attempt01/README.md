# First transient whole-patch momentum audit — attempt 01

This post-processes only the immutable native03 first-converged snapshot at
`t=0.0025 s`. The calculation integrates the actual firstpoint FRD `DISP`
and `VELO` fields over all positive-density physical timber and steel owners,
using their frozen material densities and the source-reconstructed
CalculiX 2.21 four-point C3D10 mass matrix. It runs no solver and imports no
CAD. Gmsh is used only to integrate the frozen mesh reference-volume mass.

The section map resolves 19 C3D10 owners: three timber owners at
`6e-10 tonne/mm³`, twelve steel owners at `7.85e-09
tonne/mm³`, and the four nut carrier solids at exactly zero density. The
carrier element sets are excluded from material inertia; they remain present
as kinematic constraints. The four `*RIGID BODY` cards tie every node in each
nut carrier to reference/rotation control nodes, while the frozen
`nut-coupling.inp` shaft-fit equations connect those controls to the bolt
shaft model. These constraints may pass internal force and moment between
the physical owners, but the carriers and control nodes add no mass. The DAT
also reports zero kinetic energy for `CURRENT_NUT_CARRIERS`.

| Quantity | Four-point physical-owner audit | Native DAT |
| --- | ---: | ---: |
| Total mass | 11.7756010093 kg | 11.7756 kg |
| Total kinetic energy | 6.38064889261e-09 N·mm | 6.380649e-09 N·mm |
| Linear momentum (X, Y, Z) | `[-2.3797785310605182e-14, 8.19773933384898e-14, 4.190929543969184e-14]` N·s | Compare with paired impulse below |
| Angular momentum about origin (X, Y, Z) | `[-3.912610730984278e-11, 8.170579233843068e-14, 1.0000875686435352e-11]` N·mm·s | Compare with applied angular impulse below |
| Angular momentum about actuator datum (X, Y, Z) | `[-1.0622871043489898e-12, 1.5385547673240626e-11, 1.6797039883667408e-12]` N·mm·s | Datum `[89.05, 42.906715329, 486.256134997]` mm |

The serialized actuator pair sums to a unit resultant
`[0.0, 2.6833593487432408e-17, -1.7521883358196802e-15]` N before amplitude scaling. Its firstpoint Newmark
endpoint-trapezoid linear impulse is `[0.0, 6.423291441054133e-23, -4.1943008288683596e-21]` N·s. The
actual nodal force distribution has reference-geometry moment
`[-1.1368683772161603e-13, 1.5631940186722204e-13, 0.0]` N·mm per unit amplitude and endpoint-geometry
moment `[2.621436578920111e-08, -7.260823053911736e-09, -8.6536431354034e-09]` N·mm per unit amplitude, so the corresponding
discrete angular impulse is `[6.275063810790016e-14, -1.738059518530122e-14, -2.0714658255371887e-14]` N·mm·s. At the actuator
datum the endpoint couple is `[2.621444484040422e-08, -7.260979175019616e-09, -8.653648459118476e-09]` N·mm per unit
amplitude and its discrete impulse is `[6.275082733671761e-14, -1.7380968900203207e-14, -2.0714670999014854e-14]`
N·mm·s. The pair is self-equilibrated in force; the report retains its moment
rather than assuming it is moment-free.

FRD values use 12-character scientific fields with five digits after the
mantissa decimal. For each printed exponent `e`, the audit uses a component
half-quantum of `0.5 × 10^(e−5)`. It propagates those node-specific `DISP`
and `VELO` bounds through absolute four-point mass-matrix weights for `P`
and through `Σ |Mᵢⱼ| rᵢ×vⱼ` for `H`, including `δr`, `δv`, and cross terms.
The momentum residual is `[-2.3797785310605182e-14, 8.197739327425689e-14, 4.190929963399267e-14]` N·s against componentwise bound
`[1.7487877518376762e-12, 1.3437563057941796e-11, 1.0439138946221732e-11]` N·s; within-bound flags are
`[True, True, True]`.
About the actuator datum, the angular residual is `[-1.1250379316857073e-12, 1.540292864214083e-11, 1.7004186593657557e-12]`
N·mm·s against bound `[3.3813562877284804e-09, 1.4903217306332545e-09, 1.614450387536462e-09]` N·mm·s; within-bound
flags are `[True, True, True]`.
These bounds decide what the printed fields resolve; they do not include
solver equation residuals or contact/MPC mass transformation.

The origin-shift check gives direct actuator-datum angular momentum
`[-1.0622871043489898e-12, 1.5385547673240626e-11, 1.6797039883667408e-12]` and
`H₀ − a×P = [-1.0622870770097292e-12, 1.5385547657866247e-11, 1.6797040098600394e-12]`
N·mm·s, with translation residual
`[-2.733926052633145e-20, 1.5374379530519778e-20, -2.1493298670070915e-20]`.
Per-owner mass, center of mass, momentum, angular momentum, kinetic energy,
source pins, and full residual bounds are in [`report.json`](report.json); the
executable method is [`audit.py`](audit.py).

The untransformed four-point mass gives a DAT total ELKE difference of
`-1.07392e-16 N·mm` (`-1.68309e-08` relative) on
this firstpoint. This scalar comparison is useful evidence for the summed
body kinetic energy; it does not qualify the solver's full effective mass
through contact or rigid-carrier MPC transformations. Momentum closure also
remains conditional on those internal transfer paths and the single-step
Newmark impulse. FRD rounding bounds apply only to printed-data uncertainty,
not to the solver's transformed mass or constraint residuals.
