# Knee bridge: other existing bolt references

**Parent calculation complete: all 432 applicable lateral ratios are below one.**
[knee-bridge-other-bolts.py](knee-bridge-other-bolts.py) exposes `build(output)`;
import is inert. The parent executed this fixed saved-force arithmetic once.
No solve, native/CAD/frame calculation, software test, review or prior producer
pipeline ran.

The owned census is **84 old physical axes × six nominal cases = 504 states**:
104 existing axes minus sixteen top/bottom outer-corner axes and four continuous
knee side shafts. All four `left_service_outer_lower_cleat` axes are included;
the remaining inventory is 72 quarter-inch candidate and twelve retained bolts.
The separate corner/spine work owns the exclusions and four new internal ties.

The fixed fresh comparison is `rawlocal/knee-bridge-frame/attempt02/response/comparison.json`
(`c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729`), with response
`62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` and gravity
assessment `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95`.
The current register supplies receivers/component rows only. Fresh demand export
summary `da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70` binds
`global-demands.jsonl` through its pinned receipt. Signed T and signed same-plane
V are recovered from the fresh raw response and checked against that export.
Historical register forces and original export comparison values are not used.

Geometry, bearing intervals, DF-L G=0.50 and applicability rules follow the frozen
[remaining screen](../remaining_joint_screen.py). Candidate comparisons call only
the pure angle/reference functions in [lateral_reference.py](../lateral_reference.py).
Retained comparisons use their finished-receiver register and the same primary
NDS supplied-input Fe/reduction/single-shear functions used by that screen's
92 ksi branch, with the modeled 3/8- or 1/2-inch diameter. The pinned retained
geometry register at `/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json`
is required; its prior result rows are not consumed. Old schema-specific binding,
main/build functions and 45/106 ksi wrappers are not called or patched.

There is one **92 ksi conditional Fyb scenario**, zero interface gap and full
smooth nominal-D bearing under the existing partially threaded profile assumption.
End-grain exclusions retain null lateral references/ratios. Receiver grain angles
and bearing lengths accompany each simultaneous reference. Actual shank/thread
profiles, finished detailing, group/splitting, washer transfer and hardware
qualification remain outside this comparison; signed T carries no axial acceptance.

Output is a fresh immediate child of `rawlocal/knee-bridge-other-bolts/`, containing
an ignore marker, producer snapshot, 504 JSONL records, summary, consumed source
pins and receipt. Source bytes are authenticated before/after; outputs are hash-bound.
The formal 47 pending criteria and eight false release flags remain unchanged.
All qualification, adoption and physical-release assertions remain false.

Parent command, serialized under the existing analysis slot:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-other-bolts.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-other-bolts/attempt01
```

## Completed parent result

`attempt01` records all **504 states**: 360 applicable candidate, 72 applicable
retained and **72 end-grain exclusions with null ratios**. The parent
authenticated **45 source pins and five receipt artifacts**. Governing
`rail_front_bolt_left_2`/A12-forward has **V=1042.994391 N**, simultaneous
**T=194.673315 N**, a **1094.427389 N** mode-II lateral reference and index
**0.953004650**. The four lower-left outer service axes are included; their
maximum reference ratio is **0.007473320**. Tension, group and splitting
resistance do not follow from these lateral comparisons.

| Artifact under `rawlocal/knee-bridge-other-bolts/attempt01/` | SHA-256 |
| --- | --- |
| `summary.json` | `317fd50ce080862f42bdd57c36994a71bfe499f7d069688571524a803c54e630` |
| `receipt.json` | `ee67b7e042a8fcf88d1c37eaaaaac8aebcb815e2cf73b8f1a22a61f44283da83` |
