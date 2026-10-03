# STI17 source correctness review

## Scope and disposition

Independent static source audit of the isolated STI17 build and free C3D20 coupon path. The reviewed target is `source-review-target.json`, SHA-256 `8bec53f223af3d770ea8df541d2b0cb47eeac89fee721103ae046ca55703f7e8`. All 15 listed files matched both their target SHA-256 and byte size before review. No target drift found.

Two launch-boundary defects remain. The source is not launch-ready until both are fixed and reviewed. This report does not change candidate geometry, historical failures, or the 47 pending criteria.

## Findings

### 1. High — launcher does not enforce the fixed coupon payload before execution

`docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/launch_sti17_coupon.py:31-50,56-128` checks the freeze's scope string and selected profile fields, then runs the supplied directory's `model.inp`. It does not require the designated attempt directory or compare the model deck hash and model record to the prepared free-C3D20 coupon. The stock `verify()` only checks each file against the hash self-declared in `freeze.json`; a relabeled freeze can update that hash and receive a matching review. The checker compares the deck with the known coupon hash only after execution (`check_sti17_coupon.py:368-371`). Thus a different deck can reach CalculiX before the post-run checker rejects it, and a copied freeze can mount a different output directory.

**Fix:** Before any Docker command, require the canonical `sti17-free-c3d20-coupon-freeze-attempt01` directory and enforce the expected coupon deck SHA-256 `e128a62f899c90965fd68be09a7362ed836a30ff6b1c3f1c6dc0581e118b79fe`. Also validate the expected model-record content/hash and required scope flags at launch. Keep the post-run checks as defense in depth.

### 2. Medium — hard-stop executable identity is not bound to the invocation

`launch_sti17_coupon.py:122-125` invokes bare `timeout`, resolved through the container's `PATH`. The pinned base-image known-answer receipt exercised `/usr/bin/timeout` and records its SHA-256 as `4fccd5b0192653a2446b745d5385ea547b78e466150e07ade9e2caff2b7f4e08`, but the launcher neither names that absolute path nor checks the timeout binary's identity. Its 60-second KILL guarantee therefore depends on an unrecorded executable resolution.

**Fix:** Invoke `/usr/bin/timeout` explicitly. In the image preflight, verify and record its expected hash (and version) before reserving the run; retain the final-image known-answer check against that exact utility and invocation.

## Input-pin verification

Target SHA-256: `8bec53f223af3d770ea8df541d2b0cb47eeac89fee721103ae046ca55703f7e8`.

All entries below matched the target's SHA-256 and `size_bytes`:

| Target file | SHA-256 |
|---|---|
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
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-native-elastic-operator-export-preflight-attempt01/matrix_export_oracle.py` | `17a908d1283f676df7af97511ef2ecd3c794b8c6b81dc50e2a6f14cec57b79a` |
| `docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-next-method-parent-validation.json` | `5cae8f60ce6f9af80ffd9049fb0643e7cfa44e01cddecf6799fe6f5ee12e87b2` |
| `docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/sti17-base-image-hard-stop-known-answer.json` | `133ea2c7bef6f4090d3b4016652301fe51a8134eebdd75ba28074dd13abee1d7` |

## Limits

This was source review only. No tests or Ruff checks were run. No Docker, build, solver, CAD, mesh, freeze, native-output read, ledger mutation, or Git action was performed. The source archive remains preserved.

The immutable base-image known-answer passed for `/usr/bin/timeout`; it does not qualify the not-yet-built STI17 image. Recheck the final image's utility identity and exact invocation, then perform its bounded known-answer qualification. Source review establishes no candidate export, force resolution, joint acceptance, or mechanical result. All 47 formal criteria remain pending.
