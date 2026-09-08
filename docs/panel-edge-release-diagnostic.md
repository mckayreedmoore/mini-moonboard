# Panel-edge release: mesh-transformation proof

This is a **transformation-only diagnostic**, not a new structural solution.
No released-interface FEA has been run or published by this increment. Physical
CAD, stock schedules and previously accepted meshes/results are unchanged.

## Reason for the check

The accepted `timber-base-development` 40 mm ideal-bonded mesh connects each leg
to both its rim and an upper-panel edge. Consequently, its aggregate leg-to-board
actions cannot be assigned entirely to the four rim bolts. The proposed numerical
sensitivity separates the panel-edge portion while retaining the ideal rim bond;
it does not model the bolts or establish their forces/capacities.

## Verified transformation

The proof runner authenticates the existing solver archives and source hashes.
It reconstructs both plies of each leg by traversing elements from the recorded
leg-floor nodes without crossing the recorded board-interface nodes. Recovered
element/node counts, complete shared interface, floor ownership, volume and
centroid must match the existing CAD-audited joint report.

Only shared leg-side nodes at board-local N below −0.00001 mm are duplicated.
The board keeps its original nodes. All leg elements use the duplicates together;
their coordinates and quadratic midside geometry remain identical. Shared nodes
at N=0 and the rim interface remain. Matching six-node interface faces are
classified explicitly; faces straddling the release boundary are rejected rather
than accepted using a larger tolerance.

| Actual accepted-mesh result | Per leg |
| --- | ---: |
| Duplicated nodes | 72 |
| Released finite-area panel faces | 34 |
| Released panel interface area | 9,218.148831 mm² |
| Retained finite-area rim faces | 148 |
| Retained rim interface area | 81,257.791164 mm² |
| Retained N=0 common-edge nodes | 29 |

The transformation adds 144 nodes in total. Material volume remains
289,546,572.287890 mm³, and every element retains exactly its original tuple of
physical coordinates. Recorded floor nodes and original/asymmetric load nodes
are protected from duplication. No transformed mesh is written by the proof.

## Interpretation limits

Duplicated coincident nodes create a zero-gap, traction-free interface—not
unilateral contact. The surfaces can interpenetrate after deformation. This is
not a conservative upper or lower bound on real response. The common N=0 edge
still shares nodes and can transmit discrete forces; local edge/point-load
stresses are not qualified.

The rim remains ideally bonded, as do the two leg plies. Floor constraints,
isotropic material and all other accepted bulk-model simplifications remain.
Even a successful later solution would provide conditional aggregate actions,
not isolated bolt forces or a construction/climber rating. This proof concerns
the recorded timber mesh; it does not validate the later widened-principal or
panel-insert geometry.

## Next bounded experiment

1. Save a separately identified released mesh and complete node map, bound to
   the accepted input and transformation source hashes. Retain the bonded case.
2. Solve identical small linear basis loads on each representation. Recheck
   connectivity, positive Jacobians, unchanged load/support nodes, exact applied
   forces, endpoint output, global force/moment balance and compliance reciprocity.
3. Compare loaded-point displacement and aggregate leg-to-board resultants at
   the same reference points. Do not divide them among four bolts.
4. Request displacement output on both sides of every released node pair.
   Report relative normal motion and identify closure/interpenetration. Material
   closure requires contact treatment before drawing physical joint conclusions.
5. Accept only numerically audited results with the explicit ideal-rim/common-edge
   limitation. A singular model, unexpected ownership, changed material, failed
   equilibrium or unexplained interface behavior is a failed diagnostic—not
   grounds to silently restore the panel bond or loosen tolerances.

Reproduce the transformation check with:

```bash
uv run python -m fea.prove_panel_edge_release
uv run pytest -q tests/test_panel_edge_release.py tests/test_prove_panel_edge_release.py
```

The compact automated proof checks the actual archived-mesh counts/areas and
rejects a deliberately altered ownership record. Neither command runs a solver.
