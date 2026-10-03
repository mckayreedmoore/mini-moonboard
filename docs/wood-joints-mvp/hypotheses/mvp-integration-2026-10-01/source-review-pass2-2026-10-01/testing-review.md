# Independent testing review

Target SHA-256: `02452912a8882bff4fbca15ee347d539a51c3bf827b3ac27154a6b763dd3b650`  
Scope: static testing review of the pinned STI17 build/free-coupon preparation and orthotropic stress-frame preparation for `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`. All 47 formal criteria remain pending.

## Findings

1. **The stress-frame happy-path fixture can repeat a mislabeled expected tensor.** In `docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/test_output.py:23-40`, the fixture takes `expected` from `prepare.prepare()` and uses those same values to synthesize each labeled stress block; `check_output.check()` then compares against that same object. The independent calculation in `test_constitutive_answer.py:82-90` validates the parent oracle, but never checks that `prepare.prepare()` assigns its global and local expected fields to the matching oracle keys. If those two fields are swapped in the producer, the fixture and checker can agree on the wrong `SGLOBAL`/`SLOCAL`/`SDEFAULT` values while the independent oracle test still passes. `test_prepare.py:32-40` checks the deck keywords and that the tensors differ, not their label-to-value assignment. Add an assertion binding each `prepare()` expected field to the independently calculated global/local answer, and build the synthetic blocks from that independently labeled answer.

2. **The coupon-readiness negative case does not test the image pins named by the test.** `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_sti17_preparation.py:187-218` validates a matching readiness packet and then mutates only `build_receipt_sha256`; it never changes `image_id` or `image_receipt_sha256`. The production helper checks all three bindings in `prepare_sti17_coupon.py:92-100`, but a regression dropping either exact image check would pass the present suite. A freeze could then accept readiness that does not approve the image being prepared. Add separate rejection cases for a changed image ID and image-receipt digest.

3. **The recorded-output hash test compares a mapping with itself.** `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_sti17_preparation.py:419-428` passes `bundle["execution"]["outputs_sha256"]` as both the recorded and observed hashes to `CHECK.validate_recorded_outputs()`. This only exercises the passing case; removing or weakening the comparison in `check_sti17_coupon.py:343-349` would leave the test green. Since the post-run receipt relies on matching observed `.sti`, `.mas`, and `.dof` hashes to the runner record, add synthetic mismatch and missing-recorded-hash cases.

## Checks and limits

- The required included-usage check (`python3 /tmp/mini-moonboard-included-usage-check.py`) reported 98% used, no reached limit, and ordinary usage allowed.
- Verified the target JSON SHA-256 against the supplied pin.
- Read the pinned source, test, README, and listed metadata/oracle artifacts for static coverage and assertion review. The recorded 15 STI17 tests/Ruff and 17 stress-frame tests/Ruff are supplied results; I did not rerun them.
- No Docker, native solver, CAD, build, freeze, ledger mutation, solver-output read, code edit, or Git operation was performed.
- I mistakenly started an additional Luna child before recognizing that this assignment itself designated the sole Luna/max reviewer. The parent interrupted it. I did not read or use any findings from that child.

Status: source-only testing review complete with three substantial coverage findings. No candidate acceptance or criteria pass is implied.
