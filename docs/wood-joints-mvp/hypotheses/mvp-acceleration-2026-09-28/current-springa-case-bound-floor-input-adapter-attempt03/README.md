# K12-rear 16-cell selected-floor input proposal

k12-rear/ is an input-only proposal produced by the immutable
current-springa-case-bound-floor-input-adapter-attempt02/prepare.py API, using
the case-bound K12-rear screen projection in sibling
current-springa-k12-rear-zero-u-token-screen-attempt02/. The proposed mask has
16 cells (32 active tangent rows) and 84 inactive cells (168 tangent rows
without restraint). The selected transform has rank 32.

The input adapter reports
PASS_SELECTED_FLOOR_INPUT_ALGEBRA_AND_SOURCE_PRESERVATION. The pinned full
input-context check in k12-rear/input_contract_check.json reports
PASS_CASE_BOUND_SELECTED_FLOOR_INPUT_CONTRACT_ONLY; it uses the immutable
case-bound validator source SHA-256
df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479.
Source carrier inventory is preserved: 1,840 total rows, 1,292 SPRINGA
carriers, 348 bilateral SPRING2 rows, 92 new candidate bolt axes, 12 retained
LEG/FLOOR-RUNNER bolt axes, and 66 panel-screw axes. The constraint, reference,
pivot, physical wrench, and load-correction errors all remain below their
pinned tolerances.

prepare_k12_rear.py pins each input and invokes the attempt02 adapter without
modifying it. validate_k12_rear_input_context.py reruns the read-only source
context and model contract checks. The output contains no freeze, execution
record, DAT, or FRD. The proposal is not a native run, accepted support state,
physical response, corner demand, floor qualification, stability result, or
joint acceptance. The diagnostic forces that defined the mask are not reused
as response.
