# Floor-runner recess in the rear legs

The proposed recess is geometrically plausible: a nominal 2×6 runner can move outside the panel edge by occupying a recess in the **inner face** of each solid 4×6 rear leg. This is a preliminary coordinate study, not a modeled, analyzed or released alternative. The selected full-section floor-rail candidate remains unchanged.

## Alignment and connections

Dimensions below use absolute world X, measured outward from the board center; the left side mirrors the right.

| Component or interface | Proposed position or dimension |
| --- | --- |
| Panel outside edge | X = 1219.2 mm |
| Runner thickness band | X = 1219.2–1257.3 mm |
| Original outer front post | X = 1181.1–1219.2 mm |
| Existing full rear leg | X = 1219.2–1308.1 mm |
| Rear leg remaining beside the recess | X = 1257.3–1308.1 mm: **50.8 mm / 2 inches** |
| Front post/runner bolt grip | 38.1 + 38.1 = 76.2 mm / 3 inches |
| Rear runner/leg bolt grip | 38.1 + 50.8 = **88.9 mm / 3.5 inches** |

The front connection is a direct side-face lap, with the bolt axis along X and no intervening air gap or spacer. Restoring the original outer post positions also restores the four outer kicker screw axes to X = ±1200.15 mm, retaining their current Z = 60 and 192 mm heights. The runner is outside the panel width, so the kicker can retain its complete rectangular profile. Its nominal inside face aligns with the panel edge; installation clearance and tolerances would still need explicit detailing.

Cutting the recess from the **outer** leg face would instead place the runner at X = 1270.0–1308.1 mm. That leaves a 50.8 mm gap to the original front post and does not provide the same direct front connection.

## Recess dimensions

A floor-supported 2×6 runner occupies Z = 0–139.7 mm. Its recess therefore needs **139.7 mm / 5.5 inches of vertical height**, not 5.5 inches measured along the leaning leg. At the current leg angle, this corresponds to approximately **143.875 mm / 5.664 inches along grain**, before any installation clearance. The proposed transverse recess depth is 38.1 mm / 1.5 inches.

This is an open-bottom recess with a shoulder above the runner. Any claimed compression transfer through that shoulder would need explicit contact geometry and a bearing check. Shorter rear bolt grips would require an updated complete hardware stack and thread-engagement check; existing bolt lengths do not automatically transfer.

## Structural implications

Removing 38.1 mm from an 88.9 mm thickness removes about **43% of the local leg cross-sectional area**. The remaining notched foot section retains approximately 57.1% of its original area and strong-axis second moment, 32.7% of its weak-axis section modulus, and 18.7% of its weak-axis second moment. These comparisons describe the reduced local section, not an equivalent reduction in the capacity or stiffness of the entire leg. The runner and remaining leg cannot be assumed to act as one solid section.

The existing project comparison for an inclined member's end notch does **not** directly qualify this side-face recess. Its effect on the actual leg forces, local bending and shear, splitting, shoulder bearing, floor contact and the reduced rear bolt-bearing length would require a separate assessment. AWC’s FAQ, quoting the 2005 NDS, notes that a gradual taper reduces notch stress concentration; this historical explanation does not establish a current allowable depth or resistance for the proposed side-face cut. See [AWC guidance on notches in bending members](https://awc.org/faq/how-do-i-design-for-notches-in-a-bending-member/).

The [exterior-knee alternative](clear-space-study.md) already places all knee timber outside the ±1219.2 mm panel edges: its splice plane is at |X| = 1308.1 mm and its outer timber edge at |X| = 1346.2 mm. Those pieces have square, unnotched ends. That geometry clears the panel-width climbing corridor without cutting this recess into the rear legs.
