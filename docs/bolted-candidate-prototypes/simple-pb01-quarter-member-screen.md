# PB-01 quarter-inch cleat: conditional DF-L member components

Status: **reference component calculations only; not a connection rating,
utilization, or drilling release.** The reproducible
[screen](../../scripts/simple_pb01_quarter_member_screen.py) reads the
kerf-right four-bolt trial [pose](simple_rail_joint_comparison.json) and
fails if its bolt inventory, cleat stock, or critical-section layout changes.

The assumed members are dry solid DF-L No. 2, with published 2024 NDS
Appendix E reference inputs. The cleat is 5.5 in wide in X, 2.25 in in
local T, and 300 mm along its N grain. Each modeled host is 1.5 in thick.
The diagnostic wood bores are 7.5 mm; these are **not** hole instructions.
The values below assume load parallel to each member's grain and a force
direction that makes the named section or end critical. The actual
simultaneous actions are not yet available for the new topology.

| Hypothetical component/section | Reference value (lbf) |
| --- | ---: |
| Rail host, two-bolt row tearing toward butt | 850 |
| Cleat upright-side, two-bolt row tearing toward front | 3,508 |
| Upright host, two bores on one net-tension section | 4,234 |
| Rail host, one bore on net-tension section | 4,489 |
| Cleat rail-side, two bores on one net-tension section | 6,352 |
| Cleat upright-side, one bore on net-tension section | 6,182 |

The row values apply the existing [Appendix E.3 helper](../../mini_moonboard/bolted_timber_checks.py)
with 180 psi parallel-to-grain shear. The rail's 70 mm end distance and
40 mm pitch make pitch the shorter tear-out length. The cleat's 55.159 mm
front end distance and 45 mm pitch likewise make pitch shorter. The net
values apply the Appendix E.2 helper with 575 psi tension to the remaining
section after subtracting each modeled 7.5 mm bore. They are not six
independent capacities to sum or compare without simultaneous forces.

The calculation does **not** establish the critical force direction,
other-hole and cut interaction, perpendicular tension/splitting, group
effects, cleat bending, shear or torsion, bolt axial action, local washer
bearing, adjustment factors, or a complete joint resistance. Its 850 lbf
rail row is a conditional member reference, **not** an allowable load or
proof that the rail will fail there. The separate
[yield screen](simple-pb01-quarter-yield-screen.md) is also only a
one-bolt component. Neither may be substituted for the required 2024 NDS
joint checks and same-configuration six-case demand.

Source: [AWC 2024 NDS Appendix E](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf).
