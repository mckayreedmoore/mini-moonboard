# Current-wide gusset mesh load paths

The accepted 40 mm current-wide mesh contains more gusset load paths than the
two bolt-pair statics model. It therefore cannot supply that model's wrench by
assigning all aggregate base reactions to the gusset bolts.

## Read-only extraction, September 8, 2026

The extraction used `fea.wide_asymmetric.authenticated_inputs()` to verify the
accepted current-wide deck and source identity, then selected complete gusset
elements by their corner centroid inside each raw CAD gusset. All ten nodes of
every selected quadratic tetrahedron were subsequently checked inside the same
gusset. Selected mesh volume matched raw CAD volume to displayed precision.
This is ownership evidence, not stress or force recovery.

| Quantity | Left | Right |
| --- | ---: | ---: |
| Selected elements | 814 | 808 |
| Selected nodes | 1,732 | 1,723 |
| Selected nodes outside raw gusset | 0 | 0 |
| Nodes shared with remaining mesh | 417 | 413 |
| Shared nodes also in inclined rim | 161 | 161 |
| Shared nodes also in outer post | 227 | 227 |
| Shared nodes also in header | 59 | 55 |
| Shared nodes also in kicker | 13 | 13 |

Counts by neighboring member overlap at boundaries and must **not be summed**
as disjoint interfaces. Node containment alone does not establish a finite-area
contact patch; in particular, the kicker count must not be described as a
separate area-bearing face without face classification. The existing conformal
mesh nevertheless ties shared displacement degrees of freedom, unlike a
connection with unilateral contact and discrete bolts.

## Consequence for the next demand calculation

The [two-interface gusset model](gusset-group-envelope.md) is an explicitly
conditional statics model, not a reconstruction of these bonded interfaces.
A next substructure recovery must classify shared element faces and boundary
nodes, preserve the complete parent displacement field, and distinguish rim,
post and header actions without double counting shared edges. First verify
reaction recovery against a known-load control and the gusset's full equilibrium.

Such recovery would quantify the **bonded-model** load split. It would still
not establish actual bolt forces: header/gusset contact can separate, and the
real bolt/hole/washer and member interfaces have compliance absent from the
parent model. Before using the wrench for bolt sizing, either model those
mechanics or establish a justified load-path bound. Do not arbitrarily discard
header reactions or credit permanent tensile header contact.

This audit changes no geometry, solver input or published FEA result. It identifies
why the existing aggregate output is insufficient and the specific interfaces
that the pending joint-demand model must address.

## Reproducible element-face map

`fea/gusset_interfaces.py` now authenticates the parent evidence, reproduces
the complete element selection and classifies conforming six-node tetrahedron
faces against neighboring raw CAD members. The current selected tetrahedra have
straight midside geometry within the checked 1e-6 mm limit; the reported triangle
areas are not being applied to an unverified curved mesh.

| Neighbor | Left faces | Right faces | Area per side |
| --- | ---: | ---: | ---: |
| Inclined rim | 68 | 68 | 35,402.227 mm² |
| Outer post | 100 | 100 | 47,691.675 mm² |
| Header | 20 | 18 | 10,887.075 mm² |
| Kicker | 0 | 0 | No separate shared face |

All shared gusset nodes belong to at least one of the three face-interface
groups. The kicker's node containment count above occurs on their boundaries;
it is not a fourth face interface. Interface groups still share edge nodes,
so summing their nodal reactions independently would double count those nodes.
The header has a finite, substantial tied area in the parent mesh, not merely
an incidental edge tie.

The [complete face map](../fea/results/gusset-interfaces.json) retains element,
neighbor, face and node identities, source hashes and areas. The replay test
regenerates the map from authenticated CAD/mesh, checks exact face inventory,
coverage, ownership, positive areas and mesh/CAD volume agreement:

```sh
uv run pytest -q tests/test_gusset_interfaces.py
```

This provides the interface geometry for subsequent recovery; no traction,
contact-law or actual bolt force has yet been calculated from it.

## Parent displacement availability

The original ASCII FRD files remain under `fea/generated/wide-asymmetric/`.
Their bytes were checked against the FRD hashes in the published compressed
run records, and their decks against the same records. Each A12, K12 and F6 file
contains all 153,552 parent node IDs for all three basis steps. The strict
`fea/frd_displacements.py` reader verified complete coverage before selecting
the 3,455 gusset nodes; no unselected missing node is silently ignored.

| Original run | Extracted steps | Largest absolute selected displacement component |
| --- | ---: | ---: |
| A12 | 3 | 0.0195309 mm |
| K12 | 3 | 0.0193870 mm |
| F6 | 3 | 0.00364251 mm |

These maxima are availability diagnostics over the Cartesian basis steps, not
combined-load results. FRD values retain limited printed precision; differentiating
them to recover forces needs a sensitivity/equilibrium check. The original DAT
publication contains only selected output sets, so it must not be represented as
a full-displacement archive. The full FRDs are locally retained but not yet added
to the portable replay package.

