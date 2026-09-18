# Square-cut candidates: structural diagnostic review

**Neither candidate is ready for construction or climbing.** A remains the more
promising joint-development candidate; B fails a loaded-edge-distance screening
check in its new wood blocks. Passing the rigid-body moment screen or obtaining
small bonded-model displacements does not qualify either design's connections.
This review does not change the geometry or supersede professional validation.

The candidates are [A: purchased brackets](square-cut-comparison.md) and
[B: bolted wood blocks](square-cut-comparison.md). The earlier geometry,
collision, export and browser checks establish inspection-model consistency,
not structural resistance.

## Joint findings

### B: block bolt placement fails the selected loaded-edge screen

Each of the twelve new blocks has grain along its 139.7 mm N dimension and a
38.1 mm S dimension. Its two 9.525 mm-diameter upright bolts run along X and are
centered across S. Consequently, downhill S force transferred from the block to
the upright loads the block perpendicular to grain, with only **19.05 mm (2D)**
between each bolt center and the loaded edge. The selected **4D screen requires
38.1 mm**, twice the available distance. This affects all 24 block-to-upright
bolts, not just one visually tight corner.

The basis is the American Wood Council's discussion of perpendicular-to-grain
loaded-edge distance in NDS Commentary C12.5.1.3. This is a design screening
finding, not a formal jurisdictional code-compliance determination. Splitting
and connection resistance cannot be inferred from low continuum stress alone.
[AWC NDS commentary](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf)

Other B margins also require directional checks: the upright bolts are 50 mm
apart along grain, their nearest grain-end distance is 44.85 mm, and the beam
bolt has only 25.4 mm to one X edge of its block. These are not interchangeable
with the loaded S-edge finding; their significance depends on actual joint
force direction and the applicable connection calculation. The lower blocks
are above the lower beams: they are uphill stops, not gravity-bearing seats.

### A: purchased connectors remain unqualified for this application

A contains twelve ML24Z representations and six SDS25112 screws per connector.
The manufacturer specifies a 12-gauge, 2 by 2 by 4 inch connector and separate
screw purchase. However, the CAD factory-hole locations and bend remain proxies.
The actual purchased configuration, wood species, member thickness, installation,
force directions and combined loading must match an applicable manufacturer
design basis. A catalog designation alone is not an inclined-frame joint rating.
See page 323 and its lateral-load engineering-letter reference in the
[Simpson Wood Construction Connectors catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog).

### Shared load path and connection gaps

At 40 degrees from vertical, a static 250 lb downward climber force resolves to
approximately **852 N downhill along the board and 715 N outward from its
backing**, before any dynamic amplification. The outward component separates
the face and ledges from the frame. Compression-only bearing cannot carry it;
panel fastener head pull-through, withdrawal and local bending matter.

The new 63.5 mm (2.5 inch) ledge screws pass through 38.1 mm (1.5 inch) ledges,
leaving **25.4 mm (1 inch) nominal receiver penetration**. Effective threaded
engagement may be smaller after tip and unthreaded-shank deductions. Their exact
products, head seats, pilots and resistances are still unspecified. Shortening
these screws improved assembly access; it did not establish sufficient strength.

Both candidates also retain unresolved plywood face/net-section behavior,
kicker-splice load transfer, leg bolt-group eccentricity, independent plywood
ply load sharing, local bearing and splitting, cyclic loosening/fatigue, and
actual floor contact/friction. The purchased AC Douglas-fir face plywood is not
automatically assigned the properties of the leg plywood or solid lumber.

## Current-CAD rigid-body stability screen

The calculation uses each candidate's actual drilled part inventory and floor
contact polygon. Assumed wood density is 600 kg/m³; A's connector proxies use
7,850 kg/m³. Calculated included masses are **189.17 kg for A** and **189.87 kg
for B**. Fasteners, holds, wiring, LEDs and glue are omitted. These are assumed
model masses, not measured completed-board weights.

For each climber weight, 24 combinations cover 1×/2× downward force, 80%/100%
included mass, 0/50/100 mm outward hold standoff, and 0/300 N horizontal force.
Each combination evaluates all main/kicker hold locations and the analytical
worst horizontal direction for each support-polygon edge. Mass scaling keeps
the center of mass fixed; it does not bound every possible material distribution.

| Climber weight | A: minimum moment factor | B: minimum moment factor | A: maximum friction demand | B: maximum friction demand |
| --- | ---: | ---: | ---: | ---: |
| 150 lb / 68.0 kg | 1.969 | 1.976 | 0.1394 | 0.1391 |
| 200 lb / 90.7 kg | 1.935 | 1.942 | 0.1264 | 0.1261 |
| 250 lb / 113.4 kg | 1.902 | 1.909 | 0.1156 | 0.1153 |
| 300 lb / 136.1 kg | 1.870 | 1.877 | 0.1064 | 0.1062 |

All **192 candidate/weight/sensitivity combinations** exceed the illustrative
1.5 edge-moment target. The factor compares dead restoring moment with the
destabilizing net live moment at a governing edge. It is not a strength factor
of safety or a certified stability rating.

Friction demand is the necessary aggregate horizontal-force/vertical-force
ratio, not a measured coefficient or a sliding pass. Yaw, distribution of
friction among feet, uneven flooring, flexible joints, contact separation and
dynamic response are not resolved. A person changing holds can produce a
different load distribution from the single-resultant screen. The intended
one-climber 250 lb maximum and 300 lb sensitivity remain assumptions, not ratings.

The historical opposite 1.2 kN board-normal vectors were also checked separately
at row 12 with full modeled dead mass. Both still demand uplift: A needs about
171 N of unavailable kicker-side tension in the outward/downward case and 880 N
of unavailable rear-leg tension in the inward/upward case; B needs about 168 N
and 877 N respectively. These exploratory vectors are not established governing
climbing loads, but their failures are retained rather than hidden by the
192-case downward-force envelope. Fixed-floor FEA can resist this fictitious
tension; the actual unanchored floor cannot.

