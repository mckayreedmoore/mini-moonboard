# Upper-right washer flexure: local elastic contact scenario

**2026-10-02 — conditional analytical working model. Complete joint and
physical release remain HOLD.** Reviewed geometry, source frame results,
hardware policy and the full 47-criterion authority are preserved.

## Decision

The finite flexure calculation is complete: **48/48 end states balance**,
and the single permitted degree-six witness also balances. The engineering
coupon reproduces its exact zero-bending solution.

The governing witness is K12 right, rail_1, host seat, at simultaneous
**T=709.053 N and end M=2.292109 N·m**. Including washer flexibility raises
its required head-center closure from the rigid model's **0.167389 mm**
to **0.184150 mm** in the finer approximation: **+0.016761 mm, or 10.0%**.
Head tilt rises by **8.38%**. Between the two plate bases, closure and tilt
change only **1.96% and 3.95%**. These are useful elastic deformation
sensitivities for the working scenario, not physical error bounds.

**Washer resistance remains unresolved.** The degree-four rail plate proxy
peaks at **230.401 MPa**, apparently below the declared hypothetical
250 MPa yield. At the same unchanged load, degree six gives **359.491 MPa**,
a **56.0% increase**, crossing that comparison. The apparent coarse pass
cannot be retained. The finer value is also not a converged actual stress,
a product failure or a new hardware/redesign gate.

The next useful bounded step is a **local annular plate approximation that
resolves the free inner edge and narrow head-contact band**, using these
same loads and assumptions. It should address the demonstrated numerical
stress sensitivity before another material or hardware decision. Existing
native washer packets and product detailing routes remain separate; this
packet stops after the agreed single refinement.

## Finite scope

Use the saved common-host [rail pair](upper-right-rail-pair.md) and
[side pair](upper-right-side-pair.md), both bound to the unchanged strong-T
`frame-250-attempt02` scenario. Six cases, four bolts and two outer seats
give **48 simultaneous end-load records**. Each washer carries the full
bolt tension and that end's own derived contact moment. Internal bolt
moment, receiver-datum moment and `V*L/4` are not substituted.

This calculation replaces the rigid washer with a local elastic annular
plate while holding each saved end T/M fixed. The bolt, joint groups and
frame are not solved again. It establishes how washer flexure affects the
required head motion, wood/head contact patches and conditional plate stress
for those loads. Feedback into the bolt force split remains outside this
finite calculation.

## Declared geometry and material inputs

The concentric washer, circular head/nut footprint and fully backed wood
annulus are the same geometric scenarios used by the pair producers.
Minimum OD, maximum ID and minimum thickness are used together as an
explicit tolerance scenario, not an observation of one delivered washer.

