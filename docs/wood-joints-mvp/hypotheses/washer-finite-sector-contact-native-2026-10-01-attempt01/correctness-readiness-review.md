# Independent correctness and readiness review

**Decision: REFUSE a native launch for this freeze.** This review covers only
the hypothetical contact/load-transfer software fixture. It does not qualify
the washer, wood, contact pressure, material resistance, or any candidate
joint. No solver was launched for this review.

The reviewed freeze is
`6ccdd8cee4c499c7438aef8c07a6ee9cba8d11beb145fdb1719cde9f4b7e95c4`.
Its seven input/helper/receipt hashes and all twelve declared source-copy
hashes match the frozen records. The main pins are:

| Artifact | SHA-256 |
| --- | --- |
| `model.inp` | `b31196614fe4eb597dc22eeb7ba95203772863dbafba0b0a5ac360e500842297` |
| `model.json` | `3e33665c3f11e10790ab855ad960d18cc9fc0c874beb7ebc9bdec69eacf5c06b` |
| `model_coordinates.json` | `615b432c270ac9b433c07879eda923f8c9357d4720abe4fd11668982d4207629` |
| `verify.py` | `164abdea936bb0443d66096ee89cb7059c3db2d27da945c1fb35f555042c8086` |
| `contact_pair_output.py` | `c729729c9f7d520dfaa4d835e5a0c2ce633ab9e12e0e60aef931b1c98df03496` |
| `source-pins.json` | `6e1aa81a55ebddf7d8efc41316c37e7383240485da7eafee68785f28febd26ca` |
| `preparation.json` | `80d4d571ee13f8e11939d22759403e671159efc9c9b60e6cd77862c95861b8a2` |

The pinned CalculiX 2.23 binary hash is
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`, and the
container image is
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
The official source archive (`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`),
manual HTML archive (`ed14b31b51972d5492209a42fcd52a062e36cbc7843bcd358617cb3aee0da736`),
manual PDF (`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`),
and the referenced manual-section hashes were checked against `source-pins.json`.

## Blocking finding

The frozen [`model.inp`](model.inp) contains no `*BOUNDARY` card and no
alternate constraint card. I independently scanned the full deck: counts are
zero for `*BOUNDARY`, `*EQUATION`, `*MPC`, `*COUPLING`, and `*TIE`. The `GROUND`
and `UPPER_GAUGES` node sets exist only as sets and output requests; they do
not constrain any degrees of freedom.

The pinned preparation source constructs the intended constraints at
[`prepare.py`](../washer-contact-known-answer-preflight-2026-10-01/prepare.py:519):
all `GROUND` nodes fixed in DOFs 1–3, node 33 fixed in DOFs 1–2, and node 45
fixed in DOF 2. But its deck assembly at lines 525–554 never appends
`boundary_text`. The frozen deck therefore has no fixed lower support and no
upper in-plane gauges. The assembly retains unconstrained rigid-body modes;
the intended support and gauge reactions do not exist as constrained-DOF
reactions. Consequently, the static contact solve and the verifier's ground
reaction, gauge reaction, and whole-model balance gates cannot establish the
declared load path. Solver convergence, if any, would not cure this defect.

Before another attempt, regenerate the deck with the intended boundary block
included, add an offline regression that checks the actual emitted deck for
the exact ground and gauge constraint inventory, then create a new freeze and
obtain fresh readiness reviews. Do not use this frozen deck for the reserved
launch or patch this attempt in place.

## Independent checks that do not clear the blocker

Parsing the frozen deck and coordinates independently confirmed 1,600 nodes,
768 C3D10 elements, 64 slave faces, and 64 master faces. The two contact
surface inventories match face-for-face by all six node coordinates. Their
FE contact area is `73.47521901409 mm²`; the upper and receiver FE volumes are
`110.21282852114 mm³` and `220.42565704228 mm³`.

The load surface contains 16 top-face triangles and the declared 45 pressure
nodes. Its FE area is `18.36880475352 mm²`, centroid
`(2.63149801541, 2.63149801541, 1.5) mm`, and the independent inward-pressure
resultant at 2 MPa is force `(0, 0, -36.73760950705) N` and origin moment
`(-96.67494650872, 96.67494650872, 0) N·mm`. The pressure nodes are disjoint
from gauges `{33, 45}` and from the ground set. These agree with the frozen
oracles within rounding.

The pinned 2.23 manual sections identify `P` as the pressure label on
element-face surfaces, use the C3D10 face numbering in the deck, describe
face-to-face penalty contact and its linear pressure-overclosure law, define
`RF` as total external nodal force (including distributed-load contributions),
and define `CF`, `CFN`, and `CFS` as slave-surface resultants with moments
about the global origin. The pinned `printoutcontact.f` source matches the
parser's six force/moment fields and slave-pair semantics. The upper material
and receiver remain hypothetical isotropic diagnostics; the receiver is not
wood and the normal penalty is not a wood-compliance model.

The verifier's six-point TRI6 integration uses current nodal coordinates and
is an exact degree-four integration of the continuous follower-pressure force
and origin moment for a quadratic face. CalculiX 2.23's C3D10 element-load
assembly uses current face coordinates under `NLGEOM` and the three-point
`gauss2d5` triangle rule. That rule exactly integrates the pressure area
vector, while its discrete moment need not equal the verifier's exact
continuous moment for a curved deformed face. The frozen moment tolerances
would need to bound that difference in any regenerated attempt. This method
detail does not change the refusal: the missing boundary conditions alone
make this freeze unready.

Even with corrected constraints, a pass would establish only the bounded
software load-transfer/resultant fixture. It would not establish washer
stress, wood crushing or splitting resistance, candidate joint capacity, or
product acceptance.
