# WJ-04 local +N pair access screen

This is a refined, unaccepted local extraction diagnostic for the WJ-04 right
lower and upper rail/cleat pairs. It supplements the earlier
[`wj04-pair-access.json`](wj04-pair-access.json) global-projection AABB screen;
that earlier report and note remain unchanged. The machine-readable refined
result is [`wj04-pair-access-local-n.json`](wj04-pair-access-local-n.json).

## Reproduction and source pins

The initial paired-access report is from commit `1267f224`, using producer
SHA-256
`a2eb40c664ea134ecc23cd09589577de05f63ea4fb9555b74b17020d5af7c953`.
This refined JSON was generated after the local sampled-solid screen was added;
it uses producer SHA-256
`7c29491f36d0963e8249948ef1f6ab902d2e7f95ebae74019c97810081cf4aab` and is
not reproduced by checking out `1267f224` alone. With the refined producer
available, run from the repository root:

```sh
/usr/bin/time -p uv run python -m scripts.wood_joint_wj04_pair_access --materialize > /tmp/wj04-pair-access-local-n.json
```

The recorded runtime was about 78 seconds. The archived JSON is byte-identical
to that run and has SHA-256
`dbb8d8f0267a66965c8740190f2209250969423205231f61cbcc7b6b0460f984`.
All 35 declared source-input hashes in the report matched the current files at
archive time. They form a partial transitive closure, not a hash of every
dependency. Key pins are the refined producer above, G7 materializer
`94d2b301450c942f1c7a95f89e3e7ee1ed643ce4db43576c78c1bce04f9302b9`, shared
tool helper `91e0a8c4bd1681fe5f10d96d99c8e6b3ef39b8d7a26fb42b4bb77c6f85ae2fc8`,
source inventory `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`,
and WJ-04 config
`d1c63e1fa5617999e8af68d683cc0f3074fb84f518b048a087ec5ed276206c0e`.

Focused tests: `uv run pytest -q tests/test_wood_joint_wj04_pair_access.py`
(10 passed at freeze); Ruff and `git diff --check` pass. No second CAD run was
made for this note.

## Local +N diagnostic

Each screen moves the source rail, cleat, and their attached rail T-bolt
components along +N from the materialized candidate pose. The stroke equals
the conservative AABB-corner N projection extent of the rail and cleat plus
25 mm overtravel. It is sampled at offsets no more than 5 mm apart. The
target station's principal X-bolts are treated as not yet installed; the
opposite station's principal hardware remains fixed. `base_side_right`, all
fixed service envelopes, and both unresolved far-end connector/SDS duties
remain in the obstacle map. No side-member release is modeled.

| Station | Rail+cleat N extent | +N stroke | Sampled poses | Max gap | Swept-AABB candidate pairs | Exact sampled pairs | Candidate pairs with no exact sample hit |
|---|---:|---:|---:|---:|---:|---:|---:|
| Lower | 207.249 mm | 232.249 mm | 48 | 4.941 mm | 73 | 8 | 65 |
| Upper | 202.235 mm | 227.235 mm | 47 | 4.940 mm | 43 | 8 | 35 |

The exact sampled BRep overlaps occur on each moving service-rail solid; the
cleat and attached rail-bolt solids have no exact sampled hit. The lower rail
overlaps the retained lower outer-duty SDS beam-axis envelopes and five fixed
wire envelopes:

- `clip_horizontal_lower_right_2_beam_1`: samples 1–10, offsets 4.941–49.415 mm.
- `clip_horizontal_lower_right_2_beam_2`: samples 1–18, offsets 4.941–88.947 mm.
- `clip_horizontal_lower_right_2_beam_3`: samples 1–26, offsets 4.941–128.478 mm.
- Wires `wire_078_G6_G7`, `wire_090_H7_H6`, `wire_102_I6_I7`,
  `wire_114_J7_J6`, and `wire_126_K6_K7`: each samples 4–14,
  offsets 19.766–69.181 mm.

The upper rail overlaps the retained upper outer-duty SDS beam-axis envelopes
and five fixed wire envelopes:

- `clip_horizontal_upper_right_2_beam_1`: samples 1–26, offsets 4.940–128.437 mm.
- `clip_horizontal_upper_right_2_beam_2`: samples 1–18, offsets 4.940–88.918 mm.
- `clip_horizontal_upper_right_2_beam_3`: samples 1–10, offsets 4.940–49.399 mm.
- Wires `wire_079_G7_G8`, `wire_089_H8_H7`, `wire_103_I7_I8`,
  `wire_113_J8_J7`, and `wire_127_K7_K8`: each samples 4–14,
  offsets 19.760–69.159 mm.

The largest sampled overlap per rail is 1125.675 mm³ against an SDS beam
envelope; the largest sampled wire-envelope overlap is 478.779 mm³. These are
intersections of the modeled source solids and retained envelopes at the
listed discrete offsets. They do not establish that a continuous route is
impossible. The 65 lower and 35 upper AABB candidates without exact sampled
hits may be broadphase-only overlaps, but unsampled intermediate collisions
remain possible. The report keeps each candidate and exact pair separate.

No moved solid penetrates the z=0 plane at a sampled pose. The minimum sampled
solid z values are 1142.825 mm for the lower move and 1253.173 mm for the upper
move. This plane check establishes no support, handling, or stability result.

The legacy global-projection AABB comparison remains in the JSON separately.
It extends 1444–1695 mm and is not a local unseating distance or route metric.
The new sample screen checks only +N over the stated local stroke; it does not
search another direction, release the side, or prove inter-sample clearance.

## Claim boundary

The result remains `unaccepted_access_hypothesis`, with 66 panel/kicker-axis
obligations and 12 frame-bolt obligations retained and zero accepted
replacements. The two far-end duties remain unresolved. Their SDS envelopes
and service-wire envelopes produce exact sampled hits in the model, but no
field removal, replacement, or physical-route conclusion is authorized by
this diagnostic. It establishes no assembly procedure, temporary stability,
hardware fit, load path, wood capacity, or structural acceptance.
