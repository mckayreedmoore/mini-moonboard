# Architecture result review — attempt 02

**Architecture/provenance result: PASS, with a stale-summary correction
outstanding.** The single execution and its offline audit are bound to the
assigned freeze and recorded outputs. This is not mechanical acceptance.

## Bound execution and output chain

The input freeze is
`87894949d0f9aa45ca479fa290fb2ae8c354884d290b9ac0e13e2a902522c8aa`.
The parent output receipt SHA256 is
`fa97942ad86cebfe1a35f0c1a50a05574a43b2a480d8f63a4ed9e1cc123d738d`; it
binds that freeze, authorization and readiness records, launch wrapper,
execution record, raw solver outputs, exact verifier inputs, and audit output.
The execution record, receipt, and on-disk output hashes agree. The recorded
command uses the pinned image and solver with a 60-second timeout, 1 GiB, and
one CPU. It returned zero in 5.596 seconds, confirmed the container terminal,
and the ledger records one of one launches consumed with the shared slot idle.
No retry is authorized.

The prelaunch wrapper is preserved and its recorded SHA matches. It checked
the exact freeze and run bounds, absence of a prior same-freeze run and busy
slot, source/runtime/manual pins, prior A12 process termination, included
usage eligibility, and readiness-review hashes before creating parent
readiness and calling the shared runner with the frozen limits. The readiness
record reports ordinary included usage allowed at 96%; the wrapper has no
credit or paid-fallback path. This review did not read the other readiness or
result-review documents.

The parent audit command names this packet's frozen `model.json`,
`model_coordinates.json`, `model.dat`, and verifier. Their recorded hashes
match disk. I replayed that offline command without writing files; its stdout
and stderr hashes match the receipt byte-for-byte. The raw solver-output hash
map also matches both `execution.json` and the receipt, including `.dat`,
`.frd`, `.sta`, `.cvg`, the frozen deck/model record, and native logs. The
solver log records `Job finished`; its nonfatal `*SURFACE BEHAVIOR` message
concerns a large-clearance tension value stated to be relevant only to
node-to-surface contact, while this deck declares surface-to-surface contact.
The original log remains in the hashed output set.

The frozen audit reports
`PASS_FINITE_CONTACT_RESULTANT_METHOD_FIXTURE`. The parent receipt leaves
`result_review_pending` true and records mechanical acceptance,
candidate-joint-contact validation, and product/material acceptance as false.
That is the correct separation: this execution checks the scoped hypothetical
contact/resultant software path, not wood, product, joint, candidate, or build
acceptance.

## Attempt 01 lineage and record issue

Attempt 01 remains a separate unlaunched refusal. Its freeze SHA is
`6ccdd8cee4c499c7438aef8c07a6ee9cba8d11beb145fdb1719cde9f4b7e95c4`, which
matches attempt 02's `supersedes_unlaunched_input_freeze_sha256`. The refusal
record still says not ready, no native solve, and zero launches; its current
SHA256 is `68c9c754328dd4049f415eb03208bf2076f1fa39d97cce05c965ff5fee33451e`,
and attempt 01 has no execution record. Attempt 02 therefore preserves the
failed restraint check as history and does not transfer acceptance from it.
The new freeze pins the old input freeze but not the refusal JSON itself; this
review records the refusal's current digest for durable lineage.

The attempt 02 `README.md` is stale: it still says native execution and parent
readiness do not exist. The machine records and this review show that both
have occurred. Update that summary before treating it as the packet's current
status. This documentation drift does not change the hashes or provenance of
the frozen execution and audit.
