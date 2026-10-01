# Both upper-panel screw-group equilibrium bounds — attempt03

## Engineering result and stop condition

The preceding group screen bounded only the climber-loaded panel in each
case. This source-pinned extension checks both upper panels in all six cases,
including the panel that receives only its modeled own-weight load in the
other panel's climbing cases.

For each upper-panel/case pair, force equilibrium requires at least
**104.078–1,763.868 N total axial tension across that panel's twelve screws**
under the full panel-plus-assigned-T-nut gravity bookkeeping. Using only each
panel's own modeled weight plus any climber force applied directly to it gives
a separate **101.979–1,761.485 N** lower bound, so that result does not rely on
the unverified T-nut-to-panel gravity-carrier assignment. Both ranges remain
conditional on the modeled 600 kg/m³ panel density and recorded restraint
topology. No individual screw action is inferred.

Stop at these necessary force-equilibrium group totals. Exact 42605
resistance/load-slip, installed engagement and head/panel limits, per-axis
sharing, the lower-panel `a1-rear` path, and the route from receivers into the
frame remain open. Do not treat this screen as a panel-withdrawal pass.

## Results

| Case | Upper panel | Climber load on panel? | Panel-mass-only lower bound (N) | Including assigned same-panel T-nut gravity (N) |
|---|---|---:|---:|---:|
| `a12-rear` | `main_upper_left` | Yes | 1,761.423 | 1,763.868 |
| `a12-rear` | `main_upper_right` | No | 102.041 | 104.078 |
| `a12-forward` | `main_upper_left` | Yes | 1,301.796 | 1,304.242 |
| `a12-forward` | `main_upper_right` | No | 102.041 | 104.078 |
| `a12-left` | `main_upper_left` | Yes | 1,531.610 | 1,534.055 |
| `a12-left` | `main_upper_right` | No | 102.041 | 104.078 |
| `k12-right` | `main_upper_left` | No | 101.979 | 104.424 |
| `k12-right` | `main_upper_right` | Yes | 1,531.671 | 1,533.709 |
| `k12-rear` | `main_upper_left` | No | 101.979 | 104.424 |
| `k12-rear` | `main_upper_right` | Yes | 1,761.485 | 1,763.522 |
| `a1-rear` | `main_upper_left` | No | 101.979 | 104.424 |
| `a1-rear` | `main_upper_right` | No | 102.041 | 104.078 |

The loaded-upper-panel totals reproduce the five bounded cases in
[attempt02](../panel-screw-group-total-withdrawal-attempt02/README.md). The
new values add the second upper-panel group in those same cases and both upper
groups in `a1-rear`. They are separate group totals; they do not specify a
force split between the left and right panels or among screws.

## Method and limits

The verifier binds the six-case load contract, receiver axis inventory,
reduced-static model inputs, all panel body-force rows, and recorded contact
geometry by SHA-256. For each upper panel, it verifies twelve co-directed
inward screw axes, seven recorded contact patches with nonnegative
compression-reaction projection along the panel outward normal, and zero
residual between body forces, the applied case force, and assigned gravity.
The dot-product sign checks treat serialized binary64 components as exact
rational values.

With lateral screw reactions perpendicular to the panel normal, those
reactions cannot balance the positive outward force component. Every recorded
compression-only contact can contribute only outward or tangent normal
projection. The inward screw-axial tension total must therefore be at least
the outward external force component. An active contact could require more
screw tension, but the group sum has no finite upper bound here.

The panel-mass-only column omits the same-panel T-nut gravity rows; it is the
more conservative force threshold under the recorded model. The other column
uses those rows as conditional wrench bookkeeping and still does not prove a
mechanical T-nut carrier. Both columns use modeled panel density, not an
inspection of delivered plywood. Neither closes moment equilibrium, contact
activation, lateral/shear transfer, screw-head pull-through, panel damage,
product resistance, group interaction, or receiver-to-frame transfer.

No lower-panel group is screened here. In `a1-rear`, the recorded
`kicker_left`/`main_lower_left` contact has an inward compression direction,
so the outward-force projection does not establish a lower-panel screw bound.
No unrecorded alternate restraint is included. Missing evidence is not a
physical failure finding.

Reproduce from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/panel-screw-group-total-withdrawal-attempt03/verify_upper_panel_groups.py --verify
```

Run `sha256sum -c SHA256SUMS` from this packet directory to verify the local
README, verifier, and result.