Six parser tests cover fixed-width adjacent signed numbers, node selection,
missing terminators, wrong fields, duplicate/unknown nodes and repeated steps.
All three original files passed the full-node identity check. A subsequent
substructure recovery can reuse these authenticated fields without a whole-frame
rerun, provided its own force-recovery and precision acceptance controls pass.

## Native prescribed-displacement control

`fea/prescribed_tet_control.py` now runs a single straight C3D10 tetrahedron
with all displacement components prescribed. The affine field produces known
constant uniaxial stress. Expected consistent nodal forces are calculated from
the exact volume integrals of the quadratic shape gradients, independently of
the solver output. Force/moment balance and strain energy also have exact checks.

The pinned CalculiX 2.21 image completed the all-prescribed solve successfully.
Maximum nodal-force discrepancy was 0.00003334 N, below the preselected 0.001 N
gate; imposed displacements matched within 1e-9 mm. No free DOF or artificial
spring was needed to obtain reactions. Both initial and source-hashed follow-up
runs remain locally retained; the follow-up's complete small output is in
[`prescribed-tet-control.tar.gz`](../fea/results/prescribed-tet-control.tar.gz).

Two tests verify analytic equilibrium/energy and independently replay the archive,
including source/input/output hashes and every nodal displacement/force. This
qualifies the narrow all-prescribed reaction mechanism on this affine element,
not full gusset recovery, FRD rounding sensitivity or attribution of shared-edge
forces to individual physical interfaces. Those remain the next checks.

## Actual gusset recovery: numerical gates passed

`fea/gusset_recovery.py` has now solved the two isolated gussets together using
their original 1,622 C3D10 elements and 3,455 nodes. Each of the three parent hold
runs supplies three prescribed displacement fields: a 1,000 N X force, a
1,000 N Y force and a −1,000 N Z force. Six native CalculiX jobs cover the original
six-significant-digit fields and five-digit rounding sensitivity, each with three
steps. These are recovery solves, not eighteen new whole-frame load cases.

The parent FRDs and decks were authenticated against their published run records;
the basis meshes match the accepted current-wide parent mesh. The isolated bodies
retain the parent's E = 7,000 MPa and Poisson ratio 0.3. All displacement components
are prescribed, with no applied forces, gravity, springs or added free DOFs.

Acceptance limits were set before the first recovery run:

- Complete node/step output and imposed displacement agreement within 1e-8 mm.
- Maximum reaction magnitude at a node not shared with another member ≤ 1 N
  for each 1,000 N parent basis, including the reduced-precision rerun.
- Every disjoint node bucket's rounding change in resultant force ≤ the greater
  of 1 N and 1% of its original resultant magnitude; moment change ≤ the greater
  of 1,000 N·mm and 1%. Moments use each gusset's node-coordinate centroid as
  a fixed local origin, not the global origin.
- Successful solver termination without reported errors.

All nine recovered basis fields passed. Maximum unshared-node reaction was
0.05199 N at original precision and 0.62817 N at reduced precision. Maximum
bucket resultant change was 0.82318 N; maximum moment change was 131.745 N·mm.
All comparisons used their individually calculated thresholds. These are
numerical consistency controls, not estimates of physical accuracy or safety
factors. Whole-body force/moment balance is also replay-tested, but balance alone
cannot validate an arbitrarily prescribed displacement field.

Interface edge nodes are retained in **separate overlapping-membership buckets**:
header-only, rim-only, post-only, header/rim edge and header/post edge. Each node
is counted once. The shared-edge buckets are not arbitrarily divided between
interfaces or attributed to bolt pairs. Unshared nodes have their own residual
bucket. The header transfers nonzero force and moment in these results; treating
this as a two-interface rim-to-post bolt connection would omit a real load path
in the *numerical model*, whether or not that load path is physically justified.

The [portable recovery archive](../fea/results/gusset-recovery.tar.gz) includes
all six decks, solver outputs/logs, selected prescribed fields, source hashes,
parent FRD hashes and replayable reaction summaries. It reproduces the recovery
from the selected fields without needing the large original FRDs. Independently
re-extracting those fields still requires the hash-identified local parent FRDs;
the archive does not claim to contain them. The first run was preserved locally
and rerun with repository-relative provenance paths for portable verification.

```sh
uv run pytest -q tests/test_gusset_recovery.py tests/test_frd_displacements.py tests/test_prescribed_tet_control.py
```

**Design disposition:** retain the current gusset as an inspection candidate,
not a qualified connection. Do not compare these bucket forces directly with
the two-member bolt reference values or declare the splice adequate. The next
connection model must explicitly replace the bonded header/rim/post transfers
with the intended fasteners and admissible bearing/contact behavior. This
recovery has established that the archived fields can support numerical force
inspection; it has not established actual bolt demand, separation resistance,
plywood failure resistance or unanchored support behavior.

### Independent review checkpoint

The recovery increment and preceding bolt-yield, thread-exposure, gusset-pair,
interface-map and displacement-control work received independent correctness,
testing and architecture/package-consistency reviews. All three reported no
substantial findings. The combined focused regression passed 36 tests; Ruff and
`git diff --check` were clean. Reviewers did not rerun heavy CAD or solver jobs.
This records a numerical/software review, not professional structural approval.
