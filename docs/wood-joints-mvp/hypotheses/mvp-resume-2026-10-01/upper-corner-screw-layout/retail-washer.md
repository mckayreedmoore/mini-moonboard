# Retail thick washer at the current upper-right bolt end

**Finite local model comparison. No hardware adoption or physical test.**

## Retail choice

Choose **Lowe's Hillman 885522, item 755754**, zinc-plated steel, nominal
quarter-inch size and one-inch outside diameter. Online listings checked
October 2, 2026:

| Retail option | Listed dimensions | Listed price | Assessment |
| --- | --- | --- | --- |
| [Lowe's Hillman 885522](https://www.lowes.com/pd/Hillman-4-Count-Pack-1-4-in-x-1-in-Zinc-plated-Fender-Washer/999995992) | Quarter-inch size, 1-inch OD; thickness fields conflict: 0.13 inch, 0.125 inch, and 2.5 mm | $2.48 per four | Selected for its greater listed thickness and modest footprint |
| [Home Depot Everbilt 804796](https://www.homedepot.com/p/Everbilt-1-4-in-x-1-1-4-in-Zinc-Plated-Fender-Washer-804796/204632767) | Quarter-inch size, 1.25-inch OD; listed under the retailer's [0.065-inch thickness filter](https://www.homedepot.com/b/Hardware-Fasteners-Washers-Fender-Washers/Everbilt/Fender-Washer/0065-in/N-5yc1vZc283Z402Z1z0ztd5Z1z23290) | $0.21 each | Thinner, with a larger footprint |

The Lowe's thickness fields correspond to **3.302, 3.175 and 2.5 mm**. Use
**2.5 mm**, the lowest listed nominal, for this one calculation. It is not a
guaranteed minimum or a measured dimension. The quarter-inch label may describe
bolt size; it does not establish an exact bore. Store inventory was not checked.
Neither listing supplies a numerical steel yield guarantee for this calculation.

## One declared model

The [producer](retail-washer.py) reuses the frozen single-washer plate/contact
helper without changing its source. It substitutes one washer with
**ID 8.3058 mm, OD 25.4 mm, thickness 2.5 mm**. The ID is the existing generic
quarter-inch USS hypothesis, expressly not a Hillman product fact or guaranteed
upper bound. A radius-5-mm flat head footprint leaves a nominal 0.8471-mm radial
pressing band. Actual washer/head bore, chamfer and fillet fit remain unmeasured.

The current first-order source is pinned at
`b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe`.
Its `k12-right`, right-side, `base_rail_top` host end of
`top_outer/clip_single_top_right_2/rail_1` supplies simultaneous
**707.883638 N tension and 2432.068387 Nmm moment**. This same record has the
largest tension and moment among the 48 current rail-end records. That is a
demand witness, not proof of maximum washer stress across all states.

Use the existing hypotheses E=200,000 MPa, nu=0.30, Fy=250 MPa,
Kwood=20 MPa/mm and Khead=10,000 MPa/mm. Head and wood contacts carry compression
only; both radial washer edges are free. The original known-answer full-face
100 N / zero-moment coupon and rigid-mode diagnostics accompany each run.
The [plate energy derivation](https://docu.ngsolve.org/ngs24/SaS/plates_derivation.html)
supports the inherited bending/shear formulation; it supplies no product rating.

### Saved finished-face support

The current member's finished STEP binding matches the frozen surface register.
At `base_rail_top/facet012`, the producer checks the four outer lines and all
eight circular inner wires against the current host seat. Its own timber bore
radius is 3.75 mm, smaller than the declared washer opening radius 4.1529 mm.
No foundation is credited over that bore.

The 12.7-mm outer radius remains **32.75 mm inside the nearest timber edge**
and **16.55 mm clear of the nearest other bore**. The declared backed annulus
is 452.525755 mm². This is support on the saved concentric geometry, not an
inspection or a guarantee under lateral shift, tilt, or changed installation.
No CAD reconstruction or frame solve was performed for this support audit.

## Frozen execution

Producer SHA-256:
`894608d5abc879e3d679e8149cbf181c0cda224f2fbb164a0cbdb06f882e246f`.
Read-only preflight authenticated 24 source pins and checked the finished-face
support. Ruff passes. Main completed the two serialized mechanics runs below
on October 2, 2026. They are reproduction records, not rerun requests; their
existing output directories remain immutable. No additional washer dimensions,
material sweep or refinement is planned.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/retail-washer.py --resolution coarse --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/retail-washer/attempt01-coarse
```

After coarse completes:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/retail-washer.py --resolution fine --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/retail-washer/attempt02-fine
```

Gradient, force and moment tolerances remain 1e-4 N, 0.001 N and 0.02 Nmm.
The earlier unexecuted 6.35-mm-ID draft is preserved as an ignored snapshot;
it is not the selected hypothesis and is not scheduled for execution.

## Result

Both runs completed without a numerical stop. Both known-answer coupons passed.
Independent read-only authentication verified all **24 source pins and four
output pins per run**, including the exact producer snapshot, fields and result.

| Same current simultaneous T/M | Coarse | Fine |
| --- | ---: | ---: |
| Peak elastic stress proxy (MPa) | 206.790376 | 207.205343 |
| Proxy / assumed 250 MPa yield | 0.827162 | 0.828821 |
| Percentage of assumed yield | 82.7162% | 82.8821% |
| Head closure (mm) | 0.086825985 | 0.086828099 |
| Head tilt magnitude (rad) | 0.008643027 | 0.008642510 |
| Peak wood contact pressure (MPa) | 2.959379 | 2.962580 |
| Full-annulus mean wood pressure (MPa) | 1.564295 | 1.564295 |
| Peak head contact pressure (MPa) | 103.328098 | 103.739933 |

The fine stress proxy is **17.1179% below the assumed yield**. The modeled
thicker, wider washer therefore clears this specific local comparison and is
a reasonable candidate for the washer change. This percentage is not a safety
factor or percentage of a manufacturer-rated allowable load. The head pressure
and wood pressure are recovered demands, not independent product qualifications.

Coarse-to-fine stress changes **0.2007%**, closure **0.00243%**, and tilt
**−0.00597%**. All six sampled free-edge radial moment, twisting moment and
radial shear residual maxima decrease. The stress peak remains the inner free
circle at x=4.1529 mm, y=0, predominantly hoop bending: fine face stresses are
[0.008665, −207.201011, 0] MPa. Fine combined gradient is 2.53e-10 N; contact
force residuals are at most 2.62e-12 N and moment residuals 7.54e-9 Nmm.
The coupon recovers uniform pressure 0.220981897 MPa, w=0.011049095 mm,
h=0.011071193 mm and zero bending/shear energy at its known answer. These checks
support consistency of the finite numerical comparison, not a physical error
bound. No further refinement is needed for this finite question.

| Immutable result | SHA-256 of checks.json |
| --- | --- |
| `rawlocal/retail-washer/attempt01-coarse/` | `ffac301bbdc6f9c3116713d657a2551949dc596db3869d8c3bf35b85449c7011` |
| `rawlocal/retail-washer/attempt02-fine/` | `c920d85bfdab7a9cbc802a0e4f79f817e2ac68fe8dfaf4ab1f50aa31d8dec5ae` |

The earlier ordinary/stacked washer results used a different frozen T/M and
must not be presented as a controlled same-load percentage reduction against
this run. This investigation is complete. Main retains integration and hardware
adoption; actual product capacity, other bolt ends and complete-joint acceptance
are not established by this result.

## Axial fit consequence

Replacing one existing catalog washer, whose listed thickness is
1.2954–2.0320 mm, with this **2.5-mm hypothesis** adds **0.4680–1.2046 mm**
at that end. Replacing both exterior washers adds **0.9360–2.4092 mm** total.
The wood grip does not change. A thicker head washer shifts the timber intervals
from the bolt's under-head datum; either thicker washer shifts the nut outward.

For two 2.5-mm exterior washers on the corrected 177.8-mm top-rail grip,
the existing [engagement arithmetic](../assembly-package/hardware-engagement.md)
gives minimum full-body LB **145.375 mm**, conservative full-form thread window
**182.8000–188.5404 mm**, and three-pitch overall-length option Lmin
**192.3504 mm**. These are conditional dimensions, not a hardware order or
delivered-bolt acceptance. They use the modeled thickness rather than every
contradictory retail thickness; actual dimensions must govern any later fit.
This local host-end check changes no bolt, purchasing census or CAD station.

## Interpretation limits

This is a comparison to assumed 250 MPa yield, not recommended product capacity
or measured failure load. Plate mechanics omit contact-edge three-dimensional
stress, through-thickness normal stress, plasticity, preload, friction, membrane
action and geometric nonlinearity. The thicker plate has a smaller span/thickness
ratio than the original thin washer; the inherited method remains a screen.
The current simultaneous bolt force/moment is prescribed, with no feedback of
changed washer stiffness or thickness into joint/frame response. A favorable
local result addresses this washer hypothesis, not every bolt end or complete
joint acceptance. Actual part dimensions and material remain distinct from
numerical convergence.
