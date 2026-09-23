# Two-vertical-bolt principal/header CAD-only capacity screen

## Decision

The adapted wood-bearing and ideal washer references for the current
10.0076 × 16.002 mm STAFAST barrel and 18.47 mm washer exceed the best available
bolt-tension proxy. They are not adopted capacities or a complete-joint GO. The
demand is an old-topology proxy, not a fresh response for the new joint, and
several complete-joint modes remain unsupported. The finite disposition is
**EVIDENCE-BLOCKED** and no drilling or fabrication is released.

The design retains 66 purchased Hillman panel/kicker screws. Sixty-two axes stay
at their kerf-right coordinates. Four center kicker axes move from `X = -70/+70`
mm to `X = -20.6375/+17.4625` mm, keeping their `Y = -17.74375` mm and
`Z = 60/192` mm coordinates. They enter dedicated 38.1 × 88.9 mm shallow seam
backers with 19.05 mm nominal edge distance and 16.55 mm after the provisional
placement stack. The backers provide 9,102.09 mm² nominal panel contact each,
continue support along both kicker seam edges, and receive the full embedded
screw shafts; they receive no structural-frame credit. The former 2.092 mm
angled head pocket is absent: the new vertical bolts seat flat washers against
the underside of the full 38.1 mm header.

## Demand screen

Five authenticated, converged kerf-right principal/header interface wrenches
exist for the former ML24Z/contact topology. A12-forward did not converge. They
are not barrel-joint demands. As a bounded screening input, the total interface
wrenches were shifted to the new two-row group centroid. The exact combined-cut
principal/header face was split into 16 compression-only cells per side; both
bolts were tension-only. A linear program resolved `Fz`, `Mx`, and `My` without
friction. A separate equal-`Fy` witness resolved `Fx`, `Fy`, and `Mz` between
the bolt rows without assigning resistance.

- Default five-case maximum bolt-tension row action: 272.74 N.
- A1 0.1×/10× stiffness-sensitivity bolt-tension maximum: 301.49 N.
- A1 stiffness-sensitivity face-compression maximum: 921.80 N.
- Proxy `My` range: -5.750 to +10.589 kN·mm.
- Fresh new-topology cases: zero; A12-forward remains absent.

The exact net face is 5,024.764 mm². Its full reaction matrix has rank six;
collapsing the contact cells onto the bolt X axis removes the `My` path, and
collapsing the two bolt rows removes the `Mz` path. All 14 available side/case
proxy examples have a static equilibrium witness. The governing witness uses
220.48 N tension in each bolt, 1,054.70 N total face compression, and a 2.746
MPa maximum piecewise-uniform cell-average pressure. Its maximum adapted
reference ratio is 0.637. This proves a nominal static load-path topology, not
compatible force sharing, gap state, elastic peak pressure, stiffness, or
capacity. Available proxies reverse `My`, but do not reverse `Fz` or `Mx`.

Positive Z action on the principal is face compression: the proxy separately
reports the matching positive direct-contact component. Negative row action is
therefore bolt tension. Applying pullout and washer checks to the 921.80 N
compression action would be a sign error. The 301.49 N tension value is not a
qualified design demand or a proved upper bound.

## Wood barrel bearing

The calculation combines the current 2024 NDS Douglas Fir-Larch dowel-bearing
input, the dowel-nut limit-state separation in USDA FPL RP-586 Appendix C, and
the crossed-hole projected area used by Fabbri, Tullini, and Minghini. Their
published capacities are not transferred.

For the vertical bolt load, the principal grain angle is 40 degrees. With
`G = 0.50`, barrel diameter `d = 10.0076 mm`, body length `l = 16.002 mm`, and
crossed hole `d0 = 7.5 mm`:

```text
Fe,40 = 4521 psi
Aproj = d·l - π·d0²/4 = 115.963 mm²
Rd = 4·(1 + 0.25·40/90) = 4.444
Zref = Fe,40·Aproj/Rd = 813 N per barrel
```

An earlier projected-bounding-box calculation overstated the row distances.
Source-built polygon rays show that **both** barrel centers are only 36.551 mm
from the adverse grain end. The rows are staggered by 51.423 mm along grain and
61.284 mm across grain even though their global Y pitch is 80 mm. Applying the
simple `e/(7D)` distance sensitivity gives 0.52177 and reduces this reference
to 424 N. The actual angled-load `CΔ` still needs an accepted signed method;
0.52177 is a non-adopted scalar sensitivity, not a code factor. The reduced
reference is 1.41 times the 301 N row proxy and 1.92 times the 220 N governing
static-witness tension.

The smaller-area FPL-form sensitivity, `d(l-d0)`, with its historical divide-by-
four design derivation gives 663 N nominal and 346 N after the same distance
sensitivity, or 1.15 times the 301 N row proxy. It mixes the old parallel-grain
Appendix C form with current angled `Fe`; neither result is a codified
cross-dowel rating.

## Signed combined-cut paths

The source-built breakout map subtracts the candidate service passage, all
eight panel screw axes in each principal, all ten header kicker screw axes, and
the four candidate cuts per host. Each resulting host is one valid solid.
Actual-face ray and thin-slab queries give, per principal barrel:

