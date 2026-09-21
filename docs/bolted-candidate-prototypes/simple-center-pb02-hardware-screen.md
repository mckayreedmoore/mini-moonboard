# PB02 authenticated current-case hardware screen

Status: **pre-contact-cell-correction sensitivity only; hardware and joint not
qualified**.

[`simple_center_pb02_hardware_screen.py`](../../scripts/simple_center_pb02_hardware_screen.py)
authenticates the retained Z202/link-Z328.5 `a12-forward` report, model identity,
diagnostic-scope fingerprint, active geometry fingerprint, geometry source hash, and exact ten-bolt
inventory before reading demands. The report is numerically accepted but explicitly does not provide
qualified joint demands.

A subsequent face audit found an active canonical contact spring outside the
true principal/cleat overlap and no tributary-area basis for the four equal
face springs. The authenticated forces below are therefore retained as bounded
numerical history, not current demand evidence. Recompute this screen after the
contact cells are corrected and the case is rerun.

## Conditional A307 shaft comparator

The screen parameterizes the existing `fea/reinforced_steel_capacity.py` method for nominal 1/4-in
bolts and each current wood grip: AISC 360-16 Table J3.2 A307 stresses, ASD omega 2, gross area, and
the existing 1% reduction per 1/16 in of grip beyond 5D applied to both stresses. This does not
establish that a delivered bolt is A307 or that the steel long-grip treatment applies to this wood
joint.

| Bolt | Grip mm | Tension N | Shear N | Long-grip factor | Linear ratio |
|---|---:|---:|---:|---:|---:|
| `post_block/bolt_1` | 177.8 | 0.000 | 14.674 | 0.0800 | 0.0622 |
| `post_block/bolt_2` | 177.8 | 15.175 | 11.930 | 0.0800 | 0.0892 |
| `block_header/bolt_1` | 182.0 | 0.000 | 22.207 | 0.0535 | 0.1407 |
| `block_header/bolt_2` | 182.0 | 5.490 | 22.208 | 0.0535 | **0.1616** |
| `header_principal_block/bolt_1` | 105.1 | 0.000 | 38.168 | 0.5380 | 0.0241 |
| `principal_block_principal/bolt_1` | 109.05 | 0.000 | 40.194 | 0.5131 | 0.0266 |
| `principal_upright_block/bolt_1` | 127.0 | 20.078 | 32.497 | 0.4000 | 0.0378 |
| `upright_rear_block/bolt_1` | 99.7 | 0.000 | 18.494 | 0.5720 | 0.0110 |
| `rear_block_post/bolt_1` | 127.0 | 0.000 | 64.865 | 0.4000 | 0.0550 |
| `rear_block_post/bolt_2` | 127.0 | 26.374 | 68.991 | 0.4000 | 0.0719 |

The conservative comparator is `T/Tallow + V/Vallow`. Separate references and ratios remain in the
machine-readable script output.

## Washer demand

Each head-side and nut-side washer receives the full positive bolt tension; it is not split between
ends. At the governing 26.374-N tension, the conditional 625-psi DF-L bearing arithmetic requires
6.120 mm² of annular contact. For any unsupported diameter `u`, the ideal required outside diameter
is `sqrt(u² + 4A/pi)`; at `u = 7.3 mm`, it is 7.816 mm.

The modeled 20-mm CAD envelope with a 7.3-mm unsupported diameter gives an ideal 1,173-N
wood-bearing reference and a 0.0225 demand ratio. It is only sensitivity arithmetic: the model uses
a solid disk and supplies no actual washer ID, OD, thickness, material, tolerance, or bending
resistance.
Accordingly, `washer_qualified` remains false for every bolt, including bolts with zero tension in
this case.

## Open conditions

Product-specific A307 status; root diameter; thread runout and bearing location; long-grip-rule
applicability; washer metal and bending; nut proof and thread stripping; preload; prying and
eccentric tension; qualified joint demands; and the other five load cases remain unresolved. This
screen releases no procurement, drilling, fabrication, or structural design.
