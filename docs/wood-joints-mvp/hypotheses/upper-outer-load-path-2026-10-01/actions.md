# Upper outer receiver and section actions

This packet closes the bounded source-action bookkeeping for
`top_outer_left_cleat` and `top_outer_right_cleat` at the reviewed revision
`led-clearance-2x6-runner-seated-blocks-v1`. It retains all three accepted rear
cases—A12-rear, A1-rear and K12-rear—and all seven response increments per case.
The report contains 42 block/state records, 672 individual receiver actions,
840 discrete body-load node actions, 210 exact-geometry section/state records
and 420 one-sided cut traces. These are same-state records, not an independent
maximum envelope.

The source model has sixteen incident connections per block state: four bolt
lateral-plane actions, four outer-seat axial ties and eight contact actions.
Each row retains its signed force, source row IDs, RF rounding interval and
named receiver. Axial ties use their separate `first_point` and `second_point`
when present. Their paired endpoint forces are opposite; each endpoint moment
is transported from its own physical attachment point to the same block datum.
The 20 discrete source body-load forces are retained at their model nodes and
scaled by that increment's load factor.

For every state, the individual block-side actions reproduce both host-group
force and moment resultants in the frozen upper-joint balance. The full set of
16 receiver actions and 20 body loads also reproduces the source whole-body
residual and propagated RF rounding intervals at the recorded datum. Across
the 42 records, the largest component residuals are 0.000150102 N and
0.004134260 N·mm. They remain within the source audit limits and intervals.
This verifies extraction and equilibrium bookkeeping; it does not validate
the source stiffness/contact response or accept a joint.

The section planes are the three bolt mid-bearing stations and two intervening
midpoints already extracted from each hash-verified finished block STEP solid
in the [upper-block geometry packet](../upper-block-strength-2026-10-01/README.md).
Each section receives a six-component wrench from a point-action model: source
connection resultants at their named attachment endpoints and the discrete
body-load forces at their source nodes. The mechanics input instead represents
each top outer block as one gross rectangular C3D20 member and distributes
attachment equations to member nodes. A response resultant at its source
point therefore does not establish the actual finite-element force on either
half when the interpolation support crosses a section. The finished STEP
sections retain modeled bores; the native member mesh omits them. Geometry and
point-action wrenches remain separate evidence, and neither supplies regional
cut-face traction or strength.

Every cut is evaluated from both sides. A point within 1e-6 mm of the plane is
listed as on-plane and assigned in full to one half in each trace: positive-side
material for the trace approached from below, and negative-side material for
the trace approached from above. The two traces preserve the action jump; no
force is split arbitrarily. Their partitioned external wrenches reconstruct
the whole point-action wrench at that same section datum. Across 420 traces,
the largest floating-point closure residual is 1.81e-13 N and 6.39e-12 N·mm.
That is a point-action partition identity, not an FE cut-traction result.

The three bolt-station cuts have on-plane actions in both blocks. Each outer
station coincides with one rail bolt's lateral and axial-tie resultants. The
middle station coincides with both side bolts' lateral and axial-tie resultants
and four discrete source body-load nodes. Neither between-station midpoint has
an on-plane point action. The raw report records exact source IDs per state.

No load is allocated uniformly or by area among section-face regions. No
section stress, regional transfer, capacity, complete-joint resistance,
six-case envelope, native solve, fabrication, drilling or structural release
is established. The separate source-support reconstruction belongs to the
root's separate nodal-transfer work. The four-block source review remains at its
own [bounded status](../upper-frame-joint-review-2026-09-30/README.md).

The producer is [actions.py](actions.py), SHA-256
`9a022af7462d1bbe0730d7da99510e64908cf9eae7673cb04412a0f7aa32d24f`.
The source-pinned report is the ignored local file `actions.json`, SHA-256
`4003e4caa08302eb6c6e768ad7344f5509e7c53e019117de39e2c8a1e4868f63`.
The independently replayed ignored `source-pins.json` has SHA-256
`1ce39100e5d4ac739198f1d938d81af91edaf900777affb9459247606eae3c33`.
Both raw JSON files remain ignored under the repository policy; this Markdown
summary and its source hashes are the durable record.

From the repository root, read-only verification checks all pinned source
hashes and byte-compares both ignored outputs against canonical replay:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/actions.py --verify
```

Running the same script without `--verify` writes `actions.json` and
`source-pins.json`. It is the explicit output-generation mode.

The independent pin set has twelve source files:

| Source | SHA-256 |
| --- | --- |
| `docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/upper-joints.json` | `0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6` |
| `docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/produce.py` | `d650e2abcbbcd4633ecf41d7ccb44daba4063ca4c281d9792f7204bafd6fa2a6` |
| `docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/geometry.json` | `2ba66f4242b59e73a7dfc14a0b21d20d1f2710b9f835d60fce569eb73353fe91` |
| `docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/geometry.py` | `ea1273e95833192624afd4b3b6408a3065158cc302924ed702032c2896f42680` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/model.json` | `8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/response.json` | `892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/model.json` | `72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json` | `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/model.json` | `8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/response.json` | `42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/top_outer_left_cleat.step` | `c4ecd881a9dc2e78195d028bf360cc42da86e97129ac44db7fafd7c77f50ba88` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/top_outer_right_cleat.step` | `70b94b711f629b6b1d955083c7eafddb07b104c04878c46ae032ba4c953be25c` |
