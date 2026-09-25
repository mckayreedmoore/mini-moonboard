# Retained-frame-bolt access attempt02

Attempt02 completed, but its obstacle scene treated temporary access geometry
as installed physical parts. It kept the 36 source frame-tool/withdrawal
envelopes and 142 hold-hole/provisional-projection envelopes in the collision
map. Their IDs appear as blockers in withdrawal, wrench, nut, and washer
reports; some rows also intersect modeled wires, timber, or neighboring bolt
parts. The raw overlaps therefore do not establish either access or blockage.

Keep [`access.json`](access.json) and `execution.json` as the original run
record, not as a pass/fail result. Corrected attempt03 verifies these two
source-classified families, removes their 178 envelopes from installed-part
collision checks, and retains the 142 physical T-nuts; see the
[`attempt03 README`](../retained-access-attempt03/README.md).
