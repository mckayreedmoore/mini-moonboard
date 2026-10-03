# STI17 build and free-C3D20 coupon: architecture review

## Review basis

Reviewed the isolated STI17 build, coupon preparation, hard-stop launcher, result checker, shared native runner, and free-C3D20 oracle as source only. Read `AGENTS.md`, the packet README, and the parent handoff scope. The handoff remains `PASS_SOURCE_ONLY_METHOD_CHECKS_RF_MISS_RETAINED`: build/native readiness is false, candidate export is unauthorized, 47 formal criteria remain pending, and the original raw-H27 STOP remains retained.

The review target was authenticated before source review:

- `source-review-target.json` SHA-256: `c20fba495d8d025933aa6e2551367df9e570943d1cdc96a98b51bfb6674c3570` (matches requested digest).
- All 15 manifest inputs matched both their listed SHA-256 and byte size.

| Input | SHA-256 | Bytes |
|---|---|---:|
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/README.md` | `8d79931b9147fbbfe47de4092f8a774027d0b69f0bb0d1c3aef60b571b7bb3dc` | 12914 |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/build_sti17.py` | `88e3a02da2485f51ec05c759a12e0ab62e0496ef595326be7e8a74c4c58af63a` | 31495 |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/check_sti17_coupon.py` | `1adf83f73795e1a10b612b90f315f2bafa7456b56386e59e3dd0361838ab55c3` | 16743 |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/freeze_sti17_build_inputs.py` | `3b7db599f370a1d2467d1aa81693ed1af9806b3b581211fe99e59208bb3a2e2e` | 9033 |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/launch_sti17_coupon.py` | `2dc383ce1f1b0adab7b97f7a8880726318967a2a9936ea350b566c18d9457b46` | 11516 |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/pin-receipt.json` | `832422fec1a4f12f68d46eeeacfafad6a088d07aac0d064f059a1676f96f94b3` | 7563 |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/prepare_sti17_coupon.py` | `01c8bcc344597150ba0820053e0a68b03948aea6721357ae8cebf4b4d9e72fad` | 13963 |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_hard_stop_launcher.py` | `8342d6896ad3a7b7ab0ecad68c2030d102f5d8db8ca3e8e1a23eac35bdfa2898` | 10940 |
| `docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/test_sti17_preparation.py` | `d1fb56402014f2488d6a56f3bb9ce1637e182f0282dd82a13aad512fb5a580c1` | 30273 |
| `fea/wood_joint_reduced_native.py` | `ff7a81bc604090a4791eb584f9998bc76a35be2ac3ebaed15be970291583ff61` | 10602 |
| `fea/calculix_223/solver-profile.json` | `f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c` | 966 |
| `fea/calculix_223/Makefile.upstream` | `57a25e08a51bba3897cecb3c03e45f7cf602d9c28a15c12e45d9b1ddebcad0bf` | 588 |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-native-elastic-operator-export-preflight-attempt01/matrix_export_oracle.py` | `17a908d1283f676df7af97511ef2ecd3c794b98c6b81dc50e2a6f14cec57b79a` | 7270 |
| `docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-next-method-parent-validation.json` | `5cae8f60ce6f9af80ffd9049fb0643e7cfa44e01cddecf6799fe6f5ee12e87b2` | 4035 |
| `docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/sti17-base-image-hard-stop-known-answer.json` | `133ea2c7bef6f4090d3b4016652301fe51a8134eebdd75ba28074dd13abee1d7` | 5410 |

## Findings

No substantial in-scope architecture, behavior, or source-coverage defect found. No severity-ranked findings; no fixes proposed.

The source chain is coherent for its bounded purpose: the build checks fresh readiness and frozen pins, applies one exact stiffness-format token change, constrains the compile/archive/link plan, and records source/object/library identities. Coupon preparation binds the resulting image and binary receipts, exact deck and oracle, and launch/check sources. The launcher checks the canonical freeze and exact coupon, verifies image binary and timeout utility hashes, fixes CPU/memory/network limits and a 60-second KILL timeout, mounts the deck read-only, and consumes the shared single-run ledger slot. The checker revalidates the freeze, review, command, terminal ledger records, and output hashes before applying formatting and free-coupon oracle checks.

## Limits

This is a static source review. Parent reports 26 tests / 47 subtests and Ruff passed; those checks were not rerun here. No Docker command, image build, solver, CAD/mesh operation, native output read, freeze creation, ledger mutation, or Git action was performed. The base-image timeout known-answer is existing evidence only; the final STI17 image and coupon remain unexecuted. This review does not establish runtime behavior, solver or mechanical acceptance, candidate export, engineering qualification, fabrication readiness, or climbing release.
