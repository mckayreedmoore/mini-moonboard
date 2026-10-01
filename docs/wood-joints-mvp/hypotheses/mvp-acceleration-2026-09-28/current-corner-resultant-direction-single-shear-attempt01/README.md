# BG001/BG045 resultant-direction single-bolt references

This packet checks whether the pinned single-shear helpers can compare the
accepted a12-rear lateral **resultant** for each BG001 and BG045 bolt against
an NDS lateral-yield reference evaluated in that direction. They can, using
the existing `dfl_dowel_bearing_psi` angle helper and the six-mode single-shear
wrapper. No new strength equation or summed component capacity is introduced.

For each connected wood member, the producer computes
`theta = acos(abs(unit_force · unit_source_proposed_grain))`. It sends each
member's angle-interpolated `Fe` to the pinned single-shear calculation and
uses the existing maximum-member-angle reduction term. The existing DF-L No. 2,
SG 0.50 scenario endpoints remain exactly 5600 psi parallel and 4450 psi
perpendicular; the helper reproduces both at 0° and 90°. Intermediate values
are angle interpolation within those same endpoints.

| Group / bolt | Main and side load-to-grain angles | Resultant demand | Governing conditional reference | Demand / reference |
| --- | --- | ---: | ---: | ---: |
| BG001 post 1 | 30.092° / 30.092° | 301.657 N | Mode IV, 712.070 N | 0.42363 |
| BG001 post 2 | 39.522° / 39.522° | 335.061 N | Mode IV, 682.661 N | 0.49082 |
| BG045 header 1 | inner block 90.000° / header 8.960° | 90.116 N | Mode IV, 401.080 N after Ceg | 0.22468 |
| BG045 header 2 | inner block 90.000° / header 13.353° | 24.946 N | Mode IV, 400.416 N after Ceg | 0.06230 |

All six lateral modes are retained for every bolt in
`resultant-direction-screen.json`. The BG001 assumptions remain a smooth
full-body 1/4-in bolt, 38.1 mm in both members, zero gap, and Fyb 45,000 psi.
BG045 retains its conditional inner-frame-block main member at 139 mm and
base-header side member at 38.1 mm, with the same bolt/gap/Fyb assumptions.
For BG045, the existing Ceg = 0.67 is applied once to the governing reference;
the reported Mode IV remains governing before and after that factor. No Cg,
load-duration or other service adjustment is applied.

These are conditional individual-bolt comparability ratios, not design DCRs or
joint passes. The force vectors come from the source-bound accepted numerical
a12-rear report; the grain axes are source-proposed material-map directions,
not inspected stock. Axial tie actions are listed separately and not checked.
Group action, load redistribution, bolt/washer axial resistance, splitting,
row shear, tear-out, net section, and complete connection transfer remain
outside this result. No bolt capacities or axis-component references are
summed. BG003 and the retained LEG/RUNNER arrangements are unchanged and
outside scope.

Regenerate and verify from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-resultant-direction-single-shear-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-resultant-direction-single-shear-attempt01/produce.py --verify
```
