# Accepted all-mesh acceleration output proposal — attempt 01

This is a separate, unbuilt source derivative for a later angular-balance
diagnostic. It adds one append-only file from the existing accepted-state
`results()` output hook: `wj-all-physical-acceleration.csv`. Each complete
block records exact `(step, increment, total time, dtime)`, all 116,162
mesh-node acceleration triples from native `accold` at `%.17g` precision,
and an `END` row with the expected count. It runs only beside the existing
`iout == 2`, implicit-dynamics, `CCX_WJ_DEP_RESIDUAL_AUDIT=1` hook.

The source base is the parent’s current point-map `results.c` snapshot at
SHA-256 `41deef087bdadcdf9bb7a52142c4b6982f8111d3336ab50747c2473f0e11e65c`.
The proposed change is [`results.c.patch`](results.c.patch); the complete
patched source is [`proposed-results.c`](proposed-results.c). The mesh input
is pinned at SHA-256
`117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803`.
[`node-map-audit.json`](node-map-audit.json), produced by
[`verify_node_map.py`](verify_node_map.py), proves that the mesh’s node set
and the union of all 57,643 original C3D10 connectivities are exactly the
unique contiguous IDs 1–116,162. The eight nut controls use IDs 116,163–170
and are absent from solid connectivity. The C hook rebuilds and checks this
exact set at runtime; it does not rely on a node count alone. The emitted
mesh-node set includes zero-density nut-carrier nodes; the postprocessor uses
the existing positive-density element/body map and ignores their zero mass.

The new writer reads `accold` only and writes a separate file. It does not
refresh or modify residual, force, contact, mass, or state arrays. Its caller
is the same accepted-output branch already used for the fit-MPC and contact
point-map records, so it adds accepted states only; it does not emit
iterations or cutbacks. A parser must require one complete `STATE`, exactly
116,162 finite `ACC` rows with unique expected IDs, and a matching `END`;
partial blocks are discarded. Use a fresh execution directory and preserve
the existing paired baseline/instrumented run comparison if this derivative
is built.

The DISP-token position contribution to the first-state inertial moment bound
is only `[1.31e-13, 6.06e-14, 7.08e-14]` N·mm, while the FRD-VELO acceleration
contribution is `[5.04e-5, 3.85e-5, 1.29e-5]` N·mm. Full-precision positions
are therefore not needed for that state. For later states, compute the
DISP-token moment bound `Σ(|δu_y||Ma_z| + |δu_z||Ma_y|)` and cyclic components
from each state. Add exact-`U` output only if that bound becomes material to
the selected comparison tolerance.

Estimated output size is about 10 MB per accepted state at this CSV precision.
Consider trajectory length and disk limits before a future run. This proposal
has not been applied to the active point-map build or run in a native case.
The parent compiled the actual extracted C helper with warnings as errors and
ran a bounded emitter fixture against the pinned mesh connectivity. It emitted
all 116,162 expected IDs and triples for two states, suppressed a duplicate
state, rejected bad node maps/counts/types and physical-node NaN, ignored
control-node NaNs, and left source arrays unchanged. The fixture report is
[`parent-c-emitter-fixture-attempt01/validation.json`](parent-c-emitter-fixture-attempt01/validation.json),
SHA-256 `0b0e460cdf0005176fe2982e205585a063108f3b3bcb7fb38b863bea7393aa89`.
This fixture is not a full CalculiX link or native trajectory and makes no
mechanics or acceptance claim.
