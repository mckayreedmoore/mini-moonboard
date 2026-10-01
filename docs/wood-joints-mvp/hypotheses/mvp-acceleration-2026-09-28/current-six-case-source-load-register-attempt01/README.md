# Current six-case source load register, attempt 01

This packet records the six current reduced wood-joint load cases directly
from fresh `fea.wood_joint_reduced_case.build_case` metadata. It binds the
force, applied wrench, physical external-load map, body-wrench totals and
equilibrium ledger for each source case. It does not contain solved response
forces, reactions, capacities, bearing-mask solutions or case acceptance.

## Current case inputs

All cases use 250 lb, dynamic factor 2, vertical global force
`-2224.11080763025 N`, a 20 mm panel patch, and 100 mm standoff. The table
shows the horizontal component; the full force, application point, wrench
reference point, moment, patch center and source load-map hashes are recorded
per case in `register.json`.

| Case | Hold | Loaded panel | Horizontal force `(X,Y)` N | Moment about panel-midplane reference `(X,Y,Z)` N·mm |
| --- | --- | --- | ---: | ---: |
| `a12-rear` | A12 | `main_upper_left` | `(0, 300)` | `(-164885.11528647266, 0, 0)` |
| `a12-forward` | A12 | `main_upper_left` | `(0, -300)` | `(-206972.839257467, 0, -0)` |
| `a12-left` | A12 | `main_upper_left` | `(-300, 0)` | `(-185928.97727196984, 21043.861985497188, 25079.09812327298)` |
| `k12-right` | K12 | `main_upper_right` | `(300, 0)` | `(-185928.97727196984, -21043.861985497188, -25079.09812327298)` |
| `k12-rear` | K12 | `main_upper_right` | `(0, 300)` | `(-164885.11528647266, 0, 0)` |
| `a1-rear` | A1 | `main_lower_left` | `(0, 300)` | `(-164885.11528647278, 0, 0)` |

The case-specific differences from `a12-rear` are explicit in each row's
`differences_from_a12_rear`: changed hold/panel identifiers, horizontal and
applied-force/moment deltas, application and wrench-reference point deltas,
per-node physical load-map deltas, per-body applied-wrench deltas, and changes
to the global external-load wrench. The common source geometry/carrier
signature is also compared across all six fresh builds.

## Scenario and source contract

Each fresh build uses the same explicit settings as the a12 adapter:

- `ring_case=A`, mesh size `150 mm`, panel group factor `1.0`;
- Hillman axial-to-lateral ratio `1.0`, retained as a non-qualifying
  diagnostic setting;
- bolt gap factor `0.0`, diagnostic only; contact penalty
  `100 N/mm^3`, a model setting rather than a measured connector property;
- no accessory scenario (`None`, budget `0 kg`); unverified no-slip floor
  assumption only on a bearing cell.

The producer checks each fresh `source_applied_load` against both
`scripts/wood_joint_current_load_cases.py` and the current six-case load
contract. It pins the relevant case, reduced load/body/gravity/geometry/model
sources, the shared model-input and load-contract records, and the inspected
a12 attempt01 adapter inputs. It also pins the active attempt03 adapter,
frozen a12 model/deck/response, freeze and execution records, parent terminal
assessment and all-body audit. It recursively checks the adapter's pinned
upstream sources and checks the terminal assessment fields. `register.json`
contains the observed SHA-256 values and identifies the 25-bearing /
75-separated a12 response as a separate, case-specific reference; it marks the
other five response/mask pairs unresolved.

The producer only calls `build_case`; it does not run CalculiX, rewrite a
solver deck, or read historical response forces. All registered body/global
wrenches and nodal maps are applied source loads, not support or joint
reactions.

## Relationship to the conditional a12 response

The only current numerical response reference is
[`current-springa-selected-floor-a12-rear-attempt03`](../current-springa-selected-floor-a12-rear-attempt03/README.md),
case `a12-rear`, with a 25-bearing / 75-separated floor branch. Its parent
terminal assessment records `PASS_CONDITIONAL_NUMERICAL_RESPONSE`; the frozen
model, emitted deck and response SHA-256 values are respectively
`8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8`,
`e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff`, and
`892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274`.
That result is a conditional numerical response for the listed ring-A,
ratio-1, zero-gap, zero-accessory scenario and unverified no-slip floor
assumption. It is not a six-case envelope, floor/build qualification, joint
resistance pass or climbing release.

The fresh source-load register does not supply a floor mask. A separate
case-specific bearing mask is required before each response assembly: the
a12-rear response branch cannot be transferred to the other five cases, and
the other five masks remain unresolved here. The a12 branch is a reference to
its separately frozen response, not a mask inferred by `build_case`.

To reuse the SPRINGA source/control/floor method, retain the source-bound
1,292 unilateral SPRINGA carriers, 348 bilateral SPRING2 components, 100
compression-only floor normals, and the source-point wrench/CLOAD audit. The
attempt01 `prepare.py` is specifically bound to `a12-rear`, writes to a fixed
`a12-rear` directory, compares case-dependent loads to the pinned C11 a12
map, and installs its conditional exact-stick floor transform. For another
case, the assembly must preserve invariant geometry, material, carrier and
control checks while substituting that case's fresh source load/wrench record;
re-expand and round-trip its own emitted CLOAD; replace the a12-only C11 load
equality oracle with the corresponding fresh case map; parameterize case ID
and output paths; and establish that case's own support mask and response
checks. This packet registers those source inputs only; it does not perform
those assemblies.

## Reproduction

From the repository root, write the register from six fresh source builds:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-six-case-source-load-register-attempt01/produce_register.py --write
```

Rebuild the six metadata records and compare the strict JSON output:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-six-case-source-load-register-attempt01/produce_register.py --verify
```
