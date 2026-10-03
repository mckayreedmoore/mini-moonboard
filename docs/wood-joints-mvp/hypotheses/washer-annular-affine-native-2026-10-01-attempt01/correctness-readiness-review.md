# Independent correctness and readiness review

Reviewed 2026-10-01. This review covers only the frozen affine annulus
known-answer job. **Decision: ready for one parent-owned, serialized native
launch under the recorded bounds.** This is a pre-run method-readiness decision,
not a solver result or acceptance of any physical model. The separate contact
job is outside this review and is not approved by it.

## Reviewed packet and pins

The supplied freeze identifier is the SHA-256 of `freeze.json`:

`093ab967c805858b33e3d0530cadab25625cc3b8c69f696d3c39885302fa6817`

Every digest listed by that freeze for its seven frozen files and its copied
source files matched on review. Key frozen file hashes are:

| File | SHA-256 |
|---|---|
| `model.inp` | `36333a78ef54299cefc1fbb4ca0449ec889ce8a174b3dfc0c5ce8d3b17e93e95` |
| `model.json` | `85a02498a9a73901cc6fd27910803fe33f4abc26939fba31ca660f0d8d6707f6` |
| `model_coordinates.json` | `e04f3b7ef6816042c89d6ea8d15efd2eeb139659f06dd967ed3a2dcca35418dc` |
| `verify.py` | `164abdea936bb0443d66096ee89cb7059c3db2d27da945c1fb35f555042c8086` |
| `contact_pair_output.py` | `c729729c9f7d520dfaa4d835e5a0c2ce633ab9e12e0e60aef931b1c98df03496` |
| `preparation.json` | `80d4d571ee13f8e11939d22759403e671159efc9c9b60e6cd77862c95861b8a2` |
| `source-pins.json` | `6e1aa81a55ebddf7d8efc41316c37e7383240485da7eafee68785f28febd26ca` |

The pinned runner, solver profile, manual PDF, official source archive, and
official manual HTML archive hashes also matched their records. The runtime
profile identifies CalculiX 2.23, executable digest
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`, and image
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
I did not launch that runtime.

The method references resolve to the pinned 2.23 documentation: C3D10 and its
four integration points (§6.2.7); prescribed boundary values (§7.4); isotropic
elastic input (§7.47); stress and total internal-energy output (§7.53); nodal
displacement and RF output (§7.99); and static analysis (§7.123). The separate
RF discussion confirms RF includes applied and reaction forces; this deck has
no nodal or distributed loads, so constrained-node RF is the support reaction.
The PDF SHA-256 is
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`; the HTML
archive SHA-256 is
`ed14b31b51972d5492209a42fcd52a062e36cbc7843bcd358617cb3aee0da736`.

## Geometry, boundary field, and oracle

The deck defines a straight-sided polygonal annulus with 2.5 mm inner radius,
5.5 mm outer radius, and 1.5 mm height. It contains 800 nodes and 384 C3D10
elements. I independently reconstructed the tetrahedral faces and corner
volumes from `model.inp`: all tetrahedra have positive signed volume; the
minimum is 0.1793828589 mm³. The 64 top and 64 bottom boundary triangles each
have total FE area 73.47521901409227 mm². This agrees with the 16-sided annulus
area formula and the oracle to about 5×10⁻¹² mm². Summed element volume is
110.21282852113842 mm³, agreeing with the frozen oracle to about
8×10⁻¹² mm³. The midside coordinates are edge midpoints, so each C3D10 geometry
map is affine and these corner-tetrahedron volumes are also the actual
quadratic-element volumes.

The deck prescribes all three displacement components on the 512 exterior
nodes and leaves the 288 interior nodes free. The prescribed field is
`u=(0,0,-10⁻⁴ z)`; the metadata boundary, top, and bottom inventories match
those reconstructed from the deck topology. Material `E=200000 MPa`, `nu=0`
is explicitly hypothetical. The affine solution therefore has
`sigma_zz=-20 MPa`, zero other stress components, opposing top and bottom
forces of 1469.50438028 N, zero origin moments, and elastic energy
0.110212828521 N·mm. Recomputing force and energy from the deck-derived area
and volume reproduces those frozen values within floating-point rounding.

The fixed gates are suitable for this exact patch: displacement error at most
`1e-8 mm`; stress error at most `5e-5 MPa + 1e-5 × 20 MPa`; top/bottom force and
moment limits `0.001 N + 1e-5 × reference force` and `0.02 N·mm + 1e-5 ×
reference moment`; global boundary closure `0.02 N` and `0.05 N·mm`; and energy
error `1e-9 N·mm + 1e-5 × max(actual, reference)`. No gate depends on a result,
and no result-based tolerance widening is specified.

## Verifier and method limits

The deck requests all-node `U,RF`, C3D10 integration-point stress, and the
`ELSE` total with `TOTALS=ONLY`. The frozen verifier checks all-node affine
displacements, the top and bottom reaction wrenches and moments about the
origin, whole-boundary reaction closure, the complete element/integration-point
stress inventory, and total internal energy. The pinned manual defines the
output variables and their applicable limits; the exact freeze binds the deck,
oracle, coordinate map, and verifier used for the run.

This run checks a small-strain linear-elastic C3D10 affine patch and its output
extraction. It does not exercise contact, distributed pressure, washer bending,
material yield, real washer or wood properties, wood crushing, local stress
recovery, joint resistance, or candidate acceptance. It cannot qualify any of
those methods or properties. This boundary matches the freeze's explicit
`mechanical_acceptance: false` and the preflight scope.

I performed read-only hash, deck, oracle, and pinned-document checks. I did not
run tests, Ruff, CalculiX, Docker, CAD, or any solver. The parent reported the
offline preparation tests, preparation-receipt check, and Ruff pass; those were
not repeated here. The freeze records `native_solve_executed: false`.

Proceed only with the parent-owned runner and one exact frozen affine input,
serialized at 1 CPU, 1 GiB, and a 60-second timeout. Stop on a failed launch or
failed frozen gate. This review does not authorize launching the contact job
or extending the claim beyond this method fixture.
