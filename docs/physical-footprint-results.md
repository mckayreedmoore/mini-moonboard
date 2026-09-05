# Shallow 2×8: physical leg-footprint comparison

**Development geometry and screening evidence, not construction approval.**
Intended use remains one climber, 250 lb maximum; 150/200 lb are comparison
cases and 300 lb is a sensitivity, not a validated rating. Pads are separate,
and neither anchoring nor ballast is credited.

## Selected next candidate

Move each lower leg's floor centre **100 mm / 3.94 in toward the leg side**.
This is the smallest **tested** extension meeting the 1.5 edge-moment target
throughout the stated 96-case user-load envelope. It is not a continuous
optimization, a final required clearance, or a complete stability pass.

- [Interactive 100 mm extension](https://mckayreedmoore.github.io/mini-moonboard/?model=2x8-foot100)
- [STEP assembly](../exports/footprint-frame/2x8-foot100.step)
- [Metric/imperial parts schedule](../exports/footprint-frame/2x8-foot100_parts.csv)
- [Nominal connection schedule](../exports/footprint-frame/2x8-foot100_connections.csv)
- [Machine-readable sweep](../fea/results/hybrid/physical_footprint.json)

![Extended-footprint climbing side](../exports/footprint-frame/2x8-foot100_front.png)
![Extended-footprint backing](../exports/footprint-frame/2x8-foot100_rear.png)

The published [unextended shallow candidate](shallow-frame-results.md) and
plywood reference remain unchanged. The new viewer shows drilled nominal
geometry and hardware envelopes, not a validated joint/contact FEA model.

## Physical geometry, not a shifted support polygon

Each variant rebuilds the continuous hockey-stick leg's lower profile and
clips it to a level floor. Both legs retain **two glued 19.05 mm plywood
layers, 38.1 mm total**, and a 180 mm profile width. The upper attachment
region, four bolt stations per leg, other timber, angles and fasteners are
unchanged. The lower segment is not a solid-lumber 2×8 or a pin-ended strut.

Mass, three-dimensional centre of gravity and the convex hull of the actual
level floor faces are recalculated for every variant. Wood density is assumed
600 kg/m³ and custom angle steel 7850 kg/m³; fasteners, holds, glue and LEDs
are omitted. These are comparison assumptions, not measured installed masses.

| Foot-centre extension | Lower segment angle above floor | Leg-side extreme floor Y | Modelled mass | Lowest factor across 96 cases | Cases below 1.5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 mm / 0 in | 72.716° | 1398.255 mm | 195.308 kg | 1.1020 | 18 |
| 50 mm / 1.97 in | 70.893° | 1449.246 mm | 195.434 kg | 1.3947 | 2 |
| **100 mm / 3.94 in** | **69.109°** | **1500.331 mm** | **195.573 kg** | **1.8138** | **0** |
| 150 mm / 5.91 in | 67.366° | 1551.508 mm | 195.724 kg | 2.2199 | 0 |
| 200 mm / 7.87 in | 65.667° | 1602.773 mm | 195.885 kg | 2.5137 | 0 |

Positive extension follows world +Y toward the leg-side support edge,
independent of viewer orientation. The kicker-side toe stays Y=−159.067 mm.
At 100 mm, the floor-to-floor extreme depth is 1659.398 mm / 65.33 in;
this is **not** overall assembly depth or required climbing/fall clearance.
The leg-side toe moves 102.076 mm rather than exactly 100 mm because flattening
the fixed-width leg also lengthens its floor cut. The selected centroid is
X=5.748, Y=748.742, Z=1155.097 mm, in the existing CAD coordinates.

The full assembly's overall Y bounds stay −159.067 to 1573.864 mm
for both the unextended and selected variants: **1732.931 mm / 68.23 in overall
depth**; the fastener envelopes lie inside those bounds. The board still
overhangs the extended foot. Thus this change increases
floor-contact reach without increasing that assembly bounding-box depth; it
does not move the board itself or imply unchanged required fall clearance.

## User-weight envelope

For each physical geometry, the same 96 combinations cover four weights,
1×/2× gravity load, full/80% modelled mass, 0/50/100 mm hold standoff and
0/300 N horizontal load. Every main and kicker hold is checked against every
support-polygon edge; horizontal direction is maximized analytically over all
azimuths, not just a few sampled directions. The reduced-mass cases keep each
candidate's centroid fixed; they do not simulate selectively removing parts.

The 2× gravity and 300 N horizontal values are illustrative sensitivities,
not validated dynamic load histories or prescribed design combinations.

| Climber | Minimum factor, selected 100 mm extension |
| --- | ---: |
| 150 lb / 68.0 kg | 1.9093 |
| 200 lb / 90.7 kg | 1.8764 |
| 250 lb / 113.4 kg, intended maximum | 1.8445 |
| 300 lb / 136.1 kg, sensitivity only | 1.8138 |

The governing selected-candidate case is 300 lb at 2× gravity, 80% frame mass,
100 mm hold standoff and 300 N toward the leg-side edge at row 12. The
associated edge-moment factor is 1.8138. Passing this target means only that
the stated rigid-body overturning screen has sufficient moment margin.

The global horizontal/vertical force ratio remains a translational friction
demand, not a local sliding or yaw-equilibrium check. Actual floor friction,
individual foot pressure and opposing horizontal support reactions are unknown.
Full flat CAD floor contact does not imply uniformly distributed pressure on
an actual uneven floor.

## Retained exploratory cases: still fail

All six legacy 2D row-12 cases are retained separately at full modelled mass.
The four downward/±300 N cases meet their 2D moment screen for all extensions.
**Both opposite exploratory board-normal vectors still require uplift for
every extension tested.** Neither is silently discarded or relabelled as a pass.

| Extension | Outward/downward normal factor | Inward/upward normal factor |
| --- | ---: | ---: |
| 0 mm | 0.676 | 0.567 |
| 50 mm | 0.743 | 0.569 |
| 100 mm | 0.814 | 0.571 |
| 150 mm | 0.887 | 0.572 |
| 200 mm | 0.965 | 0.574 |

Factors below 1 in these cases correspond to negative toe reactions: an
unanchored floor cannot supply the tensile restraint assumed by equilibrium.
Here **uplift means a support losing floor contact as the frame tips**, not
necessarily an upward applied load. The outward/downward case applies about
919 N horizontally and 771 N downward; it can lift the opposite support even
though its vertical load points down. The opposite exploratory case does have
an upward component. Neither vector is an established design requirement for
this installation; deciding the applicable load basis remains separate from
reporting the model's response.
Their applicability remains a load-basis question, not evidence that the
normal-direction scenarios are impossible. Increasing leg-side reach alone
does little for the opposite kicker-side tipping mechanism.

## Matched bulk FEA

The changed legs received their own frozen geometry and two matched solver
runs, each with six independent load cases. Both passed the actual-deck
load/support audit, finite displacement checks, force balance within 0.1 N,
moment balance within 1 N mm and positive final element-Jacobian checks.
[Published summaries and raw DAT results](../fea/results/hybrid/2x8-foot100/)
retain source/deck/result hashes and the support/load coordinates needed to
recheck equilibrium.

All comparisons use undrilled bulk timber, perfectly bonded touching timber,
fixed floor nodes, no gravity, and isotropic E=7000 MPa, nu=0.3. Steel and
fastener compliance are omitted. Loads are shared over five row-12 nodes near
A12/C12/F12/H12/K12. Displacement is the largest magnitude **among those five
loaded nodes**, not the maximum anywhere in the assembly.

| Independent load case | Plywood reference | Unextended shallow 2×8 | Selected +100 mm |
| --- | ---: | ---: | ---: |
| Downward 1.2 kN | 0.36846 mm | 0.85321 mm | 0.84622 mm |
| Downward 2.4 kN | 0.73693 mm | 1.70641 mm | 1.69243 mm |
| Downward 1.2 kN + outward 0.3 kN | 0.47714 mm | 1.09994 mm | 1.09002 mm |
| Downward 1.2 kN + inward 0.3 kN | 0.25996 mm | 0.60657 mm | 0.60252 mm |
| Outward/downward normal, exploratory | 0.57011 mm | 1.30466 mm | 1.29119 mm |
| Inward/upward normal, exploratory | 0.57011 mm | 1.30466 mm | 1.29119 mm |

Values above use the finer 40 mm mesh. The unchanged 2×10 and 2×12 downward
results are 0.54483 and 0.38900 mm respectively. The extension changes the
shallow candidate's sampled downward displacement by about −0.82%; it remains
about 2.30× the plywood reference. No allowable displacement or strength
criterion is established by these comparisons.

| Selected candidate mesh | Nodes | Minimum final Jacobian | Downward 1.2 kN |
| --- | ---: | ---: | ---: |
| 60 mm | 62,020 | 1010.250 | 0.84748 mm |
| 40 mm | 126,126 | 955.876 | 0.84622 mm |

The downward result changes by about 0.15% between these meshes; the largest
change across the six cases is 0.182%, relative to the finer result. This is a
two-mesh consistency check for sampled displacement, not proof of local stress
convergence. Equal opposite normal-load displacement magnitudes follow from
the linear, bilaterally restrained model; they do not overrule the separate
unanchored uplift findings.

For the same downward direction and five-node distribution, the linear
no-gravity result can be rescaled to the user-weight cases. These are
**algebraic rescalings, not four additional FEA solves or dynamic ratings**:

| Climber | Plywood reference | Unextended shallow 2×8 | Selected +100 mm |
| --- | ---: | ---: | ---: |
| 150 lb | 0.20488 mm | 0.47441 mm | 0.47052 mm |
| 200 lb | 0.27317 mm | 0.63254 mm | 0.62736 mm |
| 250 lb | 0.34146 mm | 0.79068 mm | 0.78420 mm |
| 300 lb sensitivity | 0.40975 mm | 0.94881 mm | 0.94104 mm |

The ideal-bonded, fixed-floor comparison cannot validate unanchored contact,
fastener capacity, glue lines, local knee stress or actual timber properties.
The historical [plywood](../fea/results/box_audited_40_7000.json) and
[unextended shallow results](../fea/results/hybrid/2x8-shallow/box_audited_40_7000.json)
are retained without alteration.

## Connection demand and completion boundary

The sweep records total external floor-force resultants. The maximum for the
selected geometry is **4.597 kN**, over all 96 rows. This is **not an individual
leg, joint, bolt or screw load**, and is not a hardware capacity requirement.
Lateral load sharing, upper-joint moments and local sliding require a separate
contact/connection model; the four-bolt upper leg connection is not a frictionless
pin. See the [connection and floor-contact gates](footprint-connection-gates.md)
for the conditional leg free body, material/adhesive requirements and next
joint detail to investigate.

Geometry checks cover valid single solids, full level floor cuts, unchanged
upper attachment regions, other-member collisions and the selected variant's
inherited connection, hardware, tool, LED and routing envelopes. The sweep's
tests regenerate actual CAD mass/CG/floor boundaries and all 480 envelope rows,
verify source hashes and retain exact equality with the old zero-extension
96-case record. These are nominal geometry and arithmetic checks, not rated
material, connection, fatigue or fabrication approval.

Next decision: retain the **100 mm extension provisionally** for contact/joint
development, while keeping the failing exploratory directions visible. Obtain
structural plywood and lumber properties, a suitable structural lamination
process, and rated hardware details before making a capacity conclusion.
Qualified structural review and controlled physical verification remain gates
before construction or climbing.

Reproduce the sweep and checks:

```sh
uv run python -m fea.physical_footprint
uv run pytest -q tests/test_physical_footprint.py tests/test_footprint_frame.py
```

Reproduce the selected candidate's separate bulk FEA using the existing
Docker image; do not regenerate its frozen geometry while solves are running:

```sh
uv run python -m fea.prepare_hybrid_frame --candidate 2x8-foot100
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 fea/solve_box_frame.py --candidate 2x8-foot100 --size 60 --audited
# Repeat the Docker command with --size 40.
uv run python -m fea.record_hybrid_results --candidate 2x8-foot100
uv run pytest -q tests/test_hybrid_results.py
```
