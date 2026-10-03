# Two loose flat washers at the frozen upper-right witness

**Conditional local comparison. No hardware change or complete-joint acceptance.**

This finite investigation asks whether adding a second identical loose flat
washer improves the [single-washer edge result](upper-right-washer-edge.md).
It preserves the old simultaneous **709.052842 N tension / 2292.108528 Nmm
end moment** and the existing wood/head laws. These are the earlier rail-pair
demands, not the current physical first-order corner result. Comparison at a
fixed demand isolates the washer change; main must bind any proposed adoption
to the current joint response.

## Contact model and exact reduction

Each washer is independently ri=4.1529 mm, ro=9.2329 mm and t=1.2954 mm,
with E=200,000 MPa, nu=0.30 and the same hypothetical 250 MPa yield comparison.
The upper washer contacts the existing radius-5-mm head footprint; the lower
washer contacts the existing nominal wood annulus. Khead=10,000 MPa/mm and
Kwood=20 MPa/mm remain hypothetical. Both washer radial edges are free.

The [NGSolve plate derivation](https://docu.ngsolve.org/ngs24/SaS/plates_derivation.html)
supplies the separate plate bending and shear energy, proportional to Et³ and
Et respectively. The following stack reduction is our analytical inference
from that energy, not an NGSolve or manufacturer claim about stacked washers.

For two identical, concentric, initially flat plates with frictionless hard
normal contact, consider coincident transverse displacement w and equal
rotation fields beta. The two original plate energies sum to **2Kb and 2Ks**.
Stress in each washer uses its original thickness and constitutive law.
No tangential shear is transmitted between the washers. A bonded solid 2t
plate would instead have 8Kb and is not represented here.
Normal contact constrains the transverse gap, not rotations or tangential
sliding. Equal rotations follow in this witness from the identical plate
operators and common w with no applied rotational interface load.

As an independent limiting-case comparison, [Poincloux et al., Physical Review
Letters 126, 218004](https://www.epfl.ch/labs/flexlab/wp-content/uploads/2021/06/94_2021_Poincloux_PRL_Book.pdf)
give small-deflection frictionless stack bending stiffness n times each
layer's stiffness; preventing sliding instead gives a thickness-cubed limit.
Their book/beam geometry is not this washer contact problem and supplies no
washer resistance or pressure-distribution validation.

Coincidence must satisfy the separate plate equations and normal contact,
rather than being imposed without a pressure witness. With downward positive,
extend head pressure by zero outside the pressing band:

```text
2K q + Wᵀ A (pwood - phead) = 0              combined plate equilibrium
pinterface = (phead + pwood)/2 >= 0          hard-contact multiplier
K q + Wᵀ A (pinterface - phead) = 0         upper plate equilibrium
K q + Wᵀ A (pwood - pinterface) = 0          lower plate equilibrium
gap = 0; pinterface * gap = 0               normal complementarity
```

The last three rigid-head coordinates are excluded from individual plate
residuals. Pressure is nonnegative because both external pressure laws are
compression-only. Regions where both external pressures vanish have zero
interface pressure and may have zero gap; contact need not be positively
pressed everywhere. Both individual residuals are recovered independently
with the original single-plate matrix. Interface force and first moment must
recover the same T/M. The constraint permits opening; this particular common-w
solution is admissible because it needs no tensile contact traction.

The linear elastic plate energies and unilateral external contacts form a
convex problem. An admissible coincident state satisfying each plate's weak
equilibrium and contact complementarity is consequently a solution of that
discrete two-plate problem. This does not establish delivered washer flatness,
alignment, material strength or three-dimensional contact behavior.

## Finite execution

The [producer](stacked-washers.py) imports the frozen edge helper, sums only
its assembled bending/shear matrices and retains individual stress recovery.
It changes no existing source or result. The two planned resolutions are the
existing coarse 318-coordinate and fine 1142-coordinate approximations;
there is no third refinement or product/material sweep. Each includes the
existing full-face 100 N / zero moment engineering coupon and rigid-mode
diagnostics, plus the recovered two-plate interface witness. These mechanics
checks are not software test suites.

The producer is frozen at SHA-256
`974331e6c98f07b7957adf86ebf3fd7c546e8926133ce0f6c43d5ee02a34eb97`.
The imported edge helper must retain
`ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61`.
The original fine result is
`4f637c1317f1c65c340b2013bf56a8bedc276850aada17e56ec03605b305e92b`.
Ruff passes. Main completed both following commands serially on October 2,
2026. No worker executed mechanics. Both existing output directories must
remain immutable; these commands are reproduction records, not rerun requests.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/stacked-washers.py --resolution coarse --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/stacked-washers/attempt01-coarse
```

After coarse completes:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/stacked-washers.py --resolution fine --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/stacked-washers/attempt02-fine
```

Gradient, force and moment tolerances remain 1e-4 N, 0.001 N and 0.02 Nmm.
Source/output pins and the exact producer snapshot authenticate each run.
A numerical stop records its last accepted state and proves no physical
incompatibility. Native, CAD and frame runs are outside this investigation.

## Results and finite conclusion

Both planned approximations completed and their engineering coupons passed.
The source/output receipts authenticate all 14 source pins and all five
recorded output pins for each run, including the unchanged producer snapshot.
The comparison is complete; no additional refinement or review loop is needed
for its finite question.

| Same fixed old T/M | One washer, existing fine result | Two washers, coarse | Two washers, fine |
| --- | ---: | ---: | ---: |
| Peak individual elastic stress proxy (MPa) | 512.232 | 273.898 | 274.843 |
| Proxy / hypothetical 250 MPa yield | 2.04893 | 1.09559 | 1.09937 |
| Head closure (mm) | 0.185752 | 0.177048 | 0.177048 |
| Head tilt magnitude (rad) | 0.0256630 | 0.0241204 | 0.0241203 |
| Peak wood pressure (MPa) | 6.78401 | 6.98170 | 6.98916 |
| Peak head pressure (MPa) | 142.341 | 112.401 | 113.075 |

Two washers reduce each washer's peak proxy by **46.344%**, but remain
**9.937% above the assumed yield**. They substantially improve this local
hypothesis without closing its elastic/yield comparison. Pressure redistribution
explains why the result is not exactly half the single-washer stress.
Wood bearing area and full-annulus mean pressure are unchanged; peak wood
pressure rises slightly. The stress peak remains the free inner circle at
x=4.1529 mm, y=0, predominantly hoop bending. Fine face stresses are
[0.034845, −274.825259, 0] MPa; its midplane shear proxy is 0.106518 MPa.
A free radial edge does not require the hoop moment to vanish.

Coarse-to-fine stress changes **0.3447%**, closure **0.000405%** and tilt
**−0.000272%**. All sampled inner/outer free-edge radial moment, twisting
moment and radial shear residuals decrease. This supports numerical stability
of this specific comparison without asserting a physical error bound.
The finer combined gradient is 8.02e-10 N; each individual plate residual is
4.01e-10 N. Interface pressure ranges from 0 to 59.399 MPa, with zero-pressure
area 10.2885 mm². Its force is 709.052842 N and first moment 2292.108528 Nmm;
residuals are 2.73e-12 N and 6.75e-9 Nmm. No tensile interface pressure, added
friction or bonded stiffness is needed for this discrete witness.

| Existing immutable result | SHA-256 of checks.json |
| --- | --- |
| `rawlocal/stacked-washers/attempt01-coarse/` | `4a3d910be50adcdb813b36f5497bf2f4c5097fc9a2836ad3f0c1c04e293fdbd8` |
| `rawlocal/stacked-washers/attempt02-fine/` | `55f68197099a406ba1b7ab54b5d872096b9e574bacb61cceac4d65b14be8c4ef` |

Return these results to main as a completed fixed-demand sensitivity. No
additional washer count or hardware is adopted. Current joint demand and
actual washer material remain separate integration duties; this calculation
does not qualify the complete joint.

## Axial fit and procurement consequences

The [catalog quarter-inch washer](https://boltdepot.com/Product-Details?product=2994)
thickness range is 1.2954–2.0320 mm. One added washer at one end adds that
range to the exterior stack; adding one at both ends adds 2.5908–4.0640 mm.
It does not increase wood grip or washer bearing area. Actual washers can
have unequal thicknesses within that range, outside this identical-plate
mechanical comparison.

Use the existing [hardware engagement specification](../assembly-package/hardware-engagement.md).
An added head washer moves every timber interval outward from the under-head
datum and increases the necessary full-body LB by its thickness. An added
washer at either end moves the nut outward and changes the required full-form
thread window and overall length. Minimum nominal bolt length alone cannot
establish engagement. For the corrected top rail, doubling both exterior
washers would change the conditional purchasing arithmetic as follows:

| Quantity, corrected top rail only | Existing one washer at each end | Two at each end |
| --- | ---: | ---: |
| Total exterior washer thickness range (mm) | 2.5908–4.0640 | 5.1816–8.1280 |
| Minimum LB with maximum head-washer stack (mm) | 144.9070 | 146.9390 |
| Conservative full-form external thread window (mm) | 180.3908–187.6044 | 182.9816–191.6684 |
| Three-pitch overall-length option Lmin (mm) | 191.4144 | 195.4784 |

These are conditional dimensional calculations, not a new order, inspected
fit or bolt acceptance. The number of affected ends must be selected before
changing the 208-washer purchasing census. Neither this page nor its producer
changes that census or any CAD station.

## Limits and decision boundary

The additional washer can reduce each plate's bending demand without increasing
the annular wood bearing area. At fixed T, full-annulus mean wood pressure
remains T/A; actual pressure peaks can change as the contact redistributes.
Fixed bolt tension/moment also does not decrease merely because another washer
is included in this isolated local calculation.

Interface pressure is mapped in projected XY; finite surface offsets and
changed surface normals are omitted by the linear plate approximation.
The inherited shell proxy excludes through-thickness normal stress, contact
edge three-dimensional stress, plasticity, membrane/geometric nonlinearity,
preload, lateral bolt-force transfer and friction. Initial washer dish, burrs, eccentricity, unequal
thickness/material and finite interface compliance are unmodeled. The
coincident-field reduction applies only to the declared identical flat plate
hypothesis. Added stack thickness and changed end compliance have not been
coupled back to the bolts, joint or frame.

The supplier describes low-carbon steel but publishes no numerical yield
minimum. A ratio to 250 MPa is therefore a ratio to our assumed yield, not
a recommended capacity or catalog failure load. A local reduction below that
hypothesis would still need current simultaneous bolt-end demand, real bearing
faces and product material/installation evidence before it could close the
washer duty. Main owns that integration. Physical release remains HOLD.
