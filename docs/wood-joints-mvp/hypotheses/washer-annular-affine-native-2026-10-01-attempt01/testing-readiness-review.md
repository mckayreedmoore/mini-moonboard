# Testing/readiness review: affine annulus

**Conclusion: PASS for one parent-owned affine software-method attempt under the frozen run bounds.** No substantial testing or gate defect was found. This conclusion covers only the C3D10 affine annulus with the diagnostic isotropic `nu = 0` elastic field. It does not establish native execution success, contact readiness, candidate properties, washer capacity, or mechanical acceptance.

## Reviewed freeze

`freeze.json` SHA-256: `093ab967c805858b33e3d0530cadab25625cc3b8c69f696d3c39885302fa6817`.

All seven frozen artifact hashes match the freeze:

| Artifact | SHA-256 |
|---|---|
| `model.inp` | `36333a78ef54299cefc1fbb4ca0449ec889ce8a174b3dfc0c5ce8d3b17e93e95` |
| `model.json` | `85a02498a9a73901cc6fd27910803fe33f4abc26939fba31ca660f0d8d6707f6` |
| `model_coordinates.json` | `e04f3b7ef6816042c89d6ea8d15efd2eeb139659f06dd967ed3a2dcca35418dc` |
| `verify.py` | `164abdea936bb0443d66096ee89cb7059c3db2d27da945c1fb35f555042c8086` |
| `contact_pair_output.py` | `c729729c9f7d520dfaa4d835e5a0c2ce633ab9e12e0e60aef931b1c98df03496` |
| `source-pins.json` | `6e1aa81a55ebddf7d8efc41316c37e7383240485da7eafee68785f28febd26ca` |
| `preparation.json` | `80d4d571ee13f8e11939d22759403e671159efc9c9b60e6cd77862c95861b8a2` |

The pinned supporting sources also match `freeze.json`, including `prepare.py` (`d8c5e7c037388349cee115e1d70623534aafaff529ccf0b72b7861f61f7a4aa7`), `tests/test_preparation.py` (`a90474b4a4ce9ee45638cf4771b419d535c0ca97b50b6c432df72b8ee6466826`), and `verify_preparation_receipt.py` (`2eebd775d4482f3e48dd55652bc061dac0820c520c29106a915e81199db27c54`). Source pins include the 2.23 manual, source archive, solver profile, and parent runner protocol.

## Checks and coverage

- The five offline tests pass. They cover the affine FE-area/volume and compression-sign contracts, synthetic known-answer acceptance, missing nodal rows and a perturbed free-node displacement, substituted stress element IDs and duplicate integration points, plus separate contact-fixture tests.
- The preparation receipt passes: 8 generated-file hashes and 5 supporting-code hashes verify, and it explicitly records no freeze, native run, readiness, or mechanical acceptance.
- Regeneration into a temporary directory reproduces the frozen affine deck, oracle, coordinate map, parser, source pins, and preparation receipt byte-for-byte.
- I independently parsed the frozen deck and derived its corner-tetrahedron volume and planar top/bottom face areas. The deck contains 800 nodes and 384 C3D10 elements; all 2,304 midside positions match straight edge midpoints within `7.1e-12 mm`. Derived FE volume is `110.21282852113829 mm^3` and face area is `73.47521901409227 mm^2`. Differences from the frozen oracle are `7.6e-12 mm^3` and `4.9e-12 mm^2`.
- The frozen audit requires complete displacement and RF node inventories, exact prescribed and free-interior affine displacement fields, all four stress integration points for every element and six stress components, signed top and bottom force/moment resultants, whole-boundary force/moment closure, and total elastic energy. The gates are frozen and explicit.

The reviewed run scope is the single affine job, one launch maximum, 60 seconds, 1 GiB, and one CPU as recorded in the freeze. No solver or Docker execution was performed in this review. The separate contact job remains outside this conclusion.
