# Conditional AC plywood material basis

Verified September 11, 2026. This note does not change the frozen model or solver
batch. The identified purchase remains Roseburg AC fir, 23/32 CAT, PS1-09;
see [product verification](round-material-led-verification.md).

## Published family values exist

APA D510C (2012), page 3, explicitly covers PS1-09. Section 4.2 provides
conservative directional minima across permitted constructions; exact 5- versus
7-ply identification is therefore unnecessary for a conditional family check.
Table 9, printed pages 23–25, gives these Group 1 AC 23/32 values:

| Property | Parallel | Perpendicular | Units |
|---|---:|---:|---|
| EI | 320000 | 90500 | lbf·in²/ft width |
| FbS | 775 | 455 | lbf·in/ft width |
| FtA | 5100 | 3400 | lbf/ft width |
| FcA | 4800 | 2900 | lbf/ft width |
| EA | 5100000 | 3150000 | lbf/ft width |
| Fs(Ib/Q) | 350 | 350 | lbf/ft width |
| Gv tv | 50500 | 50500 | lbf/in panel depth |
| Fv tv | 105 | 105 | lbf/in resisting length |

Table 10, page 26, supplies Group 2/3/4 multipliers:

| Property | Group 2 | Group 3 | Group 4 |
|---|---:|---:|---:|
| EI, EA, Gv tv | .83 | .67 | .56 |
| FbS, FtA | .70 | .70 | .67 |
| FcA | .73 | .65 | .61 |
| Fs(Ib/Q) | 1 | 1 | 1 |
| Fv tv | .74 | .74 | .68 |

These are certification-dependent family values, not a measured sheet's elastic
constants. Group 4 provides a conservative conditional envelope over Groups
1–4, without substituting Structural I.
[APA-authored D510C, 2012](https://design.medeek.com/resources/structural/D510C_2012.pdf).

## Applicability and shear meaning

The corresponding 2020 tables are 10 and 11. Section 2.2.1 uses face/back
species rules, including a limited sanded-panel exception; the word “fir” alone
does not determine panel group. Preserve original face-grain axes when cutting.
Section 4.4 distinguishes rolling/interlaminar shear Fs(Ib/Q) from membrane
shear Fv tv and membrane rigidity Gv tv. The latter is **not** transverse shell
Gxz or Gyz. Apparent EI already includes the specified shear-deflection
allowance. Section 4.5 requires dry service below 16% moisture; wet-service
strength/stiffness factors are .75/.85. Impact duration increases do not apply.
Narrow life-safety strips need the size adjustment, and deep in-plane shear
members need the stated buckling consideration. These tables provide no
countersunk machine-head or threaded-insert resistance qualification.
[APA D510F, 2020, §§2.2.1, 4.4–4.5](https://wood.tcaup.umich.edu/lectures/2021/D510.pdf).

Use the 2012 edition for the identified PS1-09 basis; the 2020 edition's
introduction instead identifies PS1-19/PS2-18.

## Computable stiffness inputs and model limits

The following are unit conversions and our diagnostic calculations, using
1 lbf = 4.4482216152605 N and nominal t = 18.25625 mm:

| Quantity per unit width | Parallel | Perpendicular |
|---|---:|---:|
| Apparent EI/b, N·mm | 3012928.774 | 852093.919 |
| EA/b, N/mm | 74428.905 | 45970.794 |
| Bending-equivalent E = 12(EI/b)/t³, MPa | 5942.037 | 1680.482 |
| Axial-equivalent E = (EA/b)/t, MPa | 4076.900 | 2518.085 |

Gv tv = 8843.905 N/mm, giving membrane Gxy = 484.432 MPa. Multiply these
stiffness quantities by .56 for the Group 4 sensitivity, and additionally by
.85 for wet service. The selected species and service multipliers must also be
applied separately to resistance, not inferred from stiffness.

The bending-equivalent and axial-equivalent E pairs disagree because the panel
is layered. A single homogeneous orthotropic shell cannot reproduce both
pairs simultaneously. Neither pair makes the present isotropic E = 7000 MPa
model a plywood qualification. A diagnostic probe can use both fits, both
sheet-axis orientations if not yet recorded, and the conditional group/service
cases. Those probes are sensitivity cases, not a proven bound on redistributed
connection forces. Full layered/section response still needs a defensible
coupling and transverse-shear model; the table supplies neither Poisson
coupling nor Gxz/Gyz. No actual-lot elastic measurement is inherently required
to use the published family resistance minima.
