# PB01 six-inch tension-only component comparison

Run `uv run --no-sync python -m scripts.simple_pb01_short_tension_component_comparison`
from the repository root for the full signed JSON. It reads the finished native
outputs retained in
[A12-left evidence](../bolted-candidate-evidence/pb01-short-tension-a12-165adbf-evidence.zip)
and
[K12-right evidence](../bolted-candidate-evidence/pb01-short-tension-k12-165adbf-evidence.zip),
plus the retained
[signed comparison](../bolted-candidate-evidence/pb01-short-tension-a12-k12-165adbf-comparison.json).
It does not use `/tmp`, run a solve, or write an evidence bundle. The ZIPs are
fixed by SHA-256 (`4a3a7002...3dfa8` and `e5fafb5f...edd7c`), the comparison
by `09df8d9f...8d194`, and each embedded report by its own digest. The
archive verifier checks all retained source snapshots and final artifacts;
this screen checks the embedded scope, forces and cross-archive comparison.
Both runs say
numerically accepted, with converged tension and contact active sets and
passed equilibrium audits. Each still has **23 legacy connector proxies**.
Neither report qualifies actual full-joint design demands.

This is the 152.4 mm (six-inch) `quarter_short` block, with a tension-only,
no-preload bolt axial law and compression-only face samples. It is a different
native configuration from the historical 300 mm cleat. No historical bolt,
contact, or interface force is transferred. The two cases are distinct load
scenarios; each interface force and moment below sums simultaneous bolts and
face samples **within its own case**. Host force is positive in global XYZ;
moment is the right-hand-rule `(point - datum) × force` about the shared
global datum `(134.050, 658.242, 1233.678) mm`. The cleat gets equal and
opposite connector force and moment about that same datum. The upright and
rail faces are serial interfaces, not one four-bolt group.

Axial is force **on the host** projected onto the host-to-cleat bolt axis.
Lateral XYZ is the signed remainder; the table also gives its magnitude.
Upright axes are +X; rail axes are approximately
`(0, 0.642788, 0.766044)`. Zero axial means the tension-only spring is
slack. It does **not** mean the bolt carries compression or that its washer
has a verified zero demand. Face compression is listed independently.

| Case | Bolt | Axial on host, N | Lateral on host XYZ, N | Lateral magnitude, N | Conditional 0.189 / 0.180 root one-bolt ratio |
| --- | --- | ---: | --- | ---: | ---: |
| a12-left | upright u1 | 0 (slack) | (0, +8.117, +4.751) | 9.405 | 0.0202 / 0.0215 |
| a12-left | upright u2 | 0 (slack) | (0, −7.746, −14.744) | 16.655 | 0.0365 / 0.0387 |
| a12-left | rail r1 | +20.495 (tension) | (+7.276, −8.397, +7.046) | 13.156 | 0.0274 / 0.0291 |
| a12-left | rail r2 | 0 (slack) | (+7.289, +7.585, −6.364) | 12.295 | 0.0254 / 0.0270 |
| k12-right | upright u1 | 0 (slack) | (0, +14.661, +9.249) | 17.335 | 0.0375 / 0.0398 |
| k12-right | upright u2 | 0 (slack) | (0, −2.789, −12.947) | 13.244 | 0.0280 / 0.0297 |
| k12-right | rail r1 | +19.668 (tension) | (+31.662, −12.666, +10.628) | 35.719 | 0.0755 / 0.0801 |
| k12-right | rail r2 | 0 (slack) | (+31.169, +8.203, −6.883) | 32.957 | 0.0711 / 0.0754 |

The one-bolt ratios reuse the existing dry DF-L wood-to-wood single-shear
reference helper: ¼-in nominal bolt, 45,000 psi assumed bending yield,
thread root throughout, 1.5-in host bearing, 5.5-in upright or 2.25-in rail
cleat bearing, and zero gap. The 0.189-in root is a typical value; 0.180 in
is a hypothetical sensitivity. Each force direction is projected onto the
modeled host and cleat grain axes in that **same run**, then divided by its
direction-specific one-bolt reference. These are isolated lateral components,
not adjusted capacities or bolt-group checks. Neither root is a measured
delivered minimum.

| Case / face | Active samples | Compression, N | Resultant force on host XYZ, N | Moment on host XYZ, N·mm |
| --- | ---: | ---: | --- | --- |
| a12-left / upright | 2 of 4 | 14.565 | (−14.564, +0.371, −9.993) | (+460.337, −434.859, +0.977) |
| a12-left / rail | 2 of 4 | 19.808 | (+14.565, −0.371, +1.207) | (−542.837, +604.370, −0.958) |
| k12-right / upright | 4 of 4 | 62.831 | (−62.831, +11.872, −3.698) | (+477.049, −426.758, +28.829) |
| k12-right / rail | 2 of 4 | 31.196 | (+62.831, −11.873, −5.086) | (−559.547, +596.311, −28.834) |

The active upright samples are `0_0` and `0_1` for a12-left and all four
for k12-right. The active rail samples are `1_0` and `1_1` for both cases.
They are modeled spring samples, not measured physical pressure patches.
The largest isolated one-bolt ratio here is 0.0801 at k12-right rail r1
under the hypothetical 0.180-in root. That is **not** a governing joint
utilization. The machine output leaves group, washer, cleat, contact, and
whole-joint utilization `null`; it also leaves design pass `null` and
drilling release false. Group direction and force sharing, washer/bolt
axial resistance, drilled cleat section, face bearing, other stations,
and complete load path remain open. No final capacity or drill release follows.
