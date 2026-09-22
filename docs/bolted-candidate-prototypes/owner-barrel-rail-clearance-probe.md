# Right-center rail barrel clearance probe

This is a detached CAD parameter screen for only
`clip_horizontal_lower_right_1` and `clip_horizontal_upper_right_1`.
Run `.venv/bin/python -m scripts.owner_barrel_rail_clearance_probe` from the
repository root to reproduce the 15 JSON records. The source viewer scene and
its default 60/92.25 mm rows and 70 mm barrel setback are unchanged.

The probe uses all 26 kerf-right uncut timber parts, moves only the two center
posts to X = ±180 mm, and adds the two exact owner kicker backers: 28 wood
solids total. All 66 panel/kicker screw axes and 12 retained frame-bolt axes
remain fixed. Protected solids are 142 T-nuts, 142 hold-hole/provisional
50.8 mm rear projections, 132 lights, 131 wires, 66 panel screw shafts, and
12 frame bolt shafts. Every trial screens both rows' machine bore, barrel
bore, barrel body, bolt shaft, 20 mm × 40 mm bolt access, and 20 mm × 40 mm
barrel access against that inventory and every unrelated timber solid.
Where the nominal 5 in bolt extends beyond the modeled machine bore, the
probe also screens a diagnostic 7.5 mm diameter pilot continuation through
the bolt tip. This is a possible clearance envelope, not a drill instruction.

Rows are N offsets from each rail front. The front row varies 50, 55, 60,
and 65 mm; the rear is 92.25 mm, plus one 65/95 mm sensitivity. Barrel
setbacks from the rail butt are 70, 75, and 82.5 mm. Both duties have a
38.1 mm rail thickness and a 139.7 mm rearward N envelope. Nominal markers
are 7D = 44.45 mm for front/rear/butt end distances and 4D = 25.4 mm for
row pitch, with D = 6.35 mm. These markers are geometry checks, not a wood
joint capacity rule. The barrel blind bore leaves 11.049 mm of T wood at the
far face. Both rows' machine and barrel bores intersect by about
408.396 mm³; both provisional barrel bodies are contained in the rail for
all trials. There are no unrelated-timber or inter-row hits in this grid.

| Front/rear N (mm) | Setback (mm) | Modeled clearance result for both duties |
| --- | ---: | --- |
| 50/92.25 | 70, 75 | No reported protected or unrelated hits; nominal markers pass |
| 55/92.25 | 70, 75 | No reported protected or unrelated hits; nominal markers pass |
| 50/92.25 | 82.5 | Lower barrel access hits `hold_tnut_main_G6` trial path: 403.127601 mm³ |
| 55/92.25 | 82.5 | Lower barrel access hits same hold path: 133.252457 mm³ |
| 60/92.25 | 70, 75, 82.5 | Lower/upper bolt access hits wires `wire_066_F7_F6` / `wire_065_F8_F7`: 27.164985 / 24.133152 mm³ |
| 65/92.25 and 65/95 | 70, 75, 82.5 | Same lower/upper wire hits: 87.023224 / 98.577055 mm³ |

At front row 50 mm, the front 7D margin is 5.55 mm and the 4D pitch
margin is 16.85 mm; at 55 mm they are 10.55 and 11.85 mm. The rear 7D
margin is 3.00 mm at rear row 92.25 mm and only 0.25 mm at 95 mm.
Butt 7D margins are 25.55, 30.55, and 38.05 mm for setbacks 70, 75, and
82.5 mm respectively. These are nominal center-distance reserves, without
tolerance or strength credit.

The nominal bolt tip is 950.826 mm inside the rail's far exterior for every
trial. At setbacks 70 and 75 mm it extends 10.2452 and 5.2452 mm beyond
the current modeled machine-bore end, respectively. At 82.5 mm it stops
2.2548 mm before that end. The corresponding projections beyond the
barrel's far surface are 12.2452, 7.2452, and −0.2548 mm. Projection past
the barrel is **diagnostic**, not a failure: a continued pilot may accommodate
it. The four hit-free poses' diagnostic continuations add no protected or
unrelated-timber collision at the modeled diameter.

Disposition: **geometry-only options; no selected or viable joint**. A
zero-hit pose does not establish actual tool approach, installed heads and
washers, delivered barrel body/axis/thread dimensions, thread engagement,
pilot size or depth, tolerance, timber resistance, coupled load path, or
backer attachment. The hold rear projection is provisional, and modeled
fixed screw/bolt shafts do not represent every installed feature. Preserve
the owner panel screws. No fabrication or drilling release.
