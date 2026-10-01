# Matched-resource static coupon comparison

This packet compares two serialized runs of the same frozen static coupon.
The `old` case uses the preserved attempt04 diagnostic binary; `trace` uses the
attempt01 contact-point trace build. Both use one solver thread, one CPU, 1 GiB
memory and memory-plus-swap, no network, a 60-second per-run wall limit, and a
16 MiB per-run native-output cap. The cases run in the frozen order `old`,
then `trace`; the runner will not start the second if the first fails to finish
normally or exceeds a limit. The input SHA-256 is
`73f32786bf6dee6c88e78f8e3d4e24f67afb9548225868fd10850c77e27298ab`.

The comparison retains the original gates: byte identity for `.12d`, `.cel`,
`.cvg`, `.dat`, `.sta`, and `spooles.out`; FRD identity after replacing only
one `1UTIME` clock token; exact inherited attempt04 contact/convergence event
lines and counts against the historical baseline; strict new-build trace
parsing; and exact `.cvg` contact-count coverage by unique trial element and
Gauss-point identities. No numerical tolerance relaxes the comparison.

The historical event source, both build identities, the shared source archive,
the exact input, and the qualified attempt01 trace parser/contract are pinned
in `source-dependencies.json` and `build-pins.json`. The producer rechecks
those upstream hashes whenever the packet is checked or frozen. The trace
parser is imported from attempt01 by its pinned path and SHA-256 rather than
copied into another framework.

This is an output-instrumentation regression only. It does not qualify forces,
convergence mechanics, physical contact, or the current joint. Parent owns
freeze, serialized native execution, and result acceptance. This packet is
prepared only; it has no freeze and has not run either native case.

Read-only checks are `python3 prepare.py --check`, `python3 run.py --check`,
and `python3 verifier.py --self-test`. `run.py --freeze` and
`run.py --run --freeze-sha <hash>` are parent-operated.
