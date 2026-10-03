# Architecture review: stress-frame provenance checker

## Input authentication

Reviewed target manifest SHA-256: `e27297f27f2e1941c75adf571d482eeb8605c063c673bcc37c7af60168277226`.

The supplied target hash matched. Before source inspection, all eight manifest-pinned files matched both their listed SHA-256 and byte size. Inputs: `check_provenance.py`, `test_provenance.py`, its README, `prepare.py`, `check_output.py`, the parent oracle, `fea/wood_joint_reduced_native.py`, and `fea/calculix_223/solver-profile.json`.

## Findings

1. **Medium — cached verifier can bypass frozen/live source verification.** [`check_provenance.py`](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-provenance-preparation-2026-10-01/check_provenance.py:164) prepends the repository to `sys.path`, then imports `verify` by module name. Python reuses `sys.modules` entries, so an in-process caller that already loaded `fea.wood_joint_reduced_native` can execute a stale or differently rooted verifier. That verifier supplies the snapshot/live hash checks on which the checker relies. The documented fresh CLI normally avoids this case; direct use in a long-lived coordinator process does not. Load the verifier from the pinned file path under a unique module name, or verify the snapshot/live pairs directly without relying on the import cache. Add a regression that preloads a stale verifier module.

2. **Low — frozen-source snapshot tampering lacks a negative test.** [`test_provenance.py`](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-provenance-preparation-2026-10-01/test_provenance.py:203) mutates a live source, but none of the 22 reported synthetic tests mutates a file under `sources/` while leaving its live counterpart unchanged. The suite therefore does not independently exercise the frozen half of the required frozen/live source check. Add a case that alters one snapshot and expects refusal.

## Contract and limits

Static review confirms gates for caller-supplied exact freeze SHA, required source set and reconstruction, pinned profile, exact-freeze review and authorization links, successful terminal execution, one matching ledger row, exact resource command and timeout identity record, captured output inventory/hashes, and invocation of the unchanged numerical reader. Finding 1 qualifies the source-verification guarantee for in-process use.

Parent reports 22 synthetic tests and Ruff pass; neither was rerun. No source files or tests were changed. No native, Docker, solver, CAD, mesh, freeze, shared-ledger, or Git action was performed. Production freezer and scoped launcher remain pending and are outside this checker-only review. No actual production freeze/run has happened; this review does not declare native readiness. No hostile-host attestation prerequisite was assessed or added.
