# Source-MPC force transfer and section attribution

The source attachment equations preserve each top outer block's whole-body
force and moment. They do not prescribe the physical traction on a finished
cut through its bores. This audit makes that distinction executable rather
than assuming that whole-body equilibrium identifies the local load path.

The two blocks are `top_outer_left_cleat` and `top_outer_right_cleat` in
`led-clearance-2x6-runner-seated-blocks-v1`. The source is the three
authenticated rear response families, seven increments each. No new frame
response, native solve, geometry, stiffness or load was introduced.

## Calculation

`nodal_transfer.py` recursively expands the recorded displacement MPCs to
physical translational DOFs. The transpose maps each recorded scalar spring
force to its receiver's nodal force cloud, retaining negative interpolation
weights and propagating RF rounding radii by absolute coefficients. It uses
SPRING2's signed first-end local force and SPRINGA's signed native internal
force with the recorded physical projection nodes. Numerical spring grounds
are excluded. Receiver ownership is checked at every expanded terminal.

All 672 connection/receiver transfer checks reproduce the recorded force
and zero free moment at the appropriate attachment point. Axial ties use
their separate first/second seat coordinates. The 42 complete block states
also recover both receiver-group wrenches and whole-body residuals with
gravity retained at all 20 source body-load nodes. Their source RF intervals
cover the residuals, and the existing 0.1 N / 2 N mm body limits are retained.

The audit then compares positive-side selections of the source point actions
and distributed nodal loads at the ten existing finished-geometry sample
planes. Each state has both one-sided traces, for 420 comparisons. An action
inside the declared 1e-6 mm plane-resolution band is included in the minus
trace and excluded in the plus trace; it is never divided arbitrarily. The
opposite nodal side is also recorded, and the two sides recover the complete
external wrench at the same datum.

## Measured difference

| Quantity | Largest absolute component of point selection minus nodal selection | State |
| --- | ---: | --- |
| Force | 824.989270 N | Right block, K12-rear, increment 6, S03 plus trace |
| Moment | 28,615.447342 N mm | Right block, K12-rear, increment 6, S05 minus trace |

The largest residual moment of any complete expanded connection about its
attachment point is approximately `3.153e-9 N mm`. Thus the local selection
difference is not loss of the source whole-body force/moment identity.

The nodal selections are **not integrated FE stress tractions**. A section
through an element cannot recover those tractions by selecting the element's
nodes on one side. The nodal force cloud is a generalized FE load, not a
physical bearing pressure distribution. The point selection is likewise a
declared concentrated-action equilibrium model. Neither result is assigned
to the disconnected regions of a bored section.

The frozen source represents each of these blocks by one gross rectangular
C3D20 element and 20 physical nodes. Its own geometry diagnostic explicitly
sets `gross_cut_and_bore_stiffness_modeled=false`. The finished STEP solids
contain four bores. The already documented whole-frame conditional responses
remain preserved; this audit does not reject them or declare a strength
failure. It prevents treating either simple cut selection as a validated
finished-section stress field.

## Use and remaining work

Use the complete receiver/pair wrenches as authenticated action evidence.
Use the point cut results only under their stated concentrated-load
idealization. An applicable local transfer/traction method is needed before
assigning stress or strength to an individual bore ligament. If a proposed
method needs additional analysis, the mechanics coordinator owns its
readiness, source freeze and serialized execution. Repeating unchanged
LEG/runner or panel checks does not address this local dependency.

Known-answer tests exercise virtual work, force couples and moment transport,
negative interpolation weights, receiver-specific seats, one-sided cut
selection, discrete node/DOF IDs, ownership/cycle/refusal errors and exact replay bytes. They do not
qualify a material resistance or the complete joint.

## Frozen evidence and replay

The producer is [nodal_transfer.py](nodal_transfer.py), SHA-256
`4612bd1b4b900d9cdd299a4a6e8db84feb1bc8a6fa488a016a2f80accdfa5550`.
The reported values are in the ignored local-only `nodal-transfer.json`, SHA-256
`6fc1949f98d7b40062a4d33d21e103c5f1dda2f8cb0eca99e0bf06ff9e8c744b`.
Both identities bind this summary to the checked producer and result bytes.

| Consumed local evidence | SHA-256 |
| --- | --- |
| Upper action report, `upper-frame-joint-review-2026-09-30/upper-joints.json` | `0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6` |
| Exact geometry report, `upper-block-strength-2026-10-01/geometry.json` | `2ba66f4242b59e73a7dfc14a0b21d20d1f2710b9f835d60fce569eb73353fe91` |

| Additional consumed source | SHA-256 |
| --- | --- |
| A1 model, `current-springa-selected-floor-a1-rear-attempt02/model.json` | `72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd` |
| A1 accepted response, `response-zero-u-token.json` in that folder | `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c` |
| A1 `parent-all-body-response-audit.json` in that folder | `247845921630a092c3f7a79d9ac11c92d732f021d2cb1dc5214e54b1a344deca` |
| A12 model, `current-springa-selected-floor-a12-rear-attempt03/model.json` | `8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8` |
| A12 `response.json` in that folder | `892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274` |
| A12 `parent-all-body-response-audit.json` in that folder | `3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5` |
| K12 model, `current-k12-rear-spr489-direct-native-attempt01/model.json` | `8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd` |
| K12 `response.json` in that folder | `42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6` |
| K12 `audit.json` in that folder | `66c2b9aa397b16cd4c0b2420c5cf4588e15d12bfd3fbfd75b7df8f2b0d1d4bee` |

Those case folders are under
`docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/`.

The upper report's authenticated source map supplies the exact models,
responses and all-body audits for each case. Their hashes are independently
checked and carried in the ignored local-only `nodal-transfer.json`. Public
source provenance is in the [upper action summary](../upper-frame-joint-review-2026-09-30/README.md)
and [finished-section summary](../upper-block-strength-2026-10-01/geometry.md).

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/nodal_transfer.py --verify
uv run --no-sync pytest -q docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/test_nodal_transfer.py
```

Writing requires the explicit `--write` option. Verification requires the
ignored local evidence and exact canonical output bytes; a source-only
checkout is insufficient. This packet accepts no complete joint or six-case
envelope and releases no physical operation.
