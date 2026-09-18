# Conditional lower-backing retention ceiling

The isolated backing model now combines its actual attachment positions with
the existing conditional washer/wood-bearing envelope. The outermost attachments
reach optimistic dry-case load ceilings of approximately **245 N left and 230 N
right**. These are not board capacities, measured demands or joint allowables.
They show why widening only the central principals does not settle the backing
connection: outer attachment forces still act through substantial leverage.

## Exactly what is solved

Reuse the authenticated geometry from the
[relaxed housing-contact calculation](wide-backing-contact-bound.md): two
central bolt axes and full rectangular housing contact envelopes. Apply one
outward normal force at one of the six panel-to-backing attachment positions.
Maximize that force subject to normal-force and both planar moment balances,
nonnegative inward bolt reactions, nonnegative outward housing compression,
and a separate bearing-only cap on each bolt reaction.

The [washer-bearing envelope](backing-bearing-envelope.md) supplies the
conditional caps: 997.03 N dry, 668.01 N wet, or 727.83 N under the optional
0.02-inch deformation basis. Both bearing planes are in series; neither their
areas nor their capacities are doubled. No equal bolt sharing is assumed.
Zero preload is assumed, leaving the entire conditional bearing allowance
available in this optimistic calculation.

Housing compression is unlimited and may occupy removed material inside the
full envelope. Stiffness and compatibility are omitted. Washer flexure, local
splitting, counterbore ligament, non-normal actions and other frame load paths
are not represented. Therefore the result is a ceiling only within this isolated
model and its assumed bearing caps, not an upper bound for the complete frame.

## Dry-case results

| Panel attachment | Conditional outward load ceiling |
| --- | ---: |
| `timber_panel_lower_left_3` | 1,255.52 N |
| `timber_panel_lower_left_9` | 244.60 N |
| `timber_panel_lower_left_10` | 400.82 N |
| `timber_panel_lower_right_1` | 1,255.52 N |
| `timber_panel_lower_right_9` | 398.81 N |
| `timber_panel_lower_right_10` | 229.87 N |

Wet-case values are 0.67 times these results; the optional dry deformation case
is 0.73 times them. This scaling follows the same linear model with proportionally
scaled caps, not an experimentally established failure law.

Each result retains a feasible force distribution and a matching dual certificate
for its optimization ceiling. Tests independently check force/moment equilibrium,
individual bolt bounds, dual stationarity/signs/objective equality, hand-solvable
lever examples, invalid inputs and regeneration of every published row.

```sh
uv run pytest -q tests/test_backing_retention_envelope.py tests/test_wide_backing_contact_bound.py tests/test_backing_bearing.py
```

All 19 focused tests passed September 8, 2026. The calculation is
`fea/backing_retention_envelope.py`; its output is
[`backing-retention-envelope.json`](../fea/results/backing-retention-envelope.json).
The generator refuses to overwrite existing evidence.

## Design disposition

Keep the current backing detail **unqualified**. Do not compare these numbers
directly with climber weight or the historical panel experiment's attachment
forces: neither establishes current panel-to-backing demand. The next decision
needs either that load transfer assessment or a separately qualified retention
path closer to the backing ends. The relocated ML23Z trial remains unselected
until its installation and applicable rating are resolved.

Larger washers alone are not selected: their fit, stiffness, local wood behavior
and effect on the counterbore need checking. Additional principal mass is not a
substitute for those checks. This increment changes no CAD, hardware purchase
selection or construction instruction.
