# Independent testing review: STI17 and stress-frame preparation

Scope: source and synthetic-test review of the two preparation packets. This review makes no joint-capacity or candidate-acceptance claim. The STI17 unit suite was run from a temporary copy under `/tmp` and passed 11/11. The stress-frame pytest suite was inspected but could not be replayed because `pytest` is not installed here; Ruff is also unavailable. No packet producer, build, compiler, Docker, CAD, mesh, native solver, ledger, readiness, or freeze operation was run.

## Findings

### P1 — STI17 post-run checker does not close the runner provenance chain

`check_sti17_coupon.py:69-103` accepts authorization and execution records using their local fields: scope, freeze digest, booleans, matching run ID, terminal flag, and return code. It does not compare the recorded command in authorization and execution, bind that command to the STI17 image, binary, CPU, memory and timeout, or validate the run row and its stored hashes in `luna-max-native-run-ledger.json`. The stock runner writes those authorization and execution hashes into its ledger at `fea/wood_joint_reduced_native.py:154-200`, but the checker never reads that ledger. It only compares output files with hashes copied into the local execution JSON at `check_sti17_coupon.py:106-112`.

The current test at `test_sti17_preparation.py:291-345` uses a generic `pinned-image` command and only corrupts the run ID. It therefore passes without showing that the checker rejects a mismatched command, image, limit, authorization hash, or ledger row. A locally fabricated or mixed set of success records and matching output hashes can satisfy the checker without proving they came from the one bounded invocation described in the README.

Fix the checker to require the unique ledger row for this run to be `consumed_terminal`, match its attempt path, scope and freeze digest, and match its authorization and execution record hashes to the files being checked. Also require authorization and execution commands to match and enforce the expected image, binary and resource limits. Add negative tests for each broken link and for altered command/image/limits. This is a method-result provenance blocker; it does not affect the current source-only status.

### P2 — Stress-frame synthetic tests reuse the expected stress tensors as their answer

`test_output.py:35-58` creates every synthetic stress row directly from the tensors returned by `prepare.prepare()`. `check_output.py:78-103` then compares those rows to the same expected tensors. `test_prepare.py:32-40` checks that the two tensors differ and checks one energy scalar, but does not independently compute stress from the pinned engineering constants, global strain and material axes or check the local-to-global tensor transform.

Consequently, the pure suite does not independently validate the tensor values: an incorrect but pinned oracle pair would be echoed into the synthetic output and accepted by the reader. The suite demonstrates row census, frame-tag, tolerance and corruption handling, but does not validate the orthotropic known answer itself. Add an independent pure calculation for the reciprocal compliance/stiffness response and `Q σ_local Qᵀ = σ_global`, with checks against both tensors and the strain-energy density. Keep the native frame-selection check separate, since only a solver run can establish that CalculiX emits the requested frames as documented.

## Verification notes

The STI17 11-test suite passed from a temporary source copy. The stress-frame producer and tests were inspected without invoking `prepare.py`; its 16 pytest cases were not replayed because pytest is unavailable. Both READMEs were read as the packet contracts. All 47 formal criteria remain pending, and the orthotropic packet's parent provenance wrapper and native readiness remain unfinished as its README states.
