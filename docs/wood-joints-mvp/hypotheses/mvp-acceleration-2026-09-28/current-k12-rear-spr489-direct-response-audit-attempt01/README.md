# K12-rear SPR489 direct-master response method preflight

This packet prepares a response auditor for one input-only method variant:
the K12-rear SPR489 carrier's two direct-master qghost equations. It does not
freeze inputs, launch a solver, produce variant forces, or accept the frame.

The validator first calls the original pinned 711 `_validate_model` on the
unchanged K12-rear selected-floor model, deck, and case context. It then binds
the exact direct-master input audit and source pins, verifies the emitted deck
has 21,844 equations with only rows 19,433 and 19,434 changed, and checks those
rows against the audit-serialized Qy/Qz maps. All other model fields are
preserved, except the explicit SPR489 method metadata in its two mirrored
carrier records. That metadata is checked against the baseline binding and
the pinned audit map. The source input still has 1,292 unilateral carriers,
348 retained bilateral springs, 50 bodies, the 23/77 floor mask, and 46/154
active/inert floor tangent rows.

The response-core fork factors the audited scalar coordinate from the input
audit's 80 physical master DOFs as `q = -sum(c_i U_i)` and propagates its
native-token radius as `sum(abs(c_i) U_radius_i)`. It uses that source
coordinate only for SPR489. Every other carrier continues through the pinned
711 helper. The SPRINGA geometric `dd - dd0` table law, actual emitted initial
span, 16-epsilon length-subtraction guard, endpoint RF action/reaction,
physical-owner transfer, complete MPC checks, exact-floor recovery, and
all-body/global balance checks remain in the same response core.

The sealed validator-produced contract is an immutable exact type. The core
rejects dictionaries, duck-typed builders, changed method inputs, mutations
to its source map, and contexts that do not preserve the original K12-rear
case/source/support authority. A parent-created post-freeze context is
required for a future native response audit. Its non-input authority fields
must match the pinned baseline context; only the selected model/deck paths and
hashes may point to byte-identical copies of the pinned direct-master inputs.
This packet does not create that context.

The read-only replay reproduces the prior rejection of the original K12-rear
DAT: 9,044 carrier/increment checks identify one SPR489 qghost/source-projection
interval mismatch at time 0.2. A coordinate-only comparison of the same old
DAT tokens shows the direct-master scalar interval contains qghost at all seven
reported times. That comparison reports no endpoint forces, does not audit
variant equilibrium, and does not turn the old DAT into a direct-master result.
The pure coefficient-map fixture also checks a positive affine projection,
common-translation cancellation, and propagated token radius. The already
parent-reviewed SPR489 scalar coupon supplies the separate 18-state and
owner-wrench known-answer method evidence; no new solver run was performed.

Reproduce the input, algebra, negative-contract, and old-DAT checks from the
repository root with:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-response-audit-attempt01/verify_method_and_diagnostic.py
```

For a later parent-owned native run, the postprocessor command shape is:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-response-audit-attempt01/response_core.py \
  <parent-created-variant-context.json> <frozen-run-packet/model.json> \
  <frozen-run-packet/model.dat> <frozen-run-packet/model.inp> \
  <frozen-run-packet/execution.json> \
  --output <frozen-run-packet/response-audit.json>
```

The frozen run packet's `model.json` and `model.inp` must be byte-identical to
the pinned method inputs. The context, freeze, execution record, terminal
stdout/stderr, and DAT must bind that exact copy. A passing response audit
would establish only the numerical response for this one method variant and
stated K12-rear support branch; parent validation and the existing engineering
gates remain separate.

Pinned inputs:

- Baseline model/deck/context SHA-256: `9591669b74af719e72df2a681504cab4e283d693eaac5e42920558b30773168f`, `6b630749e918189583147833e3ef94a1338dc5bb28f42171cefc05cb039695e9`, `1a352178c8fe2ad64681d2f456d9fdf29e67b72d0a1cbce3aa3ed5df21259a93`.
- Direct-master variant model/deck/audit SHA-256: `c6f01de8c656fbd4093d4a9784fdfb3b5dfe9e73ead96cf9e1aca51c68f16cd5`, `6c6f8dc02616d3b92dda2f15db1a196e47935233e47eee0afaa56fda694fd3aa`, `6548e52cb9844cd53987b93c4028e1d52a091ef28edec8c78a6bb2d8f7baa83a`.
- Original 711 wrapper/recovery SHA-256: `711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0`, `bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d`.
- The generated `source-pins.json` binds this packet's current code and replay artifacts, along with those frozen sources.

Verified preflight code hashes:

- `response_core.py`: `a1add77cb1079df4468099282269f8af8f86a51fcb527bb69c4963e241e012ca`.
- `validate_direct_master_input.py`: `881133d64a977f359df852cd6540c042a6cb1c831b1e838703d711e2e7c253a1`.
- `verify_method_and_diagnostic.py`: `d33cd4cde2e5c123f75aed4e2271eb36a505e0714c877bdb706cb543f7e97170`.
- `method-and-diagnostic-check.json`: `68ad9aa0f88e6c2e3b59f1bdbc2fdc9798e086669fface48c2915019e44d724e`.

The final read-only replay ended `PASS_INPUT_CONTRACT_AND_READ_ONLY_METHOD_DIAGNOSTICS_ONLY`; nine deliberately invalid inputs/contracts were rejected. The post-freeze CLI was not run because there is no parent-created variant freeze/context or direct-master frame DAT.
