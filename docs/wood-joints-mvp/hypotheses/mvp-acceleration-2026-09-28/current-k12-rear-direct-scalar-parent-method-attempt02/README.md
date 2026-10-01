# SPR489 geometric-law post-hoc replay

This sibling packet replays the single terminal-zero native coupon run at
`current-k12-rear-direct-scalar-native-attempt01`. It never launches a solver
and does not edit the frozen attempt01 checker or native outputs. The preserved
terminal assessment records the attempt01 constitutive-check rejection at
step 2, total time 1.825.

The mismatch is in the checker quantity. Attempt01 compared the SPRINGA force
table to the direct scalar displacement `q`. CCX evaluates the spring table
from the actual endpoint length change `dd - dd0`. At the rejected state, the
serialized initial span is exactly 100 mm, native `q` is
`2.883617e-7 mm`, and recomputed `dd - dd0` is `2.8836170429258345e-7 mm`.
Their difference is `4.2925834586395354e-15 mm`; multiplying by the serialized
slope gives about `1.13e-9 N`, enough to miss the very narrow q-only DAT/RF
intersection. The native Q RF token is `0.07586313 N` with half-last-place
radius `5e-9 N`.

The corrected replay uses the unchanged method in the pinned 711 SPRINGA
auditor: calculate `dd - dd0` from emitted endpoint coordinates and native
displacements, propagate the U-token intervals through the current spring
axis, and include the existing `16 * epsilon * max(1, dd0, dd)` bound for
length subtraction. It intersects the resulting force interval with the
native RF token interval using the existing force arithmetic guard. This
restores the constitutive quantity and its existing representation bound; it
does not loosen a threshold. Direct-MPC/source-projection checks remain
separate and unchanged.

Run the replay without invoking CalculiX:

```sh
./.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-direct-scalar-parent-method-attempt02/check.py \
  --native-dir docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-direct-scalar-native-attempt01 \
  --output docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-direct-scalar-parent-method-attempt02/native-output-audit.json
```

`diagnosis.json` and `source-pins.json` bind the replay to the original
checker, freeze, execution, native DAT, serialized deck/model, pinned 711
source, and preserved terminal assessment. The replay result remains subject
to parent independent review. It is method-coupon evidence only; it does not
accept K12-rear forces, a frame, a connection, or a design.
