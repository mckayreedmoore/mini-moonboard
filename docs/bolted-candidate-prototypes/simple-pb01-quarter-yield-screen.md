# PB-01 quarter-inch cleat: conditional lateral-yield component screen

Status: **numerical component comparison, not a joint rating or drilling release.**
The four-bolt grain-N pose has two bolts across each of two *serial*
interfaces. This screen calculates one bolt's six wood/wood single-shear
yield modes at each interface. It does not multiply a mode value by the
number of bolts or compare it with the 23-proxy hybrid response as a design
demand.

## Input provenance and assumptions

- The [four-bolt CAD record](simple_rail_joint_comparison.json) has a
  5.5-in cleat length in X at the upright face and a 2.25-in cleat width
  in local T at the rail face. Each corresponding host bearing length is
  1.5 in. The independent geometry review confirmed these as the modeled
  wood lengths. Both bolt axes are transverse to the grain of both members.
- The [2024 NDS Appendix I, Table I1][appendix] lists 45,000 psi `F_yb`
  for bolts as a class. Appendix L, Table L1 gives **0.189 in as a typical**
  root for a nominal 1/4-in standard hex bolt. Neither is a delivered-lot
  test or a verified minimum root of the retail leads. A separate 0.180-in
  input is a hypothetical smaller-root sensitivity, **not** a specified
  lower bound.
- Both members are assumed solid DF-L at assigned `G=0.50`; the
  [bearing helper](../../mini_moonboard/bolted_timber_checks.py) returns
  4,650 psi for either member at effective diameter below 1/4 in. All
  bearing is conservatively put on the trial root in both members; there
  is no full-shank credit. This presumes seated faces (`gap=0`) and an
  intact two-wood-member single shear plane.
- The [2024 NDS Table 12.3.1B erratum][errata] uses
  `R_d=(10D+0.5)K_theta` for every mode at the assumed root, with
  `K_theta=1+0.25 theta/90`. The [component helper](../../mini_moonboard/bolted_wood_wood_yield.py)
  uses `M_y=F_yb D³/6` and the existing six-mode solver. Angles 0° and
  90° bound this **component's** `K_theta` input; they are not the actual
  simultaneous force direction at either bolt.

| Trial root (in) | `M_y` (lb·in) | `R_d` at 0° / 90° | Governing mode | One-bolt `Z` at 0° / 90° (lbf) |
| ---: | ---: | ---: | --- | ---: |
| 0.180 hypothetical | 43.74 | 2.300 / 2.875 | IV | 117.6 / 94.1 |
| 0.189 NDS typical | 50.63 | 2.390 / 2.9875 | IV | 124.8 / 99.9 |

Mode IV governs at both modeled interfaces for these inputs, so their
different wood lengths do not change the displayed minimum. That does
**not** establish a group value, nor can the two serial groups' values be
added. The existing helper tests cover all six modes and the special
small-root reduction branch; an independent calculation review reproduced
these four displayed values and checked the modeled bearing lengths and
grain axes.

The root range and thread occupancy of the exact 5-in and 8-in store
bolts, nut engagement, washers and axial action, end/edge and group
effects, local splitting/net section, cleat bending/shear/torsion, contact
stiffness, and same-configuration six-case actions remain unresolved.
The authenticated hybrid solve still has **23 old angle/SDS proxies**;
its small trial bolt forces are not V4 demand. No utilization or safe
load can be inferred from this component screen.

[appendix]: https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf
[errata]: https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf
