# PB01 cleat gross-section stress screen

Status: **conditional diagnostic only; no cleat or joint pass.** Run
`uv run python -m scripts.simple_pb01_cleat_gross_section_screen` from this
repository to print all 20 cut-side records and their maxima as JSON. The
[script](../../scripts/simple_pb01_cleat_gross_section_screen.py) writes no files
and does not run a solver.

The input is the preserved
[four-contact a12-left hybrid bundle](pb01-quarter-contact4-a12left-evidence.tar.gz).
The existing [extractor](../../scripts/simple_pb01_hybrid_local_actions.py)
authenticates the fixed archive SHA-256
`fc298a3a481437a5dc9f24c02bc9a234458074c2ffcba6753fe33875f4805546`,
report SHA-256
`c10b2b2d1b979fe82ffc5bca31c60e374650610e4c44245e8e56431c7b0c4918`,
source snapshots, final-cycle artifacts, case/pose, connector inventory, and
equilibrium before the screen reads `member_section_demands.base_cleat_pb01`.
The screen also verifies the report digest and modeled section geometry.

Local section `u` is global X; `v` is the other transverse axis; the 300 mm
longitudinal axis follows cleat grain. The report models a 139.7 mm width in
`u` and 57.15 mm depth in `v`, with gross area 7,983.855 mm². For that ideal
unbored rectangle, `S_u = b d²/6 = 76,046.219 mm³` and
`S_v = d b²/6 = 185,890.757 mm³`. The script calculates signed isolated
elastic components `N/A`, `M_u/S_u`, `M_v/S_v`, `3V_u/(2A)`, and `3V_v/(2A)`.
One N/mm² equals one MPa. The shear expressions are rectangular-section
peak values for one shear direction at a time. Both sides of a concentrated
station load are retained as separate records.

At each **same cut**, the script also takes the four rectangle-corner
extremes of `N/A ± M_u/S_u ± M_v/S_v` to report tensile and compressive
normal stress, and combines the orthogonal transverse-shear components at
the section center by Euclidean magnitude. These remain gross elastic
stress screens without torsion or a failure interaction.

| Maximum isolated component | Magnitude | Station along grain | Include station loads? |
| --- | ---: | ---: | --- |
| Axial tension | 0.000000003993 MPa | 0 mm | No |
| Axial compression | 0.001135 MPa | 100.160 mm | No |
| Bending about `u` | 0.006937 MPa | 100.160 mm | Yes |
| Bending about `v` | 0.002789 MPa | 80.160 mm | No |
| Shear from `V_u`, peak | 0.002367 MPa | 80.160 mm | No |
| Shear from `V_v`, peak | 0.003438 MPa | 80.160 mm | No |
| Same-cut corner normal tension | 0.007654 MPa | 100.160 mm | Yes |
| Same-cut corner normal compression | 0.009087 MPa | 100.160 mm | Yes |
| Same-cut center transverse shear | 0.004174 MPa | 80.160 mm | No |
| Torsion action, not stress | 1,689.448 N·mm | 80.160 mm | No |

The tiny reported tension is residual scale, not evidence of a meaningful
tension demand. Maxima can occur at different cuts; only the expressly
same-cut rows combine simultaneous components. Torsion is nonzero, but this
screen does
not calculate torsional stress or a bending/shear/axial/torsion interaction.
The source report's `retained_area_fraction = 1.0` means its section records
are gross: the four modeled bolt bores are not removed. It does not establish
net area, a critical drilled section, local bearing, splitting, or connection
resistance.

The [AWC 2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/)
Table 4A publishes species/grade/size reference design values for visually
graded dimension lumber, with stated dry-service and normal-duration basis and
adjustment rules. No Table 4A value is applied here: the delivered PB01 cleat
has no verified DF-L No. 2 grade mark or established adjustment applicability.
The [2024 NDS Appendix E][appendix-e]
E.2/E.3/E.4 local-stress methods address specified parallel-to-grain
tension/shear cases, not this gross flexure/shear screen.
The JSON therefore sets `reference_design_values_mpa`,
`net_section_stress_mpa`, `combined_stress_mpa`, `capacity_n`, `utilization`,
and `complete_joint_pass` to `null`; each cut also has null torsional stress.

[appendix-e]: https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf

The source is one numerically accepted **diagnostic** hybrid a12-left run.
Its other 23 stations retain old ML24Z/SDS proxy topology, and the PB01 bolt
and contact springs are provisional. These section actions are not qualified
full V4 or six-case design demands. A defensible cleat check still needs
verified wood and load-duration/service basis, bore-aware critical sections,
torsion and full strength interaction, and the complete bolt/contact joint
load path.
