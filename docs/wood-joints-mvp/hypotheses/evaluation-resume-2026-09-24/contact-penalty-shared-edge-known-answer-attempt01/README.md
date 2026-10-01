# Shared-edge C3D10 penalty-control coupon

## Status and scope

Prepared for parent review. The two inputs have not been frozen or run. This
packet isolates the unchanged surface-to-surface penalty controls for the
shared-slave and cross-role shared-boundary cases. It does not rerun MORTAR,
qualify the full joint patch, or change the reviewed joint model.

The preceding four-case packet attempted `shared_slave_mortar` first and
stopped on the native failure: CalculiX exited 201 after 201 iterations with
no accepted state. The other three cases, including both penalty controls,
were unrun there. Its stdout also reported removal of multipliers for shared
slave nodes 1, 4, and 24; the source identifies analogous slave/master
cross-role handling, but that branch was not exercised. These observations do
not establish the cause of the MORTAR failure. This packet records the failed
attempt's frozen input, execution, and diagnostic hashes for lineage only.

## Cases and frozen geometry

Both cases use two perpendicular, initially touching contact pairs in a
three-body fixture. `shared_slave_penalty` assigns the central bottom and
central left faces as slaves; they share nodes 1, 4, and 24. In
`cross_role_penalty`, the central bottom remains a slave, the central left
face is a master, and the outer left face is the other slave; nodes 1, 4, and
24 are shared across a slave and a master in different pairs. Each input has
four distinct surface definitions, with surface-to-surface contact on both
pairs.

The decks use three exact 2 x 2 x 2 mm bodies, 81 nodes, and 18 C3D10 elements.
Each matching quadratic contact patch has 4 mm2 area. Geometry, material,
loading, boundary conditions, output requests, and contact controls match the
two corresponding penalty inputs frozen in the preceding packet. The
regenerator checks the source pins and requires byte-identical regenerated
inputs; it makes no threshold or geometry changes.

The one-step nonlinear static load is 1 N/mm2 on the central top and right
faces, for 4 N per axis. For `E=100000 N/mm2`, `nu=0`, and penalty slope
`K=100000 N/mm3`, the small-strain series compliance is
`2 mm/E + 1/K + 2 mm/E = 5e-5 mm3/N`. The expected approach is `5e-5 mm` at
4 N, with `1e-5 mm` interface overlap. Expected displacement profiles,
support groups, contact checks, and every acceptance tolerance are specified
in `expected.json` and checked by the independent offline verifier.

The unchanged gates include 1% plus 0.001 N for each 4 N axial support
resultant; 1% plus `1e-10 mm3/N` for pressure compliance; `1e-7 mm` for normal
profiles, interface gap, and face warp; 0.041 N for transverse/auxiliary
support and global force closure; and 0.041 N mm for first-moment closure
(`0.01 * 4 N * 1 mm + 0.001 N mm`). Require one accepted full increment, no
rejected attempt or cutback, all 81 nodes in DAT and FRD displacement/reaction
output, and finite requested contact fields. Additional contact-node coverage
is diagnostic; there is no pointwise pressure gate.

The linear profile estimates a 0.0025% projected contact-area reduction at
this load. It is an applicability estimate, not a rigorous worst-case local
error bound or exact pressure prediction. The consistent pressure loading at
some contact-patch edge nodes remains a parent-review item.

## Preparation and lineage

`source-snapshot.json` identifies the exact preceding frozen packet and the
failed MORTAR attempt. Only its two penalty decks are present under `input/`;
no prior freeze, execution output, or review decision is copied as authority.
`prepare.py` regenerates `expected.json` and `readiness.json` without launching
CalculiX. `parent_preflight.py` checks deck parsing and the independent
known-answer arithmetic using synthetic fields; it is software preflight, not
a physical result.

The parent owns the static review, any freeze, serialized native execution,
and final result audit. Do not widen or tune gates in response to a solver
result. A penalty-control pass would test only these penalty formulations and
the two shared-node role patterns; it would not establish MORTAR applicability,
joint acceptance, or release.
