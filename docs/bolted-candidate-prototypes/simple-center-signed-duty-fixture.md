# PB02 connected center: provisional signed replacement-duty fixture

The active seven-body PB02 center can equilibrate all five authenticated
historical right-center interface-action examples only when the point model
permits both compression-only face contact and no-preload bolt tension. This is
a topology result, not a PB02 demand, reaction prediction, capacity check,
pressure solution, or drilling release. The
[reproducible script](../../scripts/simple_center_signed_duty_fixture.py) binds
the result to the active `ligament_priority` geometry fingerprint.

## Source and fixture

For each accepted `proxy-default-v2` case, the script re-runs the strict
extractor against the raw final report and final-cycle input under
`fea/results/diagnostics/kerf-right-center/`. It also checks those files against
the SHA-256 values recorded in `center-reference-diagnostic.json`. The five
cases are `a1-rear`, `a12-left`, `a12-rear`, `k12-rear`, and `k12-right`.
There is no accepted `a12-forward` case.

Those retained reports were produced with archived `fea/current_response_model.py`
SHA-256 `e724bbb74150923265b13be2513c2634c3cb02b4c3568c43b3aee55626507dce`.
Repository commit `5b20a38a2cb0ff213105678a2082aa892cdb80a8` preserves byte-identical
producer source. The current shared model contains opt-in candidate extensions and is
not byte-identical. Historical report and input identity is verified against the
pre-existing reference manifest, whose SHA-256 is pinned separately as
`193bef4f3c8b73473d11cc6d61f4a085eae850a21f63ae71dd650cbf53609f51`.
A bounded default-path test checks the current unsolved preparation's member and floor
support inventory and metadata; separate tests exercise the candidate opt-ins. These
are semantic compatibility checks, not source-byte equivalence or solver-result replay.

The fixture retains both simultaneous complete old-interface wrenches:

- old right principal/header action maps to PB02 `principal`;
- old right post/header action maps to PB02 `post`; and
- an exact equal-and-opposite action is applied to PB02 `header` at each old
  interface origin.

Forces remain global N and moments remain global N·mm. The complete old
interface wrench is used rather than preserving the old direct-contact versus
ML24Z/SDS split. Every fixture is exactly self-equilibrated before PB02
reactions are introduced. These are authenticated old-topology examples only;
the changed PB02 topology can redistribute frame response and therefore does
not inherit them as design demand.

## Signed point model

Every active PB02 bolt center supplies two bilateral shear reaction rows. Its
axial row is tension-only with no preload. Four face points offset 20 mm from
the actual shared-face overlap center supply compression-only reactions. The
builder derives each plane and overlap from both active CAD solids and stops if
the faces do not coincide or cannot contain the sample pattern. The pattern is
still illustrative rather than a pressure patch. The contact normal is oriented
from the first named body toward the second; this work corrected the
upright-side-cleat to rear-cleat normal to global −Y because the rear cleat is
on that side of the shared face. The correction does not change the prior rank
results, but it is essential for signed contact.

The linear feasibility solve enforces equal-and-opposite actions and all 42
body-equilibrium equations. It does not assign stiffness. A feasible witness
is nonunique, so its individual reaction magnitudes are deliberately not
reported as design forces.

| Reaction model | Result in all five old-action examples |
| --- | --- |
| Bilateral bolt shear + tension-only bolt axial + compression-only contact | feasible |
| Bolt shear + tension only, all face contact removed | infeasible |
| Bolt shear + contact only, all bolt axial tension removed | infeasible |
| Bolt shear only | infeasible |

Single-edge omission gives the same necessity result in all five examples:

- compression at every edge except `header_principal_block` cannot
  individually be removed from this point model;
- tension at every one of the seven edges cannot individually be removed; and
- other individual rows may be removable only within this non-stiffness point
  equilibrium model. That does not prove they are unloaded in the real joint.

This result advances the center from conditional rank to signed load-path
feasibility and sets priorities for the next checks. It does not establish
compatible gaps, actual contact pressure, stiffness-dependent sharing,
fastener or timber resistance, the missing forward case, or whole-frame
response. Those remain required before G1/G2 or fabrication release.

The later
[compatibility-aware sensitivity](simple-center-stiffness-sensitivity.md)
adds one-sided spring compatibility and preserves two rank-deficient contrast
trials. Its stiffnesses and historical actions remain provisional.

Reproduce with `.venv/bin/python -m scripts.simple_center_signed_duty_fixture`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_signed_duty_fixture.py`.
