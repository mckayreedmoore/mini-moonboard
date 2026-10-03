# STI17 source correctness review

Review target: `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/sti17-source-review-pass2/source-review-target.json`

Target SHA-256: `c20fba495d8d025933aa6e2551367df9e570943d1cdc96a98b51bfb6674c3570`

Pin authentication: all 15 target inputs match declared SHA-256 and byte size.

Reviewed AGENTS.md, packet README, parent-validation handoff, pinned implementation and test sources, shared runner, and free-C3D20 oracle. Parent reports 26 tests / 47 subtests and Ruff passed; I did not rerun checks.

## Findings

1. **[P1] Revalidate the exact review before reserving the coupon.** `launch_sti17_coupon.py:91-97` reads and approves the review before image inspection and binary preflight (`:99-132`). After acquiring the ledger lock, it rechecks the freeze (`:170-172`) but does not re-read or revalidate the review; authorization hashes whatever currently occupies the path (`:179-180`). If the review changes during preflight, the launcher can consume the one-shot slot using the earlier in-memory approval while recording a different review hash. The post-run checker loads and validates that changed review only after execution (`check_sti17_coupon.py:404-407, 338-341`), so it can reject the result after the coupon is spent. Under the lock, read one review byte snapshot, verify its hash and approval fields against the exact freeze, and record that same digest and content. Add a test that changes the review during preflight and confirms refusal before reservation.

2. **[P2] Cap total memory plus swap for coupon execution.** `launch_sti17_coupon.py:134-159` sets `--memory=2g` but omits `--memory-swap`; `check_sti17_coupon.py:198-226` accepts that command as the fixed invocation. Docker documents that when `--memory-swap` is unset, a container can use swap equal to its memory limit, for up to 4 GiB combined when host swap is available ([Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)). This differs from the stated 2 GiB coupon limit and from the build and base-image known-answer commands, which set memory and swap equal. Add `--memory-swap=2g` to the launcher and checker expectation, then cover it in the command test.

3. **[P2] Require three distinct source-review records.** `freeze_sti17_build_inputs.py:153-161` checks only that the map has the three required keys. `build_sti17.py:114-120` repeats that key check but does not require distinct review paths or hashes. The same file can therefore fill correctness, testing, and architecture slots and still pass freeze validation, despite the README requiring three independent reviews. Reject duplicate report paths and hashes; record and validate distinct reviewer identities or dispositions so the bound freeze proves three separate reviews.

## Scope limits

Source-only review. No Docker, build, solver, CAD, mesh, native-output, freeze, ledger mutation, Git action, or target-input edit was performed. Existing base-image timeout known-answer is reported passed; final STI17 image, isolated build, and coupon remain unexecuted. This review does not establish runtime behavior, engineering acceptance, candidate export, fabrication readiness, or climbing release. Parent retains readiness, source freeze, serialized heavy execution, and final validation.
