# Shared-edge two-pair C3D10 coupon

## Status and scope

Prepared for parent review. The four decks have not been frozen or run. The
parent owns input freeze, the bounded serial execution, and result audit. This
coupon isolates two node-sharing patterns across two perpendicular contact
pairs; it does not qualify the full joint patch or change the model.

The variants are:

- `shared_slave`: central bottom and central left faces are both slaves. They
  share nodes 1, 4, and 24: two vertices and one midside node.
- `cross_role`: central bottom remains slave while central left is master; the
  outer left face becomes the second slave. Nodes 1, 4, and 24 are shared by a
  slave surface and a master surface across pairs.

Each variant has separate MORTAR and surface-to-surface penalty decks. Each
deck uses one contact type for both pairs and four distinct surface names.

## Prepared geometry and loads

The decks translate the pinned 27-node, six-tetrahedron C3D10 cube template
from the prior 2 mm coupon into three exact 2 x 2 x 2 mm bodies. The central
cube occupies `[0,2] x [0,2] x [0,2]`; lower and left cubes meet its bottom and
left faces. `prepare.py` verifies the pinned source hashes, positive corner
Jacobians, straight midside nodes, exterior quadratic faces, matching contact
triangulations, and the 4 mm2 patch areas.

All bodies use `E=100000 N/mm2` and `nu=0`. Both frictionless interfaces use
linear normal slope `K=100000 N/mm3`. Initially coincident faces are active
under the pinned 2.23 `genfirstactif.f` threshold (`c0=1e-10 mm`).

The single NLGEOM static full step applies consistent quadratic-triangle
tractions to the central top and right faces. At `p=1 N/mm2`, each face's
reference resultant is 4 N. Corner-node weights are zero; each triangle's
midside nodes receive `p * area / 3`. The generated load table verifies both
the combined `[-4, 0, -4] N` resultant and its first moment about the global
origin.

Only remote faces carry the axial supports and rigid-mode anchors. The lower
remote face supports U3; the left remote face supports U1. Separate anchors
remove the remaining remote-body rigid modes. Central node 6, at `(2,0,2)`,
provides the central Y gauge. Static preparation finds no explicitly
constrained node on any slave patch in either role variant. Auxiliary reaction
checks sum only the anchored tangential DOF components; they do not double-count
the same nodes' remote-face normal reactions.

## Known-answer gates

The small-strain series compliance per axis is
`2 mm/E + 1/K + 2 mm/E = 5e-5 mm3/N`. The reference result at 4 N is a
`5e-5 mm` outer-face approach, a `1e-5 mm` interface overlap, and
`2e-5 mm` shortening in each elastic cube. The nodewise Ux/Uz profile formulas,
force and moment resultants, support node groups, and tolerances are in
`expected.json` for the independent verifier.

Each axial support resultant must be within `1% + 0.001 N` of 4 N. Pressure
compliance must be within `1% + 1e-10 mm3/N`. Normal profiles, interface gap,
and face warp use an absolute `1e-7 mm` tolerance (0.2% of the predicted
approach). Transverse/auxiliary support and global force closure use `0.041 N`;
the first-moment closure uses `0.041 N mm`, calculated as
`0.01 * 4 N * 1 mm + 0.001 N mm`. The explicit `1 mm` reference length and
`0.001 N mm` floor keep the moment tolerance dimensionally stated without
changing its value.

At this load, the linear small-strain profiles estimate a tangential contact
overlap area near `3.9999 mm2`, a `0.0025%` reduction from the reference
`4 mm2`. This is an applicability estimate, not a rigorous worst-case local
error bound or exact pointwise pressure prediction. The pressure loads also
include consistent nodal forces at central face edges that belong to contact
patches. These limits are recorded for parent review before freeze; no
pointwise pressure or transformed MORTAR-field gate is imposed.

Require one accepted step at total/relative time 1, no rejected attempt or
cutback, and MORTAR iterations no higher than the source-derived limit 14.
DAT and FRD request U and RF for all 81 nodes. CONTACT requests CDIS/CSTR;
FRD contact data must contain the six expected components and at least one
finite node. Additional contact-node coverage is diagnostic and is compared
with each case's distinct slave-node count in `expected.json`.

## Reproduction

Run `python3 prepare.py` to recheck source pins and regenerate the four inputs,
`expected.json`, and `readiness.json`. It refuses to run after an input freeze
or execution artifact exists. It does not launch CalculiX. The parent must
review the finite-geometry and patch-edge loading notes before freezing these
inputs.

All numerical gates are fixed from the stated analytical reference before
execution. Do not widen them in response to a solver result; preserve a failed
result and document any later controlled change as a separate attempt.

## Parent-owned attempt02 lineage

This is a separately captured preparation because the earlier conversation's
verifier worker remained active. `source-snapshot.json` records the exact
captured inputs. The four decks are unchanged. Before native execution, the
parent made the existing 1% + 1e-10 mm3/N compliance tolerance numeric in the
producer, corrected measured pressure compliance to area times displacement
divided by force, and corrected the input-path key used by the root verifier.
These are verifier/schema repairs; no physical inputs or gate values change.
Synthetic preflight results are software checks, not native mechanics evidence.
The root result audit also explicitly requires the frozen and executed case
order to match `expected.json`. Source-snapshot and synthetic-preflight
artifacts are included in the input freeze.
