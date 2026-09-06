# Evidence needed for the frame decision

This tracks the broad design-recommendation objective, not just completion of
a solver run. Original plywood, 2×8, 2×10 and 2×12 candidates and their frozen
results remain references. One climber, 250 lb intended maximum, with 150/200 lb
comparisons and 300 lb sensitivity; these are not certified user ratings.

## Current development preference

Retain **2x8-foot100 as the comparison baseline**. Do not select deeper rims to
solve an unidentified connection, material or floor-interface problem. Evaluate
a separate side-tied base as a way to close spreading forces internally; it is
not yet a selected design or a substitute for global sliding/tipping checks.

| Decision requirement | Current evidence | Work still required |
| --- | --- | --- |
| Preserve and compare the original candidates | [Physical footprint and matched stiffness studies](physical-footprint-results.md) retain earlier results | Keep alternative geometry/results separately named; do not silently change reference mass, material or restraints |
| A trustworthy unanchored numerical baseline | [Continuation study](floor-contact-continuation.md): μ=0.5 completes all solver steps, but contact moment transfer fails the independent audit | Increment refinement, force/moment transfer checks, local contact and mesh/history sensitivity; no acceptance from convergence alone |
| Sensible, traceable material assumptions | [Material recommendation](material-selection-recommendation.md) distinguishes rated stock, clear-wood data and workshop lamination | Product-compatible material representation, directional properties and connection resistance; no strengths assigned to unidentified C-3 birch or an unqualified glue joint |
| An alternative that addresses the actual load path | [Side-tie options](base-restraint-options.md) distinguish internal thrust from external equilibrium | Separate candidate CAD, complete connection geometry, collision/access checks, and matched numerical comparison; no extra footprint credited to floating rails |
| A load envelope that reflects the intended use | [Load/contact basis](load-contact-basis.md) retains sourced and exploratory cases separately | Audited central/asymmetric loading, friction/hold-offset sensitivities, and material/connection demand checks; a 1.2 kN run alone is not the entire envelope |
| A clear retain/switch recommendation | 2×8 is a development preference, not a demonstrated minimum | Compare governing mechanisms, connection feasibility, mass/footprint, material procurement and fall-zone implications; document why each alternative is retained or rejected |

The recommendation milestone must explain which design to develop, the evidence
behind that choice, its sensitivity to assumptions, and the remaining physical
verification/qualified-review steps. It must not convert unknown material,
adhesive, hardware or floor properties into an implied construction approval.

## Current parallel work

- The first release/load increment refinement completes normally and passes
  released-gravity equilibrium, but still fails loaded moment balance
  (96 Nmm against 1 Nmm). Preserve this failed evidence and the original limits.
- Investigate a supported alternative contact formulation if the moment-transfer
  discrepancy persists. A different formulation is an experiment, not an assumed
  cure or permission to discard failed evidence.
- Two separate side-tied geometry exports and their direct STEP regression tests
  are complete. Compare them with the untied baseline under matched ideal-bonded
  fixed-floor assumptions first; that screen cannot establish reduced sliding
  or real joint capacity. Select material procurement paths with actual
  structural documentation before using product-dependent capacities.
