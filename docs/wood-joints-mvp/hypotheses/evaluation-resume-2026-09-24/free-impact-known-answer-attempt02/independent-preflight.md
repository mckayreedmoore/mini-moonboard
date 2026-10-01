# Independent preflight: law-code correction

## Review result

The attempt02 correction is narrowly justified. Parsed JSON comparison against attempt01 shows exactly one acceptance-contract change: `trace_contract.map_pressure_law`, from `1` to `2`. The verifier's only executable change is its synthetic MAP fixture law token changing from `1` to `2`; native parsing and arithmetic gates are unchanged. JSON formatting in `acceptance.json` differs, but its semantic diff contains no other changed field. The input, expected contract, producer, geometry/design, and input audit are byte-identical to attempt01.

This matches the pinned CalculiX source and the actual attempt01 input/output: `PRESSURE-OVERCLOSURE=LINEAR` stores `elcon(3,1,imat)=2.5d0`, and the captured MAP field is produced as `int(elcon(3,1,imat))`, hence `2`. The contact-pair setting `TYPE=SURFACE TO SURFACE` maps to separate `mortar=1`; it is not the pressure-law code. Attempt01's original frozen result remains FAIL and is explicitly recorded in `correction.json` as the reason for this new attempt.

## Reproduction and lineage

Offline checks completed without a native run:

- `python3 prepare.py --check` passed and reproduced input SHA-256 `2b253f63f9e8cee1bcb471ba3fb6b8150e72df781432bcfe6a1019e66d44caea` with 70 reference states.
- `python3 verifier.py --self-test` passed all synthetic positive and negative controls; it reported `native_run_performed: false`.
- The attempt01 source archive SHA-256 is `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; `surfacebehaviors.f` member SHA-256 is `f0088a364b9b069aa10be9c4b4f38d72df875295f339830d7e2df6762ad9e161`.
- Attempt02 `correction.json` SHA-256 is `3bd2b5c29cb7f3186143ee1a36b5835487ac2274f05f6d4c677dd287f10bb5f3`; it identifies attempt01 and records the law-code correction. The runner's external dependency inventory will bind attempt01's prior freeze (`534d22546dc808e97fedd0c3ac82b77aec8ff4f4230a5e64de471c57ff245637`), execution record (`dbeff556550e51c485da9dc778afb6f003a9d59f2dc8aefb3c4c7ed5422bff17`), original FAIL (`7632ca5f04e4d91feb55f1f5c6e3f92a021da97709470da7b26d0314121a11c4`), and independent source diagnosis (`independent-postrun.md`, SHA-256 `892a3592e3a8300b03daeba2a80d91426f5ea628e1345fd67feb252eeda8c288`) at freeze time.

Attempt02 runner adds `correction.json` to its local freeze inventory and pins the prior freeze, execution record, verifier result, and independent post-run note as dependencies. The pinned input, reference, numerical tolerances, solver/image pins, and serial case order remain unchanged. At this review, attempt02 has no `input-freeze.json`, `output/`, or `parent-review.json`; no freeze or native execution was performed. Parent readiness and freeze remain outstanding.

This review is limited to the law-code correction and packet lineage. A fresh attempt02 capture still must pass the unchanged numerical and trace gates; neither this preflight nor the prior fixture establishes joint acceptance or release.
