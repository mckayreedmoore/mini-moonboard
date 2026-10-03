# Upper-right washer free-edge approximation

**2026-10-02 — conditional local analytical scenario. Complete joint and
physical release remain HOLD.** Reviewed geometry, frozen frame evidence,
material/contact hypotheses and the full 47-criterion authority are unchanged.

## Purpose and finite decision

The [frozen washer-flexure study](upper-right-washer-flexure.md) found a
demonstrated approximation defect: increasing its global polynomial degree
changed the same-state stress proxy from 230.401 to 359.491 MPa, while the
free inner-edge moment/shear traces failed to approach zero. Its closure
and tilt were less sensitive, but this did not establish washer resistance.

This packet replaces the global polynomial approximation with local radial
elements and angular Fourier modes. It evaluates **one unchanged witness
at exactly two planned resolutions**. The question is whether resolving the
free inner edge and narrow pressing band stabilizes its conditional stress
and motion. It introduces no hardware change, new material resistance,
qualification criterion or feedback into the bolt pair/frame.

**The targeted numerical repair is complete.** Both planned resolutions
balance. The stress proxy changes only **0.321%**, closure **0.0016%** and
tilt **0.0048%**, while all sampled free-edge traction residuals decrease.
This greatly reduces the earlier global-polynomial stress instability for this
specific working scenario; two approximations do not prove a physical
error bound or complete continuum convergence.

The finer elastic plate proxy is **512.232 MPa**, or **2.049 times the
hypothetical 250 MPa yield**. The previous apparent coarse pass cannot be
retained. The declared linear-elastic/Fy hypothesis is unsupported at
this fixed T/M. Actual product yield, plastic redistribution and installed
resistance remain unverified; no physical washer failed and no manufacturer
capacity is inferred. There is no third resolution or material/hardware sweep.

## Frozen load and hypotheses

Use only `k12-right/top_outer/clip_single_top_right_2/rail_1/host` from the
saved [rail pair](upper-right-rail-pair.md): simultaneous **T=709.052842 N
and end |M|=2292.108528 Nmm**. Local +x is aligned with the saved end
moment/tilt direction; its signed source vectors remain in the receipts.
This is that receiver's bolt-end contact moment, not an internal beam
maximum or a receiver-datum moment.

The annulus remains ri=4.1529 mm, ro=9.2329 mm and t=1.2954 mm. The
concentric pressing footprint ends at radius 5 mm, leaving a 0.8471 mm
radial head-contact band. The same hypothetical inputs are retained:
E=200,000 MPa, nu=0.30, Kwood=20 MPa/mm, Khead=10,000 MPa/mm and shear
correction 5/6. Fy=250 MPa remains only an expressly hypothetical comparison;
actual washer yield, stress and resistance remain unknown.

There is no preload, friction, initial gap, plasticity, membrane response
or three-dimensional normal/contact-edge stress. Both radial edges are
free. The radius-5 circle changes the head footprint; it is not a support
or clamp. The host/cleat label does not infer the delivered head/nut placement.

## Local plate approximation

