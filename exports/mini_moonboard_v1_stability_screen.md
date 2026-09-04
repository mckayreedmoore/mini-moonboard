# V1 unanchored stability screen

This is a rigid-body **pre-FEA** screen generated from the current CAD
assembly. It is not structural approval and it does not replace a contact,
connection, or material model. Its purpose is to prevent a fixed-foot FEA from
hiding an unanchored uplift mechanism.

## Declared screen inputs

- CAD volume is assigned a provisional uniform density of
  600 kg/m³; this produces 188.6 kg total
  mass. The purchased C-3 birch stock has no verified structural density or
  grade in this project, so this is a sensitivity input, not a material claim.
- Dead weight acts at the CAD volume centroid, Y=715.3 mm.
- The floor support interval uses the extreme edges of actual CAD floor
  contact faces, from Y=-265.3 mm through
  Y=1399.8 mm.
- The source-backed 1.2 kN unroped-climber force is applied at the top-row
  climbing-face point Y=1549.4, Z=2092.9 mm in
  both opposite board-normal directions. A negative reaction is uplift and is
  impossible without an anchor.

| Load direction | Front floor reaction N | Rear floor reaction N | Minimum total dead mass kg |
| --- | ---: | ---: | ---: |
| normal +Y / -Z | -464 | 3085 | 303.8 |
| normal -Y / +Z | 1985 | -907 | 345.6 |

## Result

The current unanchored footprint fails this screen in **both** normal
directions: one floor contact has negative reaction in each case. The governing
direction needs at least 345.6 kg of total dead mass at the current
centre of mass, versus the screened 188.6 kg. Treat that
157.0 kg difference as a warning, not a ballast
prescription: moving the feet/base can be much more effective than adding mass.

Do not continue to a fixed-foot FEA as evidence of unanchored stability. First
revise and model the base footprint/ballast strategy and the kicker-to-main
load path; then solve contact, sliding, and overturning with the reviewer-set
floor friction and material data.
