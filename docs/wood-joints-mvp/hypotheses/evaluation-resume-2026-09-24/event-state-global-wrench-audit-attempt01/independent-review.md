# Independent review: event-state global wrench reconstruction

Review completed September 26, 2026. Scope was limited to the frozen parent
record, state reports, monitor preflight, source pins, and serialized global
balance arithmetic. The reviewer did not run tests, mass integration, or a
native solve, and made no model or source changes.

## Bindings checked

The parent record matches the reviewed files:

- attempt03 execution record: `fef69a37664f9dea002394270547f6c3e3adec0cb53669daa2b0b2f4de9d0052`
- monitor preflight: `9314da1b5ea0daab4826711eefb155280d164e4f1609204ecddb0f0178020da0`
- state 39 report: `4bc735ccfadfc93a3d62668f542e560640f9c581e2df9f91d4217714fb4a826e`
- state 40 report: `14465ec8d53e2537b1d6e8bf6fcdc8293ae9d17b172c008af12dd547c3f98498`
- attempt04 adapter: `8fe8d2f3c72a9ab27e25ba9b30e31830e01aaaa154550345a7ddd5c98a56e4d7`

The selected states are accepted increments 39 and 40 at 0.0195 s and
0.01975 s. Their eight frozen input pins, selected-state timing, terminal
outputs, and adapter identity agree with the parent record. The no-mass
preflight contains eight finite monitor-control vectors for each selected
state and is correctly scoped to selection only.

## Recomputed moment balance

Using the report convention
`M a − CLOAD − contact + Cᵀλ`, the reviewer recomputed the residual vector
from the serialized inertial, applied-load, contact, and authored-fit MPC
vectors. Differences from the reports are no more than about
`2.2e-17 N·mm`, consistent with component serialization precision.

| State | Recomputed residual moment (N·mm) | Conditional bound (N·mm) | Largest component ratio |
| --- | --- | --- | ---: |
| 1:39 | `(-1.117399542219e-6, 1.24948662754e-7, 8.3921621384e-8)` | `(9.0983e-5, 2.0027e-5, 2.4094e-5)` | 1.23% |
| 1:40 | `(-8.41875942449e-7, -2.11313654583e-7, -1.50284432405e-7)` | `(6.7339e-5, 2.0861e-5, 6.4290e-5)` | 1.25% |

All six component magnitudes are below their conditional output-token bounds.
These bounds depend on reconstructed `M*a` and multipliers. They omit mass
integration/assembly arithmetic, residual multiplier uncertainty, native
operator and broader solver/model uncertainty. No force-residual tolerance is
established. This is not a global-equilibrium pass. The parent record correctly
keeps runtime success, whole-horizon completion, global-equilibrium pass,
capacity, time accuracy, and mechanical acceptance false.

## Report-label caveat

The state files retain legacy `first_state` schema/status text and a nested
`READY_FOR_PARENT_MASS_RECONSTRUCTION` label even though they describe
increments 39 and 40 and the parent record includes completed mass
reconstructions. Their explicit `scope` fields and the parent run record carry
the operative state and completion status. The hash-pinned reports were left
unchanged.
