# Current resistance-basis validation

The producer is pure offline arithmetic and byte-pin verification. Nine
focused tests and Ruff pass. Tests independently compare every signed demand,
receiver force, axial tie and factor with its exact frozen source state. They
exercise altered input bytes, source manifest and changed/misbound raw receipts.
Known answers cover bearing-angle interpolation, Mode IV, assignment reversal,
same-state steel interaction, current grips and conditional transition screens.

Canonical report: `/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json`.
SHA-256: `c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1`.
Two replays under hash seeds 71 and 983 are byte-identical.

The independently authored standard-library [raw oracle](raw_oracle.py) imports
neither the producer nor a capacity helper. It authenticates the frozen load
report and accepted raw receipt, all 143 load inputs, 19 method/source inputs,
producer bytes and independently hard-pinned source manifest/evidence digests.
It reconstructs 252 signed bolt states, 504 receiver/grain/bearing records,
6,048 forward/reverse mode values across the two Fyb scenarios, 126 group angles,
and conditional steel references. Maximum relative mode difference is
`8.793471030510673e-16`.

Independent receipt:
`/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01-raw-oracle.json`.
SHA-256: `82064d584dd66810dcde8caad6b6445e8f699c7255a30529a3621bcbd6d743b1`.
The receipt identifies the checker source SHA-256
`492d4016859f5870f7a599a051f67d3adef83967dafc714eee7d10d12790e038`.
The handoff's owned-file manifest independently anchors those source bytes.
A separate parent replay checks identical receipt bytes.

Eight isolated report mutations were rejected: signed force, axial tie from a
different increment, invented Cg, changed mode value, changed steel interaction,
changed group angle, forged input pin and joint acceptance. The receipt is
`/tmp/mini-moonboard-retained-resistance-oracle-mutations-2026-10-01.json`.

The accepted upstream native-token reader was also rerun without a native solve.
Its 756 scalar channels, 504 endpoint wrenches and 168 authenticated datums
produce the original receipt bytes, SHA-256
`c6d43017d67f864dfc25e6a77832a542a97257a1da23f4ca3a12e82d6a829ea9`.

The first independent Luna/max pass produced one confirmed source-pin defect,
now resolved, and two meaningful test gaps, now covered. The second pass found
no numerical/claim defect; correctness and architecture identified missing
checker-source identity in the oracle receipt. That provenance gap is fixed by
the source hash above and independent handoff pins. The receipts are retained
as the review trail. The fresh third pass is complete with no substantial
current finding. Final receipts are [correctness](correctness-review.md),
[testing](testing-review.md) and [architecture](architecture-review.md).
The final testing reviewer independently repeated eight in-memory mutations
with the checker that includes its source hash. Correctness independently
reproduced all three controlling stack rows and checked primary supplier facts.

All 47 formal criteria remain pending and zero close here. Component references
do not qualify the finished joints, actual hardware or complete axial path.
All acceptance/release flags remain false. No CAD/native run, physical work,
shared-file or Git mutation was executed. [Final owned-file pins](final-pins.json)
anchor the handoff; integration and staging remain with the primary agent.
