# Case-bound selected-floor SPRINGA response auditor, attempt 01

This packet generalizes the strict selected-floor response checks to one
explicit case and one parent-selected diagnostic floor screen. It uses the
input context contract from
`current-springa-case-bound-floor-input-adapter-attempt01` and the unchanged
recovery kernel from `current-springa-frame-response-audit-attempt01` at
SHA256
`b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c`.
Selected cell and row counts are read from the pinned screen; no case ID,
control model, deck, screen, or mask is hard-coded in the response method.

`case-bound-response-context-contract.json` records the required external
context fields and binding rules. The all-bearing controls model/deck and the
diagnostic screen must each be pinned for the same case, and the screen's own
source hash map must include both exact controls inputs. The selected input
model/deck must then match that screen's mask and pass the serialized source
preservation checks. All 1,840 original source carrier rows remain bound;
1,292 unilateral carriers, 348 bilateral carriers, 100 floor normals, 200
floor tangent source rows, and 50 physical bodies are required. Selected
floor tangent reactions are transferred from exact emitted MPC coefficients
and CLOADs. Inactive rows have no reaction channel or restraint. Numerical
SPRINGA ground reactions never count as physical floor support.

After parent freeze, the external context's `selected_input_model_json_*` and
`selected_input_deck_*` fields must point to the exact frozen run model and
deck. The context is hashed outside the model, avoiding a circular model
hash. The context grants no native-run authority. The response auditor only
consumes an already terminal, successful native run and does not launch a
solver.

The audit rejects candidate/revision/case/hash changes, a diagnostic screen
from another control source, changed physical loads or carrier laws, legacy
linear-auditor compatibility, and any selected/inactive mask that differs
from the explicit screen. It checks every accepted increment for MPC
compatibility, unilateral table laws, retained bilateral springs, all 100
normal laws, selected-bearing/inactive-separation complementarity, zero
inactive tangent actions, and all 50 body plus global force/moment balance.
The branch remains a monotone, zero-gap, first-bearing-reference-zero
diagnostic branch. A pass would not establish recontact, branch uniqueness,
floor friction, floor qualification, mechanical acceptance, or design
qualification.

The read-only method replay consumes the already-passed scalar SPRINGA,
exact-floor MPC, and transformed-floor native coupons. It starts no solver:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-response-audit-attempt01/verify_method_fixtures.py
```

The current example binds the prepared `a12-forward` input context and checks
its case, baseline, screen, source transformations, dynamic 35/65 mask counts,
and fail-closed cases. It consumes no frame native output and leaves
`frame_ready_for_native_run` false:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-response-audit-attempt01/verify_case_context.py
```

For a future parent-owned frozen run, pass the final external context first,
then the exact frozen model JSON, DAT, deck, and terminal execution record:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-response-audit-attempt01/response_audit.py CASE_CONTEXT.json MODEL.json MODEL.dat MODEL.inp EXECUTION.json --output RESPONSE.json
```

This packet does not freeze or execute a native model, select a mask, accept a
floor branch, or transfer a response between cases. Parent owns readiness,
frozen inputs, native execution, and final validation.
