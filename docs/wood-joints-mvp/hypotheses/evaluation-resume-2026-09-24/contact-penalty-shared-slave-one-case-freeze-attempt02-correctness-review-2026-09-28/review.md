# Attempt02 correctness review

Reviewed: 2026-09-28 06:20 UTC  
Target: `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/contact-penalty-shared-slave-one-case-freeze-attempt02/`  
Bound freeze SHA-256: `5bc91ad9f4ef2027609263752fd0d6e68f29284acd3f40e2f8bd541579c5499f`

## Result

The candidate's frozen inputs, one-case scope, authorization transition, runner gate ordering, and deck audit are internally consistent. I found no defect that prevents the runner from stopping before Docker unless the exact freeze and a matching external authorization are supplied. Readiness remains false, and no execution output is present.

One assurance limitation remains in the standalone verifier: its coupon-pass result does not independently establish that the recorded native run used an authorized external parent decision. This does not bypass the runner's pre-Docker gate, and the verifier keeps mechanical/joint acceptance and release false. Treat its pass as an output audit unless the runner's execution record and external authorization are separately trusted.

## Findings

### A-1 — Verifier does not bind its pass to the external authorization record

**Severity:** Low; evidence-chain limitation, not a demonstrated runner-gate bypass.

`run.py` validates the authorization fields and their freeze/readiness hashes before the first Docker call, then stores only `external_authorization_sha256` in the execution records (`run.py:346-364`, `455-487`). `verifier.py` checks the output evidence and frozen input hashes, but it never reads or validates that authorization digest, the recorded readiness digests, or an external authorization file (`verifier.py:1120-1207`). An output audit therefore cannot itself establish that the external decision was present and matched when the native run began.

The current wording is bounded: verifier status is `PASS_SHARED_SLAVE_PENALTY_COUPON`, and all mechanical/joint acceptance and release fields remain false. Keep the pass scoped to output evidence, or extend a later verifier contract to bind the execution record to the exact external authorization and frozen readiness hashes. I did not create an authorization record or readiness-true file.

## Checks performed

- Recomputed all ten `input-freeze.json` file hashes and matched them to the frozen inventory. The freeze hash and `validation.json` hash also match `terminal-hashes.json`.
- Recomputed the selected input, upstream expected-contract, and projection-parent oracle hashes from their referenced data files. The one-case candidate retains the parent oracle's `shared_slave_penalty` case and shared load/reaction oracle; its projection removes the second case's diagnostics and updates the scope description.
- Compared the external-authorization schema's required/property names with `run.py`'s exact field set. They match. Runtime checks additionally require the two authorization gates to be true, the acceptance/execution/release claims false, and a UTC timestamp.
- Traced `run()` ordering: exact freeze validation, external-record loading, and readiness/authorization checks all precede the first subprocess call (`run.py:346-364`). The runner verifies the copied deck hash before launch and checks frozen files again when recording completion.
- Ran the verifier's pure `audit_deck()` check on the frozen deck: **PASS** (81 nodes, 18 C3D10 elements, two consistently typed surface-to-surface pairs, shared slave labels `[1, 4, 24]`, no slave/SPC overlap).
- Confirmed the false readiness gates remain false and `execution.json`/`output/` do not exist. No unit-test suite, Docker command, solver, or native solve was run.

The route-review parent reference is a prior report and was not opened or re-hashed under the review instruction. Its digest is consistent between the target snapshot and runner constant; independent byte-level confirmation of that one lineage pin is therefore outside this report's evidence.

This review concerns packet correctness only. It does not establish solver convergence, mechanics acceptance, joint capacity, fabrication readiness, or release.
