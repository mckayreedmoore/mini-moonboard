# Smooth-body leg hardware investigation

This is an isolated hardware candidate for the eight existing leg bolts in
`round-reinforcement-development`. It is **not selected or strength-qualified**.
The frame, holes, and all other hardware remain unchanged. Joint bending still
requires assessment; passing the stack and collision checks does not resolve it.

Each candidate stack contains a 3/8-16 × 5-inch SAE J429 Grade 5 bolt, two
fabricated A36 round plate washers (38.1 mm outside diameter, 11.1125 mm bore,
6.35 mm thickness), one nut-side steel spacer (20 mm outside diameter,
11.1125 mm bore, 19.05 mm length), and a matching Grade 5 nut. The spacer lies
between the nut-side plate and nut, outside the wood. Finished dimensions are
acceptance requirements. No existing purchased hardware is claimed compliant.

The dimensional calculation assumes each wood member measures 37.5–38.5 mm,
a maximum bolt length shortfall of 2.54 mm, a 25.4 mm reference thread length,
and five pitches of runout. The supplier must meet these assumptions. The
minimum smooth body covers both complete wood members and the head-side plate.
The nut seats beyond the maximum gaging length, with at least two pitches of
bolt projection beyond the maximum-height nut. Cylindrical head and nut
representations bound the conservative dimensional envelope; they do not model
thread engagement surfaces or certify a product standard.

`hardware.step` contains the 48 individually named candidate components only.
`review.json` records the dimensional corners, mass envelope and nominal CAD
checks. The CAD check tests intersections against the unchanged frame and other
hardware, and full ring support by translating each plate into its receiving
wood member. This is not a manufacturing-tolerance or installation-tool check.

Reproduce the review from the repository root:

```python
import json
from pathlib import Path
from mini_moonboard import leg_smooth_hardware as model

folder = Path("docs/leg-smooth-hardware-review")
report = model.export_review(folder)
report["geometry"] = model.geometry_review()
(folder / "review.json").write_text(json.dumps(report, indent=2) + "\n")
```
