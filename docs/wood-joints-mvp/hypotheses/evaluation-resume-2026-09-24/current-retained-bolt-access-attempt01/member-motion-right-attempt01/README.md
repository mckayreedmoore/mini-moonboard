# Right-leg individual translation screen

This prepares one outboard `+X` translation for `lumber_leg_right` from the
attempt04 STEP export. It reuses the source-pinned attempt02 left-leg runner's
STEP verification, projected exit calculation, convex-envelope construction,
containment tests, and BRep intersection helpers. The adapter derives the
direction from the right leg's own positive-X bounds and reads the four
retained stack dependencies from that pinned manifest. It does not assume the
right leg is a mirror copy of the left.

For the nonconvex continuous sweep, the adapter verifies every boundary face:
all leading planar faces are extruded with their inner wires, and every
cylindrical face must have an axis parallel to the selected translation.
Unknown surface types or misaligned cylinders yield an unsupported result.
It validates source and endpoint containment in the sweep and the sweep's
containment in the conservative convex hull. It then checks the exact sweep
against every obstacle hit by that hull; the other hull-clear obstacles are
clear by subset. No positive clearance margin is reported.

The operation assumptions match the left-leg screen: the prior 92 candidate
connector stacks, panels, 66 panel screws, holds/T-nuts, and lights are
removed; the four retained stacks named in the right-leg metadata are removed
before the leg moves; all other retained bolt roles and 131 modeled wires
stay as stationary obstacles. Temporary support, safe staging/workspace,
actual cable routing, actual tools, physical transport, and an overall removal
sequence remain unestablished.

Parent execution and the [independent review](independent-review.md) are
complete. The [report](parent-run-attempt01/report.json) records a 62.468 mm
outboard path, one conservative hull hit at the right floor member, and no
exact-sweep overlap above 1e-6 mm³. The [parent record](parent-run-attempt01/parent-review.json)
adds post-run environment versions. The original invocation was:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-right-attempt01/screen_lumber_leg_right.py --write
```

The adapter is pinned to the reviewed common runner SHA-256
`fdaf703a4b387d2789998533e857c28c7269fe3401fb222d20b26bd650f35499` and the
STEP manifest SHA-256
`d90a93440575b7871fc429c3f8cec621877f805a068b7ff09a60fddc4b1e538b`.
Focused tests use manifest metadata only and do not load CadQuery:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-right-attempt01/test_screen_lumber_leg_right.py
```
