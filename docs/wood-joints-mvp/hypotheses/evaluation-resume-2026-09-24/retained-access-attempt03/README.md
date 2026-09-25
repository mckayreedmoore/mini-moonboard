# Retained-frame-bolt access attempt03

This is the corrected current-geometry screen for the twelve retained source
frame-bolt stacks. It supersedes the collision interpretation of attempt02.
The review summary, exact ordered receiver pairs, head-side wire overlaps,
nut/washer translation results, and wrench-proxy limits are in
[`current-retained-access.md`](../../../current-retained-access.md).

The producer validated the exact source roles and ordered receiver IDs,
excluded 12 nonphysical source-axis display proxies, and separately excluded
the 36 source-classified tool/withdrawal envelopes and 142 hold projection
envelopes. The corresponding 142 physical T-nuts, 60 installed retained-bolt
roles, 92 candidate stacks, and all other live physical obstacle families
remain in the scene. The resulting obstacle count is 1,041.

Four lumber-leg withdrawal paths overlap modeled wires: `wire_010_A10_A11`
for the left pair and `wire_130_K10_K11` for the right pair. The other eight
bolt withdrawals and all twelve nut and nut-washer translation screens are
clear within their modeled source-BRep envelopes. Provisional wrench results
are pose/envelope checks only and do not establish real-tool access or
blockage.

Run record: `execution.json` reports completion in 9.662 s, unchanged source
files, and no native solve. `access.json` SHA-256 is
`fffa0027926a57583cc13ffbcef552fc8e5f8da96964d50c64ef63ffd4ce4c97`. The
producer and test source hashes are recorded in that execution record.
