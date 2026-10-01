# T08 attempt02 independent-review follow-up

**Purpose:** procedural/current-state reconciliation after the coordinator refreshed the task queue. This follow-up preserves the prior independent review and makes its pin check reproducible when the queue changes. It is not a new supplier review, hardware selection, mechanics evaluation, or candidate closeout.

The original review remains [current-hardware-material-cost-closeout-attempt02-independent-review-2026-09-28](../current-hardware-material-cost-closeout-attempt02-independent-review-2026-09-28/). The follow-up [record](follow-up-record.json) binds its README (`6b4cb0fe534f6abb5889aa052890fe0b0a7b0e1d666aa5dccaf4c1002f31b3af`), review record (`814588b80d9524291cbc0c717b3b872e7b88e81710dc7d0d5267d7a4a2c67610`), and checksum manifest (`44ac19c4996c39a318bdb9c8b119c6d31125b088ccd52f395f077e90ea0798b`). That original manifest binds attempt02's terminal `SHA256SUMS`, whose SHA-256 is `baaac3c26624c92ff96e391cbc914366321c37081186a3d212ee424754da09fd`.

The frozen attempt records 30 unique source pins with 30/30 matching hashes. Its queue pin is `e624e043f15b3fd361dc99b05be6a37ff625b6bcb0e1da2cccaf3cb557a0a35c`. The queue is a mutable coordinator artifact, so the verifier below does not require its current bytes to retain that hash. It requires that the only live source-pin drift is the queue path and that the expected hash for that pin remains the frozen value. It computes and reports the live queue SHA-256 on each run. Any other pin drift fails validation.

The verifier also checks the current attempt02 payload hashes, the frozen pin-check record, the prior review packet's bound artifacts, the axis reconciliation, and the displayed-price arithmetic. It does not reopen supplier pages or reproduce claimed web availability/prices. It does not run `build_attempt02.py`, which writes into attempt02. The result preserves the prior supported-partial, fail-closed verdict and does not mark T08 complete.

Run this read-only procedure from the repository root. It prints JSON including the current queue hash; that value is intentionally computed at runtime and is not a pass/fail constant.

