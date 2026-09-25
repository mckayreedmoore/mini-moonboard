# Estimated assembled board weight

The revised model estimates **249.4 kg / 550 lb**, including a 25 kg allowance for holds, hold hardware and electrical equipment. It excludes the climber and crash pads. This is a planning estimate, not a measured weight or load rating.

| Component | Estimated kg |
| --- | ---: |
| Plywood panels | 72.07 |
| Frame timber | 127.53 |
| Corner blocks | 15.56 |
| Block bolts nuts washers | 5.38 |
| Frame bolts nuts washers | 1.90 |
| Panel kicker screws | 0.44 |
| Hold t-nuts | 1.53 |
| Modeled subtotal | 224.42 |
| Equipment allowance | 25.00 |

Mass uses finished CAD solid volumes with 600 kg/m³ for timber and plywood and 7,850 kg/m³ for steel. The inventory includes 20 frame timbers, six panels, 24 blocks, 92 candidate bolt stacks, twelve starting frame stacks, 66 panel/kicker screws and 142 T-nuts. Axis proxies and provisional hold envelopes are excluded to avoid double counting. Actual equipment weights, wood density and moisture are unmeasured.

Using 500–600 kg/m³ for wood/plywood and 20–35 kg for equipment gives a planning sensitivity of approximately **460–572 lb**. This is an assumption range, not a statistical confidence interval. The thinner blocks and shortened exterior bolts remove about 2.54 kg / 5.6 lb relative to the preceding model.

The [full inventory](board-weight-2026-09-24.json) binds this estimate to `led-clearance-2x6-runner-seated-blocks-v1`. Density conventions follow the [historical mass assumptions](../history/provisional-floor-load-assumptions.md); the equipment allowance follows the [design basis](../current-design-basis.md). No joint or native mechanics check was run.
