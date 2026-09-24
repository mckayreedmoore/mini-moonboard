# WJ-03 bound head-withdrawal route summary

This postprocessor binds the archived head-withdrawal report to its exact nominal shaft supplement. It summarizes combinations by head starting heading, signed ratchet stroke, and one matching stationary nut-counterhold heading. The exact supplement replaces only the archived shaft-path screen; other head, nut, exit, washer, and floor checks remain from the base report.

## Evidence and result

- Base report: [`wj03-head-withdrawal.json`](wj03-head-withdrawal.json), SHA-256 `03cb0201b41b1a7dbded07bb5917301c078f698c950032c3524715583252b9f5`.
- Exact shaft supplement: [`wj03-head-withdrawal-exact-shaft.json`](wj03-head-withdrawal-exact-shaft.json), SHA-256 `58dc1e5c5d070835970c05875ea9f9cd5fac5e2fd30f6f4b3bb944713704f6a7`.
- Bound summary: [`wj03-head-withdrawal-bound-summary.json`](wj03-head-withdrawal-bound-summary.json), SHA-256 `7e0e0eeae4a5fc3a3a6f78caa20cd57fbe74610365b4feb6d3a12e4722a6e234`.
- Summary producer: [`summarize_wj03_head_withdrawal.py`](../../../scripts/summarize_wj03_head_withdrawal.py), SHA-256 `8d608cbe5e121a3fae797009304ee4c7e06966898138895e7addd229fb0d96a6`.
- Focused tests: [`test_summarize_wj03_head_withdrawal.py`](../../../tests/test_summarize_wj03_head_withdrawal.py), SHA-256 `335636a661209960ec5003582dfaedca9069dad41f0a6b526aa4e1d80404ed45`.

There are 640 sampled combinations across 20 stacks. **244 combinations across 14 stacks** pass all selected nominal geometry and tool-envelope proxy checks. The other 396 have one or more non-clear proxy checks. The exact nominal shaft sweep is clear against fixed obstacles at all 20 stacks and against each of the four discrete nut-counterhold headings at all 20 stacks. It removes 80 archived square-AABB-only obstacle pairs; the archived AABB results remain recorded in the bound summary for comparison.

Six stacks have no sampled combination clear of the other proxy checks:

- `knee_outer_left_post_1`, `knee_outer_left_post_2`, `knee_outer_right_post_1`, and `knee_outer_right_post_2`: the stationary counterhold ratchet envelope and the 10 mm nut/socket/tool exit envelopes overlap the corresponding `finished_wood/knee_outer_{left,right}_under_header_link` proxy.
- `knee_outer_left_side_2` and `knee_outer_right_side_2`: those same counterhold and short-exit proxy checks overlap `finished_wood/base_rail_bottom_{left,right}`. The 5 mm nut-washer exit proxy also overlaps that rail.

These are envelope-screen results, not proof of physical blockage. The exact shaft supplement uses a nominal 6.35 mm circular shaft and does not include the separate 6.604 mm ordinary-shank sensitivity or enlarged-peer-shaft checks. A later maximum-shaft sensitivity report is separate and is not included here. The sampled headings are discrete.

No result establishes actual wrench or socket fit, assembly access, capture or retrieval, torque, thread disengagement, an accepted sequence, fabrication readiness, or structural acceptance. The floor datum is an analytical plane, not an inspected floor. Rounded floor rows straddling the producer tolerance remain marked ambiguous.

## Reproduction

```bash
uv run python scripts/summarize_wj03_head_withdrawal.py \
  docs/wood-joints-mvp/hypotheses/wj03-head-withdrawal.json \
  --exact-shaft-report \
  docs/wood-joints-mvp/hypotheses/wj03-head-withdrawal-exact-shaft.json \
  --output /tmp/wj03-head-withdrawal-bound-summary.json
```