The [load-basis review](hybrid-load-basis.md) distinguishes sourced provisions
from project sensitivities. The [CWA document](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf)
provides the historical 1.2 kN unroped-climber load and 1.5 overturning basis;
its applicability and the complete governing envelope still require review.

Evidence: [A stability record](../fea/results/square-cut/square-cut-bracket/stability.json),
[B stability record](../fea/results/square-cut/square-cut-wood-blocks/stability.json),
and [combined evidence report](../fea/results/square-cut/report.json).

## Completed ideal-bonded FEA comparison

On 2026-09-07, CalculiX completed six independent load cases for each candidate
at 60 and 40 mm nominal mesh settings: **24 completed case solutions**. The
following values use the finer mesh. They are the maximum displacement
magnitudes among five loaded row-12 nodes, not the global maximum or an
allowable-deflection check.

| Independent load case | A displacement, mm | B displacement, mm |
| --- | ---: | ---: |
| Downward 1.2 kN | 1.243 | 1.174 |
| Downward 2.4 kN | 2.485 | 2.348 |
| Downward 1.2 kN + outward 0.3 kN | 1.606 | 1.517 |
| Downward 1.2 kN + inward 0.3 kN | 0.880 | 0.832 |
| Exploratory outward/downward normal 1.2 kN | 1.911 | 1.804 |
| Exploratory inward/upward normal 1.2 kN | 1.911 | 1.804 |

A's baseline changes from 1.240 to 1.243 mm with refinement (0.181%); B's changes
from 1.173 to 1.174 mm (0.120%). Maximum change across the six cases is 0.324%
for A and 0.274% for B. Fine meshes contain 153,291/154,174 nodes and
83,217/83,921 quadratic tetrahedra respectively. Nearest load nodes lie within
9.80 mm of their intended targets across all four runs, but move between meshes.
This supports numerical consistency for the sampled displacements, not formal
stress convergence or a bound on real construction behavior.

All four meshes pass positive final Jacobian and connected-mesh checks. Gmsh
reported intermediate distortion warnings before high-order optimization;
the final minimum determinants are positive (fine A 0.738, B 0.713).
Every load case passes complete finite output, force balance within 0.1 N and
moment balance within 1 N mm. Independent replay also checks disjoint floor
reaction patches, bounded target mapping, doubled-load linearity and opposite
normal-load symmetry. A's first 60 mm run preceded the added mapping/disjointness
guards; its saved deck and output passed those checks during final publication.

This is deliberately an **optimistic ideal-bonded stiffness diagnostic**:

- Every touching timber interface, including the independent leg plies, is
  artificially bonded. A's connectors and all actual fasteners are omitted;
  its butt joints are bonded instead. B's blocks are bonded too.
- Floor nodes are fixed in X, Y and Z. This is not the unanchored floor-contact
  condition, and tensile support reactions do not demonstrate available support.
- Material is isotropic with E = 7,000 MPa and Poisson ratio 0.3. It does not
  model lumber/plywood grain directions, damage or design strength.
- Bulk geometry omits face and connection drilling while retaining existing
  service reliefs. Self-weight, connection slip, local fastener behavior,
  buckling and dynamic loading are absent.
- The force is shared equally among five row-12 locations. This does not bound
  a concentrated one-hold load or every climber position.

The model cannot give joint capacities, a user weight rating, a rigorous
real-construction displacement bound, or a ranking of A versus B joint strength.
Source hashes, actual nodal forces, reaction-force/moment balance, mesh
connectivity and positive Jacobians are audited separately from these limitations.

## Reproduction

Run from the repository root, with the current published CAD source closure.
Preparation requires the existing CadQuery environment; meshing and CalculiX
use the existing Docker toolchain. Preserve existing result directories: the
preparer and solver context creation refuse to overwrite their frozen records.
For a fresh replay, use a separate checkout with no generated square-cut directory.

```bash
uv run python -m fea.prepare_easy_structural
docker build -t mini-moonboard-fea:box-v1 -f fea/Dockerfile .
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 -m fea.solve_easy_frame --candidate square-cut-bracket --size 60
```

Repeat the solver command for `--size 40` and for candidate
`square-cut-wood-blocks`. The default modulus is 7,000 MPa. Run these expensive
CAD/meshing/solver stages serially. Input STEP, case metadata, decks, logs,
solver output, source hashes and summaries remain under each candidate's
`fea/generated/square-cut/` directory.

```bash
uv run python -m fea.publish_easy_structural
uv run pytest tests/test_easy_structural.py -q
```

The [published evidence](../fea/results/square-cut/report.json) includes compressed
actual INP decks, DAT output, solver logs, launch contexts and summaries, plus
the drilled-CAD stability records. The tests replay published force/moment and
displacement results without Docker. Launch hashes and later audit-source hashes
are distinguished; no historical model or source-bound export was changed.
All 17 focused tests passed, including rejection witnesses for altered loads,
missing/nonfinite output, force/moment imbalance and B's current bolt-edge defect.
Passing that last regression records a known design failure, not acceptance.
Independent structural-interpretation and publication reviews found no remaining
substantial issues in this screening scope after the provenance checks were fixed.

## Decision

**Do not build or climb either candidate on this evidence alone.** B needs a
resolved block-joint detail before an adequacy determination. A first needs
verified purchased-connector geometry and application-specific resistance.
Both need selected screw products and common-joint checks, followed by an
orthotropic/net-section and realistic connection/contact assessment. Qualified
structural review and a controlled validation plan remain necessary; no person
should be used as an improvised proof load.
