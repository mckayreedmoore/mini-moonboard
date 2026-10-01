# Current group-action method attempt05: correctness review

Review date: 2026-09-28  
Scope: independent, read-only correctness review of the pinned attempt05 source and patch. No source or test files were changed. No project tests, solver, or Docker were run; two small direct input probes are recorded under the findings.

## Pin and replay verification

`attempt05.patch` was replayed in a temporary copy of the pinned attempt04 base using `patch --batch --fuzz=0 -p1`. It exited 0. The two replayed files exactly matched the attempt05 maintained hashes. The pinned attempt04 source and test bytes also matched their declared hashes. The attempt04 terminal-hash file matched the hash recorded by attempt05, and the criteria-method-map hash matched both the attempt05 pin and the current file. Attempt05's README, patch, source-pins, and validation hashes matched its terminal-hashes file.

| Reviewed item | SHA-256 |
| --- | --- |
| `AGENTS.md` | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| attempt05 `README.md` | `c31198ebcf7227442a2a9a1ce62f6b5fbf0b2a84257370bd7f22ddf1a54da50e` |
| attempt05 `attempt05.patch` | `e9f829bab63b6977e9ec071ab6e52e1fee82fa13113841f9b705dae46c7d5c36` |
| attempt05 `source-pins.json` | `6ef7bd66d0f7fa627d127d407ca25e644ed021a04242044d1a1de6abe3501e34` |
| attempt05 `validation.json` | `381f417f004299761ab7e8952dd65bbf3067ba17e4bcf111c00bd6c9f72c8238` |
| attempt05 `terminal-hashes.json` | `2fa27a9decddd8b2118078c0ccca5dddfba87eef703765d22875c02e8050d248` |
| pinned attempt04 base `mini_moonboard/nds_2024_group_action.py` | `d0d8cf193c9fb26206e459e749c176f0ace5b41bb472ffc24217d8a5942874f6` |
| pinned attempt04 base `tests/test_nds_2024_group_action.py` | `c0137a5144e135e2bac3a4eb6861e0e85d10750b0b3471eb4fc55df13222c3f2` |
| maintained attempt05 `mini_moonboard/nds_2024_group_action.py` | `95305398bf4fc9590f33fe877aafaf0544dce91503b0f09d84db590a938c8122` |
| maintained attempt05 `tests/test_nds_2024_group_action.py` | `91868751abfef9ceab746927904d7cbab9c0ba0881867980d89e2f2ab0b828e7` |
| `docs/wood-joints-mvp/criteria-method-map.md` | `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7` |
| attempt04 `terminal-hashes.json` | `74ef1baf1469d15338b8fdea823ace903c924ba289e6bceb3208a3357ba3f3a0` |

## Findings

### P2 — Deeply nested JSON input can escape the pending result path

In [nds_2024_group_action.py](../../../../../mini_moonboard/nds_2024_group_action.py#L61), `_is_strict_json_value` recursively descends mappings and lists at lines 74 and 82. `_canonical_json_sha256` calls it before entering the exception handler around `json.dumps` (lines 100–112). A sufficiently deep otherwise JSON-shaped payload, including depth in an ignored producer extension, can therefore raise `RecursionError` from the public digest/evaluator API instead of returning `None` and ultimately `pending`.

Minimal reproduction: wrap `None` in a list 1,100 times and call `canonical_group_record_sha256({"nested_extension": nested})`. Observed traceback: `canonical_group_record_sha256:97 → _canonical_json_sha256:101 → _is_strict_json_value:74 → RecursionError: maximum recursion depth exceeded`. The same reproduction raises against the pinned attempt04 base and attempt05 maintained source. Catch recursion-limit failures or use an iterative/depth-bounded validator so malformed or over-deep external records fail closed.

Classification: P2 fail-closed API robustness, but not a false Cg or capacity result. It does not block ordinary bounded method use; it is defensive hardening unless callers permit unbounded nesting and rely on every invalid record returning `pending`.

This is inherited from the pinned attempt04 source; attempt05's direction-normalization change does not introduce it.

### P3 — Sensitivity path comparison conflates distinct JSON scalar types

`_changed_payload_paths` returns unchanged when scalar values compare equal with Python `==` ([nds_2024_group_action.py](../../../../../mini_moonboard/nds_2024_group_action.py#L518), line 550). Python considers `1 == 1.0` and `1 == True`, although canonical JSON gives those different representations. Minimal reproduction: `_changed_payload_paths({"opaque": 1}, {"opaque": True})` returns `[]`. The same result occurs against the pinned attempt04 base and attempt05 maintained source. In a sensitivity call, a separate declared factor-input change can make the actual path list nonempty and allow the method-sensitivity result while this changed extension path is omitted. The numeric Cg result is unaffected by the extension, and the result remains method-only, but the advertised exact whole-payload change list can be incomplete. Compare scalar type as well as value when deriving the contract path set.

Classification: P3 sensitivity-provenance correctness. It does not block numeric Cg calculation, but it blocks relying on `changed_input_paths` as an exact whole-payload audit for this input pattern. This is limited defensive hardening unless callers use the list to enforce the complete scenario contract.

This is also inherited from attempt04, not introduced by attempt05.

## Correctness notes

The attempt05 patch itself correctly avoids overflow in direction normalization: for every finite nonzero three-component vector, scaling by its largest absolute component leaves components in `[-1, 1]`, after which the norm is bounded between 1 and `sqrt(3)`. The newly added overflow-vector cases reach the expected fail-closed direction checks by static control-flow analysis. The geometry path rejects non-finite derived coordinates, enforces a single straight uniform-pitch row, and accepts antiparallel load/row directions through the cross-product alignment check. The equation path uses the expected wood-to-wood dowel gamma, `D < 1/4 in` exception, EA ratio, and method factor form; its extreme-intermediate and result checks return pending. This form is consistent with the cited AWC Chapter 11 presentation of the method, while that 2018 excerpt alone does not independently authenticate the 2024 edition text ([AWC NDS-2018 Chapter 11 excerpt](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Chapter11.pdf)).

Successful output remains bounded to `calculated_method_only` / `calculated_method_sensitivity_only`: capacity is `None` and criterion disposition is `pending`. The attempt05 focused-test result recorded in its validation artifact was not rerun as part of this read-only review.
