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
