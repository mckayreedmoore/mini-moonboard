# Every-increment K=10000 diagnostic: parent-directed early stop

The parent stopped this owned native container on September 25, 2026 after
7948.409 seconds, before its 10800-second runtime maximum.
The original launcher session 34273 is terminal. The recorded native return
code 137 and `process_failed` status follow the explicit parent stop; they do
not mean an OOM, timeout, or proven inability to converge. The container was
running with OOMKilled false immediately before the stop. See
[parent stop decision](parent-stop-decision.json).

There are 38 accepted increments and 7 rejected attempts.
The last accepted status time is 0.217118E-01 s; the monitor's higher-precision
time is 0.02171185 s, short of the requested 0.025 s endpoint.
The final observed q is 1.05563621588 mm, maximum loaded displacement
0.859136685495 mm, and controller rotation
0.000399110209214 rad. No sampled motion stop fired.

The first-contact outputs have been captured and their applied work and
linear momentum checked. The source-conditional contact-storage upper bound
at 0.020 s leaves at least 0.179242268 N mm outside that envelope; continued
execution at the same settings would not resolve time accuracy. The next
response comparison keeps the binary, model and loading fixed while reducing
the initial and maximum timesteps. This stop frees the serialized work slot
for queued printer diagnostics and current midpoint CAD checks first.
Independent review of the contact-storage bound was underway at this decision.

All 27 frozen inputs and 15 recorded output hashes were verified
after the launcher terminated. Execution manifest SHA-256:
`0b1c9721d23be5a85e7d0c10be924e70a15f080d47b6cc186178424e82d6f602`. This note was added after that output inventory.
No input, reviewed geometry or selected-baseline authority changed. Neither
this run nor its bookkeeping checks accept engagement, time accuracy,
complete joint behavior, resistance, or any of the 47 pending criteria.
