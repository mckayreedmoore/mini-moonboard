# K12-rear direct-master parent all-body audit method

Status: **input-only helper and method-equivalence proof ready; no direct-master
response has been consumed and no all-body audit has been produced**. The
future response schema is bound to the pinned SPR489 response core:
`current_k12_rear_spr489_direct_master_physical_response_audit/v1`.
It also requires the exact status
`PASS_K12_REAR_SPR489_DIRECT_MASTER_RESPONSE_AUDIT_ONLY`, pinned to the
outer direct-master contract override in that response core.

Run the reproducible AST proof from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-direct-parent-all50-method-attempt01/prove_method.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-direct-parent-all50-method-attempt01/prove_method.py --verify
```

The proof pins the source helper
`current-springa-selected-floor-parent-response-audit-attempt01/check.py` at
SHA256 `7ff46055915e01d945cefe728cc4a4b146b05836976620c7f54100f586130b80`.
It also pins the response core that declares the accepted schema. The proof
compares the full source and target AST after normalizing only the exact
response-schema/status literals and the declared output-routing additions. The
`balance` function, seven-increment physical force/moment accumulation loop,
and audit-result/nonacceptance payload are each checked for exact AST equality.
This preserves the source's 0.1 N / 2 N·mm printed and interval criteria.

The stand-alone helper is [check.py](check.py). Once a fully audited response
exists, it accepts only that exact response schema and the existing
`current_springa_selected_floor_input_model/v1` model schema. It independently
reconstructs the fifty body datums from physical-body node sets, applies
load-factor-scaled body loads, sums signed owner forces and moments from
`physical_connection_forces` and `exact_floor_tangent_reactions`, and checks
each body plus the global system at every reported increment. It also requires
the adjacent model/deck/DAT pins, terminal zero-return execution, and final
load factor one.

Output defaults to this method folder's `audit.json` and can be redirected:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-direct-parent-all50-method-attempt01/check.py MODEL_JSON RESPONSE_JSON --output /path/to/new-audit.json
```

The helper refuses output within either input directory or the pinned original
parent-audit folder, so it cannot overwrite the source records. The audit
reports independent physical force/moment closure only; it does not validate
the direct-master SPR489 displacement method, carry connection resistance, or
accept the joint. No response was available for this input-only method packet,
so no force rows, synthetic values, audit result, or acceptance are included.
