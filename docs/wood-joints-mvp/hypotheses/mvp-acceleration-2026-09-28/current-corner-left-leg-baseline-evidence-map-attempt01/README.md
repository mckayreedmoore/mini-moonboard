# Left-corner onward transfer: retained LEG-bolt evidence map

This narrow map links the two original bolts directly joining `base_side_left`
to `lumber_leg_left`—`lumber_leg_bolt_left_1` and `_2`—to the existing selected
baseline geometry and archived per-case checks. The separate, source-bound
seven-increment signed actions for A12-rear and A1-rear are in the parent
[onward transfer register](../current-corner-left-leg-onward-transfer-register-attempt01/register.json)
(SHA-256 `b435f23d059d8b8399bcc5ab4afdbaa71171bac476b3a50953d68f8189cac8b0`).
This packet references those actions and does not recalculate or copy them.

The selected construction schedule identifies each retained through-bolt as
12.7 mm nominal diameter × 203.2 mm nominal length, 177.8 mm wood grip, and
88.9 mm bearing length in each member. The axis IDs, receiver pair and
positions remain in the source packet and current-frame review. Purchased
length and thread dimensions are blank; no delivered fastener is established.

The archived `compact-floor-flush-development` A12-rear and A1-rear
`checks.json` files contain the same two per-bolt resistance rows, direction-
dependent lateral-yield references, and group records. Both files report
`LISTED_FIRST_STAGE_SCREENS_MET_WITH_OPEN_LIMITS` and
`qualified_for_design: false`. Those values document the old candidate checks;
they do not qualify the new corner case or transfer a historical six-case
pass. The full-root sensitivity is retained only as non-adopted context.

The current 92-axis corner layout shares `base_side_left` with these old
bolts: the current-frame review records ten new candidate axes in each
`base_side` receiver, while the two original LEG axes remain in the separate
set of 12 retained arrangements. The review records no new candidate bore in
`lumber_leg_left`. The concrete changed input for the old pair's local
group/net-section/splitting evidence is therefore the new bore pattern in
`base_side_left`; this map does not infer a failure or claim that the original
bolt axes moved. It also does not imply blanket requalification of all
retained bolts.

The old case checks provide resistance evidence for the same named bolts, but
their case-specific demands and ratios cannot be carried into the corner
candidate. Any direct comparison must use the linked signed vectors, the
applicable directional grain basis, and the affected receiver geometry. This
map computes no current utilization, capacity or acceptance and runs no
solver.

Reproduce the read-only extraction from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-left-leg-baseline-evidence-map-attempt01/produce_map.py --verify
```

The producer verifies pinned sources and the parent register, then extracts
only these two axes and the A12-rear/A1-rear baseline check rows. The JSON
records the source hashes and extracted rows. `SHA256SUMS` covers this
packet's README, producer and JSON.
