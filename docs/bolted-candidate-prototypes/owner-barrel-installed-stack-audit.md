# Current barrel viewer: nominal installed-stack axial audit

This is an independent read of the **current**
`export_owner_barrel_scene.build_viewer_assembly()` composition. It does not
read an older exported scene or rebuild the three families from their producer
defaults. The assembled outer-rail trial is the new **6 in / 60 mm setback**
geometry. The script checks every one of the 48 bolt/barrel pairs and leaves
the producer and exporter unchanged.

Run `.venv/bin/python -m scripts.owner_barrel_installed_stack_audit` for the
48 named records and their shaft start/length, barrel-body center/OD,
near/assumed-axis/far-wall reach, modeled machine-bore far cap, signed tip
clearance, and head/washer presence. `tests/test_owner_barrel_installed_stack_audit.py`
guards the counts and exact exception names.

| Nominal CAD observation | Count | Status |
| --- | ---: | --- |
| Tip short of assumed barrel center | 0 | Thread axis unverified |
| Tip beyond modeled machine-bore cap | **0** | Revised nominal bores only |
| Axis reached; tip within modeled bore | 48 | Not a fit pass |
| Head absent / washer absent | 0 / 0 | Provisional envelopes only |
| Delivered thread engagement | 48 | **UNKNOWN** |

The owner-approved nominal bore-depth revision applies to both rows at each
of these four stations:

- `clip_horizontal_lower_left_2_barrel_1_bolt`,
  `clip_horizontal_lower_left_2_barrel_2_bolt`
- `clip_horizontal_lower_right_1_barrel_1_bolt`,
  `clip_horizontal_lower_right_1_barrel_2_bolt`
- `clip_horizontal_upper_left_2_barrel_1_bolt`,
  `clip_horizontal_upper_left_2_barrel_2_bolt`
- `clip_horizontal_upper_right_1_barrel_1_bolt`,
  `clip_horizontal_upper_right_1_barrel_2_bolt`

Each has a modeled 127.0 mm (5 in) shaft, tip 17.249 mm past the assumed
barrel center. The earlier pilot stopped **10.2452 mm before its tip**; the
revised trial adds **14.2452 mm of depth**, yielding **4.0 mm nominal tip
clearance**. The four recessed outer-header bores also now extend 4.0 mm
past their modeled tips, rather than ending flush. Neither change is a
drill dimension or a fit pass. The 12 revised 152.4 mm (6 in) outer-rail
shafts at 60 mm setback remain within their bores.
Their modeled tips reach only 1.849 mm past the assumed barrel axis, so the
maximum shaft overlap through the 10.0076 mm barrel body is **6.8528 mm**
even if the bolt end is fully threaded. This is a geometric upper bound,
not verified engagement or capacity. The report now records the threaded
end length required merely to reach each barrel near wall and the maximum
possible body overlap for every bolt; actual bolt runout and barrel threads
remain unknown.
A shorter 4½ in hex-bolt substitution is not selected: the readily listed
[Hillman 190055][short-bolt] is expressly **not full-thread**, and its actual
thread runout at the barrel is unverified. The owner approved the bounded
depth revision only; it does not authorize drilling or fabrication.

All 48 former-angle bolt paths now have nominal CAD head/washer envelopes,
including the 12 outer/top rows previously omitted. Presence in CAD is not
evidence of a selected retail part or a seated, installable stack.

The audit uses the actual cylindrical shaft, barrel body, and bore solids.
It confirms the connection axis agrees with the shaft solid and that each
bore is coaxial with its bolt. The **barrel-body midpoint** is used solely as
the provisional thread-axis proxy. It does not establish where the threads
really are, whether the bolt's threaded portion reaches them, or adequate
engagement. No delivered dimensions, tolerances, tool access, assembly
sequence, wood net-section strength, barrel resistance, or whole-frame load
case is passed by this audit. There is **no overall PASS, structural release,
drilling release, or fabrication release**.

[short-bolt]: https://www.lowes.com/pd/Hillman-1-4-in-x-4-1-2-in-Zinc-Plated-Coarse-Thread-Hex-Bolt/1000897796
