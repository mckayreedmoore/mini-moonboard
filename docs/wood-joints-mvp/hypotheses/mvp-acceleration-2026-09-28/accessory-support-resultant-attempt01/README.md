# Accessory-aware global support resultant — attempt01

## Engineering result and stop condition

This cross-check combines the six frozen climber-load cases, the source-bound
778-row modeled gravity inventory, the separate 25 kg allowance under each of
its nine existing placement scenarios, and the reviewed floor-support hull.
It tests the necessary global condition that the required vertical floor
resultant can act somewhere inside that hull. Stop if any of the 54
scenario/case records fails wrench reconstruction, has a nonpositive normal
resultant, or places its center of pressure outside the modeled support hull.
This result does not close the floor-support gate.

## Result

The read-only verifier reconstructs all 54 combined force and moment records
from the source case, modeled-body gravity, and accessory scenario wrenches.
Each reconstructed global center of pressure lies within the modeled hull.
The smallest hull-edge margin is **389.254 mm**, in `a12-rear` with the
`split_12_5_kg_hold_at_A12` scenario; the mirrored `k12-rear` case has the
same margin. The center is approximately `(-513.163, 1250.693) mm` in the
governing case. The required normal floor resultant is **4,670.093 N** in all
cases. The required horizontal floor resultant is 300 N in the direction
opposite the case's horizontal applied force; the required yaw reaction is
also recorded case by case. No capacity is assigned to those actions.

Reproduce the source-pin and recomputation check from the repository root:

    python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/accessory-support-resultant-attempt01/verify_accessory_support.py --verify

Use --write only after inspecting the pinned source files. Verification does
not write to the saved result.

## Method and scope

For each total external wrench `(F, M)` about the global origin, the
compression-only floor normal resultant required by vertical equilibrium is
`N = -Fz`. If the resultant can act at `(x, y, 0)`, moment balance about the
horizontal axes requires `x = My/N` and `y = -Mx/N`. The script computes the
signed perpendicular distance from that point to each edge of the pinned
convex hull and uses the minimum as the margin. It independently reconstructs
the total applied wrench by adding the case wrench shifted to the global
origin, the 778-row gravity resultant, and the accessory scenario gravity
resultant.

Inputs are the six-case load contract, the existing nine-scenario dead-load
record, and the exact support polygon saved by the current global-equilibrium
screen. The accessory scenarios use a 0–25 kg electrical / remaining hold
split or six named hold-axis endpoint placements. They are model scenarios,
not measured equipment mass, hold distribution, or installation. Existing
modeled fasteners and T-nuts are not double-counted. The hull derives from the
eight source-bound floor faces of the current modeled timber members; it is
not a floor inspection.

## Limits

An interior global center of pressure is only a necessary static equilibrium
condition. This calculation assumes the assembly has intact internal load
transfer. It does not determine the floor-normal load distribution among the
eight members, individual-foot lift, timber bearing pressure, frame stiffness,
sliding or yaw resistance, friction, anchorage, or joint/member demand. A
no-slip analytical assumption supplies no physical floor rating. Uniform
material density, accessory locations, and zero outward hold-center offset
remain scenario assumptions. The four integration gates remain open and the
record does not claim mechanical acceptance, a valid six-case frame response,
or a build/climbing release. No geometry, mesh, or native solver was changed
or run.

## Source pins

| Source | SHA-256 |
|---|---|
| [Six-case load contract](../../../../../docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json) | `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a` |
| [778-row plus 25 kg accessory scenario contract](../../../../../docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-dead-load-scenarios-attempt01/dead-load-scenarios.json) | `37df743291b49d0a2b68274cd18337051c75dc927d72e49a903162d10f982e83` |
| [Source-bound floor-support hull and original screen result](../global-equilibrium.json) | `4fe8652f4296827ed8bf06b376cee22194027d24eb64a73a17afa87679ffb381` |

The local artifact files are pinned in [SHA256SUMS](SHA256SUMS).
