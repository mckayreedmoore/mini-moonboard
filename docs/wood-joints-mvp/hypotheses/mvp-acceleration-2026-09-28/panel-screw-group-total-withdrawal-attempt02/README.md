# Panel screw-group withdrawal lower bound with assigned gravity — attempt02

## Engineering result and stop condition

This update uses the frozen loaded-panel body-force rows, so the normal-force
screen includes each panel's modeled self-weight and its same-panel T-nut
gravity. At the conditional 600 kg/m³ panel-density scenario, five cases have
a normal-only compression-contact lower bound of **1,304.24–1,763.87 N on the
sum of the twelve panel-screw axial tensions**. The governing case is
`a12-rear`. This updates the earlier climber-only group lower bound; it does
not assign any force to an individual screw.

The sixth case, `a1-rear`, has a **1,763.734 N loaded-panel outward resultant**
after assigned panel/T-nut gravity, but the finite `kicker_left` /
`main_lower_left` patch can geometrically supply inward compression. Its
contact state and force share are unknown, so this packet makes no lower-bound
claim for that screw group.

Stop and regenerate if a pinned input changes, the case-to-panel map or twelve
axis alignment changes, body force no longer reconciles to applied load plus
assigned gravity, or a new opposing-normal contact appears. Keep `a1-rear`
unresolved until its contact state/force transfer is supported. Do not convert
the group total into per-screw actions or compare it with an invented product
rating.

## Results

| Case | Loaded panel | Applied outward component (N) | Assigned panel/T-nut gravity component (N) | Conditional minimum total axial tension (N) |
|---|---|---:|---:|---:|
| `a12-rear` | `main_upper_left` | 1,659.444 | 104.424 | **1,763.868** |
| `a12-forward` | `main_upper_left` | 1,199.818 | 104.424 | **1,304.242** |
| `a12-left` | `main_upper_left` | 1,429.631 | 104.424 | **1,534.055** |
| `k12-right` | `main_upper_right` | 1,429.631 | 104.078 | **1,533.709** |
| `k12-rear` | `main_upper_right` | 1,659.444 | 104.078 | **1,763.522** |
| `a1-rear` | `main_lower_left` | 1,659.444 | 104.290 | **Not established** — opposing-normal kicker contact |

The bound follows the panel-normal force equation. For the five bounded cases,
the pinned finite panel-contact surfaces have no geometric normal that can
push inward under compression. Under the stated normal-only contact screen,
their compression reactions therefore contribute zero or outward force along
the panel normal. Since all twelve screw axes point inward along that normal,
the sum of screw tensions must be at least the loaded panel's outward
resultant. Any realized outward contact reaction can increase that sum.

## Reproduce

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/panel-screw-group-total-withdrawal-attempt02/verify_panel_group.py --verify
sha256sum -c docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/panel-screw-group-total-withdrawal-attempt02/SHA256SUMS
```

The verifier checks exact source hashes, all six case/panel mappings, twelve
inward-aligned axes per loaded panel, the panel-body force sum against applied
climber force plus source-assigned gravity, and every finite panel contact
normal. It confirms that the own-panel mass corresponds to the conditional
600 kg/m³ scenario and that the model remains non-accepted with no native run.
It writes only with `--write` after the pinned inputs pass.

## Scope and gate effect

This gives Option B a more complete **necessary group-total withdrawal
threshold** for five panel cases. It does not close the panel-withdrawal or
receiver-path gates. Exact Hillman 42605 withdrawal/load-slip data, installed
penetration, screw-head/panel limits, defensible group distribution, and the
receiver-to-frame route are still missing. Missing product evidence is not a
physical failure finding.

The calculation uses conditional source mass/wrench assignments, not
inspection of delivered panels or hardware. The panel/T-nut gravity rows are
bookkeeping inputs; this does not establish a mechanical T-nut carrier.
Unassigned screw-axis and other hardware gravity, the separate accessory
scenarios, hold/T-nut load-transfer mechanics, tangential friction, screw
shear/bending, head/panel failure modes, per-axis sharing, and downstream
receiver actions are excluded. It gives no resistance, safety factor, finite
upper bound, or capacity acceptance. No geometry, mesh, native solver input,
or physical installation was changed or evaluated.

## Source pins

| Source | SHA-256 |
|---|---|
| [Six-case load contract](../../../../../docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json) | `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a` |
| [Current receiver screen](../../../../../docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/receiver-screen-attempt04.json) | `851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991` |
| [Reduced-static source/input record](../reduced-static-attempt01/model-inputs.json) | `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9` |
| [Reduced-static loaded-body wrench rows](../reduced-static-attempt01/body-external-wrenches.csv) | `6c823add8e29fc2089bff460ce7fa59c300794511214890b638b6c1a6c77a33f` |
| [Reduced-static contact geometry](../reduced-static-attempt01/contact-geometry.json) | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |
| [Prior climber-only group-total screen](../panel-screw-group-total-withdrawal-attempt01/README.md) | `6946b2d4cdc7696d41d397e4b9b167e8f2cf6f32d932d61758cefa2028ecd7ae` |

The exact machine-readable forces are in
[`panel-group-with-gravity-result.json`](panel-group-with-gravity-result.json).
Packet files and the producer's own hash are recorded in
[`SHA256SUMS`](SHA256SUMS).
