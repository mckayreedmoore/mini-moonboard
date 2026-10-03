# Independent source-only architecture review

Reviewed target: `source-review-target.json`, SHA-256 `02452912a8882bff4fbca15ee347d539a51c3bf827b3ac27154a6b763dd3b650`. It pins 15 current files for `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`; all 15 file hashes and byte counts matched at review. Scope was STI17 isolated build/free-C3D20 coupon preparation and orthotropic stress-frame source preparation.

## Finding

No substantial architecture findings remain after control-chain re-evaluation. I withdraw the earlier oracle-provenance finding: [`prepare_sti17_coupon.py:322`](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/prepare_sti17_coupon.py:322) includes the oracle path in the frozen source set and snapshots its hash. Before importing the live module, [`check_sti17_coupon.py:377`](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/check_sti17_coupon.py:377) calls the stock verifier; its default `check_live=True` checks every frozen snapshot and corresponding live source against `source_sha256` ([`wood_joint_reduced_native.py:89`](/home/mckay-linux/repos/mini-moonboard/fea/wood_joint_reduced_native.py:89)). A live oracle changed before this verification raises an error, so the proposed changed-live-oracle scenario does not pass the ordinary checker flow. A concurrent mutation between verification and import is not established as a substantial finding here.

## Boundaries

The parent validation remains `ready_for_build_or_native_run=false`; all 47 formal criteria remain pending. This review ran no build, freeze, solver, CAD, or native check and establishes no candidate export, mechanical acceptance, or run readiness. The stress-frame fixture remains unfrozen and unexecuted; its native provenance wrapper is still a planned deliverable. Those are recorded scope boundaries, not additional findings.
