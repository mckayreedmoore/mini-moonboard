# C10 panel connection comparison

## Frozen scope

The comparison uses revision `630a567`, including the trimmed cheek splices.
The C10 upper-left climbing panel is unchanged from the previous drilled-panel
screen: the preparer checks the symmetric volume difference against the exported
STEP before reusing its 20/15 mm meshes. The frame/viewer design is not altered.
This is a local connection sensitivity study, not a complete unanchored-board
analysis or permission to climb.

## What is different from the fixed-head screen

The panel's actual countersinks now have distributed, finite-stiffness axial
supports instead of fixed XYZ nodes. Each head resists pull-away only. Its
effective spring stiffness lumps screw withdrawal, head seating and receiving
wood compliance; neither steel threads nor progressive wood failure is resolved.
The total stiffness is normalized per head, not per mesh node.

Existing backing footprints are sampled from the actual CAD battens, including
hardware reliefs. They resist compression and permit separation. This is a
frictionless, rigid-ground backing idealization with a finite penalty, not a
deformable frame. Three in-plane restraints remove rigid-body motion; none fixes
panel-normal movement. Load remains the separate 1.2 kN normal C10 flange-patch
sensitivity, not a verified worst-case climbing load or a global-frame demand.

CalculiX SPRINGA elements implement the unilateral laws. Their ground nodes
are 10,000 mm behind the corresponding panel nodes to approximate axial-only
supports; those are mathematical anchors, not physical ground connections.
Geometric nonlinearity is enabled, so tiny transverse spring components can
arise. A 1e-9 mm spring-law transition avoids an undefined initial tangent;
the bounded wrong-sign force is recorded rather than concealed. Iteration
limits are increased to allow changing contact states; force/displacement
convergence tolerances are not relaxed. The unit check solves both pull and push and verifies their different
stiffnesses. See the [CalculiX 2.21 manual, spring elements and *SPRING](https://www.dhondt.de/ccx_2.21.pdf).

## Alternatives and uncertain inputs

| Case | Change | What it can answer |
| --- | --- | --- |
| Baseline | Current 12 screws and perimeter/seam backing | Reference with flexible unilateral connections |
| Stiffer attachment | Double effective axial stiffness at the same 12 locations | Whether developing a stiffer connection is worth investigating; no product is selected |
| Closer backing | Add an analysis-only 70 mm central longitudinal bearing strip, relieved around hold/LED locations; no new screws | Whether passive backing alone helps under pull-away loading |

The closer-backing case deliberately does **not** assume that timber behind a
panel can pull it back. A batten with added screws is a different design and
would require hole placement, clearance, connection and framing checks. These
two alternatives isolate connection stiffness from passive backing; neither
is a construction-ready hardware revision.

Baseline effective axial stiffness is an **assumed 1000 N/mm per screw**, with
100 and 10,000 N/mm sensitivity endpoints. These are decade-spaced mathematical
probes, not measured values or defensible upper/lower bounds for the purchased
materials. The backing penalty is 100 N/mm³, with sensitivity checks needed to
distinguish numerical penetration from behavior. Plywood remains the explicitly
assumed isotropic E=7000 MPa, nu=0.3. Directional plywood properties and failure
limits remain unknown; no stress utilization or screw capacity is calculated.

The CAD still specifies generic #10 x 2-inch screws. An allowable withdrawal
load is not a force/displacement curve and cannot supply spring stiffness.
[Simpson's technical guide](https://www.strongtie.com/resources/literature/fastening-systems-technical-supplement)
provides product-specific load tables and installation details, but does not
establish a rating for our unidentified screws and laminated birch backing.
[GRK's R4 product listing](https://www.grkfasteners.com/grk-products/structural-framing-screws/r4-multi-purpose-screw)
and [technical documents](https://www.grkfasteners.com/technical-information/technical-documentation)
are candidate specification sources, not automatic substitutions for the CAD
placeholder. Verify exact diameter/length, head geometry, thread penetration,
substrate applicability and required edge distances before selecting a product.
The [USDA Wood Handbook](https://research.fs.usda.gov/fpl/wood-handbook), chapters
5, 8 and 12, provides background on mechanical properties, fastening and panel
products; it is not certification of the user's sheet stock.

## Numerical acceptance and evidence

Results are accepted only at the full final load, with complete finite nodal
and C3D10 integration-point output. Checks compare every support reaction to
its unilateral force law, reject spring extensions outside the tabulated range,
and verify total force and moment equilibrium using deformed coordinates.
The actual INP/DAT and frozen mesh metadata are hashed. Full raw outputs remain
under ignored `fea/generated/connection/`; compact checked records will be
published after the comparison and refinement complete.

```bash
uv run python -m fea.prepare_connection --size 20
uv run python -m fea.prepare_connection --size 15
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 fea/check_unilateral_springs.py
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 fea/solve_connection.py --size 20 --variant baseline
# Variants: stiffer_attachment, closer_backing.
# Sensitivities: --stiffness, --penalty, --modulus; reversal: --push.
# --reparse checks completed raw evidence without rerunning CalculiX.
```

The preparation requires the earlier actual drilled-panel C10 INP and STEP
exports in `fea/generated/`. Regenerate those with the
[panel screen workflow](updated-board-fea.md) if absent. A geometry mismatch
stops reuse. Do not regenerate frozen meshes while their solves are running.

## Results

The comparison is in progress. Accepted preliminary results at 1.2 kN C10
pull-away loading are:

| Case | Mesh | Maximum panel displacement | Largest effective head tension |
| --- | ---: | ---: | ---: |
| Baseline, assumed 1000 N/mm per head | 20 mm | 4.489 mm | 346 N |
| Baseline, assumed 1000 N/mm per head | 15 mm | 4.494 mm | 345 N |
| Stiffer attachment, 2000 N/mm per head | 20 mm | 4.019 mm | 498 N |
| Closer passive backing, 1000 N/mm per head, 0.000001 mm initial clearance | 20 mm | 4.489 mm | 346 N |
| Softer-property sensitivity, 100 N/mm per head | 20 mm | 6.622 mm | 187 N |
| Stiffer-property sensitivity, 10,000 N/mm per head | 20 mm | 3.195 mm | 786 N |

Doubling the assumed attachment stiffness reduces displacement about 10.5%,
but increases the maximum effective head tension about 44%. Backing compression
and attachment tension form a prying reaction pattern: total head tension can
exceed the applied 1200 N while their signed resultant remains in equilibrium.
This is not a screw-capacity verdict. More stiffness alone is not automatically
the best connection change.

The baseline mesh comparison changes displacement by 0.13% and maximum head
tension by 0.25%. The sampled backing footprint area changes by about 0.3%;
curved head and flange feature resolution remains inherited from the earlier
meshes. This supports numerical consistency for these sampled quantities, not
verified material behavior or full stress convergence.

The zero-clearance closer-backing trials at penalties 100 and 10 N/mm³ did
not converge in the attempted iterations and were stopped without accepted
results. The 0.000001 mm initial-clearance case converged with open contact
at initialization. The added strip carries zero compressive load in that case;
the panel moves away from it. A matching baseline-clearance check and finer
alternative meshes are still underway. The clearance is numerical, not a
measured manufacturing gap. Solver difficulty is not a structural failure
finding.

Reducing the baseline backing penalty from 100 to 10 N/mm³ changes displacement
from 4.489 to 4.517 mm (0.62%) and maximum effective head tension from 346
to 334 N (3.5%). Maximum numerical penetration rises from 0.0064 to 0.0348 mm.
This is a penalty sensitivity, not a measured backing compression modulus.

The checked cases' summed absolute transverse anchor forces are below 0.024 N,
compared with the applied 1200 N. The wrong-sign spring regularization bound
is below 0.031 N. Input/output hashes are distinct from the recorded re-audit
context: current script/metadata hashes are not immutable execution provenance.

No final design recommendation has been established while the remaining
alternative and sensitivity runs are underway.