- 2,716.49 mm² extrapolated nominal two-plane path area;
- 1.686 kN unadjusted 180 psi Appendix E row-tear-out reference;
- 2,955.65 mm² rear and 5,031.77 mm² forward grain-normal net sections;
- 1,245.16 mm² mapped center splitting plane; and
- 31.55 mm minimum raw-face ligament after barrel radius; and
- 26.03 mm minimum barrel-bore gap to the reduced right-principal service bore.

These are geometry and reference values only. The Appendix E expression is a
parallel-grain local-stress method, while this barrel action is 40 degrees to
grain and the receiver is blind and partial-width. No adopted resistance exists
for the mapped tension-perpendicular splitting plane. Group tear-out and adverse
tolerances remain unresolved. The executable map is
[`scripts/owner_barrel_vertical_center_breakout.py`](../../scripts/owner_barrel_vertical_center_breakout.py).

## Header washer and bolt

Using the selected controlled washer's minimum OD and maximum ID gives a
213.628 mm² contact annulus. `625 psi × area`, with no bearing-area increase,
is 920.57 N per bolt, or 3.05 times the tension proxy before washer dishing,
seat defects, tolerances, or other adjustments.

The selected Grade 5 bolt's constituent proof load is 12.02 kN. Bolt tension is
not governing this screen, but combined tension, shear, and bending have not
been qualified.

## What online evidence can and cannot close

Online methods can close much of the calculation:

- [USDA FPL RP-586](https://research.fs.usda.gov/download/treesearch/6003.pdf)
  separates dowel-nut wood bearing, net tension, and two-plane shear. Its tested
  capacity is for a much larger confined peeler-core joint and is not reused.
- [AWC 2024 NDS resources](https://awc.org/resources/2024-nds/) provide current
  wood bearing, geometry, net-section, row tear-out, and group tear-out rules.
- [Fabbri et al.](https://iris.unife.it/retrieve/aaead297-7bcb-4893-b331-847d56b3752f/Fabbri_Tullini_Minghini_2022%20-%20post-print.pdf)
  provide a direct crossed-dowel projected-area and stiffness model.
- [NASA RP-1228](https://ntrs.nasa.gov/api/citations/19900009424/downloads/19900009424.pdf)
  and the [ECSS threaded-fastener handbook](https://ecss.nl/wp-content/uploads/2023/02/ECSS-E-HB-32-23A-Rev.1%286February2023%29.pdf)
  provide thread-stripping equations once controlled female-thread dimensions
  and material strength exist.
- [Rothoblaas DADO SIMPLEX](https://www.rothoblaas.com/attachments/298664-product-550/07_SIMPLEX_USA_EN.pdf)
  proves that a manufacturer-rated structural cross-dowel route exists. Its
  22 mm body, 24 mm bore, 54 mm length, and 155 mm minimum end distance do not
  fit this 38.1 mm principal without major redesign.

No online source found a structural rating, controlled steel minimum, internal
thread class, usable complete-thread interval, or proof load for the selected
STAFAST part. “Cold rolled steel” is not a material grade. Aerospace barrel
nuts publish strong controlled axial ratings, but their fine threads, larger
bores, and metal-joint installation geometry are not drop-in timber ratings.

STAFAST's publicly posted 2016 catalog gives a generic ±0.016-inch decimal
tolerance. It can support a sensitivity only; the catalog directs users to
request a current print. With that
provisional envelope and the 301.494 N service-only row proxy, a controlled
whole-barrel design rating would need to exceed
`installation preload + gamma × 301.494 N`. NASA's tapped-hole expression gives
a required female-thread shear strength of only `7.380 × gamma MPa`, while a
non-validated lobe sensitivity gives `18.579 × gamma MPa` average shear and
`96.126 × gamma × Kt MPa` yield. These modest numbers show metal feasibility is
plausible; they do not close unknown preload, stress concentration, slot,
thread-flank loading, material minimums, or complete-part rating.

The executable sensitivity is
[`scripts/owner_barrel_metal_threshold.py`](../../scripts/owner_barrel_metal_threshold.py).

## Remaining gates

Before this joint can receive a conditional analytical GO:

1. Extend the nominal signed map to adverse drill, fit, and stock tolerances;
   enumerate group tear-out and adopt or reject a splitting resistance route.
2. Bound face-contact/fastener compatibility and stiffness; current work proves
   only static `My` topology under available proxy signs.
3. Obtain controlled STAFAST geometry, material, thread, wall, and proof
   evidence, or select an alternate barrel, then rerun the reference screens.
4. Control the current washer, seat, flexure, and tolerances; change washer size
   only if that check fails.
5. Build a bounded contact/fastener stiffness model, then obtain six fresh
   signed responses for the actual 48-barrel topology.

The executable calculation is
[`scripts/owner_barrel_vertical_center_capacity.py`](../../scripts/owner_barrel_vertical_center_capacity.py).
The signed contact calculation is
[`scripts/owner_barrel_vertical_center_contact_screen.py`](../../scripts/owner_barrel_vertical_center_contact_screen.py).
The follow-on compatibility fixture and finite decision are
[`owner-barrel-vertical-center-joint-fixture.md`](owner-barrel-vertical-center-joint-fixture.md).
The ordinary-retail ABN trial and updated governing screen are
[`owner-barrel-abn-governing-screen.md`](owner-barrel-abn-governing-screen.md).
All three stay fail-closed and report every unsupported mode rather than
substituting contact area or collision clearance for strength.
