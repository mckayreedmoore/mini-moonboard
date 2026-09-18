# Provisional material assumptions

Research date: 2026-09-11. Independent verification handoff; no whole-board load
rating. Published inputs below remain separate from proposed calculation choices.
No FE inputs or archived reference JSON changed.

## Published lumber basis — AWC24

[2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/),
[official Chapter 4](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf),
Table 4A, printed pp. 32/34 (PDF pp. 2/4).

US Douglas Fir–Larch No. 2 dimension lumber, normal duration, dry service:
E=1,600,000 psi; Emin=580,000 psi; Fb=900 psi; Ft=575 psi;
Fv=180 psi; Fc⊥=625 psi; Fc∥=1,350 psi; specific gravity=.50.
These are reference values, not fully adjusted capacities.
For nominal 2×6, size factors Fb/Ft/Fc∥=1.3/1.3/1.1;
2×8=1.2/1.2/1.05; 2×10=1.1/1.1/1.0.
E addresses deflection; Emin addresses stability.
Verify actual species/grade, moisture, treatment, orientation, net section,
load duration, bearing and stability adjustments using the matching NDS edition.

## Published plywood basis — APA20

[APA D510 official listing](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/);
[APA-authored D510F (2020), university-hosted PDF](https://wood.tcaup.umich.edu/lectures/2021/D510.pdf).
Table 9, printed pp. 25–27 (PDF pp. 29–31); §§4.4–4.5; Table 14.

Selected basis: PS 1 Structural I plywood, 23/32 category, 48/24 rating.
Values include Structural I multipliers; pairs mean parallel/perpendicular
strength axis. Table 14's five-ply column covers at least five layers.

| Property | Four layers | At least five layers |
| --- | --- | --- |
| EI, lbf·in²/ft | 440,000 / 97,500 | 440,000 / 146,400 |
| EA, lbf/ft | 5,850,000 / 5,000,000 | Same |
| FbS, lbf·in/ft | 930 / 378 | 1,000 / 607.5 |
| Rolling-shear Fs(Ib/Q), lbf/ft | 420 / 1,015 | 455 / 250 |
| Membrane-shear Gv tv, lbf/in | 52,650 | 51,150 |

Dry service means moisture below 16%. Wet-service strength/stiffness
multipliers are .75/.85. Panel impact-duration increases are prohibited.
Gv tv describes diaphragm shear, not transverse shell shear stiffness.
These section capacities require compatible resultants; concentrated loads,
unsupported edges, buckling and connections need separate checks.

## Research ratios — FPL21

[USDA Wood Handbook, FPL–GTR–282 (2021)](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/fpl_gtr282.pdf),
Table 5–1, printed p. 5–2 (PDF p. 118): Douglas-fir clear-wood ratios near
12% moisture are ET/EL=.050, ER/EL=.068, GLR/EL=.064,
GLT/EL=.078, GRT/EL=.007. They are not graded-lumber design values.
The text distinguishes apparent bending E, which includes shear deflection,
from axial E; avoid counting shear compliance twice.

## Analyst-selected next steps

Use the appropriate published layup branch after checking purchased sheets.
Pending identification, screen both branches: picking only the lower bending
stiffness does not bound every connection force. Proposed stiffness sensitivity
multipliers .7/1/1.3 are analyst choices, not published uncertainty bounds.
Do not increase allowable capacities when increasing assumed stiffness.

For a reduced panel model, calibrate membrane and bending behavior separately.
Do not invent missing transverse shear moduli, Poisson ratios or coupling terms
for a homogeneous orthotropic material. Any timber model using the FPL ratios
scaled to NDS E is an explicit mixed-source proxy requiring verification.

The reviewer should transcribe the cited tables independently, verify purchased
stamps and installed axes, and check units and all applicable adjustments.
Current local stress peaks near the assumed hold patch cannot establish a panel
failure or justify thicker sheets. Hold attachment, joint slip, frame stability
and floor contact remain separate unresolved parts of the board rating.
