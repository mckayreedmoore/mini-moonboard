# Parent live monitor observations

The parent ran the pinned finite poller against the third trajectory at
19:54:49 UTC on September 25, 2026. The exact native container was confirmed
running before invocation. `parent-poll01-execution.json` records that
observation, the command, producer/test/README hashes verified before and
after execution, return code, output and saved report/checkpoint hashes.
The poll completed in 5.98 seconds without changing or signaling the solver.

`parent-poll01-report.json` contains 29 accepted states through 0.0145 s.
All 24 target CF/CFN records per state are complete: four cleat-bore pairs,
two variables and three roles. Their reported resultants are zero. The
point-pressure and complete-output framing checks remain explicitly
unchecked, and stop eligibility remains false. No physical contact-onset
or joint-acceptance conclusion follows from the zero resultants.

The poll consumed 1,211,906,612 DAT bytes and 2,186 STA bytes. The mutable
`parent-live-checkpoint.json` stores offsets for subsequent finite polls;
`parent-live-report-latest.json` is the latest observation. The separately
saved `parent-poll01-checkpoint.json` and `parent-poll01-report.json` preserve
this first poll. Later observations must preserve their own execution and
report records rather than overwrite these numbered artifacts.

`parent-poll01-peek-comparison.json` compares the first 19 states with the
earlier independently implemented finite CFN reader. All 76 slave-force
records (228 component tokens) match exactly. This checks overlapping output
observations; it does not validate equilibrium or local contact onset.

The monitor's slave/master mismatch flag uses printed-token half-quantums
without the additional arithmetic allowance used by the earlier printer
identity audit. Treat that flag as a diagnostic for further checking, not an
independently qualified identity failure or acceptance test.

Independent review of the frozen poller and first parent observation is in
`independent-review.md`. It confirms the mapped pairs, bounded read, fixture
checks and first-report scope, and records the diagnostic-bound and test
coverage limits.

The second parent poll used `parent_poll.py --poll-number 2`. This wrapper
requires the prior numbered execution and matching live checkpoint/report,
rechecks the frozen monitor pins and exact running native container, then
preserves new numbered outputs. Poll 02 consumed only 83,832,295 new DAT
bytes and 144 STA bytes. It extends the complete target records to increment
31 (0.0155 s), still with zero reported resultants and no contact-onset or
full-output readiness claim.
