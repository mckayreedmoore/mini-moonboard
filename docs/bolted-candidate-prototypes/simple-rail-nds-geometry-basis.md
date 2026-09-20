# PB-01/PB-04: 2024 NDS bolt-geometry basis for the simple rail joint

Status: source and conditional arithmetic only. Neither grain-N cleat size
nor the four-bolt diagnostic has passed an installed-joint, member, or frame check.
The physical panel width is kerf-right. No drilling or buying is released.

## Access and edition boundary

AWC's [2024 NDS landing page](https://awc.org/resources/2024-nds/) offers
free view-only chapter PDFs. I read its official
[Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-–-Dowel-type-fasteners.pdf),
printed pp. 81, 92–99, and the official
[Chapter 11 PDF](https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf),
printed pp. 68–69. The source page's viewer could not be opened by the
web-reading tool (403); the linked public PDFs did serve through ordinary
read-only access. Chapter 12 is an encrypted view-only PDF that permitted
page reading without a password. No purchased PDF, manufacturer inquiry,
or redistributed standard is implied. Tables embedded as graphics can be
hard to extract, so the provision numbers and printed pages below matter.

The official
[March 2026 2024-NDS errata](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)
corrects cross-references from 3.4.3.3 to 3.4.4.1 in 11.1.2 and C12.5.1,
among other places. It does not replace Tables 12.5.1A–D. The official
[2024 Chapter 3 PDF](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
contains §3.4.4.1 at printed p. 21. An accessible
[2018 Chapter 12](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf)
has similar geometry tables, but no 2024 value below is inferred from 2018.
Do not mix 2018 provisions or supplement values into a 2024 check.

## Verified 2024 provisions for ordinary solid-wood bolts

- §12.1.2 defines edge distance perpendicular to grain, end distance along
  grain from a square-cut end, and a row as at least two fasteners aligned
  with load. Loaded and unloaded edges reverse with perpendicular force.
  Evaluate each wood member and each load direction, not just the cleat.
- §§12.1.3.2–12.1.3.4 require aligned bolt holes 1/32–1/16 in larger than
  the bolt, cut washers or at-least-equivalent metal bearing at head and
  nut, and the placement limits in Tables 12.5.1A–D. For a 9.525-mm bolt,
  the nominal hole interval is 10.31875–11.1125 mm. The current script
  and saved JSON use a 10.5-mm diagnostic bore inside that interval.
  This is still an analysis envelope, not a selected shop-hole diameter;
  actual hardware, fit and drilling instructions remain open.
- Table 12.5.1A: for perpendicular-to-grain loading and parallel-to-grain
  compression away from the end, end distance is at least 2D for the
  C_delta=0.5 tier and 4D for C_delta=1.0. For softwood parallel-to-grain
  tension toward the end, the tiers are 3.5D and 7D. At D=9.525 mm these
  are 19.05/38.1 mm and 33.3375/66.675 mm, respectively. Hardwoods use
  2.5D/5D for that last condition; DF-L is not a hardwood.
- Table 12.5.1B: spacing *within a row* is at least 3D. Parallel loading
  needs 4D for C_delta=1.0; perpendicular loading needs the spacing
  required for the attached members for C_delta=1.0. The 4×4 and 4×6
  single-bolt poses have no in-row spacing result. The separate 4×6
  four-bolt diagnostic has two bolts at each serial interface; its
  pitches still need signed-load and actual-row classification.
- Table 12.5.1C: for parallel-to-grain load, edge distance is 1.5D when
  the specified bearing-length ratio l/D is at most 6; above 6 it is the
  greater of 1.5D and half the row spacing. For perpendicular load, the
  loaded edge needs 4D and the unloaded edge 1.5D. At this D, 4D is
  38.1 mm and 1.5D is 14.2875 mm. Table notes define l/D from the lesser
  applicable main-member or side-member bearing length. Its footnote and
  §11.1.3 keep cross-grain tension and eccentric support in scope.
- Table 12.5.1D: between rows under parallel-to-grain load, minimum is
  1.5D. Under perpendicular load it is 2.5D for l/D at most 2,
  (5l+10D)/8 for 2<l/D<6, and 5D for l/D at least 6. The table again
  uses the lesser applicable main/side bearing-length ratio. §12.5.1.3
  also limits outermost cross-grain fastener separation to 5 in unless
  shrinkage-accommodating detailing is provided. Separate orthogonal
  serial interfaces are not automatically one ordinary fastener row.
- §12.5.1.2 assigns C_delta from the actual-to-full-value end-distance
  ratio, the specified angled-to-fastener shear-area ratio, or the
  actual-to-full-value in-row spacing ratio when the minimum tier is met.
  Use the smallest applicable factor for a fastener group and, where the
  section applies to a multi-shear connection, its shear planes. This
  adjusts lateral reference Z; it does not waive a minimum edge distance,
  replace member checks, or supply axial/washer resistance.
- §12.3.4 uses load-to-grain angle for each member's dowel bearing input;
  Table 12.3.1B uses the largest such angle in its yield-mode reduction.
  §12.3.3.4 specifically addresses a dowel axis parallel to main-member
  fibers; turning the cleat grain to N avoids that *cleat* axis condition
  in the trial but does not establish the final two-member calculation.
  §12.3.9 separates lateral load perpendicular to the bolt axis from its
  axial component; the latter needs adequate bearing, not borrowed Z.
- §§11.1.2, 11.1.3 and 11.2.2 require member stresses, eccentric
  cross-grain tension, and local multiple-fastener mechanics to be checked.
  Section 3.4.4.1 addresses shear at bolted connections in rectangular
  bending members using effective depth near the end. The 2026 erratum
  corrects its cross-reference in §11.1.2. Non-mandatory
  [2024 Appendix E](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf)
  gives net-section tension (§E.2), row tear-out (§E.3), and group
  tear-out (§E.4) methods. Apply only where their load and geometry
  assumptions hold, alongside splitting, washer and bolt checks.

## Provisional ratios at the grain-N single-bolt poses

The current [PB-01 geometry JSON](simple_rail_joint_comparison.json)
contains distinct actual CAD screens for a grain-N 4×4-sized cleat
(X width 88.9 mm, rail bolt X=44.45 mm from the butt) and a 4×6-sized
cleat (X width 139.7 mm, rail bolt X=70 mm from the butt). Each has one
trial bolt at each serial interface. The saved screens report face-contact,
full-bore, tool-envelope and 66 protected-axis diagnostics, not real
installed access or strength. These ratios use D=9.525 mm and nominal
centerline datums, not a computed allowable load or delivered stock size.

| Datum and conditional rule | 4×4 single pose | 4×6 single pose |
| --- | ---: | ---: |
| Rail grain-X end to bolt | 44.45 mm = 4.667D | 70 mm = 7.349D |
| If softwood tension bears toward that end, 7D full tier | 0.667 of 7D | 1.050 of 7D |
| If compression or perpendicular load, 4D full tier | 1.167 of 4D | 1.837 of 4D |

For the 4×4 rail, 44.45 mm exceeds the 3.5D minimum tension tier but
would give only a conditional C_delta=0.667 for *that end-distance mode*
if tension is toward the cut end. The actual 4×6 single pose clears 7D
by 3.325 mm nominally. Neither result classifies the actual same-case force,
wood cut tolerance, group distribution, or member shear.

Other single-pose grain-N datums remain unresolved even with 4×6 X width:

- The upright bolt is 50.159 mm = 5.266D from the cleat's near N-grain
  end. If softwood tension bears toward that square-cut end, its
  conditional end-distance C_delta is 50.159/66.675 = 0.752. A wider X
  4×6 single cleat does not change this N distance.
- The rail bore is 34.541 mm = 3.626D from one rail N edge. If that edge
  is loaded under perpendicular-to-grain action, it is 3.559 mm short of
  the 4D loaded-edge minimum. The opposite N edge is 105.159 mm away;
  force reversal could switch which edge is loaded. C_delta does not
  repair a short loaded edge under Table 12.5.1C.
- The upright bolt is centered 28.575 mm = 3D from either cleat T edge.
  Since T is perpendicular to cleat grain N, a T-directed force toward
  either edge would miss the 4D loaded-edge minimum by 9.525 mm. This
  remains so in the 4×6 single pose unless that geometry is redesigned.
- The two trial bolt centers are 55 mm apart in cleat N, but their axes
  and serial load-transfer interfaces differ. It is not a demonstrated
  Table 12.5.1B in-row or Table 12.5.1D row-spacing qualification.

## Separate 4×6 four-bolt diagnostic

The JSON also contains `cleat_grain_n_4x6_group`: two upright-to-cleat
and two rail-to-cleat trial bores. Its first N-front placement at
160 mm hit `main_lower_right`; the adjusted N-front datum is 209.841 mm.
The adjusted screen reports both contact faces, complete bores, no modeled
pairwise envelope intersections, and no intersection with the 66 protected
axes. Its status is `diagnostic_pose_only`, not a group capacity or installed
access check. Actual head/nut/socket stacks, tolerances and purchased
hardware remain unverified.

The upright pair is at cleat N=265/310 mm (45-mm pitch); the rail pair is
at X=70/110 mm (40-mm pitch), both at N=290 mm. If the corresponding
same-row parallel-load 4D full-value condition applies, 45/38.1=1.181
and 40/38.1=1.050 are only pitch ratios. In the cleat the second rail
bolt is 29.7 mm from its outer X edge, 8.4 mm short of 4D **if** that
edge is loaded perpendicular to cleat grain. The first upright bolt is
55.159 mm from the adjusted cleat N end, 11.516 mm short of 7D **if**
softwood tension bears toward that end. The JSON's conditional upright
host screen finds a 3.175-mm pitch shortfall if 7D front end, 4D rear
loaded edge, and 4D pitch must all apply simultaneously. None is yet a
same-case loading classification or complete 2024 NDS verdict.

No load direction, sign, delivered species/grade/moisture, bolt thread
location, washer resistance, contact distribution, member shear,
splitting, net section, or complete cleat resistance is established.
Neither a longer X width nor four trial bores is a joint pass.
