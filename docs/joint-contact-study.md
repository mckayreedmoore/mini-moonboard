# Four-pin / leg-bore contact coupon

This is a **local contact experiment, not the complete leg/rim joint and not a
strength rating**. It is separate from the existing perfectly bonded frame and
prescribed bore-traction studies; their published numerical evidence is unchanged.

## What is modelled

The right upper leg is cropped directly from the `2x8-foot100` CadQuery candidate
at S=1480–1880 mm. Its four 10 mm bores are at S=1540, 1620, 1740, and 1820 mm.
The two glued plywood layers remain one 38.1 mm solid, provisionally isotropic
E=7000 MPa, Poisson ratio 0.3. Neither laminate glue nor directional wood failure
is modelled. Secondary screw holes are omitted from this local coupon.

Four cylindrical pins occupy the actual bore axes. All pin nodes are fixed:
this explicitly idealizes infinitely rigid rim-side anchorage, omitting rim
deformation and bolt bending. No equal load sharing is imposed. Each pin's
resultant is recovered independently from its reactions.

The nominal pin diameter is 9.525 mm, giving 0.2375 mm **radial** clearance in a
10 mm bore. A separate zero-clearance sensitivity changes the pin diameter to
10 mm; this is an ideal numerical comparison, not a different specified bolt.
The bores and pins are separate meshes, not bonded or merged. Their face-to-face
contact is frictionless and compression-only, using a linear normal penalty.
Penalty stiffness is a numerical sensitivity, not a measured timber property.

The lower crop face is guided in all three translations. It is displaced along
either S (uphill) or N (into the backing) by the radial clearance plus 0.03 mm;
its other translations are held at zero. These are conditional imposed motions,
**not forces extracted from the full frame, not a service envelope, and not an
allowable-slip criterion**. The two clearance cases have different total imposed
motion but the same nominal 0.03 mm travel beyond first geometric contact.

No member-face friction, bolt preload, washers, withdrawal, thread effects,
crushing, splitting, moisture effects, or cyclic wear is represented. Releasing
pin/bore contact here does not validate any other joint or unanchored stability.

## Solver interpretation

The existing Docker Gmsh/CalculiX 2.21 installation is reused. Quadratic C3D10
tetrahedra are optimized and required to have positive final Jacobians. The
nonlinear static solve uses geometric nonlinearity and adaptive cutbacks.
Displacement control avoids the pre-contact rigid translation problem that a
force-driven free-clearance coupon would have.

