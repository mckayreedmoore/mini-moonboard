# Header replay for the four moved panel screws

The maintained [header producer](../header_joint_checks.py) now accepts
`--frame` and `--metadata-seed` through
`remaining_joint_screen.bind_frame_sources`. Existing defaults, reference
arithmetic, historical packets and acceptance limits remain intact. The
metadata seed is `corner-frame-attempt01`; it supplies case order and inherited
provenance only. Its response is authenticated without importing its force
arrays or transferring its acceptance.

## Reproduction command

Run from the repository root with the existing environment. Packet arguments
are relative to `mvp-resume-2026-10-01`. The output is immutable: the producer
refuses an existing evidence packet.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/header_joint_checks.py \
  --frame upper-corner-screw-layout/operators-attempt02 \
  --metadata-seed corner-frame-attempt01 \
  --clearance upper-corner-screw-layout/frame-250-attempt02 \
  --members member-screen-attempt02/four-screw-layout01 \
  --lateral upper-corner-screw-layout/bolted-replay-results/remaining-attempt02 \
  --route end-grain-route-attempt03/four-screw-250-attempt02 \
  --output header-joint-attempt04/four-screw-250-attempt02
```

## Result and scope

Status:
`FINITE_CONDITIONAL_STRENGTH_AND_TRANSFER_RESULT_WITH_NO_FIRST_FACE_SHORT_COMPARISON`.

The replay covers six header joints, twelve axes, 72 simultaneous bolt states,
36 interface records, 42 whole-body balances, 105 matching saved header sections
and 1,260 section states. Seventy placement states have zero in-plane force and
retain null first-ray fields. The two directional states have no first-ray
normal-distance comparison below 4D. No adopted actual detailing failure is
recorded by this bounded screen; this does not establish a universal loaded-edge
rule or local joint resistance.

| Conditional quantity | Maximum |
| --- | ---: |
| Individual lateral `V/(Ceg Z)`, 92 ksi | 0.05204245273907306 |
| Same-state lateral with two-fastener `Cg` sensitivity | 0.05252541174822645 |
| Washer pressure / wood reference | 0.2700124600317245 |
| Connected header net normal reference sum | 0.157085560907993 |
| Header net-area shear reference | 0.2381121642667763 |
| Absolute retained header torque, N mm | 29332.62742576074 |
| Header Y splitting demand, N | 159.96404206896526 |
| Characteristic F90 comparison | 0.0284250147487688 |
| Face pressure / header Fc perpendicular | 0.002934190735189075 |
| Whole-body force residual, N | 2.1458390619955026e-12 |
| Whole-body moment residual, N mm | 3.096005229963339e-09 |

The lateral peak is `k12-right / center_principal_header_right_2`.
The washer peak is `a12-rear / knee_outer_left_inner_header_1`.
References retain the existing end-grain Fe perpendicular route, one
`Ceg=0.67` application, `Cdelta=1` envelope and separate `Cg` sensitivity.
F90 remains a characteristic comparison, not a design resistance. Splitting,
torque interaction, washer metal, head/nut transfer and delivered shank
qualification remain unresolved. Complete joint acceptance, formal
qualification and physical release remain false.

The bound force scope retains saved simultaneous forces and the source's
fixed-force seating limitations. The representative position is not a unique
pose or a motion envelope. Source rank-300 gates and strict tangent stability
are not transferred.

## Geometry provenance

`reviewed_geometry_changed=true` comes from the frozen model's four
`owner_authorized_screw_movements`, copied into `checks.json`:

- `round_panel_upper_left_center_4`
- `round_panel_upper_left_rim_4`
- `round_panel_upper_right_center_4`
- `round_panel_upper_right_rim_4`

`bolt_geometry_changed=false`. The maintained binder authenticates the twelve
changed raw rows as belonging only to those four screw axes and checks
unchanged physical body geometry and proposed corner bolt axes against the
metadata seed. This replay performs no geometry or hardware change.

## Source hashes

Paths below are relative to `mvp-resume-2026-10-01`. The complete consumed
source register is the output's `source-pins.json`, including seed provenance,
reference files, support evidence, producer dependencies and finished STEP
bindings. STEP files are hashed only; no CAD operation runs.

| Source | SHA-256 |
| --- | --- |
| `header_joint_checks.py` | `c7827115e29f6366496cb5861c0cba7c19d51691c0d43a28d28d042ae6808cfb` |
| `upper-corner-screw-layout/frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `upper-corner-screw-layout/frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `upper-corner-screw-layout/operators-attempt02/operator-assessment.json` | `1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a` |
| `upper-corner-screw-layout/operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `upper-corner-screw-layout/operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `upper-corner-screw-layout/operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |
| `member-screen-attempt02/four-screw-layout01/member-results.json` | `54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5` |
| `upper-corner-screw-layout/bolted-replay-results/remaining-attempt02/screen.json` | `abe988897087ad9d07f94c5def6a7427cfeb9c493a26ef50d3d13b8baac94d45` |
| `end-grain-route-attempt03/four-screw-250-attempt02/route.json` | `277e7754b2c62e5a98d140de497c753a7cd0362080cef10185cc79be549f3261` |

The frozen remaining producer is
`4d9ea0e03ab98ba4bc8c9e4641a85d5e54603c59cf2ab1d17385de4c16dc964f`;
the member producer is
`5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9`;
the route producer and its attempt02 snapshot are
`5b9faca5696d6c7add02e9ac6d5056363896bb2a7badb7ab7bb3fa8bfc9fe5d4`.

## Output hashes and retention

Parent attempt 02 binds the finalized bottom-component producer metadata.
Its four numerical action/state/placement/section artifacts are byte-identical
to preserved attempt 01; the consumed-source register and summary bind the
final maintained dependencies. All source/output pins below match.

The active saved-array packet is
`header-joint-attempt04/four-screw-250-attempt02`.
It contains 2,528,437 bytes, including its producer snapshot and ignore file.
Raw evidence stays ignored; historical packets remain preserved. No archive
or pruning operation was performed.

| Output | SHA-256 |
| --- | --- |
| `checks.json` | `f34fba71b0416cf7a5d1081a48c66c8d518b642e53e7f7f8a80a0646b707362d` |
| `header-sections.csv` | `f32ab4731eb4cb12fbdc400f81a0fb9ba8d8065eabbccc378483ecd0b36e5953` |
| `joint-actions.json` | `2a37efc475fce1e6eb65b23a8e7fd7b0e8bbdd3be3af9f3f41df0620a262452f` |
| `joint-states.json` | `be78ec533e93963ab900103d107e391b57a1d52125025e47eb06a37f16ef6232` |
| `placement.json` | `9f0aef8c98dab5a41e47472f2c1251b9311789730927ec810c04fedd4ca6f58d` |
| `producer.py.snapshot` | `c7827115e29f6366496cb5861c0cba7c19d51691c0d43a28d28d042ae6808cfb` |
| `source-pins.json` | `5e5cb0f210ee33ec6ecc7885e91b9d68d7f294cfdb24f8efb0e5e427ebee95a6` |

## Checks performed

Targeted Ruff passed for `header_joint_checks.py`. Twenty-one incoming report,
output, clearance and maintained-producer files matched before and after
execution. All 165 consumed source pins and all six hashed generated outputs
matched after execution; the producer also checks consumed pins before and
after arithmetic. No frame solve, native solve, CAD operation, tests, review
loop or commit was performed. Parent owns integration and publishing.