```sh
python3 - <<'PY'
import hashlib, json, math, pathlib, re

root = pathlib.Path.cwd()
base = pathlib.Path('docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24')
attempt = root / base / 'current-hardware-material-cost-closeout-attempt02'
prior = root / base / 'current-hardware-material-cost-closeout-attempt02-independent-review-2026-09-28'
follow = root / base / 'current-hardware-material-cost-closeout-attempt02-independent-review-followup-2026-09-28'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_sumfile(directory, sumfile):
    rows = []
    for line in (directory / sumfile).read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        path = (directory / name.strip().lstrip('*')).resolve()
        actual = digest(path)
        assert expected == actual, (str(path), expected, actual)
        rows.append({'path': str(path.relative_to(root)), 'sha256': actual})
    return rows

# Verify this follow-up packet, all bound prior-review artifacts, and attempt02's terminal manifest.
verify_sumfile(follow, 'SHA256SUMS')
prior_manifest = digest(prior / 'SHA256SUMS')
attempt_manifest = digest(attempt / 'SHA256SUMS')
prior_record = json.loads((prior / 'review-record.json').read_text())
follow_record = json.loads((follow / 'follow-up-record.json').read_text())
assert prior_manifest == follow_record['bound_original_review']['sha256sums_sha256']
assert attempt_manifest == follow_record['bound_attempt02']['terminal_sha256sums_sha256']
assert attempt_manifest == prior_record['reviewed_attempt02']['terminal_manifest_sha256']
for artifact in follow_record['bound_original_review']['artifacts']:
    assert digest(root / artifact['path']) == artifact['sha256']
attempt_entries = verify_sumfile(attempt, 'SHA256SUMS')
assert len(attempt_entries) == 7

# Confirm the frozen 30/30 pin record without comparing a mutable live queue to its old hash.
source_pins = json.loads((attempt / 'source-pins.json').read_text())
frozen_checks = json.loads((attempt / 'verification.json').read_text())['source_pin_checks']
assert len(source_pins['sources']) == len(frozen_checks) == 30
assert len({x['path'] for x in source_pins['sources']}) == 30
assert all(x['matches'] and x['expected_sha256'] == x['actual_sha256'] for x in frozen_checks)
assert {x['path']: x['sha256'] for x in source_pins['sources']} == {x['path']: x['expected_sha256'] for x in frozen_checks}
queue_path = 'docs/wood-joints-mvp/luna-max-task-queue.json'
frozen_queue_hash = source_pins['task_queue_sha256_at_freeze']
assert frozen_queue_hash == follow_record['queue_policy']['source_pin_drift_at_authoring']['frozen_expected_sha256']
live_pin_results = []
for item in source_pins['sources']:
    actual = digest(root / item['path'])
    live_pin_results.append({'path': item['path'], 'expected_sha256': item['sha256'], 'current_sha256': actual, 'matches': actual == item['sha256']})
drift = [x for x in live_pin_results if not x['matches']]
assert len(drift) == 1 and drift[0]['path'] == queue_path
assert drift[0]['expected_sha256'] == frozen_queue_hash
live_queue_hash = digest(root / queue_path)
assert drift[0]['current_sha256'] == live_queue_hash

# Recompute count identities and cost formulas from frozen local source data.
register_path = root / base / 'current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json'
register = json.loads(register_path.read_text())
reconciliation = json.loads((attempt / 'axis-count-reconciliation.json').read_text())
candidate = sorted(x['axis_id'] for x in register['candidate_axis_rows'])
retained = sorted(x['axis_id'] for x in register['retained_axis_rows'])
hillman = sorted(x['axis_id'] for x in register['hillman_axis_rows'])
moved = sorted(x['axis_id'] for x in register['hillman_axis_rows'] if x['owner_moved_axis'])
unchanged = sorted(x['axis_id'] for x in register['hillman_axis_rows'] if not x['owner_moved_axis'])
removed = sorted(register['removed_legacy_sds25112_axis_ids'])
assert candidate == reconciliation['candidate_axis_ids'] and len(candidate) == 92
assert retained == sorted(x['axis_id'] for x in reconciliation['retained_starting_frame_bolt_axes']) and len(retained) == 12
assert hillman == reconciliation['hillman_42605_policy']['axis_ids'] and len(hillman) == 66
assert moved == reconciliation['hillman_42605_policy']['previously_owner_moved_axis_ids'] and len(moved) == 8
assert unchanged == reconciliation['hillman_42605_policy']['unchanged_axis_ids'] and len(unchanged) == 58
assert removed == reconciliation['removed_sds25112_policy']['reference_axis_ids'] and len(removed) == 144

prices = json.loads((attempt / 'public-price-observations.json').read_text())
numeric_rows = [x for x in prices['candidate_catalog_lead_rechecks'] if x.get('displayed_prices')]
assert len(numeric_rows) == 8
normalized = []
for row in numeric_rows:
    for cell in row['displayed_prices']:
        match = re.search(r'(\d+)-piece (?:box|carton)', cell['basis'])
        units = int(match.group(1)) if match else 1
        normalized.append(cell['amount'] / units)
assert math.isclose(min(normalized), 0.2314) and math.isclose(max(normalized), 2.54)
ret = prices['retained_selected_baseline_reference_only']
byid = {x['product_id']: x['displayed_each_price'] for x in ret['source_pages']}
retained_total = 4*byid['407'] + 4*byid['2573'] + 8*byid['15025'] + 4*byid['367'] + 4*byid['368'] + 8*byid['2571'] + 16*byid['15023']
hill = prices['separate_hillman_panel_kicker_purchase_reference']
hillman_total = math.ceil(66/50) * hill['displayed_price']['amount']
assert math.isclose(retained_total, 31.12) and math.isclose(hillman_total, 15.96)
assert prior_record['verdict'] == 'SUPPORTED_PARTIAL_FAIL_CLOSED'
assert prior_record['claim_boundary_review']['overstatement_found'] is False
assert prior_record['claim_boundary_review']['candidate_total_usd'] is None
assert prior_record['claim_boundary_review']['candidate_range_usd'] is None

print(json.dumps({
    'status': 'PASS',
    'verdict': 'SUPPORTED_PARTIAL_FAIL_CLOSED',
    'attempt02_payloads_verified': len(attempt_entries),
    'frozen_source_pins': {'count': len(frozen_checks), 'unique_paths': len({x['path'] for x in frozen_checks}), 'matches_at_freeze': sum(x['matches'] for x in frozen_checks)},
    'live_pin_drift': {'count': len(drift), 'path': drift[0]['path'], 'frozen_expected_sha256': frozen_queue_hash, 'current_queue_sha256': live_queue_hash},
    'reconciled_counts': {'candidate_bolts': len(candidate), 'retained_frame_bolts': len(retained), 'hillman': len(hillman), 'hillman_moved': len(moved), 'hillman_unchanged': len(unchanged), 'removed_sds_references': len(removed)},
    'arithmetic': {'candidate_display_envelope_usd_per_bolt': [round(min(normalized), 4), round(max(normalized), 2)], 'retained_reference_usd': round(retained_total, 2), 'hillman_replacement_comparator_usd': round(hillman_total, 2)},
    'candidate_cost_bound_or_t08_completion': False,
    'supplier_pages_reopened': False
}, indent=2))
PY
```

T08 remains partial. In particular, the 104 bolt-axis count is not evidence of matched/delivered stacks; product selection, fit/thread engagement, retained-bolt rechecks, compatible lumber/plywood prices and yield, Hillman receipt cost, product weight, physical receiving, and readiness/criterion evidence remain unresolved as recorded in the original review. The follow-up changes no candidate evidence and adds no acceptance claim.
