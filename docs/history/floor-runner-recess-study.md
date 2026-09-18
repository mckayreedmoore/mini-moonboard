# Recessed floor-runner trial

`compact-floor-recess-development` is a separate, unselected trial requested to move the floor runners outside the kicker edges. The selected full-section 2×6 floor-rail assembly remains the current candidate. **The A12-rear native response converged, but this trial is not accepted: local notch-corner resistance remains unqualified.** It meets 31 of 33 recorded criteria. The other unmet criterion is an intentionally more severe, full-height reduced-band diagnostic; that result does not demonstrate failure of the actual recess.

## Concrete configuration

The two full 2×6 runners retain their 38.1 × 139.7 mm section and 1880 mm length. They move outward to absolute X = 1219.2–1257.3 mm. Original outer front posts return to X = 1181.1–1219.2 mm, providing direct front laps. Both kickers retain complete rectangular profiles; their four outer post screws return to X = ±1200.15 mm at Z = 60 and 192 mm. All 66 panel/kicker screws remain.

Each solid 4×6 rear leg receives an open-bottom recess from its inner face, **38.1 mm deep and 141.7 mm vertically high**. This leaves **50.8 mm of leg thickness** beside the runner. The 141.7 mm height includes 2 mm clearance over the 139.7 mm runner; no shoulder bearing is credited. Transverse fit is nominal at zero clearance and remains an explicit installation assumption.

The trial retains two half-inch upper bolts per leg and adds two three-eighths-inch bolts at each runner end: **12 complete bolt stacks**. Front grip is 76.2 mm; rear grip is 88.9 mm. The [hardware review](floor-runner-recess-hardware.md) identifies a nut-seating defect in the initial 5-inch rear bolt and records the 4½-inch correction now applied to the model. Matching exports and schedules must be regenerated before current artifacts are accepted.

## Geometry and native representation

The initial actual-CAD receiver check reports **24/24 bolt receivers passing**, with complete represented machining. Full stock remains the source for manufacturing profiles; the actual recess is a separate, explicit cut. No old knee bores or former lower-joint bores are intentionally retained in rebuilt stock. A fresh geometry build includes the corrected 4½-inch rear bolts and actual recess metadata. Thread seating is also covered by the focused model regression.

The native model represents the actual horizontal recess with conforming
C3D20 solids, matching retained CAD volume, reduced foot contact and 50.8 mm
rear bolt-bearing intervals. It recovers section actions at both ends of the
horizontal shoulder projected onto the leg grain. The native geometry,
represented cuts, shoulder coverage and rear receiver checks pass. Full-leg
stiffness is not retained through the removed wood.

## Converged first-case result and interpretation

The [current archive](../fea/results/clear-space-floorrecess/a12-rear/) records
A12-rear with the stated 250 lb, doubled-downward load case and 300 N rearward
action. The [initial bounded attempt](../fea/results/clear-space-floorrecess-trials/initial-coulomb-a12-rear/)
exhausted its 160-iteration budget. A fresh continuation using that state only
as a search seed converged after four native solves. Numerical acceptance
comes from the new solved state, not from interpolating or accepting the
unfinished trial.

The final maximum friction-law residual is **0.0116296 N** at
`floor_base_post_outer_right_2_friction`. The unchanged criterion is 0.01 N
plus the native DAT printed-force rounding allowance; this cell's allowance
is 0.00269624 N. Its residual is below their sum, **0.01269624 N**. No numerical
acceptance limit was relaxed to obtain convergence.

| Comparison | A12-rear result |
| --- | ---: |
| Recorded criteria met | **31/33** |
| Actual-angle bolt lateral demand/reference | **0.85911** |
| Maximum sampled actual-cut net-member comparison | **0.56663** |
| Left leg sampled recess-region maximum | **0.56663**, at first rear runner bolt |
| Right leg sampled recess-region maximum | **0.24453** |
| Left shoulder-bound nominal section comparisons | **0.49456 / 0.47693** |
| Right shoulder-bound nominal section comparisons | **0.21338 / 0.20610** |
| Artificial full-height 50.8 mm band diagnostic | **1.14579** |
| Local notch-corner resistance | **Unqualified** |

The 1.14579 value occurs in the left leg at grain station **+820.8257 mm
from its CAD center**, with section-center height **1756.78 mm**. The actual
recess ends at Z = 141.7 mm. This diagnostic discards the inner 38.1 mm band
at every station, including intact stock far above the recess. Its exceedance
shows that assigning all forces to that artificial continuous narrow member
is insufficient; **it is not evidence that the actual cut section fails**.

The actual-cut comparisons include the removed side band and bolt bores where
they exist. Their passing nominal-stress values and the separate joint-group
splitting comparison do not establish re-entrant-corner stress concentration
or local notch splitting resistance. A 2 mm shoulder gap avoids runner-to-leg
shoulder bearing but does not eliminate redistribution through the changing
leg section. No composite action with the runner is credited. The old
inclined-member end-notch comparison does not directly qualify this cut;
see the [bounded recess feasibility record](floor-runner-leg-recess.md).

The batch stops at this first design gate. No other load cases are reported
as completed or passing for the recessed candidate. The selected full-section
floor-rail package remains separate and unchanged; this result does not select
a reinforcement detail or promise further studies.

The finite trial retains the existing load basis and accepted panel construction. Its converged native run uses collocated floor-contact friction with assumed μ = 0.4 and monotonic loading from zero initial slip, matching the corrected exterior trial rather than inheriting the original no-slip restraint. It introduces no floor-friction test or new panel-qualification requirement. A failed or rejected response remains a trial result; it does not displace the selected full-section floor-rail evidence.

The [exterior-knee alternative](clear-space-study.md) already places its square-ended knee timber entirely outside the panel-width climbing corridor and requires no such leg recess. Its own recorded results remain separate from this trial.
