# Independent review: attempt02 current criteria source overlay and WJ08 integration

Review date: 2026-09-28 (UTC). Reviewer: independent delegated review.

**Disposition: current provenance path validates, with one stale hash-manifest entry and a documented trust boundary.** No source, status, candidate, or solver files were changed by this review. No earlier review reports were read.

## Verified state

The current method-map bytes hash to `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`. The historical blob at commit `55ede246246842285d97946bde84f35f2362923b` hashes to `1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80`, matching the historical pin in frozen coverage. The byte diff contains exactly the two expected row replacements: `additional_group_reduction_sensitivity` and `steel_direct`; no other method-map rows or non-row text changed. Removed row IDs are `['additional_group_reduction_sensitivity', 'steel_direct']` and added row IDs are `['additional_group_reduction_sensitivity', 'steel_direct']`.

Frozen coverage remains byte-identical at SHA-256 `c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c` and retains historical method-map pin `1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80`. Its 47 criterion IDs exactly equal the ordered 47 source-register IDs; their newline-joined SHA-256 is `d2e947d860ca8a987db444eef09bc0206b73cd0b65899a919bc3db50c4411e5e`. The reconciliation record, source overlay, and coordinator review identify the attempt02 exact working-tree map bytes and describe provenance-only scope.

The current reviewed inventory at `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-criteria-overlay-attempt02/current-inventory-reviewed-attempt02/current-aggregate.json` reports **47 pending**, zero conditional passes, zero failures, zero not-applicable dispositions, and all release flags false. The overlay is accepted as `accepted_provenance_only`. The preserved pre-review inventory remains rejected while coordinator review is pending, also with all 47 pending. Candidate/revision are `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`. No criterion method, capacity, demand, disposition, or release is established.

The focused command `.venv/bin/pytest -q tests/test_wood_joint_wj08_criteria.py` passed: **27 tests**. The suite exercises changed map bytes, changed frozen-coverage bytes (even after updating the synthetic binding), invalid overlay pointers/status, and missing overlay binding; those cases remain pending/rejected. A separate isolated fixture check confirmed that editing only the parent-review JSON rejects the overlay and leaves the criterion pending.

## Trust boundary and manifest drift

The parent-review gate checks the `/root` reviewer field, provenance-only status and assertions, hashes of the reconciliation script/README/record, and the review hash echoed by the overlay. Those checks are implemented in `scripts/wood_joint_wj08_criteria.py` around lines 412–457. Current expectations bind the files' live hashes around lines 1347–1384. In an isolated synthetic fixture, a coordinated edit to the review JSON plus a matching overlay hash update, followed by regenerated expectations, is accepted; the test-only fixture then reports 47 synthetic conditional passes. This demonstrates the boundary: the overlay validates a self-consistent explicit review record and bound bytes, but is not a cryptographic signature or protection from an actor able to rewrite and re-pin the evidence bundle. The live production inventory remains 47 pending because scope and evidence are unresolved. `sha256.json` is not consumed by the aggregator as an external trust root.

There is also one hash-manifest mismatch at review time. The overlay README's current SHA-256 is `1f77ca5172b72c2d1ecb28ef00a39c2935d6f6cc6eb7c901d505b8480e015e27`, while `current-criteria-overlay-attempt02/sha256.json` pins `ee08c518a882b28ea472e8395d2d9eeeaa1d55b4d387b5984a231d7d85c886b6`. This is a README-only difference; the aggregator's provenance gate binds the reconciliation README, not the overlay README, and the latest live aggregation still accepts provenance only with all criteria pending. The report preserves the observed mismatch for the coordinator's planned post-review manifest refresh.

## Exact input hashes

The companion `sha256.json` binds this report to the reviewed input files. The manifest mismatch observed in the attempt02 `sha256.json` is included as evidence and has not been repaired here.
