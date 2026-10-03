# Independent source review: STI17 build and free C3D20 coupon

Review date: October 1, 2026

## Scope and result

Reviewed the pinned source for the isolated STI17 build, separate free C3D20 coupon freeze, hard-stop launcher, post-run checker, shared native runner, and the listed input-pin records. This was a source-only audit. No tests, Docker commands, builds, solver runs, CAD, mesh, freeze, ledger mutation, Git action, or native solver output reads were performed.

The target files authenticated without drift. The source has two substantial findings below. The manual hash mismatch blocks coupon preparation. The hard-stop launcher does not bind the `timeout` executable to the utility exercised by the known-answer receipt. Source readiness should remain false until both source issues are fixed and independently reviewed. The final STI17 image does not exist, so this review makes no runtime qualification claim.

## Target and input-pin authentication

Target file: `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/sti17-source-review-pass1/source-review-target.json`

Target SHA-256: `8bec53f223af3d770ea8df541d2b0cb47eeac89fee721103ae046ca55703f7e8`

All 15 target entries matched both the listed SHA-256 and byte size. The hash shown below is the expected and observed value for each file.

| Target file | SHA-256 |
| --- | --- |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/README.md` | `aba611aa95af76fec91c2c3338665293e1d65887138578a6ae921df705ed3837` |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/build_sti17.py` | `f93a855b858ec2ad359d6086194237b36db1da70bac217be0176b6e72c65c4f4` |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/check_sti17_coupon.py` | `3a5518cd86c50d4f9524e0ffd07cfbd80d335f130b4372b0d3609ce5afa1e352` |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/freeze_sti17_build_inputs.py` | `ea266375fac4a0af7a27aae3d55714385786b55cd65606d245a88f389ef9a88d` |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/launch_sti17_coupon.py` | `26c1e7606152423741c221d2958189db67cef2e3d7533e23d93009f8329a3d53` |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/pin-receipt.json` | `832422fec1a4f12f68d46eeeacfafad6a088d07aac0d064f059a1676f96f94b3` |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/prepare_sti17_coupon.py` | `aafdb49edbc20f4bc28020b4fe76aaf0831645f9d5299c6f6cf5ba7f5d825a17` |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_hard_stop_launcher.py` | `10673dc205b1d4d2cb18289d71f7e39dafd04ebf4f139e5012409f17ee0704a4` |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_sti17_preparation.py` | `2d3b087ab573c590169c685e0bf64339058b5e4d20d8f3bf75049be87dd6db67` |
| `fea/wood_joint_reduced_native.py` | `ff7a81bc604090a4791eb584f9998bc76a35be2ac3ebaed15be970291583ff61` |
| `fea/calculix_223/solver-profile.json` | `f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c` |
| `fea/calculix_223/Makefile.upstream` | `57a25e08a51bba3897cecb3c03e45f7cf602d9c28a15c12e45d9b1ddebcad0bf` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-native-elastic-operator-export-preflight-attempt01/matrix_export_oracle.py` | `17a908d1283f676df7af97511ef2ecd3c794b98c6b81dc50e2a6f14cec57b79a` |
| `docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-next-method-parent-validation.json` | `5cae8f60ce6f9af80ffd9049fb0643e7cfa44e01cddecf6799fe6f5ee12e87b2` |
| `docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/sti17-base-image-hard-stop-known-answer.json` | `133ea2c7bef6f4090d3b4016652301fe51a8134eebdd75ba28074dd13abee1d7` |

Cross-pin checks matched for the parent validation, precision preflight source pins and patch, base solver profile, base build manifest and result, free C3D20 deck, and matrix oracle. The separate manual dependency has a source-literal mismatch; see finding 1.

## Findings

### 1. High — Coupon preparation rejects the currently pinned solver manual

[`prepare_sti17_coupon.py:187`](../../ccx223-sti17-build-coupon-preparation-2026-10-01/prepare_sti17_coupon.py:187) compares the local manual against `a0bf3fc03f374912eb2f28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`. The current manual hashes to `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`, which is also the manual hash in the authenticated base solver profile. Therefore the current preparation script raises `pinned 2.23 manual changed` and cannot create the coupon freeze, even with otherwise valid build and image receipts.

Fix the duplicated expected hash to match the authenticated profile/manual pin, or derive the expected value from the already hash-pinned base profile. Add a regression test for this relationship, then refresh the source target and obtain a fresh review.

### 2. Medium — Hard-stop command does not bind the tested timeout executable

[`launch_sti17_coupon.py:122`](../../ccx223-sti17-build-coupon-preparation-2026-10-01/launch_sti17_coupon.py:122) invokes bare `timeout`. The checker at [`check_sti17_coupon.py:214`](../../ccx223-sti17-build-coupon-preparation-2026-10-01/check_sti17_coupon.py:214) likewise accepts the bare command name. The known-answer receipt records `/usr/bin/timeout`, GNU coreutils 9.4, SHA-256 `4fccd5b0192653a2446b745d5385ea547b78e466150e07ade9e2caff2b7f4e08`; neither launcher nor checker proves PATH resolves to that executable in the final STI17 image. A different executable earlier on PATH could change the forced-kill behavior while the command check still passes.

Invoke `/usr/bin/timeout` explicitly. After the isolated build, verify that exact utility's identity in the final image, record the observed path/hash/version in the image or coupon provenance, and require the checker to match the recorded identity and absolute command path. Final-image qualification remains pending as stated in the handoff; this finding does not assert that the not-yet-built image contains a different utility.

## Limits

The handoff reports 20 tests / 42 subtests and Ruff passing; those checks were not rerun for this review. No build or coupon image exists yet. The base-image timeout known-answer is not qualification of the final STI17 image. No solver output, candidate export, native run, mechanical acceptance, or criterion disposition was assessed. All 47 criteria remain pending; historical failures and STOP remain unchanged.
