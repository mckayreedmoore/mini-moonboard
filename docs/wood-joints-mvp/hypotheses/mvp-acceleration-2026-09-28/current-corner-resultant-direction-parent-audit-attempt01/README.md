# Independent actual-direction arithmetic audit

The parent recomputes each of the four BG001/BG045 lateral force norms,
source-proposed grain angles, Fe interpolation, angle reduction and Mode IV
reference independently, without importing the resistance producer or yield
helpers. It verifies all source pins and compares each result to the final
[resultant-direction screen](../current-corner-resultant-direction-single-shear-attempt01/README.md).

Run `python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-resultant-direction-parent-audit-attempt01/check.py`.
The bound [audit.json](audit.json) passes all four arithmetic comparisons.
This does not verify other yield-mode formulas afresh, qualify material or
hardware, complete axial/group/splitting checks, or accept a joint.
