# SPR489 direct-scalar native-output checker

`check.py` is an independent, read-only checker for the small SPR489 direct-
scalar known-answer coupon. It does not invoke CalculiX. Its `--input-audit`
mode parses the exact coupon deck, reconstructs the rank-one solution from its
serialized MPC, spring table and three CLOAD sets, and verifies the expected
owner, interpolation geometry and pinned CCX 2.23 method semantics.

After a parent-owned freeze and native run, use:

```sh
./.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-direct-scalar-parent-method-attempt01/check.py \
  --native-dir docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-direct-scalar-native-attempt01
```

The native mode verifies the frozen source/checker hashes and terminal native
outputs, then checks every printed state for direct-MPC/source-projection
consistency, the unilateral SPRINGA table and endpoint action/reaction, and
the separate numerical SPRING2 support laws. Its independent external-load
oracle and physical owner force/moment recovery apply at the three full-step
endpoints. Intermediate `*CLOAD,OP=NEW` ramp transitions are not inferred;
their load-independent checks remain active.

The three endpoint answers cover tiny positive compression at near-common
translation, a negative/open state and a 0.01 mm positive control. The input
audit records the serialized values. The duplicate `NLGEOM` spelling is
interpreted from the pinned 2.23 `steps.f`: bare `NLGEOM` enables iterations,
and the following `NLGEOM=NO` disables geometric effects without disabling
iteration. The same input card already passed the relative-coordinate
known-answer fixture.

This is method evidence only. The 100 N/mm support springs and scalar ground
are numerical devices; the coupon establishes no K12-rear frame force,
connection resistance, joint acceptance, or design qualification. Parent
readiness and serialized execution remain separate.
