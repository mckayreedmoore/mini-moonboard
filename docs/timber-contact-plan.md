# Intended panel-edge contact diagnostic

The next numerical step builds on the completed
[released-interface sensitivity](timber-release-results.md), not a new frame
redesign. The physical target is unilateral panel/leg contact while retaining
the ideal rim/common-edge connection. Even a successful result would describe
that ideal aggregate connection, not four real bolt forces.

The [eccentric compression control](panel-contact-control.md) is now complete:
four penalty/increment combinations pass independent force/moment and local-law
checks. It is a limited output-validation prerequisite, not the actual frame
contact solution or a separation/recontact test.

## Prepared geometry

`fea/timber_contact_faces.py` reconstructs explicit CalculiX S1–S4 face labels
from the authenticated timber mesh and the proven release node map. Per side,
the actual-mesh test establishes:

- 34 matching quadratic triangular panel/leg face pairs;
- complete coverage of all 72 released old nodes;
- 9,218.148831 mm² interface area;
- identical paired physical coordinates and opposite outward X normals;
- no finite-area rim face included, with 29 common-edge nodes retained.

Normals are checked against the owning tetrahedron, not guessed from face-node
order. A changed node map or incomplete surface inventory fails the check.
This is geometry preparation only: no contact law or solver deck is introduced
by this helper.

```bash
uv run pytest -q tests/test_timber_contact_faces.py
```

## Bounded implementation sequence

1. Validate frictionless face-to-face penalty contact output on an independently
   restrained matching C3D10 control coupon. Require reported contact force and
   moment to agree with an independent free-body reaction calculation at the
   same reference. Use nonuniform/eccentric loading so a force-only check cannot
   hide a moment error. Retain every actuator reaction.
2. Only if the control is interpretable, add two explicit contact pairs to the
   existing released frame. Preserve material, floor restraints, load point,
   node coordinates and retained rim/common-edge bond. State the numerical
   penalty assumption; do not call it a measured wood contact stiffness.
3. Solve the prescribed combined K12 load directly. Unilateral contact is
   nonlinear: the previous three-basis linear superposition is not valid here.
4. Audit complete surfaces, compression-only pressure, gap/penalty consistency,
   force and moment equilibrium, and a bounded penalty/increment comparison.
   Preserve failed runs; do not restore an artificial panel tie to obtain a pass.
5. For each leg, recover `leg-on-rim/common-edge = floor-on-leg + panel-on-leg`,
   expressing all forces and moments at the same reference. Use the audited
   contact wrench, not force multiplied by a geometric contact centroid. Zero
   leg gravity remains an explicit diagnostic assumption.

## Known reuse limits

The existing [contact-formulation record](contact-formulation-options.md)
documents a penalty-contact moment-transfer discrepancy in a different
configuration. The existing pair-output helpers are therefore candidates for
reuse, not proof of correct force recovery at this interface. A matching
control is required before using the contact subtraction above.

The [leg-section record](leg-section-response.md) also records failed native
C3D10 section-force recovery; it is not an approved shortcut. Switching to
MORTAR would require different output/reaction validation and is not an
automatic repair. None of these diagnostics establishes actual bolted-rim
compliance, independent-ply transfer, unanchored floor contact or joint strength.

## Frame-run interpretation contract

The first frame experiment uses the authenticated `timber-base-development`
40 mm mesh, not `wide-principal-development`. This deliberate same-mesh
comparison isolates the interface formulation from the changed principals and
base blocks. Its results must not be relabeled as the current wider candidate's
connection demands.

The prescribed load is one direct combined K12 case: 300 lb climber weight,
factor two on gravity-direction force, and 300 N in global positive Y. The
load ramps through a nonlinear static step. Floor nodes remain fixed in XYZ;
the load case has no frame self-weight. This is not a simulation of a falling
person or a complete design load combination.

Before reporting any inferred connection action, require:

- the complete prepared face inventory and unchanged archived mesh provenance;
- completed load history and finite output at every converged endpoint;
- global force and moment equilibrium using the deformed load position;
- zero movement of every prescribed floor support;
- correctly named left and right contact-pair wrenches;
- compression-only, frictionless local contact output consistent with the
  numerical penalty law, with each reported face belonging to its declared
  slave surface.

Open faces need not appear in the active contact output. An absent active face
is not permission to omit that face from the prepared contact surface. Likewise,
an inferred rim wrench is not independently validated by merely adding its two
terms: no direct rim reaction measurement is available in this bonded mesh.
The control coupon supports interpreting the contact output, but it does not
validate real bolt sharing or the retained common-edge constraint.

Preserve a failed or incomplete solver attempt with its inputs and diagnostics.
Do not relax equilibrium tolerances, add a panel tie, or substitute the released
linear basis combination to force acceptance. A successful first run is still
provisional until the bounded penalty/increment comparison is examined.

## Reproducing the first direct frame run

The implemented adapter is `fea/timber_panel_contact.py`; its companion audit
is `fea/timber_panel_contact_audit.py`. Preparation reconstructs both the
authenticated released mesh and the complete panel/leg surface inventories.
The first numerical penalty is 10,000 N/mm³, with maximum load increment 0.125.
These are numerical settings, not measured wood-contact properties. The solver
attempt is limited to 600 seconds and two OpenMP threads.

```bash
uv run python -m fea.timber_panel_contact prepare
docker run --rm --user 1000:1000 -e OMP_NUM_THREADS=2 \
  -v "$PWD":/work -w /work mini-moonboard-fea:release-v1 \
  python3 -m fea.timber_panel_contact solve
```

The Docker image and NumPy addition are documented in the
[release results](timber-release-results.md). Preparation refuses an existing
output directory. A repeat must use a fresh explicit `--directory`; never
delete a failed attempt to reuse its name. Penalty and increment overrides
belong to `prepare`, not `solve`, so the launched settings remain frozen.

The adapter's `execution.json` means only that the solver exited successfully.
It is not an accepted result; the contact and complete-history audit must pass
separately before interpreting the response. The first attempt reached load
factor 0.228125 before its 600-second limit expired. Its
[source-bound incomplete archive](../fea/results/timber-panel-contact-incomplete/README.md)
is preserved separately from accepted results. Full-load contact recovery and
the bounded sensitivity comparison remain unfinished; no structural failure or
approval can be inferred from this runtime limit.
