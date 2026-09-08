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
