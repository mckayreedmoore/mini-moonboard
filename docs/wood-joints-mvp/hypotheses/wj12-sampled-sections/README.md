# WJ12 sampled finished sections

Status: capacity-independent geometry diagnostic, 2026-09-24. The
[report](sections.json) samples exact zero-thickness planes in the
[twelve-duty composition](../wj12-integrated-static/README.md). Every result
belongs to its named plane; none is a whole-member minimum or a strength,
splitting, bearing, block-shear, or load-path acceptance.

| Feature and sample | Matching stock area, mm² | Finished area, mm² |
|---|---:|---:|
| Right compact rear bridge, grain midpoint | 3387.090000 | 3375.577849 |
| Same bridge, each of four sampled bolt stations | 3387.090000 | 3089.827849 |
| Upper right G7 cleat, retained crosscut face | 7903.210000 | 7903.210000 |
| Same cleat, middle sampled bolt station | 7903.210000 | 6569.710000 |
| Center upper right cleat, first sampled bolt station | 6547.303961 | 5789.061272 |
| Left backer, midpoint of bottom counterbores | 7903.210000 | 7274.891469 |
| Right backer, midpoint of bottom counterbores | 7903.210000 | 7274.891469 |
| Each backer, 3 mm above counterbore floor | 7903.210000 | 7819.502264 |

The report also records every sampled local bound, plane origin and basis,
and intersecting candidate-bore/purchased-screw cutter ID. The two other G7
bolt-plane areas are 7236.460000 mm². The center cleat's other bolt-plane
areas are 6098.278547 and 5789.061174 mm²; its oblique stock ends mean that
matching stock areas differ by station. These numbers are geometry measures,
not allowable resisting areas or a critical-section selection.

The G7 reference separates the full 119.7 mm stock length from its shortened
86.9 mm family input. A sample in the removed 32.8 mm portion has zero
finished area by construction. The center wire-relief reference uses the
same end-cut primitive before the relief; its T = 32 mm sample is entirely
in the removed tip and also has zero finished area. Neither zero is a
failure verdict or the minimum section carrying a load.

Both backers are sampled independently. Equal areas at these transverse
planes do not establish mirrored whole-part geometry: their finished hole
layouts differ. The helper uses each actual composed part and its own bore
IDs, including redirected fixed-axis screw cuts.

Parent ran the final helper on the retained corrected composition in 0.29 s
and checked its producer hash after execution. The report binds the exact
composition and static-diagnostic JSON hashes, source/family fingerprints,
and helper dependencies. The [manifest](sha256.json) binds the report and
exact [producer snapshot](sections.py.snapshot). Four focused tests cover
analytic box/bore areas, absent material, missing inputs, and distinct
left/right backer inputs. No native solve, capacity calculation, physical
inspection, or release is represented.

These samples support the next mechanics review. Complete critical-section
selection, stresses, cut effects, connection resistance, and current joint
demands remain open; the required native case execution is not authorized.
