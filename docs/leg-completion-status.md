# Leg completion: current design direction

The full leg-design goal remains active. No leg candidate is released for use.

## Rear-envelope preference

The owner requested that the legs preferably not extend behind the furthest
point of the board's top. The working interpretation is the top's vertical
projection onto the floor, viewed from the side. Pending confirmation of that
interpretation, use the **top frame's rear Y=1535.585 mm plane** as a conservative
limit; the upper climbing panel extends slightly farther, to Y=1549.570 mm.
This is a packaging preference, not a fall-zone or structural acceptance rule.

Actual spread-pattern 2×6 geometry:

| Additional foot-centre extension | Rearmost leg/foot Y | Relative to top-frame plane |
| --- | ---: | ---: |
| 0 mm | 1476.339 mm | 59.245 mm inside |
| 150 mm | 1628.337 mm | 92.752 mm outside |
| 300 mm | 1780.855 mm | 245.270 mm outside |

**Prioritize the zero-extension 2×6 version for the next complete comparison.**
The +150/+300 versions remain historical/diagnostic alternatives, not the
preferred final footprint. The separate hardware trial now checks both zero
and +300 mm geometry at minimum, midpoint and maximum washer thickness, with
nominal timber dimensions. Compact CAD transfer is checked; shipment compliance,
washer behavior and complete joint/group strength remain open.

```sh
uv run pytest -q tests/test_leg_rear_envelope.py
```

## Current work and remaining gates

- The long-bolt/MCX washer [hardware trial](leg-hardware-trial.md) has dimensional
  and nominal-wood CAD checks. Shipment compliance, washer behavior, group and
  combined connection resistance remain open.
- An unpinned-floor preparation now reuses the authenticated +300 mm spread
  mesh and released joint springs. A bounded native trial was started before
  the rear-envelope preference arrived. Retain it as baseline evidence; it
  does not select that footprint or validate the compact alternative.
  The first trial reached only 5% of the gravity step before its 600-second
  limit (exit 124); it did not reach the climber-load step. This is an
  incomplete calculation, not evidence that the board is unstable. See the
  [contact-trial record](spread-floor-contact-trial.md).
- Investigate compact geometry under the same gravity/contact basis before
  deciding that extra bracing is necessary. Only the ground may be restrained;
  fixed timber floor nodes cannot stand in for the intended unanchored design.
  The compact candidate's separate rigid-floor screen now has admissible
  equilibrium witnesses for all 1,296 prescribed cases at assumed friction
  coefficients 0.2 and 0.4. At 0.1, 666 cases were feasible and 630 were
  infeasible under the inscribed friction-cone approximation. This does not
  predict actual contact-force distribution or establish elastic stability;
  it is not a substitute for the unfinished native contact calculation.
- The actual front tie receiver is obstructed by the existing 19.05 mm base
  gusset. Reusing its Y=−80 mm, Z=300/380 mm bolt axes would create a rim/gusset/
  filler/rail stack and add loads to that connection. It is not a two-member
  joint or a completed anti-roll detail. Two point connectors leave rotation
  about their joining line unrestrained; side ties alone do not establish
  transverse racking restraint. Do not add a crossbar across the landing area.
- Full joint strength, full-member bending/compression/buckling, local contact
  acceptance, sensitivity checks and the synchronized build
  package remain required. None is marked complete by these preliminary checks.

The compact native comparison now passes all three stiffness-run numerical
gates. A separate [full-span demand report](leg-full-span-demands.md) includes
the bolt-loaded region as well as the clear span. The compact long-bolt geometry
is also available in the [viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-hardware-2x6-e0),
with all 283 meshes verified in a local browser. These close response/geometry
coverage gaps, not the remaining connection, buckling or contact acceptance.
