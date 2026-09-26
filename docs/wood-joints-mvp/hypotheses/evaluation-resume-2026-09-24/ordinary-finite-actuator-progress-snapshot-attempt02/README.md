# Current finite-actuator progress snapshot

This immutable snapshot preserves five accepted increments through 0.0025 s
from the still-running `ordinary-finite-actuator-k1e4-attempt02` diagnostic.
It is not a terminal execution or a joint acceptance record. The original
first-state snapshot remains unchanged.

The [manifest](snapshot.json), SHA-256
`e315511717f1da5ea94deeee6b582db0f454280487fc19a1ef6698177c3e2051`,
records each copied file's hash, size and source. All twenty copied hashes
and sizes were verified after capture. Frozen inputs and the input-defined
initial driver state match the first-state snapshot exactly.

Each output was copied only through its size when opened. Capture was not
atomic across files: accepted STA states govern interpretation, and a partial
DAT or FRD tail must remain unknown. The execution snapshot records the
launcher as running; the parent's live session poll separately confirmed it.
The large trial contact-element history (`pilot.cel`) was intentionally
omitted. This snapshot supports no assertion about omitted trial states.

The later prefix permits checking whether incomplete contact records from
the first snapshot became complete. It does not by itself establish their
completion, contact engagement, timestep accuracy, physical thread behavior,
or any of the 47 structural/layout/hardware criteria.
