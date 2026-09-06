# Evidence needed for the frame decision

This tracks the broad design-recommendation objective, not just completion of
a solver run. Original plywood, 2×8, 2×10 and 2×12 candidates and their frozen
results remain references. One climber, 250 lb intended maximum, with 150/200 lb
comparisons and 300 lb sensitivity; these are not certified user ratings.

The [consolidated recommendation](design-recommendation.md) selects the next
candidate to develop, dispositions the preserved alternatives and defines
switch triggers. The open work below is the path from that research decision
to a product-specific, validated assembly; it is not a reason to keep repeating
generic stiffness comparisons without a design question.

## Current development preference

Retain **2x8-foot100 as the comparison baseline**. Do not select deeper rims to
solve an unidentified connection, material or floor-interface problem. Evaluate
a separate side-tied base as a way to close spreading forces internally; it is
not yet a selected design or a substitute for global sliding/tipping checks.

| Decision requirement | Current evidence | Work still required |
| --- | --- | --- |
| Preserve and compare the original candidates | [Physical footprint and matched stiffness studies](physical-footprint-results.md) retain earlier results | Keep alternative geometry/results separately named; do not silently change reference mass, material or restraints |
| A trustworthy unanchored numerical baseline | [Matched MORTAR refinement](full-frame-increment-refinement.md): μ=0.5, increment 0.0625 passes both unchanged global endpoint checks; earlier failures retained | Local contact and mesh/history sensitivity, actual floor assumptions; global balance alone is not physical acceptance. Keep [diagnostic tolerance policy](numerical-acceptance-basis.md) separate from structural requirements |
| Sensible, traceable material assumptions | [Material recommendation](material-selection-recommendation.md) distinguishes rated stock, clear-wood data and workshop lamination | Product-compatible material representation, directional properties and connection resistance; no strengths assigned to unidentified C-3 birch or an unqualified glue joint |
| An alternative that addresses the actual load path | [Side-tie comparisons](tied-base-comparison.md) now include separate CAD, matched six-case bulk FEA and exact-inventory tipping screens | Complete connection design and unanchored comparison; fixed-floor reaction changes are not verified sliding benefits, and floating rails add no footprint |
| A load envelope that reflects the intended use | [Load/contact basis](load-contact-basis.md) retains sourced and exploratory cases separately | Audited central/asymmetric loading, friction/hold-offset sensitivities, and material/connection demand checks; a 1.2 kN run alone is not the entire envelope |
| A clear retain/switch recommendation | 2×8 is a development preference, not a demonstrated minimum | Compare governing mechanisms, connection feasibility, mass/footprint, material procurement and fall-zone implications; document why each alternative is retained or rejected |

The recommendation milestone must explain which design to develop, the evidence
behind that choice, its sensitivity to assumptions, and the remaining physical
verification/qualified-review steps. It must not convert unknown material,
adhesive, hardware or floor properties into an implied construction approval.

## Current parallel work

- Progress material and connection choices independently of the numerical
  moment diagnostic. The next discriminating construction choice is qualified
  leg lamination versus mechanically connected plies with no adhesive credit;
  neither is replaced by buying deeper rims. The
  [actual rib/batten fit screen](rib-batten-detail.md) preserves a same-envelope
  side-grain concept, but rules out an assumed SDS/SDWS drop-in and documents
  why grain rotation also requires rechecking the rear bolts. Its CAD regression
  prevents mixing up the current frame with the older unrotated backing.
  Enlarging the screened blocks collides with all 12 existing rear angles, so
  a replacement must redesign the joint layout as a unit. The
  [independent-ply leg comparison](../fea/results/independent_leg_response/README.md)
  now passes its control, actual-profile equilibrium/energy and two-mesh checks:
  evenly shared independent plies are 3.9223× as compliant out of plane, with
  less than 0.04% in-plane change. Next resolve real composite action, connector
  sharing and lateral stability; this is not a validated construction alternative.
- The first release/load increment refinement completes normally and passes
  released-gravity equilibrium, but still fails loaded moment balance
  (96 Nmm against 1 Nmm). Preserve this failed evidence and the original limits.
- Investigate a supported alternative contact formulation if the moment-transfer
  discrepancy persists. The [unguided matched comparison](full-frame-mortar.md)
  now completes with MORTAR, but fails loaded moment balance (204 Nmm); its
  penalty counterpart times out before full gravity. Retain both outcomes.
  The subsequent [matched increment study](full-frame-increment-refinement.md)
  completes at 0.125 and 0.0625; the latter passes both global endpoints, with
  maximum loaded moment-residual component 0.0714 Nmm. Retain 0.0625 as the next
  diagnostic baseline and qualify local contact and mesh sensitivity before a
  full-frame design conclusion. No indefinite increment search is proposed.
- Qualify member-demand extraction before using it to size joints. The
  [native section-force benchmark](section-force-extraction.md) has substantial
  mesh-dependent bending error on its C3D8 coupon. The separate
  [straight-C3D10 benchmark](section-force-tet-coupon.md) passes external balance
  and closely matches the known bending moment after a load-serialization fix.
  Check representative curved elements and member cuts next; do not transfer
  this homogeneous coupon result to joint-interface forces or capacities.
- Use the [mortar audit basis](mortar-local-audit-basis.md) for local verification.
  Its displayed contact fields are not sufficient for a pointwise law check.
  Any future numerical error budget must be declared before its acceptance runs;
  existing failed results retain their original policy and outcome.
- Two separate side-tied geometry exports, matched bulk runs and exact-inventory
  tipping screens are complete. They do not justify replacing the untied baseline
  for stiffness or tipping alone; test their intended load-path benefit under
  unanchored contact before adding their unresolved joints. Select material procurement paths with actual
  structural documentation before using product-dependent capacities.
