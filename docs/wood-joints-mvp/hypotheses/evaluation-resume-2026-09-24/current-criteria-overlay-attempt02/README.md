# Current criteria source overlay — attempt02

Attempt02 rebinds the exact47 aggregator to the current reviewed method-map
working-tree bytes while preserving the frozen coverage file byte for byte.
It supersedes attempt01 for current inputs and leaves attempt01 and its
review history intact.

The current method-map SHA-256 is
`2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`. Its
historical comparison uses the method map at commit
`55ede246246842285d97946bde84f35f2362923b`, SHA-256
`1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80`. The
current source changes only the `additional_group_reduction_sensitivity` and
`steel_direct` rows relative to that historical source. The frozen coverage
file remains SHA-256
`c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c` and
continues to contain the historical map pin.

The [attempt02 reconciliation](../current-criteria-method-map-reconciliation-attempt02/README.md)
pins exact working-tree bytes. It does not rely on a commit for the current
map or on a clean worktree. The coordinator's parent review accepts source
provenance only. The new
[`current-inventory-reviewed-attempt02/current-aggregate.json`](current-inventory-reviewed-attempt02/current-aggregate.json)
records the accepted provenance and keeps all 47 criterion dispositions
pending. The earlier inventory under `current-inventory/` is preserved as the
pre-review record. The temp-directory tests also exercise the accepted state
with an explicitly marked synthetic review record; they do not change the
production review.

The [current reviewed inventory](current-inventory-reviewed-attempt02/current-aggregate.json)
is fail-closed: source provenance is accepted, all 47 criteria remain pending,
and every release flag is false. The earlier
[`current-inventory/current-aggregate.json`](current-inventory/current-aggregate.json)
is preserved as the pre-review record.
Candidate `compact-floor-flush-wood-joints-development` and revision
`led-clearance-2x6-runner-seated-blocks-v1` are unchanged. No criterion
method, capacity, demand, or disposition is established.

For a future source revision, build a new read-only inventory in a previously
unused output directory, for example:

```sh
.venv/bin/python scripts/wood_joint_wj08_criteria.py \
  --bootstrap-current \
  --output-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-criteria-overlay-attempt02/current-inventory-rebuild-attempt01
```

The parent review and overlay must be updated together before any rebuild;
never overwrite a prior output directory or edit frozen coverage to erase its
historical pin.