The official [CalculiX 2.21 manual archive](https://www.dhondt.de/ccx_2.21.htm.tar.bz2),
sections `*CONTACT PAIR`, `*SURFACE BEHAVIOR`, and `*CONTACT PRINT`, documents
the separate face-to-face surfaces, penalty pressure/overclosure law, and DAT
contact output. The generic prose describes positive CDIS as overlap, but the
actual CalculiX 2.21 face-to-face DAT in these runs uses **negative normal CDIS
under compression**, with positive pressure satisfying `p = -K × CDIS`.
The audit preserves that observed sign and checks the constitutive relation;
it does not silently interpret these negative numbers as an open gap.

## Reproduce

The preparation command below is for a fresh generation directory. Repeating
preparation reuses a verified unchanged snapshot byte-for-byte. If geometry,
preparation source, or existing snapshot contents differ, it refuses to overwrite
anything and asks you to archive the **entire** generation directory manually
before preparing a new generation. Do not replace only the shared STEP while
retaining old runs. The historical published snapshot predates this guard and
is intentionally left unchanged; replay its bundled evidence with the test
command rather than regenerating it in place.

```bash
uv run python -m fea.prepare_joint_contact
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 fea/solve_joint_contact.py --size 8 --direction S
uv run python -m fea.record_joint_contact contact_S_8_100000_0p2375
uv run pytest -q tests/test_joint_contact.py
```

Raw working files remain under ignored `fea/generated/joint_contact/`. The
[accepted reference's compressed raw evidence](../fea/results/joint_contact/reference_raw/)
includes its INP, DAT, context, convergence/completion logs, pre-launch input
digests, and frozen STEP. CI decompresses it into a fresh temporary directory
and repeats the audit, without needing ignored local files or Gmsh.

## Acceptance gates and present findings

The audit requires finite complete final-time displacement and support output,
the intended guided motion, fixed pins, positive final Jacobians, pressure with
no tensile or tangential traction, and the recorded penalty constitutive law.
Per-pin contact force must agree with independently summed pin-node reactions;
each contact centroid must remain at its corresponding bore. The actual INP
is checked for nodes, sets, material assignments, modulus, step settings,
boundary conditions, and absence of extra loads, ties, or friction.

Force equilibrium must be within 0.1 N. Moments are calculated both about the
origin and the deformed driven-face centroid. The moment criterion is
`max(1 N·mm, 10^-6 × 400 mm × |driven resultant|)`: a fixed coupon-length-based
numerical tolerance, **not a structural margin**. This is not the old bonded
model's fixed 1 N·mm threshold. Explicit DAT force-rounding bounds are retained;
the observed residual is not explained by rounding alone. Contact discretization
and nonlinear iteration accuracy still contribute.

The accepted 8 mm S-direction reference uses 0.2375 mm radial clearance and
100000 N/mm³ normal penalty. At the imposed 0.2675 mm motion, its conditional
elastic driven-axis reaction is **7455.8 N**. Pin shares, from lowest to highest
S station, are **42.55%, 26.79%, 16.99%, 13.68%**: equal sharing was not imposed
and does not emerge under this coupon's boundary condition. This does not
establish those shares in the complete board.

Its maximum pressure is about **100.9 MPa** and maximum penalty penetration is
0.00101 mm. The provisional linear isotropic material has no crushing or damage
law; the pressure is **not a credible allowable wood stress, failure prediction,
or capacity rating**. The imposed motion was an experiment, not a service limit.
Peak pressure is not established as mesh-converged.

The reference's maximum moment residual is about 1.57 N·mm against a 2.98 N·mm
limit, and maximum force residual is below 0.0001 N. Its pre-solve input/context
hashes were captured before its final rerun; early trials lacking that capture
must not be relabelled as possessing immutable execution provenance.

The present useful design lesson is to resolve actual bore clearance, seating,
preload, and rim/bolt compliance before treating these four connections as a
perfect bond. Do not add this coupon's motion directly to the global deflection,
change bolt count from these load shares, or infer a safe climber rating.

## Mesh, penalty, direction, and clearance trials

Ten final trial jobs reached CalculiX's `Job finished`. Only three passed the
independent numerical audit. Solver completion alone is deliberately not
treated as acceptance. The [trial inventory](../fea/results/joint_contact/trial_inventory.json)
records parameters, failure reasons, provenance status, and actual raw-file hashes.

| Direction | Mesh | Radial clearance | Penalty N/mm³ | Independent audit |
| --- | ---: | ---: | ---: | --- |
| S | 12 mm | 0.2375 mm | 100000 | Rejected: 29.17 N·mm moment residual |
| S | 8 mm | 0.2375 mm | 100000 | Accepted: 7455.8 N conditional reaction |
| S | 6 mm | 0.2375 mm | 100000 | Accepted numerically: 7335.2 N; early-trial provenance |
| S | 8 mm | 0.2375 mm | 200000 | Accepted: 7506.3 N conditional reaction |
| S | 8 mm | 0 mm | 100000 | Rejected: three small tensile contact stresses, minimum −0.00222 MPa |
| N | 12 mm | 0.2375 mm | 100000 | Rejected: 7.79 N·mm moment residual |
| N | 8 mm | 0.2375 mm | 100000 | Rejected: 4.68 N·mm moment residual |
| N | 6 mm | 0.2375 mm | 100000 | Rejected: 5.01 N·mm moment residual |
| N | 8 mm | 0.2375 mm | 200000 | Rejected: 4.47 N·mm moment residual |
| N | 8 mm | 0 mm | 100000 | Rejected: 5.47 N·mm moment residual |

The S-direction reaction changes by 1.64% between the accepted 8 and 6 mm
meshes (relative to the finer result). Doubling the penalty changes the 8 mm
reaction by 0.677%. However, peak pressure changes from 100.9 to 77.1 MPa on mesh
refinement and to 134.2 MPa on penalty doubling. **Peak contact pressure is not
numerically settled**, quite apart from the missing physical material model.

The S6 trial was run before pre-launch digest capture was added. It is retained
as independently re-audited numerical evidence, clearly marked with hashes
captured at re-audit; it is **not pre-launch-provenance-verified**. S8 was actually
rerun after that change, and the doubled-penalty S8 case also has genuine
pre-launch digests. No later recording step retroactively creates solve-time
provenance for early trials.

N-direction and zero-clearance comparisons remain **numerically unresolved**.
Their rejected outputs are not used to rank the design or infer physical failure.
No further acceptance thresholds were loosened to make those runs pass. A next
contact-method investigation should use per-bore pairs and examine face-contact
moment conservation, contact discretization, and constitutive calibration before
extending this coupon to deformable bolts, rim stock, and member-face friction.

All four bore surfaces currently share one slave-surface collection, paired with
each finite pin master. The nearest foreign bore axis is at least 80 mm away;
the sub-millimetre motion cannot close its roughly 70 mm radial separation from
a foreign pin. Accepted runs also require each pair's recovered force to match
its pin reaction and its contact centroid to lie at its matching bore. Per-bore
slave collections would reduce unnecessary contact searching in future runs.
