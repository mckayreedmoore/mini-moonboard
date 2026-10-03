# Refined connector compliance reduction, attempt 02

This parent-owned attempt preserves the original exported stiffness and all
raw body force/moment maps. It uses the separately verified, five-correction
refinement wrapper with the same numerical gates. It changes no geometry,
contact law, physical support, or load. It is an elastic basis calculation,
not a physical frame response or a native solve.

The exact panel chunk rejected in attempt 01 passed after one correction in
the [parent diagnostic](../current-bordered-refinement-parent-case-attempt01/refinement-result.json).
Its extended force residual decreased from 3.0092e-10 to 3.8855e-11 against
the unchanged 1e-10 gate. The cube and explicit nonfinite, stagnation, and
five-correction stop fixtures replayed before this attempt.

This attempt completed the four panel bodies, then stopped at `kicker_left`,
interface columns 16–31, after 17.827 seconds. Refinement reduced the force
residual below 1e-10 and the gauge displacement below 2e-10 mm, but the
gauge multiplier stabilized at approximately 1.6435e-9 N against the
unchanged 2e-10 N limit. The fourth correction did not improve backward
error sufficiently, so the wrapper returned `UNRESOLVED_REFINEMENT_STAGNATION`.
The attempt status is `STOP_CONNECTOR_COMPLIANCE_NUMERICAL_GATE`.

No complete `H`, physical force, contact state, or fourth usable case was
accepted. The next bounded task is to inspect the stopped chunk's original
operator rigid-mode leakage and multiplier identity before choosing another
method. More identical refinements or a threshold change are not a remedy.
Raw stiffness, failed records, and earlier evidence remain immutable.

The run used the shared native-ledger lock, checked its idle slot, and imposed
single-threaded BLAS, 300-second and 6-GiB limits. It consumed no native
launch. `inputs.json`, copied Python sources, `assessment.json`, and
`output-pin.json` authenticate the attempt. Replaying provenance does not
repeat the reduction:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt02/build_compliance.py --verify-record
```
