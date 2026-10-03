# STI17 source correctness review

Target: `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/sti17-source-review-pass3/source-review-target.json`

Target SHA-256: `008ba73850288a620561a26558001f913079a7e904b85d029d16e07b1dd0fcf7`

Input integrity: all 15 declared SHA-256 and byte-size pairs matched before source inspection.

## Finding

**Medium — final-review gate permits target/report alias.** At `build_sti17.py:123`, `validate_review_binding()` requires distinct paths and digests among the three review records, but excludes the target record from those uniqueness checks. A review role can point to the target JSON and reuse its digest while validation succeeds; the freezer then deduplicates that path in its input set. This can count the manifest as an independent review and weaken the required three-review gate. Enforce distinct resolved paths and digests across the target plus all three reports; add a regression test for target-path and target-digest aliases.

No other substantial in-scope source defect found.

## Limits

Source-only review. No Docker, build, solver, mesh, CAD, native-output, freeze, ledger, Git, or test action performed. Parent-reported 27 tests / 48 subtests and Ruff results were not rerun.

Base-image timeout known-answer does not qualify final STI17 image. STI17 build and coupon remain unperformed. Source readiness is not runtime or mechanical acceptance.