| Family | Catalog item | OD, mm | ID, mm | Thickness, mm | Flat head/nut circle, mm |
| --- | --- | ---: | ---: | ---: | ---: |
| Rail | [Bolt Depot 2994](https://boltdepot.com/Product-Details?product=2994) | 18.4658 | 8.3058 | 1.2954 | 10 |
| Side | [Bolt Depot 2995](https://boltdepot.com/Product-Details?product=2995) | 22.0472 | 9.9060 | 1.6256 | 12 |

Both primary catalog pages were rechecked on 2026-10-02. They still identify
low-carbon steel and the same dimensional ranges, with no numeric yield
or installed washer capacity. The chosen **E=200,000 MPa, nu=0.30 and
Fy=250 MPa** are hypothetical study inputs. Fy is used only to compare
the conditional elastic stress result; actual product capacity stays null.

Wood support retains **Kwood=20 MPa/mm**, and head contact retains
**Khead=10,000 MPa/mm**, with no preload, friction or initial gaps. The
4.309 MPa timber bearing reference is not imposed as a pointwise pressure
cap or adopted as a nonlinear wood law. Inner and outer washer edges are
free; neither the head circle nor the wood annulus is artificially clamped.

## Small plate and contact model

The [NGSolve primary derivation](https://docu.ngsolve.org/ngs24/SaS/plates_derivation.html)
supports independent transverse displacement w and normal rotations beta,
with bending and transverse shear energy. Use its **dimensional energy**;
the later weak-form expressions divide by thickness cubed and must not be
copied as dimensional resultants.

```text
kappa = [d(beta_x)/dx, d(beta_y)/dy,
         d(beta_x)/dy + d(beta_y)/dx]
gamma = grad(w) - beta
D = E*t^3/[12*(1-nu^2)]
Cb = D * [[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]]
Cs = (5/6)*E/[2*(1+nu)]*t
Uplate = 1/2 * integral(kappa.Cb.kappa + Cs*gamma.gamma) dA
```

The three fields use complete normalized polynomials through degree four.
This gives 45 plate coordinates and three rigid-head coordinates. Constant
translation and two rigid tilts have zero plate strain energy. The gradient
of every displacement polynomial lies in the rotation space, so the
zero-shear limit is representable. This is a finite Ritz approximation,
not a stress upper bound. [GetFEM's official documentation](https://getfem.org/userdoc/model_Mindlin_plate.html)
describes the model and warns that unsuitable discretizations can lock.

For the rigid head plane h and zero initial gaps:

```text
pwood = Kwood * max(w,0)
qhead = Khead * max(h-w,0)
Pi = Uplate + 1/2*integral(Kwood*max(w,0)^2) dAwood
            + 1/2*integral(Khead*max(h-w,0)^2) dAhead
            - T*h_center - M*head_tilt
```

Local +x is aligned with the saved end moment/tilt direction. Signed source
vectors remain in the receipts; isotropic, concentric response depends on
their magnitude. Both contact resultants must reproduce the same T and
pressure first moment M. Complete constant/linear plate and head modes
enforce these balances through stationarity. Contact remains nonnegative,
and unloaded points supply no artificial stiffness.

The producer reuses the frozen annulus quadrature and rigid-contact
initialization. No native or CAD dependency is introduced. End labels
`host` and `cleat` refer to the two source receiver ends; identical circular
pressing profiles are assumed at both. Delivered head/nut placement is not
inferred from those labels.

## Conditional stress recovery

Recover dimensional plate resultants `Mplate=Cb*kappa` and `Q=Cs*gamma`.
For a homogeneous, membrane-free plate, bending stress at distance z from
the midplane is `12*z*Mplate/t^3`. Declare a parabolic transverse shear
recovery `tau=3*Q/(2*t)*(1-4*z^2/t^2)`. Its peak is at the midplane;
bending peaks are at the surfaces.

The recovered through-thickness von Mises maximum is therefore:

```text
max(6/t^2*sqrt(Mxx^2-Mxx*Myy+Myy^2+3*Mxy^2),
    3*sqrt(3)/(2*t)*sqrt(Qx^2+Qy^2))
```

This follows from the stated stress recovery; separate surface and midplane
peaks are not combined at a fictitious common thickness location. Contact
normal stress sigma_zz, bearing-edge concentrations, threads, washer float,
membrane effects, plasticity and actual head profiles remain excluded.
Reported stress is a **conditional plate proxy**, not actual three-dimensional
washer stress or a manufacturer rating.

## Method sign check and numerical scope

A small engineering coupon applies T=100 N, M=0 with both contact footprints
equal to the complete annulus. Its known solution is uniform wood pressure
T/A, washer translation `T/(Kwood*A)`, zero plate strain and head closure
`T/(Kwood*A)+T/(Khead*A)`. This checks force/contact signs and the rigid
plate modes before the finite end-load batch. It does not qualify the
physical washer or substitute clamped-edge evidence.

The finite production batch uses the declared degree-four basis. A single
governing end may be repeated with degree six to expose basis sensitivity;
this changes numerical approximation only. No material, wood stiffness,
head diameter or hardware sweep belongs to this packet. A numerical stop
does not prove physical incompatibility.

## Same-state comparison worksheet

The main batch uses degree four: 48 scaled unknowns per washer. Its maxima
below are over the four seats in each family in that case. These are
**coarse elastic proxies**, not accepted washer resistances. The side family
was not refined; its lower coarse stresses do not establish convergence.

| Case | Rail plate proxy, MPa | Side plate proxy, MPa | Largest rail head-center closure change, mm | Largest side head-center closure change, mm |
| --- | ---: | ---: | ---: | ---: |
| A12 rear | 29.284 | 22.864 | 0.00177 | 0.00129 |
| A12 forward | 14.176 | 10.982 | 0.00091 | 0.00068 |
| A12 left | 16.130 | 13.605 | 0.00108 | 0.00083 |
| K12 right | 230.401 | 127.520 | 0.01473 | 0.00623 |
| K12 rear | 227.613 | 127.039 | 0.01445 | 0.00609 |
| A1 rear | 3.364 | 1.546 | 0.00025 | 0.00009 |

The single refinement has 87 scaled unknowns, with all material, contact,
head and washer geometry inputs unchanged. Compare the same rail_1 host
seat and T/M, rather than unrelated case peaks:

| Quantity | Saved rigid washer | Degree four | Degree six | Change, four → six |
| --- | ---: | ---: | ---: | ---: |
| Head-center closure, mm | 0.167389 | 0.180608 | 0.184150 | +1.96% |
| Relative head tilt, rad | 0.022364 | 0.023316 | 0.024237 | +3.95% |
| Non-affine washer deflection, weighted RMS, mm | 0 | 0.009265 | 0.011338 | +22.4% |
| Sampled plate stress proxy, MPa | Unassigned | 230.401 | 359.491 | +56.0% |
| Wood pressure peak at integration points, MPa | 7.145648 | 6.927869 | 6.842123 | −1.24% |
| Pressing-face pressure peak at integration points, MPa | 81.672607 | 100.992111 | 116.163926 | +15.0% |

The fine witness has approximately **0.02914 mm maximum non-affine
deflection** in the sampled field. Its wood contact area is 200.037 mm²,
93.6% of the minimum annulus; pressing-face active area is 13.466 mm².
Both pressure fields reproduce full T and the same first moment M.
Wood mean pressure remains **3.319103 MPa** because force and annulus area
are unchanged. Flexure changes pressure distribution and compliance;
it does not convert the 4.309 MPa mean reference into a pointwise cap.

## Physical meaning of the inner-edge witness

Both bases place their maximum plate proxy at local
**(x,y)=(4.1529,0) mm**, on the free inner radial edge. At degree six,
the recovered moment components are approximately
`(Mxx,Myy,Mxy)=(-84.696,-111.112,0)` N, or N·mm/mm. One surface has
`(sigma_xx,sigma_yy,tau_xy)=(-302.836,-397.287,0)` MPa; the opposite
surface reverses all bending signs. The **359.491 MPa** value is the
bending von Mises combination of these simultaneous components, not the
sum of independently chosen stress peaks. The same-point recovered
midplane shear proxy is only **59.683 MPa**.

The free continuum edge requires zero moment traction and zero normal
transverse shear. Ritz stationarity enforces that condition weakly, not
exactly at every edge point. At this witness the degree-four and degree-six
inner-edge moment traction magnitudes are approximately **59.446 and
84.696 N**, respectively, instead of zero. Normal shear traction is
approximately **+4.514 and −29.758 N/mm**. These are numerical boundary
residual diagnostics, not additional applied loads or observed forces.
They reinforce why the rapidly changing edge stress is unresolved even
though global force/moment equilibrium and head motion look stable.

The head-contact radial band is only **0.8471 mm**, narrower than the
1.2954 mm washer thickness. The chosen plate theory includes transverse
shear, but does not resolve local three-dimensional bearing-edge stress or
contact sigma_zz. A larger recovered elastic proxy invalidates the chosen
250 MPa elastic comparison in that numerical branch; it does not prove
physical yielding or justify replacing hardware by itself.

## Receipts and reproduction

The main batch and one refinement return in 1–4 Newton steps. Across their
49 end states, maximum residuals are **1.82e-11 N** scaled gradient,
**2.32e-11 N** contact force and **6.83e-12 N·mm** contact first moment,
well below the declared 1e-4 N / 0.001 N / 0.02 N·mm local criteria.
The uniform coupon gives zero plate bending/shear energy and a
1.31e-12 N gradient; its head closure is 0.023451996 mm at T=100 N.
All three plate rigid modes retain zero matrix energy and action.

Each packet authenticates **12 source pins and five declared output pins**.
Ruff passes. The worksheet reads saved outputs only; it runs no mechanics.
No software tests, frame/native/CAD solves, review loop, geometry changes,
staging or commits were performed by this worker. Actual washer stress,
yield and capacity remain null; all authority/release flags remain unchanged.

From the repository root, use a fresh output path for each run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/upper-right-washer-flexure.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/upper-right-washer-flexure/attempt01

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/upper-right-washer-flexure.py \
  --degree 6 --state-id 'k12-right/top_outer/clip_single_top_right_2/rail_1/host' \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/upper-right-washer-flexure/attempt02-degree6
```

Ignored result folders also contain exact producer snapshots, streamed
contact/plate fields, state worksheets and source/output hashes.
`rawlocal/upper-right-washer-flexure/worksheet.py` creates the single
cross-basis `worksheet.json` from those saved receipts.

| Artifact | SHA256 |
| --- | --- |
| `upper-right-washer-flexure.py` | `782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac` |
| `attempt01/checks.json` | `a6ac3fb5587ed24926e5fbc3353f69db19fb7fe8a60eb2dee40fa911b2f2544a` |
| `attempt01/source-pins.json` | `4002d3b0af588396b380a4d748687aeb46f0bfa4a5486f994f284afd0cbb65c6` |
| `attempt02-degree6/checks.json` | `09486b37ba7b914f889301ae2691f806a1417304622660ff1366a649dfc488b2` |
| `attempt02-degree6/source-pins.json` | `dd08e930c0e1a23781fecdacb2b0537e8e3f7daf16692b5ae4df290b3442ffc7` |
| `worksheet.py` | `d4ece06dc4e1927f0fff736e7c96f246b8725812f029780e297ec7793dc4cf34` |
| `worksheet.json` | `6e9826ab8a71d2a9017df876562b0262ab2e7cf80b0afafec28ddf70646f7ee3` |
