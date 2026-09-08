# Intended panel-edge contact diagnostic

The next numerical step builds on the completed
[released-interface sensitivity](timber-release-results.md), not a new frame
redesign. The physical target is unilateral panel/leg contact while retaining
the ideal rim/common-edge connection. Even a successful result would describe
that ideal aggregate connection, not four real bolt forces.

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
