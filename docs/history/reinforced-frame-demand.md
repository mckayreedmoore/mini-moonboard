# Reinforced assembly demand calculation

The calculation in `fea/reinforced_frame_demand.py` builds a fresh native
CalculiX model of `round-reinforcement-development`. It predicts forces and
displacements under the assumptions below. It is not a release calculation for
the actual wood, plywood, fasteners, fabricated shoes or installation.

## What is actually represented

- Every current timber member uses its full uncut rectangular stock section and
  current member endpoints. The earlier continuous rear-prism approximation is
  not reused. End bevels use an explicitly documented plane-section extension;
  round service holes and connection holes are omitted from stiffness.
- Six independent shell panels retain their actual boundaries. There is no
  displacement tie across either a horizontal or a vertical panel seam. The
  model includes all 66 panel/kicker screws at their current attachment axes.
- The 22 retained ML24Z bodies each connect through six separate SDS springs.
  Both fabricated shoes connect through their actual eight bolts. All eight
  original leg bolts remain separate. Rigid-body connector kinematics preserve
  force and moment equilibrium; neither a shoe nor an ML24Z is a prescribed
  rotational clamp between timber members.
- Each shoe has unilateral normal reactions at four actual rim-seat corners and
  four corners of its footprint overlapping the header. Principal/header and
  header/post normal bearing is also unilateral. Sampled frictionless normal
  springs represent backing contact behind each independent panel.
- Four post footprints and two leg footprints use their actual horizontal CAD
  corners for compression-only floor support. The two kicker bottoms also have
  independent compression-only support samples. Current v5 grants them no
  tangential friction restraint. Floor contact cannot pull a
  part downward and member rotations are not fixed to the floor.
- Each post/leg footprint has an assumed tangential resultant at its geometric
  centroid while at least one of its normal contacts remains closed. No floor
  torsional stiffness is prescribed. A separate linear program distributes that
  shear and its full yaw moment over the **solved compressed contacts**, finding
  a sufficient friction coefficient using an inscribed 32-direction friction
  polygon. An infeasible friction witness rejects that assumed support state.

The tangential support is a reduced whole-foot model, not a calibrated contact
law for a flexible foot or pad. Its friction certificate demonstrates the
existence of an admissible force distribution for the specified normal forces;
it does not establish the actual local slip history or floor coefficient.

## Loads and numerical assumptions

The command accepts a main hold, a 250 or 300 lb comparison load and a common
connector translation stiffness. The applied load is twice that body weight,
plus 300 N in global +Y, at 100 mm outward from the climbing face. A 20 mm
contained panel patch carries the resultant and its eccentric moment. This
load does not represent a verified impact spectrum or an actual hold footprint.

Timber and plywood are homogeneous isotropic elastic materials with
E = 7000 MPa and Poisson ratio 0.3. Timber/plywood dead load uses current routed
wood volumes at 600 kg/m³, applied through each actual centroid. Hardware,
holds, LEDs and wiring dead load are omitted. The shell thickness is 18.25625 mm.

Connector translation springs are sensitivity inputs, not manufacturer load-slip
curves. The normal contact penalties and floor sticking stiffness are also
numerical assumptions. The stock's bore sections, timber bearing, bolt splitting,
plywood orthotropy and holes, screw head seating, welded-shoe flexibility, bolt
prying and connection resistance require separate evaluation. Neither use of a
lower elastic modulus nor omission of some stiffness establishes a conservative
bound on load distribution.

## Recovery and checks

The runner archives its source snapshots, input decks, native output and each
active-contact iteration. Normal contacts must satisfy complementarity. Native
expanded opposite-face S8 translations are used to recover mechanical shell
translations; ordinary shell-node output is retained but does not silently
replace that recovery. Multi-point constraint checks use the native printed
precision intervals.

Physical floor spring resultants recover the global force and moment balance.
CalculiX's ordinary fixed-node reaction block omits the vertical transfer through
the scalar normal-contact constraints, so that incomplete block is retained
separately and is not treated as the physical support resultant.

For every connection, the report supplies its actual application point, both
signed force vectors and, where appropriate, force projected along the bolt or
screw installation axis. It also supplies all rim-seat and shoe/header bearing
reactions. Each timber member receives a free-body section scan above its first
full-width section, on both sides of every applied-force station. The scan
preserves simultaneous axial force, both shears, torsion and both moments; it
does not combine independent extrema into an invented load case.

The report also retains per-member force and moment residuals. A converged
contact state with a failed global/MPC check is not accepted for downstream
resistance comparisons. A physically invalid friction witness likewise remains
a failed assumption rather than being hidden by a successful linear solve.

## Earlier failed trials

`/tmp/reinforced-F10-k1000` omitted shoe-foot/header contact and the required
expanded-shell displacement recovery. Its reported support reaction omitted the
scalar vertical MPC transfer. It is superseded debugging evidence.

`/tmp/reinforced-F10-k1000-v2` added those corrections. Global equilibrium and
MPC checks passed, but a corner support alternated between approximately
143.5 N of inadmissible tension and 0.0556 mm of penetration when that corner's
tangential spring was removed. Its contact state therefore did not converge.
Its producer source snapshot is also incomplete because a then-absolute source
path bypassed the snapshot directory. It is not an authenticated resistance
input. The v3 producer used relative paths and the whole-foot tangential support
described above. It converged, but it retained two inactive direct rim/header
bearing bypasses and omitted one transitive import from its snapshot closure.
The v4 producer removes those bypasses and walks the repository import graph,
including imports inside lazy functions. An isolated snapshot import test checks
that it does not fall back to the live checkout.

