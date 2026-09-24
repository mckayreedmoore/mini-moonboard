# WJ-03 ordinary-bolt maximum-shaft sensitivity

Diagnostic shaft-occupancy and withdrawal sensitivity for the archived compact outer WJ-03 trial. This supplements the [nominal exact-shaft report](wj03-head-withdrawal-exact-shaft.md); it does not modify the nominal geometry or report, and it is not a hardware selection, fit result, fabrication release, or structural acceptance.

- Report JSON SHA256: `dfe0585b599bd3e3340e62841cb85e982a3b19d3eed717385ab5af0587bc750e`.
- Producer SHA256: `f49075c429982bf94d47e0652532e715dab788943b75c8b56515912b7ceb2336`.
- Focused test SHA256: `881e66e3a7ac60d31928bc494c2aae596fae006b91175de22e3a7bdcd0651440`.
- Nominal exact-shaft report SHA256: `58dc1e5c5d070835970c05875ea9f9cd5fac5e2fd30f6f4b3bb944713704f6a7`.
- Coarse withdrawal report SHA256: `03cb0201b41b1a7dbded07bb5917301c078f698c950032c3524715583252b9f5`.
- Hardware schedule audit SHA256: `cc6a74bcd3f3143bdeb26b89661f10f72e33fb041262fa09ee65f1cf684f26e6`.
- Run: source/archive checks passed before materialization; one geometry materialization took 43.24 s; sensitivity screens took about 23.52 s; total 66.76 s.

## Result

The current hardware schedule audit records an ordinary 1/4-in bolt body maximum of 0.260 in (6.604 mm). All 20 WJ-03 modeled shaft occupancies were enlarged to that class maximum together. Nominal steel/design diameter remained 6.35 mm. Axes, under-head lengths, bores, seats, heads, nuts, washers, and other nonshaft geometry stayed unchanged; no delivered SKU dimensions were inferred.

All 20 nominal and all 20 maximum installed shaft occupancies were clear against retained geometry, same-stack washer rings, and peer shafts. All 20 nominal and maximum shaft-withdrawal sweeps were clear against fixed retained obstacles. Each of the four sampled stationary-nut ratchet headings was screened separately against its moving shaft sweep; none reported an overlap. No new fixed-obstacle or heading-specific hits appeared at the maximum shaft diameter. The maximum shaft sweep remained at least 126.251 mm above analytical floor Z=0.

The installed shaft checks exclude the same stack's head and nut as target assembly parts. They do not model thread fit. This sensitivity also does not screen tool envelopes against the enlarged peer-shaft map; nominal tool-route results cannot be upgraded to a maximum-diameter route result. Complete tool-envelope checks against the enlarged installed map remain separate. The class maximum is an envelope bound from the schedule audit, not a selected or received bolt dimension.

See the [per-stack JSON report](wj03-head-withdrawal-max-shaft.json) for nominal-versus-maximum hit IDs, independent heading screens, floor screens, and source pins.
