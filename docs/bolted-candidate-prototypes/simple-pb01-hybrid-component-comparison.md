# PB01 a12-left conditional component comparison

Run `uv run python -m scripts.simple_pb01_hybrid_component_comparison` from the
repository root. It prints JSON and writes no files. The local-action extractor
authenticates the frozen archive (`fc298a3a...f4805546`), report
(`c10b2b2d...b0c4918`), 260 source snapshots, final cycle, a12-left quarter
pose, ownership, equilibrium, and **23 old ML24Z/SDS proxy stations**. A changed
source identity fails before comparison. This is one diagnostic hybrid case,
not same-configuration V4 demand at all stations.

Each signed axial value below is force **on the host** dotted with the recorded
host-to-cleat installation axis: +X for principal bolts, and approximately
`(0, 0.642788, 0.766044)` for rail bolts. The lateral vector in the JSON is
the signed force remaining after that projection; its length is tabulated.
For this host-first model, positive axial *may* represent tensile bolt clamp
at the host head/washer. Negative spring axial may represent nonphysical
compression that real contact would carry. Spring sign and partition do not
prove actual washer force or seating.

The [2024 NDS root-only one-bolt helper](../../mini_moonboard/bolted_wood_wood_yield.py)
uses dry solid DF-L, 45,000 psi bolt-class bending yield, zero face gap,
thread root throughout both wood bearing lengths, and six single-shear modes.
The host is 1.5 in; the cleat is 5.5 in at the principal face and 2.25 in at
the rail face. The 0.189-in root is an NDS *typical*, not a delivered minimum;
0.180 in is a hypothetical sensitivity. The 0° and 90° inputs are endpoint
component sensitivities, not established directions for other cases. Mode IV
governs both endpoints here. References
are 124.82/99.86 lbf at 0°/90° for 0.189 in, and 117.65/94.12 lbf for
0.180 in. Each ratio is that bolt's lateral magnitude in lbf divided by its
one-bolt reference; no group multiplier is used.

The frozen pose also establishes the grain axes: the inclined principal
grain is local T, the service rail grain is X, and the cleat grain is
local N. Projecting each **modeled lateral force vector** onto both
member grain axes gives a direction-specific component sensitivity for
this one hybrid scenario. The two angles differ at each bolt; the 2024
small-root reduction uses the larger angle. These modeled directions are
not verified future loading directions or six-case envelopes.

| Bolt | Host angle | Cleat angle | 0.189 modeled-direction ratio | 0.180 modeled-direction ratio |
| --- | ---: | ---: | ---: | ---: |
| Principal u1 | 12.56° | 77.44° | 0.0327 | 0.0347 |
| Principal u2 | 7.61° | 82.39° | 0.0606 | 0.0643 |
| Rail r1 | 44.85° | 45.15° | 0.0259 | 0.0275 |
| Rail r2 | 53.11° | 36.89° | 0.0317 | 0.0336 |

| Host bolt | Axial on host (N) | Lateral (N) | 0.189 ratio 0°/90° | 0.180 ratio 0°/90° | Positive axial / wood annulus reference |
| --- | ---: | ---: | ---: | ---: | ---: |
| Principal u1 | -0.635 | 14.939 | 0.0269 / 0.0336 | 0.0285 / 0.0357 | null |
| Principal u2 | -5.356 | 27.399 | 0.0493 / 0.0617 | 0.0524 / 0.0654 | null |
| Rail r1 | +31.367 | 12.799 | 0.0231 / 0.0288 | 0.0245 / 0.0306 | 0.0325 conditional |
| Rail r2 | -22.122 | 15.321 | 0.0276 / 0.0345 | 0.0293 / 0.0366 | null |

The [washer helper](../../mini_moonboard/bolted_timber_checks.py) gives
216.68 lbf for an ideal full wood-contact annulus with 0.734-in OD,
0.312-in ID, 7.5-mm bore and 625 psi dry DF-L perpendicular-grain bearing.
The r1 ratio compares only its **positive modeled host axial** with this
reference. It is not a proven washer demand or an axial check pass. The
negative values have no axial utilization; taking their absolute values
would assume a load path this spring/contact model has not established.
Actual washer metal stiffness, full wood contact, preload and load sharing
remain unknown.

For every bolt, bolt axial steel/nut, washer metal stiffness, group behavior,
cleat resistance and contact behavior are explicitly `null` in the JSON.
The complete-joint verdict is `null` for **all six cases** (a12-rear,
a12-forward, a12-left, k12-right, k12-rear, a1-rear), including this hybrid
a12-left. Joint utilization and design pass are `null`. These small
component ratios do not establish a usable joint or drilling release.
