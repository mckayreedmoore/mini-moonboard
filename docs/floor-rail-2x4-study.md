# Isolated 2×4 floor-rail trial: not accepted

**Both A12-rear contact-solver attempts were numerically rejected. There is no
valid strength result for this trial.** The selected design remains
`compact-floor-rail-development`, with its passing single-2×6 rails and
[conditional package](clear-space-study.md).

The separate `compact-floor-rail-2x4-development` candidate substitutes
38.1 × 88.9 mm floor rails. Their tops are 50.8 mm lower than the selected
2×6 rails, improving clearance along the floor edges. Each kicker's clearance
notch becomes 40.1 × 90.9 mm. The trial has 14 complete bolt stacks: four
½-inch upper bolts, six ¼-inch front rail bolts and four ¼-inch rear rail
bolts. Use its [hardware record](floor-rail-2x4-hardware.md) for the exact
conditional catalog and fit assumptions; no hardware substitution is selected.

Estimated modeled mass is 209.2343 kg versus 213.9222 kg for the selected
2×6 assembly, a reduction of 4.6879 kg. These are model-based estimates,
not measured weights or evidence of structural adequacy.

| A12-rear attempt | Recorded outcome | Archive |
| --- | --- | --- |
| All-contact update | Repeated contact cycling; numerical rejection. | [First attempt](../fea/results/clear-space-floor2x4-trials/all-update-a12-rear/) |
| `one_per_floor_body` retry | Floor-contact oscillation through 30 recorded iterations, 0–29; numerical rejection. | [Final retry](../fea/results/clear-space-floor2x4/a12-rear/) |

Rejected contact iterations do not provide accepted connection forces,
resistance ratios or a physical failure prediction. The smaller section and
changed bolt layout cannot inherit the selected 2×6 frame's passing results.
The bounded investigation ends with this negative numerical decision; no
further studies or passing case set are promised.

The [separate viewer](../site/index.html?model=compact-floor-rail-2x4-development)
and [dimensional packet](clear-space-floor2x4-construction/) are **reference
only, not construction instructions**. They preserve the modeled profiles,
notches and drilling for inspection; their completeness does not override the
rejected response. Keep the selected 2×6 packet separate.

The accepted panel basis and explicit no-slip support assumption remain the
assessment scope. This result introduces no new panel qualification,
floor-friction test or external-review requirement. Existing unqualified
commercial-angle separation and independent flange-couple limits remain
explicit; neither solver attempt resolves them.
