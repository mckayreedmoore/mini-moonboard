# Floor-runner MVP criteria ledger

This ledger freezes the acceptance rules for the six fresh
`compact-floor-flush-development` cases required by the
[master plan](floor-runner-mvp-master-plan.md). It does not transfer any result
from the historical finite-friction A12-left case or from another candidate.

## Case prerequisites

Each case must use the exact selected geometry and source-authenticated no-slip
producer, converge its compression-only contact active set, meet the native
equilibrium and residual limits, and retain every required physical connection,
floor cell and member-contact record. Failure of identity, provenance,
convergence or inventory stops assessment rather than producing a component
pass.

## Adopted assessment criteria

`scripts.floor_flush_checks.FROZEN_ADOPTED_CRITERIA` is the machine-readable
authority. Every fresh case must contain and pass that exact required set:

- bolt and joint-group lateral resistance, local parallel bearing, supplemental
  splitting, spacing, directional edge/end distance, receiver fit, washer and
  steel checks;
- sampled gross/net member resistance and stability, represented machining,
  bolt-section sampling, header stability, base bearing and end-notch shear;
- floor-runner bearing, all six runner/post/leg contact interfaces, compression-
  only contact behavior and sampled taper-top clearance;
- native/CAD taper identity, mesh volume, slope/runout, retained net section,
  shear/torsion and unbored-region applicability checks; and
- all 24 ML24Z listed force-component interactions and complete component
  layouts.

The finite-Coulomb-law criterion is conditional and applies only to historical
or sensitivity runs that include that law. It is absent from the selected
no-slip cases. Full-root bolt results remain non-adopted hardware sensitivities;
the specified partial-thread/body condition and delivered-hardware inspection
remain mandatory.

## Retired release scalar

`base_end_cut_geometry` is preserved under `non_adopted_sensitivities`, including
its recorded value and the historical approximately −4.970 mm margin. It is not
an adopted pass/fail criterion because the quarter-depth projected-seat analogy
has no established mapping to the supported terminal bevel. Removing that one
scalar does not remove the adopted actual retained-section, base-bearing,
end-notch shear, member stability, interface-contact or gross/net checks listed
above.

## Disclosed limits

ML24Z listed interactions must remain at or below 1.0. Separation and an
independent force-parallel flange couple are not listed catalog capacities and
must be reported without calling them manufacturer-qualified. The nominal
rear-leg cut-face transverse stress inference remains a local-fracture method
limitation paired with stock and cut inspection controls; it is not converted
into a numerical pass. The owner's no-slip support condition is an analytical
assumption, not measured floor friction or an anchor.

Changing this ledger, geometry, load inputs, material basis or physical load
path requires an explicit revision and affected fresh cases. Documentation or
viewer changes alone cannot change a case result.