## Reproduction

```sh
uv run python -m fea.reinforced_frame_demand \
  --output /tmp/reinforced-F10-k1000-replay \
  --hold F10 --stiffness 1000 --frame-size 200 --panel-size 200
uv run pytest -q tests/test_reinforced_frame_demand.py
```

Use a new output directory for every run. Stiffness, load location and mesh
sensitivity must retain their own source and result identities. A passing run
predicts the stated diagnostic model; it does not by itself close the release
checks listed in the project issue.

## Concrete support failure found in the converged v3 comparison

The F10, 250 lb × 2, 300 N horizontal, 100 mm offset comparison converged at
23.661 mm maximum total panel translation. That number includes frame motion;
it is not a separately measured panel bending deflection. Global residuals were
0.000342 N and 0.455 N·mm, and the expanded-shell constraint checks passed.

The front center feet nevertheless could not supply their predicted shear at
an assumed friction coefficient of 0.4. This follows from the necessary bound
`|horizontal resultant| <= mu * total normal force`, independent of the
polygonal yaw certificate:

| Foot | Compression (N) | Horizontal resultant (N) | Necessary friction coefficient | Force ratio at mu = 0.4 |
| --- | ---: | ---: | ---: | ---: |
| Left center post | 416.923 | 372.321 | 0.8930 | 2.2326 |
| Right center post | 246.560 | 189.106 | 0.7670 | 1.9174 |
| Left leg | 1575.730 | 431.202 | 0.2737 | 0.6841 |
| Right leg | 1541.579 | 424.740 | 0.2755 | 0.6888 |

The 32-direction full force-and-yaw certificates give **sufficient**, not
necessary, coefficients of 2.1765 and 3.3180 for the center feet. The smaller
force-only bounds already reject the specified 0.4 installation assumption.
A rigid-body floor equilibrium witness cannot remove these internal frame
spreading forces. Possible remedies require a separately checked bottom tie or
another explicit restraint/load path, or a sliding-contact analysis that finds
an admissible stable configuration. Increasing a coefficient merely to make the
run pass is not a remedy.

These values are conditional on the stated gross-section, isotropic and
connection-compliance model. They establish that the assumed sticking response
is inconsistent with the specified friction allowance; they are not a proof of
the exact physical slip trajectory. The earlier source-closure limitations also
remain attached to v3. Current v4 runs provide the corrected reproducible model.

## Completed source-complete comparison

[The comparison record](../fea/results/reinforced-frame-comparison-v1.json)
authenticates the two native archives and preserves the physical support
failure separately from numerical convergence:

| Common connection stiffness (N/mm) | Contact iterations | Maximum total panel translation (mm) | Maximum timber translation (mm) | Governing necessary friction coefficient | Ratio to assumed mu = 0.4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1,000 | 14 | 23.661 | 22.372 | 0.8930 | 2.2326 |
| 10,000 | 11 | 12.831 | 11.799 | 2.2744 | 5.6859 |

Both cases pass global force/moment equilibrium, expanded-shell constraint
checks and unilateral normal-contact complementarity. Both fail the specified
floor assumption by a necessary force-only bound. The tenfold stiffness change
is not a sensitivity bound: it demonstrates that a stiffer assumed connection
response changes both deflection and internal spreading reactions materially.

The 1,000 N/mm archive uses producer v4. Its kicker floor normal and tangential
reactions are all zero. Producer v5 removes kicker-edge tangential restraint,
retaining only vertical bearing; the baseline response is therefore unaffected
by that removal. All CAD and reference source hashes match between the two
accepted numerical cases. The sole changed producer source is identified in
the comparison record. The separate v4 stiff-connection trial that cycled when
its last kicker contact opened remains preserved as failed numerical evidence.

Native archives:

- [1,000 N/mm, v4](../fea/results/reinforced-F10-k1000-v4.tar.gz)
- [10,000 N/mm, failed v4 contact state](../fea/results/reinforced-F10-k10000-v4.tar.gz)
- [10,000 N/mm, v5 with frictionless kicker edges](../fea/results/reinforced-F10-k10000-v5.tar.gz)
- [Earlier failed-trial summary](../fea/results/reinforced-frame-failed-trials-v1.json)

### Force-recovery precision

The separate [roundoff postprocessor](../fea/reinforced_frame_roundoff.py)
propagates the actual DAT/FRD print intervals through every active spring and
member free-body cut. All 18 members' force and moment residuals in both accepted
numerical cases lie within these printed-output bounds. For example, the
baseline left center principal's largest moment residual is 3,202 N·mm within
an 8,022 N·mm print interval bound; the top rail's corresponding values are
1,474 and 12,148 N·mm.

These are conservative interval sums, not statistical errors. Each section
retains separate radii for axial force, both shears, both moments and torsion.
The [baseline intervals](../fea/results/reinforced-frame-k1000-roundoff-v1.json)
and [stiff-connection intervals](../fea/results/reinforced-frame-k10000-roundoff-v1.json)
also supply every connection's physical vector-force radius. Resistance
comparisons near a threshold must account for those radii. They do not cover
mesh discretization, material properties, contact assumptions or actual joint
compliance.

The completed calculation rejects the stated sticking load path at the
specified floor friction. Further mesh refinement cannot turn that rejected
installation assumption into an accepted physical response. A corrected load
path or an admissible sliding/contact model must precede a release-level sweep
of load locations, material directions and stiffness uncertainty.