The [NGSolve dimensional derivation](https://docu.ngsolve.org/ngs24/SaS/plates_derivation.html)
supports independent displacement and rotations with bending/shear energy
and free moment/shear boundary conditions. Its later thickness-scaled weak
form is not used as dimensional resultants. The polar form below follows
by transforming that same isotropic energy. These discretization choices
are our analytical construction, not a product rating or a supplied solver
verification.

```text
kappa = [beta_r,r,
         (beta_theta,theta + beta_r)/r,
         beta_theta,r + (beta_r,theta - beta_theta)/r]
gamma = [w,r - beta_r, w,theta/r - beta_theta]
D = E*t^3/[12*(1-nu^2)]
Cb = D*[[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]]
Cs = (5/6)*E*t/[2*(1+nu)]
Uplate = 1/2*integral(kappa.Cb.kappa + Cs*|gamma|^2) r dr dtheta
```

Reflection symmetry about local x is used: w and beta_r use cosine modes
0 through mmax; beta_theta uses sine modes 1 through mmax. The concentric,
isotropic model and x-aligned loading permit this restriction. An independent
head y-tilt coordinate remains for the contact-balance diagnostic; the plate
y-tilt is outside the symmetric trial space.

```text
w = w0 + (r/ro)*u
beta_r = a/ro
beta_theta = b/ro
h = h0 + hX*x/ro + hY*y/ro
```

u uses C1 cubic Hermite radial functions. Its nodal derivative coordinates
are scaled as ro*u,r. Independent a and b use C0 piecewise cubic Lagrange
functions. Every coefficient has units of mm. Both components of grad(w)
are represented in the rotation space:

```text
w,r = (u+r*u,r)/ro
w,theta/r = u,theta/ro
```

This avoids an incompatible discrete zero-shear limit. [GetFEM's official
documentation](https://getfem.org/userdoc/model_Mindlin_plate.html) describes
the shear-locking problem; it does not establish convergence of this custom
trial space. Full integration is retained, without shear reduction.

For the axisymmetric mode, u(ri)=0 and the separate free w0 coordinate
supplies the inner-circle value. This is a trial-space representation
convention, not a fixed displacement or removal of a true duplicate basis
function. No rotation is prescribed. Free boundaries enter naturally through
the energy; **Mrr, Mrt and Qr are not forced to zero pointwise**. Their
recovered traces are independent diagnostics. Hoop moment Mtheta-theta
need not vanish at a free circular edge.

| Numerical resolution | Radial elements inside/outside radius 5 | Highest Fourier mode | Scaled unknowns including head | Angular points |
| --- | ---: | ---: | ---: | ---: |
| Coarse | 2 / 6 | 4 | 318 | 64 |
| Fine | 4 / 12 | 8 | 1142 | 128 |

Six Gauss radii per element integrate both the plate and unilateral contact
terms. The head circle is an element boundary in both resolutions. Fine
head-band/outside widths are 0.211775/0.352742 mm. These counts are fixed
before execution; adequacy is judged from the results, not presumed.

Contact energy and stress recovery match the preceding flexure packet.
Both head and wood resultants must reproduce T and pressure first moment M.
Face von Mises is recovered from 6Mplate/t²; midplane shear proxy from
3*sqrt(3)*|Q|/(2t). Their maximum compares separate thickness locations.
This remains an elastic plate proxy, excluding sigma_zz and local 3D peaks.

## Readiness and execution boundary

The producer authenticates the frozen source chain and records its own
snapshot, source/output hashes and last accepted iterate on numerical stop.
Local sparse assembly and Newton/Armijo contact equilibrium are used.
No native, CAD or frame solve is part of this packet.

The producer is frozen at SHA256
`ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61`.
Ruff passes. Execution is serialized by the main coordinator. From the
repository root, each command requires a fresh output directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/upper-right-washer-edge.py --resolution coarse --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/upper-right-washer-edge/attempt01-coarse
```

After the first run finishes, the planned fine command is:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/upper-right-washer-edge.py --resolution fine --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/upper-right-washer-edge/attempt02-fine
```

Each resolution includes the same full-face T=100 N/M=0 engineering coupon:
uniform pressure T/A, washer translation T/(Kwood*A), head translation
T/(Kwood*A)+T/(Khead*A), and zero plate strain. Exact normal and x-tilt
rigid modes must have zero plate energy. This coupon checks signs and
representation; it does not validate the candidate's stress field.

Declared numerical tolerances remain gradient 1e-4 N, resultant force
0.001 N and first moment 0.02 Nmm. Edge traction residuals and changes in
stress/closure/tilt will be reported without a new pass threshold or an
assumed physical error bound. A numerical stop does not prove physical
incompatibility. The finite task ends after these two resolutions.

## Results and recommended next step

The main coordinator executed coarse then fine with the same frozen producer
in its serialized slot; both exited 0. Each uses four Newton steps. This
worker performed only lightweight saved-result postprocessing afterward.
The engineering coupon is exact at both resolutions: uniform pressure
0.468104 MPa, washer translation 0.02340519 mm and head translation
0.02345200 mm, with zero bending/shear energy. The two in-subspace rigid
modes have sampled curvature below 1.24e-14/mm, shear strain below 3.85e-16
and matrix action below 1.48e-8 N.

The largest production scaled gradient is 3.65e-10 N, force residual
5.80e-12 N and first-moment residual 6.47e-9 Nmm. The largest relative
linear-solve residual is 3.34e-12; energy-identity residual magnitude is
3.25e-11 Nmm. No artificial stiffness or pointwise edge constraint was added.
These are numerical diagnostics, not joint resistance checks.

### Same-state comparison worksheet

All rows use the same 709.052842 N / 2292.108528 Nmm load and hypotheses.
The older global results are preserved and included for comparison only.

| Approximation | Head-center closure, mm | Head tilt, rad | Non-affine washer RMS, mm | Sampled elastic plate proxy, MPa |
| --- | ---: | ---: | ---: | ---: |
| Saved rigid contact | 0.167389 | 0.0223638 | 0 | Not modeled |
| Global degree 4 | 0.180608 | 0.0233162 | 0.00926481 | 230.401 |
| Global degree 6 | 0.184150 | 0.0242375 | 0.01133767 | 359.491 |
| Local coarse | 0.185755 | 0.0256618 | 0.01283458 | 510.595 |
| Local fine | 0.185752 | 0.0256630 | 0.01283423 | 512.232 |
| Local fine change from coarse | -0.0016% | +0.0048% | -0.0027% | +0.3207% |

Relative to the saved rigid contact, fine closure rises **0.018364 mm
(10.97%)** and tilt rises **14.75%**. These elastic motion sensitivities are
stable between the planned local approximations, but their physical accuracy
depends on the material/contact assumptions. The elastic branch also
exceeds its hypothetical yield comparison.

### Free-edge traces and governing stress

The exact continuum natural conditions are Mrr=Mrt=Qr=0 at each radial edge.
Reported maxima sample all angles; they are not zeroed by construction.

| Edge | Trace | Local coarse | Local fine |
| --- | --- | ---: | ---: |
| Inner | max abs Mrr, N | 0.151137 | 0.025715 |
| Inner | max abs Mrt, N | 0.344880 | 0.054050 |
| Inner | max abs Qr, N/mm | 0.764453 | 0.054809 |
| Outer | max abs Mrr, N | 0.022522 | 0.003506 |
| Outer | max abs Mrt, N | 0.182704 | 0.031442 |
| Outer | max abs Qr, N/mm | 0.093840 | 0.010730 |

The stress peak remains at the inner circle, local x=4.1529 mm/y=0.
At the fine witness, Mrr=0.025715 N and Qr=0.054809 N/mm are small residual
traces, while **hoop moment Mtheta-theta=-143.246714 N** remains. The free
edge does not require zero hoop moment. Surface stresses there are
approximately **[0.09194, -512.18651, 0] MPa** in radial/hoop/shear order;
opposite-face bending signs reverse. Thus the high stress is not removed
by satisfying radial free-traction conditions. The separate midplane shear
proxy at that point is only 0.10993 MPa.

Fine outer-edge stress peaks at 158.826 MPa; head-band-boundary stress at
397.495 MPa. Contact quadrature peaks are 6.784 MPa on wood and 142.341 MPa
on the head interface. Those contact pressures are not three-dimensional
washer stresses or imposed timber strength caps. Both contacts reproduce
the same T/M. The wood/head active areas are 201.992/12.866 mm².

### Practical decision

The finite numerical sensitivity is sufficiently small to distinguish this
scenario's elastic stress from the earlier approximation artifact. It still
does not establish actual washer capacity or extend to the other 47 seats.
Do not retain the degree-four apparent pass or discard the stress merely
because its peak lies at a free edge.

**Recommended next mechanical step:** incorporate the compatible washer
response in the shared-host bolt-pair calculation, preserving the signed
interface wrench, to determine whether bolt-end moments and force split
change enough to alter this conclusion. The current elastic response may
be used as a sensitivity, with its yield conflict explicit; it must not be
adopted as a validated elastic washer law. If demand persists, bind an
applicable washer material/detailing basis or a separately proposed hardware
correction before claiming resistance. Actual product yield remains a missing
fact; assuming it equals 250 or 512 MPa does not resolve it.

Complete joint behavior also needs both bolt groups and the common timber
block, including applicable timber resistance. The main coordinator owns
that integration. This packet ends here; no native/3D run, stronger-hardware
claim, new gate or additional refinement is introduced.

## Reproducible result receipts

The ignored [worksheet producer](rawlocal/upper-right-washer-edge/worksheet.py)
authenticates **13 source pins and four declared output pins per local
packet**, plus each saved checks receipt. It compares only this exact state
with the two frozen global approximations. It does not solve mechanics.
Ruff passes for both the maintained producer and worksheet; no software tests
were added or run. Complete joint and physical release flags remain false.

| Artifact under `rawlocal/upper-right-washer-edge/` | SHA256 |
| --- | --- |
| `attempt01-coarse/checks.json` | `b912f3f3d406cfda3f3c6fe7b074eb9f573438b97bc9e6278ad4de78aff07150` |
| `attempt01-coarse/source-pins.json` | `82215e53942d3eb9623bf61012d3581a58599907dac4f18d8dd30db949b973c7` |
| `attempt02-fine/checks.json` | `4f637c1317f1c65c340b2013bf56a8bedc276850aada17e56ec03605b305e92b` |
| `attempt02-fine/source-pins.json` | `0fd1b38125afa38b5297d88dbb1257f5495db77535c50cad77928164e504eb5d` |
| `worksheet.json` | `9db479cd3c850efb0630df833938ffc35b5cb003e410a1a4fe64501a6247ed3d` |

## Preserved source receipts

These were authenticated before new production. The producer authenticates
the complete reused source chain again before and after each run.

| Frozen source | SHA256 |
| --- | --- |
| `upper-right-washer-flexure.py` | `782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac` |
| `upper-right-washer-flexure.md` | `7d57430ee7cc44ceec320a55df244e430eb353bcf0f069e515512291f571efb2` |
| `rawlocal/upper-right-rail-pair/attempt01/checks.json` | `e0cccb56abb94ed16c322da888cd64a9904c4e49d1e34f573a6903c8b8b98d3d` |
| `rawlocal/upper-right-washer-flexure/attempt02-degree6/checks.json` | `09486b37ba7b914f889301ae2691f806a1417304622660ff1366a649dfc488b2` |
