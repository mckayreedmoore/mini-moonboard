# Independent testing review: stress provenance checker

## Pin verification

Target: `source-review-target.json` SHA-256 `e27297f27f2e1941c75adf571d482eeb8605c063c673bcc37c7af60168277226`.

Authenticated all eight listed files by SHA-256 and byte size before inspecting any of them. Every value matched the target manifest.

| File | SHA-256 | Bytes |
|---|---|---:|
| `docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-provenance-preparation-2026-10-01/check_provenance.py` | `6791c0c12a845a1b60d46a840a137b8c8827de1940e2436b2cbde5b452ebfb32` | 11876 |
| `docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-provenance-preparation-2026-10-01/test_provenance.py` | `3de48b526d10e055752276bf898f8f6242683a178f7fca5314678059bf248f78` | 11661 |
| `docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-provenance-preparation-2026-10-01/README.md` | `cfdb2ea8e5212c483dc051ae2e3dbc3b9727c3e3609eb92c8d637043fa09c8da` | 2401 |
| `docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/prepare.py` | `2a59e0700c7701022ecfeea4a77d47864c934df75dcf4fec7c480a6854de9821` | 6019 |
| `docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/check_output.py` | `5d084afe311a1b836d1205240c063d9362554b73170d18adf86864dd03d4966c` | 5336 |
| `docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/orthotropic-stress-frame-parent-oracle.json` | `1e82a2869b3609558024a3299363859f88e9d62c5770bacb26f92b4dfce5f5ff` | 1893 |
| `fea/wood_joint_reduced_native.py` | `ff7a81bc604090a4791eb584f9998bc76a35be2ac3ebaed15be970291583ff61` | 10602 |
| `fea/calculix_223/solver-profile.json` | `f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c` | 966 |

## Review result

No substantial concrete checker, synthetic-coverage, or checker-contract findings.

Static review confirms checker requires caller-supplied exact freeze SHA; native verifier checks frozen snapshots against live sources; producer reconstructs deck and expectation; stock profile is pinned; authorization and independent review bind the freeze; execution must be successful and terminal; matching ledger run ID must be unique and consumed; command resources, absolute KILL utility path and recorded utility identity are fixed; captured `model.*` / `native.*` file inventory and hashes must match; then unchanged pure numerical reader checks the DAT.

Parent reports 22 synthetic tests and Ruff pass. I did not run tests or Ruff, per review limits. Preparation, output reader, and analytical oracle matched their input pins. No source code was executed and no numerical checks were run.

## Limits

Source-only review. No production freeze or native run exists. Production freezer and scoped launcher remain pending and outside this checker-only review; their absence is not a finding. This review does not establish native readiness, host execution, or mechanical acceptance.
