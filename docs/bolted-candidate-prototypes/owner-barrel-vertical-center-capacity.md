# Two-vertical-bolt principal/header CAD-only capacity screen

## Decision

The adapted wood-bearing and ideal washer references for the current
10.0076 × 16.002 mm STAFAST barrel and 18.47 mm washer exceed the best available
bolt-tension proxy. They are not adopted capacities or a complete-joint GO. The
demand is an old-topology proxy, not a fresh response for the new joint, and
several complete-joint modes remain unsupported. The finite disposition is
**EVIDENCE-BLOCKED** and no drilling or fabrication is released.

All 66 panel/kicker screw axes remain at their kerf-right coordinates. The four
center kicker axes receive new stepped backing; none move. The former 2.092 mm
angled head pocket is absent: the new vertical bolts seat flat washers against
the underside of the full 38.1 mm header.

## Demand screen

Five authenticated, converged kerf-right principal/header interface wrenches
exist for the former ML24Z/contact topology. A12-forward did not converge. They
are not barrel-joint demands. As a bounded screening input, the total interface
wrenches were shifted to the new two-row group centroid and all `Fz/Mx` and
`Fx/Mz` were assigned to rows 80 mm apart. `Fy` was split equally. The two
collinear vertical bolts cannot create `My`, so that component remains assigned
to face contact or another as-yet-unproved restraint.

- Default five-case maximum bolt-tension row action: 272.74 N.
- A1 0.1×/10× stiffness-sensitivity bolt-tension maximum: 301.49 N.
- A1 stiffness-sensitivity face-compression maximum: 921.80 N.
- Maximum unclosed `My` in those proxies: 10.589 kN·mm.
- Fresh new-topology cases: zero; A12-forward remains absent.

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

The rear row is only 45.04 mm, or 4.50 barrel diameters, from the grain end.
Applying the simple `e/(7D)` distance sensitivity gives 0.643 and reduces this
reference to 523 N. The actual angled-load `CΔ` needs the signed shear area on
the adverse combined-cut solid; 0.643 is a non-adopted scalar sensitivity, not
an established conservative bound or adopted code factor. The reduced reference
is 1.73 times the 301 N tension proxy.

The smaller-area FPL-form sensitivity, `d(l-d0)`, with its historical divide-by-
four design derivation gives 663 N nominal and 426 N after the same distance
sensitivity, or 1.41 times the tension proxy. It mixes the old parallel-grain
Appendix C form with current angled `Fe`; neither result is a codified
cross-dowel rating.

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

## Remaining gates

Before this joint can receive a conditional analytical GO:

1. Map both signed, two-plane shear/block paths and splitting paths on the
   actual combined-cut solids, including drill and stock tolerances.
2. Add a face-contact or other verified path for `My`; the two bolt centers are
   collinear in Y and cannot resist that axis alone.
3. Obtain controlled STAFAST geometry, material, thread, wall, and proof
   evidence, or select an alternate barrel, then rerun the reference screens.
4. Control the current washer, seat, flexure, and tolerances; change washer size
   only if that check fails.
5. Build a bounded contact/fastener stiffness model, then obtain six fresh
   signed responses for the actual 48-barrel topology.

The executable calculation is
[`scripts/owner_barrel_vertical_center_capacity.py`](../../scripts/owner_barrel_vertical_center_capacity.py).
It stays fail-closed and reports every unsupported mode rather than substituting
contact area or collision clearance for strength.
