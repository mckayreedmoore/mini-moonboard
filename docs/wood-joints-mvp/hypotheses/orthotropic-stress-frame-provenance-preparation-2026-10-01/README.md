# Stress-frame execution provenance preparation

This separate wrapper authenticates an execution before invoking the existing
pure stress-output reader. It has no Docker, solver, build, mesh, CAD or
native-launch path. It has not checked an actual stress-frame execution.

`check_provenance.py DIRECTORY --expected-freeze-sha256 HASH` requires an
externally supplied, independently reviewed freeze hash. The freeze uses the
existing native-runner schema and must bind `model.inp`, `model.json`,
`expected.json`, the exact wrapper, producer, reader, analytical oracle,
preserved stock runner and stock solver profile. The existing verifier checks
both source snapshots and live sources. The wrapper reconstructs the deck
and expectations from those verified sources before reading output.

Authorization, independent review, execution and one unique consumed terminal
ledger row must agree on the exact freeze and run. Both recorded commands
must match one CPU, 1 GiB memory and total memory-plus-swap, no network,
the pinned image/binary, the exact
output mount, a separate read-only deck mount and
`/usr/bin/timeout --signal=KILL 60s`. Both records must bind the qualified
absolute timeout utility path and SHA-256. All captured `model.*` and
`native.*` file names and hashes must equal the terminal execution inventory.
The pure reader then checks all 4,608 stress rows, 800 displacement rows,
frame labels, time and energy against its existing numerical gates.

The tests use complete synthetic records in temporary repository copies;
they write no shared native ledger or original fixture. Deliberately broken
links include freeze/source/input drift, altered numerical expectations,
profile identity, review links, unsuccessful/nonterminal execution, duplicate
ledger rows, missing or changed outputs, widened resources and TERM-only
invocation. A numerically wrong but rehashed DAT must also be refused.

Twenty-two synthetic tests and Ruff pass. Independent review, a parent-owned production freeze and a compatible scoped
hard-stop launcher remain pending. The preserved stock launcher uses TERM;
it cannot satisfy this wrapper's command gate. No new attempt is reserved.
Source preparation and a hypothetical software-fixture pass supply no
candidate wood law, contact qualification, resistance or joint acceptance.
All 47 criteria remain pending and all physical release flags remain false.
