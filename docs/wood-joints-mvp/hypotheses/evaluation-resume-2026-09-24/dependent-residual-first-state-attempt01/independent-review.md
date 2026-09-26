# Independent review: first accepted-state dependent residuals

The 24 reported scalar values reproduce from the frozen native hook CSV and
the previously reviewed sparse mass rows. For each dependent node/DOF, I
independently evaluated

```text
Ma = sum_j M[node, j] * acceleration[j, dof]
R_dep = -fmpc - Ma
```

The hook contains one complete state at step 1, increment 1, `t = dt =
0.0005 s`: 24 unique MPC rows, all with `cdep = 1.0`, and three acceleration
components for each of the 337 support nodes. Its row identities match the
24 frozen dependent node/DOF pairs. The sparse mass rows match the immutable
mass extraction exactly: 21 dependent scalar rows, 355 nonzero coefficients,
60 incident C3D10 elements over the 337-node support, using the pinned
four-point consistent mass operator without row lumping. Recomputed `Ma` and
`R_dep` match all serialized values exactly at stored Python float precision.
The largest absolute component is `8.83660703979e-6 N` at MPC row 18
(node 93908, DOF 1).

This is a dependent-DOF full-space force-residual diagnostic under the pinned
assumptions of zero direct pivot load, no contact or rigid-carrier nodes at
the pivots, no cross-dependent right-hand-side terms, and `cdep = 1`. It is
not a solver convergence error, a contact force, a capacity, or a joint
acceptance result. The native execution record reports `solver_failed` with
return code 201 after 650 s; this review covers only the first accepted state,
not a completed history. A full output comparison remains pending.

Reviewed pins:

| Artifact | SHA-256 |
| --- | --- |
| Result `residuals.json` | `47d0128c4e4cae4b2554431b132acff6b309a363e6b76ea8efb78213caa0a4d7` |
| Postprocessor `fea/wood_joint_dependent_residual.py` | `626999de549f35a173ac1dcd478f0b4f02265f41d77e4d4d513a4e6c4965bf0f` |
| Focused tests | `ffc517e685570500c72f3e06dfd3508ac8b0c74cd4fd1e3cfe95836c23eb711d` |
| Hook CSV | `42e77159443284aba9149201377d5af04b06cc792ad86a8bdcb548b51ae21bc6` |
| Native execution record | `bb103133a63954751e926cde03c2f92299280cbe8d3ae89600da11343eba98a9` |
| Sparse mass-row artifact | `f3c6d76da9391665015095269211dea709968580c169fb39f9f61709364530ad` |
| Mass operator source `fea/dynamic_momentum.py` | `f97f0214a8dcd6ae8e539ed3f1377603031776e1b84235bb5dd058e48fd104e3` |
| Postprocessor execution record | `f10e9350642991067a87eff9bd5466461b41f35d97378ba6c9c3a2103ee72dee` |

